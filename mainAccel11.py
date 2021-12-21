# Sample application for the Accel 11 click board
import time
import BMA456 as sensor

   
# Start main loop
print( "Initializing sensor." )
err = sensor.init()

if ( err == sensor.ERR_OK ):
    val = sensor.get_temperature()
    print("Chip temperature:", val, "°C")

if ( err == sensor.ERR_OK ):
    tNow = time.time()
    tEnd = tNow + 10 
    while tNow < tEnd:
       data = sensor.get_acc()
       print( data )
       time.sleep(0.1)
       tNow = time.time()

if ( err == sensor.ERR_OK ):
  print( "OK." )
else:
    print( "Error =", err, "." )
    
sensor.close()
