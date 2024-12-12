# Sample application for the MAX77960 charger driver
from philander.battery import Status as BatStatus
from philander.charger import Charger, Status as ChgStatus
from philander.configurable import Configuration
from philander.max77960 import MAX77960 as chargerDriver
from philander.systypes import ErrorCode, Info

from simple_term_menu import TerminalMenu


def settings():
    global setup
    title = "Edit settings"
    options = []
    for k, v in setup.items():
        options.append( str(k) + ": " + str(v) )
    done = False
    while not done:
        menu = TerminalMenu(options, title=title )
        selection = menu.show()
        if (selection is None):
            done = True
        else:
            key = list( setup.keys() )[selection]
            val = input("New value: ")
            val = val.strip()
            if val:
                try:
                    numVal = int(val)
                    setup[key] = numVal
                    options[selection] = str(key) + ": " + str(numVal)
                except ValueError:
                    setup[key] = val
                    options[selection] = str(key) + ": " + str(val)
    return None

def chgOpen():
    global charger, setup
    if (charger is None):
        print("Charger is not instantiated!")
    else:
        print("Trying to open the charger with the following settings:")
        try:
            if ("SerialBus.designator" in setup):
                print("SerialBus.designator = " + str(setup["SerialBus.designator"]))
            else:
                print("SerialBus.designator not set.")
            if ("SerialBusDevice.address" in setup):
                print("SerialBusDevice.address = " + str(setup["SerialBusDevice.address"]))
            else:
                print("SerialBusDevice.address not set.")
            err = charger.open( setup )
            if (err.isOk()):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
            #traceback.print_exc()
    return None

def chgClose():
    global charger
    if (charger is None):
        print("Charger is not instantiated!")
    else:
        try:
            err = charger.close()
            if (err.isOk()):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
    return None

def getInfo():
    global charger
    if not (charger is None):
        bRaisedExc = False
        try:
            info, err = charger.getInfo()
        except Exception as exc:
            print("Exception:", exc)
            bRaisedExc = True
        if (not bRaisedExc) and (err.isOk()):
            if (info.validity == Info.validNothing):
                print("No info provided.")
            else:
                if(info.validity & Info.validChipID):
                    print("Chip ID     : ", hex(info.chipID) )
                if(info.validity & (Info.validRevMajor | Info.validRevMinor)):
                    revStr=""
                    if (info.validity & Info.validRevMajor):
                        revStr = revStr + str(info.revMajor)
                    if (info.validity & Info.validRevMinor):
                        revStr = revStr + "." + str(info.revMinor)
                    print("Revision    : ", revStr)
                if(info.validity & Info.validModelID):
                    print("Model ID    : ", hex(info.modelID) )
                if(info.validity & Info.validManufacID):
                    print("Manufacturer: ", hex(info.manufacturerID) )
                if(info.validity & Info.validSerialNum):
                    print("SerialNo.   : ", info.serialNumber)
        elif not bRaisedExc:
            print("Error: ", err)
    else:
        print("Charger is not instantiated!")
    return None

def getStatus():
    global charger
    if (charger is None):
        print("Charger is not instantiated!")
    else:
        try:
            err = charger.isBatteryPresent()
            print(f"Battery is present: {err}.")
            num = charger.getNumCells()
            print(f"#Num battery cells: {num}.")
            batstat = charger.getBatStatus()
            print( "Battery status    : ", hex(batstat.value), str(batstat) )
            print( "    Physical      : ", str( BatStatus( batstat & BatStatus.problemPhysical)) )
            print( "    Electrical    : ", str( BatStatus( batstat & BatStatus.problemElectrical)) )
            print( "    Thermal       : ", str( BatStatus( batstat & BatStatus.problemThermal)) )
            chgstat = charger.getChgStatus()
            print( "Charger status    : ", chgstat )
            dcstat = charger.getDCStatus()
            print( "DC status         : ", dcstat )
            pwrSrc = charger.getPowerSrc()
            print( "Power source      : ", pwrSrc )
            tmpRating = charger.getChargerTempStatus()
            print( "ChargerTemperature: ", tmpRating )
            tmpRating = charger.getBatteryTempStatus()
            print( "BatteryTemperature: ", tmpRating )
            chgErr = charger.getError()
            print( "Charger error     : ", chgErr )
        except Exception as exc:
            print("Exception:", exc)
    return None

def reCharge():
    global charger
    if (charger is None):
        print("Charger is not instantiated!")
    else:
        try:
            err = charger.restartCharging()
            if (err.isOk()):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
    return None

def reset():
    global charger
    if (charger is None):
        print("Charger is not instantiated!")
    else:
        try:
            err = charger.reset()
            if (err.isOk()):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
    return None

def regDump():
    global charger
    if (charger is None):
        print("Charger is not instantiated!")
    else:
        try:
            rs = charger.getAllRegistersStr()
            print('Nr Register name |    Content')
            for line in rs:
                sRegNum = format( line[0], "02x" )
                sRegName= line[1]
                sContent= format( line[2], "02x" )
                sMeaning= line[3]
                print( f'{sRegNum} {sRegName:14}|{sContent}: {sMeaning}' )
        except Exception as exc:
            print("Exception:", exc)
    return None


def main():
    global charger, setup
    
    charger = chargerDriver()
    chargerDriver.Params_init( setup )
    
    title = "Charger test application"
    options = ["Settings", "Open", "Close", "Info", "Status", \
               "reCharge", "Reset", "Register dump", "Exit"]
    menu = TerminalMenu( options, title=title )
    
    done = False
    while not done:
        selection = menu.show()
        if (selection == 0):
            settings()
        elif (selection == 1):
            chgOpen()
        elif (selection == 2):
            chgClose()
        elif (selection == 3):
            getInfo()
        elif (selection == 4):
            getStatus()
        elif (selection == 5):
            reCharge()
        elif (selection == 6):
            reset()
        elif (selection == 7):
            regDump()
        elif (selection == 8):
            done = True
    
    charger.close()
    print("Done.")
            
#
# Global variables
#
charger = None
setup = {
    #   SerialBus.busDesignator depends on the system/board. Default is "/dev/i2c-1".
    #   RaspberryPi needs "/dev/i2c-1", while Google Coral has "/dev/i2c-3".
    #   SMBus implementation needs integers (1,3), while the periphery module takes strings.
    "SerialBus.designator": "/dev/i2c-1",
    #   SerialBusDevice.addres gives the I2C address right away (0x69).
    #   Default is 0x69.
    # "SerialBusDevice.address": 0x69,
    #"MAX77960.int.gpio.pinDesignator":   4,
    #chargerDriver.CFG_COMM_MODE: chargerDriver.CFG_COMM_MODE_I2C,
    }

if __name__ == "__main__":
    main()
