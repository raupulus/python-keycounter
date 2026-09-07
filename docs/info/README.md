# Documentación técnica viva — `docs/info/`

Índice maestro de la documentación técnica **viva** del proyecto Python
KeyCounter. Un archivo `.md` por módulo. Esta carpeta es la segunda fuente de
verdad sobre el estado actual, sólo por detrás del código
(código > `docs/info/` > `AGENTS.md` > el resto).

Antes de tocar un módulo, lee **sólo** su `.md` (lectura dirigida, ver
`AGENTS.md`). Si tocas el módulo, actualizas su `.md` en el mismo commit.

## Índice de módulos

### Núcleo Python
| Módulo | Fichero | Descripción |
|--------|---------|-------------|
| [main](main.md) | `main.py` | Orquestador: arranca componentes y ejecuta el bucle de guardado/subida. |
| [keylogger](keylogger.md) | `Models/Keylogger.py` | Captura de teclado y ratón mediante hooks en hilos. |
| [keyboard-logger](keyboard-logger.md) | `Models/KeyboardLogger.py` | Modelo de datos y estadísticas del teclado (rachas, combos). |
| [mouse-logger](mouse-logger.md) | `Models/MouseLogger.py` | Modelo de datos y estadísticas del ratón (clicks, rachas). |
| [system-info](system-info.md) | `Models/SystemInfo.py` | Telemetría nativa de hardware (RAM, CPU, disco, uptime, etc.) para Linux y macOS. |
| [db-connection](db-connection.md) | `Models/DbConnection.py` | Caché local en SQLite/SQLAlchemy. |
| [api-connection](api-connection.md) | `Models/ApiConnection.py` | Subida de datos a la API remota. |
| [socket](socket.md) | `Models/Socket.py` | Servidor UNIX socket para exponer estadísticas en tiempo real. |
| [client-display-websocket](client-display-websocket.md) | `Models/ClientDisplayWebsocket.py` | Cliente TCP que envía estadísticas a una pantalla en la red local. |
| [display](display.md) | `Models/Display.py` | Puente entre las estadísticas y la pantalla LCD serie. |
| [lcd-uart](lcd-uart.md) | `Models/LCDUart.py` | Driver de bajo nivel de la pantalla LCD por UART/serie. |

### Aplicaciones cliente
| Módulo | Fichero | Descripción |
|--------|---------|-------------|
| [macos-keycounterbar](macos-keycounterbar.md) | `macos/KeyCounterBar/` | App de barra de estado en macOS que lee el UNIX socket. |

## Otros documentos de esta carpeta
- [commands.md](commands.md) — comandos y scripts del proyecto.
- [decisiones-tecnicas.md](decisiones-tecnicas.md) — decisiones deliberadas que alguien podría querer «arreglar».
- [apis/raupulus-api.md](apis/raupulus-api.md) — cómo integramos nosotros la API remota (especificación oficial en [`docs/apis/raupulus/keycounter.md`](../apis/raupulus/keycounter.md)).
- [_MODULE_TEMPLATE.md](_MODULE_TEMPLATE.md) — plantilla para nuevos módulos.

> No hay `DESIGN.md` ni `COMPONENTS.md`: el proyecto no tiene frontend web ni
> sistema de estilos. Se crearán si algún día se añade una interfaz gráfica.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-07
