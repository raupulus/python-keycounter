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
# Project Name: Python Keycounter
# Description: Este script tomará datos de las pulsaciones de teclado, las almacenará
# # # y periódicamente las subirá a una API.
#
# Dependencies:
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
##
# # Este script tomará datos de las pulsaciones de teclado, las almacenará
# # y periódicamente las subirá a una API.
##

#######################################
# #       Importar Librerías        # #
#######################################
from time import sleep
import datetime
import random  # Genera números aleatorios --> random.randrange(1,100)
import functions as func
from dotenv import load_dotenv
import os

# Importo modelos
from Models.Keylogger import Keylogger
from Models.DbConnection import DbConnection
from Models.ApiConnection import ApiConnection

# Cargo archivos de configuración desde .env sobreescribiendo variables locales.
load_dotenv(override=True)

SERIAL_PORT = '/dev/ttyUSB0'

def insert_data_to_db (self):
    """
    Añade los datos de la última racha a la db.
    TODO → Implementar insertar datos en la DB.
    :return:
    """
    pass


def main():
    keylogger = Keylogger(has_debug=True)

    while True:
        #statistics = keylogger.statistics()
        keylogger.debug()
        sleep(1)



if __name__ == "__main__":
    main()