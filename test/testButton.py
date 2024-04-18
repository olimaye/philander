# Sample application for the Button driver
from philander.gpio import GPIO
from philander.button import Button
from philander.systypes import ErrorCode, Info

from simple_term_menu import TerminalMenu

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
            if (err == ErrorCode.errOk):
                print("Success!")
                button.on( Button.EVENT_PRESSED, hdlButtonPressed )
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
            #traceback.print_exc()
    return None

def close():
    global button
    if (button is None):
        print("Button is not instantiated!")
    else:
        try:
            err = button.close()
            if (err == ErrorCode.errOk):
                print("Success!")
            else:
                print("Error: ", err)
        except Exception as exc:
            print("Exception:", exc)
    return None

def main():
    global button, setup
    
    button = Button()
    Button.Params_init( setup )
    
    title = "Button test application"
    options = ["Settings", "Open", "Close", "Exit"]
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
            done = True
    
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
