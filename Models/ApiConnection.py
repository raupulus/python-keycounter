#!/usr/bin/python3
# -*- encoding: utf-8 -*-

# @author     Raúl Caro Pastorino
# @email      public@raupulus.dev
# @web        https://raupulus.dev
# @gitlab     https://gitlab.com/raupulus
# @github     https://github.com/raupulus
# @twitter    https://twitter.com/raupulus
# @telegram   https://t.me/raupulus_diffusion

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
                if self.DEBUG:
                    print(f'Error en la API ({req.status_code}): {req.text}')
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

    def parse_to_json(self, row, columns, extra_fields=None):
        """
        Convierte los datos recibidos en JSON normalizando formatos para la API V2.
        :param row: Tupla con la entrada desde la DB.
        :param columns: Nombre de las columnas en orden respecto a tupla.
        :param extra_fields: Diccionario opcional con campos adicionales (ej: hardware_device_info)
        :return: Devuelve el objeto json
        """

        result = {}

        # Compongo el objeto json que será devuelto.
        for iteracion in range(len(columns)):
            col = columns[iteracion]
            cell = row[iteracion]

            if isinstance(cell, decimal.Decimal):
                cell = float(cell)

            if isinstance(cell, datetime.datetime):
                cell = cell.strftime("%Y-%m-%d %H:%M:%S")
            elif col in ('start_at', 'end_at', 'created_at') and isinstance(cell, str):
                # SQLite almacena cadenas con microsegundos (ej: '2026-09-07 10:52:25.729175')
                try:
                    clean_val = cell.split('.')[0].replace('T', ' ')
                    dt = datetime.datetime.strptime(clean_val, "%Y-%m-%d %H:%M:%S")
                    cell = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass

            if col != 'id':
                result.update({col: cell})

        if extra_fields and isinstance(extra_fields, dict):
            result.update(extra_fields)

        return json.dumps(
            result,
            skipkeys=False, ensure_ascii=True, check_circular=True,
            allow_nan=True, cls=None, indent=None, separators=None,
            default=None
        )

    def upload(self, name, path, datas, columns, method='GET', extra_fields=None):
        """
        Recibe la ruta dentro de la API y los datos a enviar para procesar la
        subida atacando la API.
        :param path: Ruta dentro de la api
        :param datas: Datos a enviar
        :param extra_fields: Diccionario opcional con campos adicionales para el JSON
        """
        if datas:
            if self.DEBUG:
                print('Subiendo dato: ' + name + ', ruta de api: ' + path)

            result_send = False

            for data in datas:
                datas_json = self.parse_to_json(data, columns, extra_fields=extra_fields)

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
        # El display es otro dispositivo: por seguridad el token de keycounter no
        # puede leerlo, se usan credenciales propias del display.
        display_id = os.getenv("DISPLAY_ID")
        display_token = os.getenv("DISPLAY_API_TOKEN")
        # include=status añade el estado dinámico (ip_local, etc.) anidado en
        # data.status; sin él la API no lo devuelve.
        full_url = url + '/hardware/devices/' + str(display_id) + '?include=status'

        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + str(display_token),
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

    def get_summary(self, device_id=None, date='today'):
        """
        Obtiene el resumen de estadísticas acumuladas (teclado y ratón) para el
        dispositivo y periodo indicados desde GET /keycounter/summary.
        :param device_id: ID del dispositivo (por defecto toma DEVICE_ID del entorno)
        :param date: Periodo ('today', 'month', 'AAAA-MM-DD', 'AAAA-MM')
        :return: dict con los datos de data, o None si falla / no existe
        """
        url = self.API_URL
        token = self.API_TOKEN

        if not url or not token:
            return None

        dev_id = device_id or os.getenv("DEVICE_ID")
        if not dev_id:
            return None

        full_url = f"{url}/keycounter/summary?device_id={dev_id}&date={date}"

        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + str(token),
        }

        try:
            req = self.requests_retry_session(retries=1).get(
                full_url,
                headers=headers,
                timeout=10
            )

            if self.DEBUG:
                print('Respuesta GET /keycounter/summary:', req.status_code, req.text)

            if req.status_code == 200:
                res = req.json()
                if isinstance(res, dict) and res.get('success'):
                    return res.get('data')

            return None
        except Exception as e:
            if self.DEBUG:
                print('Error al obtener /keycounter/summary de la API:', e)

            return None
