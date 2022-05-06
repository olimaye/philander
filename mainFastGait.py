# Sample application for the BMA456 sensor driver, and the fastGait system management
# encapsulating the FeelSpace actuator unit and MAX77960 power management
from BMA456 import BMA456 as sensor
from MAX77960 import MAX77960
from FGSystemManagement import FGSystemManagement

from os.path import exists
import sys
import time # Depending on the measurement strategy, this is not really necessary
import math # To use sqrt()
import logging
import argparse
import configparser

import numpy as np 
#import time
from pycoral.adapters import classify
from pycoral.adapters import common
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter
from tflite_runtime.interpreter import Interpreter
from pycoral.utils.edgetpu import get_runtime_version


gDone = False
#
# Helper functions - just handlers
#

def hdlBleConnected():
    logging.info("BLE connected.")

def hdlBleDisconnected():
    logging.info("BLE disconnected.")

def hdlDCPlugged():
    logging.info("DC plugged.")

def hdlDCUnplugged():
    logging.info("DC unplugged.")

def hdlTempCritical():
    logging.info("Temperature critical.")

def hdlTempNormal():
    logging.info("Temperature normal.")

def hdlButtonPressed():
    global gDone
    logging.info("UI button pressed.")
    gDone = True

def hdlPowerCritical():
    global gDone
    logging.info("LDO power critical.")
    #gDone = True

def hdlPowerNormal():
    logging.info("LDO power good (normal).")

#
# Main program
#
    
#
# Step 0: Configuration
#

### Command line arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "-log", "--loglevel",
    default="info",
    help="{debug|info|warning|error|critical}. Provide logging level. Example --log debug', default='info'",
)
parser.add_argument(
    "-c", "--cfg",
    default="fastgait.cfg",
    help="Configuration file name.",
    )

options = parser.parse_args()

### Configuration file
if not exists(options.cfg):
    print( "Missing configuration file:", options.cfg )
    sys.exit()
config = configparser.ConfigParser()
config.read( options.cfg )

### Logging
nowStr = time.strftime('%Y%m%d-%H%M%S')
# The general logging of application messages
fn = 'log/application-'+nowStr+'.log'
logging.basicConfig( filename=fn, format='%(asctime)s %(levelname)s %(module)s: %(message)s', datefmt='%d.%m.%Y %H:%M:%S', level=options.loglevel.upper() )
#logging.basicConfig( format='%(asctime)s %(levelname)s %(module)s: %(message)s', datefmt='%d.%m.%Y %H:%M:%S', level=options.loglevel.upper() )
logging.info( "Launching application." )
logging.info( "Config file in use: %s", options.cfg )

# The data logger
fn = 'log/data-'+nowStr+'.log'
dataLogger = logging.getLogger('FastGait.Data')
fHdlr = logging.FileHandler(fn)
fFrmt = logging.Formatter( fmt='%(asctime)s,%(msecs)03d; %(message)s', datefmt='%H:%M:%S' )
fHdlr.setFormatter( fFrmt )
dataLogger.addHandler( fHdlr )
dataLogger.setLevel( logging.INFO )
dataLogger.propagate = False
dataLogger.info('Sensor micros; AccelX; AccelY; AccelZ')

### BMA456 driver settings ###
setupSensor = {
    #"SerialDevice.busType"      : sensor.BUSTYPE_I2C,
    "SerialDevice.busDesignator": "/dev/i2c-3", 
    #   SerialDevice.deviceAddress gives either SDO status (0/1) or I2C address right
    #   away (0x18/0x19). Depends on the underlying system board.
    #   Default is 0 (i.e. 0x18).
    "SerialDevice.deviceAddress": 1,
    "Sensor.dataRange"    : sensor.ACC_RANGE_2G,
    "Sensor.dataRate"     : sensor.ACC_DATARATE_100,
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
    "UI.LED.chg.pin"          : 25,     # LED_GREEN, pin 33, GPIO25
    "UI.LED.chg.activeHigh"   : False, 
    #"UI.LED.0.pin"            : 25,     # LED_GREEN at pin #33, GPIO25
    #"UI.LED.0.activeHigh"     : False,  # LED is between Vcc and GPIO. 
    #"UI.LED.1.pin"            : 13,     # LED_ORANGE at pin #36, GPIO13
    #"UI.LED.1.activeHigh"     : False,  # LED is between Vcc and GPIO. 
    #    Definition of the button.
    "UI.Button.cmd.pin"       : 39,     # USER_BTN at pin #40, GPIO39
    "UI.Button.cmd.activeHigh" : True, 
    #    Definition of the LDO power-good pin.
    "Power.LDO.PG.pin"        : 22,      # PG_PIN at pin #7, GPIO22
    "Power.LDO.PG.activeHigh" : True,   # True, if high-state signals a push, False otherwise
    }
setupSystemManagement = { **setupSystemManagement, **config['system.management'] }

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
    #storing frequency
    acquisition_frequency= 100
    
    # number of data coming by each sd.nextData() 
    # 3 data from axis of acceleration and 1 timestamp
    nr_channel= 4
             
    # 3 acceleration channels are required. timestamp is ignored.
    data_window = np.zeros((acquisition_frequency, nr_channel-1))
    
    # orientated signal according to patient data in ghostnode
    oriented_signal = np.zeros((acquisition_frequency, nr_channel-1))
    
    i = 0
    
    logging.info('interpreter is going to load %s.', config['model.AI']['filename'] )
    interpreter = Interpreter( config['model.AI']['filename'] )
    logging.info('interpreter loaded tflite file.')
    interpreter.allocate_tensors()
    logging.info('interpreter allocated tensors.')
    # model is laoded and the required tensors allocated
    shiftX = config['model.AI'].getint('shift.x', 0)
    shiftY = config['model.AI'].getint('shift.y', 0)
    shiftZ = config['model.AI'].getint('shift.z', 0)
    
    logging.info('Measurement started.')
    print("Press button or Ctrl+C to end.")
    gDone = False
    while not gDone:
        tNow = time.time()
        data = sd.nextData()
        data_window[i] = data[1:4]
        i = i + 1
        
        # Log data
        dataLogger.info("%d; %d; %d; %d", data[0], data[1], data[2], data[3])
        
        # Change the axis, orientation and signals corresponding to axis 
        # and orientation achieved by same patient data with ghostndoe from Konstanz
        # x <- -y
        oriented_signal[:,0] = -data_window[:,1] + shiftX
        # y <- -z
        oriented_signal[:,1] = -data_window[:,2] + shiftY
        # z <- x
        oriented_signal[:,2] = data_window[:,0] + shiftZ
        
        if i == acquisition_frequency:
            # input the window of data into the LSTM model            
            common.set_input(interpreter, oriented_signal)
            # deply the inference
            interpreter.invoke()
            
            # get results of model deployment
            score_interpreter = classify.get_scores(interpreter)
            logging.info(score_interpreter)
            
            # FOG detected
            if score_interpreter[1] > score_interpreter[0]:
                sy.actorUnit.handleEvent()
                logging.info('FOG alarm triggered.')
            i = 0
    
except KeyboardInterrupt:
    pass
except KeyError as err:
    logging.critical( 'Configuration key error: %s', err )

#
# Done. When finishing the application, it's good practice to
# release the related hardware resources. So...
# Step #4: Close objects.
#
sd.close()
sy.close()
logging.info( "Program ends." )
print("Done.")
