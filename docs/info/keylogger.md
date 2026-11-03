# `keylogger`

> Ruta real en el repositorio: `Models/Keylogger.py`

## Qué hace y qué NO hace
Captura en tiempo real las pulsaciones de teclado y (opcionalmente) los clicks
del ratón. En **Linux** usa hooks de las librerías `keyboard` y `mouse` en hilos
independientes; en **macOS** usa [mac-keyboard-tap](mac-keyboard-tap.md) (event
tap pasivo nativo) para teclado y, si `MOUSE_ENABLED`, también para los clics
(la librería `mouse` no tiene backend macOS y no se importa). Traduce teclas especiales a texto legible, filtra
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
- `reboot: bool` — se activa al detectar cambios de dispositivos (sólo Linux).
- `keyboard_tap: MacKeyboardTap | None` — captura nativa en macOS (teclado y,
  opcionalmente, clics).

## Flujos principales
1. `__init__` — guarda pantalla/debug/flag de ratón, instancia (o reutiliza) los
   modelos y arranca la captura:
   - macOS: crea y arranca `MacKeyboardTap(self.callback_keyboard,
     mouse_callback=self.callback_mouse si MOUSE_ENABLED)`.
   - Linux: lee dispositivos y lanza dos hilos:
     `start_read_keyloggers_callback` y `reload_keycounter_on_new_device`.
2. `callback_keyboard(event)` — filtra `unknown`, gestiona `is_down`, cuenta la
   pulsación como especial o normal en el modelo (`increase_pulsation`) y, sólo
   si hay pantalla, lanza `send_to_display` en un hilo.
2b. `stop()` — libera la captura (en macOS desactiva e invalida el event tap).
   La llama `main.shutdown` antes de terminar el proceso.
3. `callback_mouse(button)` — agrupa clicks en rachas por `COMBO_RESET`, actualiza
   contadores del modelo de ratón y récords.
4. `reload_keycounter_on_new_device()` — sólo Linux; cada ~3 s relee dispositivos; si cambian,
   reconstruye el listener de la librería `keyboard` (acceso a internos
   `keyboard._nixkeyboard`).
5. `send_to_display()` — obtiene `model_keyboard.statistics()` y llama a
   `display.update_keycounter(data)` en un hilo.

## Puntos de entrada
- `Keylogger(display, has_debug, mouse_enabled, model_keyboard, model_mouse)`.
- `stop()` — libera la captura de teclado.
- `set_socket(socket)` — asocia el socket al modelo de teclado.
- `set_client_display_websocket(client)` — asocia el cliente websocket al modelo.

## Dependencias en ambos sentidos
- **Depende de:** Linux: `keyboard`, `mouse` (import condicionado a
  `MOUSE_ENABLED`), `subprocess`. macOS: `Models.MacKeyboardTap`. Ambos:
  `Models.KeyboardLogger`, `Models.MouseLogger`.
- **Le depende:** [main](main.md), [socket](socket.md) (recibe el keylogger),
  [client-display-websocket](client-display-websocket.md).

## Configuración
| Variable | Defecto | Efecto |
|----------|---------|--------|
| `MOUSE_ENABLED` | `False` | Registra clicks: en Linux con `mouse`, en macOS con el tap nativo. |

## Trampas conocidas
- `reload_keycounter_on_new_device` accede a atributos privados de `keyboard`
  (`_nixkeyboard`, `_KeyboardListener`); depende de la implementación de la
  librería y es específico de Linux (`/dev/input`, `/proc/bus/input/devices`).
- `read_devices_by_id` ejecuta el subproceso shell:
  ```bash
  ls /dev/input/by-id/; cat /proc/bus/input/devices | grep -v -i -E "virtual" | grep -E "keyboard|mouse"
  ```
  Es específico de Linux; en macOS ya no se ejecuta.
- En `callback_keyboard`, `is_down` filtra la autorepetición de teclas mantenidas: marca `True` al recibir evento `down` y lo elimina al recibir `up`, contabilizando únicamente la primera pulsación.
- Linux requiere **root** para capturar teclado. macOS requiere permiso de
  «Monitorización de entrada» (root sigue siendo necesario por el socket).
- En macOS **no** volver a usar la librería `keyboard`: su tap síncrono puede
  colgar WindowServer y cerrar la sesión (ver [decisiones-tecnicas.md](decisiones-tecnicas.md), D7).
- Uso intensivo de `start_new_thread` sin gestión de ciclo de vida de los hilos.

## Tests que lo cubren
Ninguno ⚠️.

## Pendiente real
- `TODO` en el código: reiniciar el hook del ratón al detectar nuevos
  dispositivos (`reload_keycounter_on_new_device`).

---
> Creado: 2026-09-06 · Última revisión: 2026-11-03
