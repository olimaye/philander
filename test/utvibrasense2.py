"""
"""
import argparse
import unittest

from philander.systypes import ErrorCode
from philander.vibrasense2 import VibraSense2 as Driver


class TestVibrasense2( unittest.TestCase ):

    def setUp(self):
        self.config = {
            "SerialBus.designator": 0, #"/dev/i2c-1",
        }
        parser = argparse.ArgumentParser()
        parser.add_argument("--bus", help="designator of the i2c bus", default=None)
        args = parser.parse_args()
        if args.bus:
            self.configSensor["SerialBus.designator"] = args.bus
            
    def test_paramsinit(self):
        cfg = self.config.copy()
        Driver.Params_init( cfg )
        self.assertIsNotNone( cfg )
        self.assertTrue( "SerialBusDevice.address" in cfg )
        self.assertTrue( cfg["SerialBusDevice.address"] in Driver.ADDRESSES_ALLOWED )
    
    
    def test_open(self):
        cfg = self.config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        # Simple open
        err = device.open(cfg)
        self.assertEqual( err, ErrorCode.errOk, f"Open error {err}." )
        self.assertTrue( err.isOk() )
        # Corresponding close
        err = device.close()
        self.assertTrue( err.isOk() )
        # Reopen
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
        # Second open may or may not be ok
        device.open(cfg)
        # Matching close
        err = device.close()
        self.assertTrue( err.isOk() )
    
    def test_measurements(self):
        cfg = self.config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )

        for _ in range(10):        
            val, err = device.getLatestData()
            self.assertTrue( err.isOk(), f"Measurement: {err}." )
            self.assertGreaterEqual( val, 0 )
    
        err = device.close()
        self.assertTrue( err.isOk() )
    
        
if __name__ == '__main__':
    unittest.main()

