import picamera
from picamera_attributes import variables
import time

def configure_camera(camera, resolution, fps):
    #camera.resolution = (2560, 1920)
    camera.resolution = resolution
    camera.framerate = fps

    ps = variables.ParameterSet(
            {
                "exposure_mode": "off",
                "awb_gains": "off",
                "shutter_speed": 70000,
                "color_effects": (128, 128),
                "analog_gain": 2,
                "awb_gains": (0.5, 0.5)
                })
    camera = ps.update_cam(camera)

    #camera.color_effects = (128,128)
    #camera.awb_mode = "off"
    #time.sleep(1)
    #camera.awb_gains = (1.8, 1.5)
    #camera.iso = 100
    #camera.exposure_mode = "off"
    ##time.sleep(3)
    ## max fps allowed : 12
    #camera.shutter_speed = 80000
    ##time.sleep(1)
    #camera.exposure_mode = "auto"
    ### give time for the analog and digital gain to adjust
    ### for the new shutter speed
    #time.sleep(12)
    #camera.exposure_mode = "off"
    return camera

