# 16 — Arranque y ejecución actual

Cómo se pone en marcha hoy el proyecto y qué limitaciones tiene ese mecanismo.
Documento de **estado actual**, no de propuestas.

---

## 1. Mecanismo actual

El arranque automático se hace añadiendo `main.py` a un **`cron @reboot`**
ejecutado **como root**, tal y como describe el README. El proceso queda
corriendo de forma permanente en segundo plano.

En **macOS**, además, la app `KeyCounterBar` se añade a los elementos de inicio
de sesión para mostrar los datos en la barra superior; el proceso Python se
lanza por separado.

Este esquema **lleva años funcionando** y es el que debe mantenerse mientras no
se decida cambiarlo.

## 2. Por qué hace falta root

| Motivo | Detalle |
|--------|---------|
| Captura de teclado | La librería `keyboard` exige root en Linux (lee `/dev/input`) |
| Socket UNIX | Se crea en `/var/run/keycounter.socket`, ruta privilegiada |
| Detección de dispositivos | Lee `/dev/input/by-id/` y `/proc/bus/input/devices` |

## 3. Limitaciones del arranque por cron

| Limitación | Consecuencia |
|------------|--------------|
| **Sin reinicio ante fallo** | Si el proceso muere (excepción no capturada, desconexión del puerto serie), no vuelve hasta el próximo reinicio |
| **Sin logs gestionados** | La salida son `print` que se pierden o acaban en el correo de cron |
| **Sin control del orden de arranque** | Puede lanzarse antes de que los dispositivos de entrada o la red estén listos |
| **Sin parada limpia** | No hay forma ordenada de detenerlo; socket, base de datos y puerto serie quedan sin cerrar |
| **Sin estado consultable** | No se puede preguntar de forma estándar si está corriendo |

## 4. Obstáculos en el código para gestionarlo como servicio

Tres elementos del código actual dificultan que un gestor de servicios aporte
valor real:

### 4.1. No hay manejo de señales

`main.loop()` es un `while True` con `sleep` fijos y sin captura de
`SIGTERM`/`SIGINT`. Una parada ordenada mataría el proceso de golpe, pudiendo
dejar rachas en memoria (`spurts`) sin volcar a la base de datos.

### 4.2. La salida son `print`, no `logging`

Impide integrarse con `journalctl` (Linux) o con los logs de `launchd` (macOS),
y obliga a repartir condicionales `if DEBUG:` por todo el código.

### 4.3. Rutas fijadas en el código

| Qué | Dónde | Implicación |
|-----|-------|-------------|
| Socket `/var/run/keycounter.socket` | `Models/Socket.py` | No configurable; en algunos sistemas la ruta canónica es `/run` |
| Base de datos `keycounter.db` | Directorio del script (vía `.env`) | Escribe en el directorio de instalación |
| Intérprete de Python | Arranque | Apunta al del sistema |

## 5. Mecanismos disponibles en cada plataforma

Referencia de qué ofrece cada sistema objetivo:

| Plataforma | Gestor de servicios | Particularidad |
|------------|---------------------|----------------|
| Debian | systemd | Caso estándar |
| Fedora | systemd | SELinux puede interferir |
| Raspberry OS | systemd | Caso estándar |
| SteamOS | systemd | Rootfs de **solo lectura**; las actualizaciones por imagen pueden revertir lo escrito en él |
| macOS | launchd | Los permisos de captura (**TCC**) se conceden por aplicación, lo que complica los demonios sin sesión |

La propuesta concreta de unidades y estrategia por plataforma está en la
planificación local (`docs/planning/02-despliegue-como-servicio.md`), fuera de
este repositorio.
