# Sample application for the Button driver
from philander.gpio import GPIO
from philander.button import Button
from philander.systypes import ErrorCode, Info

try:
    from simple_term_menu import TerminalMenu
except ImportError as exc:
    from micromenu import MicroMenu as TerminalMenu

def hdlButtonPressed( lbl ):
    print("Button <", lbl, "> pressed.")

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
    global button, setup
    if (button is None):
        print("Button is not instantiated!")
    else:
        print("Trying to open the Button <", setup["Button.label"], "> with the following settings:")
        try:
            if ("Button.gpio.pinDesignator" in setup):
                print("Button.gpio.pinDesignator = " + str(setup["Button.gpio.pinDesignator"]))
            else:
                print("Button.gpio.pinDesignator not set.")
            err = button.open( setup )
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
    global button
    if (button is None):
        print("Button is not instantiated!")
    else:
        try:
            err = button.close()
            if (err.isOk()):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print(f"Exception ({exc.__class__.__name__}): {exc}")
    return None

def main():
    global button, setup
    
    button = Button()
    button.on( Button.EVENT_PRESSED, hdlButtonPressed )
    Button.Params_init( setup )
    
    title = "Button test application"
    options = ["Settings", "Open", "Close"]
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
    
    button.close()
    print("Done.")
            
#
# Global variables
#
button = None
setup = {
    "Button.label":    "Test Button",
    #"Button.gpio.pinNumbering" : GPIO.PINNUMBERING_BCM,
    "Button.gpio.pinDesignator": 39,
}

if __name__ == "__main__":
    main()
