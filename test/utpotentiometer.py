"""
"""
import unittest
import time

from philander.potentiometer import Potentiometer
from philander.systypes import ErrorCode

class SimPot( Potentiometer ):
    
    def __init__(self):
        self.value = 0
        
    def setDigital(self, digital):
        err = Potentiometer._checkRange( digital, self._digitalMax )
        if err.isOk():
            self.value = digital
        return ErrorCode.errOk
    
    def getDigital(self):
        return self.value, ErrorCode.errOk
        
class TestPotentiometer( unittest.TestCase ):
    
    def test_paramsinit(self):
        settings = dict()
        Potentiometer.Params_init( settings )
        self.assertTrue( "Potentiometer.resistance.max" in settings)
        self.assertEqual( settings["Potentiometer.resistance.max"], Potentiometer.DEFAULT_RESISTANCE_MAX)
        self.assertTrue( "Potentiometer.digital.max" in settings)
        self.assertEqual( settings["Potentiometer.digital.max"], Potentiometer.DEFAULT_DIGITAL_MAX)
        
    def test_rangemap(self):
        vec = (
            (0, 1000, 1023, 0, True),
            (7, 1000, 1023, 7, True),
            (83.416, 1000, 1023, 85, True),
            (197, 1000, 1023, 202, True),
            (256, 1000, 1023, 262, True),
            (312, 1000, 1023, 319, True),
            (512, 1000, 1023, 524, True),
            (837.0, 1000, 1023, 856, True),
            (999, 1000, 1023, 1022, True),
            (1000, 1000, 1023, 1023, True),
            (1001, 1000, 1023, 0, False),
            (1312, 1000, 1023, 0, False),
            (-4, 1000, 1023, 0, False),
            )
        for s, sM, dM, td, flagOk in vec:
            dest, err = Potentiometer._rangeMap( s, sM, dM )
            self.assertEqual( err.isOk(), flagOk )
            if err.isOk():
                self.assertEqual( dest, td )
                newS, err = Potentiometer._rangeMap( dest, dM, sM )
                self.assertTrue( err.isOk() )
                self.assertLessEqual( newS - s, 0.5 )
                self.assertLessEqual( s - newS, 0.5 )

    def test_checkrange(self):
        vec = (
            (0, 10, True),
            (1, 10, True),
            (2.7, 10, True),
            (7, 10, True),
            (9.2, 10, True),
            (10, 10, True),
            (10.3, 10, False),
            (11, 10, False),
            (-0.2, 10, False),
            (-1, 10, False),
            (13, 999, True),
            (723, 999, True),
            (1000, 999, False),
            (0x07, 0xFF, True),
            (0x7F, 0xFF, True),
            (0x80, 0xFF, True),
            (0xF2, 0xFF, True),
            (0xFF, 0xFF, True),
            (0x100, 0xFF, False),
            )
        for val, vmax, flagOk in vec:
            err = Potentiometer._checkRange( val, vmax )
            self.assertEqual( err.isOk(), flagOk )
 
    def test_getset(self):
        dmax = 7
        rmax = 20000
        ddict = {
            # d: (r, p)
            0: (0,   0),
            1: (2857,  14),
            2: (5714,  29),
            3: (8571,  43),
            4: (11429,  57),
            5: (14286,  71),
            6: (17143,  86),
            7: (20000,  100),
            }
        vr = ( # r, d
            (    0, 0), ( 1000, 0), ( 2000, 1), ( 5000, 2), ( 8000, 3),
            (10000, 4), (12900, 5), (18200, 6), (18600, 7), (20000, 7),
            )
        vp = ( # p, d
            (  0, 0), (  5, 0), ( 10, 1), ( 25, 2), ( 40, 3),
            ( 50, 4), ( 65, 5), ( 92, 6), ( 94, 7), (100, 7),
            )
        pot = SimPot()
        cfg = {
            "Potentiometer.resistance.max": rmax,
            "Potentiometer.digital.max": dmax,
            }
        Potentiometer.Params_init( cfg )
        err = pot.open(cfg)
        self.assertTrue( err.isOk() )
        for d, (r,p) in ddict.items():
            err = pot.setDigital(d)
            self.assertTrue( err.isOk() )
            val, err = pot.getDigital()
            self.assertTrue( err.isOk() )
            self.assertEqual( val, d )
            val, err = pot.getResistance()
            self.assertTrue( err.isOk() )
            self.assertEqual( val, r )
            val, err = pot.getPercentage()
            self.assertTrue( err.isOk() )
            self.assertEqual( val, p )
        for r, d in vr:
            tr, p = ddict[d]
            err = pot.setResistance(r)
            self.assertTrue( err.isOk() )
            val, err = pot.getDigital()
            self.assertTrue( err.isOk() )
            self.assertEqual( val, d )
            val, err = pot.getResistance()
            self.assertTrue( err.isOk() )
            self.assertEqual( val, tr )
            val, err = pot.getPercentage()
            self.assertTrue( err.isOk() )
            self.assertEqual( val, p )
        for p, d in vp:
            r, tp = ddict[d]
            err = pot.setPercentage(p)
            self.assertTrue( err.isOk() )
            val, err = pot.getDigital()
            self.assertTrue( err.isOk() )
            self.assertEqual( val, d )
            val, err = pot.getResistance()
            self.assertTrue( err.isOk() )
            self.assertEqual( val, r )
            val, err = pot.getPercentage()
            self.assertTrue( err.isOk() )
            self.assertEqual( val, tp )

        err = pot.close()
        self.assertTrue( err.isOk() )



if __name__ == '__main__':
    unittest.main()

