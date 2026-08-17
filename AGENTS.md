# AGENTS.md — Python KeyCounter

Guía para agentes de IA y personas que trabajen en este repositorio. **Léela
antes de tocar nada.**

---

## 1. ⚠️ Fase actual: análisis y documentación

**No se modifica código.** El proyecto lleva años en producción funcionando
correctamente y debe seguir ejecutándose exactamente igual.

Reglas vigentes en esta fase:

| Regla | Detalle |
|-------|---------|
| ❌ **No modificar código** | Ni `.py`, ni Swift, ni comportamiento de ejecución |
| ❌ **No introducir entorno virtual** | Se sigue ejecutando contra el Python del sistema, como hasta ahora |
| ❌ **No trabajar en la rama principal** para cambios de código | Las modificaciones irán en una rama **`dev`** |
| ❌ **No desindexar ni reescribir el historial de git** | Se documenta lo que habría que hacer; lo ejecuta el autor |
| ✅ **Sí documentar** | Estado actual, problemas encontrados y propuestas |

Lo único que se modifica ahora son **documentación y configuración de
repositorio**: `docs/`, `README.md`, `AGENTS.md` y `.gitignore`.

**No improvises implementaciones.** Si algo parece obvio de arreglar, se anota
en la documentación de problemas; no se arregla.

### Secuencia prevista

1. Documentar por completo lo que hay hoy → `docs/info/`
2. Documentar problemas y potenciales problemas → `docs/info/13`
3. Planificar ampliaciones → `docs/planning/` (local, fuera de git)
4. Commit de la documentación en la rama principal
5. Crear rama **`dev`** y empezar las modificaciones allí

---

## 2. Qué es este proyecto

Contador de pulsaciones de teclado (y opcionalmente ratón) para GNU/Linux y
macOS. Registra **estadísticas agregadas por rachas** —cantidad, velocidad y una
puntuación—, las cachea en SQLite y opcionalmente las sube a una API. **No
guarda el contenido tecleado**: solo métricas.

- **Plataformas objetivo:** Debian, Fedora, SteamOS (Steam Machine de Valve),
  macOS y Raspberry OS.
- **En producción desde 2020.**
- **Licencia:** GNU GPL v3.
- **Requiere root** y **Python 3.12**.

Documentación técnica completa: [`docs/info`](docs/info/00-indice.md).

---

## 3. Reglas para cuando se retome el código

Aplicables a partir de la rama `dev`. Todo cambio **debe** cumplirlas.

### 3.1. Tipado estático (obligatorio)

- **Todo el código nuevo va tipado** con *type hints* (PEP 484 / PEP 604).
- Anota **parámetros y valores de retorno** de toda función y método (usa
  `-> None` cuando no devuelva nada).
- Anota atributos relevantes (PEP 526), preferentemente en `__init__`. Usa
  `X | None` para lo que pueda ser `None`.
- Sintaxis moderna: `list[str]`, `dict[str, Any]`, `str | None`.
- Debe pasar un *type checker* (`mypy` o `pyright`) sin errores nuevos.
- Al **editar** una función existente sin tipar, **añádele los tipos** en el
  mismo cambio.

### 3.2. Documentación (obligatorio)

- **Docstrings en todo módulo, clase, función y método**, según **PEP 257**.
- Una línea para lo trivial; multilínea para el resto, describiendo propósito,
  parámetros, retorno y excepciones.
- Mantener el estilo ya presente en el repositorio (**español**, con `:param:` /
  `:return:`) para no mezclar convenciones.
- Si un cambio afecta al comportamiento de un módulo, **actualiza su documento**
  en `docs/info/` **en el mismo commit**.

### 3.3. Estilo (PEP 8)

- Sigue **PEP 8**, la guía declarada en las cabeceras del proyecto.
- Formateo con `black`, imports con `isort`, *linting* con `ruff`/`flake8`.
- Líneas ≤ 79/88 caracteres. `snake_case` para funciones y variables,
  `PascalCase` para clases.

### 3.4. Cabecera de autoría

Los archivos nuevos mantienen el estilo de cabecera del proyecto (licencia GPL y
autoría):

- Autor / nick: **@raupulus**
- Email público: **public@raupulus.dev**
- Licencia: **GNU GPL v3**

### 3.5. Ejemplo de referencia

