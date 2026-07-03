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
        # T1...T3 and P1 ... P9
        buf, err = sensor.readBufferRegister( SDUT.REG_CALIB_T1, 24 )
        self.assertTrue( err.isOk() )
        logging.info("REG[x89:88]=0x%02x:%02x   dig_T1=0x%04x (%d)", buf[1], buf[0], self.dig_T1, self.dig_T1)
        logging.info("REG[x8B:8A]=0x%02x:%02x   dig_T2=0x%04x (%d)", buf[3], buf[2], self.dig_T2, self.dig_T2)
        logging.info("REG[x8D:8C]=0x%02x:%02x   dig_T3=0x%04x (%d)", buf[5], buf[4], self.dig_T3, self.dig_T3)
        logging.info("REG[x8F:8E]=0x%02x:%02x   dig_P1=0x%04x (%d)", buf[7], buf[6], self.dig_P1, self.dig_P1)
        logging.info("REG[x91:90]=0x%02x:%02x   dig_P2=0x%04x (%d)", buf[9], buf[8], self.dig_P2, self.dig_P2)
        logging.info("REG[x93:92]=0x%02x:%02x   dig_P3=0x%04x (%d)", buf[11], buf[10], self.dig_P3, self.dig_P3)
        logging.info("REG[x95:94]=0x%02x:%02x   dig_P4=0x%04x (%d)", buf[13], buf[12], self.dig_P4, self.dig_P4)
        logging.info("REG[x97:96]=0x%02x:%02x   dig_P5=0x%04x (%d)", buf[15], buf[14], self.dig_P5, self.dig_P5)
        logging.info("REG[x99:98]=0x%02x:%02x   dig_P6=0x%04x (%d)", buf[17], buf[16], self.dig_P6, self.dig_P6)
        logging.info("REG[x9B:9A]=0x%02x:%02x   dig_P7=0x%04x (%d)", buf[19], buf[18], self.dig_P7, self.dig_P7)
        logging.info("REG[x9D:9C]=0x%02x:%02x   dig_P8=0x%04x (%d)", buf[21], buf[20], self.dig_P8, self.dig_P8)
        logging.info("REG[x9F:9E]=0x%02x:%02x   dig_P9=0x%04x (%d)", buf[23], buf[22], self.dig_P9, self.dig_P9)
        self.assertEqual( (buf[1] << 8) | buf[0], self.dig_T1 )
        self.assertEqual( (buf[7] << 8) | buf[6], self.dig_P1 )
        # H1
        buf, err = sensor.readByteRegister( SDUT.REG_CALIB_H1 )
        self.assertTrue( err.isOk() )
        logging.info("REG[xA1]=0x%02x   dig_H1=0x%02x (%d)", buf, self.dig_H1, self.dig_H1)
        self.assertEqual( buf, self.dig_H1 )
        # H2 ... H6
        buf, err = sensor.readBufferRegister( SDUT.REG_CALIB_H2, 7 )
        self.assertTrue( err.isOk() )
        logging.info("REG[xE2:E1]=0x%02x:%02x   dig_H2=0x%04x (%d)", buf[1], buf[0], self.dig_H2, self.dig_H2)
        logging.info("REG[xE3]   =0x%02x        dig_H3=0x%02x   (%d)", buf[2], self.dig_H3, self.dig_H3)
        logging.info("REG[xE4:E5]=0x%02x:%02x   dig_H4=0x%04x (%d)", buf[3], buf[4], self.dig_H4, self.dig_H4)
        logging.info("REG[xE6:E5]=0x%02x:%02x   dig_H5=0x%04x (%d)", buf[5], buf[4], self.dig_H5, self.dig_H5)
        logging.info("REG[xE7]   =0x%02x      dig_H6=0x%02x (%d)", buf[6], self.dig_H6, self.dig_H6)
        self.assertEqual( buf[2], self.dig_H3 )
        err = sensor.close()
        self.assertTrue( err.isOk() )

    # @unittest.skip("Disabled for easier diagnostics.")
    # def test_compensation(self):
    #     global config
    #     cfg = config.copy()
    #     SDUT.Params_init( cfg )
    #     sensor = SDUT()
    #     self.assertIsNotNone( sensor )
    #     err = sensor.open(cfg)
    #     self.assertTrue( err.isOk(), f"Open failed: {err}." )

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
            logging.info("t = %4.2f °C   p = %4.3f hPa   h = %3.2f %RH",
                         meas.temperature/256, meas.pressure/256, meas.humidity/256)
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

