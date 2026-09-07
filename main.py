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
import time
from _thread import start_new_thread
from dotenv import load_dotenv
import os

# Importo modelos
from Models.DbConnection import DbConnection
from Models.ApiConnection import ApiConnection
from Models.Display import Display
from Models.Socket import Socket
from Models.ClientDisplayWebsocket import ClientDisplayWebsocket
from Models.Keylogger import Keylogger
from Models.SystemInfo import SystemInfo

# Cargo archivos de configuración desde .env sobreescribiendo variables locales.
load_dotenv(override=True)

# Parámetros de configuración por defecto, se pueden modificar en el .env

# Configuración Serial.
SERIAL_PORT = os.getenv('SERIAL_PORT') or None
SERIAL_BAUDRATE = os.getenv('SERIAL_BAUDRATE') or '9600'

# Configuración pantalla.
SERIAL_DISPLAY_ENABLED = os.getenv('SERIAL_DISPLAY_ENABLED') == 'True'
DISPLAY_ORIENTATION = os.getenv('DISPLAY_ORIENTATION') or 'horizontal'

# Indica si se registran datos del mouse.
MOUSE_ENABLED = (os.getenv('MOUSE_ENABLED') == "True") or \
                (os.getenv('MOUSE_ENABLED') == "true")

# Debug
DEBUG = os.getenv("DEBUG") == "True"
UPLOAD_API = os.getenv("UPLOAD_API") == "True"

SEND_DATA_TO_WEBSOCKET_SERVER = os.getenv("SEND_DATA_TO_WEBSOCKET_SERVER") == "True"

# Control de sincronización inicial desde la API
SYNC_RETRY_INTERVAL_SECONDS = 3600  # 1 hora tras fallo
is_synced = False
last_sync_attempt = 0


def try_sync_initial_stats(keylogger, apiconnection):
    """
    Intenta descargar las estadísticas acumuladas del día desde la API (/keycounter/summary).
    Sincroniza teclado y (si MOUSE_ENABLED) ratón.
    Si falla (error, 404 o 403), registra el intento para esperar 1 hora antes del próximo.
    Si tiene éxito, marca is_synced = True y no vuelve a sincronizar.
    """
    global is_synced, last_sync_attempt

    if is_synced or apiconnection is None:
        return

    last_sync_attempt = time.time()

    if DEBUG:
        print('Intentando sincronizar estadísticas acumuladas del día desde la API (/keycounter/summary)...')

    summary = apiconnection.get_summary(date='today')
    if summary is not None:
        if keylogger.model_keyboard:
            keylogger.model_keyboard.apply_initial_summary(summary)

        if MOUSE_ENABLED and keylogger.model_mouse and 'mouse' in summary and summary['mouse']:
            keylogger.model_mouse.apply_initial_summary(summary['mouse'])

        is_synced = True
        if DEBUG:
            print('Sincronización inicial con la API completada exitosamente.')
    else:
        if DEBUG:
            print('No se pudo sincronizar estadísticas iniciales de la API. '
                  'Próximo reintento en 1 hora.')


def insert_data_in_db(dbconnection, tablemodel):
    """
    Almacena los datos de los sensores en la base de datos.
    :param dbconnection: Conexión con la base de datos.
    :param tablemodel: Modelo de datos.
    :return:
    """

    # Almaceno la clave de los elementos guardados correctamente en db.
    saved = []

    if DEBUG:
        print('Comprobando datos para guardar en la DB del modelo ' + tablemodel.name)
        print(tablemodel.spurts)

    # Guardo las estadísticas registradas para el teclado de todas las rachas.
    for register in tablemodel.spurts:
        # Compruebo que existan datos registrados, que existe una racha.
        try:
            if register is not None:
                if (tablemodel.tablename == 'keyboard' and tablemodel.spurts[register]['pulsations'] > 1) or \
                   (tablemodel.tablename == 'mouse' and tablemodel.spurts[register]['total_clicks'] > 1):

                    if DEBUG:
                        print('Entra en if para guardar en la DB, tabla: ' + tablemodel.name)
                        print(tablemodel.spurts[register])

                    save_data = dbconnection.table_save_data(
                        tablename=tablemodel.tablename,
                        params=tablemodel.spurts[register]
                    )
                else:
                    if DEBUG:
                        print('No hay datos válidos para guardar en la DB')

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


