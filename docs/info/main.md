# `main`

> Ruta real en el repositorio: `main.py`

## Qué hace y qué NO hace
Punto de entrada de la aplicación. Carga la configuración desde `.env` mediante `python-dotenv` con `load_dotenv(override=True)` (dando prioridad al archivo sobre variables de entorno existentes), instancia
los componentes (pantalla, keylogger, API, socket, cliente websocket, colector
de telemetría de hardware [system-info](system-info.md)), gestiona la sincronización
inicial de contadores acumulados del día desde la API (teclado y ratón vía
`/keycounter/summary`, con reintento de 1 hora ante fallo) y ejecuta el bucle
periódico que vuelca las rachas a la base de datos local y las sube a la API
inyectando el estado de hardware del dispositivo (`hardware_device_info`) únicamente
en el momento de subir sesiones.

**NO** captura pulsaciones por sí mismo (eso es de [keylogger](keylogger.md)),
**NO** define el esquema de datos (eso es de [keyboard-logger](keyboard-logger.md)
y [mouse-logger](mouse-logger.md)) ni gestiona directamente la conexión a la DB.

## Modelo de datos
No define modelo propio. Opera sobre los `spurts` (rachas) de los modelos de
teclado y ratón y sobre las tablas de [db-connection](db-connection.md).

## Flujos principales
1. `main()`
   - Crea `Display` sólo si `SERIAL_DISPLAY_ENABLED`.
   - Instancia `Keylogger` (arranca hilos de captura para teclado y ratón).
   - Instancia `ApiConnection`.
   - Instancia `SystemInfo.create(debug=DEBUG)` para telemetría de hardware
     (Linux o macOS nativo).
   - Instancia `Socket` y lo asocia al keylogger (`set_socket`).
   - Si `SEND_DATA_TO_WEBSOCKET_SERVER`, instancia `ClientDisplayWebsocket` y lo
     asocia (`set_client_display_websocket`).
   - Lanza `try_sync_initial_stats` en un hilo secundario para recuperar los
     acumulados del día (teclado y ratón) desde la API sin bloquear la captura de
     teclas.
   - Llama a `loop(...)` pasando `system_info`.
2. `try_sync_initial_stats(keylogger, apiconnection)`
   - Si `is_synced` ya es `True`, no hace nada.
   - Actualiza `last_sync_attempt = time.time()`.
   - Llama a `apiconnection.get_summary(date='today')`.
   - Si recibe respuesta:
     - Aplica los datos de teclado en `keylogger.model_keyboard.apply_initial_summary(summary)`.
     - Si `MOUSE_ENABLED`, aplica los datos de ratón en `keylogger.model_mouse.apply_initial_summary(summary['mouse'])`.
     - Marca `is_synced = True` (no volverá a consultar la API en toda la vida del proceso).
   - Si falla (404/403/error/timeout), espera 1 hora antes del siguiente reintento.
3. `loop(keylogger, socket, apiconnection, display, system_info)`
   - Crea `DbConnection`, registra las tablas `keyboard` y (si `MOUSE_ENABLED`)
     `mouse`.
   - Espera 30 s de margen para acumular datos.
   - Bucle infinito: `insert_data_in_db(...)` para teclado (y ratón), y si
     `UPLOAD_API` y hay token/URL, `upload_data_to_api(...)`.
   - Tras cada subida, si `not is_synced` y han pasado 3600 s (1 hora) desde el
     último intento, relanza `try_sync_initial_stats` en segundo plano.
   - `sleep(10)` al final de cada iteración.
4. `insert_data_in_db(dbconnection, tablemodel)` — recorre `tablemodel.spurts`,
   guarda las rachas con datos válidos (`pulsations > 1` en teclado,
   `total_clicks > 1` en ratón) y elimina del map las guardadas.
5. `upload_data_to_api(dbconnection, apiconnection, tablemodel, system_info)` —
   lee los últimos `n_registers = 10` registros de la DB local. Obtiene de forma
   defensiva `system_info.get_hardware_device_info()` (si falla o da error, se
   ignora y no bloquea la subida). Llama a `apiconnection.upload(..., extra_fields={'hardware_device_info': hw_info})`
   y, si la API responde éxito, borra las rachas subidas de la DB local.

## Puntos de entrada
- `main()` — ejecutado desde `if __name__ == "__main__"`.
- Requiere permisos de **root** en Linux/macOS para capturar teclado y crear el
  socket en `/var/run/`.

## Dependencias en ambos sentidos
- **Depende de:** `Models.DbConnection`, `Models.ApiConnection`,
  `Models.Display`, `Models.Socket`, `Models.ClientDisplayWebsocket`,
  `Models.Keylogger`, `Models.SystemInfo`, `python-dotenv`.
- **Le depende:** nadie (es la raíz de ejecución).

## Configuración
| Variable | Defecto | Efecto |
|----------|---------|--------|
| `SYSTEM_OS` | `auto` | Fuerza el recolector de hardware (`auto`, `linux`, `macos`). |
| `SERIAL_PORT` | `None` | Puerto serie de la pantalla LCD. |
| `SERIAL_BAUDRATE` | `9600` | Baudios de la pantalla. |
| `SERIAL_DISPLAY_ENABLED` | `False` | Activa la pantalla LCD serie. |
| `DISPLAY_ORIENTATION` | `horizontal` | Orientación de la pantalla. |
| `MOUSE_ENABLED` | `False` (acepta `True`/`true`) | Registra también el ratón. |
| `DEBUG` | `False` | Traza por consola. |
| `UPLOAD_API` | `False` | Habilita la subida a la API. |
| `SEND_DATA_TO_WEBSOCKET_SERVER` | `False` | Activa el cliente de pantalla en red. |
| `SYNC_RETRY_INTERVAL_SECONDS` | `3600` | Intervalo mínimo (1 h) entre reintentos de sincronización si falla. |

## Trampas conocidas
- La sincronización inicial es **única**: una vez obtenida (`is_synced = True`),
  nunca se vuelve a pedir información a la API.
- El servidor hace el corte por `created_at` en UTC; las pulsaciones y clicks
  de la API se suman a lo que se haya registrado localmente durante el arranque.
- El objeto `hardware_device_info` es opcional para la API; si la recolección
  falla o lanza error, se omite y la subida de pulsaciones prosigue sin detenerse.
- `except ():` en `upload_data_to_api` es una tupla vacía que no captura ninguna excepción (debería ser `except Exception`), por lo que cualquier fallo inesperado no controlado se propaga sin traza formateada.
- El bloque de `reboot` (recarga del keylogger al conectar dispositivos) está
  **comentado** en el bucle; el flag `keylogger.reboot` se activa pero no se actúa
  sobre él aquí.
- Hay `sleep(30)` inicial y varios `sleep` que retrasan la primera persistencia.

## Tests que lo cubren
Ninguno ⚠️.

## Pendiente real
- Decidir si se implementa o se elimina el bloque `reboot` comentado.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-07
