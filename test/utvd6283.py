"""
"""
import argparse
import logging
import sys
from time import sleep
import unittest

from philander.configurable import Configuration, ConfigItem
from philander.vd6283 import VD6283 as SDUT # Sensor driver under test
from philander.sensor import SelfTest, Sensor
from philander.serialbus import SerialBusType
from philander.systypes import ErrorCode, RunLevel

config = {
    "light.SerialBus.designator": "/dev/i2c-1", #"/dev/i2c-1", 0
    #"light.int.gpio.pinDesignator": 6,
    "light.int.cfg":    	SDUT.GPIO1_CFG_PUSH_PULL,
    #"light.Sensor.mode":	SDUT.ALS_MODE_SINGLE,
    "light.Sensor.exposure": 90,
    "light.Sensor.interval": 20,
    "light.Sensor.flicker.channel": SDUT.CHANNEL_NONE,
    "light.Sensor.flicker.enable": False,
}

class TestVD6283( unittest.TestCase ):
            
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

    #@unittest.skip("Disabled for easier diagnostics.")
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
    def test_apiData(self):
        global config
        cfg = config.copy()
        SDUT.Params_init( cfg )
        sensor = SDUT()
        self.assertIsNotNone( sensor )
        err = sensor.open(cfg)
        self.assertTrue( err.isOk(), f"Open failed: {err}." )
        
        headLine = "No., "
        for chIdx in range( 1, 7 ):
            headLine += SDUT.CHANNEL[chIdx].name+"["+str(chIdx)+"], "
        logging.info( headLine )

        logging.info( "Latest data" )
        for cnt in range(10):
            sensor.settle()
            meas, err = sensor.getLatestData()
            self.assertTrue( err.isOk(), f"Measurement failed: {err}." )
            logging.info("  %d      %d    %d    %d    %d    %d    %d", cnt,
                         meas[0], meas[1], meas[2], meas[3], meas[4], meas[5])
        logging.info( "Next data" )
        for cnt in range(10):
            meas, err = sensor.getNextData()
            self.assertTrue( err.isOk(), f"Measurement failed: {err}." )
            logging.info("  %d      %d    %d    %d    %d    %d    %d", cnt,
                         meas[0], meas[1], meas[2], meas[3], meas[4], meas[5])
        err = sensor.close()
        self.assertTrue( err.isOk() )

    #@unittest.skip("Disabled for easier diagnostics.")
    def test_rawData(self):
        global config
        cfg = config.copy()
        SDUT.Params_init( cfg )
        sensor = SDUT()
        self.assertIsNotNone( sensor )
        err = sensor.open(cfg)
        self.assertTrue( err.isOk(), f"Open failed: {err}." )
        
        headLine = "No., "
        for chIdx in range( 1, 7 ):
            headLine += SDUT.CHANNEL[chIdx].name+"["+str(chIdx)+"], "
        logging.info( "Raw data" )
        logging.info( headLine )
        
        for cnt in range(10):
            sensor.settle()
            meas, err = sensor.getRawData()
            self.assertTrue( err.isOk(), f"Measurement failed: {err}." )
            logging.info("  %d      %d    %d    %d    %d    %d    %d", cnt,
                         meas[0], meas[1], meas[2], meas[3], meas[4], meas[5])
        err = sensor.close()
        self.assertTrue( err.isOk() )

    #@unittest.skip("Disabled for easier diagnostics.")
    def test_transfer(self):
        global config
        cfg = config.copy()
        cfg["light.Sensor.flicker.enable"] = False
        SDUT.Params_init( cfg )
        sensor = SDUT()
        self.assertIsNotNone( sensor )
        err = sensor.open(cfg)
        self.assertTrue( err.isOk(), f"Open failed: {err}." )
        
        exposure = (1, 2, 5, 50, 120, 360, 600, 1200, 1600, 1638)
        gain = (0.71, 0.83, 1, 5, 10, 50, 67 )
        adcData = (0, 1, 5, 25, 125, 625, 3125, 30000, 60000, 0xFFFF)
        
        logging.info( "Raw to intensity transfer function" )
        headLine = " Gain, Exp"
        for chIdx in range( 1, 7 ):
            headLine += ",  raw-"+str(chIdx)+",xfer-"+str(chIdx)
        logging.info( headLine )
        
        for gn in gain:
            for chIdx in range( 1, SDUT.CHANNEL_NUM+1):
                err = sensor.setGain( chIdx, gn )
            self.assertTrue( err.isOk(), f"Configuration of gain failed: {err}." )
            for exp in exposure:
                err = sensor.setExposure( exp )
                self.assertTrue( err.isOk(), f"Configuration of exposure={exp} failed: {err}." )
                for value in adcData:
                    raw = [value] * SDUT.CHANNEL_NUM
                    xdat, err = sensor.rawToIntensity( raw )
                    self.assertTrue( err.isOk(), f"Compensation failed: {err}." )
                    logging.info("%5.2f, %3d,  %5d, %5d,  %5d, %5d,  %5d, %5d,  %5d, %5d,  %5d, %5d,  %5d, %5d",
                                 gn, exp,
                                 raw[0], xdat[0],
                                 raw[1], xdat[1],
                                 raw[2], xdat[2],
                                 raw[3], xdat[3],
                                 raw[4], xdat[4],
                                 raw[5], xdat[5] )
        err = sensor.close()
        self.assertTrue( err.isOk() )

    #@unittest.skip("Disabled for easier diagnostics.")
    def test_multiConfig(self):
        global config
        cfg = config.copy()
        cfg["light.Sensor.flicker.enable"] = False
        SDUT.Params_init( cfg )
        sensor = SDUT()
        self.assertIsNotNone( sensor )
        err = sensor.open(cfg)
        self.assertTrue( err.isOk(), f"Open failed: {err}." )
        
        exposure = (20, 50, 120, 360, 600)
        gain = (1, 2.5, 5, 10)
        
        logging.info( "MultiConfig compensated measurement data" )
        headLine = "Gain, Exp"
        for chIdx in range( 1, 7 ):
            headLine += ",  raw-"+str(chIdx)+",xfer-"+str(chIdx)
        logging.info( headLine )
        
        for gn in gain:
            for chIdx in range( 1, SDUT.CHANNEL_NUM+1):
                err = sensor.setGain( chIdx, gn )
            self.assertTrue( err.isOk(), f"Configuration of gain failed: {err}." )
            for exp in exposure:
                err = sensor.setExposure( exp )
                self.assertTrue( err.isOk(), f"Configuration of exposure={exp} failed: {err}." )
                akk = [0] * SDUT.CHANNEL_NUM
                for _ in range(10):
                    sensor.settle()
                    meas, err = sensor.getRawData()
                    self.assertTrue( err.isOk(), f"Measurement failed: {err}." )
                    for idx in range( SDUT.CHANNEL_NUM ):
                        akk[idx] += meas[idx]
                for idx in range( SDUT.CHANNEL_NUM ):
                    akk[idx] /= 10
                xdat, err = sensor.rawToIntensity( akk )
                self.assertTrue( err.isOk(), f"Compensation failed: {err}." )
                logging.info("%4.1f, %3d,  %5d, %5d,  %5d, %5d,  %5d, %5d,  %5d, %5d,  %5d, %5d,  %5d, %5d",
                             gn, exp,
                             akk[0], xdat[0],
                             akk[1], xdat[1],
                             akk[2], xdat[2],
                             akk[3], xdat[3],
                             akk[4], xdat[4],
                             akk[5], xdat[5] )
        err = sensor.close()
        self.assertTrue( err.isOk() )

    #@unittest.skip("Disabled for easier diagnostics.")
    def test_interrupt(self):
        global config
        cfg = config.copy()
        cfg["light.int.gpio.pinDesignator"] = 6 # Spectrometer click board at port #1
        cfg["light.int.cfg"] = SDUT.GPIO1_CFG_PUSH_PULL
        SDUT.Params_init( cfg )
        sensor = SDUT()
        self.assertIsNotNone( sensor )
        err = sensor.open(cfg)
        self.assertTrue( err.isOk(), f"Open failed: {err}." )

        logging.info( "Next data - with interrupts" )
        for cnt in range(10):
            meas, err = sensor.getNextData()
            self.assertTrue( err.isOk(), f"Measurement failed: {err}." )
            logging.info("  %d      %d    %d    %d    %d    %d    %d", cnt,
                         meas[0], meas[1], meas[2], meas[3], meas[4], meas[5])
        logging.info( "Latest data - with interrupts" )
        for cnt in range(10):
            sensor.settle()
            meas, err = sensor.getLatestData()
            self.assertTrue( err.isOk(), f"Measurement failed: {err}." )
            logging.info("  %d      %d    %d    %d    %d    %d    %d", cnt,
                         meas[0], meas[1], meas[2], meas[3], meas[4], meas[5])

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