def upload_data_to_api(dbconnection, apiconnection, tablemodel, system_info=None):
    """
    Procesa la subida de datos a la API inyectando opcionalmente estadísticas
    de hardware del dispositivo.
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

    # Obtengo telemetría de hardware de forma protegida (si falla no interrumpe la subida)
    extra_fields = None
    if system_info is not None:
        try:
            hw_info = system_info.get_hardware_device_info()
            if hw_info and isinstance(hw_info, dict):
                extra_fields = {'hardware_device_info': hw_info}
        except Exception as e:
            if DEBUG:
                print('Error al recopilar hardware_device_info (ignorado):', e)
            extra_fields = None

    try:
        if params_from_db:
            if DEBUG:
                print('Hay datos para subir a la API')
            response = apiconnection.upload(
                name,
                path,
                params_from_db,
                columns,
                extra_fields=extra_fields
            )

            sleep(1)

            # Limpio los datos de la tabla si se ha subido correctamente.
            if response:
                if DEBUG:
                    print('Eliminando de la DB local rachas subidas')
                dbconnection.table_drop_last_elements(
                    tablemodel.tablename,
                    n_registers)

    except Exception as e:
        if DEBUG:
            print('Error al subir datos a la api:', e)


def loop(keylogger, socket, apiconnection=None, display=None, system_info=None):
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
    if keylogger.model_mouse:
        dbconnection.table_set_new(
            keylogger.model_mouse.tablename,  # Nombre de la tabla.
            keylogger.model_mouse.tablemodel()  # Modelo de tabla y columnas.
        )

    # Pausa de 30 segundos para dar margen a tomar datos.
    sleep(30)

    while True:
        if DEBUG:
            print('Entra en while para guardar en la DB y subir a la API')

        try:
            insert_data_in_db(dbconnection, keylogger.model_keyboard)

            if MOUSE_ENABLED:
                insert_data_in_db(dbconnection, keylogger.model_mouse)

            # Inicia la subida a la base de datos si está configurada.
            if UPLOAD_API and \
               apiconnection and \
               apiconnection.API_TOKEN and \
               apiconnection.API_URL:
                if DEBUG:
                    print('Entra en if para subir a la API')

                sleep(5)

                upload_data_to_api(dbconnection,
                                   apiconnection,
                                   keylogger.model_keyboard,
                                   system_info=system_info)

                if MOUSE_ENABLED:
                    upload_data_to_api(dbconnection,
                                       apiconnection,
                                       keylogger.model_mouse,
                                       system_info=system_info)

                sleep(1)

                # Reintento de sincronización si nunca se sincronizó y ya pasó 1 hora
                if not is_synced and (time.time() - last_sync_attempt >= SYNC_RETRY_INTERVAL_SECONDS):
                    start_new_thread(try_sync_initial_stats, (keylogger, apiconnection))

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
                      has_debug=DEBUG) if SERIAL_DISPLAY_ENABLED else None

    # Instancio el keylogger, este quedará en un subproceso leyendo teclas.
    keylogger = Keylogger(display=display,
                          has_debug=DEBUG,
                          mouse_enabled=MOUSE_ENABLED)

    # Instancio conexión con la API
    apiconnection = ApiConnection()

    # Instancio colector de telemetría de hardware (Linux / macOS nativo)
    system_info = SystemInfo.create(debug=DEBUG)

    # Instancio socket pasándole el keylogger para que alcance sus datos.
    socket = Socket(keylogger, has_debug=DEBUG)

    if socket:
        keylogger.set_socket(socket)

    # Instancio cliente para pantalla con servidor websocket
    if SEND_DATA_TO_WEBSOCKET_SERVER:
        client_display_websocket = ClientDisplayWebsocket(keylogger, apiconnection,
                                                      debug=DEBUG)
        if client_display_websocket:
            keylogger.set_client_display_websocket(client_display_websocket)

    # Intenta sincronizar estadísticas del día al arrancar en segundo plano
    if UPLOAD_API and apiconnection and apiconnection.API_TOKEN and apiconnection.API_URL:
        start_new_thread(try_sync_initial_stats, (keylogger, apiconnection))

    # Comienza el bucle para guardar datos y subirlos a la API.
    loop(keylogger, socket, apiconnection, display, system_info=system_info)


if __name__ == "__main__":
    main()
