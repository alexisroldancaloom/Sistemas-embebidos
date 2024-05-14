import RPi.GPIO as GPIO
import time

# Configura el modo del pin
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)

# Función para activar la cerradura
def activar_cerradura():
    GPIO.output(17, True)  # Enciende el relevador
    time.sleep(2)          # Mantiene la cerradura abierta por 5 segundos
    GPIO.output(17, False) # Apaga el relevador
    time.sleep(2)          # Espera 5 segundos

try:
    while True:
        activar_cerradura()
except KeyboardInterrupt:
    GPIO.cleanup()  # Limpia los ajustes de GPIO al salir
