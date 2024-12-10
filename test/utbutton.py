"""
"""
import argparse
import sys
import time
import unittest

from philander.button import Button
from philander.gpio import GPIO
from philander.systypes import ErrorCode

config = {
    "Button.label"               : "My nice button",
    "Button.gpio.pinDesignator"  : 6,
    "Button.gpio.pull"           : GPIO.PULL_UP,
    "Button.gpio.trigger"        : GPIO.TRIGGER_EDGE_FALLING,
}

class TestButton( unittest.TestCase ):
            
    def test_paramsinit(self):
        global config
        cfg = config.copy()
        Button.Params_init( cfg )
        self.assertIsNotNone( cfg )
        self.assertTrue( "Button.label" in cfg )
        self.assertTrue( "Button.gpio.direction" in cfg )
        self.assertEqual( cfg["Button.gpio.direction"], GPIO.DIRECTION_IN )
        self.assertTrue( "Button.gpio.bounce" in cfg )
        self.assertEqual( cfg["Button.gpio.bounce"], Button._DEBOUNCE_MS )

    def test_open(self):
        global config
        cfg = config.copy()
        Button.Params_init( cfg )
        button = Button()
        self.assertIsNotNone( button )
        # Simple open
        err = button.open(cfg)
        self.assertEqual( err, ErrorCode.errOk )
        self.assertTrue( err.isOk() )
        # Corresponding close
        err = button.close()
        self.assertTrue( err.isOk() )
        # Reopen
        err = button.open(cfg)
        self.assertTrue( err.isOk() )
        # Second open should yield an error
        err = button.open(cfg)
        self.assertFalse( err.isOk() )
        # Matching close
        err = button.close()
        self.assertTrue( err.isOk() )

    def test_label(self):
        global config
        cfg = config.copy()
        Button.Params_init( cfg )
        button = Button()
        self.assertIsNotNone( button )
        err = button.open(cfg)
        self.assertTrue( err.isOk() )
        altLabel = "This is an alternative label."
        self.assertEqual( button.label, cfg["Button.label"] )
        err = button.setLabel( altLabel )
        self.assertTrue( err.isOk() )
        self.assertEqual( button.label, altLabel )
        err = button.setLabel( cfg["Button.label"] )
        self.assertTrue( err.isOk() )
        self.assertEqual( button.label, cfg["Button.label"] )
        button.close()

    def test_working(self):
        global config
        cfg = config.copy()
        Button.Params_init( cfg )
        button = Button()
        self.assertIsNotNone( button )
        err = button.open(cfg)
        self.assertTrue( err.isOk() )
        stateNormal = button.get()
        print("\nNormal state is:", stateNormal, ". Press button now!")
        state = stateNormal
        done = False
        startTime = time.time()
        while not done:
            time.sleep(0.4)
            state = button.get()
            now = time.time()
            if (state != stateNormal):
                print("Button pressed. State is now:", state)
                done = True
            elif (now - startTime > 5):
                print("Timeout.")
                done = True
        self.assertNotEqual( stateNormal, state )
        err = button.close()
        self.assertTrue( err.isOk() )
        
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--pin", help="designator of the gpio pin", default=None)
    args, unknown = parser.parse_known_args()
    if args.pin:
        config["Button.gpio.pinDesignator"] = args.pin
    if sys.argv:
        sys.argv = [sys.argv[0],] + unknown
    unittest.main()

