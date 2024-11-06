"""
"""
import unittest

from philander.thermometer import Data
from philander.systypes import ErrorCode

class TestThermometer( unittest.TestCase ):
    
    def test_data(self):
        val = 17
        data = Data(temperature=val)
        self.assertIsNotNone( data )
        self.assertTrue( hasattr( data, "temperature") )
        self.assertEqual( data.temperature, val )


if __name__ == '__main__':
    unittest.main()

