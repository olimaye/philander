"""Simulation of the BMA456 accelerometer device.

This module provides a pure software implementation of the device to
virtualize its serial communication behavior. This is to support
cross-platform development and debugging.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["SimDevBMA456"]

from .bma456_reg import BMA456_Reg
from .simdev import SimDevMemory, Register, MemoryType
from .systypes import ErrorCode


class SimDevBMA456( SimDevMemory ):
    """A software simulation of the BMA456. The current implementation is
    incomplete and imperfect to some extent. The status is as follows.
    
    Working
    ========
    * simulation of its bare existence by responding properly in serial communication
    * all registers are present, accessible and constructed with correct reset values.
    * register ``CHIP_ID``
    * ``STATUS:DRDY_ACC/AUX`` cleared at each read-access to ``ACC_X/Y/Z`` or ``AUX_X/Y/Z/R`` 
    
    Limitations
    ===========
    * ``ACC_X/Y/Z`` get just incremented after each read access.
    * ``STATUS:DRDY_ACC/AUX`` get set after polling (reading) ``STATUS`` for 10 times.
    * ``SENSOR_TIME[0:1:2]`` incremented after each read-access
    * initialization sequence is satisfied by writing ``LOAD_CFG_FILE``\
    followed by ``START_INIT`` to the ``INIT_CTRL`` register. This will\
    set ``INTERNAL_STATUS:MSG`` to ``INIT_OK``. Otherwise, these bits\
    are set to ``INIT_ERR``. 
    
    Missing
    ========
    * Simulation of acceleration flow, e.g. as read from an input file
    * Feature simulation (step counter etc.)
    * Simulation of the chip status and behavior, such as ``ERROR`` and ``STATUS``
    * power modes
    * interrupts
    * NVM     
    """
        
    def __init__( self ):
        regset = [
            Register( address=BMA456_Reg.BMA456_REG_CHIP_ID,               content=BMA456_Reg.BMA456_CNT_CHIP_ID,                  type=MemoryType.ROM ),
            Register( address=BMA456_Reg.BMA456_REG_ERROR,                 content=BMA456_Reg.BMA456_CNT_ERROR_CODE_NONE,          type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_STATUS,                content=BMA456_Reg.BMA456_CNT_STATUS_CMD_RDY,           type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_AUX_X_LOW,             content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_AUX_X_HI,              content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_AUX_Y_LOW,             content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_AUX_Y_HI,              content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_AUX_Z_LOW,             content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_AUX_Z_HI,              content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_AUX_R_LOW,             content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_AUX_R_HI,              content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_ACC_X_LOW,             content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_ACC_X_HI,              content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_ACC_Y_LOW,             content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_ACC_Y_HI,              content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_ACC_Z_LOW,             content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_ACC_Z_HI,              content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_SENSOR_TIME0,          content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_SENSOR_TIME1,          content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_SENSOR_TIME2,          content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_EVENT,                 content=BMA456_Reg.BMA456_CNT_EVENT_POR,                type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_INT_STATUS0,           content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_INT_STATUS1,           content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_FSWBL_REG_STEP_COUNTER0,   content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_FSWBL_REG_STEP_COUNTER1,   content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_FSWBL_REG_STEP_COUNTER2,   content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_FSWBL_REG_STEP_COUNTER3,   content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_TEMPERATURE,           content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_FIFO_LENGTH_LOW,       content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_FIFO_LENGTH_HI,        content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_FIFO_DATA,             content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_FSWBL_REG_ACTIVITY_TYPE,   content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_FSHBL_REG_FEAT_EN1,        content=0,                                              type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_FSHBL_REG_FEAT_EN2,        content=0,                                              type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_INTERNAL_STATUS,       content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_ACC_CONF,              content=BMA456_Reg.BMA456_CNT_ACC_CONF_DEFAULT,         type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_ACC_RANGE,             content=BMA456_Reg.BMA456_CNT_ACC_RANGE_DEFAULT,        type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_AUX_CONF,              content=0x46,                                           type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_FIFO_DOWNS,            content=BMA456_Reg.BMA456_CNT_FIFO_DOWNS_FILTER,        type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_FIFO_WM_LOW,           content=0,                                              type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_FIFO_WM_HI,            content=0x02,                                           type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_FIFO_CFG0,             content=0x02,                                           type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_FIFO_CFG1,             content=0x10,                                           type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_AUX_DEV_ID,            content=0x20,                                           type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_AUX_IF_CONF,           content=0x83,                                           type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_AUX_RD_ADDR,           content=0x42,                                           type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_AUX_WR_ADDR,           content=0x4c,                                           type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_AUX_WR_DATA,           content=0x02,                                           type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_INT1_IO_CTRL,          content=BMA456_Reg.BMA456_CNT_INT1_IO_CTRL_DEFAULT,     type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_INT2_IO_CTRL,          content=BMA456_Reg.BMA456_CNT_INT2_IO_CTRL_DEFAULT,     type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_INT_LATCH,             content=BMA456_Reg.BMA456_CNT_INT_LATCH_NONE,           type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_INT1_MAP,              content=BMA456_Reg.BMA456_CNT_INTX_MAP_DEFAULT,         type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_INT2_MAP,              content=BMA456_Reg.BMA456_CNT_INTX_MAP_DEFAULT,         type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_INT_MAP_DATA,          content=BMA456_Reg.BMA456_CNT_INT_MAP_DATA_DEFAULT,     type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_INIT_CTRL,             content=0x90,                                           type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_DMA_LOW,               content=0,                                              type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_DMA_HI,                content=0,                                              type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_FEATURES,              content=0,                                              type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_INTERNAL_ERR,          content=0,                                              type=MemoryType.VOLATILE ),
            Register( address=BMA456_Reg.BMA456_REG_NVM_CFG,               content=BMA456_Reg.BMA456_CNT_NVM_CFG_PPROG_DISABLE,    type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_IF_CFG,                content=0,                                              type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_SELF_TST,              content=0,                                              type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_NVM_BE_CFG,            content=0,                                              type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_OFFSET_X,              content=0,                                              type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_OFFSET_Y,              content=0,                                              type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_OFFSET_Z,              content=0,                                              type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_PWR_CONF,              content=0x03,                                           type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_PWR_CTRL,              content=0,                                              type=MemoryType.RAM ),
            Register( address=BMA456_Reg.BMA456_REG_CMD,                   content=0,                                              type=MemoryType.RAM ),
        ]
        self._regStatusReadCnt = 0
        SimDevMemory.__init__(self, regset)


    def _onPostRead(self, reg):
        # Status register
        if (reg.address == BMA456_Reg.BMA456_REG_STATUS):
            mask = (BMA456_Reg.BMA456_CNT_STATUS_DRDY_ACC | BMA456_Reg.BMA456_CNT_STATUS_DRDY_AUX)
            if ((reg.content & mask) != mask):
                self._regStatusReadCnt = self._regStatusReadCnt + 1
                if (self._regStatusReadCnt >= 10):
                    self._regStatusReadCnt = 0
                    reg.content |= mask
        # Acceleration data
        elif (reg.address in [BMA456_Reg.BMA456_REG_AUX_X_LOW, BMA456_Reg.BMA456_REG_AUX_X_HI,
                            BMA456_Reg.BMA456_REG_AUX_Y_LOW, BMA456_Reg.BMA456_REG_AUX_Y_HI,
                            BMA456_Reg.BMA456_REG_AUX_Z_LOW, BMA456_Reg.BMA456_REG_AUX_Z_HI, 
                            BMA456_Reg.BMA456_REG_AUX_R_LOW, BMA456_Reg.BMA456_REG_AUX_R_HI,
                            BMA456_Reg.BMA456_REG_ACC_X_LOW, BMA456_Reg.BMA456_REG_ACC_X_HI,
                            BMA456_Reg.BMA456_REG_ACC_Y_LOW, BMA456_Reg.BMA456_REG_ACC_Y_HI,
                            BMA456_Reg.BMA456_REG_ACC_Z_LOW, BMA456_Reg.BMA456_REG_ACC_Z_HI, ]):
            reg.content = reg.content + 1
            statreg = self._findReg( BMA456_Reg.BMA456_REG_STATUS)
            if (reg.address in [BMA456_Reg.BMA456_REG_ACC_X_LOW, BMA456_Reg.BMA456_REG_ACC_X_HI,
                                BMA456_Reg.BMA456_REG_ACC_Y_LOW, BMA456_Reg.BMA456_REG_ACC_Y_HI,
                                BMA456_Reg.BMA456_REG_ACC_Z_LOW, BMA456_Reg.BMA456_REG_ACC_Z_HI, ]):
                statreg.content &= ~BMA456_Reg.BMA456_CNT_STATUS_DRDY_ACC
            else:
                statreg.content &= ~BMA456_Reg.BMA456_CNT_STATUS_DRDY_AUX
        # Sensor time
        elif (reg.address == BMA456_Reg.BMA456_REG_SENSOR_TIME0):
            reg.content = reg.content + 1
            if (reg.content == 0x100):
                reg.content = 0
                reg = self._findReg( BMA456_Reg.BMA456_REG_SENSOR_TIME1 )
                reg.content = reg.content + 1
                if (reg.content == 0x100):
                    reg.content = 0
                    reg = self._findReg( BMA456_Reg.BMA456_REG_SENSOR_TIME2 )
                    reg.content = reg.content + 1
                    if (reg.content == 0x100):
                        reg.content = 0
        return None

    def _onPreWrite(self, reg, newData):
        if (reg.address == BMA456_Reg.BMA456_REG_INIT_CTRL):
            if (newData == BMA456_Reg.BMA456_CNT_INIT_CTRL_START_INIT):
                # Set internal status
                statreg = self._findReg( BMA456_Reg.BMA456_REG_INTERNAL_STATUS)
                statreg.content &= ~BMA456_Reg.BMA456_CNT_INTERNAL_STATUS_MSG 
                if (reg.content == BMA456_Reg.BMA456_CNT_INIT_CTRL_LOAD_CONFIG_FILE):
                    statreg.content |= BMA456_Reg.BMA456_CNT_INTERNAL_STATUS_MSG_INIT_OK 
                else:
                    statreg.content |= BMA456_Reg.BMA456_CNT_INTERNAL_STATUS_MSG_INIT_ERR 
        return newData

    def readBufferRegister( self, aReg, length ):
        """Read a block of data starting from the given register.
        
        Do not auto-increment destination address when reading from
        ``BMA456_REG_FEATURES``.
                
        :param int aReg: The address of the first register to be read.
        :param int length: The number of bytes to read.
        :return: A buffer of the indicated length holding the response\
        and an error code indicating success or the reason of failure.
        :rtype: list(int), ErrorCode
        """
        if (aReg == BMA456_Reg.BMA456_REG_FEATURES ):
            data = [0] * length
            err = ErrorCode.errOk
            for idx in range(length):
                data[idx], err = self.readByteRegister(aReg)
        else:
            data, err = super().readBufferRegister( aReg, length )
        return data, err

    def writeBufferRegister( self, aReg, data ):
        """Write a block of byte data into registers.

        Do not auto-increment destination address when writing to
        ``BMA456_REG_FEATURES``.
        
        :param int aReg: The address of the first register to receive\
        the block of data.
        :param list data: List of bytes to be written. The length of the\
        list determines the number of bytes to write. So, all values in\
        the list will be transferred to the device.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        err = ErrorCode.errOk
        if (aReg == BMA456_Reg.BMA456_REG_FEATURES ):
            for idx in range( len(data) ):
                err = self.writeByteRegister(aReg, data[idx])
        else:
            err = super().writeBufferRegister( aReg, data )
        return err
