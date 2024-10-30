# Sample application for the LED driver
from philander.serialbus import SerialBusDevice

from generalTestSuite import run, MenuFunction



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

    dev = SerialBusDevice()
    settings = {
        #"SerialBus.busType"      : SerialBusType.I2C,
        #   RaspberryPi needs "/dev/i2c-1", while Google Coral has "/dev/i2c-3".
        #   SMBus implementation needs integers (1,3), while the periphery module takes strings.
        "SerialBus.designator": 0,
        #"SerialBus.provider": SerialBusProvider.AUTO, 
        "SerialBusDevice.address": 0x18,
    }
    SerialBusDevice.Params_init( settings )
    
    functions = [
        # connectivity functions
        MenuFunction(dev.open, args=(settings,)),
        MenuFunction(dev.close),
        # data functions
        MenuFunction(dev.isAttached),
        MenuFunction(dev.readByteRegister, args=(0x00,) ),
        MenuFunction(dev.writeByteRegister, args=(0x41, 0x02,)),
    ]
    
    title = "Serial Bus test application"

    # run test suite
    run(settings, functions, title)

    dev.close()
    print("Done.")
            

if __name__ == "__main__":
    main()
