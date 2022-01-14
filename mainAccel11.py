# Sample application for the Accel 11 click board
from BMA456 import BMA456 as sensor
import time

   
# Start main loop

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

print( "Initializing sensor." )
sd = sensor( setupSensor )
sd.init()

val = sd.getDieTemperature()
print("Chip temperature:", val, "deg C")

tNow = time.time()
tEnd = tNow + 10 
while tNow < tEnd:
   data = sd.nextData()
   print( data )
   time.sleep(0.1)
   tNow = time.time()

print( "OK." )
sd.close()
