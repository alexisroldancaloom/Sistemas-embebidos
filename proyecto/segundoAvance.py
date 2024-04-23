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

# Función para manejar el estado y el proceso de inscripción
def inscribir_huella(chat_id, location=None, step=None):
    if step is None:
        user_state[chat_id] = {'action': 'inscribir', 'step': 1, 'location': location}
        bot.send_message(chat_id, "Coloque el dedo en el sensor...")
    else:
        if step == 1:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                bot.send_message(chat_id, "Huella tomada. Retire el dedo.")
                user_state[chat_id]['step'] = 2
                time.sleep(1)  # Pause for user to remove finger
                inscribir_huella(chat_id, step=2)
            elif i == adafruit_fingerprint.NOFINGER:
                bot.send_message(chat_id, ".", parse_mode='Markdown')
            elif i == adafruit_fingerprint.IMAGEFAIL:
                bot.send_message(chat_id, "Error de Huella. Intente de nuevo.")
                del user_state[chat_id]
                led_rojo.on()
                time.sleep(2)
                led_rojo.off()
            else:
                bot.send_message(chat_id, "Error desconocido. Intente de nuevo.")
                del user_state[chat_id]

        elif step == 2:
            i = finger.image_2_tz(1)
            if i == adafruit_fingerprint.OK:
                if 'count' in user_state[chat_id]:
                    user_state[chat_id]['count'] += 1
                else:
                    user_state[chat_id]['count'] = 1

                if user_state[chat_id]['count'] < 2:
                    bot.send_message(chat_id, "Coloque el mismo dedo nuevamente.")
                    user_state[chat_id]['step'] = 1
                else:
                    bot.send_message(chat_id, "Creando modelo...")
                    i = finger.create_model()
                    if i == adafruit_fingerprint.OK:
                        i = finger.store_model(location)
                        if i == adafruit_fingerprint.OK:
                            bot.send_message(chat_id, f"Modelo almacenado en la posición {location}.")
                        else:
                            bot.send_message(chat_id, "Error al almacenar el modelo.")
                        del user_state[chat_id]
                        led_verde.off()
                    else:
                        bot.send_message(chat_id, "Las huellas no coinciden. Intente de nuevo.")
                        del user_state[chat_id]
            else:
                bot.send_message(chat_id, "Error al procesar la huella. Intente de nuevo.")
                del user_state[chat_id]

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

@bot.message_handler(func=lambda message: message.chat.id in user_state and user_state[message.chat.id].get('action') == 'get_location')
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
