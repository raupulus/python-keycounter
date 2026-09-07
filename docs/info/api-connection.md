# `api-connection`

> Ruta real en el repositorio: `Models/ApiConnection.py`

## Qué hace y qué NO hace
Cliente HTTP hacia la API remota. Serializa a JSON las tuplas leídas de la DB y
las envía por `POST` con reintentos, y pide información del servidor de pantalla
en red local. Ver la integración detallada en
[apis/raupulus-api.md](apis/raupulus-api.md).

**NO** decide qué se sube ni borra datos locales (eso lo hace [main](main.md)).

## Modelo de datos
No mantiene estado persistente. Convierte filas + nombres de columna a JSON
(omitiendo la columna `id`).

## Flujos principales
1. `upload(name, path, datas, columns, method)` — itera las filas, serializa cada
   una con `parse_to_json` y llama a `send`; devuelve `True` si al menos una se
   envió.
2. `send(path, datas_json, method)` — `POST` a `API_URL + path` con cabecera
   `Authorization: Bearer <token>`; trata `201` y `200` como éxito.
3. `requests_retry_session(...)` — sesión `requests` con reintentos
   (`status_forcelist=(500,502,504)`, `backoff_factor=0.3`).
4. `get_websocket_server_display_info()` — `GET` a
   `/hardware/devices/{DISPLAY_ID}?include=status` (API v2) usando
   `DISPLAY_API_TOKEN` (el token de keycounter no puede leer otros dispositivos
   por seguridad). El `include=status` es imprescindible: sin él, la respuesta no
   trae el estado dinámico y falta `ip_local` (ver
   [client-display-websocket](client-display-websocket.md)).

## Puntos de entrada
- `ApiConnection()`.
- `upload`, `send`, `parse_to_json`, `parse_array_to_json`,
  `get_websocket_server_display_info`.
- **Auth:** token Bearer (`API_TOKEN`). **Timeout:** 30 s. **Reintentos:** 3.

## Dependencias en ambos sentidos
- **Depende de:** `requests` (+`urllib3`), `python-dotenv`.
- **Le depende:** [main](main.md) (subida),
  [client-display-websocket](client-display-websocket.md) (info del servidor).

## Configuración
| Variable | Defecto (.env.example) | Efecto |
|----------|------------------------|--------|
| `API_URL` | `http://example.com` | Base de la API (en producción: `https://api.raupulus.dev/api/v2`). |
| `API_TOKEN` | `apitoken` | Token Bearer. |
| `DEBUG` | `False` | Traza peticiones y respuestas. |
| `DISPLAY_ID` | (vacío) | Id del dispositivo pantalla en `get_websocket_server_display_info`. |
| `DISPLAY_API_TOKEN` | (vacío) | Token Bearer propio del display (lectura de ese dispositivo). |

## Trampas conocidas
- El parámetro `method` se recibe pero `send` **siempre** hace `POST` (hay un
  `TODO` para comprobar el método). `upload` pasa `method='GET'` por defecto, que
  se ignora.
- La ruta es `/hardware/devices/{DISPLAY_ID}?include=status` (API v2), con
  `DISPLAY_ID` y `DISPLAY_API_TOKEN` propios del display (antes era el id **16**
  hardcodeado con el token de keycounter, que en v2 ya no puede leer otros
  dispositivos). `ip_local` va anidado en `data.status.ip_local`, no en `data`
  directamente; el consumidor lo comprueba y no conecta si falta.
- `parse_to_json` serializa un único registro; `parse_array_to_json` existe pero
  `upload` usa el primero fila a fila.
- `TODO` pendientes: validar método HTTP, normalizar a array, añadir metadatos.

## Tests que lo cubren
Ninguno ⚠️.

## Pendiente real
- Implementar la comprobación de método HTTP (`POST|GET|PUT|DELETE`).

---
> Creado: 2026-09-06 · Última revisión: 2026-09-07
