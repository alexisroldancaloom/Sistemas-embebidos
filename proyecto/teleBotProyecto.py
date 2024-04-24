from config import *
import telebot
from gpiozero import LED
from time import sleep
from telebot import types
import os
import time
import serial
from signal import pause
import adafruit_fingerprint
import pickle
import threading
from gpiozero import DistanceSensor


led_verde = LED(17)
led_rojo = LED(27)
sensor = DistanceSensor(echo=13, trigger=19)
turnOnSensor = False

chat_id = None

uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)

user_data = []
huellas_borradas = []

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

class PersonasHuellas:
	def __init__(self, nombre, IDHuella):
		self.nombre = nombre
		self.IDHuella = IDHuella

def eliminar_huella():
     if finger.delete_model(id) == adafruit_fingerprint.OK:
            print("¡Eliminada!")

def cargar_personas():
    try:
        with open("personas_huellas.pkl", "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return []

# Guardar la lista de personas con sus huellas en un archivo
def guardar_personas():
    with open("personas_huellas.pkl", "wb") as file:
        pickle.dump(user_data, file)

# Obtener el valor de location (ID disponible más bajo)
def obtener_location():
    if not user_data:
        return 1
    else:
         if(persona.IDHuella for persona in user_data) + 1 <= (finger.library_size):
              return max(persona.IDHuella for persona in user_data) + 1
         else:
             bot.send_message(chat_id, "no hay espacio para mas huellas")
             

lista_prueba = [PersonasHuellas("Issac", "1"), PersonasHuellas("Issac", "2"), PersonasHuellas("Ale", "1")]
lista_en_string = '\n'.join([f"Nombre: {item.nombre}, ID de Huella: {item.IDHuella}" for item in lista_prueba])
bot = telebot.TeleBot(TELEGRAM_TOKEN)
nombre = ""
texto = ""

@bot.message_handler(commands=["Start", "start", "START"])
def Get_Chat_ID(message):
     chat_id = message.chat.id
     bot.reply_to(message, "Servicio inicializado correctamente")
      
@bot.message_handler(commands=["comandos", "Comandos", "COMANDOS"])
def CMD_Comandos(message):
	bot.reply_to(message, "Los comandos implementados actualmente son: \ncerrar_puerta\nabrir_puerta\neliminar_huella\nlistar_huellas")

@bot.message_handler(commands=["eliminar_huella", "Eliminar_huella", "ELIMINAR_HUELLA", "Eliminar_Huella"])
def CMD_Eliminacion_Usuario(message):
	markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
	markup.add(types.KeyboardButton('Siguiente'))
	bot.reply_to(message, text=f"Aqui esta la lista de huellas disponibles: \n{lista_en_string}", reply_markup=markup)
	user_data[message.chat.id] = 1

@bot.message_handler(commands=["abrir_puerta", "Abrir_puerta", "Abrir_Puerta", "ABRIR_PUERTA"])
def CMD_Abrir_Puerta(message):
	#usr_text = message.text
	bot.reply_to(message, "entendido!")
	#print(usr_text)

@bot.message_handler(commands=["cerrar_puerta", "Cerrar_puerta", "Cerrar_Puerta", "CERRAR_PUERTA"])
def CMD_Abrir_Puerta(message):
        #usr_text = message.text
        bot.reply_to(message, "puertas cerradas!")
        #print(usr_text)

@bot.message_handler(commands=["listar_huellas"])
def CMD_Listar_Huellas(message):
	bot.reply_to(message, text=f"{lista_en_string}")

@bot.message_handler(func=lambda message: True)
def Manejo_Eliminacion_Usuario(message):
	global lista_prueba, nombre, lista_en_string
	chat_id = message.chat.id
	usr_text = message.text
	#IDHuella = ""
	if chat_id in user_data:
		step = user_data[chat_id]
		if step == 1:
			bot.send_message(chat_id, "Dime el nombre del propietario que deseas eliminar.")
			user_data[chat_id] = 2
		elif step == 2:
			nombre = usr_text
			print(nombre)
			bot.send_message(chat_id, "Dime que numero de huella desesas eliminar. Escribe (.) para eliminar todos")
			user_data[chat_id] = 3
		elif step == 3:
			#bot.send_message(chat_id, "Entrando al step 3")
			texto = usr_text
			list_len = len(user_data)
			for item in user_data[:]:
				print("Item: ", item.nombre)
				print("ID: ", item.IDHuella)
				if item.nombre == nombre:
					print("Entrando al ciclo if de nombre con texto: ", texto)
					if item.IDHuella == texto:
						huellas_borradas.append(item)
						user_data.remove(item)
						bot.send_message(chat_id, f"Se elimino huella No. {texto} de: {nombre}")
						lista_en_string = '\n'.join([f"Nombre: {item.nombre}, ID de Huella: {item.IDHuella}" for item in lista_prueba])
					elif texto == ".":
						print("Entrando a elif")
						huellas_borradas.append(item)
						user_data.remove(item)
						bot.send_message(chat_id, f"Se elimino huella No. {item.IDHuella} de: {nombre}")
						lista_en_string = '\n'.join([f"Nombre: {item.nombre}, ID de Huella: {item.IDHuella}" for item in lista_prueba])

			guardar_personas()
			for item in huellas_borradas:
				eliminar_huella(item.IDHuella)
			#bot.send_message(chat_id, f"Se eliminaron huellas de: {nombre}")
			#lista_en_string = '\n'.join([f"Nombre: {item.nombre}, ID de Huella: {item.IDHuella}" for item in lista_prueba])
			user_data.pop(chat_id)


@bot.message_handler(commands=["registra_huella"])
def CMD_Registrar_Huella(message):
    global personas_huellas

    # Cargar la lista de personas con sus huellas desde el archivo
    personas_huellas = cargar_personas()

    # Obtener el valor de location (ID disponible más bajo)
    location = obtener_location()

    # Solicitar el nombre del dueño de la huella
    bot.send_message(message.chat.id, "Por favor, ingrese su nombre:")
    nombre = message.text

    for fingerimg in range(1, 3):
        if fingerimg == 1:
            bot.send_message(message.chat.id, "Coloque el dedo en el sensor...")
        else:
            bot.send_message(message.chat.id, "Coloque el mismo dedo nuevamente...")

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                bot.send_message(message.chat.id, "Huella tomada")
                break
            if i == adafruit_fingerprint.NOFINGER:
                time.sleep(1)
            elif i == adafruit_fingerprint.IMAGEFAIL:
                bot.send_message(message.chat.id, "Error de Huella")
                return False
            else:
                bot.send_message(message.chat.id, "Otro error")
                return False

        bot.send_message(message.chat.id, "Templateando...")
        i = finger.image_2_tz(fingerimg)
        if i != adafruit_fingerprint.OK:
            if i == adafruit_fingerprint.IMAGEMESS:
                bot.send_message(message.chat.id, "Huella demasiado desordenada")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                bot.send_message(message.chat.id, "No se pudieron identificar las características")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                bot.send_message(message.chat.id, "Huella inválida")
            else:
                bot.send_message(message.chat.id, "Otro error")
            return False

        if fingerimg == 1:
            bot.send_message(message.chat.id, "Retire el dedo")
            time.sleep(1)
            while finger.get_image() != adafruit_fingerprint.NOFINGER:
                time.sleep(0.1)

    bot.send_message(message.chat.id, "Creando modelo...")
    i = finger.create_model()
    if i != adafruit_fingerprint.OK:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            bot.send_message(message.chat.id, "Las huellas no coinciden")
        else:
            bot.send_message(message.chat.id, "Otro error")
        return False

    # Crear una instancia de PersonasHuellas y agregarla a la lista
    persona_huella = PersonasHuellas(nombre, location)
    personas_huellas.append(persona_huella)

    # Guardar la lista de personas con sus huellas en el archivo
    guardar_personas()

    bot.send_message(message.chat.id, "Almacenando modelo #%d..." % location)
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        bot.send_message(message.chat.id, "Almacenado")
        # Aquí puedes agregar código para guardar la huella en el archivo
    else:
        bot.send_message(message.chat.id, "Error al almacenar el modelo")
        return False

    return True


def detectar_huella(chat_id):
    print("Esperando imagen...")
    while True:
        if finger.get_image() == adafruit_fingerprint.OK:
            print("Creando plantilla...")
            if finger.image_2_tz(1) == adafruit_fingerprint.OK:
                print("Buscando...")
                if finger.finger_search() == adafruit_fingerprint.OK:
                    print("Huella detectada #", finger.finger_id, "con confianza", finger.confidence)
                    bot.send_message(chat_id, "¡Huella detectada! ID: {} Confianza: {}".format(finger.finger_id, finger.confidence))
                    time.sleep(5)  # Esperar 5 segundos antes de buscar otra huella
                else:
                    print("Huella no encontrada")
            else:
                print("Error al crear plantilla")
        else:
            print("Error al obtener imagen")

@bot.message_handler(commands=["SensorON"])
def turn_sensor_on(message):
	global turnOnSensor
	turnOnSensor = True
	bot.reply_to(message, "Sensor encendido")
	while turnOnSensor:
		d = sensor.distance*100
		print(d)
		if(d < 20):
			bot.reply_to(message, "Alerta de proximidad en el sensor!!!")
		sleep(2)

@bot.message_handler(commands=["SensorOFF"])
def turn_sensor_off(message):
	global turnOnSensor
	turnOnSensor = False
	bot.reply_to(message, "Sensor apagado")

if __name__ == '__main__':
	print("Activando a Cecil")
	bot.infinity_polling()
    
	thread_huellas = threading.Thread(target=detectar_huella, args=(chat_id,))
	thread_huellas.start()
