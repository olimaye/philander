"""
"""
from time import sleep
import unittest

from philander.gpio import GPIO
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

def hasImpl( moduleName, className ):
    ret = False
    try:
        #                       name,  globals, locals, fromlist
        module = __import__( moduleName, None, None, [className,] )
        ret = hasattr(module, className)
    except ImportError:
        ret = False
    return ret
        
class TestGPIO( unittest.TestCase ):
    
    def test_factory(self):
        deps = [(SysProvider.RPIGPIO, "RPi.GPIO", "setup"),
                (SysProvider.GPIOZERO, "gpiozero", "DigitalOutputDevice"),
                (SysProvider.PERIPHERY, "periphery", "GPIO"),
                (SysProvider.MICROPYTHON, "machine", "Pin"),
                ]
        for dep in deps:
            pin = GPIO.getGPIO( dep[0] )
            if hasImpl( dep[1], dep[2] ):
                self.assertIsNotNone(pin, f"Implementation {dep[0]} not found!")
            else:
                self.assertIsNone(pin, f"Implementation {dep[0]} not installed!")
        
    #@unittest.skip("Disabled for easier development.")
    def test_output(self):
        pin = GPIO.getGPIO()
        self.assertIsNotNone( pin )
        gpioParams = {\
            "gpio.pinDesignator":   17,
            "gpio.direction"    :   GPIO.DIRECTION_OUT,
            "gpio.level"        :   GPIO.LEVEL_LOW,
            }
        GPIO.Params_init( gpioParams )
        self.assertEqual( gpioParams["gpio.pinDesignator"], 17 )
        self.assertEqual( gpioParams["gpio.direction"], GPIO.DIRECTION_OUT )
        self.assertEqual( gpioParams["gpio.level"], GPIO.LEVEL_LOW )
        err = pin.open(gpioParams)
        self.assertEqual( err, ErrorCode.errOk )
        self.assertEqual( pin.get(), 0 )
        err = pin.set( GPIO.LEVEL_HIGH )
        self.assertEqual( err, ErrorCode.errOk )
        self.assertEqual( pin.get(), 1 )
        err = pin.set( GPIO.LEVEL_LOW )
        self.assertEqual( err, ErrorCode.errOk )
        self.assertEqual( pin.get(), 0 )
        err = pin.close()
        self.assertEqual( err, ErrorCode.errOk )
        
    #@unittest.skip("Disabled for easier development.")
    def test_input(self):
        pin = GPIO.getGPIO()
        self.assertIsNotNone( pin )
        gpioParams = {\
            "gpio.pinDesignator":   17,
            "gpio.direction"    :   GPIO.DIRECTION_IN,
            "gpio.pull"         :   GPIO.PULL_UP,
            }
        GPIO.Params_init( gpioParams )
        self.assertEqual( gpioParams["gpio.pinDesignator"], 17 )
        self.assertEqual( gpioParams["gpio.direction"], GPIO.DIRECTION_IN )
        self.assertEqual( gpioParams["gpio.pull"], GPIO.PULL_UP )
        err = pin.open(gpioParams)
        self.assertEqual( err, ErrorCode.errOk )
        value = pin.get()
        print("value: ", value)
        print("Waiting 2 seconds for the input to change...")
        sleep(2)
        newValue = pin.get()
        self.assertTrue( value ^ newValue, f"Input value didn't change: {value}->{newValue}!" )
        err = pin.close()
        self.assertEqual( err, ErrorCode.errOk )
        
if __name__ == '__main__':
    unittest.main()

