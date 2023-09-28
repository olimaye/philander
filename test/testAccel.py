from philander.accelerometer import Accelerometer, EventContext, Configuration, StatusID
from philander.bma456 import BMA456 as sensorDriver
from philander.gpio import GPIO
from philander.interruptable import Event
from philander.sensor import ConfigItem
from philander.systypes import ErrorCode, RunLevel, Info

from simple_term_menu import TerminalMenu
from threading import Thread
import time
import traceback

#
# Interrupt handling routine
#
def callback(feedback, varArgs):
    global flagInterrupt, timeInterrupt, currentEvent
    if (not flagInterrupt):
        flagInterrupt = 1
        timeInterrupt = time.time()
        currentEvent = feedback

def thrInputKey():
    input()
    return None


def settings():
    global configSensor
    title = "Edit settings"
    options = []
    for k, v in configSensor.items():
        options.append( str(k) + ": " + str(v) )
    done = False
    while not done:
        menu = TerminalMenu(options, title=title )
        selection = menu.show()
        if (selection is None):
            done = True
        else:
            key = list( configSensor.keys() )[selection]
            val = input("New value: ")
            val = val.strip()
            if val:
                try:
                    numVal = int(val)
                    configSensor[key] = numVal
                    options[selection] = str(key) + ": " + str(numVal)
                except ValueError:
                    configSensor[key] = val
                    options[selection] = str(key) + ": " + str(val)
    return None

def sopen():
    global sensor, configSensor
    if (sensor is None):
        print("Sensor is not instantiated!")
    else:
        print("Trying to open the sensor with the following settings:")
        try:
            if ("SerialBus.designator" in configSensor):
                print("SerialBus.designator = " + str(configSensor["SerialBus.designator"]))
            else:
                print("SerialBus.designator not set.")
            if ("SerialBusDevice.address" in configSensor):
                print("SerialBusDevice.address = " + str(configSensor["SerialBusDevice.address"]))
            else:
                print("SerialBusDevice.address not set.")
            err = sensor.open( configSensor )
            if (err == ErrorCode.errOk):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
            #traceback.print_exc()
    return None

def sclose():
    global sensor
    if (sensor is None):
        print("Sensor is not instantiated!")
    else:
        try:
            err = sensor.close()
            if (err == ErrorCode.errOk):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
    return None

def getInfo():
    global sensor
    if not (sensor is None):
        info, err = sensor.getInfo()
        if (err == ErrorCode.errOk):
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
        else:
            print("Error: ", err)
    else:
        print("Sensor is not open!")
    return None

def _dumpStatus( id=0, format=0 ):
    global sensor
    status, err = sensor.getStatus( id )
    if (err == ErrorCode.errOk):
        if (format=="hex"):
            print(f"{id}:", hex(status) )
        else:
            print(f"{id}: {status}.")
    else:
        print(f"{id}: Error {err}.")
    return None
    
def getStatus():
    global sensor
    if (sensor is None):
        print("Sensor is not open!")
    else:
        _dumpStatus( id=StatusID.dieTemp, format="hex" )
        _dumpStatus( id=StatusID.dataReady )
        _dumpStatus( id=StatusID.interrupt )
        _dumpStatus( id=StatusID.fifo )
        _dumpStatus( id=StatusID.error, format="hex" )
        _dumpStatus( id=StatusID.activity )
        _dumpStatus( id=StatusID.stepCount )
        _dumpStatus( id=StatusID.highG )
        _dumpStatus( id=StatusID.highSlope )
        _dumpStatus( id=StatusID.orientation )
        _dumpStatus( id=StatusID.tap )
        _dumpStatus( id=StatusID.NVM )
        _dumpStatus( id=StatusID.sensorTime )
    return None

def startMeasurements():
    global sensor
    if sensor is None:
        print("Sensor is not open!")
    else:
        print("Press Enter to stop measurements and return to menu!")
        thr = Thread( target = thrInputKey, name="Keyboard observer" )
        thr.start()
        done = False
        while not done:
            mdata, err = sensor.getNextData()
            now = time.time()
            if (err == ErrorCode.errOk):
                print(now, mdata)
            else:
                print("Error ", err)
            done = not thr.is_alive()
    return None

