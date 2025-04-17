"""
"""
from time import sleep
import unittest

from philander.gpio import GPIO
from philander.pwm import PWM
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

class TestPWM_Impl( unittest.TestCase ):

    TIME_TO_CHECK   = 5     # Time in seconds to look at the lab equipment
    TIME_TO_EXPERIMENT = 20 # Time in seconds to experiment and adjust
    
    
    ProviderUnderTest = SysProvider.MICROPYTHON
    outPin          = 4
    pwmFrequency    = 100000
    pwmDuty         = 35
    
    #@unittest.skip("Known working.")
    def test_open(self):
        device = PWM.getPWM( self.ProviderUnderTest )
        self.assertIsNotNone( device )
        params = {\
            "pwm.pinDesignator":   self.outPin,
            "pwm.frequency"    :   self.pwmFrequency,
            "pwm.duty"         :   self.pwmDuty,
            }
        device.Params_init( params )
        self.assertEqual( params["pwm.pinNumbering"], GPIO.PINNUMBERING_BCM )
        self.assertEqual( params["pwm.pinDesignator"], self.outPin )
        self.assertEqual( params["pwm.frequency"], self.pwmFrequency )
        self.assertEqual( params["pwm.duty"], self.pwmDuty )
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk, "Open: " + str(err) )
        self.assertEqual( device.duty, self.pwmDuty )
        self.assertEqual( device.frequency, self.pwmFrequency )
        self.assertTrue( device.isOpen )
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )
        self.assertFalse( device.isOpen )

    #@unittest.skip("Known working.")
    def test_frequencies(self):
        device = PWM.getPWM( self.ProviderUnderTest )
        self.assertIsNotNone( device )
        params = {\
            "pwm.pinDesignator":   self.outPin,
            "pwm.frequency"    :   self.pwmFrequency,
            "pwm.duty"         :   self.pwmDuty,
            }
        device.Params_init( params )
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk, "Open: " + str(err) )
        err = device.start()
        self.assertEqual( err, ErrorCode.errOk, "Start: " + str(err) )
        testvec = (10000, 20000, 37526, 50000, 83175, 100000, 200000, 420000, 500000, 1000000)
        for val in testvec:
            #print(val)
            err = device.setFrequency( val )
            self.assertEqual( err, ErrorCode.errOk, "setFrequency("+str(val)+"): "+str(err) )
            sleep(self.TIME_TO_CHECK)
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )
    
    #@unittest.skip("Known working.")
    def test_duty(self):
        device = PWM.getPWM( self.ProviderUnderTest )
        self.assertIsNotNone( device )
        params = {\
            "pwm.pinDesignator":   self.outPin,
            "pwm.frequency"    :   self.pwmFrequency,
            "pwm.duty"         :   self.pwmDuty,
            }
        device.Params_init( params )
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk, "Open: " + str(err) )
        err = device.start()
        self.assertEqual( err, ErrorCode.errOk, "Start: " + str(err) )
        testvec = (10, 20, 50, 100, 83, 0, 45)
        for val in testvec:
            #print(val)
            err = device.setDuty( val )
            self.assertEqual( err, ErrorCode.errOk, "setDuty("+str(val)+"): "+str(err) )
            err = device.start()
            self.assertEqual( err, ErrorCode.errOk, "start()"+str(err) )
            sleep(self.TIME_TO_CHECK)
            err = device.start( (val+5) % 100 )
            self.assertEqual( err, ErrorCode.errOk, "start()"+str(err) )
            sleep(self.TIME_TO_CHECK)
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )
    
    #@unittest.skip("Known working.")
    def test_startstop(self):
        device = PWM.getPWM( self.ProviderUnderTest )
        self.assertIsNotNone( device )
        params = {\
            "pwm.pinDesignator":   self.outPin,
            "pwm.frequency"    :   self.pwmFrequency,
            "pwm.duty"         :   self.pwmDuty,
            }
        device.Params_init( params )
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk, "Open: " + str(err) )
        print()
        print("*** start ***")
        print("start(), f=", device.frequency, " d=", device.duty)
        err = device.start()
        self.assertEqual( err, ErrorCode.errOk, "Start: " + str(err) )
        sleep(self.TIME_TO_CHECK)
        print("*** stop ***")
        print("stop().")
        err = device.stop()
        self.assertEqual( err, ErrorCode.errOk, "Stop: " + str(err) )
        sleep(self.TIME_TO_CHECK)
        print("start(0), f=", device.frequency)
        err = device.start(0)
        self.assertEqual( err, ErrorCode.errOk, "Start(0): " + str(err) )
        sleep(self.TIME_TO_CHECK)
        print("stop().")
        err = device.stop()
        self.assertEqual( err, ErrorCode.errOk, "Stop: " + str(err) )
        sleep(self.TIME_TO_CHECK)
        print("stop().")
        err = device.stop()
        self.assertEqual( err, ErrorCode.errOk, "Stop: " + str(err) )
        sleep(self.TIME_TO_CHECK)
        print("start(), f=", device.frequency, " d=", device.duty)
        err = device.start()
        self.assertEqual( err, ErrorCode.errOk, "Start: " + str(err) )
        sleep(self.TIME_TO_CHECK)
        print("*** start ***")
        print("start(50), f=", device.frequency)
        err = device.start( 50 )
        self.assertEqual( err, ErrorCode.errOk, "Start: " + str(err) )
        sleep(self.TIME_TO_CHECK)
        print("start(60), f=", device.frequency)
        err = device.start( 60 )
        self.assertEqual( err, ErrorCode.errOk, "Start: " + str(err) )
        sleep(self.TIME_TO_CHECK)
        print("setFreq(", self.pwmFrequency // 2, ")")
        err = device.setFrequency( self.pwmFrequency // 2 )
        self.assertEqual( err, ErrorCode.errOk, "setFreq: " + str(err) )
        sleep(self.TIME_TO_CHECK)
        print("setDuty(30)")
        err = device.setDuty( 30 )
        self.assertEqual( err, ErrorCode.errOk, "setDuty: " + str(err) )
        sleep(self.TIME_TO_CHECK)
        print("*** stop ***")
        print("setDuty(0)")
        err = device.setDuty( 0 )
        self.assertEqual( err, ErrorCode.errOk, "setDuty(0): " + str(err) )
        sleep(self.TIME_TO_CHECK)
        print("start(), f=", device.frequency, " d=", device.duty)
        err = device.start()
        self.assertEqual( err, ErrorCode.errOk, "Start: " + str(err) )
        sleep(self.TIME_TO_CHECK)
        print("stop().")
        err = device.stop()
        self.assertEqual( err, ErrorCode.errOk, "Stop: " + str(err) )
        sleep(self.TIME_TO_CHECK)
        print("start(), f=", device.frequency, " d=", device.duty)
        err = device.start()
        self.assertEqual( err, ErrorCode.errOk, "Start: " + str(err) )
        sleep(self.TIME_TO_CHECK)
        print("*** start ***")
        print("setDuty(45)")
        err = device.setDuty( 45 )
        self.assertEqual( err, ErrorCode.errOk, "setDuty: " + str(err) )
        sleep(self.TIME_TO_CHECK)
        print("start(), f=", device.frequency, " d=", device.duty)
        err = device.start()
        self.assertEqual( err, ErrorCode.errOk, "Start: " + str(err) )
        sleep(self.TIME_TO_CHECK)        
        print("*** end ***")
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )
        
    #@unittest.skip("Known working.")
    def test_operation(self):
        device = PWM.getPWM( self.ProviderUnderTest )
        self.assertIsNotNone( device )
        params = {\
            "pwm.pinDesignator":   self.outPin,
            "pwm.frequency"    :   self.pwmFrequency,
            "pwm.duty"         :   self.pwmDuty,
            }
        device.Params_init( params )
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk, "Open: " + str(err) )
        err = device.start()
        self.assertEqual( err, ErrorCode.errOk, "Start: " + str(err) )
        sleep(self.TIME_TO_EXPERIMENT)
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )
    
        
if __name__ == '__main__':
    unittest.main()

