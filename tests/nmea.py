import serial

port = "/dev/serial0"
baud = 9600

ser = serial.Serial(port, baud, timeout=1)

print("Reading GPS data... (Ctrl+C to stop)")

try:
    while True:
        line = ser.readline().decode('ascii', errors='replace').strip()
        if line.startswith("$"):
            print(line)

except KeyboardInterrupt:
    print("\nStopped.")
    ser.close()
