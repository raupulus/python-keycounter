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
# Project Name:
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

# Librería keyboard: https://pypi.org/project/keyboard/

#######################################
# #           Descripción           # #
#######################################
# Modelo puente que extiende la librería de la pantalla que usemos y le
# añade los métodos necesarios para poder mostrar los datos de puntuación.
# Esta librería y la de la pantalla puede ser necesario modificarla si la
# utilizas en un hardware distinto al que yo he utilizado pero te servirá
# de guía para una implementación más sencilla.

#######################################
# #       Importar Librerías        # #
#######################################
import time

# Importo la pantalla
from Models.LCDUart import LCDUart

#######################################
# #             Variables           # #
#######################################
sleep = time.sleep

#######################################
# #              Clase              # #
#######################################


class Display(LCDUart):
    def update_keycounter(self, data):
        """
        Dibuja todos los datos recibidos por el keylogger/keycount en la
        pantalla la cual se extiende desde esta clase.
        TODO → Implementar.
        :return:
        """

        # ATENCIÓN → AL CREAR LAS ÓRDENES, TIENE QUE ACABAR EN \r\n sólo
        # la última orden.

        # Datos para la sesión.
        session = data['session']

        # Datos para la racha actual.
        streak = data['streak']

        print('Entra en update_keycounter')

        color = "1"
        pulsations_current = "DCV32(0, 0,KEYS:" + str(streak.get('pulsations_current')) + ", " + color + ");"
        pulsations_current_special_keys = "DCV32(0, 32,SPK:" + str(streak.get('pulsations_current_special_keys')) + ", " + color + ");"
        pulsation_average = "DCV32(0, 64,AVG:" + str(streak.get('pulsation_average')) + ", 1);"
        combo_score_current = "DCV32(0, 96,SCORE:" + str(streak.get('combo_score_current')) + ", " + color + ");"
        last_pulsation_at = "DCV16(0, 128," + str(streak.get('last_pulsation_at')) + ", " + color + ");"

        new_screen = pulsations_current + pulsations_current_special_keys + \
                     pulsation_average + last_pulsation_at + combo_score_current

        self.write(bytes(new_screen + "\r\n", encoding='utf-8'))

        self.update_streak()
        self.update_session()

        #self.debug()

    def update_streak(self):
        """
        Actualiza la racha actual
        :return:
        """
        pass

    def update_session(self):
        """
        Actualiza los datos de sessión
        :return:
        """
        pass

    def debug(self):
        self.write(b"CLR(0);\r\n")
        # time.sleep(1)
        # lcd.write(b'DCV32(0,0 ,spotpear,0);\r\n')
        # lcd.write(b'VIEW();')

        self.write(b'CLR(12);\r\n')
        time.sleep(1)
        print('apagando')
        self.off()
        time.sleep(3)
        print('encendiendo')
        self.write(b'CLR(1);\r\n')
        self.on()

        time.sleep(1)
        self.write(b'BL(255);\r\n')
        time.sleep(1)
        self.write(b'BL(200);\r\n')
        time.sleep(1)
        self.write(b'BL(150);\r\n')
        time.sleep(1)
        self.write(b'BL(100);\r\n')
        sleep(1)
        self.write(b'BL(50);\r\n')
        time.sleep(1)
        self.write(b'BL(0);\r\n')

        time.sleep(1)
        self.write(b'PS(10, 30, 12);\r\n')
        self.write(b'PS(11, 30, 12);\r\n')
        self.write(b'PS(12, 30, 12);\r\n')
        self.write(b'PS(13, 30, 12);\r\n')
        self.write(b'PS(14, 30, 12);\r\n')
        self.write(b'PS(15, 30, 12);\r\n')
        self.write(b'PS(16, 30, 12);\r\n')
        self.write(b'PS(17, 30, 12);\r\n')
        self.write(b'PS(18, 30, 12);\r\n')

        time.sleep(2)
        #self.stop()
