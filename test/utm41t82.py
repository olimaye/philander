"""
"""
import logging
import time
import unittest

from philander.rtc import RTC
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

config = {\
    #"rtc.alarm2.enable":    True,
    "rtc.ft.enable":        True,
    "rtc.SerialBus.designator":   "i2c-1",
    #"watchdog.*":           10000,
}

class TestRTC_M41T82( unittest.TestCase ):

    @unittest.skip("Known working.")
    def test_open(self):
        device = RTC.getRTC( SysProvider.COMPOSITE )
        self.assertIsNotNone( device )
        cfg = config.copy()
        device.Params_init( cfg )
        self.assertTrue( cfg["rtc.alarm2.enable"] )
        self.assertTrue( cfg["rtc.ft.enable"] )
        err = device.open(cfg)
        self.assertEqual( err, ErrorCode.errOk, "Open: " + str(err) )
        
        if cfg["rtc.alarm2.enable"]:
            self.assertEqual( device.numAlarms, 2 )
            self.assertEqual( device.lenUserData, 7 )
            sval = RTC.STATUS_ALARM_0 | RTC.STATUS_ALARM_1 | \
                   RTC.STATUS_TIMER_0 | RTC.STATUS_OSC_FAIL | \
                   RTC.STATUS_BAT_LOW | RTC.STATUS_STOPPED
        else:
            self.assertEqual( device.numAlarms, 1 )
            self.assertEqual( device.lenUserData, 12 )
            self.assertEqual( device.numTimers, 1 )
            sval = RTC.STATUS_ALARM_0 | \
                   RTC.STATUS_TIMER_0 | RTC.STATUS_OSC_FAIL | \
                   RTC.STATUS_BAT_LOW | RTC.STATUS_STOPPED
        self.assertEqual( device.supportedStatus, sval )
        self.assertTrue( device.isOpen )
        self.assertEqual( device.provider, SysProvider.COMPOSITE )
        self.assertIsNotNone( device.lastKnownAlive )
        self.assertGreaterEqual( len(device.lastKnownAlive), 8 )
        self.assertGreaterEqual( device.lastKnownAlive[0], 2026 )
        self.assertIsNotNone( device._serbusdev )
        self.assertEqual( device._bitFT, cfg["rtc.ft.enable"] )

        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )
        self.assertFalse( device.isOpen )

    @unittest.skip("Known working.")
    def test_getDateTime(self):
        device = RTC.getRTC( SysProvider.COMPOSITE )
        self.assertIsNotNone( device )
        cfg = config.copy()
        device.Params_init( cfg )
        err = device.open(cfg)
        self.assertEqual( err, ErrorCode.errOk, "Open: " + str(err) )

        delay = 0.5
        last = device.getDateTime()
        for _ in range(5):
            time.sleep(delay)
            now = device.getDateTime()
            self.assertIsNotNone( now )
            self.assertGreaterEqual( len(now), 8 )
            self.assertEqual( now[0], last[0] )     # year
            self.assertEqual( now[1], last[1] )     # month
            self.assertEqual( now[2], last[2] )     # day
            self.assertGreaterEqual( now[3], last[3] ) # hour
            if now[4] > 0:      # minute
                self.assertGreaterEqual( now[4], last[4] )
            if now[5] > 0:      # second
                self.assertGreaterEqual( now[5], last[5] )
            self.assertNotEqual( now[6], last[6] )  # microseconds
            diff = (now[3] - last[3]) * 3600
            diff += (now[4] - last[4]) * 60
            diff += (now[5] - last[5])
            diff += (now[6] - last[6]) / 1000000
            self.assertAlmostEqual( diff, delay, places=1 )
            last = now
            
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )
    
    
    
        
if __name__ == '__main__':
    logger = logging.getLogger("philander.m41t82")
    logger.setLevel( logging.INFO )
    hdlr = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(name)s.%(funcName)s %(levelname)s> %(message)s")
    hdlr.setFormatter(formatter)
    logger.addHandler( hdlr )
    
    unittest.main()


