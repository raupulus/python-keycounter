# `main`

> Ruta real en el repositorio: `main.py`

## Qué hace y qué NO hace
Punto de entrada de la aplicación. Carga la configuración desde `.env`, instancia
los componentes (pantalla, keylogger, API, socket, cliente websocket) y ejecuta
el bucle periódico que vuelca las rachas a la base de datos local y, si procede,
las sube a la API.

**NO** captura pulsaciones por sí mismo (eso es de [keylogger](keylogger.md)),
**NO** define el esquema de datos (eso es de [keyboard-logger](keyboard-logger.md)
y [mouse-logger](mouse-logger.md)) ni gestiona directamente la conexión a la DB.

## Modelo de datos
No define modelo propio. Opera sobre los `spurts` (rachas) de los modelos de
teclado y ratón y sobre las tablas de [db-connection](db-connection.md).

## Flujos principales
1. `main()`
   - Crea `Display` sólo si `SERIAL_DISPLAY_ENABLED`.
   - Instancia `Keylogger` (arranca hilos de captura).
   - Instancia `ApiConnection`.
   - Instancia `Socket` y lo asocia al keylogger (`set_socket`).
   - Si `SEND_DATA_TO_WEBSOCKET_SERVER`, instancia `ClientDisplayWebsocket` y lo
     asocia (`set_client_display_websocket`).
   - Llama a `loop(...)`.
2. `loop(keylogger, socket, apiconnection, display)`
   - Crea `DbConnection`, registra las tablas `keyboard` y (si `MOUSE_ENABLED`)
     `mouse`.
   - Espera 30 s de margen para acumular datos.
   - Bucle infinito: `insert_data_in_db(...)` para teclado (y ratón), y si
     `UPLOAD_API` y hay token/URL, `upload_data_to_api(...)`. `sleep(10)` al final
     de cada iteración.
3. `insert_data_in_db(dbconnection, tablemodel)` — recorre `tablemodel.spurts`,
   guarda las rachas con datos válidos (`pulsations > 1` en teclado,
   `total_clicks > 1` en ratón) y elimina del map las guardadas.
4. `upload_data_to_api(dbconnection, apiconnection, tablemodel)` — sube los
   últimos `n_registers = 10` registros y, si la subida responde OK, los borra de
   la DB local.

## Puntos de entrada
- `main()` — ejecutado desde `if __name__ == "__main__"`.
- Requiere permisos de **root** en Linux/macOS para capturar teclado y crear el
  socket en `/var/run/`.

## Dependencias en ambos sentidos
- **Depende de:** `Models.DbConnection`, `Models.ApiConnection`,
  `Models.Display`, `Models.Socket`, `Models.ClientDisplayWebsocket`,
  `Models.Keylogger`, `python-dotenv`.
- **Le depende:** nadie (es la raíz de ejecución).

## Configuración
| Variable | Defecto | Efecto |
|----------|---------|--------|
| `SERIAL_PORT` | `None` | Puerto serie de la pantalla LCD. |
| `SERIAL_BAUDRATE` | `9600` | Baudios de la pantalla. |
| `SERIAL_DISPLAY_ENABLED` | `False` | Activa la pantalla LCD serie. |
| `DISPLAY_ORIENTATION` | `horizontal` | Orientación de la pantalla. |
| `MOUSE_ENABLED` | `False` (acepta `True`/`true`) | Registra también el ratón. |
| `DEBUG` | `False` | Traza por consola. |
| `UPLOAD_API` | `False` | Habilita la subida a la API. |
| `SEND_DATA_TO_WEBSOCKET_SERVER` | `False` | Activa el cliente de pantalla en red. |

## Trampas conocidas
- El bloque de `reboot` (recarga del keylogger al conectar dispositivos) está
  **comentado** en el bucle; el flag `keylogger.reboot` se activa pero no se actúa
  sobre él aquí.
- `upload_data_to_api` captura `except ():` (tupla vacía), que **no** atrapa
  ninguna excepción real; los errores de subida se gestionan dentro de
  `ApiConnection.send`.
- Hay `sleep(30)` inicial y varios `sleep` que retrasan la primera persistencia.

## Tests que lo cubren
Ninguno ⚠️.

## Pendiente real
- Decidir si se implementa o se elimina el bloque `reboot` comentado.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
