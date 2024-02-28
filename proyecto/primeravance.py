import os
import time
import serial
from gpiozero import LED
from bluedot import BlueDot
from signal import pause
import adafruit_fingerprint

led_verde = LED(17)
led_rojo = LED(27)

uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

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

def obtener_detalle_huella():
    print("Obteniendo Huella...", end="")
    i = finger.get_image()
    if i == adafruit_fingerprint.OK:
        print("Huella tomada")
    else:
        if i == adafruit_fingerprint.NOFINGER:
            print("No se detectó la Huella")
        elif i == adafruit_fingerprint.IMAGEFAIL:
            print("Error de Huella")
        else:
            print("Otro error")
        return False

    print("Templateando...", end="")
    i = finger.image_2_tz(1)
    if i == adafruit_fingerprint.OK:
        print("Template creado")
    else:
        if i == adafruit_fingerprint.IMAGEMESS:
            print("Huella muy desordenada")
        elif i == adafruit_fingerprint.FEATUREFAIL:
            print("No se pudieron identificar las características")
        elif i == adafruit_fingerprint.INVALIDIMAGE:
            print("Huella inválida")
        else:
            print("Otro error")
        return False

    print("Buscando...", end="")
    i = finger.finger_fast_search()
    if i == adafruit_fingerprint.OK:
        print("¡Huella encontrada!")
        return True
    else:
        if i == adafruit_fingerprint.NOTFOUND:
            print("No se encontró coincidencia")
        else:
            print("Otro error")
        return False

def inscribir_huella(location):
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Coloque el dedo en el sensor...", end="")
        else:
            print("Coloque el mismo dedo nuevamente...", end="")

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

        print("Templateando...", end="")
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print("Template creado")
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                print("Huella demasiado desordenada")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                print("No se pudieron identificar las características")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                print("Huella inválida")
            else:
                print("Otro error")
            return False

        if fingerimg == 1:
            print("Retire el dedo")
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creando modelo...", end="")
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Creado")
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            print("Las huellas no coinciden")
        else:
            print("Otro error")
        return False

    print("Almacenando modelo #%d..." % location, end="")
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        print("Almacenado")
    else:
        if i == adafruit_fingerprint.BADLOCATION:
            print("Ubicación de almacenamiento no válida")
        elif i == adafruit_fingerprint.FLASHERR:
            print("Error de almacenamiento en la memoria flash")
        else:
            print("Otro error")
        return False

    led_verde.off()
    return True

def guardar_imagen_huella(filename):
    while finger.get_image():
        pass
    from PIL import Image
    img = Image.new("L", (256, 288), "white")
    pixeldata = img.load()
    mask = 0b00001111
    result = finger.get_fpdata(sensorbuffer="image")
    x = 0
    y = 0
    for i in range(len(result)):
        pixeldata[x, y] = (int(result[i]) >> 4) * 17
        x += 1
        pixeldata[x, y] = (int(result[i]) & mask)

def obtener_numero(max_number):
    i = -1
    while (i > max_number - 1) or (i < 0):
        try:
            i = int(input("Ingrese el ID # de 0 a {}: ".format(max_number - 1)))
        except ValueError:
            pass
    return i

def dpad(pos):
    if pos.top:
        inscribir_huella(obtener_numero(finger.library_size))
        wait_and_clear()
    elif pos.bottom:
        if obtener_huella():
            print("Detectada #", finger.finger_id, "con confianza", finger.confidence)
            led_verde.on()
            time.sleep(2)
            led_verde.off()
        else:
            print("Huella no encontrada")
            led_rojo.on()
            time.sleep(2)
            led_rojo.off()
        wait_and_clear()
    elif pos.left:
        if finger.delete_model(obtener_numero(finger.library_size)) == adafruit_fingerprint.OK:
            print("¡Eliminada!")
        else:
            print("Error al eliminar")
        wait_and_clear()
    elif pos.right:
        if finger.empty_library() == adafruit_fingerprint.OK:
            print("¡Librería vacía!")
        else:
            print("Error al vaciar la librería")
        wait_and_clear()
    elif pos.middle:
        print("Saliendo del proyecto")
        raise SystemExit

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_menu():
    clear_console()
    print("----------------")
    if finger.read_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("No se pudieron leer las plantillas")
    print("Plantillas de huella: ", finger.templates)
    if finger.count_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("No se pudieron leer las plantillas")
    print("Número de plantillas encontradas: ", finger.template_count)
    if finger.read_sysparam() != adafruit_fingerprint.OK:
        raise RuntimeError("No se pudieron obtener los parámetros del sistema")
    print("Tamaño de la librería de plantillas: ", finger.library_size)
    print("UP) inscribir huella")
    print("BOTTOM) Entrar por huella")
    print("LEFT) eliminar huella")
    print("RIGHT) reiniciar librería")
    print("MIDDLE) salir")

def wait_and_clear():
    time.sleep(3)
    clear_console()
    show_menu()

show_menu()
bd = BlueDot()

bd.when_pressed = dpad

print("----------------")
pause()
