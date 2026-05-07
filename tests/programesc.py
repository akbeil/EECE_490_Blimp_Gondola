import board
import busio
from adafruit_pca9685 import PCA9685
import sys
import termios
import tty
import time

# Setup I2C and PCA9685
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

esc_ch = [0,1]

# Track current pulse (start at neutral or min)
current_pulse = 1000

def set_pulse(channel, pulse):
    for x in channel:
        pca.channels[x].duty_cycle = int(pulse / 20000 * 65535)
        time.sleep(0.2)

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key

print("ESC keyboard control")
print("START AT MIN UNTIL CHIME TO ENTER NORMAL ESC OPERATION")
print("start at max to enter esc program mode")
print("m = max throttle")
print("n = min throttle")
print("+ = increase by 5")
print("- = decrease by 5")
print("q = quit")
print("1 = 25% throttle")
print("2 = 50% throttle")
print("3 = 75% throttle")
print("b = 1100 pwm")

while True:
    key = get_key()

    if key == "m":
        current_pulse = 2000
        set_pulse(esc_ch, current_pulse)
        print(f"MAX throttle ({current_pulse})")

    elif key == "n":
        current_pulse = 1000
        set_pulse(esc_ch, current_pulse)
        print(f"MIN throttle ({current_pulse})")

    elif key == "+":
        current_pulse = min(2000, current_pulse + 5)
        set_pulse(esc_ch, current_pulse)
        print(f"Pulse: {current_pulse}")

    elif key == "-":
        current_pulse = max(1000, current_pulse - 5)
        set_pulse(esc_ch, current_pulse)
        print(f"Pulse: {current_pulse}")

    elif key == "1":
        current_pulse = 1250
        set_pulse(esc_ch, current_pulse)
        print(f"25% throttle ({current_pulse})")

    elif key == "2":
        current_pulse = 1500
        set_pulse(esc_ch, current_pulse)
        print(f"50% throttle ({current_pulse})")

    elif key == "3":
        current_pulse = 1750
        set_pulse(esc_ch, current_pulse)
        print(f"75% throttle ({current_pulse})")

    elif key == "b":
        current_pulse = 1100
        set_pulse(esc_ch, current_pulse)
        print("1100 pwm")

    elif key == "q":
        print("Exiting")
        break
