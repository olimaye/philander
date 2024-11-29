"""
"""
import unittest
from philander.battery import Capacity, Level, Status
from philander.primitives import Percentage

class TestBattery( unittest.TestCase ):
    
    def test_level(self):
        # Micropython's unittest doesn't support assertGreater/Less() etc.
        self.assertTrue(Level.medium.value > Level.empty.value)
        self.assertTrue( Level.low.value < Level.full.value)
        self.assertTrue( 65 > Level.medium.value )
        self.assertTrue( 4 < Level.good.value )
        self.assertTrue( Level.max.value > 37 )
        self.assertTrue( Level.deepDischarge.value < 10)
        self.assertEqual( Level.invalid.value, Percentage.invalid )
    
    def test_fromPercentage(self):
        for pv in range(0, 101):
            p = Percentage(pv)
            lvl = Level.fromPercentage(p)
            self.assertGreaterEqual( p, lvl.value )
            lvl = Level.fromPercentage(pv)
            self.assertGreaterEqual( pv, lvl.value )
        self.assertGreaterEqual( Level.fromPercentage(100).value, Level.full.value)
        self.assertEqual( Level.fromPercentage(100), Level.max)
        self.assertLessEqual( Level.fromPercentage(0).value, Level.empty.value)
        self.assertEqual( Level.fromPercentage(0), Level.min)

        self.assertEqual( Level.fromPercentage("hi"), Level.invalid)
        self.assertEqual( Level.fromPercentage(-3), Level.min)
        self.assertEqual( Level.fromPercentage(120), Level.max)
        
    def test_capacity(self):
        for val in [0, 120, 1000, 5000, 20000, 600, 9443, -400, "450",
                    127.0, 534.10798, 1234.879]:
            cap=Capacity(val)
            self.assertIsNotNone( cap )
            self.assertEqual( cap, int(val) )
            self.assertNotEqual( cap, Capacity.invalid)
            self.assertIsNot( cap, Capacity.invalid )
        for val in [None, "Hello World!", Level.medium]:
            self.assertRaises( (TypeError,ValueError), lambda: Capacity(val) )

    def test_status(self):
        stat = Status( 0x03C3 )
        self.assertIsNotNone( stat )
        self.assertNotEqual( stat, Status.normal )
        self.assertTrue( stat & Status.problemPhysical )
        self.assertTrue( stat & Status.removed )
        self.assertTrue( stat & Status.broken )
        self.assertTrue( stat & Status.problemElectrical )
        self.assertFalse( stat & Status.empty )
        self.assertFalse( stat & Status.low )
        self.assertTrue( stat & Status.overvoltage )
        self.assertTrue( stat & Status.overcurrent )
        self.assertTrue( stat & Status.problemThermal )
        self.assertTrue( stat & Status.cold )
        self.assertTrue( stat & Status.hot )
        self.assertTrue( stat & Status.coldOrHot )
        self.assertNotEqual( stat, Status.unknown )
        
if __name__ == '__main__':
    unittest.main()

