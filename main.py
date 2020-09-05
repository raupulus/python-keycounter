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
# Description: Este script tomará datos de las pulsaciones de teclado,
#              las almacenará
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
from dotenv import load_dotenv
import os

# Importo modelos
from Models.DbConnection import DbConnection
from Models.ApiConnection import ApiConnection
from Models.Display import Display
from Models.Socket import Socket
from Models.Keylogger import Keylogger

# Cargo archivos de configuración desde .env sobreescribiendo variables locales.
load_dotenv(override=True)

# Parámetros de configuración por defecto, se pueden modificar en el .env

# Configuración Serial.
SERIAL_PORT = os.getenv('SERIAL_PORT') or None
SERIAL_BAUDRATE = os.getenv('SERIAL_BAUDRATE') or '9600'

# Configuración pantalla.
DISPLAY_ORIENTATION = os.getenv('DISPLAY_ORIENTATION') or 'horizontal'

# Indica si se registran datos del mouse.
MOUSE_ENABLED = (os.getenv('MOUSE_ENABLED') == "True") or \
                (os.getenv('MOUSE_ENABLED') == "true")

# Debug
DEBUG = os.getenv("DEBUG") == "True"


def insert_data_in_db(dbconnection, tablemodel):
    """
    Almacena los datos de los sensores en la base de datos.
    :param dbconnection: Conexión con la base de datos.
    :param tablemodel: Modelo de datos.
    :return:
    """

    # Almaceno la clave de los elementos guardados correctamente en db.
    saved = []

    # Guardo las estadísticas registradas para el teclado de todas las rachas.
    for register in tablemodel.spurts:
        # Compruebo que existan datos registrados, que existe una racha.
        try:
            if register is not None:
                if (tablemodel.tablename == 'keyboard' and tablemodel.spurts[register]['pulsations'] > 1) or \
                   (tablemodel.tablename == 'mouse' and tablemodel.spurts[register]['total_clicks'] > 1):
                    save_data = dbconnection.table_save_data(
                        tablename=tablemodel.tablename,
                        params=tablemodel.spurts[register]
                    )
                else:
                    save_data = True

                # Si se ha llevado a cabo el guardado, se quita del map.
                if save_data:
                    saved.append(register)
        except Exception as e:
            if DEBUG:
                print('Error al insertar elemento en modelo: ' +
                      tablemodel.name)
                print(register)
                print(e)
            continue

    # Elimino los registros que fueron almacenados en la db correctamente.
    for key in saved:
        del tablemodel.spurts[key]


def upload_data_to_api(dbconnection, apiconnection, tablemodel):
    """
    Procesa la subida de datos a la API.
    """

    # El número de registros a subir a la api y eliminar de la DB
    n_registers = 10

    if DEBUG:
        print('Comprobando datos para subir a la API del modelo ' +
              tablemodel.name)

    # Parámetros/tuplas desde la base de datos.
    params_from_db = dbconnection.table_get_data_last(
                        tablemodel.tablename,
                        n_registers)

    # Columnas del modelo.
    columns = dbconnection.tables[tablemodel.tablename].columns.keys()

    name = tablemodel.name
    path = tablemodel.api_path

    try:
        if params_from_db:
            if DEBUG:
                print('Hay datos para subir a la API')
            response = apiconnection.upload(
                name,
                path,
                params_from_db,
                columns,
            )

            sleep(1)

            # Limpio los datos de la tabla si se ha subido correctamente.
            if response:
                if DEBUG:
                    print('Eliminando de la DB local rachas subidas')
                dbconnection.table_drop_last_elements(
                    tablemodel.tablename,
                    n_registers)

    except():
        if DEBUG:
            print('Error al subir datos a la api')


def loop(keylogger, socket, apiconnection=None, display=None):
    keylogger = keylogger
    # Instancio el modelo para guardar datos en la DB cada minuto.
    dbconnection = DbConnection()

    # Seteo tabla en el modelo de conexión a la DB para el keyboard.
    dbconnection.table_set_new(
        keylogger.model_keyboard.tablename,    # Nombre de la tabla.
        keylogger.model_keyboard.tablemodel()  # Modelo de tabla y columnas.
    )

    sleep(1)

    # Seteo tabla en el modelo de conexión a la DB para el mouse.
    dbconnection.table_set_new(
        keylogger.model_mouse.tablename,  # Nombre de la tabla.
        keylogger.model_mouse.tablemodel()  # Modelo de tabla y columnas.
    )

    # Pausa de 30 segundos para dar margen a tomar datos.
    sleep(30)

    while True:
        if DEBUG:
            print('Entra en while para guardar en la DB')

        try:
            insert_data_in_db(dbconnection, keylogger.model_keyboard)

            if MOUSE_ENABLED:
                insert_data_in_db(dbconnection, keylogger.model_mouse)

            # Inicia la subida a la base de datos si está configurada.
            if apiconnection and \
               apiconnection.API_TOKEN and \
               apiconnection.API_URL:
                if DEBUG:
                    print('Entra en if para subir a la API')

                sleep(5)

                upload_data_to_api(dbconnection,
                                   apiconnection,
                                   keylogger.model_keyboard)

                if MOUSE_ENABLED:
                    upload_data_to_api(dbconnection,
                                       apiconnection,
                                       keylogger.model_mouse)

                sleep(1)

            """
            if keylogger.reboot:
                tmp_model_keyboard = keylogger.model_keyboard
                tmp_model_mouse = keylogger.model_mouse

                print('Entra en reboot')

                del keylogger

                del socket

                sleep(1)

                keylogger = Keylogger(display=display,
                                      has_debug=DEBUG,
                                      mouse_enabled=MOUSE_ENABLED,
                                      model_keyboard=tmp_model_keyboard,
                                      model_mouse=tmp_model_mouse)

                socket = Socket(keylogger, has_debug=DEBUG)

            sleep(2)
            """

        except Exception as e:
            if DEBUG:
                print('Tipo de error al leer datos:', e, e.__class__)
        finally:
            sleep(10)

def main():
    display = Display(port=SERIAL_PORT,
                      baudrate=SERIAL_BAUDRATE,
                      orientation=DISPLAY_ORIENTATION,
                      has_debug=DEBUG) if SERIAL_PORT else None

    # Instancio el keylogger, este quedará en un subproceso leyendo teclas.
    keylogger = Keylogger(display=display,
                          has_debug=DEBUG,
                          mouse_enabled=MOUSE_ENABLED)

    # Instancio conexión con la API
    apiconnection = ApiConnection()

    # Instancio socket pasándole el keylogger para que alcance sus datos.
    socket = Socket(keylogger, has_debug=DEBUG)

    # Comienza el bucle para guardar datos y subirlos a la API.
    loop(keylogger, socket, apiconnection, display)


if __name__ == "__main__":
    main()
