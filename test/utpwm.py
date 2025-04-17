"""
"""
import unittest

from philander.gpio import GPIO
from philander.pwm import PWM
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

class TestPWM( unittest.TestCase ):

    outPin          = 4
    pwmFrequency    = 85000
    pwmDuty         = 35
    
    #@unittest.skip("Known working.")
    def test_open(self):
        device = PWM()
        self.assertIsNotNone( device )
        self.assertEqual( device.frequency, PWM.DEFAULT_FREQUENCY, "frequency attribute wrong!" )
        self.assertEqual( device.duty, PWM.DEFAULT_DUTY, "duty attribute wrong!" )
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
    def test_setFrequencys(self):
        device = PWM()
        self.assertIsNotNone( device )
        params = {\
            "pwm.pinDesignator":   self.outPin,
            "pwm.frequency"    :   self.pwmFrequency,
            "pwm.duty"         :   self.pwmDuty,
            }
        device.Params_init( params )
        val = PWM.DEFAULT_FREQUENCY // 2
        err = device.setFrequency(val) 
        self.assertEqual( err, ErrorCode.errResourceConflict, "setFrequency(): " + str(err) )
        self.assertEqual( device.frequency, PWM.DEFAULT_FREQUENCY, "frequency attribute wrong!" )
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk, "Open: " + str(err) )
        self.assertEqual( device.frequency, self.pwmFrequency, "frequency attribute wrong!" )
        testvec = (10000, 20000, 37526, 50000, 83175, 100000, 200000, 420000, 500000, 1000000)
        for val in testvec:
            err = device.setFrequency( val )
            self.assertEqual( err, ErrorCode.errOk, "setFrequency("+str(val)+"): "+str(err) )
            self.assertEqual( device.frequency, val, "frequency attribute wrong!" )
        val = 0
        err = device.setFrequency(val) 
        self.assertEqual( err, ErrorCode.errSpecRange, "setFrequency(): " + str(err) )
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )
    
    #@unittest.skip("Known working.")
    def test_setDuty(self):
        device = PWM()
        self.assertIsNotNone( device )
        params = {\
            "pwm.pinDesignator":   self.outPin,
            "pwm.frequency"    :   self.pwmFrequency,
            "pwm.duty"         :   self.pwmDuty,
            }
        device.Params_init( params )
        val = (PWM.DEFAULT_DUTY + 12) // 100
        err = device.setDuty(val) 
        self.assertEqual( err, ErrorCode.errResourceConflict, "setDuty(): " + str(err) )
        self.assertEqual( device.duty, PWM.DEFAULT_DUTY, "duty attribute wrong!" )
        err = device.open(params)
        self.assertEqual( err, ErrorCode.errOk, "Open: " + str(err) )
        self.assertEqual( device.duty, self.pwmDuty, "duty attribute wrong!" )
        testvec = (10, 20, 50, 100, 83, 0, 45)
        for val in testvec:
            err = device.setDuty( val )
            self.assertEqual( err, ErrorCode.errOk, "setDuty("+str(val)+"): "+str(err) )
            self.assertEqual( device.duty, val, "duty attribute wrong!" )
        err = device.close()
        self.assertEqual( err, ErrorCode.errOk )
    
    
        
if __name__ == '__main__':
    unittest.main()

