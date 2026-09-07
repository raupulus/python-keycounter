# `api-connection`

> Ruta real en el repositorio: `Models/ApiConnection.py`

## Qué hace y qué NO hace
Cliente HTTP hacia la API remota. Serializa a JSON las tuplas leídas de la DB y
las envía por `POST` con reintentos (inyectando `hardware_device_info` únicamente
durante la subida de sesiones), pide información del servidor de pantalla en red
local y consulta el resumen acumulado del día (`GET /keycounter/summary`). Ver la
integración detallada en [apis/raupulus-api.md](apis/raupulus-api.md) y el contrato
oficial en [`docs/apis/raupulus/keycounter.md`](../../apis/raupulus/keycounter.md).

**NO** decide qué se sube ni borra datos locales (eso lo hace [main](main.md)).

## Modelo de datos
No mantiene estado persistente. Convierte filas + nombres de columna a JSON
(omitiendo la columna `id`). Normaliza automáticamente cadenas de fecha de SQLite
(con microsegundos o formato ISO) al formato estricto `Y-m-d H:i:s` requerido por la API V2.
Admite inyectar campos adicionales como `hardware_device_info` vía `extra_fields`.

## Flujos principales
1. `upload(name, path, datas, columns, method='GET', extra_fields=None)` — itera
   las filas, serializa cada una con `parse_to_json(data, columns, extra_fields)`
   y llama a `send`; devuelve `True` si al menos una se envió.
2. `send(path, datas_json, method)` — `POST` a `API_URL + path` con cabecera
   `Authorization: Bearer <token>`; trata `201` y `200` como éxito (la API V2
   devuelve `201 Created` con envelope `{ "success": true, ... }`). Imprime detalles
   en caso de error HTTP (>=400) si `DEBUG` está activo.
3. `requests_retry_session(...)` — sesión `requests` con reintentos
   (`status_forcelist=(500,502,504)`, `backoff_factor=0.3`).
4. `get_websocket_server_display_info()` — `GET` a
   `/hardware/devices/{DISPLAY_ID}?include=status` (API v2) usando
   `DISPLAY_API_TOKEN` (el token de keycounter no puede leer otros dispositivos
   por seguridad). El `include=status` es imprescindible: sin él, la respuesta no
   trae el estado dinámico y falta `ip_local` (ver
   [client-display-websocket](client-display-websocket.md)).
5. `get_summary(device_id=None, date='today')` — `GET` a
   `/keycounter/summary?device_id={device_id}&date={date}` usando `API_TOKEN`.
   Devuelve el diccionario `data` con los totales acumulados (teclado y ratón)
   o `None` si la petición falla (404/403/error/timeout).

## Puntos de entrada
- `ApiConnection()`.
- `upload`, `send`, `parse_to_json`, `parse_array_to_json`,
  `get_websocket_server_display_info`, `get_summary`.
- **Auth:** token Bearer (`API_TOKEN`) con abilities `keycounter:write` y `keycounter:read`.
- **Timeout:** 30 s (10 s en summary). **Reintentos:** 3 (1 en summary).

## Dependencias en ambos sentidos
- **Depende de:** `requests` (+`urllib3`), `python-dotenv`.
- **Le depende:** [main](main.md) (subida y sincronización inicial),
  [client-display-websocket](client-display-websocket.md) (info del servidor).

## Configuración
| Variable | Defecto (.env.example) | Efecto |
|----------|------------------------|--------|
| `API_URL` | `http://example.com` | Base de la API (en producción: `https://api.raupulus.dev/api/v2`). |
| `API_TOKEN` | `apitoken` | Token Bearer (IoT con abilities `keycounter:write` y `keycounter:read`). |
| `DEVICE_ID` | (vacío) | Id de hardware de este equipo usado por defecto en `get_summary`. |
| `DEBUG` | `False` | Traza peticiones y respuestas. |
| `DISPLAY_ID` | (vacío) | Id del dispositivo pantalla en `get_websocket_server_display_info`. |
| `DISPLAY_API_TOKEN` | (vacío) | Token Bearer propio del display (lectura de ese dispositivo). |

## Trampas conocidas
- El parámetro `method` se recibe pero `send` **siempre** hace `POST` (hay un
  `TODO` para comprobar el método). `upload` pasa `method='GET'` por defecto, que
  se ignora.
- **Rate Limit de la API**: API V2 aplica límite `api-store` de 60 req/min para subidas
  y `keycounter-summary` de 20 req/min para `/summary`.
- `get_summary` requiere ability `keycounter:read` en el token. Si el token solo tuviera
  `keycounter:write`, responderá `403 Forbidden`.
- La ruta es `/hardware/devices/{DISPLAY_ID}?include=status` (API v2), con
  `DISPLAY_ID` y `DISPLAY_API_TOKEN` propios del display (el token de keycounter no
  puede leer otros dispositivos). `ip_local` va anidado en `data.status.ip_local`,
  no en `data` directamente; el consumidor lo comprueba y no conecta si falta.
- `parse_to_json` normaliza fechas a `Y-m-d H:i:s` porque SQLite devuelve cadenas
  con microsegundos (`.729175`), lo que provocaba rechazo con `422` en la API.
- `TODO` pendientes: validar método HTTP, normalizar a array.

## Tests que lo cubren
Ninguno ⚠️.

## Pendiente real
- Implementar la comprobación de método HTTP (`POST|GET|PUT|DELETE`).
- Agrupación por lotes / array para evitar saturar el rate limit de 60 req/min.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-07
