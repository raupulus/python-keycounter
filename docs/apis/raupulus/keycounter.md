# Contrato API V2 — Contador de teclado y ratón (KeyCounter)

> Este archivo documenta **solo el contrato HTTP** de este módulo: rutas, auth,
> parámetros y forma exacta de la respuesta. Está pensado para copiarse a otro
> proyecto (o pegarse en el contexto de una IA) y que con eso baste para
> integrar estos endpoints sin leer el código fuente.
>
> Para el diseño interno (modelos, servicio, decisiones de producto) ver
> [`docs/info/keycounter.md`](../../keycounter.md).

## Base y convenciones comunes a toda la API V2

- **Base URL**: `/api/v2`
- **Todas las respuestas** usan este envelope (`App\Traits\ApiResponseTrait`):

  ```json
  // Éxito
  { "success": true, "message": "Operación exitosa", "data": { ... } }
  // Error
  { "success": false, "message": "Descripción del error", "errors": { "campo": ["detalle"] } }
  ```

  `errors` solo aparece si hay detalle (p. ej. errores de validación 422).
- **Autenticación**: Laravel Sanctum, cabecera `Authorization: Bearer <token>`.
  Todos los endpoints de este módulo (lectura **y** escritura) requieren un
  **token de dispositivo IoT** con la ability `keycounter:write` (catálogo
  completo en `app/Support/Auth/TokenAbilities.php`; se emite con `POST
  /auth/tokens/devices`, ver [`auth.md`](./auth.md)). No existe una ability de
  solo lectura para este módulo: el mismo token que registra sesiones es el
  único que puede listarlas.
- **Ruta inexistente**: cualquier método/URL que no esté documentado responde
  `404` con `{ "success": false, "message": "API V2 - Endpoint no encontrado" }`
  (incluso si el método HTTP es el que no cuadra: el contrato es la pareja
  método+ruta, no hay 405).

## Nota de diseño: el recurso es la sesión, no el periférico

Los dos recursos de este módulo son **sesiones de trabajo** delimitadas por
`start_at`/`end_at` (una racha de uso), no "el teclado" o "el ratón" como
objetos físicos. Antes las rutas eran `POST /keycounter/keyboard` y `POST
/keycounter/mouse`, que sonaban a que se daba de alta un periférico; ahora son
`.../keyboard-sessions` y `.../mouse-sessions`.

---

## Sesiones de teclado (`/keycounter/keyboard-sessions`)

### `GET /keycounter/keyboard-sessions` — Mis sesiones de teclado

No existía en V1: el módulo solo tenía escritura y los datos se veían por
Blade directamente contra la base de datos.

- **Auth**: `auth:sanctum` + `ability:keycounter:write`.
- **Rate limit**: ninguno propio (solo la comprobación de la ability).
- **Query params** (contrato genérico de colecciones de la API V2,
  `App\Http\Api\CollectionQuery`):

| Parámetro | Tipo | Reglas |
|---|---|---|
| `hardware_device_id` / `start_at` / `end_at` / `created_at` | — | filtrables por igualdad, `campo=a,b,c` (IN) o `campo[gte]=`/`campo[lte]=`/`campo[gt]=`/`campo[lt]=`/`campo[ne]=` |
| `from` | fecha | alias de `created_at >=` |
| `to` | fecha | alias de `created_at <=` |
| `sort` | string | columnas admitidas: `start_at`, `end_at`, `created_at`, `pulsations`. Por defecto `start_at` descendente. Prefijo `-` para descendente, se admite lista separada por comas |
| `page` | int | por defecto `1` |
| `per_page` | int | por defecto `25`, máximo `100` |

  Cualquier parámetro fuera de esta lista se ignora en silencio (no filtra ni
  da error). La colección se filtra siempre por el usuario dueño del token
  autenticado (`where('user_id', ...)`); no hay forma de ver sesiones de otro.

- **Respuesta 200**:

