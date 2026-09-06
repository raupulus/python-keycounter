# AGENTS.md — Python KeyCounter

Instrucciones para cualquier agente (y persona) que trabaje en este repositorio.
Archivo central de agentes. `CLAUDE.md` es un enlace a este archivo.

- Configuración de agentes centralizada en `.agents/` (el directorio `.claude`
  es un enlace simbólico a `.agents/`).
- Documentación técnica viva en `docs/info/` (una fuente de verdad por módulo).

## Idioma
- Documentación, comentarios y textos de usuario en **español** (con acentos).
- Identificadores, nombres de fichero y de directorio, y mensajes de log en
  **inglés**. Excepción: los campos que devuelve una API de terceros se usan tal
  como los manda.

## Atribución
- Nick `@raupulus`, email `public@raupulus.dev`.
- Sin firmas de agente en commits, PRs ni documentación (nada de
  `Co-Authored-By`, «Generated with…» ni identificadores de sesión).

---

# Documentación

**Documentar es parte de la tarea. Ninguna tarea está terminada si su
documentación no se actualiza EN EL MISMO COMMIT que el código.**

## Reglas permanentes
1. Toda la documentación técnica detallada vive en `docs/info/`, **un `.md` por
   módulo**, y debe mantenerse actualizada de forma **obligatoria** al editar los
   módulos.
2. Jerarquía de verdad sobre el estado actual:
   **código > `docs/info/` > `AGENTS.md` > el resto**. `docs/planning/`,
   `docs/future/` y `docs/auditorias/` **NUNCA** son fuente de verdad del estado.
3. Discrepancia entre documentación y código: se corrige en el commit en que se
   detecta, no se anota para después.
4. Tocas un módulo → actualizas su `.md`. Creas uno → lo creas desde
   `docs/info/_MODULE_TEMPLATE.md` y lo indexas en `docs/info/README.md` y en este
   archivo. Eliminas uno → borras su `.md` y lo quitas de TODOS los índices.
5. Todo archivo bajo `docs/`, en cualquier subdirectorio, termina con esta línea
   exacta, tras un separador `---`:
   `> Creado: YYYY-MM-DD · Última revisión: YYYY-MM-DD`. La fecha de creación no
   se toca nunca; la de revisión se actualiza en el mismo commit que el documento.
6. Toda fase o módulo de una planificación empieza con una descripción y termina
   con un checklist `- [ ]`. `[x]` significa verificado funcionando y cumpliendo.
   Escribir el código no marca la casilla.
7. `docs/planning/` y `docs/auditorias/` son trabajo temporal de UN desarrollador:
   no compartido, no versionado, no existe en un clon nuevo. Ciclo:
   crear → trabajar → verificar → promocionar lo duradero → BORRAR. `archived/` es
   sala de espera hasta confirmar la implementación, no archivo histórico.
8. Antes de borrar lo efímero, promociona: comportamiento del módulo →
   `docs/info/<modulo>.md`; decisión deliberada que alguien querrá «arreglar» →
   `docs/info/decisiones-tecnicas.md`; trampa duradera → tabla de trampas de este
   archivo; cambio de arquitectura, rutas o comandos → este archivo; idea aplazada
   → `docs/future/`; regresión → un test, no un documento.
9. Nada versionado puede enlazar a `docs/planning/` ni a `docs/auditorias/`: sería
   un enlace roto para quien clone. Y no los saques del `.gitignore` por
   conveniencia puntual.
10. **Lectura dirigida:** trabajando en un módulo lees SOLO su `.md`; si tocas una
    API de terceros añades `docs/apis/<api>/` en este orden: `README.md` →
    `00-fundamentos.md` + `ERRATAS.md` + `LIMITACIONES.md` → solo el dominio que
    necesites. No leas el resto de `docs/info/`, ni `docs/future/`, ni `archived/`,
    ni `src/`. (No hay `DESIGN.md`/`COMPONENTS.md`: el proyecto no tiene frontend.)
11. Nunca configures nada a partir de la especificación oficial de una API externa
    sin verificarlo con una petición real. Lo no comprobado se marca como
    `⚠️ sin verificar`.

## Disparadores
- Modificas un módulo (campos, lógica, rutas, contratos) → su `.md` en
  `docs/info/`.
- Cambias un contrato público (socket, JSON, esquema DB, endpoints API) → actualiza
  el `.md` del módulo y comprueba qué clientes lo consumen antes de romperlo.
- Integras o tocas la API remota → `docs/info/apis/raupulus-api.md` (sin duplicar
  el dato oficial, que iría destilado y verificado en `docs/apis/raupulus/`).
- Añades comando o script → `docs/info/commands.md`.
- Añades o quitas directorios → el árbol de estructura de este archivo.
- Planificas → fase en `docs/planning/` con descripción + checklist.
- Te piden auditoría → informe en `docs/auditorias/`; al cerrar hallazgos,
  promocionar y borrar.
