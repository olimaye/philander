"""
"""
import logging
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

# 2x SN74HCS594 on SolarCharly with Raspberry Pi 
# shiftParams = {\
#     "shiftreg.din.gpio.pinDesignator":  10,     # SPI0:MOSI, SPI_MOSI
#     "shiftreg.dclk.gpio.pinDesignator": 11,     # SPI0:SCLK, SPI_CLK
#     #"shiftreg.dclr.gpio.pinDesignator": xx,     # not present
#     #"shiftreg.dclr.gpio.inverted":      True,
#     #"shiftreg.rclk.gpio.pinDesignator": xx,     # different semantics -> ENA
#     #"shiftreg.rclr.gpio.pinDesignator": xx,     # not present
#     "shiftreg.enable.gpio.pinDesignator": 14,   # RN_MAIN
#
#     "shiftreg.SerialBus.designator":   0,       # "/dev/spidev0.1", SPI0
#     "shiftreg.SerialBusDevice.CS.gpio.pinDesignator": 8,    # CE0, RN_CS
# }

# 2x SN74HC595 on Mikroe 7Seg Click Board 1201 with Raspberry Pi 
shiftParams = {\
    #"shiftreg.SerialBus.provider":      SysProvider.PERIPHERY,  # MICROPYTHON, PERIPHERY, (SIM), (SMBUS2, no SPI)
    "shiftreg.dclr.gpio.pinDesignator": 5,      # /SRCLR -> RST 5 (bay#1), 12(bay#2)
    "shiftreg.dclr.gpio.inverted":      True,   # 
    "shiftreg.rclk.gpio.pinDesignator": 8,      # RCLK -> Latch -> CS0 8(bay #1), 7(bay#2)
    #"shiftreg.rclr.gpio.pinDesignator": xx,     # not present
    #"shiftreg.enable.gpio.pinDesignator": 14,   # /OE not present
     "shiftreg.SerialBus.designator":   "/dev/spidev0.0",    # "/dev/spidev0.1", SPI0
     "shiftreg.SerialBus.SPI.mode":   SPIMode.CPOL0_CPHA0,   # CLK idles low, read first edge
}

# The Mikro-e 7Seg click board adjusts brightness through the PWM pin
pwmParams = {
    "gpio.pinDesignator": 18,	# PWM, 18(bay#1), 17(bay#2)
    "gpio.level": GPIO.LEVEL_HIGH,
    "pwm.pinDesignator": 18,    # PWM, 18(bay#1), 17(bay#2)
    "pwm.chip": 0,
    "pwm.channel": 0,
    "pwm.duty": 80,
}

# A test string encoded for 7Seg board
hallo = [ 0xea, 0xee, 0x70, 0x70, 0x7e]

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
        
        for data in hallo[::-1]:
            err = sreg.write( data )
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
    unittest.main()

