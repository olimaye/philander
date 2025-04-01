"""
"""
import unittest

from philander.adc import ADC
from philander.systypes import ErrorCode

class TestADC( unittest.TestCase ):
    
    def test_open(self):
        device = ADC()
        self.assertIsNotNone( device )
        vrefLow = -700
        vrefHigh= 3000
        channel = 1
        params = {\
            "adc.channel"    :   channel,
            #"adc.samplingTime":  2,
            "adc.vref.lower" :   vrefLow,
            "adc.vref.upper" :   vrefHigh,
            }
        ADC.Params_init( params )
        self.assertEqual( params["adc.channel"], channel )
        #self.assertEqual( params["adc.samplingTime"], 2 )
        self.assertEqual( params["adc.vref.lower"], vrefLow )
        self.assertEqual( params["adc.vref.upper"], vrefHigh )
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk, "Open: " + str(err) )
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )

    #@unittest.skip("Known working.")
    def test_input(self):
        device = ADC()
        self.assertIsNotNone( device )
        params = {\
            "adc.channel"    :   1,
            "adc.vref.lower" :   0,
            "adc.vref.upper" :   3300,
            }
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk )
        total = 5
        for _ in range(total):
            _, err = device.getDigital()
            self.assertEqual( err, ErrorCode.errNotImplemented )
            _, err = device.getVoltage()
            self.assertEqual( err, ErrorCode.errNotImplemented )
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )
    
    #@unittest.skip("Known working.")
    def test_conversion(self):
        device = ADC()
        self.assertIsNotNone( device )
        vref = [(0,100), (0, 1000), (0, 3000),
                (800, 1700), (137, 12906),
                (-1000, 5000), (-837, 2417),
                (-5036, -1301), (-50132, -67) ]
        params = { "adc.channel": 1, }
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk )
        for (lo, hi) in vref:
            device.vref_lower = lo
            device.vref_upper = hi
            for dval in range( 0, 0x10000, 0x123 ):
                val1 = dval * (hi-lo) / ADC.DIGITAL_MAX + lo
                val2, err = device.toVoltage( dval )
                self.assertEqual( err, ErrorCode.errOk )
                self.assertAlmostEqual( val1, val2, delta=0.5,
                    msg="dval="+str(dval)+", vref["+str(lo)+","+str(hi)+"]" )
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )
                
        
if __name__ == '__main__':
    unittest.main()

