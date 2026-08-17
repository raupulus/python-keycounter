# 08 — Socket UNIX

**Archivos:** `Models/Socket.py` y `Debug/client_socket.py` (cliente de ejemplo)

## Objetivo del módulo

Expone las estadísticas **en tiempo real** a otros programas del sistema
mediante un **socket UNIX** (`AF_UNIX`, tipo `SOCK_STREAM`) en la ruta
`/var/run/keycounter.socket`. Cualquier proceso local puede conectarse y recibir
las pulsaciones actuales sin acoplarse al código de KeyCounter.

Uso típico del autor: mostrar las pulsaciones en la barra de estado
**i3pystatus** (entornos i3wm / sway) y en la app de la barra de menús de macOS.

## `Socket`

### Atributos

- `server_address = '/var/run/keycounter.socket'` — ruta del socket.
- `sock` — instancia del socket.
- `keylogger` — referencia para leer sus estadísticas.
- `max_clients = 99` — máximo de clientes simultáneos.
- `wait_client_connection` — flag de espera.
- `clients_list` — lista de clientes conectados (dicts con `connection` y
  `client_address`).

### Constructor `__init__(keylogger, has_debug=False)`

1. Guarda el `keylogger`.
2. `delete_old_socket()` — elimina un socket previo si existiera.
3. Crea el socket UNIX, hace `bind` en `server_address` y `listen(max_clients)`.
4. `change_permissions_socket()` — `chmod 0o666` para permitir lectura a otros
   usuarios.
5. Lanza `startWaitClients` en un hilo.

### `startWaitClients()`

Bucle que, mientras haya hueco (`< max_clients`), espera nuevos clientes con
`wait_client()`; si está lleno, duerme 10 s.

### `delete_old_socket()`

Intenta `os.unlink(server_address)`; si el fichero existe y no se puede borrar,
propaga el error.

### `change_permissions_socket()`

`os.chmod(server_address, 0o666)` — lectura/escritura para todos (la escritura
no es necesaria hoy, pero se concede).

### `wait_client()`

Bloquea en `sock.accept()` hasta que llega un cliente y lo añade a
`clients_list`. Maneja errores y actualiza `wait_client_connection`.

### `update()`

Recorre `clients_list` y a cada cliente le envía el estado actual en JSON:

```json
{
  "session": { "pulsations_total": <int> },
  "streak":  { "pulsations_current": <int>, "pulsation_average": <int> }
}
```

Si el envío falla (cliente desconectado) o el cliente no es válido, lo elimina de
la lista. `update()` lo invoca `KeyboardLogger.increase_pulsation` en cada
pulsación, de modo que los clientes reciben datos "push" en vivo.

## Cliente de ejemplo — `Debug/client_socket.py`

Script de demostración/depuración: se conecta a `/var/run/keycounter.socket` y
va imprimiendo lo que recibe en un bucle `while sock.listen`. Sirve como
plantilla para integrar el socket desde otras aplicaciones.

Comprobación rápida desde terminal:

```bash
nc -U /var/run/keycounter.socket
```

## Interacciones

- **Depende de:** `socket`, `os`, `json`, `_thread`; lee `keylogger.model_keyboard`.
- **Usado por:** `main.py` (lo crea e inyecta en el keylogger); clientes
  externos (i3pystatus, app macOS `KeyCounterBar`, `Debug/client_socket.py`).

## Notas para mejoras (ver documento 13)

- Ruta `/var/run` requiere privilegios (root); en algunos sistemas conviene
  `/run` o una ruta configurable. Es una de las razones por las que hoy se
  ejecuta como root.
- Protocolo unidireccional (solo push); no interpreta peticiones del cliente.
- `AF_UNIX` no existe en Windows (no soportado, pero a tener en cuenta).
- Falta tipado y una parada limpia del hilo.
