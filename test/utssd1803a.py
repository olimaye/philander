"""
"""
import argparse
import logging
import sys
from time import sleep
import unittest

from philander.serialbus import SerialBus, SerialBusType, SPIMode
from philander.ssd1803a import SSD1803A
from philander.systypes import ErrorCode

# Globals
TARGET_SYSTEM_SOLARCHARLY = "solarcharly"

params = {\
     "display.SerialBus.designator":   "/dev/spidev0.0",    # "/dev/spidev0.1", SPI0
     "display.SerialBus.type":          SerialBusType.SPI,
     "display.SerialBus.SPI.bitorder":   "MSB",
     "display.SerialBus.SPI.mode":   SPIMode.CPOL1_CPHA1,   # CLK idles high, read 2nd edge
}

testData = [ 0x01, 0x02, 0x03, 0x04, 0x05 ]
# Delay time in seconds
delay_s = 1

class TestSSD1803A( unittest.TestCase ):
    
    #@unittest.skip("Disabled for easier diagnostics.")
    def test_invBuffer(self):
        validSet = [0x00, 0x81, 0x42, 0xC3, 0x24, 0xA5, 0x66, 0xE7,
                    0x18, 0x99, 0x5A, 0xDB, 0x3C, 0xBD, 0x7E, 0xFF]
        for x in range(0x100):
            buffer = [x, x, x]
            SSD1803A._reverseBitOrder( buffer )
            self.assertTrue( (buffer[0] | x) in validSet, f"Failed  OR-test: x={x}, inv(x)={buffer[0]}.")
            self.assertTrue( (buffer[0] ^ x) in validSet, f"Failed XOR-test: x={x}, inv(x)={buffer[0]}.")
            self.assertTrue( (buffer[0] & x) in validSet, f"Failed AND-test: x={x}, inv(x)={buffer[0]}.")
            self.assertEqual( buffer[0], buffer[1], f"[0]={buffer[0]}  [1]={buffer[1]}" )
            self.assertEqual( buffer[0], buffer[2], f"[0]={buffer[0]}  [1]={buffer[2]}" )
            self.assertEqual( buffer[1], buffer[2], f"[0]={buffer[1]}  [1]={buffer[2]}" )

    #@unittest.skip("Disabled for easier diagnostics.")
    def test_params(self):
        dev = SSD1803A()
        self.assertIsNotNone( dev )
        cfg = params.copy()
        SSD1803A.Params_init( cfg )
        self.assertEqual( cfg["display.SerialBus.type"], params["display.SerialBus.type"] )
        if cfg["display.SerialBus.type"] == SerialBusType.I2C:
            self.assertEqual( cfg["display.SerialBus.speed"], SerialBus.DEFAULT_I2C_SPEED )
        else:
            self.assertEqual( cfg["display.SerialBus.speed"], SerialBus.DEFAULT_SPI_SPEED )
            self.assertEqual( cfg["display.SerialBus.SPI.mode"], params["display.SerialBus.SPI.mode"] )
            self.assertEqual( cfg["display.SerialBus.SPI.bitorder"], params["display.SerialBus.SPI.bitorder"] )
            self.assertEqual( cfg["display.SerialBus.SPI.bpw"], SerialBus.DEFAULT_SPI_BITS_PER_WORD )
        
        
    #@unittest.skip("Disabled for easier diagnostics.")
    def test_commHelper(self):
        dev = SSD1803A()
        self.assertIsNotNone( dev )
        cfg = params.copy()
        err = dev.open(cfg)
        self.assertEqual( err, ErrorCode.errOk )

        err = dev._writeCmd( 0x01 )
        self.assertEqual( err, ErrorCode.errOk )
        
        bf, ac, cid, err = dev._readInfo()
        self.assertFalse( bf )
        self.assertEqual( ac, 0x00 )
        # self.assertEqual( cid, SSD1803A.PART_ID )
        self.assertEqual( err, ErrorCode.errOk )

        err = dev._writeRAM( [1, 2, 3, 4] )
        self.assertEqual( err, ErrorCode.errOk )

        n = 4
        data, err = dev._readRAM(n)
        self.assertEqual( err, ErrorCode.errOk )
        self.assertEqual( len(data), n )

        err = dev.close()
        self.assertEqual( err, ErrorCode.errOk )
        
        
if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel( logging.DEBUG )
    logger.addHandler( logging.StreamHandler() )

    parser = argparse.ArgumentParser()
    parser.add_argument("--target", help="target system identifier", default=None)
    args, unknown = parser.parse_known_args()
    if args.target == TARGET_SYSTEM_SOLARCHARLY:
        # DOGM204 via SPI 
        params = {\
             "display.SerialBus.designator":   "/dev/spidev0.0",    # "/dev/spidev0.1", SPI0
             "display.SerialBus.type":          SerialBusType.SPI,
             "display.SerialBus.SPI.bitorder":   "MSB",
             "display.SerialBus.SPI.mode":   SPIMode.CPOL1_CPHA1,   # CLK idles high, read 2nd edge
        }
        delay_s = 2
    if sys.argv:
        sys.argv = [sys.argv[0],] + unknown
    unittest.main()