```json
{
  "success": true,
  "message": "Operación exitosa",
  "data": [
    {
      "id": 101,
      "hardware_device_id": 3,
      "user_id": 1,
      "start_at": "2026-08-30T09:00:00.000000Z",
      "end_at": "2026-08-30T09:15:00.000000Z",
      "duration": 900,
      "pulsations": 5230,
      "pulsations_special_keys": 340,
      "pulsation_average": 5.81,
      "score": 87,
      "weekday": 0,
      "created_at": "2026-08-30T09:15:01.000000Z"
    }
  ],
  "meta": {
    "total": 1,
    "per_page": 25,
    "current_page": 1,
    "last_page": 1,
    "from": 1,
    "to": 1
  }
}
```

- **Errores**: `401` sin token o token inválido, `403` token sin la ability
  `keycounter:write`.

---

### `POST /keycounter/keyboard-sessions` — Registra una sesión de teclado

- **Auth**: `auth:sanctum` + `ability:keycounter:write`.
- **Rate limit**: `api-store` — 60 peticiones/min (`RATE_LIMIT_IOT_STORE`,
  config `rate_limits.iot_store_per_minute`), identificado por el **id del
  token** Sanctum usado (no por IP).
- **Body**:

| Campo | Tipo | Reglas |
|---|---|---|
| `hardware_device_id` | int | `required`, debe existir en `hardware_devices`, pertenecer al usuario del token y, si el token está ligado a un dispositivo concreto vía ability `device:{id}`, coincidir con ese dispositivo. Alias aceptado: `device_id` (nombre de V1) |
| `start_at` | string | `required`, formato exacto `Y-m-d H:i:s` |
| `end_at` | string | `required`, formato exacto `Y-m-d H:i:s` |
| `pulsations` | int | `required`, mín. 0 |
| `pulsations_special_keys` | int | `required`, mín. 0 |
| `pulsation_average` | number | `required`, mín. 0 |
| `score` | int | `required`, mín. 0 |
| `weekday` | int | `required`, entre 0 y 6 (0 = domingo) |
| `hardware_device_info` | object\|null | opcional. Último estado conocido del propio dispositivo que sube la sesión (batería, temperatura, uptime...). Mismos campos que `PUT /hardware/devices/{device}/status` (`temp`, `voltage`, `battery_level`, `cpu`, `disk`, `ram`, `uptime`, `ip_local`, `extra`; **`ip_public` ya no se acepta desde el 2026-09-06**, la pone el servidor); si viene, se aplica sobre `hardware_device_id` en la misma petición. Contrato completo en [`hardware.md`](./hardware.md) |

  Dos campos del modelo **no se envían**, se calculan/fuerzan en el servidor
  antes de validar (`prepareForValidation`):
  - `duration`: se calcula como `end_at - start_at` en segundos, siempre que
    ambas fechas vengan rellenas. Si falta alguna, no se calcula y la petición
    responde `422` (el campo es `required` internamente). Lo que el cliente
    envíe en `duration` se ignora y se sobrescribe.
  - `user_id`: se fuerza siempre al usuario dueño del token autenticado; no
    hace falta enviarlo y, si se envía, se ignora.

  Si se envían `pulsations`, `pulsations_special_keys`, `score` o `weekday`
  vacíos (no solo ausentes), la petición falla con `422` en vez de guardarse
  con un `0` inventado.

- **Respuesta 201**:

```json
{
  "success": true,
  "message": "Registro de teclado almacenado",
  "data": {
    "id": 102,
    "hardware_device_id": 3,
    "user_id": 1,
    "start_at": "2026-08-30 09:00:00",
    "end_at": "2026-08-30 09:15:00",
    "duration": 900,
    "pulsations": 5230,
    "pulsations_special_keys": 340,
    "pulsation_average": 5.81,
    "score": 87,
    "weekday": 0,
    "created_at": "2026-08-30T09:15:01.000000Z"
  }
}
```

- **Errores**:
  - `401` sin token o token inválido.
  - `403` token sin la ability `keycounter:write`.
  - `422` validación: campo requerido ausente/vacío, `hardware_device_id` que
    no exista, que no sea del usuario, o que no coincida con el dispositivo al
    que el token está ligado; también si falta `start_at` o `end_at` (impide
    calcular `duration`).
  - `429` al superar 60/min con ese token.

---

## Sesiones de ratón (`/keycounter/mouse-sessions`)

### `GET /keycounter/mouse-sessions` — Mis sesiones de ratón

