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
import json
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

    # Máximo de clientes conectados.
    max_clients = 99

    # Indica si está en espera de una conexión.
    wait_client_connection = False

    """
    Listado de clientes conectados. Esto es una tupla llena de diccionarios.
    connection, representa la conexión con el cliente, address, la dirección del cliente.
    Ejemplo:
    [
        {
            connection: <socket.socket fd=5, family=AddressFamily.AF_UNIX, type=SocketKind.SOCK_STREAM, proto=0, laddr=/var/run/keycounter.socket>,
            client_address:
        }
    ]
    """
    clients_list = []

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
        self.sock.listen(self.max_clients)

        # Cambio los permisos del socket.
        self.change_permissions_socket()

        # Comienza el bucle esperando conexiones.
        start_new_thread(self.startWaitClients, ())

    def startWaitClients(self):
        """
        Comienza el bucle de espera de clientes.
        :return:
        """

        while True:
            if len(self.clients_list) < self.max_clients:
                self.wait_client()
            else:
                sleep(10)

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

    def wait_client(self):
        """
        Espera a que se conecte un cliente.
        :return:
        """

        # Queda esperando conexiones
        if self.has_debug:
            print('Socket Unix Esperando conexiones')

        self.wait_client_connection = True

        try:
            # Espera a que se conecte un cliente, se pausa la ejecución hasta recibir un cliente.
            connection, client_address = self.sock.accept()

            self.clients_list.append({
                'connection': connection,
                'client_address': client_address
            })
        except Exception as e:
            if self.has_debug:
                print('Error al esperar cliente: ' + str(e))
        finally:
            self.wait_client_connection = False

        if self.has_debug:
            print('Conexión desde', client_address)

    def update(self):
        """
        Actualiza el socket.
        :return:
        """

        if self.has_debug:
            print('Entra en actualizar Socket, lista de clientes', self.clients_list)

        for client in self.clients_list:

            connection = client.get('connection')
            client_address = client.get('client_address')

            if connection is not None and client_address is not None:
                data = {
                    'session': {
                        'pulsations_total': int(self.keylogger.model_keyboard.pulsations_total),
                    },
                    'streak': {
                        'pulsations_current': int(self.keylogger.model_keyboard.pulsations_current),
                        'pulsation_average': int(self.keylogger.model_keyboard.get_pulsation_average()),
                    }
                }

                dataJsonString = json.dumps(data, skipkeys=False,
                                            ensure_ascii=True, check_circular=True,
                                            allow_nan=True, cls=None, indent=None, separators=None,
                                            default=None)

                try:

                    if self.has_debug:
                        print('Enviando Pulsaciones: ' +
                              str(self.keylogger.model_keyboard.pulsations_current))

                    # print('Enviando Pulsaciones: ' +
                    #      str(self.keylogger.model_keyboard.pulsations_current))

                    # Envía los datos al cliente.
                    connection.sendall(
                        bytes(dataJsonString, encoding='utf-8'))

                except Exception as e:
                    if self.has_debug:
                        print('ERROR, SE ELIMINA CLIENTE DE LA LISTA')
                        print('Error en la conexión, excepción: ' + str(e))

                    self.clients_list.remove(client)
            else:
                self.clients_list.remove(client)

                if self.has_debug:
                    print('CLIENTE NO VÁLIDO, SE ELIMINA DE LA LISTA')
                    print('Eliminando cliente de la lista', self.clients_list)
