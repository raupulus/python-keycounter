# `keyboard-logger`

> Ruta real en el repositorio: `Models/KeyboardLogger.py`

## Qué hace y qué NO hace
Modelo de datos y estadísticas del teclado. Contabiliza pulsaciones agrupadas en
«rachas» (spurts), calcula puntuación de combos, mantiene contadores de sesión y
de racha actual, y define el esquema de tabla que persiste
[db-connection](db-connection.md). Reinicia los contadores globales al cambiar de
día y permite aplicar los totales acumulados del día desde la API
(`apply_initial_summary`).

**NO** captura eventos (eso lo hace [keylogger](keylogger.md)) ni persiste nada.

## Modelo de datos
Rachas acumuladas en `spurts: dict` con clave = timestamp de última pulsación y
valor con los campos que devuelve `tablemodel()`:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `start_at` | DateTime | Inicio de la racha. |
| `end_at` | DateTime | Fin (última pulsación) de la racha. |
| `pulsations` | Numeric | Pulsaciones de la racha. |
| `pulsations_special_keys` | Numeric | Pulsaciones de teclas especiales. |
| `pulsation_average` | String | Media de pulsaciones por minuto. |
| `score` | Numeric | Puntuación de combo de la racha. |
| `weekday` | Numeric | Día de la semana. |
| `hardware_device_id` | Numeric | `DEVICE_ID` del equipo. |
| `created_at` | DateTime | Timestamp de creación (default). |

Además mantiene contadores de sesión (`pulsations_total`, `combo_score`,
`combo_score_high`, `pulsation_high`…) y de racha actual (`pulsations_current`,
`combo_score_current`…).

## Flujos principales
1. `increase_pulsation(special_key)` — suma pulsación; si pasó más de
   `COMBO_RESET` (15 s) desde la última, cierra la racha anterior
   (`add_old_streak`) y abre una nueva; recalcula combo (`set_combo`), récords y
   dispara `reset_global_counter` al cambiar de día. Notifica al `socket` y al
   `client_display_websocket` si están asociados.
2. `set_combo(timestamp, reset_sesion)` — algoritmo de combos. Si no es reseteo de racha, calcula puntuación candidata `new_combo_score = int(self.pulsations_current * 0.15)` y la suma al total si se cumple la condición determinista:
   ```python
   (int((self.pulsations_current * 2.7) * ((self.pulsations_current + 1) * 3.4)) % 5) == 0
   ```
3. `add_old_streak()` — vuelca la racha actual a `spurts`.
4. `statistics()` / `statistics_session()` / `statistics_streak()` — datos para
   pantalla y socket.
5. `tablemodel()` — esquema de columnas para la DB.
6. `apply_initial_summary(summary_data)` — suma las estadísticas acumuladas
   recibidas de la API (`pulsations_total`, `pulsations_total_special_keys`) sobre
   los contadores actuales y actualiza récords del periodo (`combo_score_high`,
   `pulsation_high`, `combo_score`). Notifica a `socket` y
   `client_display_websocket`.

## Puntos de entrada
- `KeyboardLogger(has_debug)`.
- `increase_pulsation`, `add_old_streak`, `statistics`, `tablemodel`,
  `reset_global_counter`, `apply_initial_summary`.
- Atributos inyectables: `socket`, `client_display_websocket`.

## Dependencias en ambos sentidos
- **Depende de:** `datetime`, `os` (lee `DEVICE_ID`,
  `SEND_DATA_TO_WEBSOCKET_SERVER`).
- **Le depende:** [keylogger](keylogger.md), [main](main.md),
  [socket](socket.md), [db-connection](db-connection.md) (vía `tablemodel`).

## Configuración
| Variable | Defecto | Efecto |
|----------|---------|--------|
| `DEVICE_ID` | `None` | Se guarda en cada racha (`hardware_device_id`). |
| `SEND_DATA_TO_WEBSOCKET_SERVER` | `False` | Activa las notificaciones al cliente websocket. |
| `COMBO_RESET` (constante) | `15` s | Tiempo que agrupa pulsaciones en una racha. |

## Trampas conocidas
- Varios atributos se declaran a nivel de clase (`spurts`, contadores); al ser un
  único proceso con una instancia funciona, pero **`spurts` es mutable de clase**
  y sería compartido entre instancias.
- `COMBO_MAP` (tabla de 1→0.01 hasta 10→1.00) está declarada como constante pero no se usa en `set_combo` (el algoritmo usa la fórmula determinista indicada arriba).
- `tablename = 'keyboard'`, `api_path = '/keycounter/keyboard-sessions'`.
- **Día de la semana (`weekday`)**: Se calcula con `(datetime.today().weekday() + 1) % 7`
  para alinearse con la API V2 (0 = domingo, 1 = lunes).
- `duration` y `user_id` no se incluyen en el modelo ni se envían a la API: el
  servidor los calcula/asigna automáticamente.

## Tests que lo cubren
Ninguno ⚠️.

## Pendiente real
- Aclarar el uso previsto de `COMBO_MAP` (código muerto o pendiente de integrar).

---
> Creado: 2026-09-06 · Última revisión: 2026-09-07
