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
        self.DEVICE_NAME = os.getenv("DEVICE_NAME")

        self.prepare_client_thread = start_new_thread(self.prepare_client, ())

    def prepare_client(self) -> None:
        """
        Prepare the client by retrieving and processing the WebSocket server display information from the API.
        Sets the `is_busy` flag during the process to prevent concurrent operations.

        :return: None
        """
        self.is_busy = True

        try_counter = 0

        while True:
            res = self.api.get_websocket_server_display_info()

            if res is not None:
                if self.DEBUG:
                    print('Comenzando a pedir datos a la api para websockets')

                if "device" in res:
                    self.websocket_server_display_info = res["device"]

                    if self.DEBUG:
                        print('IP LOCAL',
                              self.websocket_server_display_info.get(
                                  'ip_local'))
                        print('Datos obtenidos de la api para websockets:', res)

                    break
                else:
                    if self.DEBUG:
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

    def update (self) -> None:
        """
        Handles updating the display information through websockets. This involves:

        - Checking debug flags and logging appropriately.
        - Returning early if the system is busy or does not contain necessary display information.
        - Preparing client data from the API if too many errors occur.
        - Marking the system as busy.
        - Gathering current system datetime, keyboard pulsation data, device information, and creating a data dictionary.
        - Converting data dictionary to a JSON string.
        - Establishing a socket connection to the device IP and port, sending the JSON data, receiving and processing the response.
        - Resetting error count if the response is successful, otherwise incrementing the error count.
        - Logging socket errors in debug mode, if any.
        - Handling cleanup by marking the system as not busy and introducing a pause based on error count.

        :return:
        """
        if self.DEBUG:
            print('Entra en actualizar pantalla por websockets')

        if self.is_busy or self.websocket_server_display_info is None:

            if self.DEBUG:
                print('Ocupado: ', self.is_busy)
                print('websocket_server_display_info: ',
                      self.websocket_server_display_info)

            return

        # Si hay demasiados errores, pido a la api datos del servidor actualizados
        if self.errors > 10:
            self.prepare_client()

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
                'system': {
                    'so': self.DEVICE_NAME,
                }
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

                    # Convierto la respuesta a un diccionario
                    response_dict = json.loads(
                        websocket_response.decode('utf-8'))

                    # Si va bien, reseteamos el contador de errores
                    if response_dict.get('status') == 'ok':
                        self.errors = 0
                    else:
                        if self.DEBUG:
                            print('Errores:', self.errors)

                except socket.error as e:
                    if self.DEBUG:
                        print(f"Socket error: {e}")

                    self.errors += 1
        finally:
            self.is_busy = False

            # Pausa según el número de errores
            if self.errors == 1:
                sleep(10)  # Pausa de 10 segundos
            else:
                sleep(60)  # Pausa de 1 minuto