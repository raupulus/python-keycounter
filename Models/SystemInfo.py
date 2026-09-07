#!/usr/bin/python3
# -*- encoding: utf-8 -*-

# @author     Raúl Caro Pastorino
# @email      public@raupulus.dev
# @web        https://raupulus.dev
# @gitlab     https://gitlab.com/raupulus
# @github     https://github.com/raupulus
# @twitter    https://twitter.com/raupulus
# @telegram   https://t.me/raupulus_diffusion

# Create Date: 2026
# Project Name: Python Keycounter
# Description: Módulo para la recolección de estadísticas básicas de hardware
#              (RAM, CPU, disco, temperatura, uptime, batería, voltaje) sin dependencias
#              externas para Linux y macOS.

# Guía de estilos aplicada: PEP8

#######################################
# #       Importar Librerías        # #
#######################################
import os
import platform
import subprocess
import shutil
import socket
import time
import re
import glob


#######################################
# #        Clases Base / SO         # #
#######################################

class BaseSystemInfo:
    """
    Clase base para la telemetría de hardware.
    Garantiza que ningún fallo interrumpa la ejecución ni lance excepciones.
    """
    def __init__(self, debug=False):
        self.debug = debug
        self._cached_info = None
        self._last_cache_time = 0
        self.CACHE_TTL = 30  # Caché de 30 segundos para evitar saturación

    def get_cpu_usage(self):
        return None

    def get_ram_usage(self):
        return None

    def get_disk_usage(self, path='/'):
        """
        Calcula el porcentaje de uso de disco usando la biblioteca estándar shutil.
        Funciona idénticamente en Linux y macOS.
        """
        try:
            total, used, free = shutil.disk_usage(path)
            if total > 0:
                return round((used / total) * 100.0, 2)
        except Exception as e:
            if self.debug:
                print('Error al calcular uso de disco:', e)
        return None

    def get_temperature(self):
        return None

    def get_uptime(self):
        return None

    def get_battery_level(self):
        return None

    def get_voltage(self):
        return None

    def get_ip_local(self):
        """
        Determina la IP local del equipo abriendo un socket UDP de enrutamiento
        sin enviar tráfico real.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1.0)
            try:
                s.connect(('8.8.8.8', 80))
                return str(s.getsockname()[0])
            finally:
                s.close()
        except Exception as e:
            if self.debug:
                print('Error al determinar IP local:', e)
        return None

    def get_extra(self):
        return None

    def get_hardware_device_info(self, use_cache=True):
        """
        Compila el diccionario hardware_device_info según el contrato de la API V2.
        Usa caché TTL para evitar re-ejecución innecesaria en subidas por lotes.
        Si ocurre cualquier error, devuelve None sin propagar excepciones.
        """
        now = time.time()
        if use_cache and self._cached_info is not None and (now - self._last_cache_time < self.CACHE_TTL):
            return self._cached_info

        try:
            info = {
                'cpu': self.get_cpu_usage(),
                'ram': self.get_ram_usage(),
                'disk': self.get_disk_usage(),
                'temp': self.get_temperature(),
                'uptime': self.get_uptime(),
                'battery_level': self.get_battery_level(),
                'voltage': self.get_voltage(),
                'ip_local': self.get_ip_local(),
                'extra': self.get_extra(),
            }
            self._cached_info = info
            self._last_cache_time = now
            return info
        except Exception as e:
            if self.debug:
                print('Error inesperado en get_hardware_device_info:', e)
            return None


class LinuxSystemInfo(BaseSystemInfo):
    """
    Implementación nativa para GNU/Linux leyendo directamente los sistemas de
    archivos virtuales /proc y /sys sin procesos externos.
    """
    def __init__(self, debug=False):
        super().__init__(debug=debug)
        self._last_cpu_times = None

    def _read_cpu_times(self):
        try:
            with open('/proc/stat', 'r') as f:
                for line in f:
                    if line.startswith('cpu '):
                        fields = [float(x) for x in line.split()[1:]]
                        idle = fields[3] + (fields[4] if len(fields) > 4 else 0.0)
                        total = sum(fields)
                        return idle, total
        except Exception as e:
            if self.debug:
                print('Error al leer /proc/stat en Linux:', e)
        return None, None

    def get_cpu_usage(self):
        try:
            idle2, total2 = self._read_cpu_times()
            if idle2 is None or total2 is None:
                return None

            if self._last_cpu_times is None:
                self._last_cpu_times = (idle2, total2)
                time.sleep(0.05)
                idle2, total2 = self._read_cpu_times()
                if idle2 is None or total2 is None:
                    return None

            idle1, total1 = self._last_cpu_times
            self._last_cpu_times = (idle2, total2)

            total_delta = total2 - total1
            idle_delta = idle2 - idle1
            if total_delta > 0:
                cpu_pct = 100.0 * (1.0 - (idle_delta / total_delta))
                return round(max(0.0, min(100.0, cpu_pct)), 2)
        except Exception as e:
            if self.debug:
                print('Error al calcular CPU en Linux:', e)
        return None

    def get_ram_usage(self):
        try:
            meminfo = {}
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    parts = line.split(':')
                    if len(parts) == 2:
                        meminfo[parts[0].strip()] = int(parts[1].strip().split()[0])

            total = meminfo.get('MemTotal', 0)
            available = meminfo.get('MemAvailable')
            if available is None:
                free = meminfo.get('MemFree', 0)
                buffers = meminfo.get('Buffers', 0)
                cached = meminfo.get('Cached', 0)
                available = free + buffers + cached

            if total > 0 and available is not None:
                used = total - available
                return round((used / total) * 100.0, 2)
        except Exception as e:
            if self.debug:
                print('Error al leer RAM en Linux:', e)
        return None

    def get_uptime(self):
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_sec = float(f.readline().split()[0])
                return int(uptime_sec)
        except Exception as e:
            if self.debug:
                print('Error al leer uptime en Linux:', e)
        return None

    def get_battery_level(self):
        try:
            bat_paths = glob.glob('/sys/class/power_supply/*/capacity')
            if bat_paths:
                with open(bat_paths[0], 'r') as f:
                    return int(f.read().strip())
        except Exception as e:
            if self.debug:
                print('Error al leer batería en Linux:', e)
        return None

    def get_voltage(self):
        try:
            v_paths = glob.glob('/sys/class/power_supply/*/voltage_now')
            if not v_paths:
                v_paths = glob.glob('/sys/class/power_supply/*/voltage_avg')
            if v_paths:
                with open(v_paths[0], 'r') as f:
                    val = float(f.read().strip())
                    if val > 1000000:
                        val /= 1000000.0
                    elif val > 1000:
                        val /= 1000.0
                    return round(val, 2)
        except Exception as e:
            if self.debug:
                print('Error al leer voltaje en Linux:', e)
        return None

    def get_temperature(self):
        try:
            # Buscar en zonas térmicas de CPU
            cpu_temps = []
            all_temps = []
            for tz_type_path in glob.glob('/sys/class/thermal/thermal_zone*/type'):
                try:
                    with open(tz_type_path, 'r') as f:
                        tz_type = f.read().strip().lower()
                    tz_temp_path = tz_type_path.replace('/type', '/temp')
                    if os.path.exists(tz_temp_path):
                        with open(tz_temp_path, 'r') as f:
                            val = float(f.read().strip())
                            if val > 1000:
                                val /= 1000.0
                            if 10.0 <= val <= 130.0:
                                all_temps.append(val)
                                if any(k in tz_type for k in ('cpu', 'pkg', 'core', 'soc', 'k10temp')):
                                    cpu_temps.append(val)
                except Exception:
                    pass

            if cpu_temps:
                return round(sum(cpu_temps) / len(cpu_temps), 1)

            # Buscar en hwmon (coretemp, k10temp, etc.)
            hw_temps = []
            for path in glob.glob('/sys/class/hwmon/hwmon*/temp*_input'):
                try:
                    with open(path, 'r') as f:
                        val = float(f.read().strip())
                        if val > 1000:
                            val /= 1000.0
                        if 10.0 <= val <= 130.0:
                            hw_temps.append(val)
                except Exception:
                    pass

            if hw_temps:
                return round(sum(hw_temps) / len(hw_temps), 1)
            if all_temps:
                return round(sum(all_temps) / len(all_temps), 1)
        except Exception as e:
            if self.debug:
                print('Error al leer temperatura en Linux:', e)
        return None

    def get_extra(self):
        try:
            distro = 'Linux'
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('PRETTY_NAME='):
                            distro = line.split('=', 1)[1].strip('"\n')
                            break

            loads = os.getloadavg() if hasattr(os, 'getloadavg') else None
            extra = {
                'os': distro,
                'kernel': platform.release(),
                'hostname': socket.gethostname(),
                'architecture': platform.machine(),
            }
            if loads and len(loads) >= 3:
                extra['load_avg_1m'] = round(loads[0], 2)
                extra['load_avg_5m'] = round(loads[1], 2)
                extra['load_avg_15m'] = round(loads[2], 2)
            return extra
        except Exception as e:
            if self.debug:
                print('Error al obtener extra en Linux:', e)
        return None


class MacosSystemInfo(BaseSystemInfo):
    """
    Implementación nativa para macOS usando sysctl, vm_stat, ioreg, IOKit y herramientas del sistema.
    """
    def get_uptime(self):
        try:
            res = subprocess.run(['sysctl', '-n', 'kern.boottime'], capture_output=True, text=True, timeout=2)
            m = re.search(r'sec\s*=\s*(\d+)', res.stdout)
            if m:
                boot_sec = int(m.group(1))
                return max(0, int(time.time() - boot_sec))
        except Exception as e:
            if self.debug:
                print('Error al leer uptime en macOS:', e)
        return None

    def get_ram_usage(self):
        try:
            res_mem = subprocess.run(['sysctl', '-n', 'hw.memsize'], capture_output=True, text=True, timeout=2)
            total_bytes = int(res_mem.stdout.strip())

            res_vm = subprocess.run(['vm_stat'], capture_output=True, text=True, timeout=2)
            out = res_vm.stdout

            page_size = 4096
            m_ps = re.search(r'page size of (\d+) bytes', out)
            if m_ps:
                page_size = int(m_ps.group(1))

            m_active = re.search(r'Pages active:\s+(\d+)', out)
            m_wired = re.search(r'Pages wired down:\s+(\d+)', out)
            m_spec = re.search(r'Pages speculative:\s+(\d+)', out)

            active = int(m_active.group(1)) if m_active else 0
            wired = int(m_wired.group(1)) if m_wired else 0
            spec = int(m_spec.group(1)) if m_spec else 0

            used_bytes = (active + wired + spec) * page_size
            if total_bytes > 0:
                return round((used_bytes / total_bytes) * 100.0, 2)
        except Exception as e:
            if self.debug:
                print('Error al leer RAM en macOS:', e)
        return None

    def get_cpu_usage(self):
        try:
            res = subprocess.run(['top', '-l', '1', '-n', '0'], capture_output=True, text=True, timeout=3)
            m = re.search(r'(\d+\.?\d*)%\s+idle', res.stdout)
            if m:
                idle = float(m.group(1))
                return round(max(0.0, min(100.0, 100.0 - idle)), 2)
        except Exception as e:
            if self.debug:
                print('Error al leer CPU en macOS:', e)
        return None

    def get_battery_level(self):
        try:
            res = subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True, timeout=2)
            m = re.search(r'(\d+)%', res.stdout)
            if m:
                return int(m.group(1))
        except Exception as e:
            if self.debug:
                print('Error al leer batería en macOS:', e)
        return None

    def get_voltage(self):
        try:
            import plistlib
            res = subprocess.run(
                ['ioreg', '-r', '-n', 'AppleSmartBattery', '-a'],
                capture_output=True, timeout=2
            )
            if res.returncode == 0 and res.stdout:
                pl = plistlib.loads(res.stdout)
                if pl and isinstance(pl, list) and len(pl) > 0:
                    batt = pl[0]
                    voltage_mv = batt.get('Voltage')
                    if voltage_mv and isinstance(voltage_mv, (int, float)):
                        return round(float(voltage_mv) / 1000.0, 2)
        except Exception as e:
            if self.debug:
                print('Error al leer voltaje en macOS:', e)
        return None

    def _read_iohid_temperature(self):
        """
        Lee los sensores térmicos de CPU (PMU tdie / CPU cores) en macOS mediante
        IOHIDEventSystem usando ctypes sobre IOKit y CoreFoundation.
        Funciona en Apple Silicon (M1/M2/M3/M4) e Intel moderno sin herramientas externas.
        """
        try:
            import ctypes
            iokit = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/IOKit.framework/IOKit')
            cf = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')

            cf.CFArrayGetCount.restype = ctypes.c_long
            cf.CFArrayGetCount.argtypes = [ctypes.c_void_p]
            cf.CFArrayGetValueAtIndex.restype = ctypes.c_void_p
            cf.CFArrayGetValueAtIndex.argtypes = [ctypes.c_void_p, ctypes.c_long]
            cf.CFStringGetCString.restype = ctypes.c_bool
            cf.CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32]

            iokit.IOHIDEventSystemClientCreateWithType.restype = ctypes.c_void_p
            iokit.IOHIDEventSystemClientCreateWithType.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32]
            iokit.IOHIDEventSystemClientCopyServices.restype = ctypes.c_void_p
            iokit.IOHIDEventSystemClientCopyServices.argtypes = [ctypes.c_void_p]
            iokit.IOHIDServiceClientCopyProperty.restype = ctypes.c_void_p
            iokit.IOHIDServiceClientCopyProperty.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            iokit.IOHIDServiceClientCopyEvent.restype = ctypes.c_void_p
            iokit.IOHIDServiceClientCopyEvent.argtypes = [ctypes.c_void_p, ctypes.c_int64, ctypes.c_int32, ctypes.c_int64]
            iokit.IOHIDEventGetFloatValue.restype = ctypes.c_double
            iokit.IOHIDEventGetFloatValue.argtypes = [ctypes.c_void_p, ctypes.c_uint32]

            cf.CFStringCreateWithCString.restype = ctypes.c_void_p
            cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
            kCFStringEncodingUTF8 = 0x08000100
            prod_key = cf.CFStringCreateWithCString(None, b'Product', kCFStringEncodingUTF8)

            client = iokit.IOHIDEventSystemClientCreateWithType(None, 1, 0)
            if not client:
                return None

            services = iokit.IOHIDEventSystemClientCopyServices(client)
            if not services:
                return None

            count = cf.CFArrayGetCount(services)
            field = 15 << 16  # kIOHIDEventTypeTemperature

            tdie_temps = []
            all_temps = []

            for i in range(count):
                svc = cf.CFArrayGetValueAtIndex(services, i)
                event = iokit.IOHIDServiceClientCopyEvent(svc, 15, 0, 0)
                if event:
                    val = iokit.IOHIDEventGetFloatValue(event, field)
                    if 15.0 <= val <= 115.0:
                        all_temps.append(val)
                        prop = iokit.IOHIDServiceClientCopyProperty(svc, prod_key)
                        if prop:
                            buf = ctypes.create_string_buffer(128)
                            if cf.CFStringGetCString(prop, buf, 128, kCFStringEncodingUTF8):
                                name = buf.value.decode('utf-8', errors='ignore')
                                if 'tdie' in name.lower() or 'cpu' in name.lower():
                                    tdie_temps.append(val)

            if tdie_temps:
                return round(sum(tdie_temps) / len(tdie_temps), 1)
            elif all_temps:
                return round(sum(all_temps) / len(all_temps), 1)
            return None
        except Exception as e:
            if self.debug:
                print('Error al leer temperatura con IOHID:', e)
            return None

    def get_temperature(self):
        try:
            # 1. IOHIDEventSystem nativo (Apple Silicon e Intel moderno)
            temp = self._read_iohid_temperature()
            if temp is not None:
                return temp

            # 2. Binarios conocidos si estuvieran instalados
            for cmd in ['osx-cpu-temp', 'smctemp', 'istats']:
                if shutil.which(cmd):
                    res = subprocess.run([cmd], capture_output=True, text=True, timeout=2)
                    m = re.search(r'(\d+\.?\d*)', res.stdout)
                    if m:
                        val = float(m.group(1))
                        if 15.0 <= val <= 115.0:
                            return round(val, 1)
        except Exception as e:
            if self.debug:
                print('Error al leer temperatura en macOS:', e)
        return None

    def get_extra(self):
        try:
            loads = os.getloadavg() if hasattr(os, 'getloadavg') else None
            extra = {
                'os': 'macOS',
                'os_version': platform.mac_ver()[0] or platform.platform(),
                'hostname': socket.gethostname(),
                'architecture': platform.machine(),
            }
            if loads and len(loads) >= 3:
                extra['load_avg_1m'] = round(loads[0], 2)
                extra['load_avg_5m'] = round(loads[1], 2)
                extra['load_avg_15m'] = round(loads[2], 2)
            return extra
        except Exception as e:
            if self.debug:
                print('Error al obtener extra en macOS:', e)
        return None


#######################################
# #              Fábrica            # #
#######################################

class SystemInfo:
    """
    Fábrica y punto de acceso unificado a la información del sistema.
    """
    @staticmethod
    def create(os_type=None, debug=False):
        """
        Crea la instancia correspondiente según SYSTEM_OS o autodetección por platform.system().
        :param os_type: 'auto', 'linux', 'macos'/'darwin'. Si es None, lee de SYSTEM_OS.
        :param debug: Activa trazas de depuración si es True.
        :return: Instancia de BaseSystemInfo (LinuxSystemInfo o MacosSystemInfo).
        """
        target = os_type or os.getenv('SYSTEM_OS', 'auto')
        target = str(target).strip().lower()

        if target in ('macos', 'darwin', 'mac', 'osx'):
            return MacosSystemInfo(debug=debug)
        elif target in ('linux', 'gnu/linux'):
            return LinuxSystemInfo(debug=debug)
        else:  # 'auto' o no configurado -> autodetección nativa
            system_name = platform.system().lower()
            if system_name == 'darwin':
                return MacosSystemInfo(debug=debug)
            else:
                return LinuxSystemInfo(debug=debug)