```python
def get_pulsation_average(self) -> float:
    """
    Devuelve la velocidad media de la racha actual en pulsaciones por minuto.

    :return: Pulsaciones por minuto redondeadas a 2 decimales; 0.0 si no
             hay duración o pulsaciones suficientes.
    """
    duration_seconds: int = (
        self.last_pulsation_at - self.pulsations_current_start_at
    ).seconds

    if duration_seconds > 0 and self.pulsations_current > 0:
        return round((self.pulsations_current / duration_seconds) * 60.0, 2)

    return 0.0
```

---

## 4. Estructura del repositorio

```
main.py                 # Punto de entrada: arranca captura, socket, API y bucle
functions.py            # (vacío) reservado para utilidades comunes
configuration.py        # (vacío) reservado para configuración
.env / .env.example     # Configuración por variables de entorno
LICENSE                 # GNU GPL v3
Models/
  Keylogger.py          # Orquestador de captura (teclado + ratón)
  KeyboardLogger.py     # Estadísticas y puntuación del teclado
  MouseLogger.py        # Estadísticas del ratón
  DbConnection.py       # Caché local SQLite (SQLAlchemy)
  ApiConnection.py      # Subida de estadísticas a la API
  Socket.py             # Servidor socket UNIX
  Display.py            # Puente de pantalla (formatea datos)
  LCDUart.py            # Driver de pantalla por UART/serie
  ClientDisplayWebsocket.py  # Cliente hacia pantalla en red (TCP, no WebSocket)
Debug/
  client_socket.py      # Ejemplo de cliente del socket UNIX
macos/                  # App Swift (KeyCounterBar) para la barra de menús
docs/
  images/               # Capturas
  info/                 # Documentación técnica (empezar por 00-indice.md)
  planning/             # Planificación local — EXCLUIDA de git
```

Consulta [`docs/info/00-indice.md`](docs/info/00-indice.md) antes de modificar
cualquier módulo.

---

## 5. Configuración y ejecución

- Configuración por **variables de entorno** (`.env`, plantilla en
  `.env.example`). Ver [`docs/info/12`](docs/info/12-configuracion.md).
- Se ejecuta **como root** (captura global de entrada, socket en `/var/run`,
  acceso a `/dev/input`).
- Se arranca vía **`cron @reboot`**. Ver
  [`docs/info/16`](docs/info/16-despliegue-como-servicio.md).

---

## 6. Convenciones y decisiones vigentes

- **Idioma:** código, comentarios y documentación en **español**.
- **Privacidad:** nunca registrar ni transmitir el contenido tecleado; solo
  métricas agregadas. Cualquier dato nuevo enviado a la API debe ser estadístico
  y no privado.
- **Secretos:** el `API_TOKEN` vive en `.env`, que **no se versiona**. Nunca
  incluir credenciales en código ni en documentación.
- **Zonas horarias:** la captura usa UTC. El código nuevo debe usar *datetime
  timezone-aware*, evitando `datetime.utcnow()` (obsoleto).
- **Concurrencia:** el código actual usa `_thread`; para código nuevo se prefiere
  `threading` (o `asyncio`), con parada limpia.
- **Logging:** se prefiere `logging` sobre `print` en código nuevo.
- **Dependencias:** al añadir una, **fíjala con versión** y refléjala en el
  README. Ojo: el paquete del puerto serie es **`pyserial`**, no `serial`.

---

## 7. Antes de dar un cambio por terminado

**En la fase actual:**

- [ ] No se ha modificado ningún archivo de código.
- [ ] La documentación refleja el estado real, verificado contra el código.
- [ ] La planificación está en `docs/planning/` y sigue excluida de git.
- [ ] No se ha ejecutado ningún comando de git que altere el índice.

**Cuando se retome el código (rama `dev`):**

- [ ] Código nuevo/editado **tipado** y con **docstrings** (PEP 257).
- [ ] Cumple **PEP 8**; linting y *type checker* sin errores nuevos.
- [ ] Documentación de `docs/info/` actualizada en el mismo commit.
- [ ] Sin secretos en el código ni en el repositorio.
- [ ] Respeta la privacidad (no se captura contenido tecleado).
- [ ] Compatibilidad con las cinco plataformas considerada, o la limitación
      documentada.
- [ ] Verificado que **sigue funcionando lo que ya funcionaba**.
