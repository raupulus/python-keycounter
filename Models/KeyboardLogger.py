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

#######################################
# #             Variables           # #
#######################################

#######################################
# #              Clase              # #
#######################################

class KeyboardLogger:
    # Nombre de la tabla para almacenar datos
    tablename = 'keyboard'

    # Nombre del modelo
    name = 'Keyboard'

    # Ruta para la API
    api_path = '/keycounter/keyboard/add-json'

    # Map para almacenar todas las rachas no guardadas en DB
    spurts = {}

    def reset_global_counter(self):
        pass

    def increase_pulsation(self, special_key=False):
        pass

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