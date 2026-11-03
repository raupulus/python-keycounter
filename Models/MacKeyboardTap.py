#!/usr/bin/python3
# -*- encoding: utf-8 -*-

# @author     Raúl Caro Pastorino
# @email      public@raupulus.dev
# @web        https://raupulus.dev

# Project Name: Python Keycounter
# Description: Captura de teclado (y opcionalmente clics de ratón) nativa
#              para macOS mediante un CGEventTap PASIVO (listen-only). Sustituye en macOS a la librería
#              `keyboard`, cuyo tap es un filtro síncrono que puede bloquear
#              WindowServer y cerrar la sesión del usuario.
#
# Reglas de diseño (no romperlas):
#   1. El tap se crea con kCGEventTapOptionListenOnly: WindowServer NUNCA
#      espera a este proceso para entregar eventos al resto del sistema.
#   2. El callback del tap sólo copia los datos mínimos a una cola y retorna.
#      Toda la lógica (contadores, socket, pantalla…) corre en otro hilo.
#      Teclado y ratón comparten cola y hilo consumidor: sus callbacks nunca
#      se ejecutan en paralelo.
#   3. Si macOS desactiva el tap (timeout, entrada segura, reposo) se reactiva
#      automáticamente.
#   4. Al parar, el tap se desactiva, se quita del run loop y se invalida su
#      puerto ANTES de que el proceso termine.

import queue
import sys
import threading
from collections import namedtuple

import Quartz

# Evento compatible con lo que espera Keylogger.callback_keyboard
# (mismos atributos que usa de los eventos de la librería `keyboard`).
KeyEvent = namedtuple('KeyEvent', ['event_type', 'name', 'scan_code'])

# Teclas especiales por keycode virtual de macOS. Los nombres coinciden con los
# de la librería `keyboard` para que Keylogger.KEYS_MAP las reconozca.
SPECIAL_KEY_NAMES = {
    36: 'enter', 76: 'enter', 48: 'tab', 49: 'space', 51: 'backspace',
    53: 'esc', 117: 'delete', 114: 'insert', 115: 'home', 119: 'end',
    116: 'page up', 121: 'page down', 123: 'left', 124: 'right',
    125: 'down', 126: 'up', 71: 'num lock',
    122: 'f1', 120: 'f2', 99: 'f3', 118: 'f4', 96: 'f5', 97: 'f6',
    98: 'f7', 100: 'f8', 101: 'f9', 109: 'f10', 103: 'f11', 111: 'f12',
    105: 'f13', 107: 'f14',
}

# Modificadores: llegan como kCGEventFlagsChanged, no como keyDown/keyUp.
MODIFIER_KEY_NAMES = {
    56: 'shift', 60: 'shift',
    59: 'ctrl', 62: 'ctrl',
    58: 'alt', 61: 'alt',
    55: 'command', 54: 'command',
    63: 'fn',
}

CAPS_LOCK_KEYCODE = 57

EVENT_KEY_DOWN = Quartz.kCGEventKeyDown
EVENT_KEY_UP = Quartz.kCGEventKeyUp
EVENT_FLAGS_CHANGED = Quartz.kCGEventFlagsChanged
EVENT_TAP_DISABLED = (Quartz.kCGEventTapDisabledByTimeout,
                      Quartz.kCGEventTapDisabledByUserInput)

# Clics de ratón: sólo pulsación (down). No se escucha movimiento ni scroll.
EVENT_LEFT_MOUSE_DOWN = Quartz.kCGEventLeftMouseDown
EVENT_RIGHT_MOUSE_DOWN = Quartz.kCGEventRightMouseDown
EVENT_OTHER_MOUSE_DOWN = Quartz.kCGEventOtherMouseDown

# Número de botón en kCGEventOtherMouseDown que corresponde al central.
MIDDLE_MOUSE_BUTTON_NUMBER = 2

# Marca en la cola para distinguir eventos de ratón de los de teclado.
QUEUE_MOUSE = 'mouse'


