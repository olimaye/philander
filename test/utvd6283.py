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
    
    @unittest.skip("Disabled for easier diagnostics.")
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
            sleep( 0.5 )
            meas, err = sensor.getRawData()
            self.assertTrue( err.isOk(), f"Measurement failed: {err}." )
            logging.info("  %d      %d    %d    %d    %d    %d    %d", cnt,
                         meas.get(SDUT.CHANNEL[1].name, -1),
                         meas.get(SDUT.CHANNEL[2].name, -1),
                         meas.get(SDUT.CHANNEL[3].name, -1),
                         meas.get(SDUT.CHANNEL[4].name, -1),
                         meas.get(SDUT.CHANNEL[5].name, -1),
                         meas.get(SDUT.CHANNEL[6].name, -1)
                         )
        err = sensor.close()
        self.assertTrue( err.isOk() )

    @unittest.skip("Disabled for easier diagnostics.")
    def test_latestData(self):
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
        logging.info( "Latest data" )
        logging.info( headLine )
        
        for cnt in range(10):
            sleep( 0.1 )
            meas, err = sensor.getLatestData()
            self.assertTrue( err.isOk(), f"Measurement failed: {err}." )
            logging.info("  %d      %d    %d    %d    %d    %d    %d", cnt,
                         meas.get(SDUT.CHANNEL[1].name, -1),
                         meas.get(SDUT.CHANNEL[2].name, -1),
                         meas.get(SDUT.CHANNEL[3].name, -1),
                         meas.get(SDUT.CHANNEL[4].name, -1),
                         meas.get(SDUT.CHANNEL[5].name, -1),
                         meas.get(SDUT.CHANNEL[6].name, -1)
                         )
        err = sensor.close()
        self.assertTrue( err.isOk() )

    @unittest.skip("Disabled for easier diagnostics.")
    def test_nextData(self):
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
        logging.info( "Next data" )
        logging.info( headLine )
        
        for cnt in range(10):
            meas, err = sensor.getNextData()
            self.assertTrue( err.isOk(), f"Measurement failed: {err}." )
            logging.info("  %d      %d    %d    %d    %d    %d    %d", cnt,
                         meas.get(SDUT.CHANNEL[1].name, -1),
                         meas.get(SDUT.CHANNEL[2].name, -1),
                         meas.get(SDUT.CHANNEL[3].name, -1),
                         meas.get(SDUT.CHANNEL[4].name, -1),
                         meas.get(SDUT.CHANNEL[5].name, -1),
                         meas.get(SDUT.CHANNEL[6].name, -1)
                         )
        err = sensor.close()
        self.assertTrue( err.isOk() )


    #@unittest.skip("Disabled for easier diagnostics.")
    def test_compensation(self):
        global config
        cfg = config.copy()
        cfg["light.Sensor.flicker.enable"] = False
        SDUT.Params_init( cfg )
        sensor = SDUT()
        self.assertIsNotNone( sensor )
        err = sensor.open(cfg)
        self.assertTrue( err.isOk(), f"Open failed: {err}." )
        
        cfg.clear()
        cfgParam = Configuration( item=ConfigItem.multisetting,
                                  setting=cfg )
        exposure = (120, 240, 360, 600, 960)
        gain = (1, 2.5, 5, 10, 16)
        akk = dict()
        
        headLine = "Gain, Exp,   "
        for chIdx in range( 1, 7 ):
            headLine += SDUT.CHANNEL[chIdx].name+"["+str(chIdx)+"],   "
        logging.info( "Compensated data" )
        logging.info( headLine )
        
        for gn in gain:
            cfg.clear()
            for chIdx in range( 1, SDUT.CHANNEL_NUM+1):
                name = SDUT.CHANNEL[chIdx].name
                cfg["light.Sensor."+name+".gain"] = gn
            err = sensor.configure(cfgParam)
            self.assertTrue( err.isOk(), f"Configuration of gain failed: {err}." )
            for exp in exposure:
                cfg.clear()
                cfg["light.Sensor.exposure"] = exp
                err = sensor.configure(cfgParam)
                self.assertTrue( err.isOk(), f"Configuration of exposure={exp} failed: {err}." )
                for chIdx in range( 1, SDUT.CHANNEL_NUM+1):
                    akk[chIdx] = 0
                sleepTime = (exp + config["light.Sensor.interval"] + 20) / 1000
                for cnt in range(10):
                    sleep( sleepTime )
                    meas, err = sensor.getRawData()
                    self.assertTrue( err.isOk(), f"Measurement failed: {err}." )
                    for chIdx in range( 1, SDUT.CHANNEL_NUM+1):
                        akk[chIdx] += meas.get( SDUT.CHANNEL[chIdx].name, -1 )
                for chIdx in range( 1, SDUT.CHANNEL_NUM+1):
                    akk[chIdx] /= 10
                    akk[ SDUT.CHANNEL[chIdx].name ] = akk[chIdx]
                xdat, err = sensor.raw2Abs( akk )
                self.assertTrue( err.isOk(), f"Compensation failed: {err}." )
                logging.info("  %d  %d    %d - %d    %d - %d    %d - %d    %d - %d    %d - %d    %d - %d",
                             gn, exp,
                             akk.get(SDUT.CHANNEL[1].name, -1), xdat.get(SDUT.CHANNEL[1].name, -1),
                             akk.get(SDUT.CHANNEL[2].name, -1), xdat.get(SDUT.CHANNEL[2].name, -1),
                             akk.get(SDUT.CHANNEL[3].name, -1), xdat.get(SDUT.CHANNEL[3].name, -1),
                             akk.get(SDUT.CHANNEL[4].name, -1), xdat.get(SDUT.CHANNEL[4].name, -1),
                             akk.get(SDUT.CHANNEL[5].name, -1), xdat.get(SDUT.CHANNEL[5].name, -1),
                             akk.get(SDUT.CHANNEL[6].name, -1), xdat.get(SDUT.CHANNEL[6].name, -1)
                             )
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

