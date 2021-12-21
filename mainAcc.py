# Sample application for the BMA456 sensor driver
from BMA456 import BMA456 as sensor

import time # Depending on the measurement strategy, this is not really necessary

#
# Main program
#

MEASUREMENT_INTERVAL = 0.1

setup = {
    #   busType defaults to sensor.BUSTYPE_I2C
    #"busType"      : sensor.BUSTYPE_I2C,
    #   busDesignator depends on the system/board. Default is "/dev/i2c-1".
    #   RaspberryPi needs "/dev/i2c-1", while Google Coral has "/dev/i2c-3".
    #   SMBus implementation needs integers (1,3), while the periphery module takes strings.
    "busDesignator": "/dev/i2c-1", 
    #   deviceAddres gives either SDO status (0/1) or I2C address right
    #   away (0x18/0x19). Depends on the underlying system board.
    #   Default is 0 (i.e. 0x18).
    "deviceAddress": 0,
    #   dataRange defines the measurement range. Set as needed.
    #   Defaults to sensor.ACC_RANGE_2G.
    #"dataRange"    : sensor.ACC_RANGE_2G,
    #   dataRate is the measurement frequency expressed as Hz. Set as needed.
    #   Default is sensor.ACC_DATARATE_50.
    #"dataRate"     : sensor.ACC_DATARATE_50
    }

#
# Step 1: Instantiate a BMA456 (sensor) object.
#
print( "Initializing sensor with this setup:" )
print(setup)
sd = sensor( setup )
print( "After object instantiation, setup was adjusted to:" )
print(setup)

#
# Step 2: Initialize that object.
#
sd.init()

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
        time.sleep( MEASUREMENT_INTERVAL )
    
except KeyboardInterrupt:
    pass

#
# Done. When finishing the application, it's good practice to
# release the related hardware resourfces. So...
# Step #4: Close the sensor
#
sd.close()
print( "OK." )
