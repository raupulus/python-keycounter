import json
from _thread import start_new_thread
from time import sleep, time
import os
from datetime import datetime
import socket

class ClientDisplayWebsocket:
    """
    Representa la conexión con una pantalla externa dónde esta aplicación
    se conecta como cliente websocket para enviar datos estadísticos.
    """

    is_busy = False
    websocket_server_display_info = None
    errors = 0

    def __init__(self, keylogger, api, debug=False):

        self.DEBUG = debug
        self.keylogger = keylogger
        self.api = api
        self.DEVICE_ID = os.getenv("DEVICE_ID")

        self.prepare_client_thread = start_new_thread(self.prepare_client, ())

    def prepare_client(self):
        self.is_busy = True

        try_counter = 0

        while True:
            res = self.api.get_websocket_server_display_info()

            if res is not None:
                if self.DEBUG:
                    print('Comenzando a pedir datos a la api para websockets')

                if "device" in res:
                    self.websocket_server_display_info = res["device"]

                    print('IP LOCAL', self.websocket_server_display_info.get('ip_local'))

                    if self.DEBUG:
                        print('Datos obtenidos de la api para websockets:', res)

                    break
                else:
                    print("La clave 'device' no está presente en la respuesta.")

                if self.DEBUG:
                    print('Datos obtenidos de la api para websockets:', res)

                break
            else:
                try_counter += 1

                if 3 <= try_counter <= 6:
                    sleep(30)
                if try_counter >= 6:
                    sleep(60)
                else:
                    sleep(10)

        sleep(10)
        self.is_busy = False

    def update (self):
        if self.DEBUG:
            print('Entra en actualizar pantalla por websockets')

        if self.is_busy or self.websocket_server_display_info is None:

            if self.DEBUG:
                print('Ocupado: ', self.is_busy)
                print('websocket_server_display_info: ',
                      self.websocket_server_display_info)

            return

        # TODO: Si hay demasiados errores, volver a ejecutar
        #  self.prepare_client() para actualizar datos de dónde está la pantalla

        self.is_busy = True

        try:
            # Obtener la fecha y hora actuales del sistema
            current_datetime = datetime.now()

            # Convierto a cadena la fecha y hora
            str_timestamp = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            str_time = current_datetime.strftime("%H:%M:%S")

            data = {
                'device_id': self.DEVICE_ID,
                'session': {
                    'pulsations_total': int(
                        self.keylogger.model_keyboard.pulsations_total),
                },
                'streak': {
                    'pulsations_current': int(
                        self.keylogger.model_keyboard.pulsations_current),
                    'pulsation_average': int(
                        self.keylogger.model_keyboard.get_pulsation_average()),
                },
                'timestamp': str_timestamp,
                'time': str_time,
                'SO': 'N/D (SETEAR VAR)',
            }

            data_json_string = json.dumps(data, skipkeys=False,
                                          ensure_ascii=True,
                                          check_circular=True,
                                          allow_nan=True, cls=None, indent=None,
                                          separators=None,
                                          default=None)

            device_ip = self.websocket_server_display_info.get('ip_local')
            device_port = 80

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect((device_ip, device_port))
                    s.send(data_json_string.encode('utf-8'))

                    websocket_response = s.recv(1024)

                    if self.DEBUG:
                        print('websocket_response', websocket_response)

                    # Si todo va bien, reseteamos el contador de errores
                    self.errors = 0

                except socket.error as e:
                    if self.DEBUG:
                        print(f"Socket error: {e}")
                    self.errors += 1  # Incrementar el contador de errores
        finally:
            self.is_busy = False

            # Pausa según el número de errores
            if self.errors < 10:
                sleep(10)  # Pausa de 10 segundos
            else:
                sleep(60)  # Pausa de 1 minuto