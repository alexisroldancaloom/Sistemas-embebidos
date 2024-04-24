import os
import time
import serial
from gpiozero import LED, DistanceSensor
import telebot
import adafruit_fingerprint

API_TOKEN = '6889397382:AAFaH9-seJUD0x1exdYDEuUnb23onnUAMV0'
bot = telebot.TeleBot(API_TOKEN)

led_verde = LED(17)
led_rojo = LED(27)
sensor_distancia = DistanceSensor(echo=18, trigger=23)  #  GPIO 18 y 23 para echo y trigger

uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

user_state = {}

# Proximidad
def check_proximity():
    while True:
        distancia = sensor_distancia.distance * 100  
        if distancia < 20:  # Distancia en centímetros
            led_rojo.on()
            time.sleep(1)  
            led_rojo.off()
        time.sleep(1)  

import threading
threading.Thread(target=check_proximity, daemon=True).start()

# Huellas

def inscribir_huella(chat_id, location=None, step=1):
    if location is not None:
        user_state[chat_id] = {'action': 'inscribir', 'step': step, 'location': location, 'count': 0}
    
    if user_state[chat_id]['step'] == 1 or user_state[chat_id]['step'] == 2:
        message = "Coloque el dedo en el sensor..." if user_state[chat_id]['step'] == 1 else "Coloque el mismo dedo nuevamente."
        bot.send_message(chat_id, message)
        time.sleep(1)  # Dar tiempo al usuario para colocar el dedo
        check_finger_presence(chat_id)

def check_finger_presence(chat_id):
    result = finger.get_image()
    if result == adafruit_fingerprint.OK:
        message = "Huella tomada. Retire el dedo." if user_state[chat_id]['step'] == 1 else "Huella tomada nuevamente. Procesando..."
        bot.send_message(chat_id, message)
        process_image(chat_id)
    elif result == adafruit_fingerprint.NOFINGER:
        # Poll until finger is placed
        time.sleep(0.5)
        check_finger_presence(chat_id)
    else:
        bot.send_message(chat_id, "Error de Huella. Intente de nuevo.")
        del user_state[chat_id]

def process_image(chat_id):
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
    if result == adafruit_fingerprint.OK:
        # Si la búsqueda fue exitosa, ahora necesitamos acceder a la ID de la huella y la confianza
        return True, f"Huella encontrada con ID {finger.finger_id} y confianza {finger.confidence}."
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
    

bot.polling()
