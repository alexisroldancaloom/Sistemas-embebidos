from bluedot import BlueDot
from signal import pause

# Importa la biblioteca para controlar el display de siete segmentos
from gpiozero import SevenSegmentDisplay

# Define los nombres de los integrantes del equipo
integrantes = ["Isaac", "Ale", "Fer", "Alexis"]

# Inicializa el display de siete segmentos (Ajusta los pines según la conexión de tu Raspberry Pi)
display = SevenSegmentDisplay(digits=4, segment_pins=(2, 3, 4, 5, 6, 7, 8, 9))

def saludo():
    # Muestra el nombre del primer integrante cuando se presiona el BlueDot
    display.display_text(integrantes[0])

def despedida():
    # Limpia el display cuando se suelta el BlueDot
    display.clear()

# Configura el BlueDot
bd = BlueDot()
bd.when_pressed = saludo
bd.when_released = despedida

# Mantén el programa en ejecución
pause()
