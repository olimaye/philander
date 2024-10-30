"""
"""
import unittest

from philander.dictionary import Dictionary
from philander.systypes import ErrorCode

class TestDictionary( unittest.TestCase ):

    def test_getValue(self):
        m = {
            4: 1000,
            2: 20,
            3: 100,
            5: 1013,
            1: 10,
            }
        D = Dictionary( m )
        key = 1
        val, err = D.getValue(key)
        self.assertTrue( err.isOk() )
        self.assertEqual( val, m[key] )
        key = 2
        val, err = D.getValue(key)
        self.assertTrue( err.isOk() )
        self.assertEqual( val, m[key] )
        key = 3
        val, err = D.getValue(key)
        self.assertTrue( err.isOk() )
        self.assertEqual( val, m[key] )
        key = 4
        val, err = D.getValue(key)
        self.assertTrue( err.isOk() )
        self.assertEqual( val, m[key] )
        key = 5
        val, err = D.getValue(key)
        self.assertTrue( err.isOk() )
        self.assertEqual( val, m[key] )
        key = 8
        val, err = D.getValue(key)
        self.assertFalse( err.isOk() )
        key = -2.4
        val, err = D.getValue(key)
        self.assertFalse( err.isOk() )
        key = "Key"
        val, err = D.getValue(key)
        self.assertFalse( err.isOk() )

    def test_findKey(self):
        m = {
            4: 1000,
            2: 20,
            3: 100,
            5: 1013,
            1: 10,
            }
        D = Dictionary( m )
        # Normal mode
        tstvec = { 8: 1, 25: 2, 611: 4, 1013: 5, 1025: 5}
        for v, k in tstvec.items():
            key, err = D.findKey(v)
            self.assertTrue( err.isOk() )
            self.assertEqual( key, k )
        # Clip mode
        D.mode = Dictionary.DICT_STDMODE_CLIP
        tstvec = { 8: -1, 25: 2, 611: 4, 1013: 5, 1025: -1}
        for v, k in tstvec.items():
            key, err = D.findKey(v)
            if k<0:
                self.assertFalse( err.isOk() )
            else:
                self.assertTrue( err.isOk() )
                self.assertEqual( key, k )
        # Down mode
        D.mode = Dictionary.DICT_STDMODE_DOWN
        tstvec = { 8: 1, 25: 2, 611: 3, 1013: 5, 1025: 5}
        for v, k in tstvec.items():
            key, err = D.findKey(v)
            self.assertTrue( err.isOk() )
            self.assertEqual( key, k )
        # Up mode
        D.mode = Dictionary.DICT_STDMODE_UP
        tstvec = { 8: 1, 25: 3, 611: 4, 1013: 5, 1025: 5}
        for v, k in tstvec.items():
            key, err = D.findKey(v)
            self.assertTrue( err.isOk() )
            self.assertEqual( key, k )
        # Strict mode
        D.mode = Dictionary.DICT_STDMODE_STRICT
        tstvec = { 8: -1, 25: -1, 611: -1, 1013: 5, 1025: -1}
        for v, k in tstvec.items():
            key, err = D.findKey(v)
            if k<0:
                self.assertFalse( err.isOk() )
            else:
                self.assertTrue( err.isOk() )
                self.assertEqual( key, k )
        
        
if __name__ == '__main__':
    unittest.main()

