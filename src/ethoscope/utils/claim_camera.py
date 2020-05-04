import picamera
import time
import logging
import os
import sys
import signal
import shutil

logging.basicConfig(level=logging.INFO)

pidfile = "/var/run/picamera/picamera.pid"

def remove_pidfile(pidfile=pidfile):
    logging.info("Removing pidfile")
    os.unlink(pidfile)

def create_pidfile(framerate, resolution, pidfile=pidfile):
    pid = str(os.getpid())
    directory = "/var/run/picamera/"
    os.makedirs(directory, exist_ok=True)

    try:
        capture = picamera.PiCamera(framerate=framerate, resolution=resolution)
    except Exception as e:
        logging.error(e)
        #logging.warning(f"An existing pidfile is detected in {pidfile}.")
        if os.path.isfile(pidfile):
            with open(pidfile, 'r') as fh:
                pid = fh.readline().strip("\n")
                logging.warning(f"Killing process with pid {pid}...")
                try:
                    os.kill(int(pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass
            time.sleep(5)

        #remove_pidfile(pidfile)
            try:
                shutil.move(pidfile, "/root/old_pidfile")
            except OSError:
                pass

        capture = picamera.PiCamera()

    finally:
        with open(pidfile, 'w') as fh:
            logging.info(f"Writing PID {pid} to pidfile {pidfile}")
            fh.write(str(pid))

    return capture


def claim_camera(framerate=None, resolution=None):
    capture = create_pidfile(framerate=framerate, resolution=resolution)

    return capture

