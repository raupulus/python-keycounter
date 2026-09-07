# Problemas, riesgos y deuda técnica

Catálogo de todo lo detectado durante el análisis del código: bugs reales,
riesgos latentes y deuda técnica. Es un documento de **diagnóstico**, no de
soluciones: describe qué pasa, dónde y por qué importa.

> Las propuestas de actuación están en la planificación local
> (`docs/planning/`), que no forma parte de este repositorio.
>
> **Nada de lo aquí listado se ha modificado.** El proyecto sigue funcionando
> tal cual.

Clasificación: 🔴 bug real o riesgo alto · 🟠 riesgo medio · 🟢 deuda menor

---

## A. Bugs reales detectados

### A.1. 🔴 `except ():` no captura ninguna excepción

**Dónde:** `main.py`, función `upload_data_to_api`.

```python
except ():
```

Una tupla vacía como cláusula de excepción **no captura nada**. Cualquier fallo
en la subida a la API se propaga sin el tratamiento previsto y el mensaje de
error de debug nunca se muestra. Debería ser `except Exception`.

### A.2. 🔴 `truncate_db()` usa SQL de MySQL sobre SQLite

**Dónde:** `Models/DbConnection.py`.

Ejecuta `SET FOREIGN_KEY_CHECKS = 0;`, sentencia específica de MySQL que
**SQLite no reconoce**. El método fallaría si se llegase a invocar (hoy no se
usa en el flujo normal).

### A.3. 🟠 `set_brigthness()` genera un comando mal formado

**Dónde:** `Models/LCDUart.py`.

```python
self.write(bytes("BL(" + str(value) + ";\r\n"))
```

Falta el paréntesis de cierre: genera `BL(128;` en vez de `BL(128);`. Además,
`bytes()` sin codificación lanzaría `TypeError`. El método no se usa hoy en el
flujo normal.

### A.4. 🟠 Importación desde un alias desaconsejado de `requests`

**Dónde:** `Models/ApiConnection.py`.

```python
from requests.packages.urllib3.util.retry import Retry
```

`requests.packages` es un alias de compatibilidad heredado. Lo correcto es
`from urllib3.util.retry import Retry`. Vía probable de rotura al actualizar.

### A.5. 🟢 Parámetro `method` sin efecto

**Dónde:** `Models/ApiConnection.py`.

`send()` recibe `method` pero **siempre hace `POST`**; `upload()` lo declara con
valor por defecto `'GET'`. Inconsistencia sin consecuencia funcional hoy.

---

## B. Riesgos latentes

### B.1. 🔴 Estado compartido entre hilos sin sincronización

**Dónde:** `Models/KeyboardLogger.py`, `Models/MouseLogger.py`, `main.py`.

El diccionario `spurts` y los contadores se escriben desde el hilo de captura y
se leen/modifican desde el hilo del bucle **sin ningún lock**. `insert_data_in_db`
itera sobre `spurts` mientras el callback de teclado puede estar insertando
entradas nuevas. Riesgo de condición de carrera y de `RuntimeError` por mutación
durante la iteración.

### B.2. 🔴 Acoplamiento a internals privados de `keyboard`

**Dónde:** `Models/Keylogger.py`, `reload_keycounter_on_new_device`.

Usa `keyboard._nixkeyboard`, `keyboard._listener` y
`keyboard._KeyboardListener()`. Son API privadas que pueden cambiar sin aviso.

**Agravante:** la librería está **archivada desde el 13 de febrero de 2026**
(última versión 0.13.5), así que no habrá correcciones oficiales.

### B.3. 🟠 `AttributeError` latente en macOS

**Dónde:** `Models/Keylogger.py`, `reload_keycounter_on_new_device`.

`keyboard._nixkeyboard` **no existe en macOS** (allí la librería usa su backend
Darwin). Si la comparación de dispositivos llegase a detectar un cambio, el hilo
lanzaría `AttributeError`. Hoy no se dispara porque en macOS la lectura de
dispositivos devuelve siempre la misma salida de error, pero es un fallo
esperando a ocurrir.

### B.4. 🟠 Estado definido a nivel de clase

**Dónde:** todos los modelos.

Atributos mutables como `spurts = {}` están declarados **en el cuerpo de la
clase**, no en `__init__`. Con una sola instancia funciona, pero dos instancias
compartirían el mismo diccionario. Lo mismo aplica a `engine`, `connection` y
`session` en `DbConnection`, creados en tiempo de importación.

### B.5. 🟠 `datetime.utcnow()` obsoleto

**Dónde:** todo el proyecto.

Obsoleto desde Python 3.12, con eliminación prevista. Es un **bloqueante para
subir de versión de Python**. Además genera datetimes *naive* (sin zona).

### B.6. 🟢 `datetime.now()` local mezclado con UTC

