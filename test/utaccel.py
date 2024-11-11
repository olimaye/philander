"""
"""
import unittest
from philander.accelerometer import Activity, AxesSign, Orientation, Tap, \
                                    SamplingMode, EventSource, Configuration, \
                                    StatusID, Data, EventContext
from philander.configurable import ConfigItem

class TestAccel( unittest.TestCase ):
    
    def test_activity(self):
        self.assertNotEqual( Activity.unknown, Activity.still )
        self.assertNotEqual( Activity.unknown, Activity.walking )
        self.assertNotEqual( Activity.unknown, Activity.running )
        self.assertNotEqual( Activity.still, Activity.walking )
        self.assertNotEqual( Activity.still, Activity.running )
        self.assertNotEqual( Activity.walking, Activity.running )
        self.assertNotEqual( Activity.walking, AxesSign.z )
        
    def test_axessign(self):
        self.assertEqual( AxesSign.x | AxesSign.y | AxesSign.z, AxesSign.all )
        self.assertNotEqual( AxesSign.x, Orientation.portraitDown )
    
    def test_orientation(self):
        val = Orientation.landscapeRight | Orientation.faceDown | Orientation.tiltFlat
        #self.assertEqual( val, 0x0F )
        self.assertFalse( (val & Orientation.invalidMask).value )

    def test_tap(self):
        self.assertNotEqual( Tap.none, Tap.single )
        self.assertNotEqual( Tap.none, Tap.double )
        self.assertNotEqual( Tap.none, Tap.triple )
        self.assertNotEqual( Tap.single, Tap.double )
        self.assertNotEqual( Tap.single, Tap.triple )
        self.assertNotEqual( Tap.double, Tap.triple )

    def test_eventsource(self):
        self.assertEqual( EventSource.lowG & EventSource.tap, EventSource.none )
        
    def test_configuration(self):
        c = Configuration()
        self.assertEqual( c.item, ConfigItem.implicit )
        self.assertEqual( c.value, 1 )
        self.assertIsNone( c.fifo )
        self.assertIsNone( c.rateMode )
        self.assertIsNone( c.eventCondition )
        c.rateMode = Configuration.CfgRateMode()
        c.eventCondition = Configuration.CfgInterrupt()
        self.assertEqual( c.rateMode.mValue, 2 )
        self.assertEqual( c.rateMode.control, SamplingMode.normal )
        self.assertEqual( c.eventCondition.delay, 10 )
        self.assertEqual( c.eventCondition.thrshld, 1500 )
        self.assertEqual( c.eventCondition.hysteresis, 200 )
        self.assertEqual( c.eventCondition.axes, AxesSign.z )
        self.assertEqual( c.eventCondition.event, EventSource.dataReady )

    def test_data(self):
        d = Data()
        self.assertIsNotNone(d)
        self.assertEqual( d.x, 0 )
        self.assertEqual( d.y, 0 )
        self.assertEqual( d.z, 0 )
        d = Data( z=3, x=4, y=5)
        self.assertEqual( d.x, 4 )
        self.assertEqual( d.y, 5 )
        self.assertEqual( d.z, 3 )
        
    def test_eventcontext(self):
        ec = EventContext()
        self.assertIsNotNone(ec)
        self.assertEqual( ec.source, EventSource.none )
        #self.assertIsNone(ec.data )
        self.assertEqual( ec.status, 0 )
        ec = EventContext( source=EventSource.lowSlope, data=Data(x=1, y=2, z=3), status=0x3a)
        self.assertIsNotNone(ec)
        self.assertEqual( ec.source, EventSource.lowSlope )
        self.assertIsNotNone( ec.data )
        self.assertEqual( ec.data.x, 1 )
        self.assertEqual( ec.data.y, 2 )
        self.assertEqual( ec.data.z, 3 )
        self.assertEqual( ec.status, 0x3a )
        
        

        
if __name__ == '__main__':
    unittest.main()

