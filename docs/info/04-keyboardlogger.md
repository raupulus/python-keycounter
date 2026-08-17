# 04 — `KeyboardLogger` (estadísticas y puntuación de teclado)

**Archivo:** `Models/KeyboardLogger.py`

## Objetivo del módulo

Mantiene **todo el estado estadístico del teclado** y la lógica de agrupación en
rachas y de puntuación (combos). No captura eventos por sí mismo: recibe
llamadas desde `Keylogger`. También define el **modelo de tabla** que
`DbConnection` usa para crear el esquema en SQLite.

## Identidad y destino de datos

- `tablename = 'keyboard'` — nombre de la tabla en la base de datos.
- `name = 'Keyboard'` — nombre del modelo (trazas/API).
- `api_path = '/keycounter/v1/keyboard/store'` — endpoint de subida.
- `DEVICE_ID = os.getenv("DEVICE_ID")` — identificador del equipo.

## Parámetros del algoritmo

- `COMBO_RESET = 15` — segundos de inactividad que cierran una racha.
- `COMBO_MAP` — tabla `nº_pulsaciones → puntuación` (de 1→0.01 hasta 10→1.00).
  Está **declarada pero no se usa** en el cálculo actual (`set_combo` calcula la
  puntuación con otra fórmula). Ver documento 13.

## Estado

**Sesión completa (día actual):**

- `start_at` — inicio de las mediciones.
- `pulsation_high` / `pulsation_high_at` — mayor racha de pulsaciones y cuándo.
- `pulsations_total` — total de pulsaciones.
- `pulsations_total_especial_keys` — total de pulsaciones de teclas especiales.
- `combo_score` — puntuación total acumulada por combos.
- `combo_score_high` / `combo_score_high_at` — mejor puntuación de combo en una
  racha y cuándo.

**Racha actual:**

- `pulsations_current` — pulsaciones en la racha.
- `pulsations_current_special_keys` — especiales en la racha.
- `pulsations_current_start_at` — inicio de la racha.
- `last_pulsation_at` — última pulsación.
- `combo_score_current` — puntuación de combos de la racha.

**Otros:**

- `spurts = {}` — diccionario de rachas cerradas pendientes de guardar,
  indexadas por `last_pulsation_at`.
- `socket`, `client_display_websocket` — salidas en tiempo real inyectadas por
  `Keylogger`.
- `current_day_start` / `current_day_end` — límites del día para el reinicio.

## Constructor `__init__(has_debug=False)`

Inicializa timestamps (`start_at`, `last_pulsation_at`,
`pulsations_current_start_at`) con la hora UTC actual y fija los límites del día
(`current_day_start` a las 00:00, `current_day_end` a las 23:59:59.999999). Lee
`SEND_DATA_TO_WEBSOCKET_SERVER` del entorno.

## Métodos

### `reset_global_counter()`

Reinicia todos los contadores globales de la sesión y recalcula los límites del
día. Se invoca (en un hilo) cuando se detecta que se ha cruzado la medianoche.

### `increase_pulsation(special_key=False)`

Método central, llamado por `Keylogger.callback_keyboard` en cada `down`:

1. `pulsations_total += 1`.
2. Comprueba el tiempo desde `last_pulsation_at`:
   - **Si supera `COMBO_RESET`:** cierra la racha (`add_old_streak()`), inicia
     una racha nueva (`pulsations_current = 1`, reinicia especiales, marca inicio
     y resetea el combo con `set_combo(..., reset_sesion=True)`).
   - **Si no:** `pulsations_current += 1` y actualiza el combo con
     `set_combo(..., reset_sesion=False)`.
3. Contabiliza especiales según `special_key`.
4. Actualiza `last_pulsation_at` y el récord `pulsation_high`.
5. Si se cruzó el fin de día, lanza `reset_global_counter` en un hilo.
6. Empuja actualizaciones a las salidas: `socket.update()` y, si procede y no
   está ocupado, `client_display_websocket.update()` en un hilo.

### `get_pulsation_average()`

Devuelve la **velocidad media de la racha actual en pulsaciones por minuto**:

```
(pulsations_current / duración_en_segundos) * 60
```

redondeado a 2 decimales. Si la duración o las pulsaciones son 0, devuelve 0.00.
Es la métrica de "velocidad" que se muestra en las salidas.

### `add_old_streak()`

Serializa la racha actual al diccionario `spurts`, con la clave
`last_pulsation_at` y los campos:

`start_at`, `end_at`, `pulsations`, `pulsations_special_keys`,
`pulsation_average`, `score`, `weekday` (día de la semana), `hardware_device_id`
(`DEVICE_ID`).

Estos campos coinciden con el modelo de tabla (más `created_at`, que lo añade la
base de datos).

### `set_combo(timestamp_utc, reset_sesion=False)`

Algoritmo de puntuación:

- Puntuación candidata: `new_combo_score = int(pulsations_current * 0.15)`.
- Si `reset_sesion`, pone `combo_score_current = 0` y sale.
- Determina si "toca combo" con una condición determinista:

  ```python
  (int((pulsations_current * 2.7) * ((pulsations_current + 1) * 3.4)) % 5) == 0
  ```

- Si toca, suma `new_combo_score` al total (`combo_score`) y a la racha
  (`combo_score_current`), y actualiza el récord `combo_score_high` si procede.

Es una gamificación: no toda pulsación puntúa; la puntuación crece con la
longitud de la racha.

⚠️ La fórmula es "mágica" y no está documentada su intención; `COMBO_MAP` sugiere
que hubo un diseño alternativo por tramos. Candidato a revisión. Ver documento 13.

### `statistics_session()` / `statistics_streak()` / `statistics()`

Devuelven diccionarios con los datos de sesión, de racha y ambos combinados
(`{'session': …, 'streak': …}`). Es el formato que consumen las pantallas y el
socket.

### `debug(keypress=None)`

Limpia el terminal e imprime todas las estadísticas formateadas. Solo con
`DEBUG=True`.

### `tablemodel()`

Devuelve la **definición del esquema** de la tabla `keyboard` como diccionario
`columna → {type, params, others}`, que `DbConnection.table_set_new` traduce a
columnas de SQLAlchemy. Columnas:

`start_at` (DateTime), `end_at` (DateTime), `pulsations` (Numeric),
`pulsations_special_keys` (Numeric), `pulsation_average` (String), `score`
(Numeric), `weekday` (Numeric), `hardware_device_id` (Numeric), `created_at`
(DateTime, `default=datetime.utcnow`).

## Interacciones

- **Usado por:** `Keylogger` (captura), `Socket` y `ClientDisplayWebsocket`
  (lectura de estadísticas), `main.py` vía `DbConnection` (`spurts` y
  `tablemodel`).

## Notas para mejoras (ver documento 13)

- `datetime.utcnow()` obsoleto.
- Atributos de estado definidos a **nivel de clase** (mutable compartido); con
  varias instancias `spurts` podría compartirse indebidamente.
- `COMBO_MAP` sin uso; fórmula de combo sin tipar ni documentar su intención.
- Falta tipado (type hints) en todos los métodos.
