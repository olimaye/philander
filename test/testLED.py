# Sample application for the LED driver
from philander.gpio import GPIO
from philander.led import LED
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

def open():
    global led, setup
    if (led is None):
        print("LED is not instantiated!")
    else:
        print("Trying to open the LED <", setup["LED.label"], "> with the following settings:")
        try:
            if ("LED.gpio.pinDesignator" in setup):
                print("LED.gpio.pinDesignator = " + str(setup["LED.gpio.pinDesignator"]))
            else:
                print("LED.gpio.pinDesignator not set.")
            if ("LED.gpio.level" in setup):
                print("LED.gpio.level = " + str(setup["LED.gpio.level"]))
            else:
                print("LED.gpio.level not set.")
            err = led.open( setup )
            if (err.isOk()):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
            #traceback.print_exc()
    return None

def close():
    global led
    if (led is None):
        print("LED is not instantiated!")
    else:
        try:
            err = led.close()
            if (err.isOk()):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
    return None

def brightness():
    global led
    if (led is None):
        print("LED is not instantiated!")
    else:
        title = "Select brightness"
        options = ["  0 %", " 10 %", " 20 %", " 30 %", " 40 %", " 50 %" \
                   " 60 %", " 70 %", " 80 %", " 90 %", "100 %"]
        menu = TerminalMenu( options, title=title )
        
        done = False
        while not done:
            selection = menu.show()
            if (selection is None):
                done = True
            else:
                level = selection / 10
                print(f"Setting brightness to {level} - ", end="")
                try:
                    err = led.set( level )
                    print("Success!")
                except Exception as exc:
                    print("Exception:", exc)
    return None

def blink():
    global led
    if (led is None):
        print("LED is not instantiated!")
    else:
        title = "Select pattern"
        options = ["Classic, slow (3x)", " 10 %", " 20 %", " 30 %", " 40 %", " 50 %" \
                   " 60 %", " 70 %", " 80 %", " 90 %", "100 %"]
        menu = TerminalMenu( options, title=title )
        
        done = False
        while not done:
            selection = menu.show()
            if (selection is None):
                done = True
            else:
                if (selection == 0):
                    curve = LED.CURVE_BLINK_CLASSIC
                    length = LED.CYCLEN_SLOW
                    num = 3
                try:
                    err = led.blink( curve, length, num )
                    print("Success!")
                except Exception as exc:
                    print("Exception:", exc)
    return None

def main():
    global led, setup
    
    led = LED()
    LED.Params_init( setup )
    
    title = "LED test application"
    options = ["Settings", "Open", "Close", "On", "Off", \
               "Brightness", "Blink", "Stop", "Exit"]
    menu = TerminalMenu( options, title=title )
    
    done = False
    while not done:
        selection = menu.show()
        if (selection == 0):
            settings()
        elif (selection == 1):
            open()
        elif (selection == 2):
            close()
        elif (selection == 3):
            led.on()
        elif (selection == 4):
            led.off()
        elif (selection == 5):
            brightness()
        elif (selection == 6):
            blink()
        elif (selection == 7):
            led.stop_blinking()
        elif (selection == 8):
            done = True
    
    led.close()
    print("Done.")
            
#
# Global variables
#
led = None
setup = {
    "LED.label":    "Test light",
    #"LED.gpio.pinNumbering" : GPIO.PINNUMBERING_BCM,
    "LED.gpio.pinDesignator": 17,
    "LED.gpio.level"        : GPIO.LEVEL_LOW,        
}

if __name__ == "__main__":
    main()