- **Auth**: `auth:sanctum` + `ability:keycounter:write`.
- **Rate limit**: ninguno propio.
- **Query params**: mismo contrato que las sesiones de teclado, con una
  salvedad:

| Parámetro | Tipo | Reglas |
|---|---|---|
| `hardware_device_id` / `start_at` / `end_at` / `created_at` | — | filtrables igual que en teclado |
| `from` / `to` | fecha | alias de `created_at >=` / `created_at <=` |
| `sort` | string | columnas admitidas: `start_at`, `end_at`, `created_at`. Por defecto `start_at` descendente |
| `page` / `per_page` | int | igual que en teclado (por defecto 25, máximo 100) |

- **Respuesta 200**:

```json
{
  "success": true,
  "message": "Operación exitosa",
  "data": [
    {
      "id": 55,
      "hardware_device_id": 3,
      "user_id": 1,
      "start_at": "2026-08-30T09:00:00.000000Z",
      "end_at": "2026-08-30T09:15:00.000000Z",
      "duration": 900,
      "clicks_left": 210,
      "clicks_right": 45,
      "clicks_middle": 3,
      "total_clicks": 258,
      "clicks_average": 17,
      "weekday": 0,
      "created_at": "2026-08-30T09:15:01.000000Z"
    }
  ],
  "meta": {
    "total": 1,
    "per_page": 25,
    "current_page": 1,
    "last_page": 1,
    "from": 1,
    "to": 1
  }
}
```

  Nota: `MouseResource` no incluye `score` (a diferencia de teclado): la tabla
  `keycounter_mouse` no tiene esa columna; el que puntúa es el teclado.

- **Errores**: `401` sin token o token inválido, `403` token sin la ability
  `keycounter:write`.

---

### `POST /keycounter/mouse-sessions` — Registra una sesión de ratón

- **Auth**: `auth:sanctum` + `ability:keycounter:write`.
- **Rate limit**: `api-store` — 60 peticiones/min, identificado por el id del
  token.
- **Body**:

| Campo | Tipo | Reglas |
|---|---|---|
| `hardware_device_id` | int | `required`, mismas reglas de pertenencia que en teclado. Alias aceptado: `device_id` |
| `start_at` | string | `required`, formato exacto `Y-m-d H:i:s` |
| `end_at` | string | `required`, formato exacto `Y-m-d H:i:s` |
| `clicks_left` | int | `required`, mín. 0 |
| `clicks_right` | int | `required`, mín. 0 |
| `clicks_middle` | int | `required`, mín. 0 |
| `total_clicks` | int | `required`, mín. 0 |
| `clicks_average` | int | opcional (`nullable`), mín. 0 |
| `weekday` | int | `required`, entre 0 y 6 |
| `hardware_device_info` | object\|null | opcional. Igual que en teclado: aplica el estado del dispositivo en la misma petición. Contrato completo en [`hardware.md`](./hardware.md) |

  Igual que en teclado: `duration` se calcula server-side a partir de
  `start_at`/`end_at` (lo que envíe el cliente se ignora) y `user_id` se fuerza
  al del token autenticado. No hay campo `score` en este recurso: si se envía,
  se ignora silenciosamente (no forma parte de las reglas ni del `fillable`
  del modelo).

- **Respuesta 201**:

```json
{
  "success": true,
  "message": "Registro de raton almacenado",
  "data": {
    "id": 56,
    "hardware_device_id": 3,
    "user_id": 1,
    "start_at": "2026-08-30 09:00:00",
    "end_at": "2026-08-30 09:15:00",
    "duration": 900,
    "clicks_left": 210,
    "clicks_right": 45,
    "clicks_middle": 3,
    "total_clicks": 258,
    "clicks_average": 17,
    "weekday": 0,
    "created_at": "2026-08-30T09:15:01.000000Z"
  }
}
```

- **Errores**:
  - `401` sin token o token inválido.
  - `403` token sin la ability `keycounter:write`.
  - `422` validación: campo requerido ausente/vacío, `hardware_device_id` que
    no exista, que no sea del usuario, o que no coincida con el dispositivo al
    que el token está ligado; también si falta `start_at` o `end_at`.
  - `429` al superar 60/min con ese token.

