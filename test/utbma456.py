"""
"""
import argparse
import unittest

from philander.bma456 import BMA456 as BMA
from philander.accelerometer import AxesSign
from philander.sensor import SelfTest
from philander.serialbus import SerialBusType
from philander.systypes import ErrorCode

class TestBMA456( unittest.TestCase ):

    def setUp(self):
        self.configSensor = {
            "SerialBus.designator": 0, #"/dev/i2c-1",
            "Sensor.dataRange"    : 4000,
            "Sensor.dataRate"     : 100,
            "BMA456.INT_MAP_DATA": 0xFF,
        }
        parser = argparse.ArgumentParser()
        parser.add_argument("--bus", help="designator of the i2c bus", default=None)
        parser.add_argument("--adr", help="i2c address of the device", type=int, default=None)
        args = parser.parse_args()
        if args.bus:
            self.configSensor["SerialBus.designator"] = args.bus
        if args.adr:
            self.configSensor["SerialBusDevice.address"] = args.adr
        
            
    def test_paramsinit(self):
        cfg = self.configSensor.copy()
        BMA.Params_init( cfg )
        self.assertIsNotNone( cfg )
        self.assertTrue( "SerialBus.designator" in cfg )
        self.assertTrue( "SerialBus.type" in cfg )
        self.assertEqual( cfg["SerialBus.type"], SerialBusType.I2C )
        self.assertTrue( "SerialBusDevice.address" in cfg )
        self.assertTrue( cfg["SerialBusDevice.address"] in (0x18, 0x19) )

    def test_open(self):
        cfg = self.configSensor.copy()
        BMA.Params_init( cfg )
        sensor = BMA()
        self.assertIsNotNone( sensor )
        # Simple open
        err = sensor.open(cfg)
        self.assertEqual( err, ErrorCode.errOk )
        self.assertTrue( err.isOk() )
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

    def test_selftest(self):
        cfg = self.configSensor.copy()
        BMA.Params_init( cfg )
        sensor = BMA()
        self.assertIsNotNone( sensor )
        err = sensor.open(cfg)
        self.assertTrue( err.isOk() )
        err = sensor.selfTest( SelfTest.CONNECTION )
        self.assertTrue( err.isOk() )
        err = sensor.close()
        self.assertTrue( err.isOk() )
    
    def test_working(self):
        cfg = self.configSensor.copy()
        BMA.Params_init( cfg )
        sensor = BMA()
        self.assertIsNotNone( sensor )
        err = sensor.open(cfg)
        self.assertTrue( err.isOk() )
        for _ in range(10):
            meas, err = sensor.getLatestData()
            self.assertTrue( err.isOk() )
            self.assertTrue( meas.x < 2000 )
            self.assertTrue( -2000 < meas.x)
            self.assertTrue( meas.y < 2000 )
            self.assertTrue( -2000 < meas.y)
            self.assertTrue( meas.z < 2000 )
            self.assertTrue( -2000 < meas.z)
            total = (meas.x**2 + meas.y**2 + meas.z**2) ** (1/2)
            self.assertTrue( total < 2000 )
            self.assertTrue( 500 <= total )
        err = sensor.close()
        self.assertTrue( err.isOk() )

        
if __name__ == '__main__':
    unittest.main()

