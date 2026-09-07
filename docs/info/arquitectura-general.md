# Arquitectura general

## Objetivo global

Registrar la **cantidad y la velocidad** de las pulsaciones de teclado (y
opcionalmente los clicks de ratón), agrupándolas en **rachas** con una
**puntuación**, para:

1. Mostrarlas en tiempo real (barra de estado, pantalla física, pantalla en
   red).
2. Cachearlas localmente en SQLite.
3. Subir periódicamente solo datos **estadísticos y no privados** a una API.

Explícitamente **no** se guarda el contenido tecleado. De cada tecla solo se
tiene en cuenta si es "normal" o "especial" y el instante en que se pulsa.

## Componentes y responsabilidades

```
                         ┌───────────────────────────────┐
                         │            main.py            │
                         │  (arranque + bucle temporal)  │
                         └───────────────┬───────────────┘
                                         │ instancia y coordina
        ┌────────────────────────────────┼─────────────────────────────┐
        │                                │                             │
        ▼                                ▼                             ▼
┌───────────────┐            ┌────────────────────────┐      ┌──────────────────┐
│   Keylogger   │            │      DbConnection      │      │  ApiConnection   │
│ (orquestador) │            │  (caché SQLite / ORM)  │      │ (subida a la API)│
└───────┬───────┘            └────────────────────────┘      └──────────────────┘
        │ contiene
        ├────────────► KeyboardLogger  (estadísticas + puntuación de teclado)
        └────────────► MouseLogger     (estadísticas de ratón)

  Salidas en tiempo real desde los modelos de estadística:
        ├────────────► Socket (UNIX)                 → i3pystatus, app macOS, etc.
        ├────────────► Display → LCDUart (UART/serie) → pantalla física
        └────────────► ClientDisplayWebsocket        → pantalla en red local
```

- **`main.py`** — Punto de entrada. Lee configuración del `.env`, instancia los
  componentes, conecta las salidas y ejecuta el **bucle** que cada pocos
  segundos vuelca rachas a la base de datos y (si procede) las sube a la API.
- **`Keylogger`** — Orquestador de la captura. Engancha (`hook`) la librería
  `keyboard` y, si procede, `mouse`. Lanza los hilos de escucha y de recarga
  ante cambios de dispositivos. Contiene los dos modelos de estadística.
- **`KeyboardLogger`** — Estado y lógica de las estadísticas de teclado:
  contadores de sesión y de racha, algoritmo de combo/puntuación, mapa de
  rachas pendientes (`spurts`) y definición del modelo de tabla.
- **`MouseLogger`** — Equivalente para el ratón (clicks por botón y rachas).
- **`DbConnection`** — Caché local. Crea las tablas dinámicamente a partir del
  `tablemodel()` de cada modelo y ofrece operaciones CRUD sobre SQLite (por
  defecto) u otro motor soportado por SQLAlchemy.
- **`SystemInfo`** — Recolector nativo de telemetría de hardware (CPU, RAM, disco, uptime, etc.) para Linux y macOS.
- **`ApiConnection`** — Serializa las tuplas de la base de datos a JSON y las
  envía a la API con reintentos HTTP.
- **`Socket`** — Servidor de socket UNIX en `/var/run/keycounter.socket` que
  emite las estadísticas actuales a cualquier cliente conectado.
- **`Display` + `LCDUart`** — Salida a una pantalla física conectada por puerto
  serie (UART). `LCDUart` es el driver de bajo nivel; `Display` adapta los
  datos de estadística al protocolo de esa pantalla.
- **`ClientDisplayWebsocket`** — Cliente que envía las estadísticas a una
  pantalla/dispositivo en la red local (obtiene su IP desde la API).

## Flujo de datos

1. **Captura (asíncrona).** Cada pulsación dispara un callback en `Keylogger`
   (`callback_keyboard` / `callback_mouse`) que actualiza el modelo de
   estadística correspondiente **en memoria**.
2. **Agrupación en rachas.** Si entre dos pulsaciones pasan más de
   `COMBO_RESET` segundos (15 por defecto), la racha actual se cierra y se
   guarda en el diccionario `spurts` del modelo; empieza una racha nueva.
