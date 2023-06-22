"""
"""
import unittest
from imath import *

class TestIMath( unittest.TestCase ):
    
    def test_ispowtwo(self):
        self.assertFalse( ispowtwo(0) )
        self.assertTrue(  ispowtwo(1) )
        self.assertTrue(  ispowtwo(2) )
        self.assertFalse( ispowtwo(3) )
        self.assertTrue(  ispowtwo(4) )
        self.assertFalse( ispowtwo(5) )
        self.assertFalse( ispowtwo(6) )
        self.assertFalse( ispowtwo(7) )
        self.assertTrue(  ispowtwo(8) )
        self.assertFalse( ispowtwo(9) )
        self.assertFalse( ispowtwo(10) )
        self.assertFalse( ispowtwo(11) )
        self.assertFalse( ispowtwo(12) )
        self.assertFalse( ispowtwo(13) )
        self.assertFalse( ispowtwo(14) )
        self.assertFalse( ispowtwo(15) )
        self.assertTrue(  ispowtwo(16) )
        
        self.assertFalse( ispowtwo(31) )
        self.assertTrue(  ispowtwo(32) )
        self.assertFalse( ispowtwo(33) )
        self.assertFalse( ispowtwo(47) )
        self.assertTrue(  ispowtwo(1024) )
        self.assertFalse( ispowtwo(0xFFFF) )

    def test_iprevpowtwo(self):
        self.assertEqual( iprevpowtwo(0), 0)
        self.assertEqual( iprevpowtwo(1), 1)
        self.assertEqual( iprevpowtwo(2), 2)
        self.assertEqual( iprevpowtwo(3), 2)
        self.assertEqual( iprevpowtwo(4), 4)
        self.assertEqual( iprevpowtwo(5), 4)
        self.assertEqual( iprevpowtwo(6), 4)
        self.assertEqual( iprevpowtwo(7), 4)
        self.assertEqual( iprevpowtwo(8), 8)
        self.assertEqual( iprevpowtwo(9), 8)
        self.assertEqual( iprevpowtwo(10), 8)
        self.assertEqual( iprevpowtwo(11), 8)
        self.assertEqual( iprevpowtwo(12), 8)
        self.assertEqual( iprevpowtwo(13), 8)
        self.assertEqual( iprevpowtwo(14), 8)
        self.assertEqual( iprevpowtwo(15), 8)
        self.assertEqual( iprevpowtwo(16), 16)

        self.assertEqual( iprevpowtwo(31), 16)
        self.assertEqual( iprevpowtwo(32), 32)
        self.assertEqual( iprevpowtwo(33), 32)
        self.assertEqual( iprevpowtwo(47), 32)
        self.assertEqual( iprevpowtwo(1024), 1024)
        self.assertEqual( iprevpowtwo(0xFFFF), 0x8000)
        
    def test_vlbs(self):
        self.assertEqual( vlbs(0), 0)
        self.assertEqual( vlbs(1), 1)
        self.assertEqual( vlbs(2), 2)
        self.assertEqual( vlbs(3), 1)
        self.assertEqual( vlbs(4), 4)
        self.assertEqual( vlbs(5), 1)
        self.assertEqual( vlbs(6), 2)
        self.assertEqual( vlbs(7), 1)
        self.assertEqual( vlbs(8), 8)
        self.assertEqual( vlbs(9), 1)
        self.assertEqual( vlbs(10), 2)
        self.assertEqual( vlbs(11), 1)
        self.assertEqual( vlbs(12), 4)
        self.assertEqual( vlbs(13), 1)
        self.assertEqual( vlbs(14), 2)
        self.assertEqual( vlbs(15), 1)
        self.assertEqual( vlbs(16), 16)

        self.assertEqual( vlbs(31), 1)
        self.assertEqual( vlbs(32), 32)
        self.assertEqual( vlbs(33), 1)
        self.assertEqual( vlbs(47), 1)
        self.assertEqual( vlbs(1024), 1024)
        self.assertEqual( vlbs(0xFFFF), 1)
        
if __name__ == '__main__':
    unittest.main()

