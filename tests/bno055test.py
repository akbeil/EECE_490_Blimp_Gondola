import time
import board
import busio
import adafruit_bno055
#from adafruit_bno055 import bno055

# Initialize I2C
i2c = busio.I2C(board.SCL, board.SDA)
print(i2c)
# Initialize sensor
sensor = adafruit_bno055.BNO055_I2C(i2c, address=0x29)

print("BNO055 test started...")
print(sensor.mode)
#sensor.mode = adafruit_bno055.OPERATION_MODE_NDOF
print(sensor.calibration_status)
while True:
    #print("Temperature: {} C".format(sensor.temperature))
    print("Acceleration (m/s^2): {}".format(sensor.acceleration))
    print("Magnetometer (uT): {}".format(sensor.magnetic))
    print("Gyroscope (rad/sec): {}".format(sensor.gyro))
    print("Euler angle: {}".format(sensor.euler))
    print("Quaternion: {}".format(sensor.quaternion))
    print("Linear acceleration: {}".format(sensor.linear_acceleration))
    print("Gravity: {}".format(sensor.gravity))
    #print(sensor.mode)
    print(sensor.calibration_status)
    print("-" * 40)
    time.sleep(1)
