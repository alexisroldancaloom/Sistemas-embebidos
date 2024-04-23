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

# Funciones de manejo de huella

def obtener_huella():
    print("Esperando imagen...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Creando plantilla...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    print("Buscando...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True

def inscribir_huella(location):
    for fingerimg in range(1, 3):
        print("Coloque el dedo en el sensor...")
        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Huella tomada")
                led_verde.on()
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="")
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Error de Huella")
                led_rojo.on()
                time.sleep(2)
                led_rojo.off()
                return False
            else:
                print("Otro error")
                return False

        print("Templateando...")
        i = finger.image_2_tz(fingerimg)
        if i != adafruit_fingerprint.OK:
            print("Error en creación de template")
            return False

        if fingerimg == 1:
            print("Retire el dedo")
            time.sleep(1)
            while finger.get_image() == adafruit_fingerprint.OK:
                pass

    print("Creando modelo...")
    if finger.create_model() != adafruit_fingerprint.OK:
        print("Las huellas no coinciden")
        return False

    print(f"Almacenando modelo #{location}...")
    if finger.store_model(location) != adafruit_fingerprint.OK:
        print("Error de almacenamiento")
        return False

    led_verde.off()
    return True

def eliminar_huella(location):
    if finger.delete_model(location) == adafruit_fingerprint.OK:
        return True
    else:
        return False

# Comandos del bot

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Bienvenido al bot de gestión de huellas. Use los comandos para interactuar.")

@bot.message_handler(commands=['inscribir', 'eliminar'])
def start_process(message):
    action = message.text.strip('/')
    user_state[message.chat.id] = {'action': action}
    bot.send_message(message.chat.id, "Ingrese el ID de ubicación de 0 a {}:".format(finger.library_size - 1))

@bot.message_handler(func=lambda message: message.chat.id in user_state)
def handle_number_input(message):
    chat_id = message.chat.id
    action = user_state[chat_id]['action']
    try:
        location = int(message.text)
        if location < 0 or location >= finger.library_size:
            raise ValueError("Número fuera de rango")
        if action == 'inscribir':
            if inscribir_huella(location):
                bot.send_message(chat_id, f"Huella inscrita en la ubicación {location}")
            else:
                bot.send_message(chat_id, "Falló al inscribir huella.")
        elif action == 'eliminar':
            if eliminar_huella(location):
                bot.send_message(chat_id, f"Huella eliminada de la ubicación {location}")
            else:
                bot.send_message(chat_id, "Falló al eliminar huella.")
    except ValueError:
        bot.send_message(chat_id, "Por favor, ingrese un número válido.")
    finally:
        del user_state[chat_id]

bot.polling()
