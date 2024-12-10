"""
"""
import argparse
import sys
import unittest

from philander.stc311x import OperatingMode
from philander.stc3117 import STC3117 as Driver
from philander.battery import Level
from philander.gasgauge import SOCChangeRate, EventSource, EventContext, StatusID
from philander.gpio import GPIO
from philander.primitives import Percentage, Voltage, Current
from philander.systypes import ErrorCode, RunLevel

config = {
    "SerialBus.designator": 0, #"/dev/i2c-1",
    }

class TestSTC3117( unittest.TestCase ):
            
    def test_paramsinit(self):
        global config
        cfg = config.copy()
        Driver.Params_init( cfg )
        self.assertIsNotNone( cfg )
        self.assertTrue( "SerialBusDevice.address" in cfg )
        self.assertTrue( cfg["SerialBusDevice.address"] in Driver.ADDRESSES_ALLOWED )
        self.assertTrue( "Gasgauge.SenseResistor" in cfg )
        self.assertEqual( cfg["Gasgauge.SenseResistor"], Driver.RSENSE_DEFAULT)
        self.assertTrue( "Gasgauge.battery.capacity" in cfg )
        self.assertEqual( cfg["Gasgauge.battery.capacity"], Driver.BAT_CAPACITY_DEFAULT)
        self.assertTrue( "Gasgauge.battery.impedance" in cfg )
        self.assertEqual( cfg["Gasgauge.battery.impedance"], Driver.BAT_IMPEDANCE_DEFAULT)
        self.assertTrue( "Gasgauge.alarm.soc" in cfg )
        self.assertEqual( cfg["Gasgauge.alarm.soc"], Driver.ALARM_SOC_DEFAULT)
        self.assertTrue( "Gasgauge.alarm.voltage" in cfg )
        self.assertEqual( cfg["Gasgauge.alarm.voltage"], Driver.ALARM_VOLTAGE_DEFAULT)
        self.assertTrue( "Gasgauge.relax.current" in cfg )
        self.assertEqual( cfg["Gasgauge.relax.current"], Driver.RELAX_CURRENT_DEFAULT)
        self.assertTrue( "Gasgauge.relax.timer" in cfg )
        self.assertEqual( cfg["Gasgauge.relax.timer"], Driver.RELAX_TIMER_DEFAULT)
        self.assertTrue( "Gasgauge.int.gpio.direction" in cfg )
        self.assertEqual( cfg["Gasgauge.int.gpio.direction"], GPIO.DIRECTION_IN)
        self.assertTrue( "Gasgauge.int.gpio.trigger" in cfg )
        self.assertEqual( cfg["Gasgauge.int.gpio.trigger"], GPIO.TRIGGER_EDGE_FALLING)
        self.assertTrue( "Gasgauge.int.gpio.bounce" in cfg )
        self.assertEqual( cfg["Gasgauge.int.gpio.bounce"], GPIO.BOUNCE_NONE)

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
    
    def test_info(self):
        global config
        cfg = config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
    
        info, err = device.getInfo()
        self.assertTrue( err.isOk(), f"getInfo: {err}." )
        self.assertTrue( info.validity & info.validChipID )
        self.assertEqual( info.chipID, device.REGISTER.CHIP_ID, f"chipID: {info.chipID}." )
        self.assertTrue( info.validity & info.validModelID )
        self.assertEqual( info.modelID, device.MODEL_ID, f"modelID: {info.modelID}.")
    
        err = device.close()
        self.assertTrue( err.isOk() )
    
    def test_status(self):
        global config
        cfg = config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
    
        info, err = device.getStatus( StatusID.dieTemp )
        self.assertTrue( err.isOk(), f"getStatus(dieTemp): {err}." )
        self.assertGreaterEqual( info, 0, f"dieTemp={info}.")
        self.assertLessEqual( info, 150, f"dieTemp={info}.")
        om = device._getOperatingMode()
        self.assertNotEqual( om, OperatingMode.opModeUnknown, f"OpMode={om}.")
        self.assertNotEqual( om, OperatingMode.opModeStandby, f"OpMode={om}.")
        
        err = device.close()
        self.assertTrue( err.isOk() )
    
    def test_stateOfCharge(self):
        global config
        cfg = config.copy()
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
        global config
        cfg = config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
    
        # Change rate is only available in voltage mode (sleep)
        err = device.setRunLevel(RunLevel.sleep)
        self.assertTrue( err.isOk() )
        cr = device.getChangeRate()
        self.assertNotEqual( cr, SOCChangeRate.invalid)
        self.assertGreaterEqual( cr, 0, f"rate={cr}.")
        
        err = device.close()
        self.assertTrue( err.isOk() )
    
    def test_batterVoltage(self):
        global config
        cfg = config.copy()
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
        global config
        cfg = config.copy()
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
        global config
        cfg = config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
    
        # Average current is only available in mixed mode (active)
        err = device.setRunLevel(RunLevel.active)
        self.assertTrue( err.isOk() )
        current = device.getBatteryCurrentAvg()
        self.assertNotEqual( current, Current.invalid)
        self.assertGreaterEqual( current, 0, f"avgCurrent={current}.")
        self.assertLessEqual( current, 3000000, f"avgCurrent={current}.")
        
        err = device.close()
        self.assertTrue( err.isOk() )
    
    def test_RatedSOC(self):
        global config
        cfg = config.copy()
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
        global config
        cfg = config.copy()
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--bus", help="designator of the i2c bus", default=None)
    parser.add_argument("--int", help="designator of the ALM GPIO pin", default=None)
    args, unknown = parser.parse_known_args()
    if args.bus:
        config["SerialBus.designator"] = args.bus
    if args.int:
        config["Gasgauge.int.gpio.pinDesignator"] = args.int
    if sys.argv:
        sys.argv = [sys.argv[0],] + unknown
    unittest.main()

