# Guías de despliegue

## Linux (proceso principal)
1. Instalar dependencias (ver [../info/commands.md](../info/commands.md)).
2. Configurar `.env` a partir de `.env.example`.
3. Ejecutar como root:
   ```bash
   sudo python3 main.py
   ```
4. Arranque automático: añadir a cron `@reboot` para dejarlo en segundo plano.

Requisitos: root (captura de teclado + socket en `/var/run/`). En Linux funciona
la lectura de dispositivos por `/dev/input` y `/proc/bus/input/devices`.

## macOS (proceso principal)
1. Instalar dependencias:
   ```bash
   sudo python3.12 -m pip install serial mouse keyboard sqlalchemy --break-system-packages
   ```
2. Conceder permisos de accesibilidad/monitorización de entrada al intérprete.
3. Ejecutar como root: `sudo python3 main.py`.

> La detección de dispositivos en caliente ([keylogger](../info/keylogger.md)) usa
> comandos de Linux; en macOS esa parte no aplica.

## macOS (app de barra de estado)
Cliente visualizador del socket ([macos-keycounterbar](../info/macos-keycounterbar.md)).
- Uso directo: arrastrar `macos/KeyCounterBar.app` a `Aplicaciones` y añadirla a
  los elementos de inicio de sesión.
- Compilar desde fuente: abrir `macos/KeyCounterBar/KeyCounterBar.xcodeproj` en
  Xcode y compilar (dependencias SwiftNIO vía Swift Package Manager).

Requiere que el proceso Python esté corriendo y el socket
`/var/run/keycounter.socket` sea legible.

## Pantalla LCD serie (opcional)
Activar con `SERIAL_DISPLAY_ENABLED=True` y configurar `SERIAL_PORT`,
`SERIAL_BAUDRATE`, `DISPLAY_ORIENTATION`. Para fijar el puerto ante renombrados,
crear una regla udev (ver `README.md`, «Renombrar pantalla UART»).

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
