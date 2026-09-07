# Archivos del proyecto y control de versiones

Inventario de qué hay en el repositorio, qué está bajo seguimiento de git y qué
no debería estarlo. Documento de **estado actual**.

---

## 1. Inventario de archivos

### Código y configuración (versionado)

| Archivo | Contenido |
|---------|-----------|
| `main.py` | Punto de entrada y bucle principal |
| `functions.py` | **Vacío** — reservado para utilidades |
| `configuration.py` | **Vacío** — reservado para configuración |
| `Models/*.py` | Los nueve modelos del proyecto |
| `Debug/client_socket.py` | Cliente de ejemplo del socket UNIX |
| `.env.example` | Plantilla de configuración (valores ficticios) |
| `.gitignore` | Reglas de exclusión |
| `LICENSE` | **GNU GPL v3** |
| `README.md` | Documentación de usuario |
| `AGENTS.md` | Reglas de contribución |
| `docs/info/*.md` | Documentación técnica |
| `docs/images/*` | Capturas del proyecto |

### App macOS (versionado)

| Ruta | Contenido |
|------|-----------|
| `macos/KeyCounterBar/` | Proyecto Xcode (fuentes Swift, assets, storyboard) |
| `macos/KeyCounterBar.app/` | **Binario compilado** distribuido a propósito |
| `…/xcshareddata/swiftpm/Package.resolved` | Versiones fijadas de las dependencias Swift |

El `.app` está versionado **de forma deliberada**: el README ofrece arrastrarlo
a Aplicaciones sin necesidad de compilar. No es un descuido.

### Local, no versionado

| Archivo / directorio | Motivo |
|----------------------|--------|
| `.env` | **Contiene el `API_TOKEN`** — nunca debe versionarse |
| `keycounter.db` | Base de datos local de caché |
| `keycounter.sqbpro` | Proyecto de DB Browser for SQLite |
| `__pycache__/`, `*.pyc` | Caché de bytecode |
| `.idea/` | Configuración de JetBrains, incluidos orígenes de datos |
| `docs/planning/` | Planificación local de trabajo |

---

## 2. Estado real del seguimiento de git

Comprobado sobre el índice de git:

| Elemento | ¿Bajo seguimiento? | Valoración |
|----------|:------------------:|------------|
| `.env` | ❌ No | ✅ Correcto — sin fuga del token |
| `.env.example` | ✅ Sí | ✅ Correcto |
| `.idea/` | ❌ No | ✅ Correcto |
| `__pycache__/`, `*.pyc` | ❌ No | ✅ Correcto |
| `keycounter.db`, `keycounter.sqbpro` | ❌ No | ✅ Correcto |
| **`xcuserdata/` (Xcode)** | **✅ Sí** | ❌ **No debería** |

### ⚠️ Único problema detectado: `xcuserdata` versionado

Están bajo seguimiento archivos de **preferencias personales de Xcode**:

```
macos/KeyCounterBar/KeyCounterBar.xcodeproj/
  ├── xcuserdata/fryntiz.xcuserdatad/xcschemes/xcschememanagement.plist
  └── project.xcworkspace/
      └── xcuserdata/fryntiz.xcuserdatad/
          ├── UserInterfaceState.xcuserstate      ← estado de la interfaz (binario)
          └── WorkspaceSettings.xcsettings
```

Son específicos del usuario y de la máquina: estado de ventanas, esquemas
seleccionados, preferencias del espacio de trabajo. No aportan nada al proyecto,
generan ruido en cada commit y llevan el nombre de usuario en la ruta.

**No representan un riesgo de seguridad**, solo de higiene.

Ya están excluidos en `.gitignore`, pero **`.gitignore` no desindexa lo ya
versionado**. Queda como acción pendiente, a ejecutar manualmente cuando se
prepare el commit:

```bash
git rm -r --cached "macos/KeyCounterBar/KeyCounterBar.xcodeproj/xcuserdata"
git rm -r --cached "macos/KeyCounterBar/KeyCounterBar.xcodeproj/project.xcworkspace/xcuserdata"
```

> ⚠️ `--cached` deja los archivos en disco y solo los saca del seguimiento. No
> se ha ejecutado: es una decisión que corresponde tomar al preparar el commit.

---

## 3. Reglas de `.gitignore`

Organizadas por bloques:

| Bloque | Cubre |
|--------|-------|
| Python | `__pycache__/`, `*.py[cod]`, empaquetado, coverage, mypy… |
| Entornos | `.env`, `.env.*` (con excepción de `.env.example`), `.venv`, `venv/` |
| Base de datos | `keycounter.db`, `keycounter.sqbpro` |
| Socket | `uds_socket`, `keycounter.socket` |
| IDE | `/.idea`, `.vscode/`, `*.iml` |
| Xcode / macOS | `xcuserdata/`, `*.xcuserstate`, `.DS_Store` |
| Documentación local | `docs/planning/` |

### Sobre `docs/planning/`

Excluido a propósito: contiene planificación de trabajo **local y personal**, no
documentación del proyecto. Lo que debe llegar al repositorio es el estado
actual y los problemas (`docs/info/`), no las propuestas en curso.

### Sobre `.env.example`

La regla `.env.*` excluiría también `.env.example`, así que lleva una excepción
explícita (`!.env.example`) para mantenerlo versionado.

---

## 4. Verificación recomendada antes del commit

```bash
# Qué se versionaría exactamente
git status --short

# Confirmar que .env NO aparece
git ls-files | grep -E '^\.env$'        # no debe devolver nada

# Confirmar que docs/planning queda fuera
git status --short docs/planning        # no debe devolver nada

# Ver qué archivos de Xcode siguen indexados
git ls-files | grep xcuserdata
```

---

## 5. Ramas

En el momento de redactar este documento se trabaja sobre la **rama principal**,
y solo con documentación. Según lo previsto:

- La documentación se consolida en la rama principal.
- **Las modificaciones de código irán en una rama `dev`**, no en la principal.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-07
