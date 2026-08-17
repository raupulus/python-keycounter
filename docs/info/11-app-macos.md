# 11 — App macOS (`KeyCounterBar`)

**Ubicación:** `macos/KeyCounterBar/` (proyecto Xcode) y
`macos/KeyCounterBar.app` (binario ya compilado)

## Objetivo del módulo

Aplicación nativa de macOS en **Swift** que muestra las estadísticas de
KeyCounter en la **barra de menús superior** del sistema. Actúa como **cliente
del socket UNIX** (`/var/run/keycounter.socket`) que crea el proceso Python: lee
el JSON y lo pinta en tiempo real.

Es la contraparte de macOS al uso que en Linux se hace con i3pystatus.

## Datos del bundle

Extraídos de `macos/KeyCounterBar.app/Contents/Info.plist`:

| Clave | Valor |
|-------|-------|
| Identificador | `dev.raupulus.KeyCounterBar` |
| Nombre visible | Keycounter Bar |
| Versión | 1.0 (build 1) |
| macOS mínimo | **15.0** |
| SDK / Xcode de compilación | macOS 15.0 / Xcode 16 |

**Entitlements vacíos:** `KeyCounterBar.entitlements` no declara ninguna
capacidad, es decir, la app **no está en sandbox**. Es lo que le permite leer el
socket UNIX en `/var/run`; una app sandboxed no podría.

⚠️ El `Info.plist` **no define `LSUIElement`**, así que la app aparece en el Dock
y con menú propio, en lugar de comportarse como un accesorio exclusivo de la
barra de estado. Para una app que solo vive en la barra superior, lo habitual
sería `LSUIElement = true`.

## Dependencias (SwiftPM)

Fijadas en `Package.resolved` — a diferencia del lado Python, aquí **sí hay
versiones bloqueadas**:

| Paquete | Versión |
|---------|---------|
| swift-nio | 2.74.0 |
| swift-nio-transport-services | 1.22.0 |
| swift-atomics | 1.2.0 |
| swift-collections | 1.1.4 |
| swift-system | 1.3.2 |

## Estructura del proyecto Xcode

```
macos/KeyCounterBar/
├── KeyCounterBar.xcodeproj/          # Proyecto Xcode
└── KeyCounterBar/
    ├── AppDelegate.swift             # Lógica principal (barra de estado + socket)
    ├── ViewController.swift          # Vista (sin lógica relevante)
    ├── Base.lproj/Main.storyboard    # Interfaz base
    ├── Assets.xcassets/…             # Iconos de la app
    └── KeyCounterBar.entitlements    # Permisos/sandbox
```

## `AppDelegate.swift` (núcleo)

Usa **SwiftNIO** (`NIO`, `NIOTransportServices`) para hablar con el socket UNIX.

### Modelos de datos

Reflejan el JSON que emite `Socket.update()`:

```swift
struct DataJSON  { let session: Session; let streak: Streak }
struct Session   { let pulsations_total: Int }
struct Streak    { let pulsations_current: Int; let pulsation_average: Int }
```

### `DataHandler` (ChannelInboundHandler)

Recibe los bytes del socket, decodifica el `DataJSON` con `JSONDecoder` y cierra
la conexión tras leer un mensaje.

### `leerSocket(group:)`

Abre una conexión NIO al **unix domain socket**
`/var/run/keycounter.socket`, engancha el `DataHandler` y devuelve un
`EventLoopFuture<DataJSON>`. Si no llega dato, lanza `SocketError.noDataReceived`.

### `AppDelegate`

- Crea un `NSStatusItem` en la barra de estado.
- `beginSocketReadingLoop()` — lee el socket y, en éxito, actualiza el título de
  la barra con el formato:

  ```
  <pulsations_current> / <pulsation_average>AVG / <pulsations_total>T
  ```

  Luego se reprograma a sí mismo cada **1 segundo** (`asyncAfter`), creando un
  sondeo continuo.
- `applicationDidFinishLaunching` — inicia el sondeo.
- `applicationWillTerminate` — apaga el `NIOTSEventLoopGroup` de forma ordenada.

## Instalación y arranque

Según el README:

1. Arrastrar `KeyCounterBar.app` (incluida) a `Aplicaciones`, o compilar desde
   el proyecto Xcode.
2. Añadirla a los **elementos de inicio de sesión** para que cargue tras cada
   reinicio.
3. Requiere que el proceso Python de KeyCounter esté corriendo y haya creado el
   socket UNIX.

## Interacciones

- **Depende de:** el socket UNIX creado por `Models/Socket.py`.
- **Independiente de:** el resto de la lógica Python (solo consume el JSON del
  socket).

## Observaciones (ver documento 13)

- La **captura de teclado en macOS lleva años funcionando de forma estable**;
  esta app es la prueba de ello.
- ⚠️ Lo que sí falla en macOS es la **detección de clicks de ratón**, y es un
  problema de la librería `mouse` y de los permisos del sistema, **no de esta
  app Swift** ni de la lógica de KeyCounter.
- Sondeo por *polling* cada 1 s: podría migrarse a lectura por eventos/push.
- Archivos de usuario de Xcode (`xcuserdata/`) versionados por descuido; ver
  [17. Archivos y control de versiones](17-archivos-y-control-de-versiones.md).
- El binario `.app` está versionado **a propósito** (el README ofrece
  arrastrarlo a Aplicaciones sin compilar), así que se mantiene.
