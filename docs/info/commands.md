# Comandos y scripts

Comandos verificados contra el repositorio y el `README.md`.

## Ejecución de la aplicación
Requiere **root** (captura de teclado y creación del socket en `/var/run/`).

```bash
sudo python3 main.py
```

Arranque automático en el inicio del sistema: añadir a un cron `@reboot`.

## Configuración previa
```bash
cp .env.example .env
# editar .env con los parámetros del entorno
```

## Dependencias

macOS:
```bash
sudo python3.12 -m pip install serial mouse keyboard sqlalchemy --break-system-packages
```

Linux (pip):
```bash
sudo pip3 install keyboard mouse serial sqlalchemy python-dotenv requests
```

Linux (Debian, repositorios):
```bash
sudo apt install python3-serial python3-dotenv python3-sqlalchemy python3-requests
```

## Comprobar el UNIX socket
```bash
nc -U /var/run/keycounter.socket
```
Cliente de ejemplo en Python:
```bash
python3 Debug/client_socket.py
```

## App de macOS (barra de estado)
Ver [../deploys/README.md](../deploys/README.md). Se distribuye compilada en
`macos/KeyCounterBar.app/` y el fuente Xcode en `macos/KeyCounterBar/`.

## Renombrar la pantalla UART (Linux)
Reglas udev para fijar el punto de montaje del puerto serie (ver `README.md`,
sección «Renombrar pantalla UART»).

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
