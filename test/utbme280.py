"""
"""
import argparse
import logging
import sys
import unittest

from philander.bme280 import BME280 as SDUT # Sensor driver under test
from philander.primitives import PreciseTemperature, PrecisePressure, PrecisePercentage
from philander.sensor import SelfTest, Sensor
from philander.serialbus import SerialBusType
from philander.systypes import ErrorCode

config = {
    "weather.SerialBus.type"      : SerialBusType.I2C,
    "weather.SerialBus.designator": "/dev/i2c-1", #"/dev/i2c-1", 0
    "weather.Sensor.temp.sampling": 1,
    "weather.Sensor.press.sampling": 1,
    "weather.Sensor.hum.sampling" : 1,
    "weather.Sensor.measurement.standby": 10,
    "weather.Sensor.measurement.filter": Sensor.FILTER_NONE,
}

class TestBME280( unittest.TestCase ):
            
    @unittest.skip("Disabled for easier diagnostics.")
    def test_paramsinit(self):
        global config
        cfg = config.copy()
        SDUT.Params_init( cfg )
        self.assertIsNotNone( cfg )
        self.assertIn( "weather.SerialBus.designator", cfg )
        self.assertIn( "weather.SerialBus.type", cfg )
        self.assertEqual( cfg["weather.SerialBus.type"], SerialBusType.I2C )
        self.assertIn( "weather.SerialBusDevice.address", cfg )
        self.assertIn( cfg["weather.SerialBusDevice.address"], (0x76, 0x77) )

    @unittest.skip("Disabled for easier diagnostics.")
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
    
    #@unittest.skip("Disabled for easier diagnostics.")
    def test_readCalibration(self):
        global config
        cfg = config.copy()
        SDUT.Params_init( cfg )
        sensor = SDUT()
        self.assertIsNotNone( sensor )
        err = sensor.open(cfg)
        self.assertTrue( err.isOk(), f"Open failed: {err}." )
        buf, ret = sensor.readBufferRegister( BME280.REG_CALIB_T1, 24 )
        

    @unittest.skip("Disabled for easier diagnostics.")
    def test_compensation(self):
        global config
        cfg = config.copy()
        SDUT.Params_init( cfg )
        sensor = SDUT()
        self.assertIsNotNone( sensor )
        err = sensor.open(cfg)
        self.assertTrue( err.isOk(), f"Open failed: {err}." )

    @unittest.skip("Disabled for easier diagnostics.")
    def test_working(self):
        global config
        cfg = config.copy()
        SDUT.Params_init( cfg )
        sensor = SDUT()
        self.assertIsNotNone( sensor )
        err = sensor.open(cfg)
        self.assertTrue( err.isOk(), f"Open failed: {err}." )
        for _ in range(10):
            meas, err = sensor.getLatestData()
            self.assertTrue( err.isOk() )
            self.assertNotEqual( meas.temperature, PreciseTemperature.invalid )
            self.assertGreater( meas.temperature, 0x0A00 )
            self.assertLess( meas.temperature, 0x2000 )
            self.assertNotEqual( meas.pressure, PrecisePressure.invalid )
            self.assertGreater( meas.pressure, 0x01600000 ) # ~901 hPa
            self.assertLess( meas.pressure, 0x01B00000 )    # ~1105 hPa
            self.assertNotEqual( meas.humidity, PrecisePercentage.invalid )
            self.assertGreater( meas.humidity, 0x1400 )     # 20 %
            self.assertLess( meas.humidity, 0x5000 )        # 80 %
        err = sensor.close()
        self.assertTrue( err.isOk() )

        
if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel( logging.DEBUG )
    logger.addHandler( logging.StreamHandler() )

    parser = argparse.ArgumentParser()
    parser.add_argument("--bus", help="designator of the serial bus", default=None)
    parser.add_argument("--adr", help="i2c address of the device", type=int, default=None)
    args, unknown = parser.parse_known_args()
    if args.bus:
        config["SerialBus.designator"] = args.bus
    if args.adr:
        config["SerialBusDevice.address"] = args.adr
    if sys.argv:
        sys.argv = [sys.argv[0],] + unknown
    unittest.main()

