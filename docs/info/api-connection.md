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
   `/hardware/v1/get/device/16/info` para obtener la IP local de la pantalla.

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

## Trampas conocidas
- El parámetro `method` se recibe pero `send` **siempre** hace `POST` (hay un
  `TODO` para comprobar el método). `upload` pasa `method='GET'` por defecto, que
  se ignora.
- La ruta `/hardware/v1/get/device/16/info` tiene el id de dispositivo **16
  hardcodeado**.
- `parse_to_json` serializa un único registro; `parse_array_to_json` existe pero
  `upload` usa el primero fila a fila.
- `TODO` pendientes: validar método HTTP, normalizar a array, añadir metadatos.

## Tests que lo cubren
Ninguno ⚠️.

## Pendiente real
- Implementar la comprobación de método HTTP (`POST|GET|PUT|DELETE`).
- Parametrizar el id de dispositivo en `get_websocket_server_display_info`.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
