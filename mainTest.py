# Sample application for the BMA456 sensor driver
import BMA456 as sensor

#
# Main program
#

print( "Initializing sensor." )
err = sensor.init( devSDO=0, dataRange=sensor.ACC_RANGE_4G, dataRate=sensor.ACC_DATARATE_50 )

if ( err == sensor.ERR_OK ):
    err = sensor.check_ID()
    if (err == sensor.ERR_OK ):
        print("ID check OK.")
    else:
        print("ID check failed.")

num = 32
widx = int( num / 2 )
#sensor.write_data( sensor.REG_DMA_LOW, widx & 0x0F )
#sensor.write_data( sensor.REG_DMA_HI, widx >> 4 )
d = sensor.read_data_stream( sensor.REG_FEATURES, 8 )
print(d)
    

sensor.close()

if ( err == sensor.ERR_OK ):
    print( "OK." )
else:
    print( "Error =", err, "." )

