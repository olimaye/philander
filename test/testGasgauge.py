from time import sleep
from philander.serialbus import SerialBusDevice
from philander.systypes import ErrorCode

# Replace this with any other gasgauge to test (conf might need to be adjusted accordingly)
from philander.stc3115 import STC3115 as gasgauge
from philander.primitives import Percentage

def main():
    conf = {
        }
    
    gg = gasgauge()
    err = gg.open(conf)
    print(f"open: {err}")
    
    print(gg.getInfo())    

    print("Closing connection.")
    gg.close()

if __name__ == "__main__":
    main()