3. **Emisión en tiempo real.** Tras cada pulsación, los datos actuales se
   empujan a las salidas activas (socket, pantalla UART, pantalla WebSocket).
4. **Persistencia (bucle temporal).** El bucle de `main.py` recorre `spurts` y
   escribe cada racha cerrada en SQLite mediante `DbConnection`, eliminándola
   del diccionario al guardarla.
5. **Subida a la API (opcional).** Si `UPLOAD_API=True` y hay token/URL, se
   toman los últimos registros de SQLite, se serializan a JSON y se envían a la
   API; si la subida es correcta, se borran de la caché local.
6. **Reinicio diario.** Al cruzar el fin del día (UTC) se resetean los
   contadores globales de sesión.

## Modelo de concurrencia (hilos)

El proyecto usa el módulo de bajo nivel `_thread` (`start_new_thread`) en lugar
de `threading`. Hilos relevantes:

- **Escucha de teclado/ratón** — `start_read_keyloggers_callback` engancha los
  callbacks de las librerías `keyboard`/`mouse`.
- **Vigilancia de dispositivos** — `reload_keycounter_on_new_device` comprueba
  periódicamente si cambian los dispositivos de entrada y reconstruye el hook de
  teclado (soporta conectar/desconectar un teclado USB).
- **Servidor socket** — `startWaitClients` acepta conexiones entrantes en un
  bucle.
- **Envío a pantalla** — cada actualización de pantalla se lanza en un hilo
  aparte para no bloquear la captura.
- **Bucle principal** — vive en el hilo principal (`loop()` en `main.py`).

⚠️ El estado de los modelos (`spurts`, contadores) se comparte entre el hilo de
captura y el hilo del bucle **sin locks**. Ver documento 13.

## Ciclo de vida

1. `main()` carga el `.env`, crea `Display` (si procede), `Keylogger`,
   `ApiConnection`, `Socket` y `ClientDisplayWebsocket` (si procede).
2. `Keylogger` arranca en su constructor los hilos de captura y de vigilancia de
   dispositivos.
3. `loop()` inicializa `DbConnection`, registra las tablas de teclado y ratón,
   espera 30 s para acumular datos y entra en un `while True` que cada ~10 s
   persiste y sube datos.
4. El proceso está pensado para ejecutarse **como root** y de forma permanente
   en segundo plano (hoy vía `cron @reboot`; ver mejoras propuestas para
   convertirlo en servicio).

## Persistencia de datos

- **Motor por defecto:** SQLite, fichero `keycounter.db` junto al script.
- **ORM:** SQLAlchemy (API "core" con `Table`/`MetaData`, más una `session`
  para borrados por lote).
- **Esquema:** no está hardcodeado; se genera desde el método `tablemodel()` de
  cada modelo (`KeyboardLogger`, `MouseLogger`).

## Glosario

- **Racha / spurt:** grupo de pulsaciones consecutivas separadas por menos de
  `COMBO_RESET` segundos. Es la unidad que se guarda y se sube.
- **Combo / score:** puntuación que se acumula según el número de pulsaciones de
  la racha y un algoritmo determinista (ver documento 04).
- **Sesión:** conjunto de estadísticas globales del día actual; se reinician al
  cambiar de día (UTC).
- **Tecla especial:** tecla no imprimible (Ctrl, Alt, F1…); se contabiliza
  aparte mediante el mapa `KEYS_MAP`.
- **DEVICE_ID / DEVICE_NAME:** identificador y nombre del equipo para distinguir
  el origen de los datos en la API.

## Dependencias externas

- **Python 3.12** (según README).
- Librerías: `keyboard`, `mouse` (opcional), `sqlalchemy`, `python-dotenv`,
  `requests`, `pyserial` (`serial`, solo si se usa pantalla UART).
- Herramientas de sistema que se invocan por subproceso: `ls /dev/input/by-id/`,
  `cat /proc/bus/input/devices` (Linux) para detectar dispositivos.

Ver el detalle de cada componente en los documentos siguientes.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-07
