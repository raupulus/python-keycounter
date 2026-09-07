# Matriz de compatibilidad por plataforma

Estado real de cada capacidad en las cinco plataformas objetivo, deducido del
código y contrastado con la documentación de las librerías. Sirve para saber
**qué se puede prometer en cada sistema** antes de plantear mejoras.

Leyenda: ✅ funciona · ⚠️ funciona con matices · ❌ no funciona · ➖ no aplica

## Matriz general

| Capacidad | Debian | Fedora | SteamOS | macOS | Raspberry OS |
|-----------|:------:|:------:|:-------:|:-----:|:------------:|
| Captura de teclado (`keyboard`) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Captura de ratón (`mouse`) | ✅ | ✅ | ✅ | ❌ | ✅ |
| Detección de dispositivos (`read_devices_by_id`) | ✅ | ✅ | ✅ | ❌ | ✅ |
| Recarga al conectar teclado USB | ✅ | ✅ | ✅ | ❌ | ✅ |
| Socket UNIX (`/var/run/keycounter.socket`) | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| Caché SQLite | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| Subida a la API | ✅ | ✅ | ✅ | ✅ | ✅ |
| Pantalla UART (`Display`/`LCDUart`) | ✅ | ✅ | ⚠️ | ⚠️ | ✅ |
| Reglas udev para puerto serie estable | ✅ | ✅ | ⚠️ | ➖ | ✅ |
| Pantalla en red (`ClientDisplayWebsocket`) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cliente de barra de estado | ✅ i3pystatus | ✅ i3pystatus | ⚠️ | ✅ KeyCounterBar | ⚠️ |
| Arranque como servicio | systemd | systemd | ⚠️ systemd | launchd | systemd |

## Detalle por capacidad

### Captura de teclado

Depende de la librería `keyboard`. En **Linux** lee `/dev/input` y **exige
root**.

En **macOS funciona de forma estable: lleva años en producción sin fallar**, y
es lo que alimenta la app `KeyCounterBar`. La documentación de la librería
etiqueta su soporte de macOS como "experimental", pero la experiencia real de
este proyecto lo desmiente: conviene tenerlo presente al leer esa etiqueta, no
tomarla como una limitación operativa.

⚠️ **La librería `keyboard` está sin mantenimiento**: su repositorio fue
archivado por el autor el **13 de febrero de 2026**, y la última versión
publicada es la **0.13.5**. Esto convierte el fijado de versión en obligatorio
(ver documento 15) y hace que cualquier rotura futura tenga que resolverla el
propio proyecto.

### Captura de ratón

Depende de la librería `mouse` (última versión **0.7.1**), que declara soporte
oficial para **Windows y Linux**. En **macOS** es donde se produce el fallo
conocido de este proyecto:

- Requiere permisos de **Accesibilidad / Monitorización de entrada** en
  Ajustes del Sistema → Privacidad y seguridad.
- Existen incidencias reportadas en la propia librería con `on_click()` en
  macOS (el callback no se invoca, o el programa termina al hacer click).

Es decir, el fallo está **en la librería/permisos, no en la lógica de
KeyCounter**. Alternativas a evaluar: `pynput`, Quartz Event Taps nativos, o un
backend específico por plataforma.

### Detección de dispositivos y recarga

`Keylogger.read_devices_by_id()` ejecuta `ls /dev/input/by-id/` y lee
`/proc/bus/input/devices`. Ambas rutas son **exclusivas de Linux**, así que en
macOS la detección no funciona y, por tanto, tampoco la recarga automática al
conectar un teclado USB.

⚠️ **Riesgo latente en macOS:** si esa comparación llegase a detectar un cambio,
`reload_keycounter_on_new_device` accede a `keyboard._nixkeyboard`, que **no
existe en macOS** (allí la librería usa su backend Darwin) y lanzaría
`AttributeError` dentro del hilo. Hoy no se dispara porque la salida de error es
constante, pero es un fallo esperando a ocurrir.

### Socket UNIX

Funciona en Linux y macOS (de hecho la app de macOS lo consume). Requiere
permisos de escritura en `/var/run`, de ahí la ejecución como root. En algunos
sistemas la ruta canónica es `/run` (`/var/run` suele ser un enlace simbólico).

En **SteamOS** hay que verificar la persistencia y permisos de la ruta por el
sistema de archivos de solo lectura.

### Caché SQLite

Se crea `keycounter.db` **en el mismo directorio del script**. En SteamOS, si el
proyecto se instala en una zona de solo lectura, la escritura fallará: conviene
mover la base de datos a una ruta persistente y escribible (ver documento 16).

### Pantalla UART

Depende de `pyserial` y de la ruta del puerto:

- **Linux/Raspberry:** `/dev/ttyUSB0`, `/dev/ttyACM0`… con reglas **udev** para
  fijar un `SYMLINK` estable.
- **macOS:** los dispositivos se llaman `/dev/tty.usbserial-*` o
  `/dev/cu.usbserial-*`; **no hay udev**, hay que fijar el nombre manualmente en
  `SERIAL_PORT`.
- **SteamOS:** escribir reglas udev en `/etc/udev/rules.d` choca con el rootfs
  inmutable y puede perderse en actualizaciones.

### Arranque como servicio

Hoy el arranque se hace con `cron @reboot` como root en todas las plataformas.
Los gestores disponibles serían `systemd` en Debian, Fedora, Raspberry OS y
SteamOS, y `launchd` en macOS, con los matices de SteamOS (rootfs de solo
lectura) y de macOS (permisos TCC). Estado actual y limitaciones en
[16. Arranque y ejecución actual](despliegue-como-servicio.md).

## Conclusiones

1. **La función principal —contar pulsaciones de teclado— funciona en las cinco
   plataformas**, macOS incluido, donde lleva años estable.
2. **Las carencias de macOS son periféricas**: clicks de ratón y detección de
   dispositivos, más un `AttributeError` latente. No afectan al núcleo.
3. **La captura depende de dos librerías sin mantenimiento activo** (`keyboard`
   archivada, `mouse` con incidencias abiertas). Es el mayor riesgo estructural
   a medio plazo, aunque hoy no cause problemas.
4. **SteamOS necesita un tratamiento propio** por su sistema de archivos
   inmutable: rutas de instalación, base de datos, socket y reglas udev.
5. Todo lo que es **red y persistencia** (API, SQLite, pantalla en red) es
   portable sin problemas.

## Fuentes

- [boppreh/keyboard (GitHub)](https://github.com/boppreh/keyboard) — soporte de
  plataformas, requisito de root y estado del repositorio.
- [keyboard en PyPI](https://pypi.org/project/keyboard/) — última versión 0.13.5.
- [boppreh/mouse (GitHub)](https://github.com/boppreh/mouse) — plataformas
  soportadas.
- [mouse en PyPI](https://pypi.org/project/mouse/) — versiones publicadas.
- [Incidencia `on_click()` en boppreh/mouse](https://github.com/boppreh/mouse/issues/26)
  — fallo de detección de clicks.
- [everythingishacked/keyboard](https://github.com/everythingishacked/keyboard) —
  fork con correcciones para Mac Silicon (alternativa a evaluar).

---
> Creado: 2026-09-06 · Última revisión: 2026-09-07
