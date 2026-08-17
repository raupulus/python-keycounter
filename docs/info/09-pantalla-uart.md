# 09 — Pantalla UART (`Display` y `LCDUart`)

**Archivos:** `Models/Display.py` (puente) y `Models/LCDUart.py` (driver)

## Objetivo del módulo

Mostrar las estadísticas en una **pantalla física** conectada por **puerto serie
(UART)**. Solo se activa con `SERIAL_DISPLAY_ENABLED=True`. Son dos capas:

- **`LCDUart`** — driver de bajo nivel: abre el puerto, envía comandos en bruto
  y gestiona orientación, brillo, encendido/apagado.
- **`Display`** — extiende `LCDUart` y traduce los datos de estadística al
  protocolo concreto de la pantalla (comandos de dibujo).

Esta separación permite portar el proyecto a **otra pantalla** reescribiendo
`LCDUart` (o `Display`) y manteniendo los mismos nombres de método.

## Hardware objetivo

Una pantalla serie económica (modelo "spotpear"-like) que acepta comandos de
texto tipo `DCV32(x, y, texto, color);`, `CLR(color);`, `DIR(0/1);`,
`BL(brillo);`, `LCDON(0/1);`, etc. Resolución 176×220 (vertical) o 220×176
(horizontal).

## `LCDUart` (driver)

### Atributos

- `port` (`/dev/ttyUSB0` por defecto), `baudrate` (115200), `timeout`,
  `orientation` (`vertical`), `width`/`height`.
- `ser` — objeto `serial.Serial`.
- `colors` — mapa nombre→código (0..15).

### Constructor `__init__(port, baudrate, timeout, orientation, has_debug)`

Si no hay puerto, retorna sin inicializar. Si lo hay, guarda parámetros y llama
a `initialize()`.

### `initialize()`

1. Comprueba que el puerto existe (`ls <port>`).
2. Cierra el puerto si estaba abierto.
3. Abre `serial.Serial(port, baudrate, timeout)`.
4. Envía la secuencia de arranque `RESET;BPS(115200);BL(0);CLR(0);`.
5. Aplica orientación (`set_screen_orientation`) y `configurations()`.

### Otros métodos

- `configurations()` — punto de extensión (lo sobrescribe `Display`).
- `stop()` — cierra el puerto.
- `on()` / `off()` — enciende/apaga la pantalla (`LCDON(1/0)`).
- `write(command)` — envía bytes al puerto; si está cerrado, espera y
  reinicializa.
- `get_screen_size()` / `get_screen_orientation()`.
- `set_screen_orientation(orientation)` — `vertical` (176×220, `DIR(0)`) u
  `horizontal` (220×176, `DIR(1)`).
- `set_brigthness(value)` — brillo 0..255 (255 = apagada). ⚠️ grafía
  `brigthness`; además construye el comando `BL(...` sin cerrar el paréntesis.
  Ver documento 13.
- `show_image(path)` — **incompleto**: el cuerpo real está comentado (requiere
  cargar la imagen en flash). Sin uso.

## `Display` (puente)

Extiende `LCDUart` y añade la lógica de presentación.

### Atributos

- `last_pulsations_current` — para detectar el inicio de una racha nueva y
  limpiar la pantalla.
- `color = "2"` (verde), `background = "0"` (negro).

### `configurations()`

Llama a la del padre y limpia el fondo con `CLR(<background>);`.

### `update_keycounter(data)`

Método principal, invocado desde `Keylogger.send_to_display`. Recibe el
diccionario `statistics()` (`session` + `streak`):

1. Si el puerto no está abierto, intenta `initialize()` y sale.
2. Compone las líneas de la pantalla con comandos `DCV32/DCV16`:
   - `KEYS:` pulsaciones de la racha
   - `SPK:` teclas especiales de la racha
   - `AVG:` velocidad media
   - `SCORE:` puntuación de la racha
   - `T.KEYS:` pulsaciones totales de la sesión
   - `T.SCORE:` puntuación total
3. Prefija `SBC(<background>);`.
4. Si la racha actual es menor que la anterior (empezó una nueva), limpia con
   `CLR(<background>);`.
5. Escribe todo por el puerto y guarda `last_pulsations_current`.
6. Llama a `update_streak()` y `update_session()` (hoy vacíos, `pass`).

### `debug()`

Secuencia de prueba de la pantalla (limpiar, apagar/encender, variar brillo,
dibujar puntos). Solo para depuración manual.

## Renombrado del puerto (problema conocido)

Al suspender o reconectar la pantalla, el sistema puede renombrar la interfaz
(`/dev/ttyUSB0` → otro), y deja de funcionar. Solución documentada en el README:
crear una **regla udev** que enlace un `SYMLINK` estable (p. ej.
`ttyUSB_KEYCOUNTER`) según `idVendor`/`idProduct`/`serial`, y apuntar
`SERIAL_PORT` a ese enlace.

## Interacciones

- **Depende de:** `pyserial` (`serial`), `os`, `time`.
- **Usado por:** `main.py` (crea `Display` si procede) y `Keylogger`
  (`update_keycounter`).

## Notas para mejoras (ver documento 13)

- `set_brigthness`: comando `BL(` mal cerrado y grafía del nombre.
- `show_image` incompleto.
- Comprobación de puerto por `ls`/`os.popen` (frágil; mejor usar `pyserial`
  directamente o `pathlib`).
- Acoplado al protocolo de una pantalla concreta; documentar el contrato mínimo
  (`update_keycounter(data)`) para otras pantallas.
- Falta tipado.
