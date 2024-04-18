# Sample application for the BMA456 sensor driver, and the fastGait uiPowerSys management
from philander.bma456 import BMA456 as SensorDriver
from philander.fastgait.sysman import SystemManagement
from philander.led import LED
from philander.max77960 import MAX77960		# Just for the constants
from philander.systypes import ErrorCode

from os.path import exists
import sys
import time # Depending on the measurement strategy, this is not really necessary
#import math # To use sqrt()
import logging
import argparse
import configparser
import random

DEFAULT_SCORE_LIMIT	= 0.004

gDone = False
### BMA456 driver settings ###
setupSensor = {
    "SerialBus.designator": "/dev/i2c-3", 
    "SerialBusDevice.address": 0x19,
    "Sensor.dataRange"    : 2000,
    "Sensor.dataRate"     : 100,
    }

setupSystemManagement = {
    ### Battery charger / MAX77960 driver settings ###
    "SerialBus.designator": "/dev/i2c-3", 
    #"SerialBusDevice.address": 0x69,
    #MAX77960.CFG_COMM_MODE: MAX77960.CFG_COMM_MODE_I2C,
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
    #"BLE.discovery.timeout": 5.0, # Timeout for the BLE discovery phase, given in seconds.
    #
    ### User interface settings ###
    "UI.tmp.LED.label"              : "TEMPERATURE-LED",
    "UI.tmp.LED.gpio.pinDesignator" : 11,   # LED_RED, pin 15. GPIO11.
    "UI.tmp.LED.gpio.inverted"      : True, 
    "UI.bat.LED.label"              : "BATTERY-LED",
    "UI.bat.LED.gpio.pinDesignator" : 13,   # LED_ORANGE, pin 36, GPIO13
    "UI.bat.LED.gpio.inverted"      : True, 
    "UI.ble.LED.label"              : "BLE-LED",
    "UI.ble.LED.gpio.pinDesignator" : 12,   # LED_BLUE, pin 32, GPIO12
    "UI.ble.LED.gpio.inverted"      : True, 
    "UI.aux0.LED.label"             : "AUX0-LED",
    "UI.aux0.LED.gpio.pinDesignator": 25,   # LED_GREEN, pin 33, GPIO25
    "UI.aux0.LED.gpio.inverted"     : True, 
    #    Definition of the button.
    "UI.cmd.Button.label"           : "USER-BUTTON",
    "UI.cmd.Button.gpio.pinDesignator" : 39, # USER_BTN at pin #40, GPIO39
    #    Definition of the LDO power-good pin.
    "Sys.power.status.gpio.pinDesignator"  : 22, # PG_PIN at pin #7, GPIO22
    #"Sys.power.status.gpio.inverted" : False,
    #    Other system / ui hardware
    #"UI.dc.status.gpio.pinDesignator" : 1,       #INOK at pin #18, GPIO1 
    #"UI.chg.stat.gpio.pinDesignator" : 0,       #STAT at pin #16, GPIO0
    #"UI.aux0.gpio.pinDesignator"    : 60,       free GPIO at pin #27, GPIO60
    #"UI.aux1.gpio.pinDesignator"    : 61,       free GPIO at pin #28, GPIO61
    }

config = None
sensorDevice = None
uiPowerSys = None
dataLogger = None
scoreLimit = DEFAULT_SCORE_LIMIT

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

def hdlButtonPressed(btnLabel, *_unused):
    global gDone
    logging.info("UI button %s pressed.", btnLabel)
    gDone = True

def hdlPowerCritical():
    global gDone
    logging.info("LDO power critical.")
    #gDone = True

def hdlPowerNormal():
    logging.info("LDO power good (normal).")


#
# Step 0: Configuration
#

def configure():
    global config, dataLogger
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
    parser.add_argument(
        "-o", "--output",
        default="console",
        help="Dump application log output to {console|file}.",
        )
    
    options = parser.parse_args()
    
    ### Configuration file
    if not exists(options.cfg):
        print( "Missing configuration file:", options.cfg )
        sys.exit()
    config = configparser.ConfigParser()
    # Make sure that key names are preserved in case.
    config.optionxform = lambda option : option
    config.read( options.cfg )
    
    ### Logging
    nowStr = time.strftime('%Y%m%d-%H%M%S')
    # The general logging of application messages
    sFormat = "%(asctime)s %(levelname)s %(module)s: %(message)s"
    sDate = "%d.%m.%Y %H:%M:%S"
    if (options.output.casefold()=="file".casefold()):
        fn = 'log/application-'+nowStr+'.log'
        logging.basicConfig( filename=fn, format=sFormat, datefmt=sDate, level=options.loglevel.upper() )
    else:
        logging.basicConfig( format=sFormat, datefmt=sDate, level=options.loglevel.upper() )
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
    dataLogger.info('AccelX; AccelY; AccelZ')
    return None


