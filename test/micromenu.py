"""A module to support application development by a textual menu UI.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Level", "Capacity", "Status"]

import sys

class MicroMenu():
    
    def __init__(self, options, title):
        self.options = options
        self.title = title
        
    def show(self):
        ret = None
        
        print( self.title )
        idx = 0
        for item in self.options:
            print( "  ", idx, ": ", item)
            idx += 1
        print( "  ESC: Back" )
        
        done = False
        while not done:
            key = sys.stdin.read(1)
            if( len(key) < 1):
                done = True
            else:
                key = ord(key)
                if (key==27):
                    ret = None
                    done = True
                elif( key >= 0x20 ):
                    key -= ord('0')
                    if (key>=0) and (key<len(self.options)):
                        ret = key
                        done = True
            
        return ret
    
def main():
    title = "Menu test application"
    options = ["Settings", "Open", "Close", "On", "Off", \
               "Brightness", "Blink", "Stop"]
    menu = MicroMenu( options, title=title )
    
    done = False
    while not done:
        selection = menu.show()
        if( selection is None ):
            print("Exiting...")
            done = True
        else:
            print("Selected: ", selection)
    
    print("Done.")
            
if __name__ == "__main__":
    main()
