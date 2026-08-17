# 15 — Entorno de ejecución y dependencias (estado actual)

Análisis de cómo se ejecuta hoy el proyecto y de qué depende. Documento de
**estado actual y problemas detectados**, no de propuestas.

---

## 1. Cómo se ejecuta hoy

- Contra el **Python del sistema** (se requiere **3.12** según el README).
- **Sin entorno virtual.**
- Con las dependencias instaladas de forma **global**, habitualmente con
  `sudo pip … --break-system-packages`.
- Como **root**, requisito de la librería `keyboard` en Linux y del socket en
  `/var/run`.

Es la configuración que lleva años funcionando y **debe mantenerse tal cual**
mientras no se decida lo contrario.

---

## 2. Inventario real de dependencias

Extraído leyendo los `import` de cada módulo.

### Dependencias externas

| Módulo importado | Paquete PyPI | Usado en | Obligatorio |
|------------------|--------------|----------|-------------|
| `keyboard` | `keyboard` | `Models/Keylogger.py` | ✅ Sí (núcleo) |
| `mouse` | `mouse` | `Models/Keylogger.py` (import condicional) | Solo si `MOUSE_ENABLED=True` |
| `sqlalchemy` | `SQLAlchemy` | `Models/DbConnection.py` | ✅ Sí |
| `dotenv` | `python-dotenv` | `main.py`, `DbConnection.py`, `ApiConnection.py` | ✅ Sí |
| `requests` | `requests` | `Models/ApiConnection.py` | ✅ Sí |
| `serial` | **`pyserial`** | `Models/LCDUart.py` | Solo si `SERIAL_DISPLAY_ENABLED=True` |

El código de `DbConnection` usa la **API 2.x de SQLAlchemy** (`select(table)`,
`con.commit()`, `insert().returning()`), lo que fija implícitamente la rama
mayor de esa dependencia.

### Librería estándar

`time`, `os`, `json`, `socket`, `subprocess`, `datetime`, `decimal`, `sys`,
`_thread`.

### Dependencias de la app macOS

La parte Swift **sí tiene las versiones fijadas**, mediante `Package.resolved`:

| Paquete | Versión |
|---------|---------|
| swift-nio | 2.74.0 |
| swift-nio-transport-services | 1.22.0 |
| swift-atomics | 1.2.0 |
| swift-collections | 1.1.4 |
| swift-system | 1.3.2 |

Contraste llamativo: el lado Swift tiene *lock file* y el lado Python no.

---

## 3. Errores detectados en las instrucciones de instalación

### 3.1. ⚠️ `serial` no es `pyserial` *(corregido en el README)*

El README indicaba instalar el paquete `serial`. El correcto es **`pyserial`**:
en PyPI, `serial` es una librería **distinta** que no da acceso al puerto serie.
El nombre del módulo sí es `serial` (`import serial`), de ahí la confusión.

```bash
pip uninstall serial
pip install pyserial
```

### 3.2. Dependencias omitidas en la línea de macOS *(corregido en el README)*

La orden documentada para macOS no incluía `python-dotenv` ni `requests`, ambas
obligatorias.

### 3.3. Alias interno y desaconsejado de `requests` *(pendiente, en código)*

`Models/ApiConnection.py` hace:

```python
from requests.packages.urllib3.util.retry import Retry
```

`requests.packages` es un **alias de compatibilidad heredado** y desaconsejado.
Lo correcto sería `from urllib3.util.retry import Retry`. Es otra vía por la que
una actualización de `requests` puede romper la aplicación.

---

## 4. Por qué se rompe al actualizar

No es una causa, son tres acumuladas:

1. **Instalación global contra el Python del sistema.** Al usar
   `--break-system-packages` se salta la protección de PEP 668. Cuando la
   distribución actualiza el intérprete (por ejemplo de 3.12 a 3.13), el
   `site-packages` cambia de ruta y **todo lo instalado deja de estar
   disponible**: la herramienta arranca contra un intérprete sin sus
   dependencias.

2. **Ausencia de versiones fijadas.** No hay `requirements.txt` ni lock, así que
   cada reinstalación trae la última versión de cada librería, que puede no ser
   compatible.

3. **Acoplamiento a internals privados de `keyboard`.** El código usa
   `keyboard._nixkeyboard`, `keyboard._listener` y `keyboard._KeyboardListener()`
   (ver [documento 03](03-keylogger.md)). Son API privadas: cualquier cambio de
   versión puede romperlas silenciosamente.

**Agravante:** la librería `keyboard` está **archivada desde el 13 de febrero de
2026** (última versión, la **0.13.5**), así que no habrá correcciones oficiales.

---

## 5. Riesgo de fondo

| Dependencia | Estado | Riesgo |
|-------------|--------|--------|
| `keyboard` 0.13.5 | Archivada (feb. 2026) | Alto — núcleo del proyecto, sin mantenimiento |
| `mouse` 0.7.1 | Incidencias abiertas, sin soporte oficial de macOS | Medio — funcionalidad opcional |
| `SQLAlchemy` | Mantenida | Bajo — API 2.x estable |
| `python-dotenv`, `requests`, `pyserial` | Mantenidas | Bajo |

La propuesta para abordarlo está en la planificación local
(`docs/planning/01-entorno-virtual-y-dependencias.md`), fuera de este
repositorio.

## Fuentes

- [pySerial en PyPI](https://pypi.org/project/pyserial/) y
  [documentación de pySerial](https://pyserial.readthedocs.io/en/latest/pyserial.html)
- [keyboard en PyPI](https://pypi.org/project/keyboard/) ·
  [boppreh/keyboard](https://github.com/boppreh/keyboard)
- [mouse en PyPI](https://pypi.org/project/mouse/) ·
  [boppreh/mouse](https://github.com/boppreh/mouse)
