# python-keycounter

Herramienta en python 3 para contar la cantidad de teclas que se ha pulsado en un tiempo determinado o sesión.

## Instalando (En Debian)

### Dependencias

pip install keyboard

sudo apt install python3-serial

## Ejecución

Se necesitan configurar las variables de nuestro entorno copiando el archivo
.env.example a .env y modificando en este nuestros parámetros de configuración
que se encuentran en su interior descritos.

Posteriormente ejecutar **main.py** como root. Puede añadirse a un cron @reboot
para que sea ejecutado en el inicio del sistema y esté siempre funcionando en
el background.

## Unix Socket Server

Se crea un servidor socket unix en **/var/run/keycounter.socket** al que se le 
pueden hacer peticiones para obtener las estadísticas de pulsaciones.

En el archivo para debug ** ./Debug/client_socket.py** se puede encontrar un 
ejemplo del modo para conectar desde otras aplicaciones obteniendo los datos
del momento en el que se hayan pedido.