---

## Resumen acumulado (`/keycounter/summary`)

### `GET /keycounter/summary` — Lo acumulado en un periodo

**Nuevo el 2026-09-07.** Para lo que existe: un contador que se apaga, se
reinicia o cierra el script **pierde lo que llevaba contado del día**. Al
arrancar pide aquí el acumulado y sigue sumando desde donde estaba, en vez de
empezar de cero y enseñar un total falso hasta medianoche.

- **Auth**: `auth:sanctum` + `ability:keycounter:read`.
- **Rate limit**: `keycounter-summary` — **20 peticiones/min por token**. Es una
  consulta agregada sobre una tabla de millones de filas y está pensada para una
  petición por arranque, no para sondear.
- **Query**:

| Parámetro | Tipo | Reglas |
|---|---|---|
| `device_id` | int | **Obligatorio.** El dispositivo del que se pide el resumen. Debe existir y ser del usuario del token (+ ligado a `device:{id}` si aplica), o da `422` |
| `date` | string\|null | El periodo. Cuatro formas y ninguna más: `today` (por defecto), `month`, `AAAA-MM-DD` (ese día) y `AAAA-MM` (ese mes entero). Otra cosa —o una fecha que no existe, como `2026-13-45`— da `422` |

El resumen es **de un dispositivo**: el que pregunta. No hay agregado de varios
ni forma de pedirlo.

- **Respuesta 200**:

```json
{
  "success": true,
  "message": "Operación exitosa",
  "data": {
    "period": "today",
    "from": "2026-09-07T00:00:00.000000Z",
    "to": "2026-09-07T23:59:59.999999Z",
    "hardware_device_id": 9,
    "pulsations_total": 5230,
    "pulsations_total_special_keys": 340,
    "combo_score": 87,
    "pulsation_high": 420,
    "sessions": 12,
    "duration_seconds": 4300,
    "mouse": {
      "clicks_total": 900,
      "clicks_high": 120,
      "sessions": 5,
      "duration_seconds": 3100
    }
  }
}
```

| Campo | Qué es |
|---|---|
| `period` | El periodo tal cual se pidió |
| `from` / `to` | Los dos extremos, **ambos incluidos**, en UTC |
| `hardware_device_id` | El `device_id` pedido |
| `pulsations_total` | **Suma** de pulsaciones del periodo. Es el número con el que el cacharro continúa su cuenta |
| `pulsations_total_special_keys` | Suma de pulsaciones de teclas especiales |
| `combo_score` | **Máximo** `score` de una racha del periodo: el récord, para no perderlo al reiniciar |
| `pulsation_high` | **Máximo** de pulsaciones en una sola racha |
| `sessions` | Número de rachas del periodo |
| `duration_seconds` | Segundos sumados de todas las rachas |
| `mouse` | Lo equivalente del ratón: clicks sumados, el máximo de una sesión, sesiones y duración |

Las sumas sirven para **continuar** el total; los máximos, para **no perder** el
récord del periodo. Por eso van los dos.

**El corte del periodo es por `created_at`** —cuándo llegó la racha a la API—,
que es lo mismo que usa la web de `/keycounter`: así el «total de hoy» de un
cacharro y el que enseña la web son el mismo número. Las fechas se guardan en
UTC y el corte se hace en UTC.

- **Errores**: `401` sin token, `403` con un token sin `keycounter:read`
  (el de escritura de un teclado no vale), `422` si falta `device_id`, si el
  dispositivo no es del usuario o no lo alcanza el token, o si `date` no cuadra.
  `429` al pasar de 20 por minuto.

---

## Lo que ya no existe, y por qué

| Ruta antigua | Qué pasó |
|---|---|
| `POST /keycounter/keyboard` | Es `POST /keycounter/keyboard-sessions` (mismo cuerpo; se acepta también `device_id` como alias de `hardware_device_id`) |
| `POST /keycounter/mouse` | Es `POST /keycounter/mouse-sessions` |

Antes el módulo solo tenía escritura; los `GET` (`keyboard-sessions` /
`mouse-sessions`) son nuevos en V2, no una migración de rutas previas.

---

> Creado: 2026-08-30 · Última revisión: 2026-09-07
