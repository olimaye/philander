# Sample application for the LED driver
from philander.fastgait.actorunit import ActorUnit as Driver, Configuration, Motor, TimerControl
from philander.actuator import Actuator
from philander.systypes import ErrorCode, Info
from philander.ble import BLE, Event

from simple_term_menu import TerminalMenu
import traceback

def bleDisconnected( feedback, *args):
    print("BLE: Disconnected.")
    
def bleDiscovering( feedback, *args):
    print("BLE: Discovering...")
    
def bleConnected( feedback, *args):
    print("BLE: Connected!")
    
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
    global device, setup
    if (device is None):
        print("Actuator is not instantiated!")
    else:
        print("Trying to open the actuator with the following settings:")
        try:
            print("BLE.client.name         = " + str(setup.get("BLE.client.name")))
            print("BLE.characteristic.uuid = " + str(setup.get("BLE.characteristic.uuid")))
            
            err = device.open( setup )
            if (err == ErrorCode.errOk):
                device.registerInterruptHandler( onEvent = Event.bleDisconnected, handler=bleDisconnected )
                device.registerInterruptHandler( onEvent = Event.bleDiscovering, handler=bleDiscovering )
                device.registerInterruptHandler( onEvent = Event.bleConnected, handler=bleConnected )
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
            #traceback.print_exc()
    return None

def close():
    global device
    if (device is None):
        print("Actuator is not instantiated!")
    else:
        try:
            err = device.close()
            if (err == ErrorCode.errOk):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
    return None

def couple():
    global device
    if (device is None):
        print("Actuator is not instantiated!")
    elif (device.isCoupled() == ErrorCode.errOk):
        print("Actuator is already coupled!")
    else:
        try:
            err = device.couple()
            if (err == ErrorCode.errOk):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
    return None

def decouple():
    global device
    if (device is None):
        print("Actuator is not instantiated!")
    elif not (device.isCoupled() == ErrorCode.errOk):
        print("Actuator is not coupled!")
    else:
        try:
            err = device.decouple()
            if (err == ErrorCode.errOk):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
    return None

def getHWDefaults():
    global device
    if (device is None):
        print("Actuator is not instantiated!")
    elif not (device.isCoupled() == ErrorCode.errOk):
        print("Actuator is not coupled!")
    else:
        try:
            cfg, err = device.getDefault()
            if (err == ErrorCode.errOk):
                print("Hardware defaults")
                print("1st delay:", cfg.delay, "ms")
                print("Period   :", cfg.period, "ms")
                print("On duty  :", cfg.onDuration, "ms")
                print("#Pulses  :", cfg.numPulses)
                print("Intensity:", cfg.intensity, "%")
                print("Motors   :", cfg.motors)
                print("TimerCtrl:", cfg.resetTimer)
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
    return None

def action():
    global device
    if (device is None):
        print("Actuator is not instantiated!")
    elif not (device.isCoupled() == ErrorCode.errOk):
        print("Actuator is not coupled!")
    else:
        try:
            err = device.action()
            if (err == ErrorCode.errOk):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
    return None

def stop():
    global device
    if (device is None):
        print("Actuator is not instantiated!")
    elif not (device.isCoupled() == ErrorCode.errOk):
        print("Actuator is not coupled!")
    else:
        try:
            err = device.stopOperation()
            if (err == ErrorCode.errOk):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
    return None

def runAdjustDriver():
    global device, cfgDriver
    if (device is None):
        print("Actuator is not instantiated!")
    elif not (device.isCoupled() == ErrorCode.errOk):
        print("Actuator is not coupled!")
    else:
        title = "Run/adjust driver"
        paramLabel = [ "Delay    : ", "Period   : ", "OnDuty   : ", \
                       "#Pulses  : ", "Intensity: ", "Motors   : ", \
                       "TimerCtrl: ",]
        options = [paramLabel[0] + str(cfgDriver.delay), \
                   paramLabel[1] + str(cfgDriver.period), \
                   paramLabel[2] + str(cfgDriver.onDuration), \
                   paramLabel[3] + str(cfgDriver.numPulses), \
                   paramLabel[4] + str(cfgDriver.intensity), \
                   paramLabel[5] + str(cfgDriver.motors), \
                   paramLabel[6] + str(cfgDriver.resetTimer), \
                   "Start", "Stop", "Set as HW default", ]
        
        done = False
        while not done:
            menu = TerminalMenu( options, title=title )
            selection = menu.show()
            try:
                if (selection is None):
                    done = True
                elif (0 <= selection) and (selection<=6):
                    val = input("New value: ")
                    val = val.strip()
                    if val:
                        try:
                            numVal = int(val)
                            options[selection] = paramLabel[selection] + str(numVal)
                            if (selection == 0):
                                cfgDriver.delay = numVal
                            elif (selection == 1):
                                cfgDriver.period = numVal
                            elif (selection == 2):
                                cfgDriver.onDuration = numVal
                            elif (selection == 3):
                                cfgDriver.numPulses = numVal
                            elif (selection == 4):
                                cfgDriver.intensity = numVal
                            elif (selection == 5):
                                cfgDriver.motors = Motor(numVal)
                                options[selection] = paramLabel[selection] + str(cfgDriver.motors)
                            elif (selection == 6):
                                cfgDriver.resetTimer = TimerControl(numVal)
                                options[selection] = paramLabel[selection] + str(cfgDriver.resetTimer)
                        except ValueError:
                            pass
                elif (selection == 7):
                    err = device.configure( cfgDriver )
                    if (err == ErrorCode.errOk):
                        err = device.startOperation()
                        if (err == ErrorCode.errOk):
                            print("Success!")
                        else:
                            print("Run error: ", err)
                    else:
                        print("Configuration error: ", err)
                elif (selection == 8):
                    err = device.stopOperation()
                    if (err == ErrorCode.errOk):
                        print("Success!")
                    else:
                        print("Error: ", err)
                elif (selection == 9):
                    err = device.setDefault( cfgDriver )
                    if (err == ErrorCode.errOk):
                        print("Success!")
                    else:
                        print("Error: ", err)
                    
            except Exception as exc:
                print("Exception:", exc)
    return None

