"""
"""
from time import sleep
import unittest

from philander.adc import ADC
from philander.sysfactory import SysFactory, SysProvider
from philander.systypes import ErrorCode

class TestADC_Impl( unittest.TestCase ):

    #ProviderUnderTest = SysProvider.MICROPYTHON
    ProviderUnderTest = SysProvider.COMPOSITE
    PortDesignator = 0  # "/dev/spidev0.1"
    CS_Pin = 17
    Channel = 1
    VRefLow = 0
    VRefHigh= 3300
    
    def test_open(self):
        device = SysFactory.getADC( self.ProviderUnderTest )
        self.assertIsNotNone( device )
        params = {\
            "SerialBus.designator":   self.PortDesignator,
            "SerialBusDevice.CS.gpio.pinDesignator": self.CS_Pin,
            "adc.channel"    :   self.Channel,
            "adc.vref.lower" :   self.VRefLow,
            "adc.vref.upper" :   self.VRefHigh,
            }
        device.Params_init( params )
        self.assertEqual( params["adc.channel"], self.Channel )
        #self.assertEqual( params["adc.samplingTime"], 2 )
        self.assertEqual( params["adc.vref.lower"], self.VRefLow )
        self.assertEqual( params["adc.vref.upper"], self.VRefHigh )
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk, "Open: " + str(err) )
        self.assertEqual( device.channel, self.Channel )
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )

    #@unittest.skip("Known working.")
    def test_input(self):
        device = SysFactory.getADC( self.ProviderUnderTest )
        self.assertIsNotNone( device )
        params = {\
            "SerialBus.designator":   self.PortDesignator,
            "SerialBusDevice.CS.gpio.pinDesignator": self.CS_Pin,
            "adc.channel"    :   self.Channel,
            "adc.vref.lower" :   self.VRefLow,
            "adc.vref.upper" :   self.VRefHigh,
            }
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk, "Open: " + str(err) )
        print()
        total = 5
        print("Monitoring the input.")
        for cnt in range(total):
            dvalue, err = device.getDigital()
            self.assertEqual( err, ErrorCode.errOk, "getDigital: "+str(err) )
            compVolt, err = device.toVoltage( dvalue )
            self.assertEqual( err, ErrorCode.errOk, "toVoltage: "+str(err) )
            print("d#", (cnt+1),"/", total, ": digital value=", dvalue,
                  " (", hex(dvalue),")  corr.voltage=", compVolt, " mV.", sep='')
            
            volt, err = device.getVoltage()
            self.assertEqual( err, ErrorCode.errOk, "getVolt: "+str(err) )
            print("a#", (cnt+1),"/", total, ": voltage=", volt, " mV.", sep='')
            sleep(1)
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )
    
        
if __name__ == '__main__':
    unittest.main()

