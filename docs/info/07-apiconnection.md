# 07 — `ApiConnection` (subida de estadísticas a la API)

**Archivo:** `Models/ApiConnection.py`

## Objetivo del módulo

Envía las estadísticas cacheadas a una **API remota** propia. Se encarga de la
serialización a JSON, de la autenticación por token y de reintentar los envíos
HTTP fallidos. La subida solo se activa si `UPLOAD_API=True` y hay `API_URL` y
`API_TOKEN`.

## Configuración

Lee del `.env`: `API_URL`, `API_TOKEN`, `DEBUG`.

## Métodos

### `requests_retry_session(retries=3, backoff_factor=0.3, status_forcelist=(500,502,504), session=None)`

Crea una `requests.Session` con una política de reintentos (`urllib3.Retry`)
montada sobre `http://` y `https://`. Reintenta ante errores de conexión,
lectura y los códigos 500/502/504, con backoff exponencial.

### `send(path, datas_json, method)`

Hace el `POST` real a `API_URL + path`:

- Cabeceras: `Content-type: application/json`, `Accept: application/json`,
  `Authorization: Bearer <API_TOKEN>`.
- Envía `datas_json` como cuerpo, con `timeout=30`.
- Interpreta la respuesta: `201` → éxito (`True`); `200` → éxito parcial
  (algunos elementos con error, pero `True`); cualquier otro → `False`.
- Ante excepción, espera 5 s y devuelve `False`.

⚠️ El parámetro `method` se recibe pero **siempre se hace `POST`**; hay `TODO`
para soportar GET/PUT/DELETE y para añadir metadatos del dispositivo. Ver
documento 13.

### `parse_array_to_json(rows, columns)`

Convierte una lista de tuplas de la base de datos en un JSON (array de objetos),
emparejando cada valor con su columna y **omitiendo la columna `id`**. Formatea
con `ensure_ascii=False`, `sort_keys=True`, `indent=4`.

⚠️ Definido pero **no se usa** en el flujo actual (se usa `parse_to_json` fila a
fila). Ver documento 13.

### `parse_to_json(row, columns)`

Convierte **una fila** en un objeto JSON:

- Convierte `Decimal` a `float` y `datetime` a cadena `"%Y-%m-%d %H:%M:%S"`.
- Omite la columna `id`.
- Serializa con `json.dumps` (configuración por defecto ASCII).

### `upload(name, path, datas, columns, method='GET')`

Orquesta la subida: recorre las filas (`datas`), serializa cada una con
`parse_to_json` y las envía con `send(...)`. Devuelve `True` si al menos un envío
tuvo éxito.

⚠️ El parámetro `method` por defecto es `'GET'` aunque `send` siempre hace POST;
inconsistencia a limpiar.

### `get_websocket_server_display_info()`

Pide a la API la información del dispositivo que actúa como **servidor de
pantalla WebSocket** en la red local. Hace `GET` a
`/hardware/v1/get/device/16/info` y devuelve el JSON (o `None` si falla). El id
`16` está **hardcodeado**. Lo consume `ClientDisplayWebsocket`. Ver documento 13.

## Flujo típico

`main.upload_data_to_api` → `apiconnection.upload(name, path, filas, columnas)`
→ por cada fila `parse_to_json` + `send` → si OK, `main` borra esas filas de la
caché local.

## Privacidad

Solo se envían campos **estadísticos** (timestamps de racha, número de
pulsaciones/clicks, medias, puntuación, día de la semana, id de dispositivo).
No se envía qué se ha tecleado.

## Interacciones

- **Depende de:** `requests`, `urllib3`, `python-dotenv`.
- **Usado por:** `main.py` (subida) y `ClientDisplayWebsocket` (descubrimiento
  del servidor de pantalla).

## Notas para mejoras (ver documento 13)

- Parámetro `method` sin efecto (siempre POST) e inconsistente entre `upload` y
  `send`.
- `id` del dispositivo servidor de pantalla hardcodeado (`/device/16/info`).
- `parse_array_to_json` sin uso.
- `TODO` pendientes: validar método, empaquetar en array, añadir metadatos.
- Falta tipado.
