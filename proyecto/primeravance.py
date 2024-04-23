import time
import board
import busio
from digitalio import DigitalInOut, Direction
import serial
import adafruit_fingerprint
import telebot  # Importa la librería de bot de Telegram

# Configuración del bot de Telegram
TOKEN = '6889397382:AAFaH9-seJUD0x1exdYDEuUnb23onnUAMV0'
bot = telebot.TeleBot(TOKEN)

led = DigitalInOut(board.D13)
led.direction = Direction.OUTPUT

uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

# Definiciones de funciones para manejar las huellas dactilares
def get_fingerprint():
    print("Esperando huella...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True

def enroll_finger(location):
    for attempt in range(1, 3):
        while finger.get_image() != adafruit_fingerprint.OK:
            pass
        if finger.image_2_tz(attempt) != adafruit_fingerprint.OK:
            return False
    if finger.create_model() != adafruit_fingerprint.OK:
        return False
    if finger.store_model(location) != adafruit_fingerprint.OK:
        return False
    return True

def delete_finger(location):
    return finger.delete_model(location) == adafruit_fingerprint.OK

# Comandos del bot de Telegram
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hola! Usa /enroll para registrar, /find para buscar, /delete para eliminar.")

@bot.message_handler(commands=['enroll'])
def enroll_command(message):
    bot.reply_to(message, "Por favor, coloca tu dedo en el sensor.")
    if enroll_finger(1):  # Aquí deberías calcular la ubicación dinámicamente
        bot.reply_to(message, "Huella registrada exitosamente!")
    else:
        bot.reply_to(message, "Falló el registro de la huella.")

@bot.message_handler(commands=['find'])
def find_command(message):
    if get_fingerprint():
        bot.reply_to(message, f"Huella detectada con ID {finger.finger_id} y confianza {finger.confidence}")
    else:
        bot.reply_to(message, "Huella no encontrada.")

@bot.message_handler(commands=['delete'])
def delete_command(message):
    if delete_finger(1):  # Aquí deberías pedir al usuario que especifique qué huella borrar
        bot.reply_to(message, "Huella eliminada.")
    else:
        bot.reply_to(message, "Falló al eliminar la huella.")

# Inicia el bot
bot.polling()
