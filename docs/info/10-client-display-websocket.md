# 10 — `ClientDisplayWebsocket` (pantalla en red local)

**Archivo:** `Models/ClientDisplayWebsocket.py`

## Objetivo del módulo

Enviar las estadísticas a una **pantalla/dispositivo en la red local** que actúa
como servidor. KeyCounter es aquí el **cliente**: descubre la IP del servidor
consultando la API y le manda los datos por un socket TCP. Solo se activa con
`SEND_DATA_TO_WEBSOCKET_SERVER=True`.

> Nota: pese al nombre "Websocket", la implementación usa un **socket TCP plano**
> (`AF_INET`, `SOCK_STREAM`) al puerto 80, enviando y recibiendo JSON. No es el
> protocolo WebSocket estándar.

## Atributos

- `is_busy` — evita envíos concurrentes.
- `websocket_server_display_info` — datos del servidor (incluye `ip_local`).
- `errors` — contador de fallos consecutivos.
- `DEBUG`, `keylogger`, `api`, `DEVICE_ID`, `DEVICE_NAME`.

## Constructor `__init__(keylogger, api, debug=False)`

Guarda dependencias y lanza `prepare_client()` en un hilo.

## Métodos

### `prepare_client()`

Obtiene del API la información del servidor de pantalla, en bucle hasta lograrlo:

- Llama a `api.get_websocket_server_display_info()`.
- Si la respuesta trae la clave `device`, guarda `websocket_server_display_info`
  y sale.
- Aplica backoff creciente entre intentos (10 s; 30 s entre el 3.º y 6.º; 60 s a
  partir del 6.º).
- Marca `is_busy` durante el proceso.

### `update()`

Envía el estado actual al servidor de pantalla:

1. Si está ocupado o no hay info del servidor, sale.
2. Si `errors > 10`, vuelve a pedir los datos del servidor (`prepare_client`).
3. Compone el payload JSON:

   ```json
   {
     "device_id": "<DEVICE_ID>",
     "session": { "pulsations_total": <int> },
     "streak":  { "pulsations_current": <int>, "pulsation_average": <int> },
     "timestamp": "YYYY-MM-DD HH:MM:SS",
     "time": "HH:MM:SS",
     "system": { "so": "<DEVICE_NAME>" }
   }
   ```

4. Abre un socket TCP a `ip_local:80`, envía el JSON y lee la respuesta.
5. Si la respuesta trae `status == 'ok'`, resetea `errors`; si hay error de
   socket, incrementa `errors`.
6. En `finally`, libera `is_busy` y pausa (10 s si un solo error, 60 s si más).

`update()` lo invoca `KeyboardLogger.increase_pulsation` (en un hilo) cuando hay
pulsaciones y el cliente no está ocupado.

## Interacciones

- **Depende de:** `socket`, `json`, `datetime`, `_thread`; usa `ApiConnection`
  para descubrir el servidor y lee `keylogger.model_keyboard`.
- **Usado por:** `main.py` (lo crea si procede e inyecta en el keylogger).

## Notas para mejoras (ver documento 13)

- Nombre engañoso: no es WebSocket real; documentar o renombrar.
- Puerto `80` e id de dispositivo del servidor (`/device/16/info`)
  hardcodeados.
- `datetime.now()` local (no UTC como el resto del proyecto).
- Falta tipado consistente y control de reconexión más robusto.
