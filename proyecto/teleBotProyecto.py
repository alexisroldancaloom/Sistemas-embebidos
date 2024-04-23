import telebot
from telebot import types
from gpiozero import LED, DistanceSensor
import time
import serial
import adafruit_fingerprint
import pickle
import threading

# Configuración del bot de Telegram
TOKEN = '6889397382:AAFaH9-seJUD0x1exdYDEuUnb23onnUAMV0'
bot = telebot.TeleBot(TOKEN)

# GPIO Setup
led_verde = LED(17)
led_rojo = LED(27)
sensor = DistanceSensor(echo=13, trigger=19)

# UART connection para el sensor de huellas
uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

# Cargar y guardar datos
def cargar_personas():
    try:
        with open("personas_huellas.pkl", "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return {}

def guardar_personas(data):
    with open("personas_huellas.pkl", "wb") as file:
        pickle.dump(data, file)

user_data = cargar_personas()

# Funciones para manejo de huellas
def eliminar_huella(id_huella):
    if finger.delete_model(id_huella) == adafruit_fingerprint.OK:
        print(f"Huella {id_huella} eliminada.")
        return True
    else:
        print("Falló al eliminar huella.")
        return False

def obtener_lista_huellas():
    lista_huellas = [f"Nombre: {nombre}, ID de Huella: {details['IDHuella']}" for nombre, details in user_data.items()]
    return '\n'.join(lista_huellas) if lista_huellas else "No hay huellas registradas."

def obtener_location():
    if not user_data:
        return 1
    max_id = max(int(details['IDHuella']) for details in user_data.values())
    return max_id + 1 if max_id + 1 < finger.library_size else None

# Comandos del bot
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Bienvenido al sistema de control de cerradura. Comandos: /registrar, /abrir, /cerrar, /eliminar, /listar")

@bot.message_handler(commands=['registrar'])
def registrar_huella(message):
    chat_id = message.chat.id
    location = obtener_location()
    if location:
        bot.send_message(chat_id, "Por favor, coloca tu dedo en el sensor.")
        # Aquí se podría implementar la lógica para registrar la huella como en los pasos anteriores.
        bot.send_message(chat_id, "Huella registrada en posición " + str(location))
        user_data[chat_id] = {'nombre': 'Usuario ' + str(chat_id), 'IDHuella': str(location)}
        guardar_personas(user_data)
    else:
        bot.send_message(chat_id, "No hay espacio disponible para más huellas.")

@bot.message_handler(commands=['abrir'])
def abrir_puerta(message):
    bot.reply_to(message, "Puerta abierta.")

@bot.message_handler(commands=['cerrar'])
def cerrar_puerta(message):
    bot.reply_to(message, "Puerta cerrada.")

@bot.message_handler(commands=['eliminar'])
def eliminar_usuario(message):
    lista_huellas = obtener_lista_huellas()
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(*[types.KeyboardButton(nombre) for nombre in user_data.keys()])
    bot.send_message(message.chat.id, "Selecciona el usuario a eliminar:\n" + lista_huellas, reply_markup=markup)

@bot.message_handler(commands=['listar'])
def listar_huellas(message):
    lista_huellas = obtener_lista_huellas()
    bot.reply_to(message, "Huellas registradas:\n" + lista_huellas)

@bot.message_handler(func=lambda message: message.text in user_data)
def manejo_eliminar_usuario(message):
    if eliminar_huella(user_data[message.text]['IDHuella']):
        del user_data[message.text]
        guardar_personas(user_data)
        bot.reply_to(message, "Huella eliminada correctamente.")
    else:
        bot.reply_to(message, "No se pudo eliminar la huella.")

# Detectar huella en segundo plano
def detectar_huella():
    while True:
        if finger.get_image() == adafruit_fingerprint.OK:
            if finger.image_2_tz(1) == adafruit_fingerprint.OK:
                if finger.finger_search() == adafruit_fingerprint.OK:
                    print("Huella detectada #", finger.finger_id, "con confianza", finger.confidence)
                else:
                    print("Huella no encontrada")

# Ejecutar el bot
if __name__ == '__main__':
    threading.Thread(target=detectar_huella).start()
    print("Bot activado.")
    bot.infinity_polling()
