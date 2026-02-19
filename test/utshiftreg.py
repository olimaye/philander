"""
"""
from time import sleep
import unittest

from philander.gpio import GPIO
from philander.serialbus import SerialBusType
from philander.shiftreg import ShiftReg
from philander.shiftreg_spi import ShiftRegSPI
from philander.systypes import ErrorCode

# Globals

# 2x SN74HCS594 on SolarCharly with Raspberry Pi 
# gParams = {\
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

# 2x SN74HC595 on Mikroe 7Seg Click Board 1201 in bay #1 with Raspberry Pi 
gParams = {\
    "shiftreg.din.gpio.pinDesignator":  10,     # SPI0:MOSI, SPI_MOSI
    "shiftreg.dclk.gpio.pinDesignator": 11,     # SPI0:SCLK, SPI_CLK
    "shiftreg.dclr.gpio.pinDesignator": 5,      # /SRCLR -> RST in bay #1
    "shiftreg.dclr.gpio.inverted":      True,   # 
    "shiftreg.rclk.gpio.pinDesignator": 8,      # RCLK -> Latch -> CS0 in bay #1
    #"shiftreg.rclr.gpio.pinDesignator": xx,     # not present
    #"shiftreg.enable.gpio.pinDesignator": 14,   # /OE not present
     "shiftreg.SerialBus.designator":   "/dev/spidev0.1",       # "/dev/spidev0.1", SPI0
     "shiftreg.SerialBusDevice.CS.gpio.pinDesignator": 7,    # CE1 in bay#2
}

hallo = [ 0xea, 0xee, 0x70, 0x70, 0x7e]

class TestShiftReg( unittest.TestCase ):
    
    @unittest.skip("Disabled for easier diagnostics.")
    def test_params(self):
        sreg = ShiftReg()
        self.assertIsNotNone( sreg )
        params = gParams.copy()
        ShiftReg.Params_init( params )
        self.assertEqual( params["shiftreg.gpio.direction"], GPIO.DIRECTION_OUT )
        self.assertFalse( params["shiftreg.gpio.inverted"] )
        self.assertEqual( params["shiftreg.gpio.level"], GPIO.LEVEL_LOW )
        self.assertEqual( params["shiftreg.din.gpio.pinDesignator"], gParams["shiftreg.din.gpio.pinDesignator"] )
        self.assertEqual( params["shiftreg.din.gpio.direction"], GPIO.DIRECTION_OUT )
        self.assertFalse( params["shiftreg.din.gpio.inverted"] )
        self.assertEqual( params["shiftreg.din.gpio.level"], GPIO.LEVEL_LOW )
        
    @unittest.skip("Disabled for easier diagnostics.")
    def test_gpio(self):
        sreg = ShiftReg()
        self.assertIsNotNone( sreg )
        params = gParams.copy()
        err = sreg.open(params)
        self.assertEqual( err, ErrorCode.errOk )
        
        dTime = 1
        #for cnt in range(16):
        #    err = sreg.write( cnt & 0x01)
        #    self.assertEqual( err, ErrorCode.errOk )
        #    sleep(dTime)

        for data in hallo:
            err = sreg.write( data, 8 )
            sreg.latch()
            self.assertEqual( err, ErrorCode.errOk )
            sleep(dTime)
        for data in hallo:
            sreg.clearData()	# ignore return
            sreg.latch()
            err = sreg.write( data, 8 )
            sreg.latch()
            self.assertEqual( err, ErrorCode.errOk )
            sleep(dTime)
        
        err = sreg.close()
        self.assertEqual( err, ErrorCode.errOk )
        
    #@unittest.skip("Disabled for easier diagnostics.")
    def test_spi(self):
        sreg = ShiftRegSPI()
        self.assertIsNotNone( sreg )
        params = gParams.copy()
        err = sreg.open(params)
        self.assertEqual( err, ErrorCode.errOk )
        
        dTime = 1
        for data in hallo:
            err = sreg.write( data )
            self.assertEqual( err, ErrorCode.errOk )
            sleep(dTime)
        
        err = sreg.close()
        self.assertEqual( err, ErrorCode.errOk )
        
        
if __name__ == '__main__':
    unittest.main()
