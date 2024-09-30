# Sample application for the LED driver
from philander.serialbus import SerialBusDevice

try:
    from simple_term_menu import TerminalMenu
except ImportError as exc:
    from micromenu import MicroMenu as TerminalMenu


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

def open():
    global serBusDev, setup
    if (serBusDev is None):
        print("SerialBusDevice is not instantiated!")
    else:
        print("Trying to open the serial bus with the following settings:")
        try:
            if ("SerialBusDevice.address" in setup):
                print("SerialBusDevice.address = " + str(setup["SerialBusDevice.address"]))
            else:
                print("SerialBusDevice.address not set.")
            if ("SerialBus.designator" in setup):
                print("SerialBus.designator = " + str(setup["SerialBus.designator"]))
            else:
                print("SerialBus.designator not set.")
            err = serBusDev.open( setup )
            if (err.isOk()):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print(f"Exception ({exc.__class__.__name__}): {exc}")
            #traceback.print_exc()
            #import sys
            #sys.print_exception(exc)
    return None

def close():
    global serBusDev
    if (serBusDev is None):
        print("SerialBusDevice is not instantiated!")
    else:
        try:
            err = serBusDev.close()
            if (err.isOk()):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print(f"Exception ({exc.__class__.__name__}): {exc}")
    return None

def read():
    global serBusDev
    if (serBusDev is None):
        print("SerialBusDevice is not instantiated!")
    else:
        val = input("Register number (dec): ")
        val = val.strip()
        if val:
            try:
                numVal = int(val)
                data, err = serBusDev.readByteRegister( numVal )
                if (err.isOk()):
                    print("Success, read=", data)
                else:
                    print("Error: ", err)
            except ValueError:
                print("Couldn't convert that into a number!")
            except Exception as exc:
                print(f"Exception ({exc.__class__.__name__}): {exc}")
    return None

def write():
    global serBusDev
    if (serBusDev is None):
        print("SerialBusDevice is not instantiated!")
    else:
        regStr = input("Register number  (dec): ")
        datStr = input("Content to write (dec): ")
        regStr = regStr.strip()
        datStr = datStr.strip()
        if regStr and datStr:
            try:
                regNum = int(regStr)
                regDat = int(datStr)
                err = serBusDev.readByteRegister( regNum, regDat )
                if (err.isOk()):
                    print("Success!")
                else:
                    print("Error: ", err)
            except ValueError:
                print("Couldn't convert that into a number!")
            except Exception as exc:
                print(f"Exception ({exc.__class__.__name__}): {exc}")
        else:
            print("That input was nothing.")
    return None

def main():
    global serBusDev, setup
    
    serBusDev = SerialBusDevice()
    SerialBusDevice.Params_init( setup )
    
    title = "Serial Bus test application"
    options = ["Settings", "Open", "Close", "Read", "Write"]
    menu = TerminalMenu( options, title=title )
    
    done = False
    while not done:
        selection = menu.show()
        if (selection is None):
            done = True
        elif (selection == 0):
            settings()
        elif (selection == 1):
            open()
        elif (selection == 2):
            close()
        elif (selection == 3):
            read()
        elif (selection == 4):
            write()
    
    serBusDev.close()
    print("Done.")
            
#
# Global variables
#
serBusDev = None
setup = {
    #"SerialBus.busType"      : SerialBusType.I2C,
    #   RaspberryPi needs "/dev/i2c-1", while Google Coral has "/dev/i2c-3".
    #   SMBus implementation needs integers (1,3), while the periphery module takes strings.
    "SerialBus.designator": 0,
    #"SerialBus.provider": SerialBusProvider.AUTO, 
    "SerialBusDevice.address": 0x18,
}

if __name__ == "__main__":
    main()
