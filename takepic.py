import serial
import pynmea2
import time
import argparse
import subprocess

ROTATION = 0

def get_latest_gps(port="/dev/serial0", baud=9600, timeout=10):
    ser = serial.Serial(port, baud, timeout=0.2)
    start = time.time()

    while time.time() - start < timeout:
        line = ser.readline().decode(errors="ignore").strip()

        if line.startswith("$GPGGA"):
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
    parser = argparse.ArgumentParser(
        usage="python3 takepicgps.py 720|1080|4k quality filename.jpg"
    )

    parser.add_argument("resolution", type=str)
    parser.add_argument("quality", type=int)
    parser.add_argument("filename", type=str)

    args = parser.parse_args()

    # resolutions
    if args.resolution == "720":
        width, height = 1280, 720
    elif args.resolution == "1080":
        width, height = 1920, 1080
    elif args.resolution == "4k":
        width, height = 3840, 2160
    else:
        print("Invalid resolution. Use 720, 1080, or 4k.")
        return

    print("Waiting for GPS fix...")
    gps = get_latest_gps()

    cmd = [
        "rpicam-still",
        "-n",
        "--immediate",
        "--width", str(width),
        "--height", str(height),
        "--quality", str(args.quality),
        "--rotation", str(ROTATION),
        "-o", args.filename
    ]

    if not gps: # take pic without gps data
        print("No valid GPS fix. Capturing without GPS metadata.")

        subprocess.run(cmd)
        return

    print("\nUsing GPS Data:")
    print("Latitude :", gps["lat"])
    print("Longitude:", gps["lon"])
    print("Altitude :", gps["alt"], "meters\n")

    lat_ref = "N" if gps["lat"] >= 0 else "S"
    lon_ref = "E" if gps["lon"] >= 0 else "W"

    lat_dms = decimal_to_dms(gps["lat"])
    lon_dms = decimal_to_dms(gps["lon"])
    altitude = f"{int(gps['alt']*1000)}/1000"

    exif_tags = [
        f"GPS.GPSLatitudeRef={lat_ref}",
        f"GPS.GPSLatitude={lat_dms}",
        f"GPS.GPSLongitudeRef={lon_ref}",
        f"GPS.GPSLongitude={lon_dms}",
        f"GPS.GPSAltitude={altitude}"
    ]

    for tag in exif_tags:
        cmd.extend(["--exif", tag])
    # exif tags added to cmd

    print("Capturing image with GPS EXIF...")
    print(" ".join(cmd))
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("ERROR: rpicam-still failed!")
        return

    print(f"Saved {args.filename}")


if __name__ == "__main__":
    main()
