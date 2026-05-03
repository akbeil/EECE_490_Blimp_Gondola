import math
import time
import board
import busio
import serial
import pynmea2
from adafruit_bno055 import BNO055_I2C
from adafruit_pca9685 import PCA9685
from pygeomag import GeoMag
geomag = GeoMag()

GPS_PORT = "/dev/serial0"
GPS_BAUD = 9600
GPS_TIMEOUT = 10

SERVO_NEUTRAL = 1500
SERVO_MIN = 500
SERVO_MAX = 2500
DEADBAND = 5

SERVO_CH = [7, 8]
ESC_CH = [0, 1]

PCA_FREQ = 50 # Hz for standard servos / ESCs

def get_latest_gps(ser):
    """read latest GPS fix"""
    while ser.in_waiting:
        line = ser.readline().decode(errors="ignore").strip()

        if line.startswith("$GPGGA"):
            try:
                msg = pynmea2.parse(line)
                if int(msg.gps_qual) > 0:
                    return {
                        "lat": msg.latitude,
                        "lon": msg.longitude,
                        "alt": float(msg.altitude)
                    }
            except Exception:
                pass

    return None

def get_bearing(lat1, lon1, lat2, lon2):
    """get bearing from point 1 to point 2 in degrees (0-360)"""
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    dlon = math.radians(lon2 - lon1)

    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dlon)

    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360

def heading_error(target, current):
    """compute heading error (-180 to 180)"""
    error = target - current
    if error > 180:
        error -= 360
    elif error < -180:
        error += 360
    return error

def distance_m(lat1, lon1, lat2, lon2):
    """distance between two lat/lon points in meters"""
    R = 6371000  # Earth radius (m)

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    dlat = lat2 - lat1
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def thrust_vector_control(error, alt_error, pca):
    abs_err = abs(error)
    direction = 1 if error > 0 else -1  # +1 = right turn, -1 = left

    base_throttle = 1100
    min_throttle = 1000
    max_throttle = 1200
    forward = 32

    if alt_error > 5:
        forward = 17
    elif alt_error < -5:
        forward = 47
    else:
        forward = 32

    # straight
    if abs_err <= 10:
        set_servo_pair(forward, pca)
        set_pulse(ESC_CH, base_throttle, pca)
        return

    # 10 to 90
    elif abs_err <= 90:
        #t = (abs_err - 10) / (90 - 10)  # 0 → 1

        active = base_throttle
        reduced = 1000 #base_throttle - t * (base_throttle - min_throttle)

        set_servo_pair(forward, pca)

        if direction > 0:
            # turn right
            set_pulse(ESC_CH[0], active, pca)
            set_pulse(ESC_CH[1], reduced, pca)
        else:
            # turn left
            set_pulse(ESC_CH[0], reduced, pca)
            set_pulse(ESC_CH[1], active, pca)

        return

    # 90 to 180
    else:
        #t = (abs_err - 90) / (180 - 90)  # 0 → 1

        #ramp = min_throttle + t * (max_throttle - min_throttle)

        if direction > 0:
            # turn right
            set_pulse(ESC_CH[0], base_throttle, pca)
            set_pulse(ESC_CH[1], base_throttle, pca)

            set_pulse(SERVO_CH[1], 2500, pca)
            set_pulse(SERVO_CH[0], 2500-2000*0.32, pca)

        else:
            # turn left
            set_pulse(ESC_CH[0], base_throttle, pca)
            set_pulse(ESC_CH[1], base_throttle, pca)

            set_pulse(SERVO_CH[0], 500, pca)
            set_pulse(SERVO_CH[1], 2000*0.32+500, pca)

        return

def set_pulse(channels, pulse_us, pca):
    """Set PWM pulse width for PCA9685"""
    duty = int(pulse_us / (1000000 / PCA_FREQ) * 65535)
    if isinstance(channels, int):
        pca.channels[channels].duty_cycle = duty
    else:
        for ch in channels:
            pca.channels[ch].duty_cycle = duty

servo_ch = [7,8]
def set_servo_pair(percent, pca):
    """set both servos to a percent 0 down 100 backwards"""
    percent = max(0, min(100, percent))

    min_pulse = 500
    max_pulse = 2500
    step = (max_pulse - min_pulse) / 100

    pulse1 = int(min_pulse + percent * step)
    pulse2 = int(max_pulse - percent * step)

    pca.channels[servo_ch[1]].duty_cycle = int(pulse1 / 20000 * 65535)
    pca.channels[servo_ch[0]].duty_cycle = int(pulse2 / 20000 * 65535)

