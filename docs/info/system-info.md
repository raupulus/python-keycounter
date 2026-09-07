# `system-info`

> Ruta real en el repositorio: `Models/SystemInfo.py`

## Qué hace y qué NO hace
Recolector de telemetría y métricas básicas de hardware (`cpu`, `ram`, `disk`,
`temp`, `uptime`, `battery_level`, `voltage`, `ip_local`, `extra`) para adjuntar
el objeto `hardware_device_info` en las peticiones a la API V2 antes de subir las
rachas. Implementa clases nativas separadas para GNU/Linux (`LinuxSystemInfo`) y
macOS (`MacosSystemInfo`) sin requerir dependencias externas como `psutil`. Todos
los métodos están aislados con manejo de excepciones defensivo y tiempos límite
estrictos en subprocesos para garantizar que ningún fallo bloquee o interfiera en
la captura o subida de pulsaciones.

**NO** envía datos HTTP por su cuenta (eso lo hace [api-connection](api-connection.md)
a petición de [main](main.md)), **NO** almacena métricas en la base de datos local
ni depende de paquetes externos adicionales.

## Modelo de datos
Devuelve un diccionario estructurado que coincide con el contrato de la API V2
(`hardware_device_info` / `PUT /hardware/devices/{id}/status`):

| Clave | Tipo | Descripción |
|-------|------|-------------|
| `cpu` | float \| null | Porcentaje de uso de CPU (0.0 a 100.0). |
| `ram` | float \| null | Porcentaje de uso de memoria RAM (0.0 a 100.0). |
| `disk` | float \| null | Porcentaje de uso del disco principal `/` (0.0 a 100.0). |
| `temp` | float \| null | Temperatura de la CPU en grados Celsius (º C). |
| `uptime` | int \| null | Tiempo encendido del equipo en segundos. |
| `battery_level` | int \| null | Nivel de batería en porcentaje (0 a 100) si existe. |
| `voltage` | float \| null | Voltaje de la batería en voltios si está disponible. |
| `ip_local` | string \| null | Dirección IP en la red local. |
| `extra` | dict \| null | Metadatos contextuales en tipos escalares simples: `os`, `os_version` o `kernel`, `hostname`, `architecture`, `load_avg_1m`, `load_avg_5m`, `load_avg_15m`. |

## Flujos principales
1. **Instanciación y selección de SO**: `SystemInfo.create(os_type, debug)` evalúa
   `SYSTEM_OS` del entorno; si es `'auto'` o no está definido, consulta
   `platform.system()`. Devuelve una instancia de `MacosSystemInfo` en Darwin o
   `LinuxSystemInfo` en Linux.
2. **Obtención con caché (`get_hardware_device_info(use_cache=True)`)**:
   - Comprueba si existe una lectura en caché de menos de `CACHE_TTL` (30 segundos).
   - Si caducó o no existe, ejecuta las llamadas de cada métrica protegidas por
     bloques `try...except` independientes.
   - Guarda el resultado en caché y lo retorna.
3. **Métricas en GNU/Linux (`LinuxSystemInfo`)**:
   - `cpu`: lectura delta de `/proc/stat`.
   - `ram`: lectura y cálculo de `/proc/meminfo` (`100 * (1 - MemAvailable / MemTotal)`).
   - `uptime`: primer valor de `/proc/uptime`.
   - `battery_level`: lectura de `/sys/class/power_supply/*/capacity`.
   - `voltage`: lectura de `/sys/class/power_supply/*/voltage_now` o `voltage_avg` en microvoltios y conversión a voltios.
   - `temp`: lectura de zonas térmicas `/sys/class/thermal/thermal_zone*` filtrando por tipo CPU (`cpu`, `pkg`, `core`, `soc`, `k10temp`) o `/sys/class/hwmon/`.
   - `extra`: lectura de `PRETTY_NAME` en `/etc/os-release`, arquitectura y promedios de carga escalares.
