# Integración con la API de raupulus.dev

Cómo **integramos nosotros** esta API desde el proyecto. No duplica la
especificación oficial completa de la API (que vive en
[`docs/apis/raupulus/`](../../apis/raupulus/README.md) y en su
[Contrato API V2 KeyCounter](../../apis/raupulus/keycounter.md)).

> El contrato de KeyCounter (sesiones de teclado, ratón y resumen acumulado) está
> **verificado** y alineado con el [Contrato API V2](../../apis/raupulus/keycounter.md)
> (revisión 2026-09-07).

## Base y autenticación
- **Base URL**: configurable por `API_URL` (`.env.example`: `http://example.com`,
  producción: `https://api.raupulus.dev/api/v2`).
- **Envelope estándar V2**:
  - Éxito: `{ "success": true, "message": "...", "data": { ... } }`
  - Error: `{ "success": false, "message": "...", "errors": { ... } }`
  - Rutas no documentadas o método incorrecto: `404` con `{ "success": false, "message": "API V2 - Endpoint no encontrado" }` (no hay 405).
- **Autenticación**: Laravel Sanctum, cabecera `Authorization: Bearer <API_TOKEN>`.
  - Los endpoints de registro de sesiones requieren la ability `keycounter:write`.
  - El endpoint de resumen acumulado (`/keycounter/summary`) requiere la ability `keycounter:read`.
- **Headers HTTP**: `Content-type: application/json`, `Accept: application/json`,
  timeout 30 s (10 s en summary), 3 reintentos en `500/502/504` (1 en summary).

## Endpoints que consumimos
| Uso | Método | Ruta (relativa a `API_URL`) | Origen |
|-----|--------|-----------------------------|--------|
| Subir rachas de teclado | `POST` | `/keycounter/keyboard-sessions` | `KeyboardLogger.api_path` |
| Subir rachas de ratón | `POST` | `/keycounter/mouse-sessions` | `MouseLogger.api_path` |
| Info del dispositivo pantalla | `GET` | `/hardware/devices/{DISPLAY_ID}?include=status` | `ApiConnection.get_websocket_server_display_info` (id `DISPLAY_ID`, token `DISPLAY_API_TOKEN`) |
| Resumen del día (teclado + ratón) | `GET` | `/keycounter/summary?device_id={DEVICE_ID}&date=today` | `ApiConnection.get_summary` |

> Nota: aunque `ApiConnection.send` recibe un parámetro `method`, siempre realiza
> `POST` (ver [api-connection](../api-connection.md), trampas conocidas).

## Estrategia de sincronización inicial (`/keycounter/summary`)
Para no perder el acumulado de pulsaciones y clicks del día al reiniciar el script o el equipo:
1. **Arranque asíncrono**: al iniciar `main.py`, se lanza un hilo en segundo plano
   para pedir `GET /keycounter/summary?device_id={DEVICE_ID}&date=today` sin bloquear la captura.
2. **Corte del periodo**: el corte lo realiza el servidor en UTC por `created_at`
   (cuándo llegó la racha a la API). Al recibir el resumen, el cliente suma los totales
   de la API sobre los contadores que ya hubiese acumulado localmente desde que arrancó el proceso.
3. **Sincronización única**: una vez completada con éxito (`is_synced = True`), no se
   vuelve a consultar en todo el tiempo que el script permanezca abierto.
4. **Fallback defensivo ante error o 403/404 (1 hora)**: si la llamada falla, da 404,
   403 (token sin `keycounter:read`) o timeout de red, se anota `last_sync_attempt` y
   **no se vuelve a reintentar hasta transcurrida 1 hora** (`SYNC_RETRY_INTERVAL_SECONDS = 3600`).
   Este reintento se evalúa tras cada ciclo de subida en `loop()`.

