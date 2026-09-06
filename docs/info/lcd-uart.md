# `lcd-uart`

> Ruta real en el repositorio: `Models/LCDUart.py`

## Qué hace y qué NO hace
Driver de bajo nivel de la pantalla LCD por UART/serie usando `pyserial`. Abre el
puerto, configura orientación y baudios, y ofrece primitivas para escribir
comandos en bruto, encender/apagar, ajustar brillo y (parcialmente) mostrar
imágenes.

**NO** conoce las estadísticas del keycounter; eso lo añade [display](display.md),
que hereda de esta clase.

## Modelo de datos
- `ser` — instancia `serial.Serial` o `None`.
- `colors: dict` — mapa nombre → código de color de la pantalla.
- Dimensiones según orientación (`176x220` vertical / `220x176` horizontal).

## Flujos principales
1. `__init__(port, baudrate, timeout, orientation, has_debug)` — si no hay puerto
   devuelve `None`; si `initialize()` falla, `None`.
2. `initialize()` — comprueba que el puerto existe (`ls`), lo abre, envía
   `RESET;BPS;BL;CLR`, fija orientación y aplica `configurations()`.
3. `write(command)` — escribe bytes si el puerto está abierto; si no, espera y
   reintenta `initialize`.
4. `on`/`off`/`set_brigthness`/`set_screen_orientation`/`get_screen_size`.

## Puntos de entrada
- `LCDUart(...)` (normalmente vía la subclase `Display`).
- `write`, `initialize`, `on`, `off`, `set_screen_orientation`,
  `set_brigthness`, `get_screen_size`, `get_screen_orientation`.

## Dependencias en ambos sentidos
- **Depende de:** `serial` (pyserial), `os`, `time`.
- **Le depende:** [display](display.md) (subclase).

## Configuración
| Parámetro (constructor) | Defecto | Efecto |
|-------------------------|---------|--------|
| `port` | `/dev/ttyUSB0` | Puerto serie. |
| `baudrate` | `115200` | Velocidad. |
| `timeout` | `1` | Timeout de lectura serie. |
| `orientation` | `vertical` | Orientación inicial. |

Valores reales inyectados desde [main](main.md) vía `SERIAL_PORT`,
`SERIAL_BAUDRATE`, `DISPLAY_ORIENTATION`.

## Trampas conocidas
- Comprueba la existencia del puerto con `ls`/`os.popen`, dependiente de Linux.
- Ante errores de puerto hace `sleep` y reintenta; no lanza excepciones.
- `set_brigthness` compone el comando sin `encoding` en `bytes(...)`, lo que puede
  fallar; usar con cuidado.
- `show_image` está mayormente comentado (no funcional).

## Tests que lo cubren
Ninguno ⚠️.

## Pendiente real
- `show_image` sin implementar (carga de imagen en flash de la pantalla).

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
