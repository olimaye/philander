"""
"""
import argparse
import logging
import sys
import unittest

from philander.vd6283tx import VD6283TX as SDUT # Sensor driver under test
from philander.sensor import SelfTest, Sensor
from philander.serialbus import SerialBusType
from philander.systypes import ErrorCode

config = {
    "light.SerialBus.designator": "/dev/i2c-1", #"/dev/i2c-1", 0
    #"light.int.gpio.pinDesignator": 6,
    "light.int.cfg":    SDUT.GPIO1_CFG_PUSH_PULL,
}

class TestVD6283TX( unittest.TestCase ):
            
    #@unittest.skip("Disabled for easier diagnostics.")
    def test_paramsinit(self):
        global config
        cfg = config.copy()
        SDUT.Params_init( cfg )
        self.assertIsNotNone( cfg )
        self.assertIn( "light.SerialBus.designator", cfg )
        self.assertIn( "light.SerialBus.type", cfg )
        self.assertEqual( cfg["light.SerialBus.type"], SerialBusType.I2C )
        self.assertIn( "light.SerialBusDevice.address", cfg )
        self.assertEqual( cfg["light.SerialBusDevice.address"], SDUT.ADDRESSES_ALLOWED[0] )

    #@unittest.skip("Disabled for easier diagnostics.")
    def test_open(self):
        global config
        cfg = config.copy()
        SDUT.Params_init( cfg )
        sensor = SDUT()
        self.assertIsNotNone( sensor )
        # Simple open
        err = sensor.open(cfg)
        self.assertTrue( err.isOk(), f"Open failed: {err}. serialBus is a {type(sensor.serialBus)}." )
        # Corresponding close
        err = sensor.close()
        self.assertTrue( err.isOk() )
        # Reopen
        err = sensor.open(cfg)
        self.assertTrue( err.isOk() )
        # Second open should yield an error
        err = sensor.open(cfg)
        self.assertFalse( err.isOk() )
        # Matching close
        err = sensor.close()
        self.assertTrue( err.isOk() )
        # Another close should given an error
        err = sensor.close()
        self.assertFalse( err.isOk() )

    @unittest.skip("Disabled for easier diagnostics.")
    def test_selftest(self):
        global config
        cfg = config.copy()
        SDUT.Params_init( cfg )
        sensor = SDUT()
        self.assertIsNotNone( sensor )
        err = sensor.open(cfg)
        self.assertTrue( err.isOk(), f"Open failed: {err}." )
        err = sensor.selfTest( SelfTest.CONNECTION )
        self.assertTrue( err.isOk() )
        err = sensor.close()
        self.assertTrue( err.isOk() )
    
    @unittest.skip("Disabled for easier diagnostics.")
    def test_working(self):
        global config
        cfg = config.copy()
        SDUT.Params_init( cfg )
        sensor = SDUT()
        self.assertIsNotNone( sensor )
        err = sensor.open(cfg)
        self.assertTrue( err.isOk(), f"Open failed: {err}." )
        headLine = "No., "
        for chIdx in range( 1, 7 ):
            headLine += SDUT.CHANNEL_NAME[chIdx]+"["+chIdx+"], "
        logging.info( headLine )
        for _ in range(10):
            meas, err = sensor.getLatestData()
            self.assertTrue( err.isOk() )
            logging.info("%d  %d  %d  %d  %d  %d  %d",
                         meas[1], meas[2], meas[3], meas[4], meas[5], meas[6] )
            # self.assertNotEqual( meas.temperature, PreciseTemperature.invalid )
            # self.assertGreater( meas.temperature, 0x0A00 )
        err = sensor.close()
        self.assertTrue( err.isOk() )

        
if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel( logging.INFO )
    logger.addHandler( logging.StreamHandler() )

    parser = argparse.ArgumentParser()
    parser.add_argument("--bus", help="designator of the serial bus", default=None)
    args, unknown = parser.parse_known_args()
    if args.bus:
        config["SerialBus.designator"] = args.bus
    if sys.argv:
        sys.argv = [sys.argv[0],] + unknown
    unittest.main()

