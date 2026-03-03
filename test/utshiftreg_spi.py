"""
"""
import argparse
import logging
import sys
from time import sleep
import unittest

from philander.gpio import GPIO
from philander.pwm import PWM
from philander.serialbus import SerialBusType, SPIMode
from philander.shiftreg import ShiftReg
from philander.shiftreg_spi import ShiftRegSPI
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

# Globals
TARGET_SYSTEM_GENERIC = "generic"
TARGET_SYSTEM_7SEG = "7seg"
TARGET_SYSTEM_SOLARCHARLY = "solarcharly"

shiftParams = {\
     "shiftreg.SerialBus.designator":   "/dev/spidev0.0",    # "/dev/spidev0.1", SPI0
     "shiftreg.SerialBus.SPI.mode":   SPIMode.CPOL1_CPHA1,   # CLK idles high, read 2nd edge
}
testData = [ 0x01, 0x02, 0x03, 0x04, 0x05 ]
testDataWidth = 8
# Delay time in seconds
delay_s = 1

class TestShiftReg( unittest.TestCase ):
    
    #@unittest.skip("Disabled for easier diagnostics.")
    def test_params(self):
        sreg = ShiftReg()
        self.assertIsNotNone( sreg )
        params = shiftParams.copy()
        ShiftRegSPI.Params_init( params )
        self.assertEqual( params["shiftreg.SerialBus.type"], SerialBusType.SPI )
        
        
    #@unittest.skip("Disabled for easier diagnostics.")
    def test_spi(self):
        sreg = ShiftRegSPI()
        self.assertIsNotNone( sreg )
        params = shiftParams.copy()
        err = sreg.open(params)
        self.assertEqual( err, ErrorCode.errOk )

        # If necessary, assure brightness        
        if "pwmParams" in globals():
            pwm = GPIO.getGPIO()
            params = pwmParams.copy()
            err = pwm.open(params)
            self.assertEqual( err, ErrorCode.errOk, f"Instance: {type(pwm)}" )
        
        for data in testData:
            err = sreg.write( data, numBits=testDataWidth )
            self.assertEqual( err, ErrorCode.errOk )
            sleep(delay_s)
        
        err = sreg.clear()
        self.assertEqual( err, ErrorCode.errOk )
        err = sreg.close()
        self.assertEqual( err, ErrorCode.errOk )
        
        
if __name__ == '__main__':
    #logger = logging.getLogger()
    #logger.setLevel( logging.DEBUG )
    #logger.addHandler( logging.StreamHandler() )

    parser = argparse.ArgumentParser()
    parser.add_argument("--target", help="target system identifier", default=None)
    args, unknown = parser.parse_known_args()
    if args.target == TARGET_SYSTEM_7SEG:
        # 2x SN74HC595 on Mikroe 7Seg Click Board 1201 with Raspberry Pi 
        shiftParams = {\
            #"shiftreg.SerialBus.provider":      SysProvider.PERIPHERY,  # MICROPYTHON, PERIPHERY, (SIM), (SMBUS2, no SPI)
            "shiftreg.dclr.gpio.pinDesignator": 5,      # /SRCLR -> RST 5 (bay#1), 12(bay#2)
            "shiftreg.dclr.gpio.inverted":      True,   # 
            "shiftreg.rclk.gpio.pinDesignator": 8,      # RCLK -> Latch -> CS0 8(bay #1), 7(bay#2)
            "shiftreg.SerialBus.designator":   "/dev/spidev0.0",    # "/dev/spidev0.1", SPI0
            "shiftreg.SerialBus.SPI.mode":   SPIMode.CPOL0_CPHA0,   # CLK idles low, read first edge
        }
        # ... adjusts brightness through the PWM pin
        pwmParams = {
            "gpio.pinDesignator": 18,	# PWM, 18(bay#1), 17(bay#2)
            "gpio.level": GPIO.LEVEL_HIGH,
            "pwm.pinDesignator": 18,    # PWM, 18(bay#1), 17(bay#2)
            "pwm.chip": 0,
            "pwm.channel": 0,
            "pwm.duty": 80,
        }
        # A test string encoded for 7Seg board
        testData = [ 0xea, 0xee, 0x70, 0x70, 0x7e]
        testDataWidth = 8
    elif args.target == TARGET_SYSTEM_SOLARCHARLY:
        # 2x SN74HCS594 on SolarCharly with Raspberry Pi 
        shiftParams = {\
             "shiftreg.rclk.gpio.pinDesignator": 14,     # RN_MAIN
             "shiftreg.SerialBus.designator":   "/dev/spidev0.0",    # "/dev/spidev0.1", SPI0
             "shiftreg.SerialBus.SPI.mode":   SPIMode.CPOL1_CPHA1,   # CLK idles high, read 2nd edge
        }
        # Resistor network of the SolarCharly board in descending order
        testData = [    0x3FFF, 0x5FFF, 0x6FFF, 0x77FF, 0x7BFF, 0x7DFF, 0x7EFF,
                0x7F7F, 0x7FBF, 0x7FDF, 0x7FEF, 0x7FF7, 0x7FFB, 0x7FFD, 0x7FFE,
                0x8000, 0x7FFF]
        testDataWidth = 16
        delay_s = 2
    if sys.argv:
        sys.argv = [sys.argv[0],] + unknown
    unittest.main()

