"""
"""
from time import sleep
import unittest

from philander.adc import ADC
from philander.sysfactory import SysFactory, SysProvider
from philander.systypes import ErrorCode

class TestADC( unittest.TestCase ):
    
    def test_open(self):
        device = SysFactory.getADC()
        self.assertIsNotNone( device )
        vrefLow = -700
        vrefHigh= 3000
        params = {\
            "adc.pinDesignator": 1,
            "adc.samplingTime":  2,
            "adc.vref.lower" :   vrefLow,
            "adc.vref.upper" :   vrefHigh,
            }
        ADC.Params_init( params )
        self.assertEqual( params["adc.pinDesignator"], 1 )
        self.assertEqual( params["adc.samplingTime"], 2 )
        self.assertEqual( params["adc.vref.lower"], vrefLow )
        self.assertEqual( params["adc.vref.upper"], vrefHigh )
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk )
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )

    def test_input(self):
        device = SysFactory.getADC()
        self.assertIsNotNone( device )
        params = {\
            "adc.pinDesignator": 1,
            "adc.vref.lower" :   0,
            "adc.vref.upper" :   3000,
            }
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk )
        total = 5
        for cnt in range(total):
            dvalue, err = device.getDigital()
            self.assertEqual( err, ErrorCode.errOk )
            volt, err = device.getVoltage()
            self.assertEqual( err, ErrorCode.errOk )
            print("#", (cnt+1),"/", total, ": digital value=", dvalue,
                  " (", hex(dvalue),")  voltage=", volt, " mV.", sep='')
            print("Waiting 2 seconds for the input to change...")
            sleep(2)
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )
        
    def test_conversion(self):
        device = SysFactory.getADC( SysProvider.SIM )
        self.assertIsNotNone( device )
        vref = [(0,100), (0, 1000), (0, 3000),
                (800, 1700), (137, 12906),
                (-1000, 5000), (-837, 2417),
                (-5036, -1301), (-50132, -67) ]
        params = { "adc.pinDesignator": 1, }
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk )
        for (lo, hi) in vref:
            device.vref_lower = lo
            device.vref_upper = hi
            for dval in range( 0x10000 ):
                val1 = dval * (hi-lo) / ADC.DIGITAL_MAX + lo
                val2, err = device.toVoltage( dval )
                self.assertEqual( err, ErrorCode.errOk )
                self.assertAlmostEqual( val1, val2, delta=0.5,
                    msg="dval="+str(dval)+", vref["+str(lo)+","+str(hi)+"]" )
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )
                
        
if __name__ == '__main__':
    unittest.main()

