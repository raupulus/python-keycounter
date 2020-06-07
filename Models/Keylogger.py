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
from functools import partial
# import os
import keyboard
# from datetime import datetime, date, time, timezone
from datetime import datetime
from _thread import start_new_thread

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
    # Nombre de la tabla para almacenar datos
    tablename = 'keyboard'

    # Map para almacenar todas las rachas no guardadas en DB
    spurts = {}

    # Tecla para terminar el programa o None para no utilizar ninguna tecla.
    terminate_key = None

    # Almacena si hay una tecla presionada.
    is_down = {}

    # Indica si se pintará por pantalla datos para depuración.
    has_debug = False

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

    def __init__(self, display=None, has_debug=False, terminate_key=None):
        # Establezco pantalla si existiera.
        self.display = display

        # Establezco si existe debug.
        self.has_debug = has_debug

        # Creo timestamp para inicializar contadores.
        current_timestamp = datetime.utcnow()

        # Establezco tecla para finalizar la captura.
        self.terminate_key = terminate_key

        # Establezco marca de inicio.
        self.start_at = current_timestamp

        # Establezco timestamps.
        self.last_pulsation_at = current_timestamp
        self.pulsations_current_start_at = current_timestamp
        self.pulsation_high_at = current_timestamp
        self.combo_score_high_at = current_timestamp

        # Comienza la escucha de teclas pulsadas
        start_new_thread(self.read_keyboard, ())

    def read_keyboard(self):
        """
        Esta función inicia la escucha de teclas constantemente para el
        keylogger.
        """
        keyboard.hook(partial(self.callback))
        keyboard.wait(self.terminate_key)

    def get_pulsation_average(self):
        """
        Devuelve la media de pulsaciones para la racha actual por segundos.
        :return:
        """
        timestamp_utc = datetime.utcnow()
        duration_seconds = (timestamp_utc - self.pulsations_current_start_at).seconds

        if duration_seconds > 0 and self.pulsations_current > 0:
            average_per_minute = (self.pulsations_current / duration_seconds) * 60.0
        else:
            return 0.00

        return round(average_per_minute, 2)

    def increase_pulsation(self, special_key=False):
        """
        Aumenta una pulsación controlando la racha.
        :return:
        """
        timestamp_utc = datetime.utcnow()

        self.pulsations_total += 1

        # Comparo el tiempo desde la última pulsación para agrupar la racha.
        if (timestamp_utc - self.last_pulsation_at).seconds > 15:
            # Guardo la racha actual en el map de rachas antes de resetear.
            self.add_old_streak(timestamp_utc)

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

    def add_old_streak(self, timestamp_utc):
        """
        Establece una racha pasada al map de rachas de forma que pueda ser
        insertado en la db o subido a la API.
        :return:
        """
        self.spurts[timestamp_utc] = {
            'start_at': self.pulsations_current_start_at,
            'end_at': timestamp_utc,
            'pulsations': self.pulsations_current,
            'pulsations_special_keys': self.pulsations_current_special_keys,
            'pulsation_average': self.get_pulsation_average(),
            'score': self.combo_score_current,
            'weekday': datetime.today().weekday(),
        }

    def set_combo(self, timestamp_utc, reset_sesion=False):
        """
        Establece la puntuación según la cantidad de pulsaciones y algoritmo
        :return:
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
        :return:
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
        :return:
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
        :return:
        """
        return {
            'session': self.statistics_session(),
            'streak': self.statistics_streak()
        }

    def callback(self, event):
        """
        Esta función se ejecuta como callback cada vez que una tecla es pulsada
        recibiendo el evento y filtrando solo por las primeras pulsaciones
        (no las continuadas).
        """
        if event.event_type in ('up', 'down'):
            key = self.KEYS_MAP.get(event.name, event.name)
            modifier = len(key) > 1

            # Almaceno si es una tecla especial
            special_key = True if event.name in self.KEYS_MAP else False

            # Almaceno el tipo de evento
            event_type = event.event_type

            # Las teclas desconocidas o eventos de ratón se descartan
            if event.name == 'unknown':
                # TODO → Distinguir si es un click e implementar contador.
                return None

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
            self.send_to_display()

            return True

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

        # Accede al método "update_keycounter" del modelo para la pantalla.
        self.display.update_keycounter(data)

        return True

    def tablemodel(self):
        """
        Plantea campos como modelo de datos para una base de datos y poder ser
        tomados desde el exterior.

        - Timestamp de inicio racha → start_at
        - Timestamp de fin racha → end_at
        - Pulsación total racha → pulsations
        - Pulsación total racha para teclas especiales → pulsations_special_keys
        - Pulsaciones media por minuto → pulsation_average
        - Puntuación del combo → score
        - Día de la semana (0 domingo) → weekday
        - Timestamp en el que se crea el registro → created_at
        """

        return {
            'start_at': {
                'type': 'DateTime',
                'params': None,
                'others': None,
            },
            'end_at': {
                'type': 'DateTime',
                'params': None,
                'others': None,
            },
            'pulsations': {
                'type': 'Numeric',
                'params': {
                    'precision': 15,
                    'asdecimal': False,
                },
                'others': None,
            },
            'pulsations_special_keys': {
                'type': 'Numeric',
                'params': {
                    'precision': 15,
                    'asdecimal': False,
                },
                'others': None,
            },

            'pulsation_average': {
                'type': 'String',
                'params': {},
                'others': None,
            },
            'score': {
                'type': 'Numeric',
                'params': {
                    'precision': 15,
                    'asdecimal': False,
                },
                'others': None,
            },
            'weekday': {
                'type': 'Numeric',
                'params': {
                    'precision': 1,
                    'asdecimal': False,
                },
                'others': None,
            },
            'created_at': {
                'type': 'DateTime',
                'params': None,
                'others': {
                    'default': datetime.utcnow
                },
            },
        }

    def debug(self, keypress=None):
        """
        Utilizada para debug de la aplicación.
        :return:
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