## Otros endpoints disponibles en API V2 (no consumidos actualmente)
| Uso | Método | Ruta | Detalle |
|-----|--------|------|---------|
| Listar sesiones de teclado | `GET` | `/keycounter/keyboard-sessions` | Soporta filtros (`hardware_device_id`, `start_at`, `end_at`, `created_at`, `from`, `to`), ordenación (`sort`) y paginación (`page`, `per_page`). Requiere `keycounter:write`. |
| Listar sesiones de ratón | `GET` | `/keycounter/mouse-sessions` | Mismos filtros y paginación que teclado. |

## Códigos de respuesta y rate limit
- **Rate Limit**:
  - `POST /keycounter/*-sessions`: límite `api-store` de **60 peticiones/min** (`RATE_LIMIT_IOT_STORE`), identificado por el ID del token Sanctum.
  - `GET /keycounter/summary`: límite `keycounter-summary` de **20 peticiones/min** por token.
- **Códigos HTTP**:
  - `201 Created` → guardado exitoso en API V2 (`True`).
  - `200 OK` → tratado por el cliente como éxito (`True`), usado en consultas GET (`/summary` y `/devices`).
  - `401 Unauthorized` → sin token o token no válido.
  - `403 Forbidden` → token sin ability (`keycounter:write` para sesiones, `keycounter:read` para summary).
  - `422 Unprocessable Entity` → error de validación (fechas con formato distinto a `Y-m-d H:i:s`, campos vacíos/faltantes, o `device_id` no válido/ajeno al token).
  - `429 Too Many Requests` → superado el límite de peticiones por minuto.
  - `500/502/504` → reintentados automáticamente por la sesión de requests.

## Cuerpo enviado y reglas de negocio del servidor
JSON de un registro por petición, con los campos de `tablemodel()` de cada modelo
(omitiendo la columna `id`):

- **Fechas**: `start_at` y `end_at` deben enviarse en formato estricto `Y-m-d H:i:s`.
- **Campos calculados en el servidor**:
  - `duration`: el servidor lo calcula en segundos (`end_at - start_at`) antes de validar. El cliente no lo envía (si se envía, el servidor lo sobrescribe).
  - `user_id`: se fuerza en el servidor al dueño del token; no se envía desde el cliente.
- **Día de la semana (`weekday`)**:
  - La API espera un entero entre `0` y `6`, donde `0 = domingo`.
  - Alineado: el cliente calcula `(datetime.today().weekday() + 1) % 7` para enviar `0 = domingo`, `1 = lunes`, etc.
- **Sesiones de ratón**:
  - La tabla de ratón en la API no tiene campo `score` (el recurso `MouseResource` no lo incluye). Si se envía, la API lo ignora silenciosamente.
- **Info de hardware opcional**:
  - Los endpoints de guardado admiten opcionalmente un objeto `hardware_device_info` en el cuerpo para actualizar el estado del dispositivo en la misma petición (mismo contrato que `/hardware/devices/{id}/status`).

## Respuesta de la info de dispositivo (verificada)
`GET /hardware/devices/{id}?include=status` responde con el envelope v2
`{ "success": true, "message": ..., "data": { ...dispositivo... } }`. Se consulta
el dispositivo pantalla (`DISPLAY_ID`) con su propio token (`DISPLAY_API_TOKEN`),
porque el token de keycounter no puede leer otros dispositivos. Verificado con
petición real (device 16 = Raspberry Pi Pico Display, `200`): `data` trae datos
estáticos (`id`, `user_id`, `name`, `type`, `brand`, `model`, versiones...) **y**,
gracias a `include=status`, un objeto anidado `data.status` con el estado
dinámico:

```json
"status": {
  "hardware_device_id": 16,
  "temp": null, "voltage": null, "battery_level": null,
  "cpu": null, "disk": null, "ram": null, "uptime": null,
  "ip_local": "172.18.1.209",
  "ip_public": "139.47.158.109",
  "extra": null,
  "last_seen_at": "2026-09-05T10:59:24.000000Z"
}
```

`ip_local` vive ahí, no en `data` directamente. Sin `include=status` la API omite
este bloque por completo.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-07
