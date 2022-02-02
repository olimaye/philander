# Sample application for the BMA456 sensor driver, and the fastGait system management
# encapsulating the FeelSpace actuator unit and MAX77960 power management
from BMA456 import BMA456 as sensor
from MAX77960 import MAX77960
from FGSystemManagement import FGSystemManagement

import time # Depending on the measurement strategy, this is not really necessary
import math # To use sqrt()
import logging
import argparse


gDone = False
#
# Helper functions - just handlers
#

def hdlBleConnected():
    logging.info("Main App> BLE connected.")

def hdlBleDisconnected():
    logging.info("Main App> BLE disconnected.")

def hdlDCPlugged():
    logging.info("Main App> DC plugged.")

def hdlDCUnplugged():
    logging.info("Main App> DC unplugged.")

def hdlTempCritical():
    logging.info("Main App> Temperature critical.")

def hdlTempNormal():
    logging.info("Main App> Temperature normal.")

def hdlButtonPressed():
    global gDone
    logging.info("Main App> UI button pressed.")
    gDone = True

def hdlPowerCritical():
    global gDone
    logging.info("Main App> LDO power critical.")
    #gDone = True

def hdlPowerNormal():
    logging.info("Main App> LDO power good (normal).")

#
# Step 0: Configure logging
#
parser = argparse.ArgumentParser()
parser.add_argument(
    "-log", 
    "--loglevel",
    default="info",
    help=( "{debug|info|warning|error|critical}. Provide logging level. Example --log debug', default='info'"
    ),
)
options = parser.parse_args()
logging.basicConfig( level=options.loglevel.upper() )


#
# Main program
#

MEASUREMENT_INTERVAL = 0.1 # given in seconds
ACCELERATION_THRESHOLD = 1200 # measured in milli-g

    
### BMA456 driver settings ###
setupSensor = {
    #"SerialDevice.busType"      : sensor.BUSTYPE_I2C,
    "SerialDevice.busDesignator": "/dev/i2c-3", 
    #   SerialDevice.deviceAddress gives either SDO status (0/1) or I2C address right
    #   away (0x18/0x19). Depends on the underlying system board.
    #   Default is 0 (i.e. 0x18).
    "SerialDevice.deviceAddress": 1,
    #"Sensor.dataRange"    : sensor.ACC_RANGE_2G,
    #"Sensor.dataRate"     : sensor.ACC_DATARATE_50,
    }

