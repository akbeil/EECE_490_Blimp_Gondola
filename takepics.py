import argparse
import time
import subprocess
import os

QUEUE_FILE = "./queue.txt"
COUNTER_FILE = "./counter.txt"

parser = argparse.ArgumentParser(
    usage="python3 takepics.py <count> <interval_seconds>"
)

parser.add_argument("count", type=int)
parser.add_argument("interval", type=int)

args = parser.parse_args()

for i in range(args.count):

    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE) as f:
            n = int(f.read())
    else:
        n = 0
    n += 1

    filename = f"/home/blimp26/final/pics/pic{n:04d}.jpg"

    subprocess.run([
        "python3",
        "takepic.py",
        "1080", "75", filename
    ])

    with open(COUNTER_FILE, "w") as f:
        f.write(str(n))

    print(f"Captured {filename}")

    # enqueue upload
    with open(QUEUE_FILE, "a") as f:
        f.write(f"UPLOAD {filename}\n")

    if i < args.count - 1:
        time.sleep(args.interval)