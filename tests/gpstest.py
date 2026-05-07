import serial
import pynmea2
import time
import argparse
import subprocess
import os
import sys


ROTATION = 0   # change if needed (0, 90, 180, 270)

#COUNTER_FILE = "./counter.txt"

def get_latest_gps(port="/dev/serial0", baud=9600, timeout=10):
    ser = serial.Serial(port, baud, timeout=0.2)
    start = time.time()

    #print("Listening for GPS data...\n")

    while time.time() - start < timeout:
        line = ser.readline().decode(errors="ignore").strip()

        if line.startswith("$GPGGA"):# or line.startswith("$GNGGA"):
            try:
                msg = pynmea2.parse(line)

                if int(msg.gps_qual) > 0:
                    ser.close()
                    return {
                        "lat": msg.latitude,
                        "lon": msg.longitude,
                        "alt": float(msg.altitude),
                    }

            except Exception:
                pass
        
        time.sleep(0.05)
    
    ser.close()
    return None

def decimal_to_dms(value):
    abs_val = abs(value)
    degrees = int(abs_val)
    minutes_float = (abs_val - degrees) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60, 6)

    sec_num = int(seconds * 10000)
    sec_den = 10000

    return f"{degrees}/1,{minutes}/1,{sec_num}/{sec_den}"

def main():
    while 1:
        gps = get_latest_gps()
        if gps:
            print("GPS Fix:")
            print(f"Latitude:  {gps['lat']}")
            print(f"Longitude: {gps['lon']}")
            print(f"Altitude:  {gps['alt']} m")
        else:
            print("No GPS fix received.")
        


if __name__ == "__main__":
    main()