setupSystemManagement = {
    ### Battery charger / MAX77960 driver settings ###
    #"SerialDevice.busType"      : sensor.BUSTYPE_I2C,
    "SerialDevice.busDesignator": "/dev/i2c-3", 
    #"SerialDevice.deviceAddress": 0x69,
    MAX77960.CFG_COMM_MODE: MAX77960.CFG_COMM_MODE_I2C,
    #MAX77960.CFG_STAT_EN  : MAX77960.CFG_STAT_EN_ON,
    MAX77960.CFG_FCHGTIME : MAX77960.CFG_FCHGTIME_6H,
    #MAX77960.CFG_CHGCC    : MAX77960.CFG_CHGCC_1000,
    MAX77960.CFG_TO_TIME  : MAX77960.CFG_TO_TIME_10_MIN,
    #MAX77960.CFG_TO_ITH   : MAX77960.CFG_TO_ITH_100,
    MAX77960.CFG_CHG_CV_PRM: MAX77960.CFG_CHG_CV_PRM_2C_8400,
    MAX77960.CFG_JEITA_EN : MAX77960.CFG_JEITA_EN_ON,
    #MAX77960.CFG_REGTEMP  : MAX77960.CFG_REGTEMP_115,
    #MAX77960.CFG_CHGIN_ILIM: 2500,
    #MAX77960.CFG_MINVSYS  : MAX77960.CFG_MINVSYS_2C_6150,
    MAX77960.CFG_VCHGIN_REG: MAX77960.CFG_VCHGIN_REG_4550,
    #
    ### ActorUnit's settings ###
    #"ActorUnit.delay"          : 0,  # Initial delay [0...65535]ms
    "ActorUnit.pulsePeriod"   : 600,  # Length of one period [0...65535]ms
    "ActorUnit.pulseOn"       : 250,  # Length of the active part in that period [0...pulsePeriod]ms
    "ActorUnit.pulseCount"    : 3,    # Number of pulses [0...255]. Zero (0) means infinite pulses.
    "ActorUnit.pulseIntensity": 55,   # Intensity of the pulses [0...100]%
    #"ActorUnit.actuators"     : ActorUnit.MOTORS_ALL,
    #"ActorUnit.BLE.discovery.timeout": 5.0, # Timeout for the BLE discovery phase, given in seconds.
    #
    ### User interface settings ###
    "UI.LED.tmp.pin"          : 11,   # LED_RED, pin 15. GPIO11.
    "UI.LED.tmp.activeHigh"   : False, 
    "UI.LED.bat.pin"          : 13,  # LED_ORANGE, pin 36, GPIO13
    "UI.LED.bat.activeHigh"   : False, 
    "UI.LED.ble.pin"          : 12,   # LED_BLUE, pin 32, GPIO12
    "UI.LED.ble.activeHigh"   : False, 
    #"UI.LED.dc.pin"           : 'BOARD33', # Actually hard-wired. Leave as comment!
    #"UI.LED.dc.activeHigh"    : False, 
    #"UI.LED.chg.pin"          : 'BOARD33', # Actually hard-wired. Leave as comment!
    #"UI.LED.chg.activeHigh"   : False, 
    "UI.LED.0.pin"            : 25,     # LED_GREEN at pin #33, GPIO25
    "UI.LED.0.activeHigh"     : False,  # LED is between Vcc and GPIO. 
    #"UI.LED.1.pin"            : 13,     # LED_ORANGE at pin #36, GPIO13
    #"UI.LED.1.activeHigh"     : False,  # LED is between Vcc and GPIO. 
    #    Definition of the button.
    "UI.Button.cmd.pin"       : 39,     # USER_BTN at pin #40, GPIO39
    "UI.Button.cmd.activeHigh" : True, 
    #    Definition of the LDO power-good pin.
    "Power.LDO.PG.pin"        : 22,      # PG_PIN at pin #7, GPIO22
    "Power.LDO.PG.activeHigh" : True,   # True, if high-state signals a push, False otherwise
    }

#
# Step 1: Instantiate objects.
#
logging.info( "Instantiating objects." )
sd = sensor( setupSensor )
sy = FGSystemManagement( setupSystemManagement )
logging.info( "Object instantiation done." )

#
# Step 2: Initialize objects.
#
sd.init()
sy.init()
sy.on( FGSystemManagement.EVT_BLE_CONNECTED, hdlBleConnected )
sy.on( FGSystemManagement.EVT_BLE_DISCONNECTED, hdlBleDisconnected )
sy.on( FGSystemManagement.EVT_DC_PLUGGED, hdlDCPlugged )
sy.on( FGSystemManagement.EVT_DC_UNPLUGGED, hdlDCUnplugged )
sy.on( FGSystemManagement.EVT_TEMP_CRITICAL, hdlTempCritical )
sy.on( FGSystemManagement.EVT_TEMP_NORMAL, hdlTempNormal )
sy.on( FGSystemManagement.EVT_BUTTON_PRESSED, hdlButtonPressed )
sy.on( FGSystemManagement.EVT_POWER_CRITICAL, hdlPowerCritical )
sy.on( FGSystemManagement.EVT_POWER_NORMAL, hdlPowerNormal )

#
# This is not mandatory, but just illustrates the
# capabilities of an initialized object.
#
val = sd.getDieTemperature()
logging.info("Chip temperature: %d deg.C", val)

#
# Step 3: Collect measurements by either nextData() or lastData().
#
try:
    logging.info('Measurement started.')
    print("Press button or Ctrl+C to end.")
    gDone = False
    while not gDone:
        tNow = time.time()
        data = sd.nextData()
        #data = sensor.lastData()
        #print(f'{tNow:0.4f}  {data}')
        #print( data[1], data[2], data[3] )
        
        # Alerting part
        norm = math.sqrt( data[1]**2 + data[2]**2 + data[3]**2 )
        if norm > ACCELERATION_THRESHOLD:
            sy.actorUnit.handleEvent()
            
        # Loop delay
        time.sleep( MEASUREMENT_INTERVAL )
    
except KeyboardInterrupt:
    pass

#
# Done. When finishing the application, it's good practice to
# release the related hardware resources. So...
# Step #4: Close objects.
#
sd.close()
sy.close()
logging.info( "Program ends." )
