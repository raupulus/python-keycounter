# Configuración (`.env`)

La configuración se gestiona por **variables de entorno**, cargadas con
`python-dotenv` (`load_dotenv(override=True)`). Existe un `.env.example` como
plantilla; se copia a `.env` y se ajusta. `override=True` hace que el `.env`
tenga prioridad sobre variables ya presentes en el entorno.

> El `.env` cubre la configuración **en tiempo de ejecución** y funciona
> correctamente. Es distinto del **entorno de ejecución de Python** (intérprete y
> dependencias), que se analiza en
> [15. Entorno y dependencias](entorno-y-dependencias.md).

## Variables

### Base de datos (caché local)

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `DB_CONNECTION` | `sqlite` | Motor. Con `sqlite` la cadena es `sqlite:///<DB_DATABASE>`; otros motores usan usuario/host/puerto. |
| `DB_HOST` | `127.0.0.1` | Host (solo motores no SQLite). |
| `DB_PORT` | *(vacío)* | Puerto (opcional). |
| `DB_DATABASE` | `keycounter.db` | Nombre del fichero/BD. |
| `DB_USERNAME` | `dbuser` | Usuario (no SQLite). |
| `DB_PASSWORD` | `dbpassword` | Contraseña (no SQLite). |

### Sistema operativo y telemetría

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `SYSTEM_OS` | `auto` | Sistema operativo para telemetría de hardware (`auto`, `linux`, `macos`). |

### API remota

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `API_URL` | `http://example.com` | URL base de la API. |
| `API_TOKEN` | `apitoken` | Token Bearer de autenticación. |
| `UPLOAD_API` | `False` | Habilita la subida de estadísticas a la API. |

### Identificación del equipo

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `DEVICE_NAME` | `N/D` | Nombre legible del equipo (p. ej. "Sobremesa", "Dell XPS"). |
| `DEVICE_ID` | `1` | Identificador del equipo en la API (se guarda como `hardware_device_id`). |

### Pantalla serie (UART)

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `SERIAL_DISPLAY_ENABLED` | `False` | Activa la pantalla física por serie. |
| `SERIAL_PORT` | `/dev/ttyUSB1` | Puerto serie de la pantalla. |
| `SERIAL_BAUDRATE` | `115200` | Baudios. |
| `DISPLAY_ORIENTATION` | `horizontal` | `horizontal` o `vertical`. |
| `DISPLAY_ID` | `16` | ID del dispositivo pantalla en la API para consultar su IP local. |
| `DISPLAY_API_TOKEN` | `token` | Token propio del dispositivo pantalla para leer su info en la API v2. |

### Ratón

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `MOUSE_ENABLED` | `True` | Registra clicks de ratón (además carga la librería `mouse`). |

### Depuración

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `DEBUG` | `False` | Traza detallada por consola. |

### Pantalla en red (WebSocket/TCP)

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `SEND_DATA_TO_WEBSOCKET_SERVER` | `False` | Envía estadísticas a una pantalla/servidor en la red local. |

## Notas de interpretación de valores

- Los booleanos se leen comparando texto: normalmente `== "True"`. `MOUSE_ENABLED`
  acepta además `"true"`. **El resto son sensibles a mayúsculas** (`true` no
  equivale a `True`). Homogeneizar sería una mejora (ver documento 13).
- `SERIAL_PORT` por defecto es `None` en `main.py` si no está definido.

## Seguridad

- El `.env` está en `.gitignore` (no se versiona). El `.env.example` sí, con
  valores ficticios.
- `API_TOKEN` es un secreto: no debe compartirse ni subirse al repositorio.

## Relación con el código

Las variables se leen principalmente en `main.py`, `DbConnection`,
`ApiConnection`, `KeyboardLogger`/`MouseLogger` (`DEVICE_ID`) y
`ClientDisplayWebsocket` (`DEVICE_ID`, `DEVICE_NAME`).

---
> Creado: 2026-09-06 · Última revisión: 2026-09-07
