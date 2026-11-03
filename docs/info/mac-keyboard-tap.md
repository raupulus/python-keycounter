# `mac-keyboard-tap`

> Ruta real en el repositorio: `Models/MacKeyboardTap.py`

## Qué hace y qué NO hace
Captura de teclado nativa en **macOS** mediante un `CGEventTap` **pasivo**
(`kCGEventTapOptionListenOnly`) en la sesión del usuario. Traduce los eventos
`keyDown`/`keyUp`/`flagsChanged` a objetos `KeyEvent(event_type, name,
scan_code)` compatibles con `Keylogger.callback_keyboard` y los entrega en un
hilo consumidor propio. Si recibe `mouse_callback`, escucha también los clics
(`leftMouseDown`, `rightMouseDown` y `otherMouseDown` con botón 2 = central) en
el mismo tap y llama a `mouse_callback('left'|'right'|'middle')`.

Sustituye en macOS a la librería `keyboard`, cuyo tap es un **filtro síncrono**
(`kCGEventTapOptionDefault`): WindowServer espera la respuesta de Python por
cada tecla, el tap se desactivaba por timeout sin reactivarse (el contador dejaba
de registrar) y al terminar el proceso WindowServer llegó a colgarse hasta que
el watchdog lo mató, cerrando la sesión del usuario.

**NO** cuenta pulsaciones ni calcula estadísticas (eso es de
[keylogger](keylogger.md) y [keyboard-logger](keyboard-logger.md)), **NO**
suprime ni modifica eventos y **NO** escucha movimiento, arrastre, scroll ni
botones laterales del ratón.

## Modelo de datos
- `KeyEvent(event_type: 'down'|'up', name: str, scan_code: int)`.
- `SPECIAL_KEY_NAMES` / `MODIFIER_KEY_NAMES` — keycode virtual de macOS → nombre
  compatible con `Keylogger.KEYS_MAP` (`enter`, `shift`, `ctrl`, `alt`, `f1`…).
  `command` y `fn` no están en `KEYS_MAP` y cuentan como teclas normales.
- Teclas normales: el carácter en minúscula; si no es imprimible (p. ej. con
  Ctrl) `key_<keycode>`.
- Ratón: en la cola se encola `('mouse', botón, None)`; teclado y ratón
  comparten cola e hilo consumidor, así que sus callbacks nunca corren en
  paralelo.
- Cola interna acotada a `QUEUE_MAX_SIZE = 10000`; si se llena se descartan
  eventos (`dropped_events`), nunca se bloquea el hilo del tap.

## Flujos principales
1. `start()` — lanza el hilo consumidor y el hilo del tap; espera hasta 5 s a que
   el tap exista. Devuelve `False` si no se pudo crear (falta de permiso).
2. Hilo del tap — crea el tap listen-only, lo añade a su `CFRunLoop` y lo ejecuta
   en intervalos de 1 s. En cada vuelta comprueba `CGEventTapIsEnabled` y lo
   reactiva si macOS lo desactivó (vigilante).
3. `_tap_callback` — mínimo: si recibe `kCGEventTapDisabledByTimeout`/`ByUserInput`
   reactiva el tap; si no, lee keycode, autorepetición y carácter y hace
   `put_nowait` en la cola. Nunca propaga excepciones.
4. Hilo consumidor — saca eventos de la cola, los traduce con
   `KeyEventTranslator` y llama al callback. Errores del callback se capturan.
5. `stop()` — idempotente y acotado (≤ 3 s): para el run loop, espera al hilo y
   desactiva el tap, lo quita del run loop e invalida su puerto Mach.

## Puntos de entrada
- `MacKeyboardTap(callback, has_debug=False, mouse_callback=None)`, `start()`,
  `stop()`, `is_enabled()`.
- `KeyEventTranslator.translate(event_type, keycode, chars, is_autorepeat)` —
  lógica pura, probada sin Quartz.
- **Permisos:** el proceso (o el terminal que lo lanza) necesita «Monitorización
  de entrada» en Ajustes del Sistema → Privacidad y seguridad. Sin él
  `CGEventTapCreate` devuelve `None` y se avisa por `stderr`. Si los clics no
  se registran, revisar también «Accesibilidad» ⚠️ sin verificar.

## Dependencias en ambos sentidos
- **Depende de:** `pyobjc` (`Quartz`), `queue`, `threading`.
- **Le depende:** [keylogger](keylogger.md) (sólo en macOS).

## Configuración
Sin variables de entorno. Constantes de clase: `QUEUE_MAX_SIZE` (10000),
`RUN_LOOP_INTERVAL_SECONDS` (1.0).

## Trampas conocidas
- **No cambiar a `kCGEventTapOptionDefault`** ni hacer trabajo en
  `_tap_callback`: reintroduce el bloqueo de WindowServer (ver
  [decisiones-tecnicas.md](decisiones-tecnicas.md), D7).
- El emparejado down/up usa el nombre del último `keyDown` de cada keycode, para
  que soltar Shift antes que la tecla no deje `is_down` bloqueado.
- Bloq Mayús emite un único `flagsChanged` por pulsación: se traduce a
  `down` + `up`.
- Modificadores izquierdo/derecho comparten nombre (`shift`, `ctrl`…).

## Tests que lo cubren
Ninguno automatizado ⚠️. `KeyEventTranslator` se verificó manualmente con
eventos simulados (pares down/up, Shift, autorepetición, Bloq Mayús, Ctrl), y el
reparto de clics al `MouseLogger` con eventos simulados en la cola.

## Pendiente real
- Verificar en uso real el cierre con Ctrl+C / `SIGTERM` sin afectar a
  WindowServer ⚠️ sin verificar.
- Verificar en uso real la captura de clics y su subida a la API ⚠️ sin verificar.

---
> Creado: 2026-11-03 · Última revisión: 2026-11-03