#
#
#
def main():
    global sensor, configSensor
    sensor = sensorDriver()
    sensorDriver.Params_init( configSensor )
    
    title = "Sensor test application"
    options = ["Settings", "Open", "Close", "Info", "Status", "Measurements", "Exit"]
    menu = TerminalMenu( options, title=title )

    done = False
    while not done:
        selection = menu.show()
        if (selection == 0):
            settings()
        elif (selection == 1):
            sopen()
        elif (selection == 2):
            sclose()
        elif (selection == 3):
            getInfo()
        elif (selection == 4):
            getStatus()
        elif (selection == 5):
            startMeasurements()
        else:
            done = True
    print("Done.")


#
# Global variables
#
sensor = None
flagInterrupt = 0
timeInterrupt = 0
currentEvent = None
### sensor driver settings ###
configSensor = {
    #"SerialBus.busType"      : SerialBusType.I2C,
    #   RaspberryPi needs "/dev/i2c-1", while Google Coral has "/dev/i2c-3".
    #   SMBus implementation needs integers (1,3), while the periphery module takes strings.
    "SerialBus.designator": "/dev/i2c-1",
    #"SerialBus.provider": SerialBusProvider.AUTO, 
    "SerialBusDevice.address": 0x18,
    "Sensor.dataRange"    : 4000,
    "Sensor.dataRate"     : 100,
    #    BMA456.int1.gpio.pinDesginator names the interrupt pin. Note that pin numbering
    #    refers to the BOARD numbering scheme. So, pin numbers of the GPIO expansion header
    #    are expected.
    #      BCM          BCM       BOARD
    #      Coral        RasPi     HdrPin#  ClickShield    Accel11Click    BMA456
    #      GPIO22       GPIO4        7     AN1 port 1        AN           INT1
    #      (UART_RX)    GPIO6       31     INT port 1        INT          INT2
    #      (PWM_B)      GPIO13      33     AN2 port 2        AN           INT1
    #      GPIO45       GPIO26      37     INT port 2        INT          INT2
    #"BMA456.int1.gpio.pinNumbering":   GPIO.PINNUMBERING_BCM,	# {BCM | BOARD}
    "BMA456.int1.gpio.pinDesignator":   4,
    #"BMA456.int1.gpio.direction":    GPIO.DIRECTION_IN,
    #"BMA456.int1.gpio.level":   GPIO.LEVEL_LOW,
    #"BMA456.int1.gpio.pull":    GPIO.PULL_NONE,
    "BMA456.int1.gpio.trigger": GPIO.TRIGGER_EDGE_FALLING,
    #"BMA456.int1.gpio.bounce":  GPIO.BOUNCE_NONE,
    "BMA456.int1.gpio.feedback":  Event.evtInt1,
    "BMA456.int1.gpio.handler":  callback,
    #"BMA456.INT1_IO_CTRL": sensorDriver.BMA456_CNT_INT1_IO_CTRL_DEFAULT,
    #"BMA456.INT1_MAP": sensorDriver.BMA456_CNT_INTX_MAP_DEFAULT,
    #"BMA456.int2.gpio.pinDesignator":   31,
    #"BMA456.int2.gpio.direction":    GPIO.DIRECTION_IN,
    #"BMA456.int2.gpio.level":   GPIO.LEVEL_LOW,
    #"BMA456.int2.gpio.pull":    GPIO.PULL_NONE,
    #"BMA456.int2.gpio.trigger": GPIO.TRIGGER_EDGE_FALLING,
    #"BMA456.int2.gpio.bounce":  GPIO.BOUNCE_NONE,
    #"BMA456.int2.gpio.feedback":  None,
    #"BMA456.int2.gpio.handler":  None,
    #"BMA456.INT2_IO_CTRL": sensorDriver.BMA456_CNT_INT2_IO_CTRL_DEFAULT,
    #"BMA456.INT2_MAP": sensorDriver.BMA456_CNT_INTX_MAP_DEFAULT,
    "BMA456.INT_MAP_DATA": 0xFF,
}


if __name__ == "__main__":
    main()
