import subprocess
import time
import os
import re

QUEUE_FILE = "./queue.txt"
MODEM_ID = "0"

def run_mmcli(args): # to run mmcli cmds
    result = subprocess.run(
        ["mmcli"] + args,
        capture_output=True,
        text=True
    )
    return result.stdout

def list_sms(): # list sms messages
    out = run_mmcli(["-m", MODEM_ID, "--messaging-list-sms"])
    return re.findall(r'/SMS/(\d+)', out)

def read_sms(sms_id):
    return run_mmcli(["-s", sms_id])

def delete_sms(sms_id): # to delete after reading
    subprocess.run([
        "sudo",
        "mmcli",
        "-m", MODEM_ID,
        f"--messaging-delete-sms={sms_id}"
    ])

def parse_sms_text(raw): # parser
    for line in raw.splitlines():
        if "text:" in line.lower():
            return line.split(":", 1)[1].strip()
    return None

def safe_enqueue(line): # safe
    with open(QUEUE_FILE, "a") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())

def safe_prequeue(line):
    # Read existing content (if file exists)
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r") as f:
            existing = f.read()
    else:
        existing = ""

    # Write new line at the beginning
    with open(QUEUE_FILE, "w") as f:
        f.write(line + "\n" + existing)
        f.flush()
        os.fsync(f.fileno())


def handle_command(command_text):
    command_text = command_text.strip().lower()
    print("\x1b[1;31m")
    print("Received command:", command_text)

    parts = command_text.split()

    if not parts:
        return

    if parts[0] == "takepic":
        safe_enqueue("TAKEPIC")

    elif parts[0] == "takepics":
        if len(parts) == 3:
            safe_enqueue(f"TAKEPICS {parts[1]} {parts[2]}")
        else:
            print("\x1b[1;31m")
            print("Invalid TAKEPICS format")

    elif parts[0] == "goto":
        if len(parts) >= 5:
            lat, lon, alt, radius = parts[1], parts[2], parts[3], parts[4]
            safe_prequeue(f"GOTO {lat} {lon} {alt} {radius}")
        else:
            print("\x1b[1;31m")
            print("Invalid GOTO format")

    elif parts[0] == "stop":
        safe_prequeue("STOP")

    elif parts[0] == "reboot":
        safe_enqueue("REBOOT")

    elif parts[0] == "home":
        safe_prequeue("HOME")

    elif parts[0] == "picset":
        if len(parts) == 3:
            safe_prequeue(f"PICSET {parts[1]} {parts[2]}")
        else:
            print("\x1b[1;31m")
            print("Invalid PICSET format")

    else:
        print("\x1b[1;31m")
        print("Unknown command")


def main():
    print("\x1b[1;31m")
    print("Polling for SMS via mmcli...\n")

    seen = set()

    while True:
        sms_ids = list_sms()

        for sms_id in sms_ids:
            if sms_id in seen:
                continue

            print("\x1b[1;31m")
            print("New SMS:", sms_id)

            raw = read_sms(sms_id)
            print("\x1b[1;31m")
            print(raw)

            text = parse_sms_text(raw)

            if text:
                handle_command(text)

            delete_sms(sms_id)
            seen.add(sms_id)

        time.sleep(5)  # polling interval


if __name__ == "__main__":
    main()