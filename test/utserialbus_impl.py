"""
"""
import time
import unittest
from philander.serialbus import SerialBusDevice, SerialBusType, SPIMode
from philander.systypes import ErrorCode
from philander.sysfactory import SysFactory, SysProvider
from philander.simBMA456 import SimDevBMA456

class TestSerialBus( unittest.TestCase ):

    #@unittest.skip("step-wise testing")
    def test_i2c(self):
        # Enforce specific implementation of serial bus
        # and open the device
        bus = SysFactory.getSerialBus( SysProvider.PERIPHERY )
        dev = SerialBusDevice()
        #bus = SysFactory.getSerialBus( SysProvider.SIM )
        #dev.sim = SimDevBMA456()
        self.assertIsNotNone( dev )

        # Assume BMA456 @ I2C.1 to be the device under test.
        params = {\
            "SerialBus.designator":   "/dev/i2c-1",     #1,
            "SerialBusDevice.address":    0x18,
            "SerialBusDevice.bus":    bus,
            }
        SerialBusDevice.Params_init( params )
        self.assertEqual( params["SerialBus.designator"], "/dev/i2c-1" )
        self.assertEqual( params["SerialBusDevice.bus"], bus )
        err = dev.open(params)
        self.assertEqual( err, ErrorCode.errOk )

        # Read chip ID, error and status
        data, err = dev.readByteRegister( 0 )   # ChipID
        self.assertEqual( err, ErrorCode.errOk )
        self.assertEqual( data, 0x16 )
        data, err = dev.readByteRegister( 2 )   # Error
        self.assertEqual( err, ErrorCode.errOk )
        self.assertEqual( data, 0 )
        data, err = dev.readByteRegister( 3 )   # Status
        self.assertEqual( err, ErrorCode.errOk )
        self.assertEqual( data & 0x7F, 0x10 )
        data, err = dev.readWordRegister( 0x12 )   # ACC_X
        self.assertEqual( err, ErrorCode.errOk )
        
        # Test write operation
        regNum = 0x46   # FIFO_WTM_0
        for data in [0, 0x07, 0x55, 0xAA, 0xB3, 0xFF]:
            err = dev.writeByteRegister( regNum, data )
            self.assertEqual( err, ErrorCode.errOk )
            newData, err = dev.readByteRegister( regNum )
            self.assertEqual( err, ErrorCode.errOk )
            self.assertEqual( newData, data )

            data = (data + 1) & 0xFF
            err = dev.writeBuffer( [regNum, data] )
            self.assertEqual( err, ErrorCode.errOk )
            newData, err = dev.readBufferRegister( regNum, 1 )
            self.assertEqual( err, ErrorCode.errOk )
            self.assertEqual( newData[0], data )

        # Finally, close the device
        err = dev.close()
        self.assertEqual( err, ErrorCode.errOk )


    #@unittest.skip("step-wise testing")
    def test_spi(self):
        # Enforce specific implementation of serial bus
        # and open the device
        bus = SysFactory.getSerialBus( SysProvider.PERIPHERY )
        dev = SerialBusDevice()
        self.assertIsNotNone( dev )

        # Assume BME280 @ SPI.1 to be the device under test.
        params = {\
            "SerialBus.type":         SerialBusType.SPI,
            "SerialBus.designator":   "/dev/spidev0.1",
            #"SerialBus.SPI.mode":     SPIMode.CPOL1_CPHA1,
            "SerialBusDevice.bus":    bus,
            }
        SerialBusDevice.Params_init( params )
        self.assertEqual( params["SerialBus.designator"], "/dev/spidev0.1" )
        self.assertEqual( params["SerialBus.SPI.mode"], SPIMode.CPOL1_CPHA1 )
        self.assertEqual( params["SerialBusDevice.bus"], bus )
        err = dev.open(params)
        self.assertEqual( err, ErrorCode.errOk )

        # Initialize = set to active mode; read back and check
        regNum = 0xF4   # ctrl_meas
        initData = 0x03
        err = dev.writeByteRegister( regNum & 0x7F, initData )
        self.assertEqual( err, ErrorCode.errOk )
        data, err = dev.readByteRegister( regNum | 0x80 )
        self.assertEqual( err, ErrorCode.errOk )
        self.assertEqual( data, initData)

        # Read chip ID, error and status
        data, err = dev.readByteRegister( 0xD0 )   # ChipID
        self.assertEqual( err, ErrorCode.errOk )
        self.assertEqual( data, 0x60)
        data, err = dev.readByteRegister( 0xE0 )   # Reset
        self.assertEqual( err, ErrorCode.errOk )
        self.assertEqual( data, 0 )
        data, err = dev.readWordRegister( 0xFA )   # temp
        self.assertEqual( err, ErrorCode.errOk )

        # Test write operation
        regNum = 0xF4   # ctrl_meas
        for data in [0x03, 0x07, 0x57, 0xAB, 0xB3, 0xFF]:
            err = dev.writeByteRegister( regNum & 0x7F, data )
            self.assertEqual( err, ErrorCode.errOk )
            time.sleep(0.1)
            newData, err = dev.readByteRegister( regNum | 0x80 )
            self.assertEqual( err, ErrorCode.errOk )
            self.assertEqual( newData, data )

            data = (data + 1) & 0xFF
            newData, err = dev.readWriteBuffer( outBuffer=[regNum & 0x7F, data, regNum | 0x80], inLength=1 )
            self.assertEqual( err, ErrorCode.errOk )
            self.assertEqual( newData[0], data )
            

        # Finally, close the device
        err = dev.close()
        self.assertEqual( err, ErrorCode.errOk )

if __name__ == '__main__':
    unittest.main()

