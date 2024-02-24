from gpiozero import LED
from time import sleep
from signal import pause

# Define los pines GPIO para cada LED
pin_led1 = 5
pin_led2 = 6
pin_led3 = 13
pin_led4 = 19
pin_led5 = 26

# Crea objetos LED individuales para cada LED
led1 = LED(pin_led1)
led2 = LED(pin_led2)
led3 = LED(pin_led3)
led4 = LED(pin_led4)
led5 = LED(pin_led5)

# Enciende todos los LEDs al principio
led1.on()
led2.on()
led3.on()
led4.on()
led5.on()

sleep(1)

# Apaga todos los LEDs después de un segundo
led1.off()
led2.off()
led3.off()
led4.off()
led5.off()

sleep(1)

# Establece el estado de cada LED individualmente
led1.value = 1
led2.value = 0
led3.value = 1
led4.value = 0
led5.value = 1

sleep(1)

# Hace parpadear todos los LEDs
led1.blink()
led2.blink()
led3.blink()
led4.blink()
led5.blink()

pause()
