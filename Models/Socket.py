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
# Project Name: Python Socket
# Description: Este script abre un socket para atender peticiones de estadísticas a otros
# programas
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

#
# Fuente de información: https://pymotw.com/3/socket/uds.html
#

#######################################
# #           Descripción           # #
#######################################
##
# # Este script abre un socket para atender peticiones de estadísticas a otros
# # programas.
##

#######################################
# #       Importar Librerías        # #
#######################################

import socket
import os
# import sys
from _thread import start_new_thread
from time import sleep

#######################################
# #             Clase               # #
#######################################


class Socket:
    has_debug = False

    # Ruta dónde se creará el Socket.
    server_address = '/var/run/keycounter.socket'

    # Instancia del Socket
    sock = None

    # Almacena la instancia del keylogger para obtener sus datos.
    keylogger = None

    # Conexión
    connection = None

    # Cliente
    client_address = None

    # Indica si está en espera de una conexión.
    wait_client_connection = False

    def __init__(self, keylogger, has_debug=False):
        self.keylogger = keylogger
        self.has_debug = has_debug

        # Limpio sockets anteriores que pueda existir.
        self.delete_old_socket()

        # Creando el socket UNIX.
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Crea el socket en la dirección indicada con "server_address.
        if self.has_debug:
            print('Comenzando socket abierto en {}'.format(self.server_address))

        self.sock.bind(self.server_address)

        # Comienza a escuchar conexiones entrantes.
        self.sock.listen(99)

        # Cambio los permisos del socket.
        self.change_permissions_socket()

        # Comienza el bucle esperando conexiones.
        start_new_thread(self.wait_client, ())

    def delete_old_socket(self):
        """
        Comprueba de que no exista ya el socket e intenta eliminarlo.
        :return:
        """
        try:
            os.unlink(self.server_address)
        except OSError:
            if os.path.exists(self.server_address):
                raise

    def change_permissions_socket(self):
        """
        Otorga permisos de lectura a otros usuarios.
        :return:
        """
        # Otorgo permisos de lectura a todos (Escribir no es necesario, pero por ahora se establece).
        os.chmod(self.server_address, 0o666)

    def ready(self):
        """
            Queda en bucle esperando conexiones.
            :return:
            """
        while True:

            try:

                """
                # Recibe los datos en pequeños trozos para retrasmitirlos.
                while True:
                    data = connection.recv(16)
                    print('Recibido {!r}'.format(data))
                    if data:
                        # Envío los datos de conexión
                        print('Enviando Pulsaciones: ' + \
                            str(self.keylogger.pulsations_current))
                        # connection.sendall(bytes(self.keylogger.pulsations_current, encoding='utf-8'))
                        connection.sendall(str(self.keylogger.pulsations_current))

                        # print('Devolviendo los datos al cliente.')
                        # self.keylogger.debug()
                        # connection.sendall(data)
                    else:
                        print('No hay más datos desde:', client_address)
                        break
                """
            except Exception as e:
                print('Error en la conexión: ' + str(e))

                # Cierra y limpia la conexión.
                self.connection.close()
            finally:
                sleep(1)

    def wait_client(self):
        """
        Espera a que se conecte un cliente.
        :return:
        """

        # Queda esperando conexiones
        if self.has_debug:
            print('Socket Unix Esperando conexiones')

        # DELETE: TMP DEBUG
        print('Entra en wait_client, esperando conexiones. (wait_client_connection: ' +
              str(self.wait_client_connection) + ')')

        if self.wait_client_connection is False and (self.connection is None or self.client_address is None):

            self.wait_client_connection = True
            print('COMPROBACION 1, wait_client_connection: ' +
                  str(self.wait_client_connection))

            self.connection, self.client_address = self.sock.accept()
            self.wait_client_connection = False

            """
            try:
                pass
            except Exception as e:
                print('Error en la conexión: ' + str(e))

                self.connection = None
                self.client_address = None
            finally:
                self.wait_client_connection = False
            """

            print('COMPROBACION 3', self.wait_client_connection,
                  self.connection, self.client_address)

        # DELETE: TMP DEBUG
        print('Conexión desde', self.client_address)

        if self.has_debug:
            print('Conexión desde', self.client_address)

    def update(self):
        """
        Actualiza el socket.
        :return:
        """

        print('Entra en actualizar Socket')

        if self.wait_client_connection is False and (self.connection is None or self.client_address is None):
            print('Se va a realizar llamada para esperar cliente')
            print('COMPROBACION 2:', self.wait_client_connection,
                  self.connection, self.client_address)

            start_new_thread(self.wait_client, ())

            return

        if self.connection is not None and self.client_address is not None:
            print('HAY CLIENTE')
            try:
                #data = self.connection.recv(2048)

                if self.has_debug:
                    print('Enviando Pulsaciones: ' +
                          str(self.keylogger.model_keyboard.pulsations_current))

                print('Enviando Pulsaciones: ' +
                      str(self.keylogger.model_keyboard.pulsations_current))

                self.connection.sendall(
                    bytes(str(self.keylogger.model_keyboard.pulsations_current), encoding='utf-8'))
            except Exception as e:
                print('Error en la conexión, excepción: ' + str(e))
                self.connection = None
                self.client_address = None
        else:
            print('NO HAY CLIENTE')
