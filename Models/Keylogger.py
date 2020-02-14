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
# Description: Keylogger escrito en python 3 para detectar las teclas pulsadas en un equipo linux. En principio debería funcionar también en windows (no comprobado por no tener ese sistema)

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
# Keylogger escrito en python 3 para detectar las teclas pulsadas en un equipo linux. 
# En principio debería funcionar también en windows (no comprobado por no tener ese 
# sistema)

#######################################
# #       Importar Librerías        # #
#######################################
from functools import partial
import atexit
import os
import keyboard
from datetime import datetime, date, time, timezone

#######################################
# #             Variables           # #
#######################################

#######################################
# #             TODO                # #
#######################################
# Crear dos subprocesos:
# 1 → Solo para el callback escuchando teclas
# 2 → Comprobar cada X segundos si hay racha

# En el MAP: COMBO_MAP → crear algoritmo dividiendo y redondeando hacia abajo
# que utilice la pareja de clave_map: combo_puntuacion_sumar

# Crear DB sqlite para registrar:
# Timestamp de inicio racha → start_at
# Timestamp de fin racha → end_at
# Pulsación total racha → pulsations
# Pulsación total racha para teclas especiales → pulsations_special_keys
# Puntuación del combo → score
# created_at
# Día de la semana (0 domingo) → weekday

# Implementar contador de clicks

# TODO → ERROR: el contador de teclas especiales cuenta el total, no la racha actual → revisar!!!

# TODO → Mayor racha de pulsaciones NO CUENTA NADA

# TODO → Teclas especiales como PrtSC las detecta como desconocidas y actualmente eso se interpreta como si fuese el ratón

# TODO → Implementar solo contador de carácteres para escribir, no teclas especiales
# y añadir a una variable independiente tanto la más alta como el combo y total
# de forma independiente al general

#######################################
# #              Clases             # #
#######################################

