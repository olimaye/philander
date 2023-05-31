"""Simulation of the BMA456 accelerometer device.

This module provides a pure software implementation of the device to
virtualize its serial communication behavior. This is to support
cross-platform development and debugging.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["SimDevBMA456"]

from simdev import SimDevMemory, Register, MemoryType
from bma456_reg import BMA456_Reg

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
            Register( BMA456_Reg.BMA456_REG_CHIP_ID,               BMA456_Reg.BMA456_CNT_CHIP_ID,                 MemoryType.ROM ),
            Register( BMA456_Reg.BMA456_REG_ERROR,                 BMA456_Reg.BMA456_CNT_ERROR_CODE_NONE,         MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_STATUS,                BMA456_Reg.BMA456_CNT_STATUS_CMD_RDY,          MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_AUX_X_LOW,             0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_AUX_X_HI,              0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_AUX_Y_LOW,             0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_AUX_Y_HI,              0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_AUX_Z_LOW,             0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_AUX_Z_HI,              0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_AUX_R_LOW,             0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_AUX_R_HI,              0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_ACC_X_LOW,             0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_ACC_X_HI,              0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_ACC_Y_LOW,             0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_ACC_Y_HI,              0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_ACC_Z_LOW,             0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_ACC_Z_HI,              0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_SENSOR_TIME0,          0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_SENSOR_TIME1,          0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_SENSOR_TIME2,          0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_EVENT,                 BMA456_Reg.BMA456_CNT_EVENT_POR,               MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_INT_STATUS0,           0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_INT_STATUS1,           0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_FSWBL_REG_STEP_COUNTER0,   0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_FSWBL_REG_STEP_COUNTER1,   0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_FSWBL_REG_STEP_COUNTER2,   0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_FSWBL_REG_STEP_COUNTER3,   0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_TEMPERATURE,           0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_FIFO_LENGTH_LOW,       0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_FIFO_LENGTH_HI,        0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_FIFO_DATA,             0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_FSWBL_REG_ACTIVITY_TYPE,   0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_FSHBL_REG_FEAT_EN1,        0,                                              MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_FSHBL_REG_FEAT_EN2,        0,                                              MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_INTERNAL_STATUS,       0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_ACC_CONF,              BMA456_Reg.BMA456_CNT_ACC_CONF_DEFAULT,        MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_ACC_RANGE,             BMA456_Reg.BMA456_CNT_ACC_RANGE_DEFAULT,       MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_AUX_CONF,              0x46,                                           MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_FIFO_DOWNS,            BMA456_Reg.BMA456_CNT_FIFO_DOWNS_FILTER,       MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_FIFO_WM_LOW,           0,                                              MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_FIFO_WM_HI,            0x02,                                           MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_FIFO_CFG0,             0x02,                                           MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_FIFO_CFG1,             0x10,                                           MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_AUX_DEV_ID,            0x20,                                           MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_AUX_IF_CONF,           0x83,                                           MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_AUX_RD_ADDR,           0x42,                                           MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_AUX_WR_ADDR,           0x4c,                                           MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_AUX_WR_DATA,           0x02,                                           MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_INT1_IO_CTRL,          BMA456_Reg.BMA456_CNT_INT1_IO_CTRL_DEFAULT,    MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_INT2_IO_CTRL,          BMA456_Reg.BMA456_CNT_INT2_IO_CTRL_DEFAULT,    MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_INT_LATCH,             BMA456_Reg.BMA456_CNT_INT_LATCH_NONE,          MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_INT1_MAP,              BMA456_Reg.BMA456_CNT_INTX_MAP_DEFAULT,        MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_INT2_MAP,              BMA456_Reg.BMA456_CNT_INTX_MAP_DEFAULT,        MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_INT_MAP_DATA,          BMA456_Reg.BMA456_CNT_INT_MAP_DATA_DEFAULT,    MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_INIT_CTRL,             0x90,                                           MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_DMA_LOW,               0,                                              MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_DMA_HI,                0,                                              MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_FEATURES,              0,                                              MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_INTERNAL_ERR,          0,                                              MemoryType.VOLATILE ),
            Register( BMA456_Reg.BMA456_REG_NVM_CFG,               BMA456_Reg.BMA456_CNT_NVM_CFG_PPROG_DISABLE,   MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_IF_CFG,                0,                                              MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_SELF_TST,              0,                                              MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_NVM_BE_CFG,            0,                                              MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_OFFSET_X,              0,                                              MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_OFFSET_Y,              0,                                              MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_OFFSET_Z,              0,                                              MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_PWR_CONF,              0x03,                                           MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_PWR_CTRL,              0,                                              MemoryType.RAM ),
            Register( BMA456_Reg.BMA456_REG_CMD,                   0,                                              MemoryType.RAM ),
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
