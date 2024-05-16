import os
import time
import serial
import RPi.GPIO as GPIO
from gpiozero import LED, DistanceSensor
import telebot
import adafruit_fingerprint
import threading

API_TOKEN = '6889397382:AAFaH9-seJUD0x1exdYDEuUnb23onnUAMV0'
bot = telebot.TeleBot(API_TOKEN)

# Configuración de los LEDs y el sensor de distancia
led_verde = LED(17)
led_rojo = LED(27)
sensor_distancia = DistanceSensor(echo=18, trigger=23)

# Configuración del sensor de huellas dactilares
uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

# Configuración del GPIO para la cerradura
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)

# Diccionario para mantener el estado del usuario
user_state = {}

# Función para activar la cerradura
def activar_cerradura():
    GPIO.output(17, True)  # Enciende el relevador
    time.sleep(5)          # Mantiene la cerradura abierta por 5 segundos
    GPIO.output(17, False) # Apaga el relevador

# Función para verificar la proximidad
def check_proximity():
    while True:
        distancia = sensor_distancia.distance * 100  # Convertir a centímetros
        if distancia < 20:
            led_rojo.on()
            time.sleep(1)
            led_rojo.off()
        time.sleep(1)

# Iniciar la verificación de proximidad en un hilo separado
threading.Thread(target=check_proximity, daemon=True).start()

# Función para inscribir una huella
def inscribir_huella(chat_id, location=None, step=1):
    if location is not None:
        user_state[chat_id] = {'action': 'inscribir', 'step': step, 'location': location, 'count': 0}
    
    if user_state[chat_id]['step'] in [1, 2]:
        message = "Coloque el dedo en el sensor..." if user_state[chat_id]['step'] == 1 else "Coloque el mismo dedo nuevamente."
        bot.send_message(chat_id, message)
        time.sleep(1)
        check_finger_presence(chat_id)

# Función para verificar la presencia del dedo en el sensor
def check_finger_presence(chat_id):
    try:
        result = finger.get_image()
        if result == adafruit_fingerprint.OK:
            message = "Huella tomada. Retire el dedo." if user_state[chat_id]['step'] == 1 else "Huella tomada nuevamente. Procesando..."
            bot.send_message(chat_id, message)
            process_image(chat_id)
        elif result == adafruit_fingerprint.NOFINGER:
            time.sleep(0.5)
            check_finger_presence(chat_id)
        else:
            bot.send_message(chat_id, "Error de Huella. Intente de nuevo.")
            del user_state[chat_id]
    except Exception as e:
        bot.send_message(chat_id, f"Error de comunicación: {str(e)}")

# Función para procesar la imagen de la huella
def process_image(chat_id):
    try:
        result = finger.image_2_tz(user_state[chat_id]['step'])
        if result == adafruit_fingerprint.OK:
            user_state[chat_id]['count'] += 1
            if user_state[chat_id]['count'] == 1:
                user_state[chat_id]['step'] = 2
                time.sleep(1)
                inscribir_huella(chat_id, step=2)
            else:
                create_model(chat_id)
        else:
            bot.send_message(chat_id, "Error al procesar la huella. Intente de nuevo.")
            del user_state[chat_id]
    except Exception as e:
        bot.send_message(chat_id, f"Error de comunicación: {str(e)}")

# Función para crear el modelo de huella
def create_model(chat_id):
    try:
        result = finger.create_model()
        if result == adafruit_fingerprint.OK:
            store_model(chat_id)
        else:
            bot.send_message(chat_id, "Las huellas no coinciden. Intente de nuevo.")
            del user_state[chat_id]
    except Exception as e:
        bot.send_message(chat_id, f"Error de comunicación: {str(e)}")

# Función para almacenar el modelo de huella
def store_model(chat_id):
    try:
        location = user_state[chat_id]['location']
        result = finger.store_model(location)
        if result == adafruit_fingerprint.OK:
            bot.send_message(chat_id, f"Modelo almacenado en la posición {location}.")
            led_verde.on()
            time.sleep(1)
            led_verde.off()
        else:
            bot.send_message(chat_id, "Error al almacenar el modelo.")
        del user_state[chat_id]
    except Exception as e:
        bot.send_message(chat_id, f"Error de comunicación: {str(e)}")

# Función para obtener una huella
def obtener_huella():
    try:
        print("Esperando imagen...")
        while finger.get_image() != adafruit_fingerprint.OK:
            pass
        print("Creando plantilla...")
        if finger.image_2_tz(1) != adafruit_fingerprint.OK:
            return False, "Error al crear plantilla."
        print("Buscando...")
        result = finger.finger_search()
        if result == adafruit_fingerprint.OK:
            # Si la búsqueda fue exitosa, activar la cerradura
            activar_cerradura()
            return True, f"Huella encontrada con ID {finger.finger_id} y confianza {finger.confidence}."
        else:
            return False, "Huella no encontrada."
    except Exception as e:
        return False, f"Error de comunicación: {str(e)}"

# Función para eliminar una huella
def eliminar_huella(location):
    try:
        if finger.delete_model(location) == adafruit_fingerprint.OK:
            return True
        else:
            return False
    except Exception as e:
        return False

# Función para resetear la librería de huellas
def resetear_libreria():
    try:
        if finger.empty_library() == adafruit_fingerprint.OK:
            return True, "Librería reseteada correctamente."
        else:
            return False, "Error al resetear la librería."
    except Exception as e:
        return False, f"Error de comunicación: {str(e)}"

# Función para mostrar las huellas inscritas
def mostrar_huellas():
    try:
        if finger.read_templates() != adafruit_fingerprint.OK:
            return False, "Error al leer las plantillas."
        return True, f"Huellas inscritas: {finger.templates}"
    except Exception as e:
        return False, f"Error de comunicación: {str(e)}"

# Manejo de comandos del bot y menú interactivo
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    menu = ("Bienvenido al gestor de huellas. Elige una opción:\n"
            "/inscribir - Inscribir nueva huella\n"
            "/buscar - Buscar una huella\n"
            "/eliminar - Eliminar una huella\n"
            "/resetear - Resetear la librería de huellas\n"
            "/mostrar - Mostrar todas las huellas inscritas\n"
            "/salir - Salir del bot")
    bot.reply_to(message, menu)

@bot.message_handler(commands=['inscribir'])
def command_inscribir(message):
    bot.send_message(message.chat.id, "Ingrese el ID de ubicación de 0 a {}:".format(finger.library_size - 1))
    user_state[message.chat.id] = {'action': 'get_location'}

@bot.message_handler(func=lambda message: message.chat.id in user_state and user_state[message.chat.id]['action'] == 'get_location')
def handle_location_input(message):
    try:
        location = int(message.text)
        if location < 0 or location >= finger.library_size:
            raise ValueError("Número fuera de rango")
        inscribir_huella(message.chat.id, location=location)
    except ValueError:
        bot.send_message(message.chat.id, "Por favor, ingrese un número válido.")

@bot.message_handler(commands=['buscar'])
def buscar_huella(message):
    success, response = obtener_huella()
    bot.reply_to(message, response)

@bot.message_handler(commands=['resetear'])
def resetear(message):
    success, response = resetear_libreria()
    bot.reply_to(message, response)

@bot.message_handler(commands=['mostrar'])
def mostrar(message):
    success, response = mostrar_huellas()
    bot.reply_to(message, response)

@bot.message_handler(commands=['salir'])
def salir(message):
    bot.reply_to(message, "Gracias por usar el bot de gestión de huellas. ¡Hasta pronto!")

# Iniciar la escucha de comandos del bot
bot.polling()
