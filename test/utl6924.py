"""
"""
import argparse
import sys
import unittest

from philander.battery import Status as BatStatus
from philander.charger import Status as ChgStatus, DCStatus, PowerSrc, TemperatureRating, ChargerError
from philander.gpio import GPIO
from philander.l6924 import L6924 as Driver
from philander.systypes import ErrorCode

config = {
    "L6924.St1.gpio.pinDesignator": 2, 
    "L6924.St2.gpio.pinDesignator": 3, 
}

class TestL6924( unittest.TestCase ):
            
    def test_paramsinit(self):
        global config
        cfg = config.copy()
        Driver.Params_init( cfg )
        self.assertIsNotNone( cfg )
        self.assertTrue( "L6924.St1.gpio.direction" in cfg )
        self.assertEqual( cfg["L6924.St1.gpio.direction"], GPIO.DIRECTION_IN )
        self.assertTrue( "L6924.St1.gpio.pull" in cfg )
        self.assertEqual( cfg["L6924.St1.gpio.pull"], GPIO.PULL_UP )
        self.assertTrue( "L6924.St1.gpio.inverted" in cfg )
        self.assertTrue( cfg["L6924.St1.gpio.inverted"] )
        self.assertTrue( "L6924.St2.gpio.direction" in cfg )
        self.assertEqual( cfg["L6924.St2.gpio.direction"], GPIO.DIRECTION_IN )
        self.assertTrue( "L6924.St2.gpio.pull" in cfg )
        self.assertEqual( cfg["L6924.St2.gpio.pull"], GPIO.PULL_UP )
        self.assertTrue( "L6924.St2.gpio.inverted" in cfg )
        self.assertTrue( cfg["L6924.St2.gpio.inverted"] )

    def test_open(self):
        global config
        cfg = config.copy()
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

    def test_infostatus(self):
        global config
        cfg = config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
        
        _, err = device.getInfo()
        self.assertTrue( err.isOk(), f"getInfo: {err}." )
        err = device.isBatteryPresent()
        self.assertTrue( err.isOk(), f"isBatteryPresent: {err}." )
        num = device.getNumCells()
        self.assertEqual( num, 1, f"getNumCells: {num}." )
        stat = device.getBatStatus()
        self.assertGreaterEqual( stat.value, BatStatus.normal.value, f"getBatStatus: {stat}." )
        self.assertLessEqual( stat.value, BatStatus.unknown.value, f"getBatStatus: {stat}." )
        stat = device.getChgStatus()
        self.assertIsInstance( stat, ChgStatus, f"getChgStatus: {stat}." )
        stat = device.getDCStatus()
        self.assertIsInstance( stat, DCStatus, f"getDCStatus: {stat}." )
        src = device.getPowerSrc()
        self.assertIsInstance( src, PowerSrc, f"getPowerSrc: {src}." )
        stat = device.getChargerTempStatus()
        self.assertIsInstance( stat, TemperatureRating, f"getChargerTempStatus: {stat}." )
        stat = device.getBatteryTempStatus()
        self.assertIsInstance( stat, TemperatureRating, f"getBatteryTempStatus: {stat}." )
        err = device.getError()
        self.assertIsInstance( err, ChargerError, f"getError: {err}." )

        err = device.close()
        self.assertTrue( err.isOk() )
    

    def test_restart(self):
        global config
        cfg = config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
        
        err = device.restartCharging()
        self.assertTrue( err.isOk() )
        err = device.restartCharging()
        self.assertTrue( err.isOk() )
        err = device.restartCharging()
        self.assertTrue( err.isOk() )
        
        err = device.close()
        self.assertTrue( err.isOk() )

        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--st1", help="designator of the ST1 GPIO pin", default=None)
    parser.add_argument("--st2", help="designator of the ST2 GPIO pin", default=None)
    args, unknown = parser.parse_known_args()
    if args.st1:
        config["L6924.St1.gpio.pinDesignator"] = args.st1
    if args.st2:
        config["L6924.St2.gpio.pinDesignator"] = args.st2
    if sys.argv:
        sys.argv = [sys.argv[0],] + unknown
    unittest.main()

