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
from _thread import start_new_thread

# Importo modelos
from Models.Keylogger import Keylogger
from Models.DbConnection import DbConnection
from Models.ApiConnection import ApiConnection
from Models.Display import Display
from Models.Socket import Socket

# Cargo archivos de configuración desde .env sobreescribiendo variables locales.
load_dotenv(override=True)

# Parámetros de configuración por defecto, se pueden modificar en el .env

# Configuración Serial.
SERIAL_PORT = os.getenv('SERIAL_PORT') or None
SERIAL_BAUDRATE = os.getenv('SERIAL_BAUDRATE') or '9600'

# Configuración pantalla.
DISPLAY_ORIENTATION = os.getenv('SERIAL_BAUDRATE') or 'horizontal'

# Configuración DB.
DB_CONNECTION = os.getenv("DB_CONNECTION")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Configuración API para el volcado de datos.
API_URL = os.getenv("API_URL")
API_TOKEN = os.getenv("API_TOKEN")

# Configuración para identificar el dispositivo que envía los datos.
MI_PC = os.getenv("MI_PC")
PC_ID = os.getenv("PC_ID")
PC_TOKEN = os.getenv("PC_TOKEN")

# Debug
DEBUG = os.getenv("DEBUG") == "True"

def insert_data_to_db(self):
    """
    Añade los datos de la última racha a la db.
    TODO → Implementar insertar datos en la DB.
    :return:
    """
    pass


def upload_data_to_api(self):
    """
    Procesa la subida de datos a la API.
    TODO → Implementar Subir a la API.
    :return:
    """
    pass


def main():
    display = Display(port=SERIAL_PORT,
                      baudrate=SERIAL_BAUDRATE,
                      orientation=DISPLAY_ORIENTATION) if SERIAL_PORT else None

    # Instancio el keylogger, este quedará en un subproceso leyendo teclas.
    keylogger = Keylogger(display=display, has_debug=DEBUG)

    # TODO → Añadir a otro hilo
    # Instancio socket pasándole el keylogger para que alcance sus datos.
    socket = Socket(keylogger)


if __name__ == "__main__":
    main()
