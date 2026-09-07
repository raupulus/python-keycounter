# `mouse-logger`

> Ruta real en el repositorio: `Models/MouseLogger.py`

## Qué hace y qué NO hace
Modelo de datos y estadísticas del ratón. Cuenta clicks por botón (izquierdo,
central, derecho) agrupados en rachas, calcula la media por minuto, define el
esquema de tabla `mouse` y permite sincronizar los totales acumulados del día
desde la API (`apply_initial_summary`). Sólo se instancia si `MOUSE_ENABLED`.

**NO** captura eventos (los recibe desde [keylogger](keylogger.md)) ni persiste
datos.

## Modelo de datos
Rachas en `spurts: dict` (clave = timestamp de última pulsación) con los campos
de `tablemodel()`:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `start_at` | DateTime | Inicio de la racha. |
| `end_at` | DateTime | Última pulsación. |
| `clicks_left` | Numeric | Clicks del botón izquierdo. |
| `clicks_right` | Numeric | Clicks del botón derecho. |
| `clicks_middle` | Numeric | Clicks del botón central. |
| `total_clicks` | Numeric | Clicks totales de la racha (desde `current_clicks`). |
| `clicks_average` | String | Media de clicks por minuto. |
| `weekday` | Numeric | Día de la semana. |
| `hardware_device_id` | Numeric | `DEVICE_ID`. |
| `created_at` | DateTime | Timestamp de creación (default). |

## Flujos principales
1. `add_old_streak()` — vuelca la racha actual a `spurts`.
2. `get_clicks_average()` — media de clicks por minuto de la racha.
3. `reset_global_counter()` — reinicia el récord de racha.
4. `tablemodel()` — esquema de columnas para la DB.
5. `apply_initial_summary(summary_data)` — suma `clicks_total` al contador local
   acumulado `total_clicks` y actualiza el récord de racha `pulsations_hight = max(local, clicks_high)`
   a partir de los datos recibidos de `/keycounter/summary`.

La lógica de conteo (incremento por botón, apertura/cierre de racha por
`COMBO_RESET`) vive en `Keylogger.callback_mouse`, que actúa sobre los atributos
de este modelo.

## Puntos de entrada
- `MouseLogger(has_debug)`.
- `add_old_streak`, `get_clicks_average`, `reset_global_counter`, `tablemodel`,
  `apply_initial_summary`.

## Dependencias en ambos sentidos
- **Depende de:** `datetime`, `os` (lee `DEVICE_ID`).
- **Le depende:** [keylogger](keylogger.md) (lo alimenta), [main](main.md),
  [db-connection](db-connection.md) (vía `tablemodel`).

## Configuración
| Variable | Defecto | Efecto |
|----------|---------|--------|
| `DEVICE_ID` | `None` | Se guarda en cada racha. |
| `COMBO_RESET` (constante) | `15` s | Agrupa clicks en una racha (usado por el callback). |

## Trampas conocidas
- `spurts` es atributo de clase mutable (compartido si hubiera varias instancias).
- `COMBO_MAP` declarado pero no utilizado.
- En [main](main.md) sólo se guarda la racha si `total_clicks > 1`.
- `tablename = 'mouse'`, `api_path = '/keycounter/mouse-sessions'`.
- **Sin `score`**: a diferencia de teclado, la tabla `keycounter_mouse` en la API
  V2 no tiene columna `score` (`MouseResource` no lo incluye). Este modelo no lo
  genera ni lo persiste.
- **Día de la semana (`weekday`)**: `datetime.today().weekday()` de Python devuelve
  `0` para lunes y `6` para domingo, mientras que el contrato API V2 de Laravel
  documenta `0 = domingo`.
- `duration` y `user_id` no se incluyen en el modelo ni se envían a la API: el
  servidor los calcula/asigna automáticamente.

## Tests que lo cubren
Ninguno ⚠️.

## Pendiente real
- Alinear el cálculo de `weekday` con la convención de la API V2 (0 = domingo).

---
> Creado: 2026-09-06 · Última revisión: 2026-09-07
