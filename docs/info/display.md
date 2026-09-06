# `display`

> Ruta real en el repositorio: `Models/Display.py`

## Qué hace y qué NO hace
Puente entre las estadísticas del keylogger y la pantalla LCD serie. Extiende
[lcd-uart](lcd-uart.md) y traduce el diccionario de estadísticas en comandos de
dibujo (`DCV32`, `DCV16`, `CLR`, `SBC`…) que la pantalla entiende.

**NO** habla directamente con el puerto serie (eso es de `LCDUart`) ni calcula
estadísticas.

## Modelo de datos
No define esquema. Consume el dict de `KeyboardLogger.statistics()`
(`session` + `streak`). Guarda `last_pulsations_current` para detectar nuevas
rachas y limpiar la pantalla.

## Flujos principales
1. `update_keycounter(data)` — si el puerto no está abierto, reinicia la pantalla;
   compone la pantalla con pulsaciones actuales, especiales, media, score de
   racha y totales, y la envía por `write`. Limpia (`CLR`) cuando empieza una
   racha nueva.
2. `configurations()` — extiende la de `LCDUart` aplicando color de fondo.
3. `update_streak`, `update_session` — placeholders (`pass`).
4. `debug()` — secuencia de prueba de la pantalla (encender/apagar, brillo,
   píxeles).

## Puntos de entrada
- `Display(port, baudrate, orientation, has_debug)`.
- `update_keycounter(data)` — llamado por [keylogger](keylogger.md) vía
  `send_to_display`.

## Dependencias en ambos sentidos
- **Depende de:** [lcd-uart](lcd-uart.md) (clase base), `serial` (indirecto).
- **Le depende:** [main](main.md) (lo instancia si `SERIAL_DISPLAY_ENABLED`),
  [keylogger](keylogger.md) (lo usa como `display`).

## Configuración
| Variable | Defecto | Efecto |
|----------|---------|--------|
| `SERIAL_DISPLAY_ENABLED` | `False` | Sin esto, `main` no crea la pantalla. |
| `SERIAL_PORT` / `SERIAL_BAUDRATE` / `DISPLAY_ORIENTATION` | ver [lcd-uart](lcd-uart.md) | Parámetros del puerto y orientación. |

Atributos de clase: `color = "2"`, `background = "0"`.

## Trampas conocidas
- El protocolo de comandos es específico de la pantalla LCD concreta del autor;
  para otra pantalla hay que reescribir esta clase o `LCDUart` manteniendo los
  nombres de método.
- Sólo la última orden debe terminar en `\r\n`.

## Tests que lo cubren
Ninguno ⚠️.

## Pendiente real
- `TODO` en el código: implementar `update_keycounter` de forma completa y la
  reinicialización periódica de la pantalla.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
