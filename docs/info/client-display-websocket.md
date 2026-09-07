# `client-display-websocket`

> Ruta real en el repositorio: `Models/ClientDisplayWebsocket.py`

## Qué hace y qué NO hace
Cliente que envía estadísticas a una pantalla/dispositivo en la red local. Pide a
la API la información del dispositivo servidor (IP local) y, en cada `update()`,
abre una conexión TCP al puerto 80 de esa IP y envía un JSON con las
estadísticas actuales.

**NO** es un servidor websocket ni usa el protocolo WebSocket real: es un cliente
TCP plano (el nombre es histórico). **NO** persiste datos.

## Modelo de datos
JSON enviado en `update()`:
```json
{
  "device_id": "<DEVICE_ID>",
  "session": { "pulsations_total": <int> },
  "streak": { "pulsations_current": <int>, "pulsation_average": <int> },
  "timestamp": "YYYY-MM-DD HH:MM:SS",
  "time": "HH:MM:SS",
  "system": { "so": "<DEVICE_NAME>" }
}
```
- `websocket_server_display_info` — el objeto `status` del dispositivo servidor
  (`data.status` de la API v2), que incluye `ip_local`, `ip_public`, `temp`,
  `battery_level`... Sólo se asigna si `ip_local` viene presente.
- `is_busy: bool`, `errors: int`.

## Flujos principales
1. `__init__` — lanza `prepare_client` en un hilo.
2. `prepare_client()` — pide a la API
   (`ApiConnection.get_websocket_server_display_info`, que consulta con
   `?include=status`) y lee `data.status` (envelope v2, estado anidado); con
   reintentos escalonados (10/30/60 s) mientras la respuesta sea `None`. Sólo fija
   `websocket_server_display_info` si `status` trae `ip_local`; si no, el envío
   por red queda inactivo.
3. `update()` — si no está ocupado y hay info del servidor, conecta a
   `ip_local:80`, envía el JSON, lee la respuesta y espera `status == 'ok'`.
   Cuenta errores; si superan 10 vuelve a `prepare_client`. Lo invoca el modelo de
   teclado en un hilo.

## Puntos de entrada
- `ClientDisplayWebsocket(keylogger, api, debug)`.
- `update()` — llamado por [keyboard-logger](keyboard-logger.md).
- **Red:** TCP saliente a `ip_local:80`, timeout implícito del socket del SO.

## Dependencias en ambos sentidos
- **Depende de:** `socket`, `json`, [api-connection](api-connection.md), keylogger.
- **Le depende:** [main](main.md), [keyboard-logger](keyboard-logger.md).

## Configuración
| Variable | Defecto | Efecto |
|----------|---------|--------|
| `DEVICE_ID` | `None` | Se envía en el JSON. |
| `DEVICE_NAME` | `N/D` | Se envía como `system.so`. |
| `DISPLAY_ID` | (vacío) | Id del dispositivo pantalla a consultar en la API. |
| `DISPLAY_API_TOKEN` | (vacío) | Token propio del display para leer su info. |
| `SEND_DATA_TO_WEBSOCKET_SERVER` | `False` | El modelo de teclado sólo llama a `update()` si está activo. |

## Trampas conocidas
- El id y token del servidor los toma `get_websocket_server_display_info` de
  `DISPLAY_ID` y `DISPLAY_API_TOKEN` (`.env`), distintos de `DEVICE_ID`/`API_TOKEN`
  (que son de este equipo): en v2 el token de keycounter no puede leer otros
  dispositivos.
- El `ip_local` sólo llega si la petición incluye `?include=status`; sin ese
  parámetro la API v2 omite el estado dinámico por completo.
- El puerto destino está **hardcodeado a 80**.
- `prepare_client` puede bucle-esperar indefinidamente sólo si la API responde
  `None` (error/timeout); ante un `200` sin `ip_local` sale limpio y deja el
  envío inactivo.

## Tests que lo cubren
Ninguno ⚠️.

## Pendiente real
- Parametrizar el puerto destino.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-07
