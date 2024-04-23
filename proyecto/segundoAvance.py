import os
import time
import serial
from gpiozero import LED
import telebot
import adafruit_fingerprint

API_TOKEN = '6889397382:AAFaH9-seJUD0x1exdYDEuUnb23onnUAMV0'
bot = telebot.TeleBot(API_TOKEN)

led_verde = LED(17)
led_rojo = LED(27)

uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

user_state = {}

def inscribir_huella(chat_id, location=None, step=1):
    if location is not None:
        user_state[chat_id] = {'action': 'inscribir', 'step': step, 'location': location, 'count': 0}

    if user_state[chat_id]['step'] == 1:
        bot.send_message(chat_id, "Coloque el dedo en el sensor...")
        time.sleep(1)  # Give time for the user to place the finger
        check_finger_presence(chat_id)

def check_finger_presence(chat_id):
    result = finger.get_image()
    if result == adafruit_fingerprint.OK:
        bot.send_message(chat_id, "Huella tomada. Retire el dedo.")
        process_image(chat_id)
    elif result == adafruit_fingerprint.NOFINGER:
        # Poll until finger is placed
        time.sleep(0.5)
        check_finger_presence(chat_id)
    else:
        bot.send_message(chat_id, "Error de Huella. Intente de nuevo.")
        del user_state[chat_id]

def process_image(chat_id):
    result = finger.image_2_tz(1 + user_state[chat_id]['count'])
    if result == adafruit_fingerprint.OK:
        user_state[chat_id]['count'] += 1
        if user_state[chat_id]['count'] == 1:
            user_state[chat_id]['step'] = 2
            bot.send_message(chat_id, "Coloque el mismo dedo nuevamente.")
            time.sleep(1)
            inscribir_huella(chat_id)
        else:
            create_model(chat_id)
    else:
        bot.send_message(chat_id, "Error al procesar la huella. Intente de nuevo.")
        del user_state[chat_id]

def create_model(chat_id):
    result = finger.create_model()
    if result == adafruit_fingerprint.OK:
        store_model(chat_id)
    else:
        bot.send_message(chat_id, "Las huellas no coinciden. Intente de nuevo.")
        del user_state[chat_id]

def store_model(chat_id):
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

# Funciones de manejo de huellas

def obtener_huella():
    print("Esperando imagen...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Creando plantilla...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False, "Error al crear plantilla."
    print("Buscando...")
    result = finger.finger_search()
    if result[0] == adafruit_fingerprint.OK:
        return True, f"Huella encontrada con ID {result[1]} y confianza {result[2]}."
    else:
        return False, "Huella no encontrada."

def eliminar_huella(location):
    if finger.delete_model(location) == adafruit_fingerprint.OK:
        return True
    else:
        return False

def resetear_libreria():
    if finger.empty_library() == adafruit_fingerprint.OK:
        return True, "Librería reseteada correctamente."
    else:
        return False, "Error al resetear la librería."

def mostrar_huellas():
    if finger.read_templates() != adafruit_fingerprint.OK:
        return False, "Error al leer las plantillas."
    return True, f"Huellas inscritas: {finger.templates}"

# Comandos del bot y menú interactivo

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
    # Aquí podrías implementar lógica para cerrar la sesión o limpiar recursos si es necesario.

# Lógica similar para los otros comandos

bot.polling()
