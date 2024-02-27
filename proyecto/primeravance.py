import time
import serial

import adafruit_fingerprint

uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

##################################################


def obtener_huella():
    # Obtiene una imagen de la huella, la templatea y verifica si coincide
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


# pylint: disable=too-many-branches
def obtener_detalle_huella():
    # Obtiene una imagen de la huella, la templatea y verifica si coincide.
    # Esta vez, imprime cada error en lugar de simplemente regresar en caso de fallo
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
    # pylint: disable=no-else-return
    # Este bloque necesita ser refactorizado cuando se pueda probar.
    if i == adafruit_fingerprint.OK:
        print("¡Huella encontrada!")
        return True
    else:
        if i == adafruit_fingerprint.NOTFOUND:
            print("No se encontró coincidencia")
        else:
            print("Otro error")
        return False


# pylint: disable=too-many-statements
def inscribir_huella(location):
    # Toma 2 imágenes de la huella y las templatea, luego las almacena en 'location
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Coloque el dedo en el sensor...", end="")
        else:
            print("Coloque el mismo dedo nuevamente...", end="")

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Huella tomada")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="")
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Error de Huella")
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

    return True


def guardar_imagen_huella(filename):
    # Escanea la huella y luego guarda la imagen en filename
    while finger.get_image():
        pass

    # deja que PIL se encargue de los encabezados de la imagen y la estructura del archivo
    from PIL import Image  # pylint: disable=import-outside-toplevel

    img = Image.new("L", (256, 288), "white")
    pixeldata = img.load()
    mask = 0b00001111
    result = finger.get_fpdata(sensorbuffer="image")

    # este bloque "desempaqueta" los datos recibidos del módulo de huella digital
    #   luego copia los datos de la imagen al placeholder de imagen "img"
    #   píxel por píxel.  por favor refiérase a la sección 4.2.1 del manual para
    #   más detalles.  gracias a Bastian Raschke y Danylo Esterman.
    # pylint: disable=invalid-name
    x = 0
    # pylint: disable=invalid-name
    y = 0
    # pylint: disable=consider-using-enumerate
    for i in range(len(result)):
        pixeldata[x, y] = (int(result[i]) >> 4) * 17
        x += 1
        pixeldata[x, y] = (int(result[i]) & mask)
