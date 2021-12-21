# Sample application for the HTU21D click board
import time
import HTU21D as sensor

DURATION = 20
   
# Start main loop
print( "Initializing sensor." )
err = sensor.init()

if ( err == sensor.ERR_OK ):
    tNow = time.time()
    tEnd = tNow + DURATION
    while tNow < tEnd:
       data = sensor.get_measurement()
       print( data )
       time.sleep(0.1)
       tNow = time.time()

if ( err == sensor.ERR_OK ):
  print( "OK." )
else:
    print( "Error =", err, "." )
    
sensor.close()
