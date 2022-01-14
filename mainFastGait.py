# Sample application for the BMA456 sensor driver, and the fastGait system management
# encapsulating the FeelSpace actuator unit and MAX77960 power management
from BMA456 import BMA456 as sensor
from FGSystemManagement import FGSystemManagement

import time # Depending on the measurement strategy, this is not really necessary
import math # To use sqrt()

#
# Main program
#

MEASUREMENT_INTERVAL = 0.1 # given in seconds
ACCELERATION_THRESHOLD = 1200 # measured in milli-g

    
### BMA456 driver settings ###
setupSensor = {
    #   SerialDevice.busType defaults to sensor.BUSTYPE_I2C
    #"SerialDevice.busType"      : sensor.BUSTYPE_I2C,
    #   SerialDevice.busDesignator depends on the system/board. Default is "/dev/i2c-1".
    #   RaspberryPi needs "/dev/i2c-1", while Google Coral has "/dev/i2c-3".
    #   SMBus implementation needs integers (1,3), while the periphery module takes strings.
    #"SerialDevice.busDesignator": "/dev/i2c-1", 
    "SerialDevice.busDesignator": 1, 
    #   SerialDevice.deviceAddress gives either SDO status (0/1) or I2C address right
    #   away (0x18/0x19). Depends on the underlying system board.
    #   Default is 0 (i.e. 0x18).
    "SerialDevice.deviceAddress": 1,
    #   Sensor.dataRange defines the measurement range. Set as needed.
    #   Defaults to sensor.ACC_RANGE_2G.
    #"Sensor.dataRange"    : sensor.ACC_RANGE_2G,
    #   Sensor.dataRate is the measurement frequency expressed as Hz. Set as needed.
    #   Default is sensor.ACC_DATARATE_50.
    #"Sensor.dataRate"     : sensor.ACC_DATARATE_50
    #
    }

setupSystemManagement = {
    ### MAX77960 driver settings ###
    #   SerialDevice.busType defaults to sensor.BUSTYPE_I2C
    #"SerialDevice.busType"      : sensor.BUSTYPE_I2C,
    #   SerialDevice.busDesignator depends on the system/board. Default is "/dev/i2c-1".
    #   RaspberryPi needs "/dev/i2c-1", while Google Coral has "/dev/i2c-3".
    #   SMBus implementation needs integers (1,3), while the periphery module takes strings.
    #"SerialDevice.busDesignator": "/dev/i2c-1", 
    "SerialDevice.busDesignator": 1, 
    #   SerialDevice.deviceAddress gives either SDO status (0/1) or I2C address right
    #   away (0x69). Depends on the underlying system board.
    #   Default is 0x69.
    #"SerialDevice.deviceAddress": 0x69,
    ### ActorUnit's settings ###
    #"ActorUnit.delay"          : 0,
    #    Initial delay [0...65535]ms
    "ActorUnit.pulsePeriod"   : 600,
    #    Length of one period [0...65535]ms
    "ActorUnit.pulseOn"       : 250,
    #    Length of the active part in that period [0...pulsePeriod]ms
    "ActorUnit.pulseCount"    : 3,
    #    Number of pulses [0...255]. Zero (0) means infinite pulses.
    "ActorUnit.pulseIntensity": 55,
    #    Intensity of the pulses [0...100]%
    #"ActorUnit.actuators"     : ActorUnit.MOTORS_ALL,
    #    Motors to be used for the pulses, one of ActorUnit.{MOTORS_NONE,MOTORS_1,MOTORS_2,MOTORS_ALL}
    #"ActorUnit.BLE.discovery.timeout": 5.0,
    #    Timeout for the BLE discovery phase, given in seconds.
    ### User interface settings ###
    "UI.LED.tmp.pin"          : 'BOARD15', # LED_RED, pin 15.
    #    Pin of the TMP LED.
    "UI.LED.tmp.activeHigh"   : False,     # LED is between Vcc and GPIO. 
    #    True, if a logical 1 switches LED on; False, if it makes LED off.
    "UI.LED.bat.pin"          : 'BOARD36', # LED_ORANGE, pin 36.
    #    Pin of the BAT LED.
    "UI.LED.bat.activeHigh"   : False,     # LED is between Vcc and GPIO. 
    #    True, if a logical 1 switches LED on; False, if it makes LED off.
    "UI.LED.ble.pin"          : 'BOARD32', # LED_BLUE, pin 32.
    #    Pin of the BLE LED.
    "UI.LED.ble.activeHigh"   : False,     # LED is between Vcc and GPIO. 
    #    True, if a logical 1 switches LED on; False, if it makes LED off.
    #"UI.LED.dc.pin"           : 'BOARD33', # Actually hard-wired. Leave as comment!
    #    Pin of the DC LED.
    #"UI.LED.dc.activeHigh"   : False, 
    #    True, if a logical 1 switches LED on; False, if it makes LED off.
    #"UI.LED.chg.pin"          : 'BOARD33', # Actually hard-wired. Leave as comment!
    #    Pin of the CHG LED.
    #"UI.LED.chg.activeHigh"   : False, 
    #    True, if a logical 1 switches LED on; False, if it makes LED off.
    }

#
# Step 1: Instantiate objects.
#
print( "Instantiating objects." )
sd = sensor( setupSensor )
sy = FGSystemManagement( setupSystemManagement )
print( "Object instantiation done." )

#
# Step 2: Initialize objects.
#
sd.init()
sy.init()

#
# This is not mandatory, but just illustrates the
# capabilities of an initialized object.
#
sd.checkID()
print("ID check OK.")
    
val = sd.getDieTemperature()
print("Chip temperature:", val, " deg.C")

#
# Step 3: Collect measurements by either nextData() or lastData().
#
try:
    print("Measurement started. Press Ctrl+C to end.")
    while True:
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
print( "OK." )
