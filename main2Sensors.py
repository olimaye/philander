import time

import BMA456 as sensor
#import vibrasense2 as sensor2






MEASUREMENT_INTERVAL = 0.1

print( "Initializing sensors." )
err = sensor.init()
if ( err == sensor.ERR_OK ):
    #err = sensor2.init()

    try:
        print("Measurement started. Press Ctrl+C to end.")
        while True:
            tNow = time.time()
            data = sensor.get_measurement()
            #data2 = sensor2.get_measurement()
            
            print(data)
            #print(f"{data}  {data2}") 
            time.sleep( MEASUREMENT_INTERVAL )
        
    except KeyboardInterrupt:
        pass

sensor.close()
#sensor2.close()

if ( err == sensor.ERR_OK ):
    print( "OK." )
else:
    print( "Error =", err, "." )
 