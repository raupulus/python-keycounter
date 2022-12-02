#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import socket
import sys
from time import sleep
# Create a UDS socket
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = '/var/run/keycounter.socket'
print('Conectando a {}'.format(server_address))
try:
    sock.connect(server_address)
except socket.error as msg:
    print(msg)
    sys.exit(1)

try:

    # sock.listen

    # TOFIX: esperar evento y pintar todo, sin bucles!!

    # Pido cantidad de pulsaciones actual
    #message = b'pulsations_current'
    #print('Enviando {!r}'.format(message))
    # sock.sendall(message)

    # Recibo la cantidad de pulsaciones
    #data = sock.recv(2048)
    #print('Recibido {!r}'.format(data.decode("utf-8")))

    """
    amount_received = 0
    amount_expected = len(message)

    while amount_received < amount_expected:
        #data = sock.recv(16)
        data = sock.recv()
        amount_received += len(data)
        print('received {!r}'.format(data))
    """

    while sock.listen:
        data = sock.recv(2048)
        print('Recibido {!r}'.format(data.decode("utf-8")))


finally:
    print('closing socket')
    sock.close()
