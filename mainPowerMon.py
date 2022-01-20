# Sample application for the MAX77960 charger driver
from MAX77960 import MAX77960 as power, MAX77960
from BatteryCharger import BatteryCharger

#
# Menu related helper functions
#

def printMenu():
    print('========== Charger Monitor ==========')
    print('C - Charger view   i - switch to i2c config')
    print('R - register dump  r - restart charging')
    print('q - quit')
    print('=====================================')
    
#
# Main program
#

setup = {
    #   SerialDevice.busType defaults to sensor.BUSTYPE_I2C
    #"SerialDevice.busType"      : sensor.BUSTYPE_I2C,
    #   SerialDevice.busDesignator depends on the system/board. Default is "/dev/i2c-1".
    #   RaspberryPi needs "/dev/i2c-1", while Google Coral has "/dev/i2c-3".
    #   SMBus implementation needs integers (1,3), while the periphery module takes strings.
    "SerialDevice.busDesignator": "/dev/i2c-3",
    #   SerialDevice.deviceAddres gives the I2C address right away (0x69).
    #   Default is 0x69.
    # "SerialDevice.deviceAddress": 0x69,
    }

#
# Step 1: Instantiate a MAX77960 (power) object.
#
pw = power( setup )

#
# Step 2: Initialize that object.
#
pw.init()

#
# This is not mandatory, but just illustrates the
# capabilities of an initialized object.
#
pw.checkID()

#
# Step 3: Adjust and control power as necessary
#
done = False
while not done:
    printMenu()
    try:
        line = input('Press a key and hit enter: ')
    except KeyboardInterrupt:
        line = 'q'
    line = line.strip()
    if not line:
        key = None
    else:
        key = line[0]
        
    if key == 'q':  # Quit
        done = True
    elif key == 'C':  # Charger view
        val = pw.getID()
        print(f'Chip-ID  : {val:02x}')
        val = str( pw.isBatteryPresent() )
        val1= pw.getNumCells()
        print(f'Bat.found: {val:10}      #Cells: {val1}')
        val = BatteryCharger.batState2Str.get( pw.getBatStatus(), 'UNKNOWN' )
        val1= BatteryCharger.chgState2Str.get( pw.getChgStatus(), 'UNKNOWN' )
        print(f'Bat.state: {val:10}   Chg.state: {val1}')
        val = BatteryCharger.dcState2Str.get( pw.getDCStatus(), 'UNKNOWN' )
        val1= BatteryCharger.pwrsrc2Str.get( pw.getPowerSrc(), 'UNKNOWN' )
        print(f' DC.state: {val:10}    PowerSrc: {val1}')
        val = BatteryCharger.temp2Str.get( pw.getChargerTempState(), 'UNKNOWN' )
        try:
            val1= BatteryCharger.temp2Str.get( pw.getBatteryTempState(), 'UNKNOWN' )
        except RuntimeError:
            val1 = 'Undet.'
        print(f'Chg.temp : {val:10}    Bat.temp: {val1}')
        val = BatteryCharger.err2Str.get( pw.getError(), 'UNKNOWN' )
        val1= pw.getIntStatus()
        print(f'   Error : {val:10}   Int.state: {val1:04x}')
    elif key == 'i':  # Switch to i2c
        config = { MAX77960.CFG_COMM_MODE: MAX77960.CFG_COMM_MODE_I2C }
        pw.configure( config )
        print('Comm. mode set to i2c.')
    elif key == 'R':  # Register dump
        rs = pw.getAllRegistersStr()
        print('Nr Register name |    Content')
        for line in rs:
            sRegNum = format( line[0], "02x" )
            sRegName= line[1]
            sContent= format( line[2], "02x" )
            sMeaning= line[3]
            print( f'{sRegNum} {sRegName:14}|{sContent}: {sMeaning}' )
    elif key == 'r':  # Restart charging
        try:
            pw.restartCharging()
            print ('Charger restarted.')
        except RuntimeError as exc:
            print(exc)
print('Program stopped.')
                

#
# Done. When finishing the application, it's good practice to
# release the related hardware resourfces. So...
# Step #4: Close the power
#
pw.close()
