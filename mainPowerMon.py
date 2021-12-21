# Sample application for the MAX77960 sensor driver
from MAX77960 import MAX77960 as power

#
# Main program
#

setup = {
    #   busType defaults to sensor.BUSTYPE_I2C
    #"busType"      : sensor.BUSTYPE_I2C,
    #   busDesignator depends on the system/board. Default is "/dev/i2c-1".
    #   RaspberryPi needs "/dev/i2c-1", while Google Coral has "/dev/i2c-3".
    #   SMBus implementation needs integers (1,3), while the periphery module takes strings.
    "busDesignator": 1,
    #   deviceAddres gives the I2C address right away (0x69).
    #   Default is 0x69.
    # "deviceAddress": 0x69,
    }

#
# Step 1: Instantiate a MAX77960 (power) object.
#
print( "Initializing power with this setup:" )
print(setup)
pw = power( setup )
print( "After object instantiation, setup was adjusted to:" )
print(setup)

#
# Step 2: Initialize that object.
#
pw.init()

#
# This is not mandatory, but just illustrates the
# capabilities of an initialized object.
#
pw.checkID()
print("ID check OK.")

#
# Step 3: Adjust and control power as necessary
#
try:
    print("Run started. Press Ctrl+C to end.")
    rs = pw.getAllRegistersStr()
    for line in rs:
        sRegNum = format( line[0], "02x" )
        sRegName= line[1]
        sContent= format( line[2], "02x" )
        sMeaning= line[3]
        print( f'{sRegNum} {sRegName:14}|{sContent}: {sMeaning}' )

    done = False
    while not done:
        pass
        # key = keyboard.read_key()
        # if key == 'R':
                
    
except KeyboardInterrupt:
    pass


#
# Done. When finishing the application, it's good practice to
# release the related hardware resourfces. So...
# Step #4: Close the power
#
pw.close()
