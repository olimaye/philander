"""
"""
import unittest
from serialbus import SerialBus, SerialBusDevice
from systypes import ErrorCode

class TestSerialBus( unittest.TestCase ):
    
    def test_openAttach(self):
        bus = SerialBus()
        self.assertIsNotNone( bus )
        
        params = {\
            "SerialBus.designator":   1,
            }
        SerialBus.Params_init( params )
        self.assertEqual( params["SerialBus.designator"], 1 )
        
        self.assertEqual( bus.isOpen(), ErrorCode.errUnavailable )
        err = bus.open(params)
        self.assertEqual( err, ErrorCode.errOk )
        self.assertEqual( bus.isOpen(), ErrorCode.errOk )

        dev = SerialBusDevice()
        self.assertIsNotNone( dev )
        
        params["SerialBusDevice.bus"] = bus
        SerialBusDevice.Params_init( params )
        self.assertEqual( params["SerialBusDevice.bus"], bus )
        
        self.assertEqual( dev.isAttached(), ErrorCode.errUnavailable )
        self.assertEqual( bus.isAttached(dev), ErrorCode.errUnavailable )
        err = dev.open(params)
        self.assertEqual( err, ErrorCode.errOk )
        self.assertEqual( dev.isAttached(), ErrorCode.errOk )
        self.assertEqual( bus.isAttached(dev), ErrorCode.errOk )
        
        err = bus.detach(dev)
        self.assertEqual( err, ErrorCode.errOk )
        self.assertEqual( dev.isAttached(), ErrorCode.errUnavailable )
        self.assertEqual( bus.isAttached(dev), ErrorCode.errUnavailable )
        self.assertEqual( bus.isOpen(), ErrorCode.errUnavailable )
        
        err = bus.open(params)
        self.assertEqual( err, ErrorCode.errOk )
        self.assertEqual( bus.isOpen(), ErrorCode.errOk )

        err = bus.attach(dev)
        self.assertEqual( err, ErrorCode.errOk )
        self.assertEqual( dev.isAttached(), ErrorCode.errOk )
        self.assertEqual( bus.isAttached(dev), ErrorCode.errOk )

        err = dev.close()
        self.assertEqual( err, ErrorCode.errOk )
        self.assertEqual( dev.isAttached(), ErrorCode.errUnavailable )
        self.assertEqual( bus.isAttached(dev), ErrorCode.errUnavailable )
        self.assertEqual( bus.isOpen(), ErrorCode.errUnavailable )
        err = bus.close()
        self.assertEqual( err, ErrorCode.errOk )

    def test_readWrite(self):
        dev = SerialBusDevice()
        self.assertIsNotNone( dev )
        params = {\
            "SerialBus.designator":   1,
            }
        SerialBusDevice.Params_init( params )
        self.assertEqual( params["SerialBus.designator"], 1 )
        err = dev.open(params)
        self.assertEqual( err, ErrorCode.errOk )
        self.assertTrue( "SerialBusDevice.bus" in params )
        self.assertIsNotNone( params["SerialBusDevice.bus"] )

        regNum = 47
        data, err = dev.readByteRegister( regNum )
        self.assertEqual( err, ErrorCode.errOk )
        data += 1
        err = dev.writeByteRegister( regNum, data )
        self.assertEqual( err, ErrorCode.errOk )
        newData, err = dev.readByteRegister( regNum )
        self.assertEqual( err, ErrorCode.errOk )
        #self.assertEqual( newData, data )

        err = dev.close()
        self.assertEqual( err, ErrorCode.errOk )


if __name__ == '__main__':
    unittest.main()

