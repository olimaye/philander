from sbsim import sbsimMemory, Register, RegType
from _BMA456_Reg import _BMA456_Reg

class sbsimBMA456( sbsimMemory ):
    
        
    def __init__( self ):
        regset = [
            Register( _BMA456_Reg.BMA456_REG_CHIP_ID, _BMA456_Reg.BMA456_CNT_CHIP_ID, RegType.rtROM ),
            Register( _BMA456_Reg.BMA456_REG_ERROR, _BMA456_Reg.BMA456_CNT_ERROR_CODE_NONE, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_STATUS, _BMA456_Reg.BMA456_CNT_STATUS_CMD_RDY, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_AUX_X_LOW, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_AUX_X_HI, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_AUX_Y_LOW, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_AUX_Y_HI, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_AUX_Z_LOW, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_AUX_Z_HI, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_AUX_R_LOW, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_AUX_R_HI, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_ACC_X_LOW, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_ACC_X_HI, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_ACC_Y_LOW, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_ACC_Y_HI, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_ACC_Z_LOW, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_ACC_Z_HI, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_SENSOR_TIME0, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_SENSOR_TIME1, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_SENSOR_TIME2, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_EVENT, _BMA456_Reg.BMA456_CNT_EVENT_POR, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_INT_STATUS0, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_INT_STATUS1, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_FSWBL_REG_STEP_COUNTER0, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_FSWBL_REG_STEP_COUNTER1, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_FSWBL_REG_STEP_COUNTER2, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_FSWBL_REG_STEP_COUNTER3, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_TEMPERATURE, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_FIFO_LENGTH_LOW, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_FIFO_LENGTH_HI, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_FIFO_DATA, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_FSWBL_REG_ACTIVITY_TYPE, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_FSHBL_REG_FEAT_EN1, 0, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_FSHBL_REG_FEAT_EN2, 0, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_INTERNAL_STATUS, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_ACC_CONF, _BMA456_Reg.BMA456_CNT_ACC_CONF_DEFAULT, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_ACC_RANGE, _BMA456_Reg.BMA456_CNT_ACC_RANGE_DEFAULT, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_AUX_CONF, 0x46, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_FIFO_DOWNS, _BMA456_Reg.BMA456_CNT_FIFO_DOWNS_FILTER, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_FIFO_WM_LOW, 0, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_FIFO_WM_HI, 0x02, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_FIFO_CFG0, 0x02, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_FIFO_CFG1, 0x10, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_AUX_DEV_ID, 0x20, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_AUX_IF_CONF, 0x83, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_AUX_RD_ADDR, 0x42, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_AUX_WR_ADDR, 0x4c, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_AUX_WR_DATA, 0x02, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_INT1_IO_CTRL, _BMA456_Reg.BMA456_CNT_INT1_IO_CTRL_DEFAULT, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_INT2_IO_CTRL, _BMA456_Reg.BMA456_CNT_INT2_IO_CTRL_DEFAULT, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_INT_LATCH, _BMA456_Reg.BMA456_CNT_INT_LATCH_NONE, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_INT1_MAP, _BMA456_Reg.BMA456_CNT_INTX_MAP_DEFAULT, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_INT2_MAP, _BMA456_Reg.BMA456_CNT_INTX_MAP_DEFAULT, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_INT_MAP_DATA, _BMA456_Reg.BMA456_CNT_INT_MAP_DATA_DEFAULT, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_INIT_CTRL, 0x90, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_DMA_LOW, 0, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_DMA_HI, 0, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_FEATURES, 0, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_INTERNAL_ERR, 0, RegType.rtVOLATILE ),
            Register( _BMA456_Reg.BMA456_REG_NVM_CFG, _BMA456_Reg.BMA456_CNT_NVM_CFG_PPROG_DISABLE, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_IF_CFG, 0, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_SELF_TST, 0, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_NVM_BE_CFG, 0, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_OFFSET_X, 0, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_OFFSET_Y, 0, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_OFFSET_Z, 0, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_PWR_CONF, 0x03, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_PWR_CTRL, 0, RegType.rtRAM ),
            Register( _BMA456_Reg.BMA456_REG_CMD, 0, RegType.rtRAM ),
        ]
        self._regStatusReadCnt = 0
        sbsimMemory.__init__(self, regset)


    def updateVolatileOnRead(self, reg):
        if (reg.address == _BMA456_Reg.BMA456_REG_STATUS):
            mask = (_BMA456_Reg.BMA456_CNT_STATUS_DRDY_ACC | _BMA456_Reg.BMA456_CNT_STATUS_DRDY_AUX)
            if ((reg.content & mask) != mask):
                self._regStatusReadCnt = self._regStatusReadCnt + 1
                if (self._regStatusReadCnt >= 10):
                    self._regStatusReadCnt = 0
                    reg.content |= mask
                
        elif (reg.address in [_BMA456_Reg.BMA456_REG_AUX_X_LOW, _BMA456_Reg.BMA456_REG_AUX_X_HI,
                            _BMA456_Reg.BMA456_REG_AUX_Y_LOW, _BMA456_Reg.BMA456_REG_AUX_Y_HI,
                            _BMA456_Reg.BMA456_REG_AUX_Z_LOW, _BMA456_Reg.BMA456_REG_AUX_Z_HI, 
                            _BMA456_Reg.BMA456_REG_AUX_R_LOW, _BMA456_Reg.BMA456_REG_AUX_R_HI,
                            _BMA456_Reg.BMA456_REG_ACC_X_LOW, _BMA456_Reg.BMA456_REG_ACC_X_HI,
                            _BMA456_Reg.BMA456_REG_ACC_Y_LOW, _BMA456_Reg.BMA456_REG_ACC_Y_HI,
                            _BMA456_Reg.BMA456_REG_ACC_Z_LOW, _BMA456_Reg.BMA456_REG_ACC_Z_HI, ]):
            reg.content = reg.content + 1
            statreg = self._findReg( _BMA456_Reg.BMA456_REG_STATUS)
            if (reg.address in [_BMA456_Reg.BMA456_REG_ACC_X_LOW, _BMA456_Reg.BMA456_REG_ACC_X_HI,
                                _BMA456_Reg.BMA456_REG_ACC_Y_LOW, _BMA456_Reg.BMA456_REG_ACC_Y_HI,
                                _BMA456_Reg.BMA456_REG_ACC_Z_LOW, _BMA456_Reg.BMA456_REG_ACC_Z_HI, ]):
                statreg.content &= ~_BMA456_Reg.BMA456_CNT_STATUS_DRDY_ACC
            else:
                statreg.content &= ~_BMA456_Reg.BMA456_CNT_STATUS_DRDY_AUX
        elif (reg.address == _BMA456_Reg.BMA456_REG_SENSOR_TIME0):
            reg.content = reg.content + 1
            if (reg.content == 0x100):
                reg.content = 0
                reg = self._findReg( _BMA456_Reg.BMA456_REG_SENSOR_TIME1 )
                reg.content = reg.content + 1
                if (reg.content == 0x100):
                    reg.content = 0
                    reg = self._findReg( _BMA456_Reg.BMA456_REG_SENSOR_TIME2 )
                    reg.content = reg.content + 1
                    if (reg.content == 0x100):
                        reg.content = 0
        return None

    def updateOnWrite(self, reg, newData):
        if (reg.address == _BMA456_Reg.BMA456_REG_INIT_CTRL):
            if (newData == _BMA456_Reg.BMA456_CNT_INIT_CTRL_START_INIT):
                # Set internal status
                statreg = self._findReg( _BMA456_Reg.BMA456_REG_INTERNAL_STATUS)
                statreg.content &= ~_BMA456_Reg.BMA456_CNT_INTERNAL_STATUS_MSG 
                if (reg.content == _BMA456_Reg.BMA456_CNT_INIT_CTRL_LOAD_CONFIG_FILE):
                    statreg.content |= _BMA456_Reg.BMA456_CNT_INTERNAL_STATUS_MSG_INIT_OK 
                else:
                    statreg.content |= _BMA456_Reg.BMA456_CNT_INTERNAL_STATUS_MSG_INIT_ERR 
        # Actually overwrite the register content with the new data
        super().updateOnWrite(reg, newData)
        return None