#
# Step 1: Instantiate and initialize objects.
#
def prepare():
    global config, setupSensor, setupSystemManagement, sensorDevice, \
    uiPowerSys, scoreLimit
    
    logging.info( "Instantiating sensor object." )
    sensorDevice = SensorDriver()
    logging.info( "Instantiating system management object." )
    uiPowerSys = SystemManagement()
    logging.info( "Object instantiation done." )

    try:
        if ("model.AI" in config):
            cfgModelAI = config["model.AI"]
            scoreLimit = cfgModelAI.get( "scorelimit", scoreLimit )
            try:
                scoreLimit = float( scoreLimit )
            except ValueError:
                scoreLimit = DEFAULT_SCORE_LIMIT

            if ("filename" in cfgModelAI):
                logging.info( "Model file name = %s", cfgModelAI["filename"] )
            else:
                logging.info( "Model file name not set." )
        logging.debug( "Effective score limit = %s", str(scoreLimit) )
        
        if ("sensor" in config):
            setupSensor.update( config["sensor"] )    
        logging.debug( "Effective sensor setup = %s", str(setupSensor) )
        err = sensorDevice.open( setupSensor )
        logging.debug( "Open sensor device, error = %s", str(err) )
        logging.debug( "Returned sensor setup = %s", str(setupSensor) )
        
        if ("system.management" in config):
            setupSystemManagement.update( config["system.management"] )
        logging.debug( "Effective system management setup = %s", str(setupSystemManagement) )
        err = uiPowerSys.open( setupSystemManagement )
        logging.debug( "Open system management, error = %s", str(err) )
        logging.debug( "Returned system management setup = %s", str(setupSystemManagement) )
    except configparser.NoSectionError as err:
        logging.debug( 'Configuration section error: %s', err )
    except KeyError as exc:
        logging.debug( 'Configuration key error: %s', exc )
        
    uiPowerSys.on( SystemManagement.EVT_BLE_CONNECTED, hdlBleConnected )
    uiPowerSys.on( SystemManagement.EVT_BLE_DISCONNECTED, hdlBleDisconnected )
    uiPowerSys.on( SystemManagement.EVT_DC_PLUGGED, hdlDCPlugged )
    uiPowerSys.on( SystemManagement.EVT_DC_UNPLUGGED, hdlDCUnplugged )
    uiPowerSys.on( SystemManagement.EVT_TEMP_CRITICAL, hdlTempCritical )
    uiPowerSys.on( SystemManagement.EVT_TEMP_NORMAL, hdlTempNormal )
    uiPowerSys.on( SystemManagement.EVT_POWER_CRITICAL, hdlPowerCritical )
    uiPowerSys.on( SystemManagement.EVT_POWER_NORMAL, hdlPowerNormal )
    uiPowerSys.on( SystemManagement.EVT_BUTTON_PRESSED, hdlButtonPressed )
    return None


#
# Step 2: Collect measurements
#
def doTheJob():
    global gDone, dataLogger, scoreLimit
    try:
        logging.info('Measurement started.')
        gDone = False
        while not gDone:
            data, err = sensorDevice.getNextData()
            if not (err == ErrorCode.errOk):
                logging.debug( 'Measurement error: ', err )
            else:
                # Log data
                dataLogger.info("%d; %d; %d", data[0], data[1], data[2])
                
                score = random.random()
                logging.debug("Score: %s.", str(score) )
                    
                # FOG detected
                if score < scoreLimit:
                    uiPowerSys.actorUnit.action()
                    logging.info('FOG alarm triggered.')
                    if uiPowerSys.aux0LED:
                        uiPowerSys.aux0LED.blink( LED.CURVE_BLINK_CLASSIC, LED.CYCLEN_NORMAL, 1 )
        
    except KeyboardInterrupt:
        logging.info('Interrupted by console input.')
    return None

#
# Step #3: Close objects.
#
def shutdown():
    global sensorDevice, uiPowerSys
    
    err = sensorDevice.close()
    logging.debug( "Close sensor device, error = %s", str(err) )
    err = uiPowerSys.close()
    logging.debug( "Close system management, error = %s", str(err) )
    
    logging.info( "Program ends." )
    #print("Done.")
    return None

#
# The main loop
#

def main():
    configure()
    prepare()
    doTheJob()
    shutdown()
    
if __name__ == "__main__":
    main()
