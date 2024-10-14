#!/usr/bin/python3
# -*- encoding: utf-8 -*-
# @author     Raúl Caro Pastorino
# @email      public@raupulus.dev
# @web        https://raupulus.dev
# @gitlab     https://gitlab.com/raupulus
# @github     https://github.com/raupulus
# @twitter    https://twitter.com/raupulus
# @telegram   https://t.me/raupulus_diffusion

# Create Date: 2020
# Project Name: Python Keylogger
# Description: Keylogger escrito en python 3 para detectar las teclas
# pulsadas en equipos Linux o MacOs.

from datetime import datetime
from _thread import start_new_thread
from time import sleep
import subprocess
import keyboard
from Models.KeyboardLogger import KeyboardLogger
from Models.MouseLogger import MouseLogger
import os


if os.getenv('MOUSE_ENABLED') == 'True':
    import mouse

class Keylogger:
    # Modelo que representa datos y registros del teclado.
    model_keyboard = None

    # Modelo que representa datos y registros del ratón.
    model_mouse = None

    # Indica si necesita reiniciar Keycounter
    reboot = False

    # Lista con los dispositivos encontrados, se usa para recargar al
    # conectar algo como un teclado usb.
    devices = None

    # Almacena si hay una tecla presionada.
    is_down = { }

    # Indica si se pintará por pantalla datos para depuración.
    has_debug = False

    # Indica si también se cuentan pulsaciones del ratón
    MOUSE_ENABLED = False

    # Almacena la pantalla para mostrar datos, establecer None si no se usará
    # tiene que disponer del método update_keycounter(data) que procese los
    # datos devueltos por el método statistics() de esta clase.
    display = None

    # Traducción de carácteres para hacerlos imprimibles en texto plano.
    KEYS_MAP = {
        "space": " ",
        'backspace': " ",
        "\r": "(ENTER)",
        'enter': "(ENTER)",
        'unknown': '(click o tecla especial)',
        'ctrl': '(CTRL)',
        'alt': '(ALT)',
        'alt gr': '(ALT GR)',
        'menu': '(MENU)',
        'tab': '(TAB)',
        'shift': '(SHIFT)',
        'caps lock': '(CAPS LOCK)',
        'up': '(UP)',
        'down': '(DOWN)',
        'left': '(LEFT)',
        'right': '(RIGHT)',
        'home': '(HOME)',
        'page up': '(PAGE UP)',
        'page down': '(PAGE DOWN)',
        'insert': '(INSERT)',
        'delete': '(DELETE)',
        'help': '(HELP or VOLUME UP)',
        'pause': '(PAUSE)',
        'scroll lock': '(SCROLL LOCK)',
        'f1': '(F1)',
        'f2': '(F2)',
        'f3': '(F3)',
        'f4': '(F4)',
        'f5': '(F5)',
        'f6': '(F6)',
        'f7': '(F7)',
        'f8': '(F8)',
        'f9': '(F9)',
        'f10': '(F10)',
        'f11': '(F11)',
        'f12': '(F12)',
        'f13': '(F13 or VOLUME SILENCE)',
        'f14': '(F14 or VOLUME DOWN)',
        'num lock': '(NUM LOCK)',
        'esc': '(ESC)',
        'end': '(END)',
    }

    #######################################
    # #           Estadísticas          # #
    #######################################

    def __init__ (self, display=None, has_debug=False, mouse_enabled=True,
                  model_keyboard=None, model_mouse=None):
        # Establezco pantalla si existiera.
        self.display = display

        # Establezco si existe debug.
        self.has_debug = has_debug

        # Establezco control para ratón
        self.MOUSE_ENABLED = mouse_enabled

        # Instancio modelo para teclado
        if model_keyboard:
            self.model_keyboard = model_keyboard
        else:
            self.model_keyboard = KeyboardLogger()

        # Instancio modelo para ratón si procede
        if model_mouse and mouse_enabled:
            self.model_mouse = model_mouse
        elif mouse_enabled:
            self.model_mouse = MouseLogger()

        # Establezco contadores para sesión completa por día
        # self.model_keyboard.reset_global_counter()

        # Almaceno los dispositivos de entrada conectados
        self.devices = self.read_devices_by_id()

        # Comienza la escucha de teclas pulsadas
        start_new_thread(self.start_read_keyloggers_callback, ())

        # Inicio hilo para comprobar cambios en dispositivos conectados/desconectados
        start_new_thread(self.reload_keycounter_on_new_device, ())

    def read_devices_by_id (self):
        """
        Lee todos los dispositivos de entrada conectados en el sistema por id y
        los devuelve.
        """

        sleep(0.1)

        try:
            return subprocess.getoutput(
                'ls /dev/input/by-id/; cat /proc/bus/input/devices | grep -i -v -E "[Vv][Ii][Rr][Tt][Uu][Aa][Ll]" | grep -E "([Kk][Ee][Yy][Bb][Oo][Aa][Rr][Dd]|[Mm][Oo][Uu][Ss][Ee])"'
            )
        except Exception as e:
            if self.has_debug:
                print(
                    'Ha ocurrido un problema al comprobar lista de dispositivos')
                print('Esperando 10 segundos para reintentar')
                print(e)

            sleep(10)
            return ''

    def start_read_keyloggers_callback (self):
        """
        Inicia el callback para contar las teclas pulsadas
        """
        keyboard.hook(self.callback_keyboard)

        if self.MOUSE_ENABLED:
            mouse.on_click(self.callback_mouse, ('left',))
            mouse.on_right_click(self.callback_mouse, ('right',))
            mouse.on_middle_click(self.callback_mouse, ('middle',))

    def reload_keycounter_on_new_device (self):
        """
        Cuando se detecta un nuevo dispositivo conectado al sistema se recargará
        el keycounter para añadirlo a la lista de soportados.
        """
        while True:
            sleep(0.2)
            new_devices = self.read_devices_by_id()

            if self.devices != new_devices:
                # Almaceno los nuevos dispositivos en la clase
                self.devices = new_devices

                self.reboot = True

                if self.has_debug:
                    print(
                        'Hay cambios en los dispositivos, reiniciando callback')
                    print(new_devices)

                # Quito todos los hooks
                # keyboard.unhook_all()

                # Reestablezco lecturas de teclado en la librería keyboard
                keyboard._nixkeyboard.device = None
                keyboard._nixkeyboard.build_device()
                keyboard._nixkeyboard.build_tables()

                if keyboard._nixkeyboard.device:
                    sleep(0.1)
                    # keyboard._hooks = {}
                    keyboard._listener = keyboard._KeyboardListener()

                # Añado de nuevo el hook para leer teclado
                # keyboard.hook(self.callback_keyboard)

                # TODO → Reiniciar MOUSE, comprobar si ya se realiza?

            # Pausa entre cada comprobación.
            sleep(3)

    def callback_mouse (self, button):
        """
        Esta función registra las pulsaciones del ratón.
        :param button:
        """

        timestamp_utc = datetime.utcnow()

        # Comparo el tiempo desde la última pulsación para agrupar la racha.
        if (
                timestamp_utc - self.model_mouse.last_pulsation_at).seconds > self.model_mouse.COMBO_RESET:
            # Guardo la racha actual en la variable de rachas del modelo.
            self.model_mouse.add_old_streak()

            self.model_mouse.click_left = 0
            self.model_mouse.click_middle = 0
            self.model_mouse.click_right = 0
            self.model_mouse.current_clicks = 0
            self.model_mouse.clicks_current_start_at = timestamp_utc

        if self.has_debug:
            print('Botón pulsado: ' + button)

        if button == 'left':
            self.model_mouse.click_left += 1
        elif button == 'middle':
            self.model_mouse.click_middle += 1
        elif button == 'right':
            self.model_mouse.click_right += 1
        else:
            return

        # Asigno momento de esta pulsación.
        self.model_mouse.last_pulsation_at = timestamp_utc

        # Aumento contador de clicks en la racha actual.
        self.model_mouse.current_clicks += 1

        # Aumento el contador de clicks totales.
        self.model_mouse.total_clicks += 1

        # Asigno puntuación más alta si lo fuese.
        if self.model_mouse.current_clicks >= self.model_mouse.pulsations_hight:
            self.model_mouse.pulsations_hight = self.model_mouse.current_clicks
            self.model_mouse.pulsations_hight_at = timestamp_utc

        # Compruebo el día para restablecer contadores globales de sesión
        if timestamp_utc > self.model_mouse.current_day_end:
            start_new_thread(self.model_mouse.reset_global_counter, ())

        # Debug para comprobar rachas almacenadas.
        if self.has_debug:
            print('Rachas de ratón almacenadas')
            print(self.model_mouse.spurts)

    def callback_keyboard (self, event):
        """
        Esta función se ejecuta como callback cada vez que una tecla es pulsada
        recibiendo el evento y filtrando solo por las primeras pulsaciones
        (no las continuadas).
        """

        # Almaceno el tipo de evento
        event_type = event.event_type

        # Las teclas desconocidas o eventos de ratón se descartan
        if event.name == 'unknown':
            return None

        if event_type in ('up', 'down'):
            key = self.KEYS_MAP.get(event.name, event.name)

            # Almaceno si es una tecla especial
            special_key = True if event.name in self.KEYS_MAP else False

            # Marco si está pulsado para evitar registrar teclas presionadas
            if event_type == "down":
                if self.is_down.get(key, False):
                    return None
                else:
                    self.is_down[key] = True
            elif event_type == "up":
                self.is_down[key] = False

            # Aumento las pulsaciones de teclas indicando si es especial o no.
            if (
                    special_key or event.name == 'unknown') and event_type == 'down':
                self.model_keyboard.increase_pulsation(True)
            elif event_type == 'down':
                self.model_keyboard.increase_pulsation(False)

            # Añado salto de línea cuando se ha pulsado INTRO.
            if key == '(ENTER)' and event_type == 'down':
                key = "\n"

            # Pinta por consola datos de depuración si se indica debug.
            if self.has_debug:
                self.model_keyboard.debug(keypress=str(key))

            # Muestra datos actuales por la pantalla si esta existiera.
            start_new_thread(self.send_to_display, ())

    def send_to_display (self):
        """
        Muestra los datos por la pantalla usando el método: update_keycounter()
        que deberá existir en el modelo para la pantalla.
        :return:
        """

        # En caso de no existir pantalla se salta.
        if self.display is None:
            # En caso de querer debug se muestra advertencia.
            if self.has_debug:
                print('No hay pantalla, no se intentará pintar nada.')

            return False

        # Almaceno todos los datos actuales para pasarlos a la pantalla.
        data = self.model_keyboard.statistics()

        try:
            # Accede al método "update_keycounter" del modelo para la pantalla.
            start_new_thread(self.display.update_keycounter, (data,))
            return True
        except Exception as e:
            if self.has_debug:
                print(
                    'En Keylogger.py método send_to_display error al dibujar por pantalla')
                print(e)
            return False

    def set_socket (self, socket):
        """
        Asocia el socket del sistema al contador para el teclado.
        """
        self.model_keyboard.socket = socket

    def set_client_display_websocket(self, client):
        """
        Asocia una pantalla en la red local para mostrar datos siendo este
        el cliente.
        :param client: Datos del cliente.
        :return:
        """

        self.model_keyboard.client_display_websocket = client
