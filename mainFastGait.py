# Sample application for the BMA456 sensor driver, FeelSpace actuator unit and MAX77960 power management
from BMA456 import BMA456 as sensor
from ActorUnit import ActorUnit

import time # Depending on the measurement strategy, this is not really necessary
import math # To use sqrt()

#
# Main program
#

MEASUREMENT_INTERVAL = 0.1 # given in seconds
ACCELERATION_THRESHOLD = 1.5 # measured in g

setup = {
    ### BMA456 driver settings ###
    #   SerialDevice.busType defaults to sensor.BUSTYPE_I2C
    #"SerialDevice.busType"      : sensor.BUSTYPE_I2C,
    #   SerialDevice.busDesignator depends on the system/board. Default is "/dev/i2c-1".
    #   RaspberryPi needs "/dev/i2c-1", while Google Coral has "/dev/i2c-3".
    #   SMBus implementation needs integers (1,3), while the periphery module takes strings.
    "SerialDevice.busDesignator": "/dev/i2c-1", 
    #   SerialDevice.deviceAddress gives either SDO status (0/1) or I2C address right
    #   away (0x18/0x19). Depends on the underlying system board.
    #   Default is 0 (i.e. 0x18).
    "SerialDevice.deviceAddress": 0,
    #   Sensor.dataRange defines the measurement range. Set as needed.
    #   Defaults to sensor.ACC_RANGE_2G.
    #"Sensor.dataRange"    : sensor.ACC_RANGE_2G,
    #   Sensor.dataRate is the measurement frequency expressed as Hz. Set as needed.
    #   Default is sensor.ACC_DATARATE_50.
    #"Sensor.dataRate"     : sensor.ACC_DATARATE_50
    #
    ### ActorUnit's settings ###
    #"ActorUnit.delay"          : 0,
    #    Initial delay [0...65535]ms
    #"ActorUnit.pulsePeriod"   : 1000,
    #    Length of one period [0...65535]ms
    #"ActorUnit.pulseOn"       : 600,
    #    Length of the active part in that period [0...pulsePeriod]ms
    #"ActorUnit.pulseCount"    : 3,
    #    Number of pulses [0...255]. Zero (0) means infinite pulses.
    #"ActorUnit.pulseIntensity": 80,
    #    Intensity of the pulses [0...100]%
    #"ActorUnit.actuators"     : ActorUnit.MOTORS_ALL
    #    Motors to be used for the pulses, one of ActorUnit.{MOTORS_NONE,MOTORS_1,MOTORS_2,MOTORS_ALL}
    #
    ### MAX77960 driver settings ###
    }

#
# Step 1: Instantiate a BMA456 (sensor) object.
#
print( "Initializing sapplication with this setup:" )
print(setup)
sd = sensor( setup )
au = ActorUnit( setup )
print( "After object instantiation, setup was adjusted to:" )
print(setup)

#
# Step 2: Initialize that object.
#
sd.init()
au.init()

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
        print(f'{tNow:0.4f}  {data}')
        #print( data[1], data[2], data[3] )
        norm = math.sqrt( data[1]**2 + data[2]**2 + data[3]**2 )
        if norm > ACCELERATION_THRESHOLD:
            au.handleEvent()
        time.sleep( MEASUREMENT_INTERVAL )
    
except KeyboardInterrupt:
    pass

#
# Done. When finishing the application, it's good practice to
# release the related hardware resourfces. So...
# Step #4: Close the sensor
#
sd.close()
au.close()
print( "OK." )
