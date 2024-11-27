"""
"""
import argparse
import unittest

from philander.stc311x import STC311x as Driver
from philander.stc311x_reg import ChipType, _STC311x_Reg 
from philander.battery import Level
from philander.gasgauge import SOCChangeRate, EventSource, EventContext, StatusID
from philander.gpio import GPIO
from philander.primitives import Percentage, Voltage, Current
from philander.systypes import ErrorCode


class TestSTC311x( unittest.TestCase ):

    def setUp(self):
        self.config = {
            "SerialBus.designator": 0, #"/dev/i2c-1",
            "Gasgauge.ChipType": ChipType.STC3117,
            }
        parser = argparse.ArgumentParser()
        parser.add_argument("--bus", help="designator of the i2c bus", default=None)
        parser.add_argument("--int", help="designator of the ALM GPIO pin", default=None)
        args = parser.parse_args()
        if args.bus:
            self.configSensor["SerialBus.designator"] = args.bus
        if args.int:
            self.config["Gasgauge.int.gpio.pinDesignator"] = args.int
            
    def test_paramsinit(self):
        cfg = self.config.copy()
        Driver.Params_init( cfg )
        self.assertIsNotNone( cfg )
        self.assertTrue( "SerialBusDevice.address" in cfg )
        self.assertTrue( cfg["SerialBusDevice.address"] in Driver.ADDRESSES_ALLOWED )
        self.assertTrue( "Gasgauge.ChipType" in cfg )
        self.assertEqual( cfg["Gasgauge.ChipType"], ChipType.STC3117)
        self.assertTrue( "Gasgauge.SenseResistor" in cfg )
        self.assertEqual( cfg["Gasgauge.SenseResistor"], _STC311x_Reg.CONFIG_RSENSE_DEFAULT)

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
    
    def test_info(self):
        cfg = self.config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
    
        info, err = device.getInfo()
        self.assertTrue( err.isOk(), f"getInfo: {err}." )
        validity = info.validChipID
        self.assertEqual( info.validity ^ validity, 0 )
        self.assertEqual( info.chipID, device.REGISTER.CHIP_ID, f"chipID: {info.chipID}." )
    
        err = device.close()
        self.assertTrue( err.isOk() )
    
    def test_status(self):
        cfg = self.config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
    
        info, err = device.getStatus( StatusID.batTemp )
        self.assertTrue( err.isOk(), f"getStatus(batTemp): {err}." )
        self.assertGreaterEqual( info, 0, f"batTemp={info}.")
        self.assertLessEqual( info, 100, f"batTemp={info}.")
        info, err = device.getStatus( StatusID.dieTemp )
        self.assertTrue( err.isOk(), f"getStatus(dieTemp): {err}." )
        self.assertGreaterEqual( info, 0, f"dieTemp={info}.")
        self.assertLessEqual( info, 150, f"dieTemp={info}.")
        
        err = device.close()
        self.assertTrue( err.isOk() )
    
    def test_stateOfCharge(self):
        cfg = self.config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
    
        perc = device.getStateOfCharge()
        self.assertNotEqual( perc, Percentage.invalid)
        self.assertGreaterEqual( perc, 0, f"perc={perc}.")
        self.assertLessEqual( perc, 100, f"perc={perc}.")
        
        err = device.close()
        self.assertTrue( err.isOk() )
    
    def test_changeRate(self):
        cfg = self.config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
    
        cr = device.getChangeRate()
        self.assertNotEqual( cr, SOCChangeRate.invalid)
        self.assertGreaterEqual( cr, 0, f"rate={cr}.")
        
        err = device.close()
        self.assertTrue( err.isOk() )
    
    def test_batterVoltage(self):
        cfg = self.config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
    
        voltage = device.getBatteryVoltage()
        self.assertNotEqual( voltage, Voltage.invalid)
        self.assertGreaterEqual( voltage, 0, f"voltage={voltage}.")
        self.assertLessEqual( voltage, 9000, f"voltage={voltage}.")
        
        err = device.close()
        self.assertTrue( err.isOk() )
    
    def test_batterCurrent(self):
        cfg = self.config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
    
        current = device.getBatteryCurrent()
        self.assertNotEqual( current, Current.invalid)
        self.assertGreaterEqual( current, 0, f"current={current}.")
        self.assertLessEqual( current, 3000000, f"current={current}.")
        
        err = device.close()
        self.assertTrue( err.isOk() )
    
    def test_batterCurrentAvg(self):
        cfg = self.config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
    
        current = device.getBatteryCurrentAvg()
        self.assertNotEqual( current, Current.invalid)
        self.assertGreaterEqual( current, 0, f"avgCurrent={current}.")
        self.assertLessEqual( current, 3000000, f"avgCurrent={current}.")
        
        err = device.close()
        self.assertTrue( err.isOk() )
    
    def test_RatedSOC(self):
        cfg = self.config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
    
        lvl = device.getRatedSOC()
        self.assertNotEqual( lvl, Level.invalid )
        self.assertGreaterEqual( lvl, 0, f"soc={str(lvl)} ({lvl}).")
        
        err = device.close()
        self.assertTrue( err.isOk() )
    
    def test_RatedSOCStr(self):
        cfg = self.config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
    
        lvlstr = device.getRatedSOCStr()
        self.assertIsNotNone( lvlstr )
        self.assertTrue( lvlstr )
        
        err = device.close()
        self.assertTrue( err.isOk() )
    

        
if __name__ == '__main__':
    unittest.main()

