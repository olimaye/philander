"""
"""
import argparse
import sys
import unittest

from philander.htu21d import HTU21D as Sensor, StatusID
from philander.sensor import SelfTest
from philander.serialbus import SerialBusType
from philander.systypes import ErrorCode

config = {
    "SerialBus.designator": 0, #"/dev/i2c-1",
    "Sensor.dataRate"     : 100,
}

class TestHTU21D( unittest.TestCase ):
            
    def test_paramsinit(self):
        global config
        cfg = config.copy()
        Sensor.Params_init( cfg )
        self.assertIsNotNone( cfg )
        self.assertTrue( "SerialBus.designator" in cfg )
        self.assertTrue( "SerialBus.type" in cfg )
        self.assertEqual( cfg["SerialBus.type"], SerialBusType.I2C )
        self.assertTrue( "SerialBusDevice.address" in cfg )
        self.assertTrue( cfg["SerialBusDevice.address"] in (Sensor.ADDRESS, ) )

    def test_open(self):
        global config
        cfg = config.copy()
        Sensor.Params_init( cfg )
        sensor = Sensor()
        self.assertIsNotNone( sensor )
        # Simple open
        err = sensor.open(cfg)
        self.assertEqual( err, ErrorCode.errOk, f"Open error {err}." )
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

    def test_selftest(self):
        global config
        cfg = config.copy()
        Sensor.Params_init( cfg )
        sensor = Sensor()
        self.assertIsNotNone( sensor )
        err = sensor.open(cfg)
        self.assertTrue( err.isOk() )
        err = sensor.selfTest( SelfTest.FUNCTIONAL )
        self.assertTrue( err.isOk(), f"Self test error {err}." )
        err = sensor.close()
        self.assertTrue( err.isOk() )
    
    def test_working(self):
        global config
        cfg = config.copy()
        Sensor.Params_init( cfg )
        sensor = Sensor()
        self.assertIsNotNone( sensor )
        err = sensor.open(cfg)
        self.assertTrue( err.isOk() )
        for _ in range(10):
            meas, err = sensor.getLatestData()
            self.assertTrue( err.isOk() )
            self.assertTrue( meas.temperature < 40 )
            self.assertTrue( -10 < meas.temperature)
            self.assertTrue( meas.humidity < 80 )
            self.assertTrue( 10 < meas.humidity )
        err = sensor.close()
        self.assertTrue( err.isOk() )

    def test_status(self):
        global config
        cfg = config.copy()
        Sensor.Params_init( cfg )
        sensor = Sensor()
        self.assertIsNotNone( sensor )
        err = sensor.open(cfg)
        self.assertTrue( err.isOk() )
        status, err = sensor.getStatus( StatusID.powerOk )
        self.assertTrue( err.isOk() )
        self.assertTrue( status )
        err = sensor.close()
        self.assertTrue( err.isOk() )

        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--bus", help="designator of the i2c bus", default=None)
    parser.add_argument("--adr", help="i2c address of the device", type=int, default=None)
    args, unknown = parser.parse_known_args()
    if args.bus:
        config["SerialBus.designator"] = args.bus
    if args.adr:
        config["SerialBusDevice.address"] = args.adr
    if sys.argv:
        sys.argv = [sys.argv[0],] + unknown
    unittest.main()

