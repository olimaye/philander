"""
"""
from time import sleep
import unittest

from philander.gpio import GPIO
from philander.mux import Mux
from philander.systypes import ErrorCode

# Globals
gMuxParams = {\
    "mux.gpio.level"        :   GPIO.LEVEL_LOW,
    "mux.bit0.gpio.pinDesignator":   23,
    "mux.bit1.gpio.pinDesignator":   24,
    "mux.bit2.gpio.pinDesignator":   25,
    "mux.enable.gpio.pinDesignator":   26,
}

class TestMux( unittest.TestCase ):
    
    #@unittest.skip("Disabled for easier diagnostics.")
    def test_params(self):
        mux = Mux()
        self.assertIsNotNone( mux )
        muxParams = gMuxParams.copy()
        Mux.Params_init( muxParams )
        self.assertEqual( muxParams["mux.gpio.direction"], GPIO.DIRECTION_OUT )
        self.assertFalse( muxParams["mux.gpio.inverted"] )
        self.assertEqual( muxParams["mux.gpio.level"], GPIO.LEVEL_LOW )
        self.assertEqual( muxParams["mux.bit0.gpio.pinDesignator"], gMuxParams["mux.bit0.gpio.pinDesignator"] )
        self.assertEqual( muxParams["mux.bit0.gpio.direction"], GPIO.DIRECTION_OUT )
        self.assertFalse( muxParams["mux.bit1.gpio.inverted"] )
        self.assertEqual( muxParams["mux.bit2.gpio.level"], GPIO.LEVEL_LOW )
        
    @unittest.skip("Disabled for easier diagnostics.")
    def test_select(self):
        mux = Mux()
        self.assertIsNotNone( mux )
        muxParams = gMuxParams.copy()
        err = mux.open(muxParams)
        self.assertEqual( err, ErrorCode.errOk )
        
        err = mux.select(0)
        self.assertEqual( err, ErrorCode.errOk )
        err = mux.enable(True)
        self.assertEqual( err, ErrorCode.errOk )
        sleep(2)
        err = mux.enable(False)
        self.assertEqual( err, ErrorCode.errOk )
        sleep(1)
        err = mux.enable(True)
        self.assertEqual( err, ErrorCode.errOk )
        sleep(2)
        err = mux.disable()
        self.assertEqual( err, ErrorCode.errOk )
        sleep(1)
        
        for idx in range(8):
            err = mux.select( idx )
            self.assertEqual( err, ErrorCode.errOk )
            sleep(1)
        for idx in range(8):
            err = mux.select( idx, automute=True )
            self.assertEqual( err, ErrorCode.errOk )
            sleep(1)
            

        err = mux.close()
        self.assertEqual( err, ErrorCode.errOk )
        
        
if __name__ == '__main__':
    unittest.main()