def runAdjustApp():
    global device, cfgApp
    if (device is None):
        print("Actuator is not instantiated!")
    elif not (device.isCoupled() == ErrorCode.errOk):
        print("Actuator is not coupled!")
    else:
        title = "Run/adjust app"
        paramLabel = [ "Period   : ", "OnDuty   : ", \
                       "#Pulses  : ", "Intensity: ",]
        options = [paramLabel[0] + str(cfgApp.period), \
                   paramLabel[1] + str(cfgApp.onDuration), \
                   paramLabel[2] + str(cfgApp.numPulses), \
                   paramLabel[3] + str(cfgApp.intensity), \
                   "Start", "Stop", ]
        
        done = False
        while not done:
            menu = TerminalMenu( options, title=title )
            selection = menu.show()
            try:
                if (selection is None):
                    done = True
                elif (0 <= selection) and (selection<=3):
                    val = input("New value: ")
                    val = val.strip()
                    if val:
                        try:
                            numVal = int(val)
                            options[selection] = paramLabel[selection] + str(numVal)
                            if (selection == 0):
                                cfgApp.period = numVal
                            elif (selection == 1):
                                cfgApp.onDuration = numVal
                            elif (selection == 2):
                                cfgApp.numPulses = numVal
                            elif (selection == 3):
                                cfgApp.intensity = numVal
                        except ValueError:
                            pass
                elif (selection == 4):
                    err = device.startOperation( strengthIntensity=cfgApp.intensity,
                                                 onSpeedDuty=cfgApp.onDuration,
                                                 ctrlInterval=cfgApp.period,
                                                 durationLengthCycles=cfgApp.numPulses )
                    if (err == ErrorCode.errOk):
                        print("Success!")
                    else:
                        print("Error: ", err)
                elif (selection == 5):
                    err = device.stopOperation()
                    if (err == ErrorCode.errOk):
                        print("Success!")
                    else:
                        print("Error: ", err)
                    
            except Exception as exc:
                print("Exception:", exc)
    return None


def main():
    global device, setup, cfgDriver, cfgApp
    
    device = Driver()
    Driver.Params_init( setup )
    cfgDriver = Configuration()
    cfgApp = Configuration()
    
    title = "FastGait ActorUnit test application"
    options = ["Startup settings", "Open", "Close", \
               "Couple", "Decouple", \
               "Show HW defaults", "Action (HW defaults)", "Stop", \
               "Run/adjust driver", \
               "Run/adjust app", \
               "Exit"]
    menu = TerminalMenu( options, title=title )
    
    done = False
    while not done:
        selection = menu.show()
        if selection is None:
            done = True
        elif (selection == 0):
            settings()
        elif (selection == 1):
            open()
        elif (selection == 2):
            close()
        elif (selection == 3):
            couple()
        elif (selection == 4):
            decouple()
        elif (selection == 5):
            getHWDefaults()
        elif (selection == 6):
            action()
        elif (selection == 7):
            stop()
        elif (selection == 8):
            runAdjustDriver()
        elif (selection == 9):
            runAdjustApp()
        elif (selection == 10):
            done = True
    
    device.close()
    print("Done.")
            
#
# Global variables
#
device = None
setup = {
    "BLE.discovery.timeout" : BLE.DISCOVERY_TIMEOUT,
    #"BLE.client.name"       : Driver.CLIENT_NAME,        
    #"BLE.characteristic.uuid": Driver.CHARACTERISTIC_UUID,
    #"ActorUnit.delay"           : Driver.DELAY_DEFAULT,
    #"ActorUnit.pulsePeriod"     : Driver.PULSE_PERIOD_DEFAULT,
    #"ActorUnit.pulseOn"         : Driver.PULSE_ON_DEFAULT,
    #"ActorUnit.pulseCount"      : Driver.PULSE_COUNT_DEFAULT,
    #"ActorUnit.pulseIntensity"  : Driver.PULSE_INTENSITY_DEFAULT,
    #"ActorUnit.actuators"       : Driver.ACTUATORS_DEFAULT,
}
cfgDriver = None
cfgApp = None

if __name__ == "__main__":
    main()
