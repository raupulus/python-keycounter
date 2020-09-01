#!/usr/bin/python3
# -*- encoding: utf-8 -*-

# @author     Raúl Caro Pastorino
# @email      dev@fryntiz.es
# @web        https://fryntiz.es
# @gitlab     https://gitlab.com/fryntiz
# @github     https://github.com/fryntiz
# @twitter    https://twitter.com/fryntiz
# @telegram   https://t.me/fryntiz

# Create Date: 2020
# Project Name: Python Keylogger
# Description: Keylogger escrito en python 3 para detectar las teclas pulsadas
# en un equipo linux. En principio debería funcionar también en windows
# (no comprobado por no tener ese sistema)

#
# Dependencies: keyboard
#
# Revision 0.01 - File Created
# Additional Comments:

# @copyright  Copyright © 2020 Raúl Caro Pastorino
# @license    https://wwww.gnu.org/licenses/gpl.txt

# Copyright (C) 2020  Raúl Caro Pastorino
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

# Guía de estilos aplicada: PEP8

# Librería keyboard: https://pypi.org/project/keyboard/

#######################################
# #           Descripción           # #
#######################################
# Description: Keylogger escrito en python 3 para detectar las teclas pulsadas
# en un equipo linux. En principio debería funcionar también en windows
# (no comprobado por no tener ese sistema)

#######################################
# #       Importar Librerías        # #
#######################################
import keyboard
import mouse
from datetime import datetime
from _thread import start_new_thread
import subprocess
from time import sleep
from Models.KeyboardLogger import KeyboardLogger
from Models.MouseLogger import MouseLogger

#######################################
# #             Variables           # #
#######################################

#######################################
# #        NUEVAS FEATURES          # #
#######################################
# Esta lista describe las nuevas características que se "podría" implementar
# para mejorar la herramienta. Es necesario barajar cada una y su utilidad real.

# Implementar contador de clicks, algunas teclascomo PrtSC las detecta como
# desconocidas y no puedo filtrar que todos los clicks sean el "unknown"

# Implementar solo contador de carácteres para escribir (a-Z,.*[]}{:;),
# no teclas especiales. El objetivo es saber cuantas veces pulsa cada tecla

#######################################
# #              Clase              # #
#######################################


