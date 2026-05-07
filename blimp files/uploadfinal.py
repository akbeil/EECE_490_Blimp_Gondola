import time
import subprocess
import os

QUEUE_FILE = "./queue.txt"
COUNTER_FILE = "./counter.txt"

def get_next_job(): # get next job and remove from queue
    if not os.path.exists(QUEUE_FILE):
        return None

    with open(QUEUE_FILE, "r") as f:
        lines = f.readlines()

    if not lines:
        return None

    job = lines[0].strip()

    with open(QUEUE_FILE, "w") as f:
        f.writelines(lines[1:])

    return job

def take_picture(res, qual): # call takepic script
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE) as f:
            n = int(f.read())
    else:
        n = 0

    n += 1
    filename = f"/home/blimp26/final/pics/pic{n:04d}.jpg"

    subprocess.run([
        "python3",
        "/home/blimp26/final/takepic.py",
        res, qual, filename
    ])

    with open(COUNTER_FILE, "w") as f:
        f.write(str(n))

    return filename

def upload_file(filename): # upload with rclone
    
    result = subprocess.run([
        "rclone", "copy", filename, "blimp26:/BlimpImages/final", "-vv"
    ])
   
    print("\x1b[1;33m")
    if result.returncode == 0:
        print("Upload successful")
        return True
    else:
        print("Upload failed, will retry later")
        return False

def main():
    print("\x1b[1;33m")
    print("Worker running...")

    with open("picsettings.txt") as f:
        line = f.read().strip()
        res, qual = line.split()

    while True:
        job = get_next_job()

        if not job:
            time.sleep(2)
            continue

        print("\x1b[1;33m")
        print("Job:", job)

        if job == "TAKEPIC":
                
            file = take_picture(res, qual)

            # queue upload separately
            with open(QUEUE_FILE, "a") as f:
                f.write(f"UPLOAD {file}\n")

        elif job.startswith("TAKEPICS"):
            _, count, interval = job.split()

            subprocess.Popen([ # open in background
                "python3",
                "/home/blimp26/final/takepics.py",
                count,
                interval
            ])

            print("\x1b[1;33m")
            print("Started timelapse job in background")

        elif job.startswith("GOTO"): # write to target.txt
            _, lat, lon, alt, radius = job.split()

            print("\x1b[1;33m")
            print(f"Navigating to {lat},{lon} at {alt}m within {radius} ft")

            with open("target.txt", "w") as t:
                t.write(f"{lat},{lon},{alt},{radius}")
            
        elif job.startswith("STOP"): # clr target.txt
            print("\x1b[1;33m")
            print("stopping, clr target")

            with open("target.txt", "w") as t:
                t.write("")
            
        elif job.startswith("HOME"): # target.txt = home.txt
            print("\x1b[1;33m")
            print("going home")

            try:
                with open("home.txt", "r") as h:
                    line = h.read().strip()

                    if not line:
                        print("Home file is empty")
                    else:
                        lat, lon, alt = map(float, line.split(","))

                        with open("target.txt", "w") as t:
                            t.write(f"{lat},{lon},{alt},10")

                        print(f"Returning home: {lat},{lon},{alt},10")

            except Exception as e:
                print("Failed to load home:", e)

        elif job.startswith("UPLOAD"): # upload
            _, filename = job.split()

            if not os.path.exists(filename):
                print("\x1b[1;33m")
                print(f"File {filename} does not exist. Dropping job.")
                continue  # DO NOT requeue

            success = upload_file(filename)

            if not success:
                # retry later
                with open(QUEUE_FILE, "a") as f:
                    f.write(job + "\n")

        elif job.startswith("PICSET"): # write settings to file
            _, res, qual = job.split()
            with open("picsettings.txt", "w") as s:
                s.write(f"{res} {qual}")
            
        elif job == "REBOOT":
            subprocess.Popen(["sudo", "reboot"])

        else:
            print("\x1b[1;33m")
            print("Unknown job")

        time.sleep(1)


if __name__ == "__main__":
    main()
