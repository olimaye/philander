"""
"""
import unittest
from pymitter import EventEmitter

# We use a global variable to make calls of the event handler
# visible to the tester.
callReflect = 0

# Callback handler
def handlerFunc(arg):
    global callReflect
    callReflect = arg

class TestPymitter( unittest.TestCase ):
    
    def test_invocation(self):
        global callReflect
        # Create instance
        ee = EventEmitter()
        self.assertIsNotNone( ee )
        # Register handler
        ee.on("myevent", handlerFunc)
        # Reset indicator
        callReflect = 0
        
        # Emit events
        ee.emit("myevent", "foo")       # -> handler called with "foo"
        self.assertEqual( callReflect, "foo" )
        ee.emit("myotherevent", "bar")  # -> handler not called
        self.assertEqual( callReflect, "foo" )
        ee.emit("myevent", 3)           # -> handler called with value 3
        self.assertEqual( callReflect, 3 )
        
        ee.off( "myevent", handlerFunc )
        ee.emit("myevent", 17)           # -> handler not called
        self.assertEqual( callReflect, 3 )

        # Test TTL
        ee.on("myevent", handlerFunc, ttl=3)
        ee.emit("myevent", 1)
        self.assertEqual( callReflect, 1 )
        ee.emit("myevent", "something")
        self.assertEqual( callReflect, "something" )
        ee.emit("myevent", 4.2)
        self.assertEqual( callReflect, 4.2 )
        ee.emit("myevent", 37)          # handler not called any more.
        self.assertEqual( callReflect, 4.2 )
        
        # Test wildcards
        ee = EventEmitter(wildcard=True)
        self.assertIsNotNone( ee )
        ee.on("myevent.*", handlerFunc)
        ee.emit("myevent.", 2)
        self.assertEqual( callReflect, 2 )
        ee.emit("myevent.sub1", 5)
        self.assertEqual( callReflect, 5 )
        ee.emit("myevent.sub2", 6)
        self.assertEqual( callReflect, 6 )
        ee.emit("myotherevent.sub1", 5) # handler not called
        self.assertEqual( callReflect, 6 )
        
        
if __name__ == '__main__':
    unittest.main()