class Keylogger:
    ## Modelo que representa datos y registros del teclado.
    model_keyboard = KeyboardLogger()

    ## Modelo que representa datos y registros del ratón.
    model_mouse = MouseLogger()

    # Lista con los dispositivos encontrados, se usa para recargar al
    # conectar algo como un teclado usb.
    devices = None

    # Almacena si hay una tecla presionada.
    is_down = {}

    # Indica si se pintará por pantalla datos para depuración.
    has_debug = False

    # Indica si también se cuentan pulsaciones del ratón
    MOUSE_ENABLED = False

    # Almacena la pantalla para mostrar datos, establecer None si no se usará
    # tiene que disponer del método update_keycounter(data) que procese los
    # datos devueltos por el método statistics() de esta clase.
    display = None

    # Tiempo que dura una racha en segundos.
    COMBO_RESET = 15

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

    # Valores para el algoritmo del combo → clave_map: combo_puntuacion_a_sumar
    COMBO_MAP = {
        1: 0.01,
        2: 0.03,
        3: 0.05,
        4: 0.15,
        5: 0.30,
        6: 0.50,
        7: 0.70,
        8: 0.80,
        9: 0.90,
        10: 1.00
    }

    # Representa el inicio del día actual, para resetear contadores totales cada día.
    current_day_start = None
    current_day_end = None

    #######################################
    # #           Estadísticas          # #
    #######################################

    # ############# SESIÓN COMPLETA ############# #

    # Timestamp con el comienzo de las mediciones.
    start_at = None

    # Mayor racha de pulsaciones.
    pulsation_high = 0

    # Timestamp de la mejor racha de puntuaciones.
    pulsation_high_at = None

    # Total de pulsaciones.
    pulsations_total = 0

    # Total de pulsaciones para teclas especiales.
    pulsations_total_especial_keys = 0

    # Puntuación total según la cantidad de combos.
    combo_score = 0

    # Mayor Puntuación de combo en toda la sesión.
    combo_score_high = 0

    # Timestamp del momento en el que se consiguió la mejor racha
    combo_score_high_at = None

    # ############# RACHA ACTUAL ############# #

    # Pulsaciones en la racha actual.
    pulsations_current = 0

    # Pulsaciones de teclas especiales en la racha actual.
    pulsations_current_special_keys = 0

    # Timestamp de la inicialización para la racha actual
    pulsations_current_start_at = None

    # Timestamp con la última pulsación.
    last_pulsation_at = None

    # Puntuación de combos en la racha actual.
    combo_score_current = 0

    def __init__(self, display=None, has_debug=False, mouse_enabled=True):
        # Establezco pantalla si existiera.
        self.display = display

        # Establezco si existe debug.
        self.has_debug = has_debug

        # Establezco control para ratón
        self.MOUSE_ENABLED = mouse_enabled

        # Creo timestamp para inicializar contadores.
        current_timestamp = datetime.utcnow()

        # Establezco contadores para sesión completa por día
        self.reset_global_counter()

        # Establezco timestamps.
        self.last_pulsation_at = current_timestamp
        self.pulsations_current_start_at = current_timestamp

        # Almaceno los dispositivos de entrada conectados
        self.devices = self.read_devices_by_id()

        # Comienza la escucha de teclas pulsadas
        start_new_thread(self.start_read_keycounter_callback, ())

        # Inicio hilo para comprobar cambios en dispositivos conectados/desconectados
        start_new_thread(self.reload_keycounter_on_new_device, ())

    def read_devices_by_id(self):
        """
        Lee todos los dispositivos de entrada conectados en el sistema por id y
        los devuelve.
        """
        return subprocess.getoutput('ls /dev/input/by-id/')

    def start_read_keycounter_callback(self):
        """
        Inicia el callback para contar las teclas pulsadas
        """
        keyboard.hook(self.callback)

        mouse.on_click(self.callback_mouse, ('left',))
        mouse.on_right_click(self.callback_mouse, ('right',))
        mouse.on_middle_click(self.callback_mouse, ('middle',))

    def reload_keycounter_on_new_device(self):
        """
        Cuando se detecta un nuevo dispositivo conectado al sistema se recargará
        el keycounter para añadirlo a la lista de soportados.
        """
        while True:
            new_devices = self.read_devices_by_id()

            if self.devices != new_devices:
                # Almaceno los nuevos dispositivos en la clase
                self.devices = new_devices

                if self.has_debug:
                    print('Hay cambios en los dispositivos, reiniciando callback')
                    print(new_devices)

                # Quito todos los hooks
                keyboard.unhook_all()

                # Reestablezco lecturas de teclado en la librería keyboard
                keyboard._nixkeyboard.device = None
                keyboard._nixkeyboard.build_device()
                sleep(1)
                keyboard._nixkeyboard.build_tables()
                sleep(1)
                keyboard._hooks = {}
                keyboard._listener = keyboard._KeyboardListener()
                sleep(1)

                # Vuelvo a quitar todos los hooks, esto activa eventos por defecto
                keyboard.unhook_all()

                # Añado de nuevo el hook para leer teclado
                keyboard.hook(self.callback)

                # TODO → Reiniciar MOUSE


            # Pausa entre cada comprobación.
            sleep(3)

    def reset_global_counter(self):
        """
        Borra los contadores globales al acabar el día.
        """
        if self.has_debug:
            print('Restableciendo contadores de la sesión')

        current_day_start = datetime.utcnow()
        current_day_start = current_day_start.replace(hour=0, minute=0,
                                                      second=0, microsecond=0)
        current_day_end = datetime.utcnow()
        current_day_end = current_day_end.replace(hour=23, minute=59,
                                                      second=59, microsecond=999999)

        if self.has_debug:
            print('Marca de inicio de la sesión')
            print(current_day_start)

            print('Marca de final de la sesión')
            print(current_day_end)

        self.current_day_start = current_day_start
        self.current_day_end = current_day_end

        # Creo timestamp para inicializar contadores.
        current_timestamp = datetime.utcnow()

        # Timestamp con el comienzo de las mediciones.
        self.start_at = current_timestamp

        # Mayor racha de pulsaciones.
        self.pulsation_high = 0

        # Timestamp de la mejor racha de puntuaciones.
        self.pulsation_high_at = current_timestamp

        # Total de pulsaciones.
        self.pulsations_total = 0

        # Total de pulsaciones para teclas especiales.
        self.pulsations_total_especial_keys = 0

        # Puntuación total según la cantidad de combos.
        self.combo_score = 0

        # Mayor Puntuación de combo en toda la sesión.
        self.combo_score_high = 0

        # Timestamp del momento en el que se consiguió la mejor racha
        self.combo_score_high_at = current_timestamp

        # Borro contadores globales para el teclado
        # TODO → Refactorizar guardado de datos en el modelo de teclado
        self.model_keyboard.reset_global_counter()

        # Borro contadores globales para el ratón
        self.model_mouse.reset_global_counter()

    def get_pulsation_average(self):
        """
        Devuelve la media de pulsaciones para la racha actual por segundos.
        """
        timestamp_utc = self.last_pulsation_at
        duration_seconds = (timestamp_utc - self.pulsations_current_start_at).seconds

        if duration_seconds > 0 and self.pulsations_current > 0:
            average_per_minute = (self.pulsations_current / duration_seconds) * 60.0
        else:
            return 0.00

        return round(average_per_minute, 2)

    def increase_pulsation(self, special_key=False):
        """
        Aumenta una pulsación controlando la racha.
        """
        timestamp_utc = datetime.utcnow()

        self.pulsations_total += 1

        # Comparo el tiempo desde la última pulsación para agrupar la racha.
        if (timestamp_utc - self.last_pulsation_at).seconds > self.COMBO_RESET:
            # Guardo la racha actual en el map de rachas antes de resetear.
            self.add_old_streak()

            # Establezco marca de tiempo para la nueva racha
            self.pulsations_current_start_at = timestamp_utc

            # Reseteo contador de teclas pulsadas en la nueva racha.
            self.pulsations_current = 1

            # Reseteo contador de teclas especiales pulsadas en la nueva racha.
            self.pulsations_current_special_keys = 0

            # Establezco el valor actual del combo reseteando contador de racha.
            self.set_combo(timestamp_utc, reset_sesion=True)

            # Si es una tecla especial la contabilizo.
            if special_key:
                self.pulsations_current_special_keys = 1
                self.pulsations_total_especial_keys += 1
        else:
            # Sumo una pulsación al contador.
            self.pulsations_current += 1

            # Establezco el valor actual del combo sin resetear contador de racha.
            self.set_combo(timestamp_utc, reset_sesion=False)

            # Si es una tecla especial la contabilizo.
            if special_key:
                self.pulsations_current_special_keys += 1
                self.pulsations_total_especial_keys += 1

        # Asigno momento de esta pulsación.
        self.last_pulsation_at = timestamp_utc

        # Asigno puntuación más alta si lo fuese.
        if self.pulsations_current >= self.pulsation_high:
            self.pulsation_high = self.pulsations_current
            self.pulsation_high_at = timestamp_utc

        # Compruebo el día para reestablecer contadores globales de sesión
        if timestamp_utc > self.current_day_end:
            start_new_thread(self.reset_global_counter, ())

    def add_old_streak(self):
        """
        Establece una racha pasada al map de rachas de forma que pueda ser
        insertado en la db o subido a la API.
        """
        self.model_keyboard.spurts[self.last_pulsation_at] = {
            'start_at': self.pulsations_current_start_at,
            'end_at': self.last_pulsation_at,
            'pulsations': self.pulsations_current,
            'pulsations_special_keys': self.pulsations_current_special_keys,
            'pulsation_average': self.get_pulsation_average(),
            'score': self.combo_score_current,
            'weekday': datetime.today().weekday(),
        }

    def set_combo(self, timestamp_utc, reset_sesion=False):
        """
        Establece la puntuación según la cantidad de pulsaciones y algoritmo
        """

        # Creo el valor de la puntuación para sumar con este combo.
        new_combo_score = int(self.pulsations_current * 0.15)

        # Controlo si restablecer contador de combos para la sesión.
        if reset_sesion:
            self.combo_score_current = 0
            return False

        # Compruebo si pertenece combo y devuelvo bool indiciando si hay
        if (int((self.pulsations_current * 2.7) *
                ((self.pulsations_current + 1) * 3.4)) % 5) == 0:

            # Añado puntuación al contador global.
            self.combo_score += new_combo_score

            # Añado puntuación al contador de racha.
            self.combo_score_current += new_combo_score

            # En caso de ser una puntuación de combo record se añade al registro.
            if self.combo_score_current > self.combo_score_high:
                self.combo_score_high = self.combo_score_current
                self.combo_score_high_at = timestamp_utc

            return True

        return False

    def statistics_session(self):
        """
        Devuelve las estadísticas generales a nivel de la sesión.
        """
        return {
            'start_at': self.start_at,
            'pulsation_high': self.pulsation_high,
            'pulsation_high_at': self.pulsation_high_at,
            'pulsations_total': self.pulsations_total,
            'pulsations_total_especial_keys': self.pulsations_total_especial_keys,
            'combo_score': self.combo_score,
            'combo_score_high': self.combo_score_high,
            'combo_score_high_at': self.combo_score_high_at
        }

    def statistics_streak(self):
        """
        Devuelve las estadísticas solo para la racha actual.
        """
        return {
            'pulsations_current': self.pulsations_current,
            'pulsations_current_special_keys': self.pulsations_current_special_keys,
            'pulsation_average': self.get_pulsation_average(),
            'pulsations_current_start_at': self.pulsations_current_start_at,
            'last_pulsation_at': self.last_pulsation_at,
            'combo_score_current': self.combo_score_current
        }

    def statistics(self):
        """
        Devuelve todas las estadísticas.
        """
        return {
            'session': self.statistics_session(),
            'streak': self.statistics_streak()
        }

    def callback_mouse(self, button):
        """
        Esta función registra las pulsaciones del ratón.
        :param button:
        """

        timestamp_utc = datetime.utcnow()

        # Comparo el tiempo desde la última pulsación para agrupar la racha.
        if (timestamp_utc - self.model_mouse.last_pulsation_at).seconds > self.COMBO_RESET:
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
        if timestamp_utc > self.current_day_end:
            start_new_thread(self.model_mouse.reset_global_counter, ())

        # Debug para comprobar rachas almacenadas.
        if self.has_debug:
            print('Rachas de ratón almacenadas')
            print(self.model_mouse.spurts)

    def callback(self, event):
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
            if (special_key or event.name == 'unknown') and event_type == 'down':
                self.increase_pulsation(True)
            elif event_type == 'down':
                self.increase_pulsation(False)

            # Añado salto de línea cuando se ha pulsado INTRO.
            if key == '(ENTER)' and event_type == 'down':
                key = "\n"

            # Pinta por consola datos de depuración si se indica debug.
            if self.has_debug:
                self.debug(keypress=str(key))

            # Muestra datos actuales por la pantalla si esta existiera.
            start_new_thread(self.send_to_display, ())

    def send_to_display(self):
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
        data = self.statistics()

        try:
            # Accede al método "update_keycounter" del modelo para la pantalla.
            start_new_thread(self.display.update_keycounter, (data,))
            return True
        except Exception as e:
            if self.has_debug:
                print('En Keylogger.py método send_to_display error al dibujar por pantalla')
                print(e)
            return False

    def debug(self, keypress=None):
        """
        Utilizada para debug de la aplicación.
        """
        statistics = self.statistics()
        session = statistics['session']
        streak = statistics['streak']

        # Limpiar la salida del terminal.
        print(chr(27) + "[2J")

        if keypress:
            print('')
            print('Se ha pulsado la tecla: ' + str(keypress))
            print('')

        # Muestro todos los datos formateados.
        print('')
        print('---------------------------------')
        print('--------- SESIÓN COMPLETA -------')
        print('---------------------------------')
        print('')
        print('La sesión comenzó: ' + str(session.get('start_at')))
        print('Racha con número de pulsacionespulsaciones más alta: ' + str(session.get('pulsation_high')))
        print('Momento de la puslación más alta: ' + str(session.get('pulsation_high_at')))
        print('Número de pulsaciones total: ' + str(session.get('pulsations_total')))
        print('Número de pulsaciones total en teclas especiales: ' + str(session.get('pulsations_total_especial_keys')))
        print('Puntuación total obtenida en combos: ' + str(session.get('combo_score')))
        print('Puntuación más alta obtenida en combos en una racha: ' + str(session.get('combo_score_high')))
        print('Momento de la puntuación más alta obtenida en combos en una racha: ' + str(session.get('combo_score_high_at')))
        print('')
        print('---------------------------------')
        print('---------- RACHA ACTUAL ---------')
        print('---------------------------------')
        print('Pulsaciones en racha actual: ' + str(streak.get('pulsations_current')))
        print('Pulsaciones de teclas especiales en racha actual: ' + str(streak.get('pulsations_current_special_keys')))
        print('Velocidad media de pulsaciones por minuto: ' + str(streak.get('pulsation_average')))
        print('Momento en el que inicia la racha: ' + str(streak.get('pulsations_current_start_at')))
        print('Momento de la última pulsación: ' + str(streak.get('last_pulsation_at')))
        print('Puntuación de combo para la racha actual: ' + str(streak.get('combo_score_current')))
        print('')
