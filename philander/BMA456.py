from _BMA456_Reg import _BMA456_Reg
from _BMA456_Feature import _BMA456_Feature
from Accelerometer import Accelerometer, Activity, AxesSign, Configuration, EventSource, Orientation, SamplingMode, StatusID, Tap
from dictionary import dictionary
import imath
from Interruptable import Event, EventContextControl
from Sensor import ConfigItem, Sensor
from Serial_Bus import Serial_Bus_Device
from systypes import ErrorCode, RunLevel
import time
from sbsimBMA456 import SimBusBMA456
from gpio import GPIO

class BMA456( _BMA456_Reg, _BMA456_Feature, Serial_Bus_Device, Accelerometer ):
    #
    # Protected / private attributes
    #
    
    #
    # Default address is 0x18 assuming that SDO is set/tied to GND.
    # Alternatively, the address can be 0x19 by pulling SDO high (VDDIO).
    _ADRESSES_ALLOWED = [0x18, 0x19]
    
    # No. of bytes that can be written at once
    BMA456_CHUNK_SIZE     = 8
    BMA456_FEATUREBUF_HEADER_IDX    = 0
    BMA456_FEATUREBUF_HEADER_SIZE   = 1
    BMA456_FEATUREBUF_CONTENT_IDX   = BMA456_FEATUREBUF_HEADER_SIZE
    BMA456_FEATUREBUF_TOTAL_SIZE    = (BMA456_FEATUREBUF_HEADER_SIZE + _BMA456_Reg.BMA456_FEATURE_MAX_SIZE)


    # Public attributes
    
    #
    # The dictionary to map range setting bits into the corresponding
    # range value, meant in milli-g.
    #
    dictRange = dictionary( 
        myMap = {
            _BMA456_Reg.BMA456_CNT_ACC_RANGE_2G         :   2000,
            _BMA456_Reg.BMA456_CNT_ACC_RANGE_4G         :   4000,
            _BMA456_Reg.BMA456_CNT_ACC_RANGE_8G         :   8000,
            _BMA456_Reg.BMA456_CNT_ACC_RANGE_16G        :   16000
        },
        mode = dictionary.DICT_STDMODE_UP )
    
    #
    # The dictionary to map data rate setting bits into the corresponding
    # data rates, meant in Hz.
    #
    dictRate = dictionary( 
        myMap = {
            _BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_0P78    :   1,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_1P5     :   2,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_3P1     :   3,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_6P25    :   6,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_12P5    :   12,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_25      :   25,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_50      :   50,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_100     :   100,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_200     :   200,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_400     :   400,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_800     :   800,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_1K6     :   1600,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_3K2     :   3200,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_6K4     :   6400,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_12K8    :   12800
        },
        mode = dictionary.DICT_STDMODE_UP )

    #
    # The dictionary to map config mode settings into averaging window size,
    # i.e. the number of samples to average.
    #
    dictAverage = dictionary(
        myMap = {
            _BMA456_Reg.BMA456_CNT_ACC_CONF_MODE_AVG1   :   1,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_MODE_AVG2   :   2,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_MODE_AVG4   :   4,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_MODE_AVG8   :   8,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_MODE_AVG16  :   16,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_MODE_AVG32  :   32,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_MODE_AVG64  :   64,
            _BMA456_Reg.BMA456_CNT_ACC_CONF_MODE_AVG128 :   128
        },
        mode = dictionary.DICT_STDMODE_NORMAL )

    #
    dictFeatureSetLength = dictionary(
        myMap = {
        _BMA456_Reg.BMA456_FEATURE_SET_WEARABLE  : _BMA456_Reg.BMA456_FSWBL_TOTAL_SIZE,
        _BMA456_Reg.BMA456_FEATURE_SET_HEARABLE  : _BMA456_Reg.BMA456_FSHBL_TOTAL_SIZE,
        _BMA456_Reg.BMA456_FEATURE_SET_MM        : _BMA456_Reg.BMA456_FSMM_TOTAL_SIZE,
        _BMA456_Reg.BMA456_FEATURE_SET_AN        : _BMA456_Reg.BMA456_FSAN_TOTAL_SIZE,
        },
        mode = dictionary.DICT_STDMODE_STRICT )

    #    
    dictConfigLength = dictionary(
        myMap = {
        _BMA456_Reg.BMA456_FEATURE_SET_WEARABLE  : _BMA456_Feature.bma456_wbl_configFileSize,
        _BMA456_Reg.BMA456_FEATURE_SET_HEARABLE  : _BMA456_Feature.bma456_hbl_configFileSize,
        _BMA456_Reg.BMA456_FEATURE_SET_MM        : _BMA456_Feature.bma456_mm_configFileSize,
        _BMA456_Reg.BMA456_FEATURE_SET_AN        : _BMA456_Feature.bma456_an_configFileSize,
        },
        mode = dictionary.DICT_STDMODE_STRICT )
    
    #    
    dictConfigData = dictionary(
        myMap = {
        _BMA456_Reg.BMA456_FEATURE_SET_WEARABLE  : _BMA456_Feature.bma456_wbl_configFile,
        _BMA456_Reg.BMA456_FEATURE_SET_HEARABLE  : _BMA456_Feature.bma456_hbl_configFile,
        _BMA456_Reg.BMA456_FEATURE_SET_MM        : _BMA456_Feature.bma456_mm_configFile,
        _BMA456_Reg.BMA456_FEATURE_SET_AN        : _BMA456_Feature.bma456_an_configFile,
        },
        mode = dictionary.DICT_STDMODE_STRICT )
    
    
    #
    # Constructor
    #
    def __init__(self):
        # Create instance attributes
        self.featureSet = BMA456.BMA456_DEFAULT_FEATURE_SET
        self.featureBuf = []
        self.pinInt1 = None
        self.pinInt2 = None
        self.regInt1IOctrl = 0
        self.regInt2IOctrl = 0
        self.regInt1Map    = 0
        self.regInt2Map    = 0
        self.regIntMapData = 0
        self.sim = SimBusBMA456()
        Serial_Bus_Device.__init__(self)
        Accelerometer.__init__(self)

    #
    # Sensor-specific ("public") helper functions
    #

    def _getFeatureByteAt(self, idx):
        return self.featureBuf[idx]
        
    def _getFeatureWordAt(self, idx):
        high = self._getFeatureByteAt(idx)
        low = self._getFeatureByteAt(idx+1)
        return (high << 8) | low
        
    def _putFeatureByteAt(self, idx, data):
        self.featureBuf[idx] = (data & 0xFF)
        return None
        
    def _putFeatureWordAt(self, idx, data):
        self._putFeatureByteAt(idx, data >> 8)
        self._putFeatureByteAt(idx+1, data & 0xFF)
        return None
            
    #
    # Transfer function to translate digital measurement reading into
    # physical dimension value.
    # return: acceleration in milli-g
    #
    def _transfer( self, reading ):
        ret = reading
        if reading > 0x7FFF:
            ret = reading - 0x10000
            ret = ret * self.dataRange - 0x4000
        else:
            ret = ret * self.dataRange + 0x4000
        ret = ret >> 15
        return ret

    def _readFeatures( self ):
        length, ret = BMA456.dictFeatureSetLength.getValue( self.featureSet )
        if (ret != ErrorCode.errOk):
            ret = ErrorCode.errCorruptData
        else:
            self.featureBuf, ret = self.read_Reg_Buffer( BMA456.BMA456_REG_FEATURES, length )
        return ret

    
    def _writeFeatures( self ):
        ret = self.write_Reg_Buffer( BMA456.BMA456_REG_FEATURES, self.featureBuf )
        return ret

    #
    # Start-up the chip and fill/restore configuration registers
    #
    def _initialize( self ):
        result = ErrorCode.errOk
        
        # Retrieve config file and file size
        if (result == ErrorCode.errOk):
            fileSize, result = BMA456.dictConfigLength.getValue( self.featureSet )
        if (result == ErrorCode.errOk):
            cfgFile, result  = BMA456.dictConfigData.getValue( self.featureSet )
            
        # Test address
        if (result == ErrorCode.errOk):
            val, result = self.read_Reg_Byte( BMA456.BMA456_REG_CHIP_ID )
        if (result == ErrorCode.errOk):
            if (val != BMA456.BMA456_CNT_CHIP_ID ):
                result = ErrorCode.errMalfunction
        if (result == ErrorCode.errOk):
            # Initialization sequence for interrupt feature engine
            # Disable advanced power save mode: PWR_CONF.adv_power_save = 0.
            result = self.write_Reg_Byte( BMA456.BMA456_REG_PWR_CONF, BMA456.BMA456_CNT_PWR_CONF_ADV_PWR_SAVE_DISABLE )
        if (result == ErrorCode.errOk):
            # Wait for 450 us.
            time.sleep( 500 / 1000000 )   
            # Write INIT_CTRL.init_ctrl=0x00
            self.write_Reg_Byte( BMA456.BMA456_REG_INIT_CTRL, BMA456.BMA456_CNT_INIT_CTRL_LOAD_CONFIG_FILE )
            # Load configuration file
            for idx in range(0, fileSize, BMA456.BMA456_CHUNK_SIZE):
                chunk = cfgFile[idx : idx+BMA456.BMA456_CHUNK_SIZE]
                widx = int(idx/2)
                self.write_Reg_Byte( BMA456.BMA456_REG_DMA_LOW, widx & 0x0F )
                self.write_Reg_Byte( BMA456.BMA456_REG_DMA_HI, widx >> 4 )
                self.write_Reg_Buffer( BMA456.BMA456_REG_FEATURES, chunk )
            # Enable sensor features: write 0x01 into register INIT_CTRL.init_ctrl.
            # This operation must not be performed more than once after POR or softreset.
            result = self.write_Reg_Byte( BMA456.BMA456_REG_INIT_CTRL, BMA456.BMA456_CNT_INIT_CTRL_START_INIT )
           
        if (result == ErrorCode.errOk):
            # Check status of the interrupt feature engine
            # Wait until Register INTERNAL_STATUS.message contains the value 1. This will happen after at most 140-150 msec.
            time.sleep( 150 / 1000 )   
            val, result = self.read_Reg_Byte( BMA456.BMA456_REG_INTERNAL_STATUS )
            if ( val & BMA456.BMA456_CNT_INTERNAL_STATUS_MSG) != BMA456.BMA456_CNT_INTERNAL_STATUS_MSG_INIT_OK:
                result = ErrorCode.errFailure
               
        if (result == ErrorCode.errOk):
            # After initialization sequence has been completed, the device is in
            # configuration mode (power mode). Now it is possible to switch to the
            # required power mode and all features are ready to use.
            val, result = self.dictRange.getValue( BMA456.BMA456_CNT_ACC_RANGE_DEFAULT )

        if (result == ErrorCode.errOk):
            self.dataRange = val
            # Clear por_detect bit: read EVENT register and ignore the result.
            val, result = self.read_Reg_Byte( BMA456.BMA456_REG_EVENT )
        
        if (result == ErrorCode.errOk):
            # Read feature parameters
            result = self._readFeatures()

        if (result == ErrorCode.errOk):
            # Configure power mode:
            result = self.setRunLevel( RunLevel.runLevelActive )
            
        if (result == ErrorCode.errOk):
            # Configure interrupt maps:
            self.write_Reg_Byte( BMA456.BMA456_REG_INT1_MAP, self.regInt1Map );
            self.write_Reg_Byte( BMA456.BMA456_REG_INT2_MAP, self.regInt2Map );
            self.write_Reg_Byte( BMA456.BMA456_REG_INT_MAP_DATA, self.regIntMapData );
            # And latch interrupts
            self.write_Reg_Byte( BMA456.BMA456_REG_INT_LATCH, BMA456.BMA456_CNT_INT_LATCH_PERM );
        return result

    #
    # Convert a single interrupt as indicated in the INT_STATUS0+1 word to an
    # Accelerometer.EventSource
    #
    def _bmaInt2accelEvtSrc( self, intID ):
        ret = EventSource.evtSrcNone
    
        # INT_STATUS_1, high-byte
        if( intID & BMA456.BMA456_CNT_INT_STATUS_ACC_DRDY ):
            ret |= EventSource.evtSrcDataRdy;
        if( intID & BMA456.BMA456_CNT_INT_STATUS_AUX_DRDY ):
            ret |= EventSource.evtSrcNone
        if( intID & BMA456.BMA456_CNT_INT_STATUS_FIFO_WM ):
            ret |= EventSource.evtSrcFifoWM
        if( intID & BMA456.BMA456_CNT_INT_STATUS_FIFO_FULL ):
            ret |= EventSource.evtSrcFifoFull
        # INT_STATUS_0, low-byte
        if( intID & BMA456.BMA456_CNT_INT_STATUS_ERROR ):
            ret |= EventSource.evtSrcError
        # Interpretation of the rest of the low-byte INT_STATUS_0 depends
        # on the feature set.
        if (self.featureSet == BMA456.BMA456_FEATURE_SET_WEARABLE):
            if( intID & BMA456.BMA456_FSWBL_CNT_INT_STATUS_NO_MOTION ):
                ret |= EventSource.evtSrcLowSlopeTime
            if( intID & BMA456.BMA456_FSWBL_CNT_INT_STATUS_ANY_MOTION ):
                ret |= EventSource.evtSrcHighSlopeTime
            if( intID & BMA456.BMA456_FSWBL_CNT_INT_STATUS_DBL_TAP ):
                ret |= EventSource.evtSrcTap
            if( intID & BMA456.BMA456_FSWBL_CNT_INT_STATUS_WRIST_WKUP ):
                ret |= EventSource.evtSrcGesture
            if( intID & BMA456.BMA456_FSWBL_CNT_INT_STATUS_ACTIVITY ):
                ret |= EventSource.evtSrcActivity
            if( intID & BMA456.BMA456_FSWBL_CNT_INT_STATUS_STEP_COUNT ):
                ret |= EventSource.evtSrcStep
            if( intID & BMA456.BMA456_FSWBL_CNT_INT_STATUS_TAP_DETECT ):
                ret |= EventSource.evtSrcTap
        elif (self.featureSet == BMA456.BMA456_FEATURE_SET_HEARABLE):
            if( intID & BMA456.BMA456_FSHBL_CNT_INT_STATUS_NO_MOTION ):
                ret |= EventSource.evtSrcLowSlopeTime
            if( intID & BMA456.BMA456_FSHBL_CNT_INT_STATUS_ANY_MOTION ):
                ret |= EventSource.evtSrcHighSlopeTime
            if( intID & BMA456.BMA456_FSHBL_CNT_INT_STATUS_ACTIVITY ):
                ret |= EventSource.evtSrcActivity
            if( intID & BMA456.BMA456_FSHBL_CNT_INT_STATUS_STEP_COUNT ):
                ret |= EventSource.evtSrcStep
            if( intID & BMA456.BMA456_FSHBL_CNT_INT_STATUS_TAP_DETECT ):
                ret |= EventSource.evtSrcTap
        elif (self.featureSet == BMA456.BMA456_FEATURE_SET_MM):
            if( intID & BMA456.BMA456_FSMM_CNT_INT_STATUS_NO_MOTION ):
                ret |= EventSource.evtSrcLowSlopeTime
            if( intID & BMA456.BMA456_FSMM_CNT_INT_STATUS_ANY_MOTION ):
                ret |= EventSource.evtSrcHighSlopeTime
            if( intID & BMA456.BMA456_FSMM_CNT_INT_STATUS_SIG_MOTION ):
                ret |= EventSource.evtSrcSigMotion
            if( intID & BMA456.BMA456_FSMM_CNT_INT_STATUS_HIGH_G ):
                ret |= EventSource.evtSrcHighGTime
            if( intID & BMA456.BMA456_FSMM_CNT_INT_STATUS_LOW_G ):
                ret |= EventSource.evtSrcLowGTime
            if( intID & BMA456.BMA456_FSMM_CNT_INT_STATUS_ORIENT ):
                ret |= EventSource.evtSrcOrientation
            if( intID & BMA456.BMA456_FSMM_CNT_INT_STATUS_TAP_DETECT ):
                ret |= EventSource.evtSrcTap
        elif (self.featureSet == BMA456.BMA456_FEATURE_SET_AN):
            if( intID & BMA456.BMA456_FSAN_CNT_INT_STATUS_NO_MOTION ):
                ret |= EventSource.evtSrcLowSlopeTime
            if( intID & BMA456.BMA456_FSAN_CNT_INT_STATUS_ANY_MOTION ):
                ret |= EventSource.evtSrcHighSlopeTime

        return ret;
    
    #
    # Given a single interrupt identifier, fills the event context structure,
    # i.e. the source and detail attributes, appropriately.
    #
    def _fillEventContext( self, singleIntID, context ):
        ret = ErrorCode.errOk
        
        # Map BMA interrupt source to API event source
        context.source = self._bmaInt2accelEvtSrc( singleIntID )
        # Now, depending on the event source, get additional information.
        if (context.source == EventSource.evtSrcDataRdy):
            context.data, ret = self.getLatestData()
        elif (context.source == EventSource.evtSrcFifoWM) or (context.source == EventSource.evtSrcFifoFull):
            context.status, ret = self.getStatus( StatusID.StatusFifo )
        elif (context.source == EventSource.evtSrcActivity):
            context.status, ret = self.getStatus( StatusID.StatusActivity )
        elif (context.source == EventSource.evtSrcStep):
            context.status, ret = self.getStatus( StatusID.StatusStepCnt )
        elif (context.source == EventSource.evtSrcHighGTime):
            context.status, ret = self.getStatus( StatusID.StatusHighG )
        elif (context.source == EventSource.evtSrcOrientation):
            context.status, ret = self.getStatus( StatusID.StatusOrientation )
        elif (context.source == EventSource.evtSrcTap):
            if( self.featureSet == BMA456.BMA456_FEATURE_SET_WEARABLE ):
                if( singleIntID == BMA456.BMA456_FSWBL_CNT_INT_STATUS_TAP_DETECT ):
                    context.status = Tap.tapSingle
                elif( singleIntID == BMA456.BMA456_FSWBL_CNT_INT_STATUS_DBL_TAP ):
                    context.status = Tap.tapDouble
                else:
                    context.status = Tap.tapNone
            else:
                # Multi-tap concept.
                context.status, ret = self.getStatus( StatusID.StatusTap )
    
        return ret

    #
    # Convert an API accel_EventSource_t to a BMA interrupt-map bit mask
    # compatible to the INTx_MAP and INT_MAP_DATA register content.
    #
    def _accelEvtSrc2bmaMap( self, evtSrc ):
        remainder = evtSrc
    
        # Set INT_MAP_DATA, first
        dataMap = BMA456.BMA456_CNT_INTX_MAP_NONE
        if( evtSrc & EventSource.evtSrcDataRdy ):
            dataMap |= (BMA456.BMA456_CNT_INT_MAP_DATA_INT1_DRDY | BMA456.BMA456_CNT_INT_MAP_DATA_INT2_DRDY)
            remainder &= ~EventSource.evtSrcDataRdy
        if( evtSrc & EventSource.evtSrcFifoWM ):
            dataMap |= (BMA456.BMA456_CNT_INT_MAP_DATA_INT1_FIFO_WM | BMA456.BMA456_CNT_INT_MAP_DATA_INT2_FIFO_WM)
            remainder &= ~EventSource.evtSrcFifoWM
        if( evtSrc & EventSource.evtSrcFifoFull ):
            dataMap |= (BMA456.BMA456_CNT_INT_MAP_DATA_INT1_FIFO_FULL | BMA456.BMA456_CNT_INT_MAP_DATA_INT2_FIFO_FULL)
            remainder &= ~EventSource.evtSrcFifoFull
    
        # Now, set INT1_MAP
        featMap = BMA456.BMA456_CNT_INTX_MAP_NONE
        if( evtSrc & EventSource.evtSrcError ):
            featMap |= BMA456.BMA456_CNT_INTX_MAP_ERROR
            remainder &= ~EventSource.evtSrcError
        
        # Interpretation of INTx_MAP depends on the feature set.
        if (self.featureSet == BMA456.BMA456_FEATURE_SET_WEARABLE):
            if( evtSrc & EventSource.evtSrcLowSlopeTime ):
                featMap |= BMA456.BMA456_FSWBL_CNT_INTX_MAP_NO_MOTION
                remainder &= ~EventSource.evtSrcLowSlopeTime
            if( evtSrc & EventSource.evtSrcHighSlopeTime ):
                featMap |= BMA456.BMA456_FSWBL_CNT_INTX_MAP_ANY_MOTION
                remainder &= ~EventSource.evtSrcHighSlopeTime
            # Double tap must be treated by the caller
            if( evtSrc & EventSource.evtSrcGesture):
                featMap |= BMA456.BMA456_FSWBL_CNT_INTX_MAP_WRIST_WKUP
                remainder &= ~EventSource.evtSrcGesture
            if( evtSrc & EventSource.evtSrcActivity):
                featMap |= BMA456.BMA456_FSWBL_CNT_INTX_MAP_ACTIVITY
                remainder &= ~EventSource.evtSrcActivity
            if( evtSrc & EventSource.evtSrcStep ):
                featMap |= BMA456.BMA456_FSWBL_CNT_INTX_MAP_STEP_CNT
                remainder &= ~EventSource.evtSrcStep
            if( evtSrc & EventSource.evtSrcTap):
                featMap |= BMA456.BMA456_FSWBL_CNT_INTX_MAP_STAP
                remainder &= ~EventSource.evtSrcTap
        elif (self.featureSet == BMA456.BMA456_FEATURE_SET_HEARABLE):
            if( evtSrc & EventSource.evtSrcLowSlopeTime):
                featMap |= BMA456.BMA456_FSHBL_CNT_INTX_MAP_NO_MOTION
                remainder &= ~EventSource.evtSrcLowSlopeTime
            if( evtSrc & EventSource.evtSrcHighSlopeTime):
                featMap |= BMA456.BMA456_FSHBL_CNT_INTX_MAP_ANY_MOTION
                remainder &= ~EventSource.evtSrcHighSlopeTime
            if( evtSrc & EventSource.evtSrcActivity):
                featMap |= BMA456.BMA456_FSHBL_CNT_INTX_MAP_ACTIVITY
                remainder &= ~EventSource.evtSrcActivity
            if( evtSrc & EventSource.evtSrcStep):
                featMap |= BMA456.BMA456_FSHBL_CNT_INTX_MAP_STEP_CNT
                remainder &= ~EventSource.evtSrcStep
            if( evtSrc & EventSource.evtSrcTap):
                featMap |= BMA456.BMA456_FSHBL_CNT_INTX_MAP_TAP
                remainder &= ~EventSource.evtSrcTap
        elif (self.featureSet == BMA456.BMA456_FEATURE_SET_MM):
            if( evtSrc & EventSource.evtSrcLowSlopeTime):
                featMap |= BMA456.BMA456_FSMM_CNT_INTX_MAP_NO_MOTION
                remainder &= ~EventSource.evtSrcLowSlopeTime
            if( evtSrc & EventSource.evtSrcHighSlopeTime):
                featMap |= BMA456.BMA456_FSMM_CNT_INTX_MAP_ANY_MOTION
                remainder &= ~EventSource.evtSrcHighSlopeTime
            if( evtSrc & EventSource.evtSrcSigMotion):
                featMap |= BMA456.BMA456_FSMM_CNT_INTX_MAP_SIG_MOTION
                remainder &= ~EventSource.evtSrcSigMotion
            if( evtSrc & EventSource.evtSrcHighGTime):
                featMap |= BMA456.BMA456_FSMM_CNT_INTX_MAP_HIGH_G
                remainder &= ~EventSource.evtSrcHighGTime
            if( evtSrc & EventSource.evtSrcLowGTime):
                featMap |= BMA456.BMA456_FSMM_CNT_INTX_MAP_LOW_G
                remainder &= ~EventSource.evtSrcLowGTime
            if( evtSrc & EventSource.evtSrcOrientation):
                featMap |= BMA456.BMA456_FSMM_CNT_INTX_MAP_ORIENT
                remainder &= ~EventSource.evtSrcOrientation
            if( evtSrc & EventSource.evtSrcTap):
                featMap |= BMA456.BMA456_FSMM_CNT_INTX_MAP_TAP
                remainder &= ~EventSource.evtSrcTap
        elif (self.featureSet == BMA456.BMA456_FEATURE_SET_AN):
            if( evtSrc & EventSource.evtSrcLowSlopeTime):
                featMap |= BMA456.BMA456_FSAN_CNT_INTX_MAP_NO_MOTION
                remainder &= ~EventSource.evtSrcLowSlopeTime
            if( evtSrc & EventSource.evtSrcHighSlopeTime ):
                featMap |= BMA456.BMA456_FSAN_CNT_INTX_MAP_ANY_MOTION
                remainder &= ~EventSource.evtSrcHighSlopeTime
        return remainder, dataMap, featMap

    #
    # Module API
    #

    @classmethod
    def Params_init(cls, paramDict):
        # Set defaults, where necessary
        if not ("Serial_Bus_Device.deviceAddress" in paramDict):
            paramDict["Serial_Bus_Device.deviceAddress"] = BMA456._ADRESSES_ALLOWED[0]
        else:
            da = paramDict["Serial_Bus_Device.deviceAddress"]
            if not (da in BMA456._ADRESSES_ALLOWED):
                da = BMA456._ADRESSES_ALLOWED[da!=0]   
                paramDict["Serial_Bus_Device.deviceAddress"] = da
        if not ("Sensor.dataRange" in paramDict):
            paramDict["Sensor.dataRange"], _ = BMA456.dictRange.getValue( _BMA456_Reg.BMA456_CNT_ACC_RANGE_DEFAULT )
        if not ("Sensor.dataRate" in paramDict):
            paramDict["Sensor.dataRate"], _ = BMA456.dictRate.getValue( _BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_DEFAULT )
        Accelerometer.Params_init(paramDict)
        Serial_Bus_Device.Params_init(paramDict)
        SimBusBMA456.Params_init(paramDict)
        # Specific configuration options
        if not ("BMA456.INT1_IO_CTRL" in paramDict):
            paramDict["BMA456.INT1_IO_CTRL"] = BMA456.BMA456_CNT_INT1_IO_CTRL_DEFAULT
        if not ("BMA456.INT2_IO_CTRL" in paramDict):
            paramDict["BMA456.INT2_IO_CTRL"] = BMA456.BMA456_CNT_INT2_IO_CTRL_DEFAULT
        if not ("BMA456.INT1_MAP" in paramDict):
            paramDict["BMA456.INT1_MAP"] = BMA456.BMA456_CNT_INTX_MAP_DEFAULT
        if not ("BMA456.INT2_MAP" in paramDict):
            paramDict["BMA456.INT2_MAP"] = BMA456.BMA456_CNT_INTX_MAP_DEFAULT
        if not ("BMA456.INT_MAP_DATA" in paramDict):
            paramDict["BMA456.INT_MAP_DATA"] = BMA456.BMA456_CNT_INT_MAP_DATA_DEFAULT
        # Add interrupt pin /gpio specifics
        paramDict["BMA456.int1.gpio.direction"] = GPIO.DIRECTION_IN
        paramDict["BMA456.int2.gpio.direction"] = GPIO.DIRECTION_IN
        if not ("BMA456.int1.gpio.trigger" in paramDict):
            paramDict["BMA456.int1.gpio.trigger"] = GPIO.TRIGGER_EDGE_FALLING
        if not ("BMA456.int2.gpio.trigger" in paramDict):
            paramDict["BMA456.int2.gpio.trigger"] = GPIO.TRIGGER_EDGE_FALLING
        if not ("BMA456.int1.gpio.bounce" in paramDict):
            paramDict["BMA456.int1.gpio.bounce"] = GPIO.BOUNCE_NONE
        if not ("BMA456.int2.gpio.bounce" in paramDict):
            paramDict["BMA456.int2.gpio.bounce"] = GPIO.BOUNCE_NONE
        gpioParams = {}
        GPIO.Params_init( gpioParams )
        gp1 = dict( [("BMA456.int1."+k,v) for k,v in gpioParams.items()] )
        gp2 = dict( [("BMA456.int2."+k,v) for k,v in gpioParams.items()] )
        gp1.update(gp2)
        for key, value in gp1.items():
            if not( key in paramDict):
                paramDict[key] = value


    def open(self, paramDict):
        result = ErrorCode.errOk
        
        if (self.isAttached()):
            result = ErrorCode.errResourceConflict
        else:
            if not (self.sim is None):
                result = self.sim.open(paramDict)
            if (result == ErrorCode.errOk):
                paramDict["Serial_Bus_Device.deviceAddress"] = paramDict.get("Serial_Bus_Device.deviceAddress", BMA456._ADRESSES_ALLOWED[0])
                result = Serial_Bus_Device.open(self, paramDict)
            if (result == ErrorCode.errOk):
                # Ramp-up the chip
                result = self._initialize()
            if (result == ErrorCode.errOk):
                # Set data rate and range
                result = Accelerometer.open(self, paramDict)
            if (result == ErrorCode.errOk):
                # Setup interrupt related stuff.
                if ("BMA456.int1.gpio.pinDesignator" in paramDict):
                    paramDict["BMA456.int1.gpio.direction"] = GPIO.DIRECTION_IN
                    gpioParams = dict( [(k.replace("BMA456.int1.", ""),v) for k,v in paramDict.items() if k.startswith("BMA456.int1.")] )
                    self.pinInt1 = GPIO()
                    result = self.pinInt1.open(gpioParams)
                    self.regInt1IOctrl = paramDict.get ("BMA456.INT1_IO_CTRL", BMA456.BMA456_CNT_INT1_IO_CTRL_DEFAULT)
                    self.regInt1IOctrl &= ~BMA456.BMA456_CNT_INT1_IO_CTRL_OUTPUT
                    self.regInt1IOctrl |= BMA456.BMA456_CNT_INT1_IO_CTRL_OUTPUT_DISABLE
                    self.write_Reg_Byte( BMA456.BMA456_REG_INT1_IO_CTRL, self.regInt1IOctrl )
                    self.regInt1Map = paramDict.get ("BMA456.INT1_MAP", BMA456.BMA456_CNT_INTX_MAP_DEFAULT)
                    self.write_Reg_Byte( BMA456.BMA456_REG_INT1_MAP, self.regInt1Map )
                if ("BMA456.int2.gpio.pinDesignator" in paramDict):
                    paramDict["BMA456.int2.gpio.direction"] = GPIO.DIRECTION_IN
                    gpioParams = dict( [(k.replace("BMA456.int2.", ""),v) for k,v in paramDict.items() if k.startswith("BMA456.int2.")] )
                    self.pinInt2 = GPIO()
                    result = self.pinInt2.open(gpioParams)
                    self.regInt2IOctrl = paramDict.get ("BMA456.INT2_IO_CTRL", BMA456.BMA456_CNT_INT2_IO_CTRL_DEFAULT)
                    self.regInt2IOctrl &= ~BMA456.BMA456_CNT_INT2_IO_CTRL_OUTPUT
                    self.regInt2IOctrl |= BMA456.BMA456_CNT_INT1_IO_CTRL_OUTPUT_DISABLE
                    self.write_Reg_Byte( BMA456.BMA456_REG_INT2_IO_CTRL, self.regInt2IOctrl )
                    self.regInt2Map = paramDict.get ("BMA456.INT2_MAP", BMA456.BMA456_CNT_INTX_MAP_DEFAULT)
                    self.write_Reg_Byte( BMA456.BMA456_REG_INT2_MAP, self.regInt2Map )
                self.regIntMapData = paramDict.get ("BMA456.INT_MAP_DATA", BMA456.BMA456_CNT_INT_MAP_DATA_DEFAULT)
                self.write_Reg_Byte( BMA456.BMA456_REG_INT_MAP_DATA, self.regIntMapData )
                self.enableInterrupt()
        return result


    def close(self):
        if (self.isAttached()):
            self.setRunLevel( RunLevel.runLevelShutdown )
            Serial_Bus_Device.close(self)
        if not (self.pinInt1 is None):
            self.pinInt1.close()
            self.pinInt1 = None
        if not (self.pinInt2 is None):
            self.pinInt2.close()
            self.pinInt2 = None
        return None
    
    #
    #
    #
    def setRunLevel(self, level):
        ret = ErrorCode.errOk
        pwrCtrl = 0
        pwrConf = 0
        accConf = 0
        if( self.isAttached()):
            # Map run levels to register configurations
            if (level == RunLevel.runLevelActive):  # High performance operating mode
                pwrCtrl = BMA456.BMA456_CNT_PWR_CTRL_ACC_ENABLE | BMA456.BMA456_CNT_PWR_CTRL_AUX_DISABLE
                pwrConf = BMA456.BMA456_CNT_PWR_CONF_ADV_PWR_SAVE_DISABLE
                accConf = BMA456.BMA456_CNT_ACC_CONF_PERF_MODE_CONT
                ret = ErrorCode.errOk
            elif (level == RunLevel.runLevelIdle):  # Averaging operating mode
                pwrCtrl = BMA456.BMA456_CNT_PWR_CTRL_ACC_ENABLE | BMA456.BMA456_CNT_PWR_CTRL_AUX_DISABLE
                pwrConf = BMA456.BMA456_CNT_PWR_CONF_ADV_PWR_SAVE_DISABLE
                accConf = BMA456.BMA456_CNT_ACC_CONF_PERF_MODE_AVG
                ret = ErrorCode.errOk
            elif (level == RunLevel.runLevelRelax): # Low power mode, still operating, automatic FIFO wakeup
                pwrCtrl = BMA456.BMA456_CNT_PWR_CTRL_ACC_ENABLE | BMA456.BMA456_CNT_PWR_CTRL_AUX_DISABLE
                pwrConf = BMA456.BMA456_CNT_PWR_CONF_ADV_PWR_SAVE_ENABLE | BMA456.BMA456_CNT_PWR_CONF_FIFO_WKUP_ENABLE
                accConf = BMA456.BMA456_CNT_ACC_CONF_PERF_MODE_AVG
                ret = ErrorCode.errOk
            elif (level == RunLevel.runLevelSnooze):    # Lowest power mode, still operating, no FIFO wakeup
                pwrCtrl = BMA456.BMA456_CNT_PWR_CTRL_ACC_ENABLE | BMA456.BMA456_CNT_PWR_CTRL_AUX_DISABLE
                pwrConf = BMA456.BMA456_CNT_PWR_CONF_ADV_PWR_SAVE_ENABLE | BMA456.BMA456_CNT_PWR_CONF_FIFO_WKUP_DISABLE
                accConf = BMA456.BMA456_CNT_ACC_CONF_PERF_MODE_AVG
                ret = ErrorCode.errOk
            # Suspend mode, no operation.
            elif (level == RunLevel.runLevelNap) or (level == RunLevel.runLevelSleep) or (level == RunLevel.runLevelDeepSleep) or (level == RunLevel.runLevelShutdown):
                pwrCtrl = BMA456.BMA456_CNT_PWR_CTRL_ACC_DISABLE | BMA456.BMA456_CNT_PWR_CTRL_AUX_DISABLE
                pwrConf = BMA456.BMA456_CNT_PWR_CONF_ADV_PWR_SAVE_ENABLE | BMA456.BMA456_CNT_PWR_CONF_FIFO_WKUP_DISABLE
                accConf = BMA456.BMA456_CNT_ACC_CONF_PERF_MODE_AVG
                ret = ErrorCode.errOk
            else:
                ret = ErrorCode.errNotSupported
            # Apply new register settings
            if( ret == ErrorCode.errOk ):
                ret = self.write_Reg_Byte( BMA456.BMA456_REG_PWR_CTRL, pwrCtrl )
                time.sleep( 450 / 1000000 )   
                ret = self.write_Reg_Byte( BMA456.BMA456_REG_PWR_CONF, pwrConf )
                time.sleep( 450 / 1000000 )   
                # For ACC_CONF, only copy the PERF_MODE bit:
                temp, ret = self.read_Reg_Byte( BMA456.BMA456_REG_ACC_CONF )
                if( (ret == ErrorCode.errOk) and ((temp & BMA456.BMA456_CNT_ACC_CONF_PERF_MODE) != accConf) ):
                    temp &= ~BMA456.BMA456_CNT_ACC_CONF_PERF_MODE
                    accConf |= temp;
                    ret = self.write_Reg_Byte( BMA456.BMA456_REG_ACC_CONF, accConf )
        else:
            ret = ErrorCode.errResourceConflict
        return ret

    #
    # Interruptable API
    #

    #
    #
    #
    def registerInterruptHandler(self, onEvent=None, callerFeedBack=None, handler=None ):
        ret = ErrorCode.errOk
        fAny = False
        if ((onEvent == Event.evtInt1) or (onEvent == Event.evtAny)) and not (self.pinInt1 is None):
            fAny = True
            self.pinInt1.registerInterruptHandler( GPIO.EVENT_DEFAULT, callerFeedBack, handler )
        if ((onEvent == Event.evtInt2) or (onEvent == Event.evtAny)) and not (self.pinInt2 is None):
            fAny = True
            self.pinInt2.registerInterruptHandler( GPIO.EVENT_DEFAULT, callerFeedBack, handler )
        if (fAny):
            ret = self.enableInterrupt()
        else:
            ret = ErrorCode.errExhausted
        return ret
    
    #
    #
    #
    def enableInterrupt(self):
        ret = ErrorCode.errOk
        if (not self.isAttached()):
            ret = ErrorCode.errResourceConflict
        else:
            ret = ErrorCode.errOk
            # Clear interrupt
            _, ret = self.read_Reg_Word( BMA456.BMA456_REG_INT_STATUS )
            # Enable from upper layer down to hardware
            if not (self.pinInt1 is None):
                ret = self.pinInt1.enableInterrupt()
                data = self.regInt1IOctrl & ~BMA456.BMA456_CNT_INT1_IO_CTRL_OUTPUT
                data |= BMA456.BMA456_CNT_INT1_IO_CTRL_OUTPUT_ENABLE
                ret = self.write_Reg_Byte( BMA456.BMA456_REG_INT1_IO_CTRL, data )
            if not(self.pinInt2 is None):
                ret = self.pinInt2.enableInterrupt()
                data = self.regInt2IOctrl & ~BMA456.BMA456_CNT_INT2_IO_CTRL_OUTPUT
                data |= BMA456.BMA456_CNT_INT2_IO_CTRL_OUTPUT_ENABLE
                err = self.write_Reg_Byte( BMA456.BMA456_REG_INT2_IO_CTRL, data )
                if (ret == ErrorCode.errOk):
                    ret = err
        return ret;
    
    #
    #
    #
    def disableInterrupt(self):
        ret = ErrorCode.errOk
        if (not self.isAttached()):
            ret = ErrorCode.errResourceConflict
        else:
            ret = ErrorCode.errOk
            if not(self.pinInt1 is None):
                data = self.regInt1IOctrl & ~BMA456.BMA456_CNT_INT1_IO_CTRL_OUTPUT
                data |= BMA456.BMA456_CNT_INT1_IO_CTRL_OUTPUT_DISABLE
                ret = self.write_Reg_Byte( BMA456.BMA456_REG_INT1_IO_CTRL, data )
                ret = self.pinInt1.disableInterrupt()
            if not(self.pinInt2 is None):
                data = self.regInt2IOctrl & ~BMA456.BMA456_CNT_INT2_IO_CTRL_OUTPUT
                data |= BMA456.BMA456_CNT_INT2_IO_CTRL_OUTPUT_DISABLE
                err = self.write_Reg_Byte( BMA456.BMA456_REG_INT2_IO_CTRL, data )
                if (ret == ErrorCode.errOk):
                    ret = err
                ret = self.pinInt2.disableInterrupt()
        return ret;
 
 
    def getEventContext(self, event, context):
        ret = ErrorCode.errOk
        
        if (context is None):
            ret = ErrorCode.errInvalidParameter
        elif( not self.isAttached() ):
            ret = ErrorCode.errResourceConflict
        elif( event == Event.evtNone ):
            ret = ErrorCode.errFewData
        elif( (event == Event.evtInt1) or (event == Event.evtInt2) ):
            ret = ErrorCode.errOk
            # Retrieving the interrupt status resets all bits in these registers!
            if( context.control == EventContextControl.evtCtxtCtrl_clearAll ):
                _, ret = self.read_Reg_Word( BMA456.BMA456_REG_INT_STATUS )
                context.remainInt = 0;
                context.source = EventSource.evtSrcNone
            else:
                if (context.control == EventContextControl.evtCtxtCtrl_getFirst):
                    data, ret = self.read_Reg_Word( BMA456.BMA456_REG_INT_STATUS )
                    context.remainInt = data
                    context.control = EventContextControl.evtCtxtCtrl_getNext
                elif (context.control == EventContextControl.evtCtxtCtrl_getLast):
                    data, ret = self.read_Reg_Word( BMA456.BMA456_REG_INT_STATUS )
                    context.remainInt = data
                    context.control = EventContextControl.evtCtxtCtrl_getPrevious
                if (ret == ErrorCode.errOk):
                    if (context.remainInt == 0):
                        ret = ErrorCode.errFewData
                    else:
                        data16 = context.remainInt
                        if (context.control == EventContextControl.evtCtxtCtrl_getNext):
                            # Find value of highest bit:
                            data16 = imath.iprevpowtwo( data16 )
                        else:
                            # Find (value of) least bit set:
                            data16 = imath.vlbs(data16)
                        ret = self._fillEventContext( data16, context )
                        context.remainInt &= ~data16
                        if ((ret == ErrorCode.errOk) and (context.remainInt != 0) ):
                            ret = ErrorCode.errMoreData
        else:
            ret = ErrorCode.errInvalidParameter
        return ret;


    #
    # Sensor API, as derived from Sensor
    #

    def selfTest(self, tests):
        ret = ErrorCode.errOk
    
        if ((tests & SelfTest.CONNECTION) and (ret == ErrorCode.errOk) ):
            info, ret = self.getInfo()
            if (ret == ErrorCode.errOk):
                if (info.chipID == BMA456.BMA456_CNT_CHIP_ID):
                    ret = ErrorCode.errOk
                else:
                    ret = ErrorCode.errFailure
        if ((tests & SelfTest.FUNCTIONAL) and (ret == ErrorCode.errOk)):
            # Set +-8g range
            oldRange = self.dataRange
            config = Configuration()
            config.type = ConfigItem.cfgRange
            config.range = BMA456.BMA456_SELFTEST_RANGE
            ret = self.configure( config )
            # Set self-test amplitude to low
            ret = self.write_Reg_Byte( BMA456.BMA456_REG_SELF_TST,
                                       BMA456.BMA456_CNT_SELF_TST_AMP_LOW | BMA456.BMA456_CNT_SELF_TST_DISABLE )
            # ODR=1600Hz, BWP=norm_avg4, performance mode (continuous)
            oldRate, ret = self.read_Reg_Byte( BMA456.BMA456_REG_ACC_CONF )
            ret = self.write_Reg_Byte( BMA456.BMA456_REG_ACC_CONF,
                                        BMA456.BMA456_CNT_ACC_CONF_ODR_1K6 | BMA456.BMA456_CNT_ACC_CONF_MODE_NORM )
            # Wait for min. 2ms
            time.sleep( BMA456.BMA456_SELFTEST_DELAY_CONFIG / 1000000 )
            # Enable self-test and positive test polarity
            ret = self.write_Reg_Byte( BMA456.BMA456_REG_SELF_TST,
                                        BMA456.BMA456_CNT_SELF_TST_AMP_LOW | BMA456.BMA456_CNT_SELF_TST_SIGN_POS | BMA456.BMA456_CNT_SELF_TST_ENABLE )
            # Wait for min. 50ms
            time.sleep( BMA456.BMA456_SELFTEST_DELAY_MEASURE / 1000000 )
            # Read positive acceleration value
            posData, ret = self.getLatestData()
            # Enable self-test and negative test polarity
            ret = self.write_Reg_Byte( BMA456.BMA456_REG_SELF_TST,
                                        BMA456.BMA456_CNT_SELF_TST_AMP_LOW | BMA456.BMA456_CNT_SELF_TST_SIGN_NEG | BMA456.BMA456_CNT_SELF_TST_ENABLE )
            # Wait for min. 50ms
            time.sleep( BMA456.BMA456_SELFTEST_DELAY_MEASURE / 1000000 )
            # Read negative acceleration value
            negData, ret = self.getLatestData()
            # Calculate difference and compare against threshold
            if ((ret == ErrorCode.errOk) and (
                ((posData.x - negData.x) < BMA456.BMA456_SELFTEST_THRESHOLD)   or
                ((posData.y - negData.y) < BMA456.BMA456_SELFTEST_THRESHOLD)   or
                ((posData.z - negData.z) < BMA456.BMA456_SELFTEST_THRESHOLD)   )):
                ret = ErrorCode.errFailure
            # Disable self-test
            self.write_Reg_Byte( BMA456.BMA456_REG_SELF_TST,
                                    BMA456.BMA456_CNT_SELF_TST_AMP_LOW | BMA456.BMA456_CNT_SELF_TST_DISABLE )
            # Restore old configuration
            self.write_Reg_Byte( BMA456.BMA456_REG_ACC_CONF, oldRate )
            config.type = ConfigItem.cfgRange
            config.range = oldRange
            self.configure( config )
        return ret
    
    def reset(self):
        # Known issue with BMA456: It does not ACK the softreset command, when
        # the sensor is not in suspend mode. (Search for "BMA456 soft reset error"!)
        # Instead of suspending, we catch and ignore the exception thrown.
        ret = ErrorCode.errOk
        # Initiate the soft reset
        try:
            ret = self.write_Reg_Byte( BMA456.BMA456_REG_CMD, BMA456.BMA456_CNT_CMD_SOFTRESET )
        except OSError:
            pass
        # Wait for some time
        time.sleep( 5 / 1000 )   
        # Restore configuration
        if (ret == ErrorCode.errOk):
            ret = self._initialize()
            data = self.regInt1IOctrl & ~BMA456.BMA456_CNT_INT1_IO_CTRL_OUTPUT
            data |= BMA456.BMA456_CNT_INT1_IO_CTRL_OUTPUT_DISABLE
            self.write_Reg_Byte( BMA456.BMA456_REG_INT1_IO_CTRL, data )
            self.write_Reg_Byte( BMA456.BMA456_REG_INT1_MAP, self.regInt1Map )
            data = self.regInt2IOctrl & ~BMA456.BMA456_CNT_INT2_IO_CTRL_OUTPUT
            data |= BMA456.BMA456_CNT_INT2_IO_CTRL_OUTPUT_DISABLE
            self.write_Reg_Byte( BMA456.BMA456_REG_INT2_IO_CTRL, data )
            self.write_Reg_Byte( BMA456.BMA456_REG_INT2_MAP, self.regInt2Map )
            self.write_Reg_Byte( BMA456.BMA456_REG_INT_MAP_DATA, self.regIntMapData )
            self.enableInterrupt()
        return ret

    #
    #
    #
    def configure(self, config):
        ret = ErrorCode.errOk
    
        if (config.type == ConfigItem.cfgRate):
            # Construct ACC_CONF register content
            key, ret = self.dictRate.findKey( config.value )
            if (ret == ErrorCode.errOk):
                data = key
                if (isinstance( config, Configuration)):
                    if (config.rateMode.control == SamplingMode.smplAverage):
                        key, ret = self.dictAverage.findKey( config.rateMode.mValue )
                        data |= key
                    elif (config.rateMode.control == SamplingMode.smplNormal):
                        data |= BMA456.BMA456_CNT_ACC_CONF_MODE_NORM
                    elif (config.rateMode.control == SamplingMode.smplOSR2):
                        data |= BMA456.BMA456_CNT_ACC_CONF_MODE_OSR2
                    elif (config.rateMode.control == SamplingMode.smplOSR4):
                        data |= BMA456.BMA456_CNT_ACC_CONF_MODE_OSR4
                    else:
                        ret = ErrorCode.errNotSupported
                else:
                    data |= BMA456.BMA456_CNT_ACC_CONF_MODE_NORM
            if (ret == ErrorCode.errOk):
                ret = self.write_Reg_Byte( BMA456.BMA456_REG_ACC_CONF, data )
                if (ret == ErrorCode.errOk):
                    self.dataRate, _ = self.dictRate.getValue(key)
                    # Check, if configuration is ok
                    data, ret = self.read_Reg_Byte( BMA456.BMA456_REG_ERROR )
                    if ((data & BMA456.BMA456_CNT_ERROR_CODE) == BMA456.BMA456_CNT_ERROR_CODE_ACC):
                        ret = ErrorCode.errSpecRange
        elif (config.type == ConfigItem.cfgRange):
            # Construct ACC_RANGE register content
            key, ret = self.dictRange.findKey( config.value )
            if (ret == ErrorCode.errOk):
                data = key
                ret = self.write_Reg_Byte( BMA456.BMA456_REG_ACC_RANGE, data )
            if (ret == ErrorCode.errOk):
                value, ret = self.dictRange.getValue(key)
            if (ret == ErrorCode.errOk):
                self.dataRange = value
        elif (config.type == ConfigItem.cfgFifo):
            ret = ErrorCode.errNotImplemented
        elif (config.type == ConfigItem.cfgEventArm):
            # Translate accel_EventSource_t into INTxMAP and INT_MAT_DATA bit masks
            remainEvt, dataMap, featureMap = self._accelEvtSrc2bmaMap( config.armedEvents )
            if (remainEvt != EventSource.evtSrcNone):
                ret = ErrorCode.errNotSupported
            else:
                ret = self.write_Reg_Byte( BMA456.BMA456_REG_INT_MAP_DATA, dataMap )
            if (ret == ErrorCode.errOk):
                ret = self.write_Reg_Byte( BMA456.BMA456_REG_INT1_MAP, featureMap )
            if (ret == ErrorCode.errOk):
                ret = self.write_Reg_Byte( BMA456.BMA456_REG_INT2_MAP, featureMap )
        elif (config.type == ConfigItem.cfgEventCondition):
            if (config.eventCondition.event in [EventSource.evtSrcDataRdy, EventSource.evtSrcFifoWM,
                                                        EventSource.evtSrcFifoFull, EventSource.evtSrcError]):
                # Nothing to condition, already done.
                ret = ErrorCode.errOk
            elif (config.eventCondition.event in [EventSource.evtSrcLowGTime, EventSource.evtSrcHighGTime,
                                                          EventSource.evtSrcLowSlopeTime, EventSource.evtSrcHighSlopeTime,
                                                          EventSource.evtSrcSigMotion, EventSource.evtSrcTap,
                                                          EventSource.evtSrcStep, EventSource.evtSrcGesture,
                                                          EventSource.evtSrcActivity, EventSource.evtSrcLyingFlat,
                                                          EventSource.evtSrcOrientation]):
                # Conditions are part of the feature configuration.
                # Changing that, is not implemented.
                ret = ErrorCode.errNotImplemented
            else:
                # Either unsupported event or invalid event mask.
                if( not imath.ispowtwo( config.eventCondition.event ) ):
                    ret = ErrorCode.errInvalidParameter
                else:
                    ret = ErrorCode.errNotSupported
        else:
            ret = ErrorCode.errNotSupported
        return ret;

    #
    # Gets static info data from sensor
    #
    def calibrate(self, calib):
        ret = ErrorCode.errOk
        if (calib.type == CalibrationType.calibDefault):
            ret = ErrorCode.errNotImplemented
        elif (calib.type == CalibrationType.calibTrueValue):
            ret = ErrorCode.errNotImplemented
        else:
            ret = ErrorCode.errNotSupported
        return ret

    #
    # Gets static info data from sensor
    #
    def getInfo(self):
        info = Info()
        
        # Model ID
        info.modelID = self._getFeatureWordAt( BMA456.BMA456_FSWBL_IDX_GENERAL_CONFIG_ID )
        info.validity |= Info.VALID_MODELID
        # Chip ID
        info.chipID, ret = self.read_Reg_Byte( BMA456.BMA456_REG_CHIP_ID )
        info.validity |= Info.VALID_CHIPID
        return info, ret

    #
    # Gets dynamic status data from sensor
    #
    def getStatus(self, statID):
        ret = ErrorCode.errOk
        status = 0
    
        if (statID == StatusID.StatusDieTemp):
            # Temperature in degree Celsiusas Q8.8
            data, ret = self.read_Reg_Byte( BMA456.BMA456_REG_TEMPERATURE )
            if (ret == ErrorCode.errOk):
                # sign-extend data
                if (data > 0x7F):
                    data = data - 0x100
                status = (data + BMA456.BMA456_TEMPERATURE_SHIFT) << 8
        elif (statID == StatusID.StatusDataReady):
            # Just 0 or 1 to indicate if new data is ready
            data, ret = self.read_Reg_Byte( BMA456.BMA456_REG_STATUS )
            if (ret == ErrorCode.errOk):
                status = ((data & BMA456.BMA456_CNT_STATUS_DRDY_ACC) != 0)
        elif (statID == StatusID.StatusInterrupt):
            # EventSource mask
            data, ret = self.read_Reg_Word( BMA456.BMA456_REG_INT_STATUS )
            if (ret == ErrorCode.errOk):
                status = self._bmaInt2accelEvtSrc( data )
        elif (statID == StatusID.StatusFifo):
            # Number of elements in FIFO
            data, ret = self.read_Reg_Word( BMA456.BMA456_REG_FIFO_LENGTH )
            if (ret == ErrorCode.errOk):
                status = data
        elif (statID == StatusID.StatusError):
            # Implementation-specific error/health code
            status = 0
            # Copy INTERNAL_ERROR 0x5F (int_err_2, int_err_1)
            if (ret == ErrorCode.errOk):
                data, ret = self.read_Reg_Byte( BMA456.BMA456_REG_INTERNAL_ERR )
                status = (status << 8) | data
            # Copy INTERNAL_STATUS 0x2A (odr_high_error, odr_50hz_error, axes_remap_error, message)
            if (ret == ErrorCode.errOk):
                data, ret = self.read_Reg_Byte( BMA456.BMA456_REG_INTERNAL_STATUS )
                status = (status << 8) | data
            # Copy EVENT 0x1B (por_detected)
            if (ret == ErrorCode.errOk):
                data, ret = self.read_Reg_Byte( BMA456.BMA456_REG_EVENT )
                status = (status << 8) | data
            # Copy ERR_REG 0x02 (aux_err, fifo_err, error_code, cmd_err, fatal_err)
            if (ret == ErrorCode.errOk):
                data, ret = self.read_Reg_Byte( BMA456.BMA456_REG_ERROR )
                status = (status << 8) | data
        elif (statID == StatusID.StatusActivity):
            # Activity
            if (self.featureSet in [BMA456.BMA456_FEATURE_SET_WEARABLE, BMA456.BMA456_FEATURE_SET_HEARABLE]):
                data, ret = self.read_Reg_Byte( BMA456.BMA456_FSWBL_REG_ACTIVITY_TYPE )
                if (ret == ErrorCode.errOk):
                    if ((data & BMA456.BMA456_FSWBL_CNT_ACTIVITY_TYPE) == BMA456.BMA456_FSWBL_CNT_ACTIVITY_TYPE_UNKNOWN):
                        status = Activity.actUnknown
                    elif ((data & BMA456.BMA456_FSWBL_CNT_ACTIVITY_TYPE) == BMA456.BMA456_FSWBL_CNT_ACTIVITY_TYPE_STILL):
                        status = Activity.actStill
                    elif ((data & BMA456.BMA456_FSWBL_CNT_ACTIVITY_TYPE) == BMA456.BMA456_FSWBL_CNT_ACTIVITY_TYPE_WALK):
                        status = Activity.actWalking
                    elif ((data & BMA456.BMA456_FSWBL_CNT_ACTIVITY_TYPE) == BMA456.BMA456_FSWBL_CNT_ACTIVITY_TYPE_RUN):
                        status = Activity.actRunning
                    else:
                        ret = ErrorCode.errCorruptData
            else:
                ret = ErrorCode.errNotSupported
        elif (statID == StatusID.StatusStepCnt):
            # Step count
            if (self.featureSet in [BMA456.BMA456_FEATURE_SET_WEARABLE, BMA456.BMA456_FEATURE_SET_HEARABLE]):
                status, ret = self.read_Reg_DWord( BMA456.BMA456_FSWBL_REG_STEP_COUNTER )
            else:
                ret = ErrorCode.errNotSupported
        elif (statID == StatusID.StatusHighG):
            # AxesSign
            if (self.featureSet == BMA456.BMA456_FEATURE_SET_MM):
                data, ret = self.read_Reg_Byte( BMA456.BMA456_FSMM_REG_HIGH_G_OUTPUT )
                if (ret == ErrorCode.errOk):
                    status = AxesSign.axsNone
                    if (data & BMA456.BMA456_FSMM_CNT_HIGH_G_OUTPUT_AXES_X ):
                        status |= AxesSign.axsX
                    if (data & BMA456.BMA456_FSMM_CNT_HIGH_G_OUTPUT_AXES_Y ):
                        status |= AxesSign.axsY
                    if (data & BMA456.BMA456_FSMM_CNT_HIGH_G_OUTPUT_AXES_Z ):
                        status |= AxesSign.axsZ
                    if ((data & BMA456.BMA456_FSMM_CNT_HIGH_G_OUTPUT_SIGN) == BMA456.BMA456_FSMM_CNT_HIGH_G_OUTPUT_SIGN_POS ):
                        status |= AxesSign.axsSignPos
                    else:
                        status |= AxesSign.axsSignNeg
            else:
                ret = ErrorCode.errNotSupported
        elif (statID == StatusID.StatusOrientation):
            # accel_Orientation_t mask
            if (self.featureSet == BMA456.BMA456_FEATURE_SET_MM):
                data, ret = self.read_Reg_Byte( BMA456.BMA456_FSMM_REG_ORIENT_OUTPUT )
                if (ret == ErrorCode.errOk):
                    if ((data & BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_STAND) == BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_STAND_PORT_UP):
                        status = Orientation.orientPortUp
                    elif ((data & BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_STAND) == BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_STAND_PORT_DOWNUP):
                        status = Orientation.orientPortDown
                    elif ((data & BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_STAND) == BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_STAND_LAND_LEFT):
                        status = Orientation.orientLandLeft
                    elif ((data & BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_STAND) == BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_STAND_LAND_RIGHT):
                        status = Orientation.orientLandRight
                    else:
                        # Should never reach here.
                        status = Orientation.orientPortUp
                    # face up/down info
                    if ((data & BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_FACE) == BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_FACE_UP):
                        status |= Orientation.orientFaceUp
                    else:
                        status |= Orientation.orientFaceDown
                    status |= Orientation.orientInvalidTilt
            else:
                ret = ErrorCode.errNotSupported
        elif (statID == StatusID.StatusTap):
            # Number of taps detected as an Tap type
            if (self.featureSet == BMA456.BMA456_FEATURE_SET_WEARABLE):
                #
                # Dedicated interrupts for single and double tap, here.
                # So, there is no other chance to find out about single vs.
                # double tap, than to read out INT_STATUS_0, again.
                # As this would clear the pending interrupts, we abstain
                # from this and cannot report more than NONE, at this
                # point.
                #
                status = Tap.tapNone
            elif (self.featureSet == BMA456.BMA456_FEATURE_SET_HEARABLE):
                data, ret = self.read_Reg_Byte( BMA456.BMA456_FSHBL_REG_FEAT_OUT )
                if (ret == ErrorCode.errOk):
                    status = Tap.tapNone
                    if (data & BMA456.BMA456_FSHBL_CNT_FEAT_OUT_STAP):
                        status |= Tap.tapSingle
                    if (data & BMA456.BMA456_FSHBL_CNT_FEAT_OUT_DTAP):
                        status |= Tap.tapDouble
                    if (data & BMA456.BMA456_FSHBL_CNT_FEAT_OUT_TTAP):
                        status |= Tap.tapTriple
            elif (self.featureSet == BMA456.BMA456_FEATURE_SET_MM):
                data, ret = self.read_Reg_Byte( BMA456.BMA456_FSMM_REG_MULTITAP_OUTPUT )
                if (ret == ErrorCode.errOk):
                    status = Tap.tapNone
                    if (data & BMA456.BMA456_FSMM_CNT_MULTITAP_OUTPUT_STAP):
                        status |= Tap.tapSingle
                    if (data & BMA456.BMA456_FSMM_CNT_MULTITAP_OUTPUT_DTAP):
                        status |= Tap.tapDouble
                    if (data & BMA456.BMA456_FSMM_CNT_MULTITAP_OUTPUT_TTAP):
                        status |= Tap.tapTriple
            else:
                ret = ErrorCode.errNotSupported
        elif (statID == StatusID.StatusSensorTime):
            # Sensor time in ms as an unsigned Q24.8
            status, ret = self.read_Reg_DWord( BMA456.BMA456_REG_SENSOR_TIME )
            if (ret == ErrorCode.errOk):
                # Result's LSB is 625/16 = 39.0625 us (microseconds).
                # So we look for result * 625/16 * 256/1000 = result * 10.
                status = status * 10
        else:
            ret = ErrorCode.errNotSupported
        return status, ret


    def getLatestData(self):
        buf, ret = self.read_Reg_Buffer( BMA456.BMA456_REG_ACC_X, 6 )
        if (ret == ErrorCode.errOk):
            x = buf[0] | (buf[1] << 8)
            x = self._transfer( x )
            y = buf[2] | (buf[3] << 8)
            y = self._transfer( y )
            z = buf[4] | (buf[5] << 8)
            z = self._transfer( z )
            data = [x, y, z]
        else:
            data = None
        return data, ret


    def getNextData(self):
        done = False
        while( not done ):
            stat, err = self.getStatus( StatusID.StatusDataReady )
            done = (stat != 0) or (err != ErrorCode.errOk)
        if (err == ErrorCode.errOk):
            data, err = self.getLatestData()
        else:
            data = None
        return data, err


