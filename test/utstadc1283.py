"""
"""
from time import sleep
import unittest

from philander.stadc1283 import STADC1283 as Driver
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

config = {\
    # Pi 3 click board, port 0.
    "SerialBus.designator":   "/dev/spidev0.0",
    # SolarCharly
    # "SerialBus.designator":   "/dev/spidev0.1"
    #"SerialBusDevice.CS.gpio.pinDesignator": 17,

    "adc.channel"    :   2,
    "adc.vref.lower" :   0,
    "adc.vref.upper" :   3300,	# VRef on Pi 3 click shield by mikroe
    }

class TestSTADC1283( unittest.TestCase ):
    
    def test_open(self):
        global config
        params = config.copy()
        device = Driver()
        self.assertIsNotNone( device )
        self.assertEqual( device.provider, SysProvider.COMPOSITE, "Wrong provider!")
        Driver.Params_init( params )
        self.assertEqual( params["adc.channel"], config["adc.channel"] )
        #self.assertEqual( params["adc.samplingTime"], 2 )
        self.assertEqual( params["adc.vref.lower"], config["adc.vref.lower"] )
        self.assertEqual( params["adc.vref.upper"], config["adc.vref.upper"] )
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk, "Open: " + str(err) )
        self.assertEqual( device.channel, config["adc.channel"] )
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )

    def test_input(self):
        global config
        params = config.copy()
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk, "Open: " + str(err) )
        print()
        total = 5
        print("Monitoring the input. Explicitly set the channel.")
        for cnt in range(total):
            dvalue, err = device.getDigital( params["adc.channel"] )
            self.assertEqual( err, ErrorCode.errOk, "getDigital: "+str(err) )
            compVolt, err = device.toVoltage( dvalue )
            self.assertEqual( err, ErrorCode.errOk, "toVoltage: "+str(err) )
            print("d#", (cnt+1),"/", total, ": digital value=", dvalue,
                  " (", hex(dvalue),")  corr.voltage=", compVolt, " mV.", sep='')
            
            volt, err = device.getVoltage( params["adc.channel"] )
            self.assertEqual( err, ErrorCode.errOk, "getVolt: "+str(err) )
            print("a#", (cnt+1),"/", total, ": voltage=", volt, " mV.", sep='')
            sleep(1)
        print("Monitoring the input. Use the configured channel.")
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

