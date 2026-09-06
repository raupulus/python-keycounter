# `keylogger`

> Ruta real en el repositorio: `Models/Keylogger.py`

## Qué hace y qué NO hace
Captura en tiempo real las pulsaciones de teclado y (opcionalmente) los clicks
del ratón mediante hooks de las librerías `keyboard` y `mouse`, ejecutados en
hilos independientes. Traduce teclas especiales a texto legible, filtra
repeticiones por tecla mantenida y delega el conteo/estadística en los modelos
[keyboard-logger](keyboard-logger.md) y [mouse-logger](mouse-logger.md).

**NO** persiste datos ni los sube a la API; sólo alimenta los modelos y notifica
a la pantalla y al socket.

## Modelo de datos
- `model_keyboard: KeyboardLogger` y `model_mouse: MouseLogger` (este último sólo
  si `MOUSE_ENABLED`).
- `is_down: dict` — marca qué teclas están pulsadas para ignorar auto-repetición.
- `KEYS_MAP: dict` — traducción de nombres de tecla a etiquetas imprimibles.
- `devices` — salida de la lectura de dispositivos de entrada del sistema.
- `reboot: bool` — se activa al detectar cambios de dispositivos.

## Flujos principales
1. `__init__` — guarda pantalla/debug/flag de ratón, instancia (o reutiliza) los
   modelos, lee dispositivos y lanza dos hilos:
   `start_read_keyloggers_callback` y `reload_keycounter_on_new_device`.
2. `callback_keyboard(event)` — filtra `unknown`, gestiona `is_down`, cuenta la
   pulsación como especial o normal en el modelo (`increase_pulsation`) y lanza
   `send_to_display` en un hilo.
3. `callback_mouse(button)` — agrupa clicks en rachas por `COMBO_RESET`, actualiza
   contadores del modelo de ratón y récords.
4. `reload_keycounter_on_new_device()` — cada ~3 s relee dispositivos; si cambian,
   reconstruye el listener de la librería `keyboard` (acceso a internos
   `keyboard._nixkeyboard`).
5. `send_to_display()` — obtiene `model_keyboard.statistics()` y llama a
   `display.update_keycounter(data)` en un hilo.

## Puntos de entrada
- `Keylogger(display, has_debug, mouse_enabled, model_keyboard, model_mouse)`.
- `set_socket(socket)` — asocia el socket al modelo de teclado.
- `set_client_display_websocket(client)` — asocia el cliente websocket al modelo.

## Dependencias en ambos sentidos
- **Depende de:** `keyboard`, `mouse` (import condicionado a `MOUSE_ENABLED`),
  `subprocess`, `Models.KeyboardLogger`, `Models.MouseLogger`.
- **Le depende:** [main](main.md), [socket](socket.md) (recibe el keylogger),
  [client-display-websocket](client-display-websocket.md).

## Configuración
| Variable | Defecto | Efecto |
|----------|---------|--------|
| `MOUSE_ENABLED` | `False` | Importa `mouse` y registra clicks. |

## Trampas conocidas
- `reload_keycounter_on_new_device` accede a atributos privados de `keyboard`
  (`_nixkeyboard`, `_KeyboardListener`); depende de la implementación de la
  librería y es específico de Linux (`/dev/input`, `/proc/bus/input/devices`).
- `read_devices_by_id` usa comandos Linux; en macOS no devuelve dispositivos.
- Requiere ejecutarse como **root** para capturar teclado.
- Uso intensivo de `start_new_thread` sin gestión de ciclo de vida de los hilos.

## Tests que lo cubren
Ninguno ⚠️.

## Pendiente real
- `TODO` en el código: reiniciar el hook del ratón al detectar nuevos
  dispositivos (`reload_keycounter_on_new_device`).

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
