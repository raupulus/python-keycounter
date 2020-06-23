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
DISPLAY_ORIENTATION = os.getenv('DISPLAY_ORIENTATION') or 'horizontal'

# Debug
DEBUG = os.getenv("DEBUG") == "True"


def insert_data_to_db(keylogger, dbconnection):
    """
    Almacena los datos de los sensores en la base de datos.
    :param dbconnection:
    :return:
    """

    # Almaceno la clave de los elementos guardados correctamente en db.
    saved = []

    # Guardo las estadísticas registradas para el teclado de todas las rachas.
    for register in keylogger.spurts:
        # Compruebo que existan datos registrados, que existe una racha.
        try:
            if register is not None:
                if keylogger.spurts[register]['pulsations'] > 1:
                    save_data = dbconnection.table_save_data(
                        tablename=keylogger.tablename,
                        params=keylogger.spurts[register]
                    )
                else:
                    save_data = True

                # Si se ha llevado a cabo el guardado, se quita del map.
                if save_data:
                    saved.append(register)
        except:
            print('Error al insertar elemento')
            print(register)

    # Elimino los registros que fueron almacenados en la db correctamente.
    for key in saved:
        del keylogger.spurts[key]


def upload_data_to_api(dbconnection, apiconnection):
    """
    Procesa la subida de datos a la API.
    """

    print('Comprobando datos para subir a la API')

    ## Parámetros/tuplas desde la base de datos.
    params_from_db = dbconnection.table_get_data_last('keyboard', 10)

    print('params_from_db')
    print(params_from_db)

    ## Columnas del modelo.
    columns = dbconnection.tables['keyboard'].columns.keys()

    name = 'Keyboard'
    path = '/keycounter/keyboard/add-json'

    try:
        if params_from_db:
            print('Hay datos para subir a la API')
            response = apiconnection.upload(
                name,
                path,
                params_from_db,
                columns,
            )

        # Limpio los datos de la tabla si se ha subido correctamente.
        if response:
            print('Eliminando de la DB local rachas subidas')
            dbconnection.table_drop_last_elements('keyboard', 10)

    except():
        print('Error al subir datos a la api')


def loop(keylogger, apiconnection=None):
    # Instancio el modelo para guardar datos en la DB cada minuto.
    dbconnection = DbConnection()

    # Seteo tabla en el modelo de conexión a la DB.
    dbconnection.table_set_new(
        keylogger.tablename,    # Nombre de la tabla.
        keylogger.tablemodel()  # Modelo de tabla y columnas.
    )

    # Pausa de 60 segundos para dar margen a tomar datos.
    sleep(60)

    while True:
        print('Entra en while para guardar en la DB')

        insert_data_to_db(keylogger, dbconnection)

        # TODO → Limitar subida a la api cada 5 minutos
        if apiconnection and apiconnection.API_TOKEN and apiconnection.API_URL:
            print('Entra en if para subir a la API')
            sleep(2)
            upload_data_to_api(dbconnection, apiconnection)
            sleep(1)

        try:
            pass

        except Exception as e:
            print('Tipo de error al leer datos:', e.__class__)
        finally:
            sleep(10)


def main():
    display = Display(port=SERIAL_PORT,
                      baudrate=SERIAL_BAUDRATE,
                      orientation=DISPLAY_ORIENTATION) if SERIAL_PORT else None

    # Instancio el keylogger, este quedará en un subproceso leyendo teclas.
    keylogger = Keylogger(display=display, has_debug=DEBUG)

    # Instancio conexión con la API
    apiconnection = ApiConnection()

    # Instancio socket pasándole el keylogger para que alcance sus datos.
    socket = Socket(keylogger)

    # Comienza el bucle para guardar datos y subirlos a la API.
    loop(keylogger, apiconnection)


if __name__ == "__main__":
    main()
