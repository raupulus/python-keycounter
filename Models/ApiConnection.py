#!/usr/bin/python3
# -*- encoding: utf-8 -*-

# @author     Raúl Caro Pastorino
# @email      dev@fryntiz.es
# @web        https://fryntiz.es
# @gitlab     https://gitlab.com/fryntiz
# @github     https://github.com/fryntiz
# @twitter    https://twitter.com/fryntiz
# @telegram   https://t.me/fryntiz

# Create Date: 2022
# Project Name:
# Description:
#
# Dependencies:
#
# Revision 0.01 - File Created
# Additional Comments:

# @copyright  Copyright © 2022 Raúl Caro Pastorino
# @license    https://wwww.gnu.org/licenses/gpl.txt

# Copyright (C) 2022  Raúl Caro Pastorino
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
# # Conexión a la base de datos.
##

#######################################
# #       Importar Librerías        # #
#######################################

import time
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import requests
import json
import os
import datetime

# Cargo archivos de configuración desde .env
import decimal

from dotenv import load_dotenv
load_dotenv(override=True)

#######################################
# #             Variables           # #
#######################################
sleep = time.sleep

#######################################
# #             Funciones           # #
#######################################


class ApiConnection:
    API_URL = os.getenv("API_URL")
    API_TOKEN = os.getenv("API_TOKEN")
    DEBUG = os.getenv("DEBUG") == "True"

    def requests_retry_session(
            self,
            retries=3,
            backoff_factor=0.3,
            status_forcelist=(500, 502, 504),
            session=None,
    ):
        """
        Crea una sesión para reintentar envío HTTP cuando falla.
        :param backoff_factor:
        :param status_forcelist:
        :param session:
        :return:
        """
        session = session or requests.Session()

        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        return session

    def send(self, path, datas_json, method):
        """
        Envía la petición a la API.
        :param path: Directorio dentro de la api (ex: /api/path/endpoint)
        :param datas_json:
        :return:
        """

        url = self.API_URL
        token = self.API_TOKEN
        full_url = url + path

        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + str(token),
        }

        # TODO → Check method POST|GET|PUT|DELETE

        # TODO → Comprobar si no es un array (datas_json), convertirlo en uno.

        # TODO → Añadir metadatos a la subida (info sobre iot que envía)

        # data.push(info)
        try:
            req = self.requests_retry_session().post(
                full_url,
                # data=json.dumps(datas_json),
                data=datas_json,
                headers=headers,
                timeout=30
            )

            if self.DEBUG:
                print('Respuesta de API: ', req.status_code)
                print('Recibido: ', req.text)

            # Guardado correctamente 201, con errores 200, mal 500 u otro error
            if int(req.status_code) == 201:
                return True
            elif int(req.status_code) == 200:
                if self.DEBUG:
                    print('Al guardar en la API algunos elementos tuvieron error.')
                return True
            else:
                return False
        except Exception as e:
            if self.DEBUG:
                print('Ha fallado la petición http :', e.__class__.__name__)
                print(e)

            sleep(5)

            return False

    def parse_array_to_json(self, rows, columns):
        """
        Convierte los datos recibidos en JSON
        :param rows: Tuplas con todas las entradas desde la DB.
        :param columns: Nombre de las columnas en orden respecto a tuplas.
        :return: Devuelve el objeto json
        """

        result = []

        # Compongo el objeto json que será devuelto.
        for row in rows:
            tupla = {}

            # Por cada tupla creo la pareja de clave: valor
            for iteracion in range(len(columns)):
                cell = str(row[iteracion])

                if columns[iteracion] != 'id':
                    tupla.update({columns[iteracion]: cell})

            result.append(tupla)

        return json.dumps(
            result,
            default=None,
            ensure_ascii=False,
            sort_keys=True,
            indent=4,
        )

    def parse_to_json(self, row, columns):
        """
        Convierte los datos recibidos en JSON
        :param rows: Tuplas con todas las entradas desde la DB.
        :param columns: Nombre de las columnas en orden respecto a tuplas.
        :return: Devuelve el objeto json
        """

        result = {}

        # Compongo el objeto json que será devuelto.
        for iteracion in range(len(columns)):
            cell = row[iteracion]
            #print('cell: ', cell)

            if isinstance(cell, decimal.Decimal):
                cell = float(cell)

            if isinstance(cell, datetime.datetime):
                cell = cell.strftime("%Y-%m-%d %H:%M:%S")

            if columns[iteracion] != 'id':
                result.update({columns[iteracion]: cell})

        return json.dumps(
            result,
            # default=None,
            # ensure_ascii=False,
            # sort_keys=True,
            # indent=4,
            skipkeys=False, ensure_ascii=True, check_circular=True,
            allow_nan=True, cls=None, indent=None, separators=None,
            default=None
        )

    def upload(self, name, path, datas, columns, method='GET'):
        """
        Recibe la ruta dentro de la API y los datos a enviar para procesar la
        subida atacando la API.
        :param path: Ruta dentro de la api
        :param datas: Datos a enviar
        """
        if datas:
            if self.DEBUG:
                print('Subiendo dato: ' + name + ', ruta de api: ' + path)

            result_send = False

            for data in datas:
                # print(data)
                datas_json = self.parse_to_json(data, columns)
                # print('Datos formateados en JSON:', datas_json)

                if (self.send(path, datas_json, method=method)):
                    result_send = True

            return result_send

    def get_websocket_server_display_info(self):
        """
        Pide a la api información sobre el dispositivo en la red local que
        actuará como servidor de websocket.
        :return:
        """
        url = self.API_URL
        token = self.API_TOKEN
        full_url = url + '/hardware/v1/get/device/16/info'

        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + str(token),
        }

        try:
            req = self.requests_retry_session().get(headers=headers,
                                                    url=full_url,
                                                    timeout=30)

            return json.loads(req.text)
        except Exception as e:
            if self.DEBUG:
                print('Error en get_websocket_server_display_info: ', e)

            return None
