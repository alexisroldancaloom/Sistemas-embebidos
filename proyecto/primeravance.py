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

# Define la secuencia que se debe seguir
secuencia_correcta = ["up", "down", "left", "right"]

# Inicializa la lista que almacenará las entradas del usuario
entradas_usuario = []
bd = BlueDot()
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
    # Toma 2 imágenes de la huella y las templatea, luego las almacena en 'location'
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Coloque el dedo en el sensor...", end="")
        else:
            print("Coloque el mismo dedo nuevamente...", end="")

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Huella tomada")
                led_verde.on()  # Enciende el LED verde
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="")
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Error de Huella")
                led_rojo.on()   # Enciende el LED rojo
                time.sleep(2)   # Espera 2 segundos
                led_rojo.off()  # Apaga el LED rojo
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

    # Apagar el LED verde después de que el proceso de inscripción ha finalizado
    led_verde.off()

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


def obtener_numero(max_number):
    """Utiliza input() para obtener un número válido de 0 al tamaño máximo
    de la librería. Reintentar hasta tener éxito!"""
    i = -1
    while (i > max_number - 1) or (i < 0):
        try:
            i = int(input("Ingrese el ID # de 0 a {}: ".format(max_number - 1)))
        except ValueError:
            pass
    return i

# Función para verificar la secuencia
def verificar_secuencia(pos):
    # Agrega la posición actual a las entradas del usuario
    entradas_usuario.append(pos)

    # Verifica si la secuencia del usuario coincide con la secuencia correcta
    if entradas_usuario == secuencia_correcta:
        print("¡Acceso concedido!")
        # Limpia las entradas del usuario para el próximo intento
        led_verde.on()  # Enciende el LED verde
        time.sleep(2)   # Espera 2 segundos
        led_verde.off() # Apaga el LED verde
            
        entradas_usuario.clear()
    else:
        print("Secuencia incorrecta")
        led_rojo.on()   # Enciende el LED rojo
        time.sleep(2)   # Espera 2 segundos
        led_rojo.off()  # Apaga el LED rojo


while True:
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
    print("a) inscribir huella")
    print("b) Entrar por huella")
    print("c) Entrar por clave")
    print("d) eliminar huella")
    print("e) guardar imagen de huella")
    print("f) reiniciar librería")
    print("g) salir")
    print("----------------")
    c = input("> ")

    if c == "a":
        inscribir_huella(obtener_numero(finger.library_size))
    if c == "b":
        if obtener_huella():
            print("Detectada #", finger.finger_id, "con confianza", finger.confidence)
            led_verde.on()  # Enciende el LED verde
            time.sleep(2)   # Espera 2 segundos
            led_verde.off() # Apaga el LED verde
            
        else:
            print("Huella no encontrada")
            led_rojo.on()   # Enciende el LED rojo
            time.sleep(2)   # Espera 2 segundos
            led_rojo.off()  # Apaga el LED rojo
    if c == "c":
    # Limpiamos las entradas del usuario para la nueva secuencia
        entradas_usuario.clear()
        print("Ingrese la secuencia de la contraseña usando el Bluedot.")
        bd.when_pressed = verificar_secuencia

        # Nos mantenemos en un bucle hasta que la verificación de la secuencia haya terminado
        while True:
            # Esperamos a que la longitud de las entradas del usuario sea igual a la longitud de la secuencia correcta
            if len(entradas_usuario) == len(secuencia_correcta):
                break
            time.sleep(0.1)  # Esperamos un poco para evitar un uso excesivo de la CPU

    if c == "d":
        if finger.delete_model(obtener_numero(finger.library_size)) == adafruit_fingerprint.OK:
            print("¡Eliminada!")
        else:
            print("Error al eliminar")
    if c == "e":
        if guardar_imagen_huella("huella.png"):
            print("Imagen de huella guardada")
        else:
            print("Error al guardar la imagen de la huella")
    if c == "f":
        if finger.empty_library() == adafruit_fingerprint.OK:
            print("¡Librería vacía!")
        else:
            print("Error al vaciar la librería")
    if c == "g":
        print("Saliendo del programa de ejemplo de huella digital")
        raise SystemExit