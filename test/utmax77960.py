"""
"""
import argparse
import sys
import unittest

from philander.max77960 import MAX77960 as Driver

from philander.battery import Status as BatStatus
from philander.charger import Status as ChgStatus, DCStatus, PowerSrc, TemperatureRating, ChargerError
from philander.gpio import GPIO
from philander.systypes import ErrorCode

config = {
    "SerialBus.designator": 0, #"/dev/i2c-1",
    }

class TestMAX77960( unittest.TestCase ):
            
    def test_paramsinit(self):
        global config
        cfg = config.copy()
        Driver.Params_init( cfg )
        self.assertIsNotNone( cfg )
        self.assertTrue( "SerialBusDevice.address" in cfg )
        self.assertTrue( cfg["SerialBusDevice.address"] in Driver.ADDRESSES_ALLOWED )
        self.assertTrue( "Charger.Comm.Mode" in cfg )
        self.assertEqual( cfg["Charger.Comm.Mode"], Driver.COMM_MODE_I2C)
        self.assertTrue( "Charger.DisIBS" in cfg )
        self.assertEqual( cfg["Charger.DisIBS"], Driver.DISIBS_DEFAULT)
        self.assertTrue( "Charger.Mode" in cfg )
        self.assertEqual( cfg["Charger.Mode"], Driver.MODE_DEFAULT)
        self.assertTrue( "Charger.Prequal" in cfg )
        self.assertEqual( cfg["Charger.Prequal"], Driver.PQEN_DEFAULT)
        self.assertTrue( "Charger.Restart" in cfg )
        self.assertEqual( cfg["Charger.Restart"], Driver.CHG_RSTRT_DEFAULT)
        self.assertTrue( "Charger.Stat" in cfg )
        self.assertEqual( cfg["Charger.Stat"], Driver.STAT_EN_DEFAULT)
        self.assertTrue( "Charger.Timer.FastCharge" in cfg )
        self.assertEqual( cfg["Charger.Timer.FastCharge"], Driver.FCHGTIME_DEFAULT)
        self.assertTrue( "Charger.Current.FastCharge" in cfg )
        self.assertEqual( cfg["Charger.Current.FastCharge"], Driver.CHGCC_DEFAULT)
        self.assertTrue( "Charger.Timer.Topoff" in cfg )
        self.assertEqual( cfg["Charger.Timer.Topoff"], Driver.TO_TIME_DEFAULT)
        self.assertTrue( "Charger.Current.Topoff" in cfg )
        self.assertEqual( cfg["Charger.Current.Topoff"], Driver.TO_ITH_DEFAULT)
        self.assertTrue( "Charger.Voltage.ChargeTermination" in cfg )
        self.assertEqual( cfg["Charger.Voltage.ChargeTermination"], Driver.CHG_CV_PRM_DEFAULT)
        self.assertTrue( "Charger.Current.Trickle" in cfg )
        self.assertEqual( cfg["Charger.Current.Trickle"], Driver.ITRICKLE_DEFAULT)
        self.assertTrue( "Charger.Current.Batt2Sys" in cfg )
        self.assertEqual( cfg["Charger.Current.Batt2Sys"], Driver.B2SOVRC_DEFAULT)
        self.assertTrue( "Charger.Jeita" in cfg )
        self.assertEqual( cfg["Charger.Jeita"], Driver.JEITA_EN_DEFAULT)
        self.assertTrue( "Charger.Temp.Reg" in cfg )
        self.assertEqual( cfg["Charger.Temp.Reg"], Driver.REGTEMP_DEFAULT)
        self.assertTrue( "Charger.Voltage.Jeita.Term" in cfg )
        self.assertEqual( cfg["Charger.Voltage.Jeita.Term"], Driver.VCHGCV_COOL_DEFAULT)
        self.assertTrue( "Charger.Current.Jeita.FastCharge" in cfg )
        self.assertEqual( cfg["Charger.Current.Jeita.FastCharge"], Driver.ICHGCC_COOL_DEFAULT)
        self.assertTrue( "Charger.Current.Input" in cfg )
        self.assertEqual( cfg["Charger.Current.Input"], Driver.CHGIN_ILIM_DEFAULT)
        self.assertTrue( "Charger.Current.OTG" in cfg )
        self.assertEqual( cfg["Charger.Current.OTG"], Driver.OTG_ILIM_DEFAULT)
        self.assertTrue( "Charger.Voltage.MinVSys" in cfg )
        self.assertEqual( cfg["Charger.Voltage.MinVSys"], Driver.MINVSYS_DEFAULT)
        self.assertTrue( "Charger.Voltage.ChargeIn" in cfg )
        self.assertEqual( cfg["Charger.Voltage.ChargeIn"], Driver.VCHGIN_REG_DEFAULT)
        self.assertTrue( "Charger.int.gpio.direction" in cfg )
        self.assertEqual( cfg["Charger.int.gpio.direction"], GPIO.DIRECTION_IN )
        self.assertTrue( "Charger.int.gpio.trigger" in cfg )
        self.assertEqual( cfg["Charger.int.gpio.trigger"], GPIO.TRIGGER_EDGE_FALLING )
        self.assertTrue( "Charger.int.gpio.bounce" in cfg )
        self.assertEqual( cfg["Charger.int.gpio.bounce"], GPIO.BOUNCE_NONE )

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
    
        info, err = device.getInfo()
        self.assertTrue( err.isOk(), f"getInfo: {err}." )
        validity = (info.validChipID | info.validRevMajor | info.validRevMinor)
        self.assertEqual( info.validity ^ validity, 0 )
        self.assertTrue( info.chipID in [Driver.CID_REV_MIN, Driver.CID_REV_MAX], f"chipID: {info.chipID}." )
        self.assertTrue( info.revMajor in [5,6] )
        self.assertTrue( info.revMinor in range(0, 0x20) )
        err = device.checkID()
        self.assertTrue( err.isOk(), f"checkID: {err}, chipID is: {info.chipID}." )                
        err = device.isBatteryPresent()
        self.assertTrue( err.isOk(), f"isBatteryPresent: {err}." )
        num = device.getNumCells()
        self.assertEqual( num, 2, f"getNumCells: {num}." )
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
    parser.add_argument("--bus", help="designator of the i2c bus", default=None)
    parser.add_argument("--int", help="designator of the INTB GPIO pin", default=None)
    args, unknown = parser.parse_known_args()
    if args.bus:
        config["SerialBus.designator"] = args.bus
    if args.int:
        config["Charger.int.gpio.pinDesignator"] = args.int
    if sys.argv:
        sys.argv = [sys.argv[0],] + unknown
    unittest.main()

