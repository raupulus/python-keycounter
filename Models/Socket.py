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

#######################################
# #             Clase               # #
#######################################


class Socket:
    # Ruta dónde se creará el Socket.
    server_address = '/var/run/keycounter.socket'

    # Instancia del Socket
    sock = None

    # Almacena la instancia del keylogger para obtener sus datos.
    keylogger = None

    def __init__(self, keylogger):
        self.keylogger = keylogger

        # Limpio sockets anteriores que pueda existir.
        self.delete_old_socket()

        # Creando el socket UNIX.
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Crea el socket en la dirección indicada con "server_address.
        print('Comenzando socket abierto en {}'.format(self.server_address))
        self.sock.bind(self.server_address)

        # Comienza a escuchar conexiones entrantes.
        self.sock.listen(1)

        # Cambio los permisos del socket.
        self.change_permissions_socket()

        # Comienza el bucle esperando conexiones.
        self.ready()

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
        # Otorgo permisos de lectura a todos
        os.chmod('/var/run/keycounter.socket', 755)

    def ready(self):
        """
        Queda en bucle esperando conexiones.
        :return:
        """
        while True:
            # Queda esperando conexiones
            print('Socket Unix Esperando conexiones')
            connection, client_address = self.sock.accept()

            try:
                print('Conexión desde', client_address)
                data = connection.recv(2048)
                print('Enviando Pulsaciones: ' + str(self.keylogger.pulsations_current))
                connection.sendall(bytes(str(self.keylogger.pulsations_current), encoding='utf-8'))

                """
                # Recibe los datos en pequeños trozos para retrasmitirlos.
                while True:
                    data = connection.recv(16)
                    print('Recibido {!r}'.format(data))
                    if data:
                        # Envío los datos de conexión
                        print('Enviando Pulsaciones: ' + str(self.keylogger.pulsations_current))
                        #connection.sendall(bytes(self.keylogger.pulsations_current, encoding='utf-8'))
                        connection.sendall(str(self.keylogger.pulsations_current))

                        #print('Devolviendo los datos al cliente.')
                        #self.keylogger.debug()
                        #connection.sendall(data)
                    else:
                        print('No hay más datos desde:', client_address)
                        break
                """
            finally:
                # Cierra y limpia la conexión.
                connection.close()
