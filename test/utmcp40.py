"""
"""
import argparse
import sys
#import time
import unittest

from philander.mcp40 import MCP40 as Driver
from philander.systypes import ErrorCode

config = {
    "SerialBus.designator"      : 0, #"/dev/i2c-1",
    #"SerialBusDevice.address"   : 0x2E,
    "Potentiometer.resistance.max": 100000,
    }

class TestMCP40( unittest.TestCase ):
            
    def test_paramsinit(self):
        global config
        cfg = config.copy()
        Driver.Params_init( cfg )
        self.assertIsNotNone( cfg )
        self.assertTrue( "SerialBusDevice.address" in cfg )
        self.assertTrue( cfg["SerialBusDevice.address"] in Driver.ADDRESSES_ALLOWED, f"SerialBusDevice.address={cfg['SerialBusDevice.address']}." )
        key = "Potentiometer.resistance.max"
        self.assertTrue( key in cfg )
        self.assertTrue( isinstance(cfg[key], (int, float, complex)) and not isinstance(cfg[key], bool) )
        self.assertTrue( cfg[key] > 0, f"{key}={cfg[key]}." )
        key = "Potentiometer.digital.max"
        self.assertTrue( key in cfg )
        self.assertTrue( isinstance(cfg[key], (int, float, complex)) and not isinstance(cfg[key], bool) )
        self.assertTrue( cfg[key] > 0, f"{key}={cfg[key]}." )
        self.assertLessEqual( cfg[key], 0xFFFFFFFF )
        

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
    
    def test_digital(self):
        global config
        cfg = config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
    
        maxValue = device._digitalMax
        for value in range( maxValue+1 ):
            err = device.setDigital( value )
            self.assertTrue( err.isOk(), f"setDigital({value}): {err}.")
            nValue, err = device.getDigital()
            self.assertTrue( err.isOk(), f"getDigital(): {err}.")
            self.assertEqual( nValue, value, f"got {nValue} after set {value}.")

        oldValue, err = device.getDigital()
        self.assertTrue( err.isOk(), f"getDigital(): {err}.")
        value = maxValue+1
        err = device.setDigital( value )
        self.assertFalse( err.isOk(), f"setDigital({value}): {err}.")
        value = maxValue+17
        err = device.setDigital( value )
        self.assertFalse( err.isOk(), f"setDigital({value}): {err}.")
        value = -1
        err = device.setDigital( value )
        self.assertFalse( err.isOk(), f"setDigital({value}): {err}.")
        value, err = device.getDigital()
        self.assertTrue( err.isOk(), f"getDigital(): {err}.")
        self.assertEqual( value, oldValue, f"internal value changed from {oldValue} to {value}.")
        err = device.close()
        self.assertTrue( err.isOk() )

    # def test_manual(self):
    #     global config
    #     cfg = config.copy()
    #     Driver.Params_init( cfg )
    #     device = Driver()
    #     self.assertIsNotNone( device )
    #     err = device.open(cfg)
    #     self.assertTrue( err.isOk() )
    #
    #     for value in (0, 30, 50, 70, 100):
    #         print("Setting to: ", value)
    #         err = device.setPercentage( value )
    #         self.assertTrue( err.isOk(), f"set({value}): {err}.")
    #         time.sleep(5)
    #
    #     err = device.close()
    #     self.assertTrue( err.isOk() )
    
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--bus", help="designator of the i2c bus", default=None)
    parser.add_argument("--adr", help="i2c address of the device", type=int, default=None)
    parser.add_argument("--rmax", help="maximum resistance in Ohms.", type=int, default=None)
    args, unknown = parser.parse_known_args()
    if args.bus:
        config["SerialBus.designator"] = args.bus
    if args.adr:
        config["SerialBusDevice.address"] = args.adr
    if args.rmax:
            config["Potentiometer.resistance.max"] = args.rmax
    if sys.argv:
        sys.argv = [sys.argv[0],] + unknown
    unittest.main()