4. **Métricas en macOS (`MacosSystemInfo`)**:
   - `cpu`: parseo de porcentaje idle mediante `top -l 1 -n 0` con timeout de 3 s.
   - `ram`: combinación de `sysctl -n hw.memsize` y `vm_stat` (páginas activas, wired y especulativas).
   - `uptime`: diferencia entre `time.time()` y el valor `sec` de `sysctl -n kern.boottime`.
   - `battery_level`: parseo de `pmset -g batt` con timeout de 2 s.
   - `voltage`: consulta de `AppleSmartBattery` mediante `ioreg -r -n AppleSmartBattery -a` y extracción de `Voltage` en milivoltios convirtiendo a voltios vía `plistlib`.
   - `temp`: lectura de sensores térmicos de núcleos CPU (`PMU tdie`) vía `IOHIDEventSystemClient` de IOKit/CoreFoundation mediante `ctypes` (nativo en Apple Silicon e Intel, sin requerir root ni herramientas externas). Si fallase, busca binarios alternativos (`osx-cpu-temp`, `smctemp`, `istats`).
   - `extra`: versión de macOS (`platform.mac_ver()`), arquitectura y promedios de carga escalares.
5. **Métricas comunes (biblioteca estándar)**:
   - `disk`: `shutil.disk_usage('/')`.
   - `ip_local`: conexión de enrutamiento sin tráfico sobre socket UDP a `8.8.8.8:80`.

## Puntos de entrada
- `SystemInfo.create(os_type=None, debug=False)`: método estático de factoría.
- `get_hardware_device_info(use_cache=True)`: retorna el diccionario de métricas.
- Métodos individuales: `get_cpu_usage()`, `get_ram_usage()`, `get_disk_usage()`,
  `get_temperature()`, `get_uptime()`, `get_battery_level()`, `get_voltage()`,
  `get_ip_local()`, `get_extra()`.

## Dependencias en ambos sentidos
- **Depende de:** biblioteca estándar de Python (`os`, `platform`, `subprocess`,
  `shutil`, `socket`, `time`, `re`, `glob`, `plistlib`, `ctypes`). **Cero dependencias externas**.
- **Le depende:** [main](main.md) (lo instancia y solicita el estado de hardware
  antes de subir las rachas a la API).

## Configuración
| Variable | Defecto | Efecto |
|----------|---------|--------|
| `SYSTEM_OS` | `auto` | Fuerza el recolector (`auto`, `linux`, `macos`). Si es `auto`, se autodetecta de forma determinista mediante `platform.system()`. |
| `DEBUG` | `False` | Imprime advertencias en consola si alguna métrica específica no se puede leer. |

## Trampas conocidas
- **Aislamiento de fallos**: cada llamada interna está envuelta en `try...except`.
  Si un sensor no está disponible o el comando falla, devuelve `None` sin lanzar
  excepciones ni detener el programa.
- **Tipos escalares en `extra`**: la API V2 requiere estrictamente que los valores
  de `extra` sean escalares simples (string, número o booleano). Arrays o listas
  como `load_avg: [1.2, 0.8, 0.5]` son rechazados con error de validación `422`.
- **Timeouts en subprocesos**: todas las llamadas `subprocess.run` en macOS tienen
  un `timeout` de 2 o 3 segundos para evitar bloqueos si el sistema está bajo
  carga extrema.
- **Caché TTL**: la caché de 30 segundos evita ejecutar comandos repetidos como `top`
  o `ioreg` múltiples veces al subir lotes seguidos de varias rachas de teclado y ratón.
- **Verificación pendiente en Linux**: mientras que en macOS (`MacosSystemInfo`) la telemetría completa ha sido validada y verificada contra el hardware real (Apple Silicon M1 Pro), en GNU/Linux (`LinuxSystemInfo`) la implementación se basa en la especificación estándar del kernel (`/proc` y `/sys`), pero debe probarse en una máquina Linux real para verificar que las rutas térmicas y de energía devuelven los formatos y escalas correctos en dicho entorno.

## Tests que lo cubren
Ninguno ⚠️.

## Pendiente real
- **Comprobación en Linux real**: Ejecutar y revisar en un entorno GNU/Linux real el comportamiento de `LinuxSystemInfo`, verificando que la lectura de temperatura (`/sys/class/thermal/thermal_zone*` y `/sys/class/hwmon/`) y el voltaje/batería (`/sys/class/power_supply/`) detecten correctamente los sensores del hardware específico y no devuelvan `null` o escalas incorrectas (mV vs µV).

---
> Creado: 2026-09-07 · Última revisión: 2026-09-07
