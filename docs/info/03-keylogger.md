# 03 — `Keylogger` (orquestador de captura)

**Archivo:** `Models/Keylogger.py`

## Objetivo del módulo

Es el **orquestador de la captura**. Engancha las librerías de bajo nivel
(`keyboard` y, opcionalmente, `mouse`), traduce cada evento a una actualización
de estadísticas y reparte los datos hacia las salidas (pantalla, socket,
WebSocket). También vigila cambios en los dispositivos de entrada para
resincronizar la escucha del teclado.

Contiene las dos instancias de estadística: `model_keyboard` (`KeyboardLogger`)
y `model_mouse` (`MouseLogger`).

## Importación condicional del ratón

```python
if os.getenv('MOUSE_ENABLED') == 'True':
    import mouse
```

La librería `mouse` solo se importa si el ratón está habilitado, evitando la
dependencia cuando no se usa.

## Atributos de clase relevantes

- `model_keyboard`, `model_mouse` — modelos de estadística.
- `reboot` — flag que indica que se detectó un cambio de dispositivos.
- `devices` — cadena con los dispositivos de entrada detectados (para comparar).
- `is_down` — diccionario que marca qué teclas están pulsadas (evita contar el
  autorepeat de una tecla mantenida).
- `has_debug`, `MOUSE_ENABLED`, `display`.
- `KEYS_MAP` — traducción de nombres de teclas especiales a etiquetas legibles
  (`space`→`" "`, `enter`→`"(ENTER)"`, `ctrl`→`"(CTRL)"`, teclas de función,
  navegación, etc.). Se usa tanto para presentación como para decidir si una
  tecla es "especial".

## Constructor `__init__(display, has_debug, mouse_enabled, model_keyboard, model_mouse)`

1. Guarda `display`, `has_debug`, `MOUSE_ENABLED`.
2. Instancia `model_keyboard` (reutiliza el recibido o crea `KeyboardLogger()`).
3. Instancia `model_mouse` si el ratón está activo (reutiliza o crea
   `MouseLogger()`).
4. Lee los dispositivos conectados con `read_devices_by_id()`.
5. Arranca **dos hilos**:
   - `start_read_keyloggers_callback` — engancha los callbacks.
   - `reload_keycounter_on_new_device` — vigila cambios de dispositivos.

## Métodos

### `read_devices_by_id()`

Devuelve la lista de dispositivos de entrada del sistema mediante un subproceso
shell:

```
ls /dev/input/by-id/; cat /proc/bus/input/devices | grep -v -i -E "virtual" | grep -E "keyboard|mouse"
```

Sirve para detectar cuándo se conecta/desconecta un teclado o ratón. En caso de
error espera 10 s y devuelve cadena vacía.

⚠️ Es específico de Linux (`/dev/input`, `/proc/bus/input/devices`). En macOS
no aplica. Ver documento 13.

### `start_read_keyloggers_callback()`

Engancha los callbacks de captura:

- `keyboard.hook(self.callback_keyboard)` para todas las teclas.
- Si `MOUSE_ENABLED`: `mouse.on_click`, `mouse.on_right_click`,
  `mouse.on_middle_click` apuntando a `callback_mouse`.

### `reload_keycounter_on_new_device()`

Bucle infinito que cada ~3 s compara los dispositivos actuales con los
almacenados. Si cambian:

1. Actualiza `self.devices` y pone `reboot = True`.
2. Reconstruye internamente el dispositivo de teclado de la librería:
   `keyboard._nixkeyboard.device = None`, `build_device()`, `build_tables()`.
3. Si hay dispositivo, recrea el listener: `keyboard._listener =
   keyboard._KeyboardListener()`.

Esto permite que, al conectar un teclado USB nuevo, la captura vuelva a
funcionar sin reiniciar el proceso.

⚠️ Accede a **internals privados** de la librería `keyboard`
(`_nixkeyboard`, `_listener`), lo que la acopla a una versión concreta y es una
de las causas de rotura al actualizar. Contiene un `TODO` para reiniciar también
el ratón. Ver documento 13.

### `callback_mouse(button)`

Se ejecuta en cada click. Delegando en `model_mouse`:

1. Si desde el último click han pasado más de `COMBO_RESET` segundos, cierra la
   racha (`add_old_streak()`) y reinicia contadores de la racha actual.
2. Incrementa el contador del botón (`click_left`/`click_middle`/`click_right`).
3. Actualiza `last_pulsation_at`, `current_clicks`, `total_clicks`.
4. Registra el récord de clicks de racha si procede.
5. Si se cruzó el fin de día, lanza `reset_global_counter` en un hilo.

### `callback_keyboard(event)`

Se ejecuta en cada evento de teclado (`up`/`down`). Lógica:

1. Descarta eventos `unknown` (incluye eventos de ratón que llegan por aquí).
2. Traduce el nombre con `KEYS_MAP` y determina si es **tecla especial**.
3. Usa `is_down` para **contar solo la primera pulsación** de una tecla
   mantenida (ignora autorepeat): marca al `down` y limpia al `up`.
4. En el `down`, incrementa la pulsación en `model_keyboard`
   (`increase_pulsation(True/False)` según sea especial).
5. Si la tecla es ENTER, sustituye por `"\n"` para la salida de debug.
6. Si `has_debug`, imprime el estado con `model_keyboard.debug(...)`.
7. Lanza `send_to_display` en un hilo para refrescar la pantalla.

### `send_to_display()`

Envía los datos actuales a la pantalla física (si existe):

- Si no hay `display`, retorna `False`.
- Toma `model_keyboard.statistics()` y llama, en un hilo, a
  `display.update_keycounter(data)`.

El contrato es que cualquier pantalla debe exponer `update_keycounter(data)`.

### `set_socket(socket)` / `set_client_display_websocket(client)`

Inyectan en `model_keyboard` el socket UNIX y el cliente WebSocket, para que el
propio modelo empuje actualizaciones cuando cambian las pulsaciones.

## Interacciones

- **Depende de:** `KeyboardLogger`, `MouseLogger`, librerías `keyboard`/`mouse`,
  utilidades del SO (`subprocess`).
- **Usado por:** `main.py` (lo crea y le inyecta socket/WebSocket), `Socket` y
  `ClientDisplayWebsocket` (leen sus modelos).

## Notas para mejoras (ver documento 13)

- Acoplamiento a internals privados de `keyboard`.
- Detección de dispositivos solo válida en Linux.
- `datetime.utcnow()` está obsoleto en Python moderno.
- Uso de `_thread` en lugar de `threading`.
