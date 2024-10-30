"""
"""
import unittest
from philander.actuator import Direction

class TestActuator( unittest.TestCase ):
    
    def test_direction(self):
        p = Direction(1)
        n = Direction(-1)
        self.assertIsNotNone(p)
        self.assertIsNotNone(n)
        self.assertNotEqual( p, n)
        
        self.assertEqual( p, Direction.positive )
        self.assertEqual( Direction.positive, Direction.counterclockwise )
        self.assertEqual( Direction.positive, Direction.left )
        self.assertEqual( Direction.positive, Direction.forth )
        self.assertEqual( Direction.positive, Direction.up )

        self.assertEqual( n, Direction.negative )
        self.assertEqual( Direction.negative, Direction.clockwise )
        self.assertEqual( Direction.negative, Direction.right )
        self.assertEqual( Direction.negative, Direction.back )
        self.assertEqual( Direction.negative, Direction.down )

        
if __name__ == '__main__':
    unittest.main()

