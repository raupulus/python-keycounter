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
- `websocket_server_display_info` — datos del dispositivo servidor (incluye
  `ip_local`).
- `is_busy: bool`, `errors: int`.

## Flujos principales
1. `__init__` — lanza `prepare_client` en un hilo.
2. `prepare_client()` — pide a la API
   (`ApiConnection.get_websocket_server_display_info`) hasta obtener la clave
   `device`; con reintentos escalonados (10/30/60 s).
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
| `SEND_DATA_TO_WEBSOCKET_SERVER` | `False` | El modelo de teclado sólo llama a `update()` si está activo. |

## Trampas conocidas
- El id de dispositivo del servidor está fijado a **16** dentro de
  `ApiConnection.get_websocket_server_display_info` (no en este módulo).
- El puerto destino está **hardcodeado a 80**.
- `prepare_client` puede bucle-esperar indefinidamente si la API nunca devuelve
  `device`.

## Tests que lo cubren
Ninguno ⚠️.

## Pendiente real
- Parametrizar id de dispositivo y puerto destino.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
