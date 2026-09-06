# `socket`

> Ruta real en el repositorio: `Models/Socket.py`

## Qué hace y qué NO hace
Servidor de **UNIX domain socket** que expone las estadísticas de teclado en
tiempo real a otros procesos (barra de estado, `nc -U`, la app de macOS…). Crea
el socket en `/var/run/keycounter.socket`, acepta clientes y les envía JSON cada
vez que `update()` es invocado desde el modelo de teclado.

**NO** captura ni persiste datos; sólo reenvía estadísticas del keylogger.

## Modelo de datos
JSON enviado a cada cliente en `update()`:
```json
{
  "session": { "pulsations_total": <int> },
  "streak": {
    "pulsations_current": <int>,
    "pulsation_average": <int>
  }
}
```
- `clients_list: list[dict]` — clientes conectados (`connection`, `client_address`).

## Flujos principales
1. `__init__` — borra el socket previo, crea el `AF_UNIX`/`SOCK_STREAM`, hace
   `bind` + `listen`, ajusta permisos a `0o666` y lanza `startWaitClients` en un
   hilo.
2. `startWaitClients()` — acepta clientes mientras haya menos de `max_clients`
   (99).
3. `update()` — recorre `clients_list`, serializa las estadísticas actuales y hace
   `sendall`; elimina de la lista los clientes que fallan. Lo invoca
   `KeyboardLogger.increase_pulsation`.

## Puntos de entrada
- `Socket(keylogger, has_debug)`.
- `update()` — llamado por el modelo de teclado.
- **Permisos:** el socket se crea con `0o666`; requiere escribir en `/var/run/`
  (root). Cliente de ejemplo en `Debug/client_socket.py`.

## Dependencias en ambos sentidos
- **Depende de:** `socket`, `os`, `json`, keylogger (para leer estadísticas).
- **Le depende:** [main](main.md), [keyboard-logger](keyboard-logger.md) (llama a
  `update`), y clientes externos ([macos-keycounterbar](macos-keycounterbar.md),
  i3pystatus…).

## Configuración
Sin variables de entorno. Constantes de clase: `server_address`
(`/var/run/keycounter.socket`), `max_clients` (99).

## Trampas conocidas
- Ruta fija en `/var/run/`, que exige **root**; para cambiarla hay que editar
  `server_address`.
- `update()` puede modificar `clients_list` mientras la itera al eliminar
  clientes caídos.

## Tests que lo cubren
Ninguno ⚠️. Existe un cliente manual de prueba en `Debug/client_socket.py` (ver
[commands.md](commands.md)).

## Pendiente real
- Ninguno verificado en el código.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
