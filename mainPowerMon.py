# Sample application for the MAX77960 charger driver
from MAX77960 import MAX77960 as power
from BatteryCharger import BatteryCharger
from pynput import keyboard

#
# Keyboard helper not related to the charger/power management
#
gKey = None # Global variable holding the last key pressed

def on_press(key):
    global gKey
    gKey = key

def getKey():
    global gKey
    ret = gKey
    done = False
    while not done:
        ret = gKey
        if isinstance(ret, keyboard.KeyCode) or (ret==keyboard.Key.esc):
            done = True
    gKey = None
    return ret

keyListener =  keyboard.Listener(on_press=on_press)

#
# Menu related helper functions
#

def printMenu():
    print('========== Charger Monitor ==========')
    print(' C  - Charger view  R - register dump')
    print('Esc - quit')
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
    "SerialDevice.busDesignator": 1,
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
try:
    keyListener.start()
    done = False
    while not done:
        printMenu()
        key = getKey()
        if key == keyboard.Key.esc:
            done = True
        elif key == keyboard.KeyCode(char='C'):
            val = pw.getID()
            print(f'Chip-ID  : {val:02x}')
            val = str( pw.isBatteryPresent() )
            val1= pw.getNumCells()
            print(f'Bat.found: {val:10}      #Cells: {val1}')
            val = BatteryCharger.state2Str.get( pw.getChgStatus(), 'UNKNOWN' )
            val1= BatteryCharger.pwrsrc2Str.get( pw.getPowerSrc(), 'UNKNOWN' )
            print(f'Chg.state: {val:10}    PowerSrc: {val1}')
            val = BatteryCharger.temp2Str.get( pw.getChargerTempState(), 'UNKNOWN' )
            try:
                val1= BatteryCharger.temp2Str.get( pw.getBatteryTempState(), 'UNKNOWN' )
            except RuntimeError:
                val1 = 'Undet.'
            print(f'Chg.temp : {val:10}    Bat.temp: {val1}')
            val = BatteryCharger.err2Str.get( pw.getError(), 'UNKNOWN' )
            val1= pw.getIntStatus()
            print(f'   Error : {val:10}   Int.state: {val1:04x}')
        elif key == keyboard.KeyCode(char='R'):
            rs = pw.getAllRegistersStr()
            print('Nr Register name |    Content')
            for line in rs:
                sRegNum = format( line[0], "02x" )
                sRegName= line[1]
                sContent= format( line[2], "02x" )
                sMeaning= line[3]
                print( f'{sRegNum} {sRegName:14}|{sContent}: {sMeaning}' )
    keyListener.stop()
    print('Program stopped.')
                
    
except KeyboardInterrupt:
    pass


#
# Done. When finishing the application, it's good practice to
# release the related hardware resourfces. So...
# Step #4: Close the power
#
pw.close()
