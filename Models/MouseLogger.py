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
# Description:

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

#######################################
# #           Descripción           # #
#######################################
# Description:

#######################################
# #       Importar Librerías        # #
#######################################
from datetime import datetime
import os

#######################################
# #             Variables           # #
#######################################

#######################################
# #              Clase              # #
#######################################


class MouseLogger:
    # Nombre de la tabla para almacenar datos
    tablename = 'mouse'

    # Nombre del modelo
    name = 'Mouse'

    # Ruta para la API
    api_path = '/keycounter/v1/mouse/store'

    DEVICE_ID = os.getenv("DEVICE_ID")

    # Map para almacenar todas las rachas no guardadas en DB
    spurts = {}

    has_debug = False

    # Representa el inicio del día actual, para resetear contadores totales cada día.
    current_day_start = None
    current_day_end = None

    # Tiempo que dura una racha en segundos.
    COMBO_RESET = 15

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

    # Clicks por cada botón.
    click_left = 0
    click_right = 0
    click_middle = 0

    # Cantidad de clicks totales en la racha actual.
    current_clicks = 0

    # Comienzo de la racha actual.
    current_start_at = None

    # Momento de la última pulsación.
    last_pulsation_at = None

    # Almaceno el total de clicks entre todas las rachas.
    total_clicks = 0

    # Registro la mayor racha de clicks que se haya obtenido en las sesiones.
    pulsations_hight = 0
    pulsations_hight_at = None

    def __init__(self, has_debug=False):
        # Creo timestamp para inicializar contadores.
        current_timestamp = datetime.utcnow()

        self.has_debug = has_debug

        # Establezco timestamps.
        if self.last_pulsation_at is None:
            self.last_pulsation_at = current_timestamp

        if self.current_start_at is None:
            self.current_start_at = current_timestamp

        self.current_day_start = current_timestamp.replace(hour=0, minute=0,
                                                           second=0,
                                                           microsecond=0)
        self.current_day_end = current_timestamp.replace(hour=23, minute=59,
                                                         second=59,
                                                         microsecond=999999)

    def reset_global_counter(self):
        current_timestamp = datetime.utcnow()
        self.pulsations_hight = 0
        self.pulsations_hight_at = current_timestamp

    def add_old_streak(self):
        """
        Establece una racha pasada al map de rachas de forma que pueda ser
        insertado en la db o subido a la API.
        """
        self.spurts[self.last_pulsation_at] = {
            'start_at': self.current_start_at,
            'end_at': self.last_pulsation_at,
            'clicks_left': self.click_left,
            'clicks_right': self.click_right,
            'clicks_middle': self.click_middle,
            'total_clicks': self.current_clicks,
            'clicks_average': self.get_clicks_average(),
            'weekday': datetime.today().weekday(),
            'hardware_device_id': self.DEVICE_ID,
        }

    def get_clicks_average(self):
        """
        Devuelve la media de pulsaciones para la racha actual por segundos.
        """
        timestamp_utc = self.last_pulsation_at
        duration_seconds = (timestamp_utc - self.current_start_at).seconds

        if duration_seconds > 0 and self.current_clicks > 0:
            average_per_minute = (self.current_clicks / duration_seconds) * 60.0
        else:
            return 0.00

        return round(average_per_minute, 2)

    def tablemodel(self):
        """
        Plantea campos como modelo de datos para una base de datos y poder ser
        tomados desde el exterior.

        - Timestamp de inicio racha → start_at
        - Timestamp de fin racha → end_at
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
            'clicks_left': {
                'type': 'Numeric',
                'params': {
                    'precision': 15,
                    'asdecimal': False,
                },
                'others': None,
            },
            'clicks_right': {
                'type': 'Numeric',
                'params': {
                    'precision': 15,
                    'asdecimal': False,
                },
                'others': None,
            },
            'clicks_middle': {
                'type': 'Numeric',
                'params': {
                    'precision': 15,
                    'asdecimal': False,
                },
                'others': None,
            },
            'total_clicks': {
                'type': 'Numeric',
                'params': {
                    'precision': 15,
                    'asdecimal': False,
                },
                'others': None,
            },
            'clicks_average': {
                'type': 'String',
                'params': {},
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
            'hardware_device_id': {
                'type': 'Numeric',
                'params': {
                    'precision': 15,
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
