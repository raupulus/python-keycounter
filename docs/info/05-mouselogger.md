# 05 — `MouseLogger` (estadísticas de ratón)

**Archivo:** `Models/MouseLogger.py`

## Objetivo del módulo

Equivalente a `KeyboardLogger` pero para el **ratón**. Mantiene el estado de
clicks por botón, la agrupación en rachas y define el modelo de tabla `mouse`.
Solo se usa si `MOUSE_ENABLED=True`. Recibe llamadas desde
`Keylogger.callback_mouse`.

## Identidad y destino de datos

- `tablename = 'mouse'`
- `name = 'Mouse'`
- `api_path = '/keycounter/v1/mouse/store'`
- `DEVICE_ID = os.getenv("DEVICE_ID")`

## Parámetros del algoritmo

- `COMBO_RESET = 15` — segundos que cierran una racha.
- `COMBO_MAP` — declarado igual que en teclado, **sin uso** en el cálculo
  actual (el ratón no calcula `score`). Ver documento 13.

## Estado

- `click_left`, `click_right`, `click_middle` — clicks por botón en la racha
  actual.
- `current_clicks` — total de clicks de la racha actual.
- `current_start_at` — inicio de la racha actual.
- `last_pulsation_at` — momento del último click.
- `total_clicks` — total de clicks acumulados entre rachas.
- `pulsations_hight` / `pulsations_hight_at` — récord de clicks en una racha
  (nótese la grafía `hight`).
- `current_day_start` / `current_day_end` — límites del día.
- `spurts = {}` — rachas cerradas pendientes de guardar.

## Constructor `__init__(has_debug=False)`

Inicializa `last_pulsation_at` y `current_start_at` con la hora UTC actual y fija
los límites del día (00:00 y 23:59:59.999999).

## Métodos

### `reset_global_counter()`

Reinicia el récord de racha (`pulsations_hight`) y su timestamp. Es más simple
que el de teclado (el ratón guarda menos métricas globales).

### `add_old_streak()`

Serializa la racha actual a `spurts`, indexada por `last_pulsation_at`, con:

`start_at`, `end_at`, `clicks_left`, `clicks_right`, `clicks_middle`,
`total_clicks` (usa `current_clicks`), `clicks_average`, `weekday`,
`hardware_device_id`.

### `get_clicks_average()`

Media de clicks por minuto de la racha actual:

```
(current_clicks / duración_en_segundos) * 60
```

redondeado a 2 decimales; 0.00 si no hay duración/clicks.

### `tablemodel()`

Define el esquema de la tabla `mouse` como diccionario `columna → {type,
params, others}`. Columnas:

`start_at` (DateTime), `end_at` (DateTime), `clicks_left` (Numeric),
`clicks_right` (Numeric), `clicks_middle` (Numeric), `total_clicks` (Numeric),
`clicks_average` (String), `weekday` (Numeric), `hardware_device_id` (Numeric),
`created_at` (DateTime, `default=datetime.utcnow`).

## Diferencias frente a `KeyboardLogger`

- No calcula puntuación (`score`/combos): solo cuenta clicks.
- El incremento de contadores lo hace directamente `Keylogger.callback_mouse`
  (no hay un `increase_pulsation` propio del ratón).
- Guarda el desglose por botón (izq./centro/der.).

## Interacciones

- **Usado por:** `Keylogger` (captura de clicks), `main.py` vía `DbConnection`
  (`spurts` y `tablemodel`).

## Notas para mejoras (ver documento 13)

- ⚠️ **En macOS la detección de clicks falla en la versión actual** (problema
  conocido; ver documento 13).
- `datetime.utcnow()` obsoleto.
- Grafía `pulsations_hight` (debería ser `height`/`high`); mantener por
  compatibilidad o migrar con cuidado.
- Estado a nivel de clase; falta tipado.