**Dónde:** `Models/ClientDisplayWebsocket.py`.

Usa hora local mientras el resto del proyecto usa UTC. Los timestamps enviados a
la pantalla en red no son coherentes con los almacenados.

---

## C. Limitaciones de plataforma

### C.1. 🟠 Clicks de ratón en macOS

La librería `mouse` declara soporte oficial solo para **Windows y Linux**, exige
permisos de Accesibilidad en macOS y tiene incidencias abiertas con `on_click()`.
El fallo está en la librería y los permisos, **no en la lógica de KeyCounter**.

> La captura de **teclado** en macOS, en cambio, lleva años funcionando de forma
> estable en este proyecto.

Detalle en [14. Matriz de compatibilidad](matriz-compatibilidad.md).

### C.2. 🟠 Detección de dispositivos solo válida en Linux

`read_devices_by_id()` usa `ls /dev/input/by-id/` y `/proc/bus/input/devices`,
rutas exclusivas de Linux. En macOS no funciona, y con ella tampoco la recarga
automática al conectar un teclado USB.

---

## D. Deuda técnica

### D.1. 🟢 Falta de tipado

Prácticamente ningún método tiene *type hints*. Ya es obligatorio para código
nuevo según [`AGENTS.md`](../../AGENTS.md).

### D.2. 🟢 `print` en lugar de `logging`

Impide integrar la salida con el sistema y obliga a repartir `if DEBUG:` por
todo el código.

### D.3. 🟢 Archivos vacíos

`functions.py` y `configuration.py` existen pero **están vacíos**. O se usan
para extraer utilidades y centralizar configuración, o se eliminan.

### D.4. 🟢 Código muerto y sin terminar

| Elemento | Dónde | Estado |
|----------|-------|--------|
| `COMBO_MAP` | `KeyboardLogger`, `MouseLogger` | Declarado, **nunca usado** |
| `parse_array_to_json()` | `ApiConnection` | Definido, sin uso |
| `get_all_data()`, `truncate_all_table_data()` | `DbConnection` | Vacíos (`pass`) |
| `update_streak()`, `update_session()` | `Display` | Vacíos (`pass`) |
| `show_image()` | `LCDUart` | Cuerpo comentado, incompleto |
| Bloque de *reboot* | `main.loop()` | Comentado, inactivo |
| `TODO` de reinicio del ratón | `Keylogger` | Pendiente |

### D.5. 🟢 Algoritmo de combo sin documentar

**Dónde:** `KeyboardLogger.set_combo`.

```python
(int((self.pulsations_current * 2.7) *
     ((self.pulsations_current + 1) * 3.4)) % 5) == 0
```

Fórmula sin explicación de su intención. La existencia de `COMBO_MAP` sin usar
sugiere que hubo un diseño alternativo por tramos. Además, el ratón no calcula
puntuación mientras el teclado sí.

### D.6. 🟢 Valores fijados en el código

| Valor | Dónde |
|-------|-------|
| `/hardware/v1/get/device/16/info` (id 16) | `ApiConnection` |
| Puerto `80` | `ClientDisplayWebsocket` |
| `/var/run/keycounter.socket` | `Socket` |
| `n_registers = 10`, `sleep(30)`, `sleep(10)` | `main.py` |
| `COMBO_RESET = 15` | `KeyboardLogger`, `MouseLogger` |

### D.7. 🟢 Nombres con erratas

| Actual | Debería ser | Dónde |
|--------|-------------|-------|
| `pulsations_hight` | `pulsations_high` | `MouseLogger` |
| `set_brigthness` | `set_brightness` | `LCDUart` |
| `pulsations_total_especial_keys` | `…_special_keys` | `KeyboardLogger` |
| `ClientDisplayWebsocket` | No usa WebSocket, sino TCP plano | `Models/` |

Cambiarlos afecta a la API y a la base de datos: valorar el coste antes.

### D.8. 🟢 Ausencia de tests

No hay ninguna prueba automatizada. La lógica de rachas y de combos es
determinista y sería fácil de cubrir.

### D.9. 🟢 Interpretación inconsistente de booleanos del `.env`

Casi todas las variables se comparan con `== "True"` (sensible a mayúsculas),
salvo `MOUSE_ENABLED`, que además acepta `"true"`. Ver
[12. Configuración](configuracion.md).

---

## Resumen

| Prioridad | Elementos |
|-----------|-----------|
| 🔴 Alta | A.1, A.2, B.1, B.2 |
| 🟠 Media | A.3, A.4, B.3, B.4, B.5, C.1, C.2 |
| 🟢 Baja | A.5, B.6, y todo el bloque D |

Ninguno de estos puntos impide que el proyecto funcione hoy: lleva años en
producción. Son riesgos de mantenimiento y de evolución, no fallos operativos.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-07
