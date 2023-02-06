import RPi.GPIO as GPIO
import time

VS_SLOT = 2   # Select the slot that the sensor resides in: 1 or 2.
tStart = 0    # Start time offset


if VS_SLOT == 1:
    VS_CHANNEL_ENABLE = 29  # P1.29 = GPIO:5 = RST
    VS_CHANNEL_OUT    = 31  # P1.31 = GPIO:6 = INT
elif VS_SLOT == 2:
    VS_CHANNEL_ENABLE = 32  # P1.32 = GPIO:12 = RST
    VS_CHANNEL_OUT    = 37  # P1.37 = GPIO:26 = INT
else:
    print("Wrong slot selected for VibraSense!")
    exit()

ERR_OK             = 0


def vs_intHandler(channel):
    tNow = time.time()
    tDisplay = tNow - tStart
    print(f"{tDisplay:.2f}: VibraSense")

def get_measurement():
    return ""

def init():
    global tStart
    
    ret = ERR_OK
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup( VS_CHANNEL_ENABLE, GPIO.OUT )
    GPIO.setup( VS_CHANNEL_OUT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN )
    GPIO.output( VS_CHANNEL_ENABLE, 1 )
    GPIO.add_event_detect(VS_CHANNEL_OUT, GPIO.RISING, callback=vs_intHandler, bouncetime=10)
    tStart = time.time()
    return ret

def close():
    GPIO.cleanup()           # clean up GPIO on exit  
