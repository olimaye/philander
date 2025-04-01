"""
"""
import unittest

from test.utaccel import TestAccel
from test.utactuator import TestActuator
from test.utadc import TestADC
from test.utbattery import TestBattery
#from test.utbutton import TestButton
from test.utdictionary import TestDictionary
from test.utimath import TestIMath
from test.utinterruptable import TestInterruptable
from test.utpenum import TestPenum
from test.utpotentiometer import TestPotentiometer
from test.utpymitter import TestPymitter
from test.utthermometer import TestThermometer

def suite():
    suite = unittest.TestSuite()
    suite.addTest( TestAccel() )
    suite.addTest( TestActuator() )
    suite.addTest( TestADC() )
    suite.addTest( TestBattery )
    #suite.addTest( TestButton )
    suite.addTest( TestDictionary )
    suite.addTest( TestIMath )
    suite.addTest( TestInterruptable )
    suite.addTest( TestPenum )
    suite.addTest( TestPotentiometer )
    suite.addTest( TestPymitter )
    suite.addTest( TestThermometer )
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())