- Idea decidida pero aplazada → `docs/future/`, nunca `docs/info/`.

## Índice de `docs/info/`
| Módulo | Fichero real | Doc |
|--------|--------------|-----|
| main | `main.py` | `docs/info/main.md` |
| keylogger | `Models/Keylogger.py` | `docs/info/keylogger.md` |
| keyboard-logger | `Models/KeyboardLogger.py` | `docs/info/keyboard-logger.md` |
| mouse-logger | `Models/MouseLogger.py` | `docs/info/mouse-logger.md` |
| db-connection | `Models/DbConnection.py` | `docs/info/db-connection.md` |
| api-connection | `Models/ApiConnection.py` | `docs/info/api-connection.md` |
| socket | `Models/Socket.py` | `docs/info/socket.md` |
| client-display-websocket | `Models/ClientDisplayWebsocket.py` | `docs/info/client-display-websocket.md` |
| display | `Models/Display.py` | `docs/info/display.md` |
| lcd-uart | `Models/LCDUart.py` | `docs/info/lcd-uart.md` |
| macos-keycounterbar | `macos/KeyCounterBar/` | `docs/info/macos-keycounterbar.md` |

Índice maestro navegable: `docs/info/README.md`. Otros: `commands.md`,
`decisiones-tecnicas.md`, `apis/raupulus-api.md`, `_MODULE_TEMPLATE.md`.

## Tabla de trampas conocidas (transversales)
| Trampa | Dónde | Detalle |
|--------|-------|---------|
| Requiere root | proceso Python | Captura de teclado + socket en `/var/run/`. |
| Internos de `keyboard` | `Models/Keylogger.py` | Usa `keyboard._nixkeyboard`/`_KeyboardListener`; frágil ante cambios de la librería, específico de Linux. |
| `method` ignorado | `Models/ApiConnection.py` | `send` siempre hace `POST`. |
| id de dispositivo 16 hardcodeado | `Models/ApiConnection.py` | `get_websocket_server_display_info`. |
| «WebSocket» = TCP plano | `Models/ClientDisplayWebsocket.py` | No es protocolo WebSocket; TCP al puerto 80. |
| Estado a nivel de clase | modelos y `DbConnection` | Varios atributos/conexiones se definen en la clase, no por instancia. |
| SQLite como caché | `keycounter.db` | Se vacía tras subir a la API; está en `.gitignore`. |

---

# Estructura del repositorio

```
python-keycounter/
├── AGENTS.md                     # Este archivo (instrucciones de agentes)
├── CLAUDE.md                     # Enlace simbólico → AGENTS.md
├── README.md                     # Documentación de usuario
├── LICENSE
├── .env.example                  # Plantilla de configuración
├── .agents/                      # Config de agentes (real)
│   ├── settings.local.json
│   └── hooks/
├── .claude                       # Enlace simbólico → .agents/
├── main.py                       # Orquestador / punto de entrada
├── configuration.py              # Vacío (placeholder sin uso)
├── functions.py                  # Vacío (placeholder sin uso)
├── Models/                       # Módulos de dominio (Python)
│   ├── Keylogger.py
│   ├── KeyboardLogger.py
│   ├── MouseLogger.py
│   ├── DbConnection.py
│   ├── ApiConnection.py
│   ├── Socket.py
│   ├── ClientDisplayWebsocket.py
│   ├── Display.py
│   └── LCDUart.py
├── Debug/
│   └── client_socket.py          # Cliente de ejemplo del UNIX socket
├── macos/
│   ├── KeyCounterBar/            # Fuente Xcode de la app de barra de estado
│   └── KeyCounterBar.app/        # App compilada
└── docs/
    ├── info/                     # Documentación técnica VIVA (versionada)
    │   ├── README.md             # Índice maestro
    │   ├── _MODULE_TEMPLATE.md
    │   ├── commands.md
    │   ├── decisiones-tecnicas.md
    │   ├── <modulo>.md           # Uno por módulo
    │   └── apis/raupulus-api.md  # Cómo integramos la API
    ├── deploys/                  # Guías de despliegue (versionado)
    ├── images/                   # Imágenes del README
    ├── apis/<api>/               # Doc oficial destilada de terceros (cuando exista)
    ├── future/                   # Decidido pero aplazado (cuando exista)
    ├── planning/                 # [NO GIT · efímero por desarrollador]
    └── auditorias/               # [NO GIT · efímero por desarrollador]
```

> `docs/planning/` y `docs/auditorias/` están en `.gitignore` y sólo existen en la
> copia local de quien las crea. `docs/apis/<api>/` y `docs/future/` se crean sólo
> cuando haya contenido real (no se dejan carpetas vacías).

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
