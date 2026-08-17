# 02 — `main.py` y el bucle principal

**Archivo:** `main.py`

## Objetivo del módulo

Es el **punto de entrada** de la aplicación. Se encarga de:

1. Cargar la configuración desde el `.env`.
2. Instanciar y conectar todos los componentes (captura, socket, API,
   pantallas).
3. Ejecutar el **bucle temporal** que persiste las rachas en la base de datos
   local y, si procede, las sube a la API.

## Carga de configuración

Al importarse, ejecuta `load_dotenv(override=True)` y lee las variables de
entorno hacia constantes de módulo con valores por defecto:

| Constante | Variable `.env` | Defecto | Uso |
|-----------|-----------------|---------|-----|
| `SERIAL_PORT` | `SERIAL_PORT` | `None` | Puerto serie de la pantalla UART. |
| `SERIAL_BAUDRATE` | `SERIAL_BAUDRATE` | `'9600'` | Baudios de la pantalla. |
| `SERIAL_DISPLAY_ENABLED` | `SERIAL_DISPLAY_ENABLED` | `False` | Activa la pantalla física. |
| `DISPLAY_ORIENTATION` | `DISPLAY_ORIENTATION` | `'horizontal'` | Orientación de la pantalla. |
| `MOUSE_ENABLED` | `MOUSE_ENABLED` | `False` | Activa el registro del ratón (acepta `True`/`true`). |
| `DEBUG` | `DEBUG` | `False` | Traza por consola. |
| `UPLOAD_API` | `UPLOAD_API` | `False` | Habilita la subida a la API. |
| `SEND_DATA_TO_WEBSOCKET_SERVER` | `SEND_DATA_TO_WEBSOCKET_SERVER` | `False` | Habilita el envío a pantalla en red. |

## Funciones

### `insert_data_in_db(dbconnection, tablemodel)`

Vuelca las rachas cerradas del modelo (`tablemodel.spurts`) a la base de datos.

- Recorre `tablemodel.spurts`. Para cada racha comprueba que tenga datos
  significativos:
  - teclado: `pulsations > 1`
  - ratón: `total_clicks > 1`
- Si la racha es válida, la inserta con `dbconnection.table_save_data(...)`. Si
  no lo es, la marca igualmente como "guardada" (`save_data = True`) para
  descartarla.
- Acumula en `saved` las claves de las rachas procesadas y, al final, las
  **elimina de `spurts`** para no reprocesarlas.
- Envuelve cada iteración en `try/except` para que un registro problemático no
  detenga el resto.

**Objetivo:** trasladar el estado en memoria (volátil) a la caché persistente,
liberando memoria de rachas ya consolidadas.

### `upload_data_to_api(dbconnection, apiconnection, tablemodel)`

Sube a la API los últimos registros de la tabla del modelo.

- Toma `n_registers = 10` filas recientes con
  `dbconnection.table_get_data_last(...)`.
- Obtiene los nombres de columnas del esquema.
- Llama a `apiconnection.upload(name, path, params_from_db, columns)`.
- Si la respuesta es correcta, borra esos registros de la caché local con
  `dbconnection.table_drop_last_elements(...)`.

⚠️ El manejo de errores usa `except ():` (tupla vacía), que **no captura
ninguna excepción**. Ver documento 13.

### `loop(keylogger, socket, apiconnection=None, display=None)`

Bucle principal, vive en el hilo principal.

1. Crea `DbConnection()`.
2. Registra la tabla de teclado con `table_set_new(tablename, tablemodel())`.
3. Si hay ratón, registra también su tabla.
4. Espera **30 s** para dar margen a acumular datos.
5. Entra en `while True`:
   - `insert_data_in_db` para teclado (y ratón si `MOUSE_ENABLED`).
   - Si `UPLOAD_API` y hay `apiconnection` con token y URL, sube a la API
     teclado (y ratón).
   - `finally: sleep(10)` entre iteraciones.

Contiene un bloque comentado de "reboot" (reinstanciar `Keylogger`/`Socket`
cuando cambian dispositivos) que **no está activo**.

### `main()`

Orquesta el arranque:

1. Crea `Display(...)` solo si `SERIAL_DISPLAY_ENABLED`.
2. Crea `Keylogger(display=…, has_debug=DEBUG, mouse_enabled=MOUSE_ENABLED)` —
   esto ya arranca la captura en hilos.
3. Crea `ApiConnection()`.
4. Crea `Socket(keylogger, has_debug=DEBUG)` y lo asocia al keylogger con
   `keylogger.set_socket(socket)`.
5. Si `SEND_DATA_TO_WEBSOCKET_SERVER`, crea `ClientDisplayWebsocket(...)` y lo
   asocia con `keylogger.set_client_display_websocket(...)`.
6. Llama a `loop(...)`.

### Bloque de arranque

```python
if __name__ == "__main__":
    main()
```

## Interacciones

- **Depende de:** `Keylogger`, `DbConnection`, `ApiConnection`, `Display`,
  `Socket`, `ClientDisplayWebsocket`.
- **Consumido por:** el sistema operativo (arranque como root, hoy vía
  `cron @reboot`).

## Notas para mejoras (ver documento 13)

- `except ():` en `upload_data_to_api` no captura errores.
- Uso de `sleep` fijos y `while True` sin señal de parada limpia.
- Estado compartido entre hilos sin sincronización.
- `functions.py` y `configuration.py` existen pero están **vacíos**; serían el
  lugar natural para extraer utilidades y centralizar la configuración.