class Keylogger:
    # Tecla para terminar el programa o None para no utilizar ninguna tecla.
    terminate_key = None

    # Almacena si hay una tecla presionada.
    is_down = {}

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
        'help': '(HELP)',

    }

    #######################################
    # #           Estadísticas          # #
    #######################################

    # Timestamp con el comienzo de las mediciones.
    start_at = None

    # Timestamp con la última pulsación.
    last_pulsation_at = None

    # Total de pulsaciones.
    pulsations_total = 0

    # Total de pulsaciones para teclas especiales.
    pulsations_total_especial_keys = 0

    # Pulsaciones en la racha actual.
    pulsations_current = 0

    # Pulsaciones de teclas especiales en la racha actual.
    pulsations_current_special_keys = 0

    # Timestamp de la inicialización para la racha actual
    pulsations_current_start_at = None

    # Mayor racha de pulsaciones.
    pulsation_high = 0

    # Timestamp de la mejor racha de puntuaciones.
    pulsation_high_at = None

    # Puntuación total según la cantidad de combos.
    # TODO → Plantear si esto es viable, si llega a usarse horas el int desborda¿?¿?
    combo_score = 0

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

    def __init__(self, terminate_key=None):
        current_timestamp = datetime.utcnow()

        # Establezco tecla para finalizar la captura.
        self.terminate_key = terminate_key

        # Establezco marca de inicio.
        self.start_at = current_timestamp

        # Establezco timestamps.
        self.last_pulsation_at = current_timestamp
        self.pulsations_current_start_at = current_timestamp
        self.pulsation_high_at = current_timestamp

        # Se inicia la escucha de teclas.
        keyboard.hook(partial(self.callback))
        keyboard.wait(self.terminate_key)

    def get_pulsation_average(self):
        """
        Devuelve la media de pulsaciones para la racha actual por segundos.
        :return:
        """
        timestamp_utc = datetime.utcnow()
        duration_seconds = (timestamp_utc - self.pulsations_current_start_at).seconds

        return self.pulsations_current / duration_seconds

    def get_pulsations_total(self):
        """
        Devuelve la cantidad total de pulsaciones.
        :return:
        """
        return self.pulsations_total

    def get_pulsation_hight(self):
        """
        Devuelve la puntuación más alta de toda la sesión.
        :return:
        """
        return self.pulsation_high

    def increase_pulsation(self):
        """
        Aumenta una pulsación controlando la racha.
        TODO → De esta forma, al apagar equipo o terminar no guardaría, replantear esta parte
        :return:
        """
        timestamp_utc = datetime.utcnow()

        self.pulsations_total += 1

        # Comparo el tiempo desde la última pulsación para agrupar la racha.
        if (timestamp_utc - self.last_pulsation_at).seconds > 15:
            self.pulsations_current = 1
        else:
            self.pulsations_current += 1

        # Establezco el valor actual del combo
        self.set_combo()

        # Asigno momento de esta pulsación.
        self.last_pulsation_at = timestamp_utc

        # Asigno puntuación más alta si lo fuese.
        if self.pulsations_current >= self.pulsations_total:
            self.pulsations_total = self.pulsations_current
            self.pulsation_high_at = timestamp_utc

    def increase_pulsation_special_key(self):
        """
        Contabiliza como tecla especial pulsada.
        :return:
        """
        timestamp_utc = datetime.utcnow()

        self.pulsations_total_especial_keys += 1

        # Comparo el tiempo desde la última pulsación para agrupar la racha.
        if (timestamp_utc - self.last_pulsation_at).seconds > 15:
            self.pulsations_current_special_keys = 1
        else:
            self.pulsations_current_special_keys += 1

        pass

    def set_combo(self):
        """
        Establece la puntuación según la cantidad de pulsaciones y tiempo
        TODO → Temporalmente devuelvo una operación matemática estática, dinamizar para cuanto más pulsaciones mejor premio de combo.
        :return:
        """
        self.combo_score += int(self.pulsations_current * 0.05)

        return True

    def statistics(self):
        """
        Devuelve todas las estadísticas del momento.
        :return:
        """
        return [
            # Comienzo del contador
            self.start_at,

            # Timestamp con la última pulsación.
            self.last_pulsation_at,

            # Total de pulsaciones.
            self.pulsations_total,

            # Total de pulsaciones para teclas especiales.
            self.pulsations_total_especial_keys,

            # Pulsaciones en la racha actual.
            self.pulsations_current,

            # Pulsaciones de teclas especiales en la racha actual.
            self.pulsations_current_special_keys,

            # Timestamp de la inicialización para la racha actual
            self.pulsations_current_start_at,

            # Mayor racha de pulsaciones.
            self.pulsation_high,

            # Timestamp de la mejor racha de puntuaciones.
            self.pulsation_high_at,

            # Puntuación total según la cantidad de combos.
            self.combo_score
        ]

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

            # Aumento las pulsaciones de teclas.
            if event_type == 'down':
                self.increase_pulsation()

            # Contabilizo teclas especiales dado el caso.
            if (special_key or event.name == 'unknown') and event_type == 'down':
                #print('Es una tecla especial')
                self.increase_pulsation_special_key()
                pass

            # Añado salto de línea cuando se ha pulsado INTRO
            if key == '(ENTER)' and event_type == 'down':
                key = "\n"

            # DEBUG
            print('')
            print('Se ha pulsado la tecla: ' + str(key))
            print('')
            self.debug()

            return True

    def debug(self):
        """
        Utilizada para debug de la aplicación.
        :return:
        """
        statistics = self.statistics()

        print('')
        print('---------------------------------')
        print('------------- NUEVO -------------')
        print('Comienzo del contador: ' + str(statistics[0]))
        print('Timestamp con la última pulsación:' + str(statistics[1]))
        print('Total de pulsaciones: ' + str(statistics[2]))
        print('Total de pulsaciones para teclas especiales:' + str(statistics[3]))
        print('Pulsaciones en la racha actual: ' + str(statistics[4]))
        print('Pulsaciones de teclas especiales en la racha actual: ' + str(statistics[5]))
        print('Timestamp de la inicialización para la racha actual: ' + str(statistics[6]))
        print('Mayor racha de pulsaciones: ' + str(statistics[7]))
        print('Timestamp de la mejor racha de puntuaciones: ' + str(statistics[8]))
        print('Puntuación total según la cantidad de combos: ' + str(statistics[9]))
        print('---------------------------------')
        print('')
