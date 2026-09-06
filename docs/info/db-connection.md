# `db-connection`

> Ruta real en el repositorio: `Models/DbConnection.py`

## Qué hace y qué NO hace
Caché local de datos usando SQLAlchemy Core. Crea tablas dinámicamente a partir
del esquema que devuelven los modelos (`tablemodel()`), inserta rachas, consulta
los últimos N registros y los elimina tras subirlos a la API. Por defecto usa
SQLite en el fichero `keycounter.db`.

**NO** define el esquema (lo reciben de los modelos) ni sube nada a la API.

## Modelo de datos
- `tables: dict` — tablas SQLAlchemy registradas en runtime por nombre.
- Cada tabla añade una columna `id` autoincremental como PK y el resto según el
  `tablemodel()` del modelo correspondiente (tipos soportados: `Numeric`,
  `DateTime`, `Integer`, `String`; fallback `String`).

## Flujos principales
1. `table_set_new(tablename, parameters)` — construye columnas y crea la tabla
   (`create_all`) con `extend_existing=True`.
2. `table_save_data(tablename, params)` — inserta con `RETURNING id`; hace
   `rollback` ante `SQLAlchemyError`.
3. `table_get_data_last(tablename, limit)` — últimos registros por
   `created_at DESC`.
4. `table_drop_last_elements(tablename, limit)` — borra por lista de `id`
   obtenida del punto anterior.
5. `table_get_data`, `table_truncate` — utilidades adicionales.

## Puntos de entrada
- `DbConnection()`.
- `table_set_new`, `table_save_data`, `table_get_data_last`,
  `table_drop_last_elements`, `table_get_data`, `table_truncate`,
  `close_connection`.

## Dependencias en ambos sentidos
- **Depende de:** `sqlalchemy`, `python-dotenv`.
- **Le depende:** [main](main.md) (única llamante de sus métodos).

## Configuración
| Variable | Defecto (.env.example) | Efecto |
|----------|------------------------|--------|
| `DB_CONNECTION` | `sqlite` | Motor. `sqlite` → cadena `sqlite:///<db>`; otro → `motor://user:pass@host[:port]/db`. |
| `DB_DATABASE` | `keycounter.db` | Nombre/ruta de la base de datos. |
| `DB_HOST` | `127.0.0.1` | Host (no-SQLite). |
| `DB_PORT` | vacío | Puerto (se añade si `> 0`). |
| `DB_USERNAME` | `dbuser` | Usuario (no-SQLite). |
| `DB_PASSWORD` | `dbpassword` | Contraseña (no-SQLite). |
| `DEBUG` | `False` | Traza SQL y errores. |

## Trampas conocidas
- La conexión y la `Session` se abren **a nivel de clase** (se crean al importar
  el módulo, no por instancia).
- `truncate_db()` ejecuta `SET FOREIGN_KEY_CHECKS` (sintaxis MySQL) y no funciona
  en SQLite; `get_all_data`, `truncate_all_table_data` son `pass` (sin
  implementar).
- El fichero `keycounter.db` está en `.gitignore`.

## Tests que lo cubren
Ninguno ⚠️.

## Pendiente real
- Implementar `get_all_data`, `truncate_all_table_data` (actualmente `pass`).
- Revisar `truncate_db` para SQLite.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
