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
