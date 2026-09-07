# Documentación técnica viva — `docs/info/`

Índice maestro de la documentación técnica **viva** del proyecto Python
KeyCounter. Un archivo `.md` por módulo y documentos técnicos transversales.
Esta carpeta es la segunda fuente de verdad sobre el estado actual, sólo por
detrás del código (código > `docs/info/` > `AGENTS.md` > el resto).

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

## Documentación transversal del sistema

| Documento | Descripción |
|-----------|-------------|
| [arquitectura-general.md](arquitectura-general.md) | Visión global, flujo de datos, concurrencia (hilos), persistencia y ciclo de vida. |
| [configuracion.md](configuracion.md) | Todas las variables de entorno (`.env`), valores por defecto y su efecto. |
| [pendientes-y-mejoras.md](pendientes-y-mejoras.md) | Catálogo de bugs, riesgos latentes y deuda técnica priorizada. |
| [matriz-compatibilidad.md](matriz-compatibilidad.md) | Matriz de compatibilidad por plataforma (Debian, Fedora, SteamOS, macOS, Raspberry OS). |
| [entorno-y-dependencias.md](entorno-y-dependencias.md) | Entorno de ejecución, paquetes de sistema, dependencias Python y PEP 668. |
| [despliegue-como-servicio.md](despliegue-como-servicio.md) | Mecanismos de despliegue y arranque en segundo plano (systemd, cron, launchd). |
| [archivos-y-control-de-versiones.md](archivos-y-control-de-versiones.md) | Inventario de archivos del proyecto, políticas git e higiene de repositorio. |
| [commands.md](commands.md) | Comandos y scripts de prueba y ejecución. |
| [decisiones-tecnicas.md](decisiones-tecnicas.md) | Decisiones deliberadas que alguien podría querer «arreglar». |
| [apis/raupulus-api.md](apis/raupulus-api.md) | Cómo integramos nosotros la API remota (especificación oficial en [`docs/apis/raupulus/keycounter.md`](../apis/raupulus/keycounter.md)). |
| [_MODULE_TEMPLATE.md](_MODULE_TEMPLATE.md) | Plantilla para nuevos módulos. |

> No hay `DESIGN.md` ni `COMPONENTS.md`: el proyecto no tiene frontend web ni
> sistema de estilos. Se crearán si algún día se añade una interfaz gráfica.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-07
