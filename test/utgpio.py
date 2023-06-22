"""
"""
import unittest
from gpio import *
from systypes import ErrorCode
from time import sleep

class TestGPIO( unittest.TestCase ):
    
    def test_output(self):
        pin = GPIO()
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
        
    def test_input(self):
        pin = GPIO()
        self.assertIsNotNone( pin )
        gpioParams = {\
            "gpio.pinDesignator":   17,
            "gpio.direction"    :   GPIO.DIRECTION_IN,
            "gpio.pull"         :   GPIO.PULL_NONE,
            }
        GPIO.Params_init( gpioParams )
        self.assertEqual( gpioParams["gpio.pinDesignator"], 17 )
        self.assertEqual( gpioParams["gpio.direction"], GPIO.DIRECTION_IN )
        self.assertEqual( gpioParams["gpio.pull"], GPIO.PULL_NONE )
        err = pin.open(gpioParams)
        self.assertEqual( err, ErrorCode.errOk )
        value = pin.get()
        if (pin._implpak == GPIO._IMPLPAK_SIM):
            self.assertGreaterEqual( value, 0 )
        else:
            print("value: ", value)
            print("Waiting 3 seconds for the input to change...")
            sleep(3)
            newValue = pin.get()
            self.assertTrue( value ^ newValue, "Input value didn't change!" )
        err = pin.close()
        self.assertEqual( err, ErrorCode.errOk )
        
if __name__ == '__main__':
    unittest.main()