def main():
    TARGET_LAT = None
    TARGET_LON = None
    TARGET_ALT = None
    TARGET_RAD = None
    HOME_LAT = None
    HOME_LON = None
    HOME_ALT = None

    # i2c
    i2c = busio.I2C(board.SCL, board.SDA)

    # bno055
    sensor = BNO055_I2C(i2c, address = 0x29)
    sensor.mode = 12

    # pca9685
    pca = PCA9685(i2c, address = 0x40)
    pca.frequency = PCA_FREQ

    # gps
    ser = serial.Serial(GPS_PORT, GPS_BAUD, timeout=0.2)

    # bno055
    while not ((sensor.calibration_status[3] == 3) & (sensor.calibration_status[0] == 3)):
        print("mag status: ", sensor.calibration_status[3], ", sys status: ", sensor.calibration_status[0])
        time.sleep(0.5)

    print("starting nav loop")
    set_servo_pair(31, pca)
    time.sleep(0.5)
    set_servo_pair(32, pca)
    set_pulse(ESC_CH, 1000, pca)
    time.sleep(5)
    booldec = False
    head_error = 9999
    declination = 0
    check = 10

    while True:
        gps = get_latest_gps(ser)
        if gps is None:
            print("no gps")
            time.sleep(1)
            continue
        
        # set home coords
        if gps is not None and HOME_LAT is None:
            HOME_LAT = gps["lat"]
            HOME_LON = gps["lon"]
            HOME_ALT = gps["alt"]
            with open("home.txt", "w") as h:
                h.write(f"{HOME_LAT},{HOME_LON},{HOME_ALT}")
            print("home set:", HOME_LAT, HOME_LON, HOME_ALT)

        # calculate declination
        if gps is not None and (not booldec):
            declination = geomag.calculate(gps["lat"], gps["lon"], gps["alt"], 2026.25).dec
            print ("declination: ", declination)
            booldec = True
        
        mag_heading = sensor.euler[0]
        
        if mag_heading is None:
            print("waiting for bno heading")
            time.sleep(0.1)

        # no gps for 5sec stop motors
        last_valid_time = time.time()
        if gps:
            last_valid_time = time.time()

        if time.time() - last_valid_time > 5:
            print("failsafe: stopping motors")
            set_pulse(ESC_CH, 1000, pca)
        
        # check for updates to target file
        if (check > 10):
            check = 0
            try:
                with open("target.txt") as f:
                    line = f.read().strip()

                    if not line:
                        # Empty file → clear target
                        TARGET_LAT = None
                        TARGET_LON = None
                        TARGET_ALT = None
                        TARGET_RAD = None
                        print("Target cleared (empty file)")
                    else:
                        print("setting local target vars\n")
                        lat, lon, alt, rad = map(float, line.split(","))
                        TARGET_LAT, TARGET_LON, TARGET_ALT, TARGET_RAD = lat, lon, alt, rad

            except Exception as e:
                print("Bad target file:", e)
        check = check + 1

        # main part if there is a target to go to
        if TARGET_LAT is not None:
            alt_error = gps["alt"] - TARGET_ALT

            if sensor.calibration_status[3] >= 2:
                current_heading = (mag_heading + declination + 360) % 360
                target_heading = get_bearing(gps["lat"], gps["lon"], TARGET_LAT, TARGET_LON)
                head_error = heading_error(target_heading, current_heading)

                print(f"GPS: ({gps['lat']:.5f},{gps['lon']:.5f}) | "
                f"Heading: {current_heading:.1f}° | "
                f"Target: {target_heading:.1f}° | "
                f"Error: {head_error:.1f}° | "
                f"Altitude: {gps['alt']}m |")
            else:
                print("mag < 2")

            # if at target adjust alt if needed
            if (distance_m(gps["lat"], gps["lon"], TARGET_LAT, TARGET_LON) < TARGET_RAD): 
                print("at location")
                if alt_error > 5: # straight down
                    set_servo_pair(0, pca)
                    set_pulse(ESC_CH, 1100, pca)
                elif alt_error < -5: # straight up
                    set_servo_pair(67, pca)
                    set_pulse(ESC_CH, 1100, pca)
                else: # off
                    set_pulse(ESC_CH, 1000, pca)
                    time.sleep(2)
            else:
                print("going")
                thrust_vector_control(head_error, alt_error, pca)
        else: # off
            print("no target")
            set_pulse(ESC_CH, 1000, pca)
            set_servo_pair(32, pca)

        time.sleep(1)


if __name__ == "__main__":
    main()
