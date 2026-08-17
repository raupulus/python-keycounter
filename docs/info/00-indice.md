# Documentación técnica — Python KeyCounter

Este directorio (`docs/info`) contiene la documentación técnica del proyecto
**Python KeyCounter**, generada tras analizar el código módulo a módulo. El
objetivo es dejar constancia de **qué hace cada parte**, **qué objetivos cubre**
y **qué problemas tiene**, como base para futuras ampliaciones y mejoras.

> **Estado:** en producción desde 2020, funcionando de forma estable tras años de
> uso. Esta documentación corresponde a la fase de **análisis y recopilación de
> información**; el código **no se ha modificado**.

## Qué es este proyecto

Contador de pulsaciones de teclado (y opcionalmente ratón) para GNU/Linux y
macOS. **No es un keylogger de contenido**: no guarda qué se escribe, solo
estadísticas agregadas por "rachas" (spurts) de actividad, a las que asigna una
puntuación. Esos datos estadísticos (no privados) se cachean en una base de
datos local SQLite y, opcionalmente, se suben a una API propia.

Además expone los datos en tiempo real por varios canales: un socket UNIX local,
una pantalla física por serie (UART) y/o una pantalla en red.

## Índice

### Visión general

| # | Documento | Contenido |
|---|-----------|-----------|
| 01 | [Arquitectura general](01-arquitectura-general.md) | Visión global, flujo de datos, hilos, ciclo de vida y glosario. |
| 02 | [main.py y el bucle principal](02-main-y-bucle.md) | Punto de entrada, orquestación, `loop()`, persistencia y subida. |

### Captura y estadísticas

| # | Documento | Contenido |
|---|-----------|-----------|
| 03 | [Keylogger (orquestador)](03-keylogger.md) | Enganche de teclado/ratón, hilos, recarga por dispositivos. |
| 04 | [KeyboardLogger](04-keyboardlogger.md) | Rachas, algoritmo de combo/puntuación, modelo de tabla. |
| 05 | [MouseLogger](05-mouselogger.md) | Clicks por botón, rachas y modelo de tabla. |

### Persistencia y comunicación

| # | Documento | Contenido |
|---|-----------|-----------|
| 06 | [DbConnection (caché SQLite)](06-dbconnection.md) | Definición dinámica de tablas y CRUD con SQLAlchemy. |
| 07 | [ApiConnection](07-apiconnection.md) | Reintentos HTTP, serialización JSON y subida de rachas. |
| 08 | [Socket UNIX](08-socket-unix.md) | Servidor de estadísticas en tiempo real para otras apps. |

### Salidas y clientes

| # | Documento | Contenido |
|---|-----------|-----------|
| 09 | [Pantalla UART](09-pantalla-uart.md) | Salida a pantalla física por puerto serie. |
| 10 | [ClientDisplayWebsocket](10-client-display-websocket.md) | Envío de estadísticas a una pantalla en la red local. |
| 11 | [App macOS (KeyCounterBar)](11-app-macos.md) | Cliente Swift que muestra las rachas en la barra superior. |

### Configuración, estado y diagnóstico

| # | Documento | Contenido |
|---|-----------|-----------|
| 12 | [Configuración (.env)](12-configuracion.md) | Todas las variables de entorno y su efecto. |
| 13 | [Problemas, riesgos y deuda técnica](13-pendientes-y-mejoras.md) | Catálogo de bugs, riesgos latentes y deuda, priorizado. |
| 14 | [Matriz de compatibilidad](14-matriz-compatibilidad.md) | Qué funciona en Debian, Fedora, SteamOS, macOS y Raspberry OS. |
| 15 | [Entorno y dependencias](15-entorno-y-dependencias.md) | Cómo se ejecuta hoy, de qué depende y por qué rompe al actualizar. |
| 16 | [Arranque y ejecución actual](16-despliegue-como-servicio.md) | Mecanismo de arranque, requisito de root y sus limitaciones. |
| 17 | [Archivos y control de versiones](17-archivos-y-control-de-versiones.md) | Inventario de archivos, qué versiona git y qué no debería. |

## Estructura del repositorio

```
python-keycounter/
├── main.py                  # Punto de entrada: arranca captura, socket, API y bucle
├── functions.py             # (vacío) reservado para utilidades comunes
├── configuration.py         # (vacío) reservado para configuración
├── .env / .env.example      # Configuración por variables de entorno
├── LICENSE                  # GNU GPL v3
├── AGENTS.md                # Reglas de contribución
├── Models/
│   ├── Keylogger.py         # Orquestador: engancha teclado y ratón
│   ├── KeyboardLogger.py    # Estadísticas y puntuación del teclado
│   ├── MouseLogger.py       # Estadísticas del ratón
│   ├── DbConnection.py      # Caché local SQLite vía SQLAlchemy
│   ├── ApiConnection.py     # Subida de estadísticas a la API
│   ├── Socket.py            # Servidor socket UNIX
│   ├── Display.py           # Puente de pantalla (formatea datos)
│   ├── LCDUart.py           # Driver de la pantalla física por UART
│   └── ClientDisplayWebsocket.py  # Cliente hacia pantalla en red
├── Debug/
│   └── client_socket.py     # Ejemplo de cliente del socket UNIX
├── macos/
│   ├── KeyCounterBar/       # Proyecto Xcode (Swift)
│   └── KeyCounterBar.app/   # Binario compilado, distribuido a propósito
└── docs/
    ├── images/              # Capturas del proyecto
    ├── info/                # (este directorio) documentación técnica
    └── planning/            # Planificación local — excluida de git
```

## Convenciones de la documentación

- Los nombres de métodos, variables de entorno y rutas se citan **tal cual
  aparecen en el código** en el momento de redactar estos documentos.
- Los comportamientos problemáticos se marcan con **⚠️ Nota** y se recogen de
  forma consolidada en el [documento 13](13-pendientes-y-mejoras.md).
- Este directorio documenta **el estado actual**. Las propuestas de cambio viven
  en `docs/planning/`, que es local y no se versiona.
- Toda modificación futura del código debe seguir las reglas de
  [`AGENTS.md`](../../AGENTS.md).
