"""
"""
from time import sleep
import unittest

from philander.mcp3208 import MCP3208 as Driver
from philander.serialbus import SPIMode
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

config = {\
    "SerialBus.designator":   "/dev/spidev1.2",
    #"SerialBusDevice.CS.gpio.pinDesignator": 16,
    "SerialBus.SPI.mode": SPIMode.CPOL0_CPHA0,	# Note that SPI modes 1 and 3 do not work on Pi's SPI1 !
    "adc.channel"    :   0,
    "adc.vref.lower" :   0,
    "adc.vref.upper" :   4096,	# VRef on Pi 3 click shield by mikroe
    }

class TestMCP3208( unittest.TestCase ):

    #@unittest.skip("Disabled for easier diagnostics.")
    def test_open(self):
        global config
        params = config.copy()
        
        device = Driver()
        self.assertIsNotNone( device )
        self.assertEqual( device.provider, SysProvider.COMPOSITE, "Wrong provider!")
        Driver.Params_init( params )
        self.assertEqual( params["adc.channel"], config["adc.channel"] )
        self.assertEqual( params["adc.vref.lower"], config["adc.vref.lower"] )
        self.assertEqual( params["adc.vref.upper"], config["adc.vref.upper"] )
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk, "Open: " + str(err) )
        self.assertEqual( device.channel, config["adc.channel"] )
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )

    #@unittest.skip("Disabled for easier diagnostics.")
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

