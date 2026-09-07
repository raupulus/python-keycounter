# `<nombre-del-módulo>`

> Ruta real en el repositorio: `<ruta/al/fichero.py>`

## Qué hace y qué NO hace
Descripción breve de la responsabilidad del módulo. Enumera explícitamente lo
que queda fuera de su alcance para evitar suposiciones.

## Modelo de datos
Estructuras, tablas, atributos de clase o formatos de mensaje que maneja. Si no
aplica, indícalo con «No aplica».

## Flujos principales
Pasos de los procesos relevantes (inicialización, bucle, callbacks, envío…).

## Puntos de entrada
Métodos o funciones públicas que consume el resto del sistema. Indica, cuando
proceda, autenticación, permisos y límites (rate limit, tamaño, timeout).

## Dependencias en ambos sentidos
- **Depende de:** módulos/librerías que necesita.
- **Le depende:** módulos que lo usan.

## Configuración
Variables de entorno u opciones que afectan al módulo, con valor por defecto y
efecto de cada una.

| Variable | Defecto | Efecto |
|----------|---------|--------|
| `EJEMPLO` | `valor` | Qué cambia |

## Trampas conocidas
Comportamientos no evidentes, condiciones de carrera, dependencias del sistema
operativo, etc.

## Tests que lo cubren
Rutas de los tests que verifican este módulo. Si no hay, escribe «Ninguno ⚠️».

## Pendiente real
`TODO` verificados en el código o carencias reales. No listes deseos vagos.

---
> Creado: 2026-09-06 · Última revisión: 2026-09-06
