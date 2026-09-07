# `macos-keycounterbar`

> Ruta real en el repositorio: `macos/KeyCounterBar/`
> (código fuente Xcode; binario compilado en `macos/KeyCounterBar.app/`)

## Qué hace y qué NO hace
Aplicación nativa de macOS (Swift/Cocoa) que muestra en la barra de estado del
sistema las estadísticas de pulsaciones. Lee el UNIX socket
`/var/run/keycounter.socket` que expone [socket](socket.md), decodifica el JSON y
actualiza el título del `NSStatusItem` una vez por segundo.

**NO** captura pulsaciones ni escribe en la DB: es sólo un cliente visualizador
del socket que crea el proceso Python.

## Datos del bundle y compilación
- **Bundle ID:** `dev.raupulus.KeyCounterBar`
- **Versión:** 1.0 (build 1)
- **macOS mínimo:** 15.0 (compilado con Xcode 16)
- **Entitlements:** Vacíos (sin sandbox, lo que le permite conectar al socket UNIX en `/var/run`).
- **Nota Info.plist:** No declara `LSUIElement = true`, por lo que aparece en el Dock y barra de menús en lugar de ser un elemento exclusivo de la barra de estado.
- **Dependencias SwiftPM (fijadas en `Package.resolved`):**
  - `swift-nio` (2.74.0)
  - `swift-nio-transport-services` (1.22.0)
  - `swift-atomics` (1.2.0)
  - `swift-collections` (1.1.4)
  - `swift-system` (1.3.2)

## Modelo de datos
Decodifica (Swift `Decodable`) el JSON del socket:
```swift
struct DataJSON { let session: Session; let streak: Streak }
struct Session  { let pulsations_total: Int }
struct Streak   { let pulsations_current: Int; let pulsation_average: Int }
```
Muestra: `"<current> / <average>AVG / <total>T"`.

## Flujos principales
1. `applicationDidFinishLaunching` — crea el `NSStatusItem` y arranca
   `beginSocketReadingLoop`.
2. `beginSocketReadingLoop()` — con SwiftNIO (`NIOTS`) conecta al UNIX socket, lee
   una respuesta (`DataHandler.channelRead`), actualiza el título y se
   reprograma con `asyncAfter(+1s)`.
3. `applicationWillTerminate` — cierra el `EventLoopGroup`.

## Puntos de entrada
- Ficheros fuente: `AppDelegate.swift`, `ViewController.swift`.
- Depende de que el proceso Python esté corriendo y el socket exista.

## Dependencias en ambos sentidos
- **Depende de:** SwiftNIO (`NIO`, `NIOTransportServices`,
  `NIOFoundationCompat`), el UNIX socket de [socket](socket.md).
- **Le depende:** nadie dentro del repositorio (aplicación final).

## Configuración
Sin variables de entorno. La ruta del socket
(`/var/run/keycounter.socket`) está fija en `AppDelegate.swift`; el intervalo de
refresco es `timeRefreshRate = 1.0` s.

## Trampas conocidas
- Requiere que el socket exista y sea legible por el usuario de la app.
- Ruta del socket y periodo de refresco hardcodeados.
- Instalación/compilación descritas en [../deploys/README.md](../deploys/README.md).

## Tests que lo cubren
Ninguno ⚠️.

## Pendiente real
- Ninguno verificado en el código.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-07
