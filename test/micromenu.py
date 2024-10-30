"""A module to support application development by a textual menu UI.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Level", "Capacity", "Status"]

import sys

class MicroMenu():
    
    _optionKeys="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    def __init__(self, options, title="Menu", addExit=False):
        self.options = options
        self.title = title
        self.addExit = addExit
        
    def show(self):
        ret = None
        
        print( self.title )
        idx = 0
        for item in self.options:
            print( "  ", MicroMenu._optionKeys[idx], ": ", item)
            idx += 1
            if (idx >= len(MicroMenu._optionKeys)):
                break;
        if self.addExit:
            print( "  ESC: Back/Exit" )
        
        done = False
        while not done:
            key = sys.stdin.read(1)
            if( len(key) < 1):
                done = True
            elif (ord(key)==27):   # ESC
                ret = None
                done = True
            else:
                idx = MicroMenu._optionKeys.find(key)
                if (idx>=0) and (idx<len(self.options)):
                    ret = idx
                    done = True
            
        return ret
    
def main():
    title = "Menu test application"
    options = ["Settings", "Open", "Close", "On", "Off", \
               "Brightness", "Blink", "Stop"]
    menu = MicroMenu( options, title=title, addExit=True )
    
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