class KeyEventTranslator:
    """
    Traduce los datos crudos del tap (tipo, keycode, carácter) a KeyEvent.
    No depende de Quartz en tiempo de ejecución para poder probarse aislado.
    """

    def __init__(self):
        # Modificadores actualmente pulsados (por keycode, distingue izq/der).
        self.pressed_modifiers = set()

        # Nombre asignado a cada keycode en su último keyDown. Se reutiliza en
        # el keyUp para que el par down/up tenga siempre el mismo nombre aunque
        # cambien los modificadores entre medias (p. ej. soltar shift antes).
        self.name_by_keycode = {}

    def translate(self, event_type, keycode, chars, is_autorepeat=False):
        """
        Devuelve una lista de KeyEvent (vacía si el evento se descarta).
        """
        if event_type == EVENT_FLAGS_CHANGED:
            if keycode == CAPS_LOCK_KEYCODE:
                # Bloq Mayús emite un único flagsChanged por pulsación física.
                return [KeyEvent('down', 'caps lock', keycode),
                        KeyEvent('up', 'caps lock', keycode)]

            name = MODIFIER_KEY_NAMES.get(keycode)

            if name is None:
                return []

            if keycode in self.pressed_modifiers:
                self.pressed_modifiers.discard(keycode)
                return [KeyEvent('up', name, keycode)]

            self.pressed_modifiers.add(keycode)
            return [KeyEvent('down', name, keycode)]

        if event_type == EVENT_KEY_DOWN:
            if is_autorepeat:
                return []

            name = SPECIAL_KEY_NAMES.get(keycode)

            if name is None:
                name = self._name_from_chars(keycode, chars)

            self.name_by_keycode[keycode] = name
            return [KeyEvent('down', name, keycode)]

        if event_type == EVENT_KEY_UP:
            name = self.name_by_keycode.pop(keycode, None)

            if name is None:
                name = SPECIAL_KEY_NAMES.get(keycode) or \
                    self._name_from_chars(keycode, chars)

            return [KeyEvent('up', name, keycode)]

        return []

    @staticmethod
    def _name_from_chars(keycode, chars):
        """
        Nombre para teclas normales: el carácter en minúscula si es imprimible,
        si no un identificador estable basado en el keycode.
        """
        if chars and len(chars) == 1 and chars.isprintable() and \
                not chars.isspace():
            return chars.lower()

        return 'key_{}'.format(keycode)


