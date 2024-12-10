"""
"""
import argparse
import sys
import time
import unittest

from philander.gpio import GPIO
from philander.systypes import ErrorCode
from philander.vibrasense import VibraSense as Driver

config = {
    #"VibraSense.slot"   :   1,
    "VibraSense.int.gpio.pinDesignator": 0, 
    "VibraSense.int.gpio.pull"         :   GPIO.PULL_NONE,
    "VibraSense.int.gpio.trigger"      :   GPIO.TRIGGER_EDGE_RISING,
    "VibraSense.enable.gpio.pinDesignator": 1, 
}

# We use a global variable to make calls of the event handler
# visible to the tester.
callReflect = 0

# Callback handler
def handlerFunc( *arg):
    global callReflect
    if len(arg) > 0:
        callReflect = arg[0]
    else:
        callReflect = callReflect+1


class TestVibrasense( unittest.TestCase ):
            
    def test_paramsinit(self):
        cfg = dict()
        Driver.Params_init( cfg )
        self.assertIsNotNone( cfg )
        self.assertTrue( "VibraSense.slot" in cfg )
        self.assertEqual( cfg["VibraSense.slot"], Driver.SLOT_DEFAULT )
        self.assertTrue( "VibraSense.int.gpio.pinNumbering" in cfg )
        self.assertEqual( cfg["VibraSense.int.gpio.pinNumbering"], GPIO.PINNUMBERING_BOARD )
        self.assertTrue( "VibraSense.int.gpio.pinDesignator" in cfg )
        self.assertEqual( cfg["VibraSense.int.gpio.pinDesignator"], Driver.SLOT1_PIN_SIGNAL )
        self.assertTrue( "VibraSense.int.gpio.direction" in cfg )
        self.assertEqual( cfg["VibraSense.int.gpio.direction"], GPIO.DIRECTION_IN )
        self.assertTrue( "VibraSense.int.gpio.pull" in cfg )
        self.assertEqual( cfg["VibraSense.int.gpio.pull"], GPIO.PULL_DOWN )
        self.assertTrue( "VibraSense.int.gpio.trigger" in cfg )
        self.assertEqual( cfg["VibraSense.int.gpio.trigger"], GPIO.TRIGGER_EDGE_RISING )
        self.assertTrue( "VibraSense.int.gpio.bounce" in cfg )
        self.assertEqual( cfg["VibraSense.int.gpio.bounce"], Driver.DEBOUNCE_MS )
        self.assertTrue( "VibraSense.enable.gpio.pinNumbering" in cfg )
        self.assertEqual( cfg["VibraSense.enable.gpio.pinNumbering"], GPIO.PINNUMBERING_BOARD )
        self.assertTrue( "VibraSense.enable.gpio.pinDesignator" in cfg )
        self.assertEqual( cfg["VibraSense.enable.gpio.pinDesignator"], Driver.SLOT1_PIN_ENABLE )
        self.assertTrue( "VibraSense.enable.gpio.direction" in cfg )
        self.assertEqual( cfg["VibraSense.enable.gpio.direction"], GPIO.DIRECTION_OUT )
        self.assertTrue( "VibraSense.enable.gpio.level" in cfg )
        self.assertEqual( cfg["VibraSense.enable.gpio.level"], GPIO.LEVEL_HIGH )
        cfg = { "VibraSense.int.gpio.pinDesignator": 0, }
        Driver.Params_init( cfg )
        self.assertIsNotNone( cfg )
        self.assertTrue( "VibraSense.int.gpio.direction" in cfg )
        self.assertEqual( cfg["VibraSense.int.gpio.direction"], GPIO.DIRECTION_IN )
        self.assertTrue( "VibraSense.int.gpio.bounce" in cfg )
        self.assertEqual( cfg["VibraSense.int.gpio.bounce"], Driver.DEBOUNCE_MS )
        self.assertFalse( "VibraSense.slot" in cfg )
        self.assertFalse( "VibraSense.enable.gpio.pinDesignator" in cfg )
        self.assertFalse( "VibraSense.enable.gpio.direction" in cfg )
        cfg["VibraSense.enable.gpio.pinDesignator"] = 1
        Driver.Params_init( cfg )
        self.assertTrue( "VibraSense.enable.gpio.direction" in cfg )
        self.assertEqual( cfg["VibraSense.enable.gpio.direction"], GPIO.DIRECTION_OUT )
    
    
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
    
    def test_poll(self):
        global config
        cfg = config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
    
        v0, err = device.getLatestData()
        self.assertTrue( err.isOk(), f"Error: {err}." )
        t0 = time.time()
        done = False
        while not done:
            v, err = device.getLatestData()
            t = time.time()
            if (not err.isOk()) or (v!=v0) or (t-t0 > 5):
                done = True
        self.assertTrue( err.isOk(), f"Error: {err}." )
        self.assertNotEqual( v, v0, f"Output didn't change: {v}.")
    
        err = device.close()
        self.assertTrue( err.isOk() )
    

    def test_interrupt(self):
        global callReflect
        global config
        cfg = config.copy()
        Driver.Params_init( cfg )
        device = Driver()
        self.assertIsNotNone( device )
        err = device.open(cfg)
        self.assertTrue( err.isOk() )
        
        # Register handler
        device.on( GPIO.EVENT_DEFAULT, handlerFunc )
            
        # Reset indicator
        callReflect = 0

        t0 = time.time()
        done = False
        while not done:
            t = time.time()
            if (callReflect!=0) or (t-t0 > 5):
                done = True
        self.assertNotEqual( callReflect, 0 )
        
        err = device.close()
        self.assertTrue( err.isOk() )

        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", help="slot number [1|2] of the click board", default=None)
    parser.add_argument("--int", help="designator of the INT GPIO pin", default=None)
    parser.add_argument("--enable", help="designator of the EN GPIO pin", default=None)
    args, unknown = parser.parse_known_args()
    if args.slot:
        config["VibraSense.slot"] = args.slot
    if args.int:
        config["VibraSense.int.gpio.pinDesignator"] = args.int
    if args.enable:
        config["VibraSense.enable.gpio.pinDesignator"] = args.enable
    if sys.argv:
        sys.argv = [sys.argv[0],] + unknown
    unittest.main()

