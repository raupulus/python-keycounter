# 06 — `DbConnection` (caché local SQLite / ORM)

**Archivo:** `Models/DbConnection.py`

## Objetivo del módulo

Gestiona la **caché persistente** de rachas. Crea las tablas dinámicamente a
partir del `tablemodel()` de cada modelo y ofrece operaciones CRUD sobre la base
de datos. Por defecto usa **SQLite** (`keycounter.db` junto al script), pero la
cadena de conexión admite otros motores de SQLAlchemy.

## Configuración de conexión

Lee del `.env` (con `load_dotenv(override=True)`):

`DB_CONNECTION`, `DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`,
`DB_PASSWORD`.

Construye la cadena de conexión:

- **SQLite:** `sqlite:///<DB_DATABASE>`.
- **Otros motores:** `<conn>://<user>:<pass>@<host>[:<port>]/<database>`.

Inicializa a nivel de clase: `engine = create_engine(str_conn)`, `meta =
MetaData()`, `connection = engine.connect()` y una `session` de SQLAlchemy para
operaciones por lote. `tables = {}` almacena las tablas registradas.

⚠️ Estos objetos se crean a **nivel de clase** (en tiempo de import), no en el
constructor. Ver documento 13.

## Métodos

### `table_set_new(tablename, parameters)`

Crea (o redefine) una tabla a partir del diccionario de columnas:

1. Añade siempre una columna `id` (Integer, PK, autoincrement).
2. Por cada columna del `parameters` traduce el `type` textual al tipo de
   SQLAlchemy: `Numeric` (con `params`), `DateTime`, `Integer`, `String` (con
   `params`); *fallback* a `String`.
3. Aplica los `others` (p. ej. `default=datetime.utcnow`).
4. Crea la `Table` con `extend_existing=True` (permite redefinir) y ejecuta
   `meta.create_all(engine)`.

**Objetivo:** que el esquema lo definan los modelos (`KeyboardLogger`,
`MouseLogger`) sin duplicar DDL aquí.

### `table_get_data(tablename)`

Devuelve todas las filas de la tabla (`select(table)`).

### `table_get_data_last(tablename, limit)`

Devuelve las últimas `limit` filas ordenando por `created_at DESC`. Se usa para
elegir qué subir a la API.

### `table_save_data(tablename, params)`

Inserta una fila y devuelve el `id` generado (`INSERT … RETURNING id`) con
commit. En caso de `SQLAlchemyError` hace `rollback` y devuelve `None`.

### `table_truncate(tablename)`

Borra todas las filas de la tabla.

### `table_drop_last_elements(tablename, limit)`

Elimina las últimas `limit` filas (las que se acaban de subir a la API):
obtiene sus `id` con `table_get_data_last` y ejecuta un `DELETE … WHERE id IN
(...)` usando la `session`, con `commit`/`rollback`.

### `get_all_data()` / `truncate_all_table_data()`

Declaradas pero **vacías** (`pass`). Reservadas para el futuro.

### `truncate_db()`

Vacía todas las tablas. Usa sentencias `SET FOREIGN_KEY_CHECKS` propias de
MySQL; **no es válido en SQLite**. Ver documento 13.

### `close_connection()`

Cierra la conexión y la sesión.

## Flujo típico

1. `main.loop` llama a `table_set_new('keyboard', KeyboardLogger().tablemodel())`
   (y lo mismo para `mouse`).
2. Cada iteración: `insert_data_in_db` → `table_save_data` por cada racha.
3. Al subir a la API: `table_get_data_last` → subida → `table_drop_last_elements`.

## Interacciones

- **Depende de:** SQLAlchemy, `python-dotenv`, y de los `tablemodel()` de los
  modelos.
- **Usado por:** `main.py`.

## Notas para mejoras (ver documento 13)

- Estado a nivel de clase (engine/conexión compartidos globalmente); mejor
  moverlo al constructor.
- `truncate_db()` usa SQL específico de MySQL incompatible con SQLite.
- Mezcla de estilos de acceso (conexiones `with engine.connect()` y `session`).
- Falta tipado y control de errores homogéneo.