class MacKeyboardTap:
    """
    Escucha pasiva de teclado (y opcionalmente clics de ratón) en macOS.

    Uso:
        tap = MacKeyboardTap(callback, mouse_callback=None)
        tap.start()
        ...
        tap.stop()

    `callback(event)` recibe un KeyEvent. `mouse_callback(button)` recibe
    'left', 'right' o 'middle'; si es None no se escuchan eventos de ratón.
    Ambos se ejecutan en el hilo consumidor, nunca en el hilo del tap.
    """

    # Máximo de eventos pendientes; si el consumidor se atasca se descartan
    # eventos en lugar de crecer sin límite. Nunca se bloquea el hilo del tap.
    QUEUE_MAX_SIZE = 10000

    # Cada cuántos segundos el run loop despierta para comprobar el estado.
    RUN_LOOP_INTERVAL_SECONDS = 1.0

    def __init__(self, callback, has_debug=False, mouse_callback=None):
        self.callback = callback
        self.mouse_callback = mouse_callback
        self.has_debug = has_debug

        self._queue = queue.Queue(maxsize=self.QUEUE_MAX_SIZE)
        self._translator = KeyEventTranslator()

        self._running = False
        self._stopped = threading.Event()
        self._ready = threading.Event()

        self._tap = None
        self._source = None
        self._run_loop = None

        self._tap_thread = None
        self._consumer_thread = None

        self.dropped_events = 0
        self.reenabled_count = 0

    #######################################
    # #         Ciclo de vida           # #
    #######################################

    def start(self, timeout=5.0):
        """
        Arranca el hilo del tap y el consumidor. Devuelve True si el tap se
        creó correctamente.
        """
        if self._running:
            return self._tap is not None

        self._running = True

        self._consumer_thread = threading.Thread(
            target=self._consume_loop, name='mac-keyboard-consumer',
            daemon=True)
        self._consumer_thread.start()

        self._tap_thread = threading.Thread(
            target=self._tap_loop, name='mac-keyboard-tap', daemon=True)
        self._tap_thread.start()

        self._ready.wait(timeout)

        return self._tap is not None

    def stop(self, timeout=3.0):
        """
        Para la captura: desactiva e invalida el tap y detiene los hilos.
        Es idempotente y nunca bloquea más de `timeout` segundos.
        """
        if not self._running:
            return

        self._running = False

        run_loop = self._run_loop

        if run_loop is not None:
            try:
                Quartz.CFRunLoopStop(run_loop)
            except Exception:
                pass

        if self._tap_thread is not None and \
                self._tap_thread is not threading.current_thread():
            self._tap_thread.join(timeout)

        # Si el hilo del tap no llegó a limpiar (p. ej. timeout), se fuerza
        # aquí. Desactivar/invalidar desde otro hilo es seguro en CoreFoundation.
        self._teardown_tap()

        self._stopped.set()

    def is_enabled(self):
        """
        Indica si el tap existe y está activo ahora mismo.
        """
        tap = self._tap

        if tap is None:
            return False

        try:
            return bool(Quartz.CGEventTapIsEnabled(tap))
        except Exception:
            return False

    #######################################
    # #           Hilo del tap          # #
    #######################################

    def _tap_loop(self):
        try:
            mask = (Quartz.CGEventMaskBit(EVENT_KEY_DOWN) |
                    Quartz.CGEventMaskBit(EVENT_KEY_UP) |
                    Quartz.CGEventMaskBit(EVENT_FLAGS_CHANGED))

            if self.mouse_callback is not None:
                mask |= (Quartz.CGEventMaskBit(EVENT_LEFT_MOUSE_DOWN) |
                         Quartz.CGEventMaskBit(EVENT_RIGHT_MOUSE_DOWN) |
                         Quartz.CGEventMaskBit(EVENT_OTHER_MOUSE_DOWN))

            tap = Quartz.CGEventTapCreate(
                Quartz.kCGSessionEventTap,
                Quartz.kCGTailAppendEventTap,
                Quartz.kCGEventTapOptionListenOnly,
                mask,
                self._tap_callback,
                None
            )

            if tap is None:
                print('[MacKeyboardTap] ERROR: could not create the event '
                      'tap. Grant "Input Monitoring" permission to the '
                      'terminal/Python in System Settings > Privacy & '
                      'Security.', file=sys.stderr)
                return

            self._tap = tap
            self._source = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
            self._run_loop = Quartz.CFRunLoopGetCurrent()

            Quartz.CFRunLoopAddSource(self._run_loop, self._source,
                                      Quartz.kCFRunLoopCommonModes)
            Quartz.CGEventTapEnable(tap, True)

            if self.has_debug:
                print('[MacKeyboardTap] listen-only event tap started')
        except Exception as e:
            print('[MacKeyboardTap] ERROR starting event tap:', e,
                  file=sys.stderr)
            self._teardown_tap()
            return
        finally:
            self._ready.set()

        try:
            while self._running:
                Quartz.CFRunLoopRunInMode(Quartz.kCFRunLoopDefaultMode,
                                          self.RUN_LOOP_INTERVAL_SECONDS,
                                          False)

                # Vigilante: si macOS desactivó el tap y no llegó el aviso
                # (o se perdió), se reactiva aquí.
                if self._running and self._tap is not None and \
                        not self.is_enabled():
                    self._reenable('watchdog')
        finally:
            self._teardown_tap()

    def _tap_callback(self, proxy, event_type, event, refcon):
        """
        Callback del tap. Debe ser mínimo: nada de lógica, ni E/S, ni locks.
        En un tap listen-only el valor devuelto se ignora, pero se devuelve el
        evento por claridad.
        """
        try:
            if event_type in EVENT_TAP_DISABLED:
                if self._running:
                    self._reenable('disabled event {}'.format(event_type))
                return event

            if event_type == EVENT_LEFT_MOUSE_DOWN:
                self._queue.put_nowait((QUEUE_MOUSE, 'left', None))
                return event

            if event_type == EVENT_RIGHT_MOUSE_DOWN:
                self._queue.put_nowait((QUEUE_MOUSE, 'right', None))
                return event

            if event_type == EVENT_OTHER_MOUSE_DOWN:
                button_number = Quartz.CGEventGetIntegerValueField(
                    event, Quartz.kCGMouseEventButtonNumber)

                # Botones laterales (atrás/adelante…) no se contabilizan.
                if button_number == MIDDLE_MOUSE_BUTTON_NUMBER:
                    self._queue.put_nowait((QUEUE_MOUSE, 'middle', None))

                return event

            keycode = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGKeyboardEventKeycode)

            chars = None
            is_autorepeat = False

            if event_type == EVENT_KEY_DOWN:
                is_autorepeat = bool(Quartz.CGEventGetIntegerValueField(
                    event, Quartz.kCGKeyboardEventAutorepeat))

                if not is_autorepeat:
                    _length, chars = Quartz.CGEventKeyboardGetUnicodeString(
                        event, 4, None, None)

            if is_autorepeat:
                return event

            self._queue.put_nowait((event_type, keycode, chars))
        except queue.Full:
            self.dropped_events += 1
        except Exception:
            # Jamás propagar excepciones dentro del callback del tap.
            pass

        return event

    def _reenable(self, reason):
        tap = self._tap

        if tap is None:
            return

        try:
            Quartz.CGEventTapEnable(tap, True)
            self.reenabled_count += 1

            if self.has_debug:
                print('[MacKeyboardTap] event tap re-enabled ({})'.format(
                    reason))
        except Exception as e:
            print('[MacKeyboardTap] ERROR re-enabling event tap:', e,
                  file=sys.stderr)

    def _teardown_tap(self):
        """
        Desactiva el tap, lo quita del run loop e invalida su puerto. Seguro de
        llamar varias veces y desde cualquier hilo.
        """
        tap, source, run_loop = self._tap, self._source, self._run_loop
        self._tap = self._source = self._run_loop = None

        if tap is not None:
            try:
                Quartz.CGEventTapEnable(tap, False)
            except Exception:
                pass

        if source is not None and run_loop is not None:
            try:
                Quartz.CFRunLoopRemoveSource(run_loop, source,
                                             Quartz.kCFRunLoopCommonModes)
            except Exception:
                pass

        if tap is not None:
            try:
                Quartz.CFMachPortInvalidate(tap)
            except Exception:
                pass

    #######################################
    # #         Hilo consumidor         # #
    #######################################

    def _consume_loop(self):
        while self._running:
            try:
                event_type, keycode, chars = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if event_type == QUEUE_MOUSE:
                # En eventos de ratón el segundo campo es el botón.
                self._dispatch_mouse(keycode)
                continue

            try:
                events = self._translator.translate(event_type, keycode, chars)
            except Exception as e:
                if self.has_debug:
                    print('[MacKeyboardTap] translate error:', e)
                continue

            for key_event in events:
                try:
                    self.callback(key_event)
                except Exception as e:
                    if self.has_debug:
                        print('[MacKeyboardTap] callback error:', e)

    def _dispatch_mouse(self, button):
        if self.mouse_callback is None:
            return

        try:
            self.mouse_callback(button)
        except Exception as e:
            if self.has_debug:
                print('[MacKeyboardTap] mouse callback error:', e)
