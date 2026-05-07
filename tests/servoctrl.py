import board
import busio
from adafruit_pca9685 import PCA9685
import sys
import termios
import tty

# Setup I2C and PCA9685
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

servo_ch = [7,8]

def set_servo_pair(percent):
    percent = max(0, min(100, percent))

    min_pulse = 500
    max_pulse = 2500
    step = (max_pulse - min_pulse) / 100

    pulse1 = int(min_pulse + percent * step)
    pulse2 = int(max_pulse - percent * step)

    pca.channels[servo_ch[1]].duty_cycle = int(pulse1 / 20000 * 65535)
    pca.channels[servo_ch[0]].duty_cycle = int(pulse2 / 20000 * 65535)

def set_pulse(channel, pulse):
    for x in channel:
        pca.channels[x].duty_cycle = int(pulse / 20000 * 65535)

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key

print("Servo keyboard control")
print("1,2,3,4,5,6,7,8,9,0 = 10% rotation")
print("q = quit")

while True:
    key = get_key()

    if key == "m":
        set_pulse(esc_ch, 2000)
        print("MAX throttle")
    elif key == "`":
        set_servo_pair(0)
    elif key == "1":
        set_servo_pair(10)
    elif key == "2":
        set_servo_pair(20)
    elif key == "3":
        set_servo_pair(30)
    elif key == "4":
        set_servo_pair(40)
    elif key == "5":
        set_servo_pair(50)
    elif key == "6":
        set_servo_pair(60)
    elif key == "7":
        set_servo_pair(70)
    elif key == "8":
        set_servo_pair(80)
    elif key == "9":
        set_servo_pair(90)
    elif key == "0":
        set_servo_pair(100)
    elif key == "q":
        print("Exiting")
        break
