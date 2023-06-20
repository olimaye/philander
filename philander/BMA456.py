# -*- coding: utf-8 -*-
"""Driver implementation for the BMA456 3-axis digital acceleromter.

More information on the functionality of the chip can be found at
the Bosch-Sensortec site:
https://www.bosch-sensortec.com/products/motion-sensors/accelerometers/bma456/#documents
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["BMA456"]

from bma456_reg import BMA456_Reg
from _bma456_feature import _BMA456_Feature
from accelerometer import Accelerometer, Activity, AxesSign, Configuration, EventSource, Orientation, SamplingMode, StatusID, Tap
from dictionary import dictionary
import imath
from interruptable import Event, EventContextControl, Interruptable
from sensor import CalibrationType, ConfigItem, Info, SelfTest
from serialbus import SerialBusDevice
from systypes import ErrorCode, RunLevel
import time
from simBMA456 import SimDevBMA456
from gpio import GPIO

class BMA456( BMA456_Reg, _BMA456_Feature, SerialBusDevice, Accelerometer, Interruptable ):
    """BMA456 driver implementation.
    """
    
    ADRESSES_ALLOWED = [0x18, 0x19]
    """Default address is 0x18 assuming that SDO is set/tied to GND.
    
    Alternatively, the address can be 0x19 by pulling SDO high (VDDIO).
    """

    BMA456_CHUNK_SIZE     = 8
    """No. of bytes that can be written at once."""
    
    BMA456_FEATUREBUF_HEADER_IDX    = 0
    BMA456_FEATUREBUF_HEADER_SIZE   = 1
    BMA456_FEATUREBUF_CONTENT_IDX   = BMA456_FEATUREBUF_HEADER_SIZE
    BMA456_FEATUREBUF_TOTAL_SIZE    = (BMA456_FEATUREBUF_HEADER_SIZE + BMA456_Reg.BMA456_FEATURE_MAX_SIZE)

    dictRange = dictionary( 
        myMap = {
            BMA456_Reg.BMA456_CNT_ACC_RANGE_2G         :   2000,
            BMA456_Reg.BMA456_CNT_ACC_RANGE_4G         :   4000,
            BMA456_Reg.BMA456_CNT_ACC_RANGE_8G         :   8000,
            BMA456_Reg.BMA456_CNT_ACC_RANGE_16G        :   16000
        },
        mode = dictionary.DICT_STDMODE_UP )
    """The dictionary to map range setting bits into the corresponding\
    range value, meant in milli-g.
    """
    
    dictRate = dictionary( 
        myMap = {
            BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_0P78    :   1,
            BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_1P5     :   2,
            BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_3P1     :   3,
            BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_6P25    :   6,
            BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_12P5    :   12,
            BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_25      :   25,
            BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_50      :   50,
            BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_100     :   100,
            BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_200     :   200,
            BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_400     :   400,
            BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_800     :   800,
            BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_1K6     :   1600,
            BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_3K2     :   3200,
            BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_6K4     :   6400,
            BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_12K8    :   12800
        },
        mode = dictionary.DICT_STDMODE_UP )
    """Dictionary to map data rate setting bits into the corresponding\
    data rates, meant in Hz.
    """
    
    dictAverage = dictionary(
        myMap = {
            BMA456_Reg.BMA456_CNT_ACC_CONF_MODE_AVG1   :   1,
            BMA456_Reg.BMA456_CNT_ACC_CONF_MODE_AVG2   :   2,
            BMA456_Reg.BMA456_CNT_ACC_CONF_MODE_AVG4   :   4,
            BMA456_Reg.BMA456_CNT_ACC_CONF_MODE_AVG8   :   8,
            BMA456_Reg.BMA456_CNT_ACC_CONF_MODE_AVG16  :   16,
            BMA456_Reg.BMA456_CNT_ACC_CONF_MODE_AVG32  :   32,
            BMA456_Reg.BMA456_CNT_ACC_CONF_MODE_AVG64  :   64,
            BMA456_Reg.BMA456_CNT_ACC_CONF_MODE_AVG128 :   128
        },
        mode = dictionary.DICT_STDMODE_NORMAL )
    """Dictionary to map config mode settings into averaging window size,\
    i.e. the number of samples to average.
    """
    
    dictFeatureSetLength = dictionary(
        myMap = {
        BMA456_Reg.BMA456_FEATURE_SET_WEARABLE  : BMA456_Reg.BMA456_FSWBL_TOTAL_SIZE,
        BMA456_Reg.BMA456_FEATURE_SET_HEARABLE  : BMA456_Reg.BMA456_FSHBL_TOTAL_SIZE,
        BMA456_Reg.BMA456_FEATURE_SET_MM        : BMA456_Reg.BMA456_FSMM_TOTAL_SIZE,
        BMA456_Reg.BMA456_FEATURE_SET_AN        : BMA456_Reg.BMA456_FSAN_TOTAL_SIZE,
        },
        mode = dictionary.DICT_STDMODE_STRICT )

    dictConfigLength = dictionary(
        myMap = {
        BMA456_Reg.BMA456_FEATURE_SET_WEARABLE  : _BMA456_Feature.bma456_wbl_configFileSize,
        BMA456_Reg.BMA456_FEATURE_SET_HEARABLE  : _BMA456_Feature.bma456_hbl_configFileSize,
        BMA456_Reg.BMA456_FEATURE_SET_MM        : _BMA456_Feature.bma456_mm_configFileSize,
        BMA456_Reg.BMA456_FEATURE_SET_AN        : _BMA456_Feature.bma456_an_configFileSize,
        },
        mode = dictionary.DICT_STDMODE_STRICT )
    
    dictConfigData = dictionary(
        myMap = {
        BMA456_Reg.BMA456_FEATURE_SET_WEARABLE  : _BMA456_Feature.bma456_wbl_configFile,
        BMA456_Reg.BMA456_FEATURE_SET_HEARABLE  : _BMA456_Feature.bma456_hbl_configFile,
        BMA456_Reg.BMA456_FEATURE_SET_MM        : _BMA456_Feature.bma456_mm_configFile,
        BMA456_Reg.BMA456_FEATURE_SET_AN        : _BMA456_Feature.bma456_an_configFile,
        },
        mode = dictionary.DICT_STDMODE_STRICT )
    
    
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
        self.sim = SimDevBMA456()
        SerialBusDevice.__init__(self)
        Accelerometer.__init__(self)

    #
    # Sensor-specific helper functions
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
            
    def _transfer( self, reading ):
        """Transfer function.
        
        Translate digital measurement reading into physical dimension
        value.
        
        :return: Acceleration in milli-g
        :rtype: 16 bit signed int
        """
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
            self.featureBuf, ret = self.readBufferRegister( BMA456.BMA456_REG_FEATURES, length )
        return ret

    
    def _writeFeatures( self ):
        ret = self.writeBufferRegister( BMA456.BMA456_REG_FEATURES, self.featureBuf )
        return ret

    def _initialize( self ):
        """Start-up the chip and fill/restore configuration registers.
        """
        result = ErrorCode.errOk
        
        # Retrieve config file and file size
        if (result == ErrorCode.errOk):
            fileSize, result = BMA456.dictConfigLength.getValue( self.featureSet )
        if (result == ErrorCode.errOk):
            cfgFile, result  = BMA456.dictConfigData.getValue( self.featureSet )
            
        # Test address
        if (result == ErrorCode.errOk):
            val, result = self.readByteRegister( BMA456.BMA456_REG_CHIP_ID )
        if (result == ErrorCode.errOk):
            if (val != BMA456.BMA456_CNT_CHIP_ID ):
                result = ErrorCode.errMalfunction
        if (result == ErrorCode.errOk):
            # Initialization sequence for interrupt feature engine
            # Disable advanced power save mode: PWR_CONF.adv_power_save = 0.
            result = self.writeByteRegister( BMA456.BMA456_REG_PWR_CONF, BMA456.BMA456_CNT_PWR_CONF_ADV_PWR_SAVE_DISABLE )
        if (result == ErrorCode.errOk):
            # Wait for 450 us.
            time.sleep( 500 / 1000000 )   
            # Write INIT_CTRL.init_ctrl=0x00
            self.writeByteRegister( BMA456.BMA456_REG_INIT_CTRL, BMA456.BMA456_CNT_INIT_CTRL_LOAD_CONFIG_FILE )
            # Load configuration file
            for idx in range(0, fileSize, BMA456.BMA456_CHUNK_SIZE):
                chunk = cfgFile[idx : idx+BMA456.BMA456_CHUNK_SIZE]
                widx = int(idx/2)
                self.writeByteRegister( BMA456.BMA456_REG_DMA_LOW, widx & 0x0F )
                self.writeByteRegister( BMA456.BMA456_REG_DMA_HI, widx >> 4 )
                self.writeBufferRegister( BMA456.BMA456_REG_FEATURES, chunk )
            # Enable sensor features: write 0x01 into register INIT_CTRL.init_ctrl.
            # This operation must not be performed more than once after POR or softreset.
            result = self.writeByteRegister( BMA456.BMA456_REG_INIT_CTRL, BMA456.BMA456_CNT_INIT_CTRL_START_INIT )
           
        if (result == ErrorCode.errOk):
            # Check status of the interrupt feature engine
            # Wait until Register INTERNAL_STATUS.message contains the value 1. This will happen after at most 140-150 msec.
            time.sleep( 150 / 1000 )   
            val, result = self.readByteRegister( BMA456.BMA456_REG_INTERNAL_STATUS )
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
            val, result = self.readByteRegister( BMA456.BMA456_REG_EVENT )
        
        if (result == ErrorCode.errOk):
            # Read feature parameters
            result = self._readFeatures()

        if (result == ErrorCode.errOk):
            # Configure power mode:
            result = self.setRunLevel( RunLevel.active )
            
        if (result == ErrorCode.errOk):
            # Configure interrupt maps:
            self.writeByteRegister( BMA456.BMA456_REG_INT1_MAP, self.regInt1Map );
            self.writeByteRegister( BMA456.BMA456_REG_INT2_MAP, self.regInt2Map );
            self.writeByteRegister( BMA456.BMA456_REG_INT_MAP_DATA, self.regIntMapData );
            # And latch interrupts
            self.writeByteRegister( BMA456.BMA456_REG_INT_LATCH, BMA456.BMA456_CNT_INT_LATCH_PERM );
        return result

    def _bmaInt2accelEvtSrc( self, intID ):
        """Convert a single interrupt as indicated in the INT_STATUS0+1\
        word to an :class:`EventSource`.
        
        The exact mapping is documented at :meth:`getStatus`.
        
        :param int intID: Interrupt indicator as read from INT_STATUS0+1 register.
        :returns: Event source flag
        :rtype: EventSource
        """
        ret = EventSource.none
    
        # INT_STATUS_1, high-byte
        if( intID & BMA456.BMA456_CNT_INT_STATUS_ACC_DRDY ):
            ret |= EventSource.dataReady;
        if( intID & BMA456.BMA456_CNT_INT_STATUS_AUX_DRDY ):
            ret |= EventSource.none
        if( intID & BMA456.BMA456_CNT_INT_STATUS_FIFO_WM ):
            ret |= EventSource.fifoWatermark
        if( intID & BMA456.BMA456_CNT_INT_STATUS_FIFO_FULL ):
            ret |= EventSource.fifoFull
        # INT_STATUS_0, low-byte
        if( intID & BMA456.BMA456_CNT_INT_STATUS_ERROR ):
            ret |= EventSource.error
        # Interpretation of the rest of the low-byte INT_STATUS_0 depends
        # on the feature set.
        if (self.featureSet == BMA456.BMA456_FEATURE_SET_WEARABLE):
            if( intID & BMA456.BMA456_FSWBL_CNT_INT_STATUS_NO_MOTION ):
                ret |= EventSource.lowSlopeTime
            if( intID & BMA456.BMA456_FSWBL_CNT_INT_STATUS_ANY_MOTION ):
                ret |= EventSource.highSlopeTime
            if( intID & BMA456.BMA456_FSWBL_CNT_INT_STATUS_DBL_TAP ):
                ret |= EventSource.tap
            if( intID & BMA456.BMA456_FSWBL_CNT_INT_STATUS_WRIST_WKUP ):
                ret |= EventSource.gesture
            if( intID & BMA456.BMA456_FSWBL_CNT_INT_STATUS_ACTIVITY ):
                ret |= EventSource.activity
            if( intID & BMA456.BMA456_FSWBL_CNT_INT_STATUS_STEP_COUNT ):
                ret |= EventSource.step
            if( intID & BMA456.BMA456_FSWBL_CNT_INT_STATUS_TAP_DETECT ):
                ret |= EventSource.tap
        elif (self.featureSet == BMA456.BMA456_FEATURE_SET_HEARABLE):
            if( intID & BMA456.BMA456_FSHBL_CNT_INT_STATUS_NO_MOTION ):
                ret |= EventSource.lowSlopeTime
            if( intID & BMA456.BMA456_FSHBL_CNT_INT_STATUS_ANY_MOTION ):
                ret |= EventSource.highSlopeTime
            if( intID & BMA456.BMA456_FSHBL_CNT_INT_STATUS_ACTIVITY ):
                ret |= EventSource.activity
            if( intID & BMA456.BMA456_FSHBL_CNT_INT_STATUS_STEP_COUNT ):
                ret |= EventSource.step
            if( intID & BMA456.BMA456_FSHBL_CNT_INT_STATUS_TAP_DETECT ):
                ret |= EventSource.tap
        elif (self.featureSet == BMA456.BMA456_FEATURE_SET_MM):
            if( intID & BMA456.BMA456_FSMM_CNT_INT_STATUS_NO_MOTION ):
                ret |= EventSource.lowSlopeTime
            if( intID & BMA456.BMA456_FSMM_CNT_INT_STATUS_ANY_MOTION ):
                ret |= EventSource.highSlopeTime
            if( intID & BMA456.BMA456_FSMM_CNT_INT_STATUS_SIG_MOTION ):
                ret |= EventSource.significantMotion
            if( intID & BMA456.BMA456_FSMM_CNT_INT_STATUS_HIGH_G ):
                ret |= EventSource.highGTime
            if( intID & BMA456.BMA456_FSMM_CNT_INT_STATUS_LOW_G ):
                ret |= EventSource.lowGTime
            if( intID & BMA456.BMA456_FSMM_CNT_INT_STATUS_ORIENT ):
                ret |= EventSource.orientation
            if( intID & BMA456.BMA456_FSMM_CNT_INT_STATUS_TAP_DETECT ):
                ret |= EventSource.tap
        elif (self.featureSet == BMA456.BMA456_FEATURE_SET_AN):
            if( intID & BMA456.BMA456_FSAN_CNT_INT_STATUS_NO_MOTION ):
                ret |= EventSource.lowSlopeTime
            if( intID & BMA456.BMA456_FSAN_CNT_INT_STATUS_ANY_MOTION ):
                ret |= EventSource.highSlopeTime

        return ret;
    
    def _fillEventContext( self, singleIntID, context ):
        """Given a single interrupt identifier, fill the event context\
        structure, i.e. the source and detail attributes, appropriately.
        
        The mapping is detailed at :meth:`getEventContext`.
        """
        ret = ErrorCode.errOk
        
        # Map BMA interrupt source to API event source
        context.source = self._bmaInt2accelEvtSrc( singleIntID )
        # Now, depending on the event source, get additional information.
        if (context.source == EventSource.dataReady):
            context.data, ret = self.getLatestData()
        elif (context.source == EventSource.fifoWatermark) or (context.source == EventSource.fifoFull):
            context.status, ret = self.getStatus( StatusID.fifo )
        elif (context.source == EventSource.activity):
            context.status, ret = self.getStatus( StatusID.activity )
        elif (context.source == EventSource.step):
            context.status, ret = self.getStatus( StatusID.stepCount )
        elif (context.source == EventSource.highGTime):
            context.status, ret = self.getStatus( StatusID.highG )
        elif (context.source == EventSource.orientation):
            context.status, ret = self.getStatus( StatusID.orientation )
        elif (context.source == EventSource.tap):
            if( self.featureSet == BMA456.BMA456_FEATURE_SET_WEARABLE ):
                if( singleIntID == BMA456.BMA456_FSWBL_CNT_INT_STATUS_TAP_DETECT ):
                    context.status = Tap.single
                elif( singleIntID == BMA456.BMA456_FSWBL_CNT_INT_STATUS_DBL_TAP ):
                    context.status = Tap.double
                else:
                    context.status = Tap.none
            else:
                # Multi-tap concept.
                context.status, ret = self.getStatus( StatusID.tap )
    
        return ret

    def _accelEvtSrc2bmaMap( self, evtSrc ):
        """For a given event source, get the corresponding interrupt map.
        
        Convert an :class:`EventSource` to a BMA interrupt-map bit mask
        compatible to the INTx_MAP and INT_MAP_DATA register content.
        The translation is described in detail at :meth:`configure`
        when arming events.
        """
        remainder = evtSrc
    
        # Set INT_MAP_DATA, first
        dataMap = BMA456.BMA456_CNT_INTX_MAP_NONE
        if( evtSrc & EventSource.dataReady ):
            dataMap |= (BMA456.BMA456_CNT_INT_MAP_DATA_INT1_DRDY | BMA456.BMA456_CNT_INT_MAP_DATA_INT2_DRDY)
            remainder &= ~EventSource.dataReady
        if( evtSrc & EventSource.fifoWatermark ):
            dataMap |= (BMA456.BMA456_CNT_INT_MAP_DATA_INT1_FIFO_WM | BMA456.BMA456_CNT_INT_MAP_DATA_INT2_FIFO_WM)
            remainder &= ~EventSource.fifoWatermark
        if( evtSrc & EventSource.fifoFull ):
            dataMap |= (BMA456.BMA456_CNT_INT_MAP_DATA_INT1_FIFO_FULL | BMA456.BMA456_CNT_INT_MAP_DATA_INT2_FIFO_FULL)
            remainder &= ~EventSource.fifoFull
    
        # Now, set INT1_MAP
        featMap = BMA456.BMA456_CNT_INTX_MAP_NONE
        if( evtSrc & EventSource.error ):
            featMap |= BMA456.BMA456_CNT_INTX_MAP_ERROR
            remainder &= ~EventSource.error
        
        # Interpretation of INTx_MAP depends on the feature set.
        if (self.featureSet == BMA456.BMA456_FEATURE_SET_WEARABLE):
            if( evtSrc & EventSource.lowSlopeTime ):
                featMap |= BMA456.BMA456_FSWBL_CNT_INTX_MAP_NO_MOTION
                remainder &= ~EventSource.lowSlopeTime
            if( evtSrc & EventSource.highSlopeTime ):
                featMap |= BMA456.BMA456_FSWBL_CNT_INTX_MAP_ANY_MOTION
                remainder &= ~EventSource.highSlopeTime
            # Double tap must be treated by the caller
            if( evtSrc & EventSource.gesture):
                featMap |= BMA456.BMA456_FSWBL_CNT_INTX_MAP_WRIST_WKUP
                remainder &= ~EventSource.gesture
            if( evtSrc & EventSource.activity):
                featMap |= BMA456.BMA456_FSWBL_CNT_INTX_MAP_ACTIVITY
                remainder &= ~EventSource.activity
            if( evtSrc & EventSource.step ):
                featMap |= BMA456.BMA456_FSWBL_CNT_INTX_MAP_STEP_CNT
                remainder &= ~EventSource.step
            if( evtSrc & EventSource.tap):
                featMap |= BMA456.BMA456_FSWBL_CNT_INTX_MAP_STAP
                remainder &= ~EventSource.tap
        elif (self.featureSet == BMA456.BMA456_FEATURE_SET_HEARABLE):
            if( evtSrc & EventSource.lowSlopeTime):
                featMap |= BMA456.BMA456_FSHBL_CNT_INTX_MAP_NO_MOTION
                remainder &= ~EventSource.lowSlopeTime
            if( evtSrc & EventSource.highSlopeTime):
                featMap |= BMA456.BMA456_FSHBL_CNT_INTX_MAP_ANY_MOTION
                remainder &= ~EventSource.highSlopeTime
            if( evtSrc & EventSource.activity):
                featMap |= BMA456.BMA456_FSHBL_CNT_INTX_MAP_ACTIVITY
                remainder &= ~EventSource.activity
            if( evtSrc & EventSource.step):
                featMap |= BMA456.BMA456_FSHBL_CNT_INTX_MAP_STEP_CNT
                remainder &= ~EventSource.step
            if( evtSrc & EventSource.tap):
                featMap |= BMA456.BMA456_FSHBL_CNT_INTX_MAP_TAP
                remainder &= ~EventSource.tap
        elif (self.featureSet == BMA456.BMA456_FEATURE_SET_MM):
            if( evtSrc & EventSource.lowSlopeTime):
                featMap |= BMA456.BMA456_FSMM_CNT_INTX_MAP_NO_MOTION
                remainder &= ~EventSource.lowSlopeTime
            if( evtSrc & EventSource.highSlopeTime):
                featMap |= BMA456.BMA456_FSMM_CNT_INTX_MAP_ANY_MOTION
                remainder &= ~EventSource.highSlopeTime
            if( evtSrc & EventSource.significantMotion):
                featMap |= BMA456.BMA456_FSMM_CNT_INTX_MAP_SIG_MOTION
                remainder &= ~EventSource.significantMotion
            if( evtSrc & EventSource.highGTime):
                featMap |= BMA456.BMA456_FSMM_CNT_INTX_MAP_HIGH_G
                remainder &= ~EventSource.highGTime
            if( evtSrc & EventSource.lowGTime):
                featMap |= BMA456.BMA456_FSMM_CNT_INTX_MAP_LOW_G
                remainder &= ~EventSource.lowGTime
            if( evtSrc & EventSource.orientation):
                featMap |= BMA456.BMA456_FSMM_CNT_INTX_MAP_ORIENT
                remainder &= ~EventSource.orientation
            if( evtSrc & EventSource.tap):
                featMap |= BMA456.BMA456_FSMM_CNT_INTX_MAP_TAP
                remainder &= ~EventSource.tap
        elif (self.featureSet == BMA456.BMA456_FEATURE_SET_AN):
            if( evtSrc & EventSource.lowSlopeTime):
                featMap |= BMA456.BMA456_FSAN_CNT_INTX_MAP_NO_MOTION
                remainder &= ~EventSource.lowSlopeTime
            if( evtSrc & EventSource.highSlopeTime ):
                featMap |= BMA456.BMA456_FSAN_CNT_INTX_MAP_ANY_MOTION
                remainder &= ~EventSource.highSlopeTime
        return remainder, dataMap, featMap

    #
    # Module API
    #

    @classmethod
    def Params_init(cls, paramDict):
        """Initializes configuration parameters with defaults.
        
        The following settings are supported:
        
        =============================    ==========================================================================================================
        Key name                         Value type, meaning and default
        =============================    ==========================================================================================================
        SerialBusDevice.deviceAddress    ``int`` I2C serial device address, one of :attr:`ADRESSES_ALLOWED`; default is :attr:`ADRESSES_ALLOWED` ``[0]``.
        Sensor.dataRange                 ``int`` Measurement range in milli-g; default corresponds to :attr:`.BMA456_CNT_ACC_RANGE_DEFAULT`.
        Sensor.dataRate                  ``int`` Data rate in Hz; default corresponds to :attr:`.BMA456_CNT_ACC_CONF_ODR_DEFAULT`.
        BMA456.INT1_IO_CTRL              ``int`` Content of the INT1_IO_CTRL register; default is :attr:`.BMA456_CNT_INT1_IO_CTRL_DEFAULT`.
        BMA456.INT2_IO_CTRL              ``int`` Content of the INT2_IO_CTRL register; default is :attr:`.BMA456_CNT_INT2_IO_CTRL_DEFAULT`.
        BMA456.INT1_MAP                  ``int`` Content of the INT1_MAP register; default is :attr:`.BMA456_CNT_INTX_MAP_DEFAULT`.
        BMA456.INT2_MAP                  ``int`` Content of the INT2_MAP register; default is :attr:`.BMA456_CNT_INTX_MAP_DEFAULT`.
        BMA456.INT_MAP_DATA              ``int`` Content of the INT_MAP_DATA register; default is :attr:`.BMA456_CNT_INT_MAP_DATA_DEFAULT`.
        BMA456.int1.gpio.direction       see :meth:`.GPIO.Params_init`; default is :attr:`.GPIO.DIRECTION_IN`.
        BMA456.int2.gpio.direction       see :meth:`.GPIO.Params_init`; default is :attr:`.GPIO.DIRECTION_IN`.
        BMA456.int1.gpio.trigger         see :meth:`.GPIO.Params_init`; default is :attr:`.GPIO.TRIGGER_EDGE_FALLING`.
        BMA456.int2.gpio.trigger         see :meth:`.GPIO.Params_init`; default is :attr:`.GPIO.TRIGGER_EDGE_FALLING`.
        BMA456.int1.gpio.bounce          see :meth:`.GPIO.Params_init`; default is :attr:`.GPIO.BOUNCE_NONE`.
        BMA456.int2.gpio.bounce          see :meth:`.GPIO.Params_init`; default is :attr:`.GPIO.BOUNCE_NONE`.
        All other BMA456.int1.gpio.* and BMA456.int1.gpio.* settings as documented at :meth:`.GPIO.Params_init`.
        ===========================================================================================================================================
        
        For the ``SerialBusDevice.deviceAddress`` value, also 0 or 1
        can be specified alternatively to the absolute addresses to reflect
        the level of the ``SDO`` pin. In this case, 0 will be mapped to
        0x18, while 1 maps to 0x19.
        
        Also see: :meth:`.Sensor.Params_init`, :meth:`.SerialBusDevice.Params_init`, :meth:`.GPIO.Params_init`. 
        """
        # Set defaults, where necessary
        if not ("SerialBusDevice.deviceAddress" in paramDict):
            paramDict["SerialBusDevice.deviceAddress"] = BMA456.ADRESSES_ALLOWED[0]
        else:
            da = paramDict["SerialBusDevice.deviceAddress"]
            if not (da in BMA456.ADRESSES_ALLOWED):
                da = BMA456.ADRESSES_ALLOWED[da!=0]   
                paramDict["SerialBusDevice.deviceAddress"] = da
        if not ("Sensor.dataRange" in paramDict):
            paramDict["Sensor.dataRange"], _ = BMA456.dictRange.getValue( BMA456_Reg.BMA456_CNT_ACC_RANGE_DEFAULT )
        if not ("Sensor.dataRate" in paramDict):
            paramDict["Sensor.dataRate"], _ = BMA456.dictRate.getValue( BMA456_Reg.BMA456_CNT_ACC_CONF_ODR_DEFAULT )
        Accelerometer.Params_init(paramDict)
        SerialBusDevice.Params_init(paramDict)
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
        return None

    def open(self, paramDict):
        """Set up serial communication and initialize the chip.
        
        Must be called once, before the device can be used.
        Carry out the following steps:
        
        * establish serial communication, attach device to bus, if necessary.
        * execute the device initialization procedure, see chapter 4.2 of the data sheet for more information.
        * adjust data rate and measurement range
        * set up interrupt GPIO pins - direction, trigger etc.
        * set up interrupt behavior - registers IOCTRL, INT1_MAP etc.
        * enable interrupts
        
        Additionally to the defaults generated by :meth:`.Params_init`,
        the following configuration parameters are supported - as documented
        at :meth:`.GPIO.open`:
        
        * BMA456.int1.gpio.pinDesignator
        * BMA456.int2.gpio.pinDesignator
        
        Also see :meth:`.Sensor.open`, :meth:`.close`. 
        """
        result = ErrorCode.errOk
        
        if (self.isAttached()):
            result = ErrorCode.errResourceConflict
        else:
            if not (self.sim is None):
                result = self.sim.open(paramDict)
            if (result == ErrorCode.errOk):
                paramDict["SerialBusDevice.deviceAddress"] = paramDict.get("SerialBusDevice.deviceAddress", BMA456.ADRESSES_ALLOWED[0])
                result = SerialBusDevice.open(self, paramDict)
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
                    self.writeByteRegister( BMA456.BMA456_REG_INT1_IO_CTRL, self.regInt1IOctrl )
                    self.regInt1Map = paramDict.get ("BMA456.INT1_MAP", BMA456.BMA456_CNT_INTX_MAP_DEFAULT)
                    self.writeByteRegister( BMA456.BMA456_REG_INT1_MAP, self.regInt1Map )
                if ("BMA456.int2.gpio.pinDesignator" in paramDict):
                    paramDict["BMA456.int2.gpio.direction"] = GPIO.DIRECTION_IN
                    gpioParams = dict( [(k.replace("BMA456.int2.", ""),v) for k,v in paramDict.items() if k.startswith("BMA456.int2.")] )
                    self.pinInt2 = GPIO()
                    result = self.pinInt2.open(gpioParams)
                    self.regInt2IOctrl = paramDict.get ("BMA456.INT2_IO_CTRL", BMA456.BMA456_CNT_INT2_IO_CTRL_DEFAULT)
                    self.regInt2IOctrl &= ~BMA456.BMA456_CNT_INT2_IO_CTRL_OUTPUT
                    self.regInt2IOctrl |= BMA456.BMA456_CNT_INT1_IO_CTRL_OUTPUT_DISABLE
                    self.writeByteRegister( BMA456.BMA456_REG_INT2_IO_CTRL, self.regInt2IOctrl )
                    self.regInt2Map = paramDict.get ("BMA456.INT2_MAP", BMA456.BMA456_CNT_INTX_MAP_DEFAULT)
                    self.writeByteRegister( BMA456.BMA456_REG_INT2_MAP, self.regInt2Map )
                self.regIntMapData = paramDict.get ("BMA456.INT_MAP_DATA", BMA456.BMA456_CNT_INT_MAP_DATA_DEFAULT)
                self.writeByteRegister( BMA456.BMA456_REG_INT_MAP_DATA, self.regIntMapData )
                self.enableInterrupt()
        return result


    def close(self):
        """Shut down the device after usage.
        
        This method should be called when the device is not used, anymore,
        e.g. as part of the application exit procedure.
        The following steps are executed:
        
        * shut down the device by switching to :attr:`.RunLevel.shutdown`
        * close serial communication, detach from bus.
        * close GPIO pins for int1 and int2
        
        After return, the device can still be re-used, by calling
        :meth:`.open` again.
        
        Also see: :meth:`.SerialBusDevice.close`, :meth:`.GPIO.close`,
        :meth:`.Module.close`.
        """
        result = ErrorCode.errOk
        if (self.isAttached()):
            result = self.setRunLevel( RunLevel.shutdown )
            result = SerialBusDevice.close(self)
        if not (self.pinInt1 is None):
            result = self.pinInt1.close()
            self.pinInt1 = None
        if not (self.pinInt2 is None):
            result = self.pinInt2.close()
            self.pinInt2 = None
        return result
    
    def setRunLevel(self, level):
        """Switches the device to the desired power-save mode.
        
        The given run level affects the hardware registers
        :attr:`.BMA456_REG_PWR_CTRL`,
        :attr:`.BMA456_REG_PWR_CONF` and
        :attr:`.BMA456_REG_ACC_CONF`
        and, thus, chip behavior as follows:

        ==============   =======   =======    ================    ==============    =============
        RunLevel         ACC_EN    AUX_EN     FIFO_SELF_WAKEUP    ADV_POWER_SAVE    ACC_PERF_MODE
        ==============   =======   =======    ================    ==============    =============
        active           ENABLE    DISABLE    DISABLE             DISABLE           CONT
        idle             ENABLE    DISABLE    DISABLE             DISABLE           AVG
        relax            ENABLE    DISABLE    ENABLE              ENABLE            AVG
        snooze           ENABLE    DISABLE    DISABLE             ENABLE            AVG
        nap and below    DISABLE   DISABLE    DISABLE             ENABLE            AVG
        ==============   =======   =======    ================    ==============    =============
        
        For detailed information on the power modes of the underlying
        hardware, see the data shhet, chapter 4.3.
        
        Also see :meth:`.Module.setRunLevel`.
        
        :param RunLevel level: The level to switch to.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        pwrCtrl = 0
        pwrConf = 0
        accConf = 0
        if( self.isAttached()):
            # Map run levels to register configurations
            if (level == RunLevel.active):  # High performance operating mode
                pwrCtrl = BMA456.BMA456_CNT_PWR_CTRL_ACC_ENABLE | BMA456.BMA456_CNT_PWR_CTRL_AUX_DISABLE
                pwrConf = BMA456.BMA456_CNT_PWR_CONF_ADV_PWR_SAVE_DISABLE
                accConf = BMA456.BMA456_CNT_ACC_CONF_PERF_MODE_CONT
                ret = ErrorCode.errOk
            elif (level == RunLevel.idle):  # Averaging operating mode
                pwrCtrl = BMA456.BMA456_CNT_PWR_CTRL_ACC_ENABLE | BMA456.BMA456_CNT_PWR_CTRL_AUX_DISABLE
                pwrConf = BMA456.BMA456_CNT_PWR_CONF_ADV_PWR_SAVE_DISABLE
                accConf = BMA456.BMA456_CNT_ACC_CONF_PERF_MODE_AVG
                ret = ErrorCode.errOk
            elif (level == RunLevel.relax): # Low power mode, still operating, automatic FIFO wakeup
                pwrCtrl = BMA456.BMA456_CNT_PWR_CTRL_ACC_ENABLE | BMA456.BMA456_CNT_PWR_CTRL_AUX_DISABLE
                pwrConf = BMA456.BMA456_CNT_PWR_CONF_ADV_PWR_SAVE_ENABLE | BMA456.BMA456_CNT_PWR_CONF_FIFO_WKUP_ENABLE
                accConf = BMA456.BMA456_CNT_ACC_CONF_PERF_MODE_AVG
                ret = ErrorCode.errOk
            elif (level == RunLevel.snooze):    # Lowest power mode, still operating, no FIFO wakeup
                pwrCtrl = BMA456.BMA456_CNT_PWR_CTRL_ACC_ENABLE | BMA456.BMA456_CNT_PWR_CTRL_AUX_DISABLE
                pwrConf = BMA456.BMA456_CNT_PWR_CONF_ADV_PWR_SAVE_ENABLE | BMA456.BMA456_CNT_PWR_CONF_FIFO_WKUP_DISABLE
                accConf = BMA456.BMA456_CNT_ACC_CONF_PERF_MODE_AVG
                ret = ErrorCode.errOk
            # Suspend mode, no operation.
            elif (level == RunLevel.nap) or (level == RunLevel.sleep) or (level == RunLevel.deepSleep) or (level == RunLevel.shutdown):
                pwrCtrl = BMA456.BMA456_CNT_PWR_CTRL_ACC_DISABLE | BMA456.BMA456_CNT_PWR_CTRL_AUX_DISABLE
                pwrConf = BMA456.BMA456_CNT_PWR_CONF_ADV_PWR_SAVE_ENABLE | BMA456.BMA456_CNT_PWR_CONF_FIFO_WKUP_DISABLE
                accConf = BMA456.BMA456_CNT_ACC_CONF_PERF_MODE_AVG
                ret = ErrorCode.errOk
            else:
                ret = ErrorCode.errNotSupported
            # Apply new register settings
            if( ret == ErrorCode.errOk ):
                ret = self.writeByteRegister( BMA456.BMA456_REG_PWR_CTRL, pwrCtrl )
                time.sleep( 450 / 1000000 )   
                ret = self.writeByteRegister( BMA456.BMA456_REG_PWR_CONF, pwrConf )
                time.sleep( 450 / 1000000 )   
                # For ACC_CONF, only copy the PERF_MODE bit:
                temp, ret = self.readByteRegister( BMA456.BMA456_REG_ACC_CONF )
                if( (ret == ErrorCode.errOk) and ((temp & BMA456.BMA456_CNT_ACC_CONF_PERF_MODE) != accConf) ):
                    temp &= ~BMA456.BMA456_CNT_ACC_CONF_PERF_MODE
                    accConf |= temp;
                    ret = self.writeByteRegister( BMA456.BMA456_REG_ACC_CONF, accConf )
        else:
            ret = ErrorCode.errResourceConflict
        return ret

    #
    # Interruptable API
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
    
    def enableInterrupt(self):
        """Enable the interrupt mechanism/engine.
        
        Clear the interrupts that possibly occurred so far. Then, enable
        interrupt signaling at the corresponding GPIO pin. Finally, set
        the OUTPUT_ENABLE bit at the involved interrupt IO_CTRL
        registers.
        
        Note that this method is just for switching the interrupt capability
        on.
        For switching it off, see :meth:`.disableInterrupt`.
        For configuring interrupts, see :meth:`.configure` and
        :meth:`.registerInterruptHandler`.
        
        Also see :meth:`.Interruptable.enableInterrupt`.
        
        :return: An error code indicating either success or the reason\
        of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if (not self.isAttached()):
            ret = ErrorCode.errResourceConflict
        else:
            ret = ErrorCode.errOk
            # Clear interrupt
            _, ret = self.readWordRegister( BMA456.BMA456_REG_INT_STATUS )
            # Enable from upper layer down to hardware
            if not (self.pinInt1 is None):
                ret = self.pinInt1.enableInterrupt()
                data = self.regInt1IOctrl & ~BMA456.BMA456_CNT_INT1_IO_CTRL_OUTPUT
                data |= BMA456.BMA456_CNT_INT1_IO_CTRL_OUTPUT_ENABLE
                ret = self.writeByteRegister( BMA456.BMA456_REG_INT1_IO_CTRL, data )
            if not(self.pinInt2 is None):
                ret = self.pinInt2.enableInterrupt()
                data = self.regInt2IOctrl & ~BMA456.BMA456_CNT_INT2_IO_CTRL_OUTPUT
                data |= BMA456.BMA456_CNT_INT2_IO_CTRL_OUTPUT_ENABLE
                err = self.writeByteRegister( BMA456.BMA456_REG_INT2_IO_CTRL, data )
                if (ret == ErrorCode.errOk):
                    ret = err
        return ret;
    
    def disableInterrupt(self):
        """Disable interrupts.
        
        Switch off the interrupt functionality both, on the GPIO and the
        chip level.
        
        Note that this method is just for switching the interrupt capability
        off.
        For switching it on, see :meth:`.enableInterrupt`.
        
        Also see :meth:`.Interruptable.disableInterrupt`.
        
        :return: An error code indicating either success or the reason\
        of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if (not self.isAttached()):
            ret = ErrorCode.errResourceConflict
        else:
            ret = ErrorCode.errOk
            if not(self.pinInt1 is None):
                data = self.regInt1IOctrl & ~BMA456.BMA456_CNT_INT1_IO_CTRL_OUTPUT
                data |= BMA456.BMA456_CNT_INT1_IO_CTRL_OUTPUT_DISABLE
                ret = self.writeByteRegister( BMA456.BMA456_REG_INT1_IO_CTRL, data )
                ret = self.pinInt1.disableInterrupt()
            if not(self.pinInt2 is None):
                data = self.regInt2IOctrl & ~BMA456.BMA456_CNT_INT2_IO_CTRL_OUTPUT
                data |= BMA456.BMA456_CNT_INT2_IO_CTRL_OUTPUT_DISABLE
                err = self.writeByteRegister( BMA456.BMA456_REG_INT2_IO_CTRL, data )
                if (ret == ErrorCode.errOk):
                    ret = err
                ret = self.pinInt2.disableInterrupt()
        return ret;
 
 
    def getEventContext(self, event, context):
        """Retrieve more detailed information on an event.
        
        Typically, an original event notification just carries the
        information, that an event/interrupt occurred. This method is
        to reveal more details on the cause of the interrupt.
        
        The ``event`` parameter is an input to tell, which of the two
        interrupt lined actually fired.
        On return, the ``context`` parameter carries the resulting
        information. It must be an instance of :class:`.accelerometer.EventContext`,
        which is semantically multiplexed by its :attr:`.accelerometer.EventContext.source`
        attribute. Depending on that event source indicator, the rest of
        the structure is filled as follows: 
        
        =======================    ==========================================================================================
        Event source (flag)        Context attribute and data
        =======================    ==========================================================================================
        dataReady                  ``data`` latest measurement as retrieved by :meth:`getLatestData`
        fifoWatermark, fifoFull    ``status`` fifo status retrieved from :meth:`getStatus` and :attr:`StatusID.fifo`
        activity                   ``status`` activity status retrieved from :meth:`getStatus` and :attr:`StatusID.activity`
        step                       ``status`` step count retrieved from :meth:`getStatus` and :attr:`StatusID.stepCount`
        highGTime                  ``status`` high-G status retrieved from :meth:`getStatus` and :attr:`StatusID.highG`
        orientation                ``status`` orientation retrieved from :meth:`getStatus` and :attr:`StatusID.orientation`
        tap                        ``status`` :class:`Tap` instance depending on feature set and interrupt
        =======================    ==========================================================================================

        A single interrupt may have several reasons, simultaneously.
        That's why, it may be meaningful/necessary to call this method
        repeatedly, until all reasons were reported. Upon its first
        call after an event, the context's :attr:`.interruptable.EventContext.control`
        attribute must be set to :attr:`.interruptable.EventContextControl.evtCtxtCtrl_getFirst`.
        Upon subsequent calls, this attribute should not be changed by
        the caller, anymore. In generally, event context information is
        retrieved in the order according to the priority of the
        corresponding event sources.
        
        The return value indicates, whether or not more information is
        available as follows:
        
        ==============================    ======================================================
        Return value                      Meaning
        ==============================    ======================================================
        :attr:`.ErrorCode.errOk`          Success. Last context info. No more data to retrieve.
        :attr:`.ErrorCode.errMoreData`    Success. Context is valid. More data to be retrieved.
        :attr:`.ErrorCode.errFewData`     No data to retrieve. Context is invalid.
        any other ErrorCode.*             Error. Context data is invalid.
        ==============================    ======================================================
        
        Also see: :meth:`.Interruptable.getEventContext`.
        
        :param int event: The original event occurred, as received by the\
        handling routine. This must be one of the event mnemonics defined\
        by :class:``Event``.
        :param .accelerometer.EventContext context: Context information. 
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
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
                _, ret = self.readWordRegister( BMA456.BMA456_REG_INT_STATUS )
                context.remainInt = 0;
                context.source = EventSource.none
            else:
                if (context.control == EventContextControl.evtCtxtCtrl_getFirst):
                    data, ret = self.readWordRegister( BMA456.BMA456_REG_INT_STATUS )
                    context.remainInt = data
                    context.control = EventContextControl.evtCtxtCtrl_getNext
                elif (context.control == EventContextControl.evtCtxtCtrl_getLast):
                    data, ret = self.readWordRegister( BMA456.BMA456_REG_INT_STATUS )
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
        """Execute one or more sensor self tests.
        
        The test(s) to execute is given as a bit mask. This sensor
        supports the following tests:
        
        :attr:`.SelfTest.CONNECTION`: 
        An attempt is made to read the sensor's chip ID. If reading is
        successful, the result is compared to :attr:`.BMA456_CNT_CHIP_ID`.
        On a match, the method returns successfully. Otherwise, a failure
        is indicated.
        
        :attr:`.SelfTest.FUNCTIONAL`: 
        A functional sensor self test is executed as described in the
        data sheet, chapter 4.9.
        
        Also see: :meth:`.Sensor.selfTest`.

        :param int tests: A bit mask to select the tests to be executed.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
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
            config.type = ConfigItem.range
            config.value = BMA456.BMA456_SELFTEST_RANGE
            ret = self.configure( config )
            # Set self-test amplitude to low
            ret = self.writeByteRegister( BMA456.BMA456_REG_SELF_TST,
                                       BMA456.BMA456_CNT_SELF_TST_AMP_LOW | BMA456.BMA456_CNT_SELF_TST_DISABLE )
            # ODR=1600Hz, BWP=norm_avg4, performance mode (continuous)
            oldRate, ret = self.readByteRegister( BMA456.BMA456_REG_ACC_CONF )
            ret = self.writeByteRegister( BMA456.BMA456_REG_ACC_CONF,
                                        BMA456.BMA456_CNT_ACC_CONF_ODR_1K6 | BMA456.BMA456_CNT_ACC_CONF_MODE_NORM )
            # Wait for min. 2ms
            time.sleep( BMA456.BMA456_SELFTEST_DELAY_CONFIG / 1000000 )
            # Enable self-test and positive test polarity
            ret = self.writeByteRegister( BMA456.BMA456_REG_SELF_TST,
                                        BMA456.BMA456_CNT_SELF_TST_AMP_LOW | BMA456.BMA456_CNT_SELF_TST_SIGN_POS | BMA456.BMA456_CNT_SELF_TST_ENABLE )
            # Wait for min. 50ms
            time.sleep( BMA456.BMA456_SELFTEST_DELAY_MEASURE / 1000000 )
            # Read positive acceleration value
            posData, ret = self.getLatestData()
            # Enable self-test and negative test polarity
            ret = self.writeByteRegister( BMA456.BMA456_REG_SELF_TST,
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
            self.writeByteRegister( BMA456.BMA456_REG_SELF_TST,
                                    BMA456.BMA456_CNT_SELF_TST_AMP_LOW | BMA456.BMA456_CNT_SELF_TST_DISABLE )
            # Restore old configuration
            self.writeByteRegister( BMA456.BMA456_REG_ACC_CONF, oldRate )
            config.type = ConfigItem.range
            config.value = oldRange
            self.configure( config )
        return ret
    
    def reset(self):
        """Reset the sensor to its default state.
        
        After executing the reset command with the chip, it is re-configured
        using the start-up settings. Also, interrupt configuration is
        restored and interrupts are enabled.
        
        Also see: :meth:`.Sensor.reset`.

        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        # Known issue with BMA456: It does not ACK the soft reset command, when
        # the sensor is not in suspend mode. (Search for "BMA456 soft reset error"!)
        # Instead of suspending, we catch and ignore the exception thrown.
        ret = ErrorCode.errOk
        # Initiate the soft reset
        try:
            ret = self.writeByteRegister( BMA456.BMA456_REG_CMD, BMA456.BMA456_CNT_CMD_SOFTRESET )
        except OSError:
            pass
        # Wait for some time
        time.sleep( 5 / 1000 )   
        # Restore configuration
        if (ret == ErrorCode.errOk):
            ret = self._initialize()
            data = self.regInt1IOctrl & ~BMA456.BMA456_CNT_INT1_IO_CTRL_OUTPUT
            data |= BMA456.BMA456_CNT_INT1_IO_CTRL_OUTPUT_DISABLE
            self.writeByteRegister( BMA456.BMA456_REG_INT1_IO_CTRL, data )
            self.writeByteRegister( BMA456.BMA456_REG_INT1_MAP, self.regInt1Map )
            data = self.regInt2IOctrl & ~BMA456.BMA456_CNT_INT2_IO_CTRL_OUTPUT
            data |= BMA456.BMA456_CNT_INT2_IO_CTRL_OUTPUT_DISABLE
            self.writeByteRegister( BMA456.BMA456_REG_INT2_IO_CTRL, data )
            self.writeByteRegister( BMA456.BMA456_REG_INT2_MAP, self.regInt2Map )
            self.writeByteRegister( BMA456.BMA456_REG_INT_MAP_DATA, self.regIntMapData )
            self.enableInterrupt()
        return ret

    def configure(self, config):
        """Configure the device as specified in the ``config`` parameter.
        
        Remember, the ``config`` parameter should be an instance of
        :class:`.accelerometer.Configuration`. Its attributes are
        de-multiplexed by :attr:`.sensor.Configuration.type`.
        The following configuration types are supported:
        
        :attr:`.ConfigItem.rate`:
        The data rate given as an integer value in Hz is expected in
        :attr:`.Configuration.value`. If it doesn't match a supported
        rate value exactly, it is rounded up appropriately. So, the
        rate actually configured may be slightly higher than the value
        given here.
        Furthermore, the sampling mode must be specified in the
        :attr:`.Configuration.rateMode` attribute.
        The chip supports under-sampling (:attr:`.SamplingMode.average`),
        normal sampling and over-sampling (2x and 4x). For averaging mode,
        the number of samples to average must be given in
        :attr:`.Configuration.rateMode.mValue`.
         
        :attr:`.ConfigItem.range`:
        The :attr:`.Configuration.value` attribute is expected to carry
        the measurement range given as an integer in milli-g. If the
        given value doesn't match one of the hardware-supported range
        levels, exactly, it is rounded-up accordingly.
        
        :attr:`.ConfigItem.fifo`: Not yet implemented.
        
        :attr:`.ConfigItem.eventArm`: Selectively enables or disables
        certain event sources (interrupts). Remember that the following
        conditions must be fulfilled in order to get a specific interrupt
        fired:
        
        #. Interrupts must be enabled. See :meth:`.enableInterrupt`.
        #. That interrupt (event source) must be armed - using this method.
        #. The corresponding interrupt condition must be true.
        
        Note that the armed events are always configured to fire on both
        interrupt lines :attr:`.Event.evtInt1` and :attr:`.Event.evtInt2`.
        The bit mask of events to be armed is expected in
        :attr:`.accelerometer.Configuration.value` as an equivalent
        of :class:`.accelerometer.EventSource`. The translation between
        the given event source and the underlying hardware interrupt is
        as follows:
        
        =================    ==================================================
        Event source         Hardware interrupt mapping bit mask
        =================    ==================================================
        dataReady            INT_MAP_DATA: (INT1_DRDY | INT2_DRDY)
        fifoWatermark        INT_MAP_DATA: (INT1_FIFO_WM | INT2_FIFO_WM)
        fifoFull             INT_MAP_DATA: (INT1_FIFO_FULL | INT2_FIFO_FULL)
        error                INTX_MAP: ERROR
        lowSlopeTime         INTX_MAP: NO_MOTION
        highSlopeTime        INTX_MAP: ANY_MOTION
        gesture              INTX_MAP: WRIST_WKUP
        activity             INTX_MAP: ACTIVITY
        step                 INTX_MAP: STEP_CNT
        tap                  INTX_MAP: STAP (wearable), TAP (hearable, MM)
        significantMotion    INTX_MAP: SIG_MOTION
        highGTime            INTX_MAP: HIGH_G
        lowGTime             INTX_MAP: LOW_G
        orientation          INTX_MAP: ORIENT
        =================    ==================================================

        :attr:`.ConfigItem.eventCondition`:
        Configures the trigger condition for parameterized events, such
        as ``tap`` or ``lowGTime``. The details, such as thresholds and
        delays, are expected in the given ``config`` 's 
        :attr:`.accelerometer.Configuration.eventCondition` attribute,
        which is de-multiplexed by its
        :attr:`.accelerometer.Configuration.CfgInterrupt.event` attribute.
        
        Note that the event sources ``dataReady``, ``fifoWatermark``,
        ``fifoFull`` and ``error`` are not parameterized. They cannot
        be conditioned any further.
        
        The configuration of other event conditions is not implemented, yet.
        
        Also see: :meth:`.Sensor.configure`.

        :param .accelerometer.Configuration config: Specific configuration information.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
    
        if (config.type == ConfigItem.rate):
            # Construct ACC_CONF register content
            key, ret = self.dictRate.findKey( config.value )
            if (ret == ErrorCode.errOk):
                data = key
                if (isinstance( config, Configuration)):
                    if (config.rateMode.control == SamplingMode.average):
                        key, ret = self.dictAverage.findKey( config.rateMode.mValue )
                        data |= key
                    elif (config.rateMode.control == SamplingMode.normal):
                        data |= BMA456.BMA456_CNT_ACC_CONF_MODE_NORM
                    elif (config.rateMode.control == SamplingMode.OSR2):
                        data |= BMA456.BMA456_CNT_ACC_CONF_MODE_OSR2
                    elif (config.rateMode.control == SamplingMode.OSR4):
                        data |= BMA456.BMA456_CNT_ACC_CONF_MODE_OSR4
                    else:
                        ret = ErrorCode.errNotSupported
                else:
                    data |= BMA456.BMA456_CNT_ACC_CONF_MODE_NORM
            if (ret == ErrorCode.errOk):
                ret = self.writeByteRegister( BMA456.BMA456_REG_ACC_CONF, data )
                if (ret == ErrorCode.errOk):
                    self.dataRate, _ = self.dictRate.getValue(key)
                    # Check, if configuration is ok
                    data, ret = self.readByteRegister( BMA456.BMA456_REG_ERROR )
                    if ((data & BMA456.BMA456_CNT_ERROR_CODE) == BMA456.BMA456_CNT_ERROR_CODE_ACC):
                        ret = ErrorCode.errSpecRange
        elif (config.type == ConfigItem.range):
            # Construct ACC_RANGE register content
            key, ret = self.dictRange.findKey( config.value )
            if (ret == ErrorCode.errOk):
                data = key
                ret = self.writeByteRegister( BMA456.BMA456_REG_ACC_RANGE, data )
            if (ret == ErrorCode.errOk):
                value, ret = self.dictRange.getValue(key)
            if (ret == ErrorCode.errOk):
                self.dataRange = value
        elif (config.type == ConfigItem.fifo):
            ret = ErrorCode.errNotImplemented
        elif (config.type == ConfigItem.eventArm):
            # Translate accel_EventSource_t into INTxMAP and INT_MAT_DATA bit masks
            remainEvt, dataMap, featureMap = self._accelEvtSrc2bmaMap( config.value )
            if (remainEvt != EventSource.none):
                ret = ErrorCode.errNotSupported
            else:
                ret = self.writeByteRegister( BMA456.BMA456_REG_INT_MAP_DATA, dataMap )
            if (ret == ErrorCode.errOk):
                ret = self.writeByteRegister( BMA456.BMA456_REG_INT1_MAP, featureMap )
            if (ret == ErrorCode.errOk):
                ret = self.writeByteRegister( BMA456.BMA456_REG_INT2_MAP, featureMap )
        elif (config.type == ConfigItem.eventCondition):
            if (config.eventCondition.event in [EventSource.dataReady, EventSource.fifoWatermark,
                                                        EventSource.fifoFull, EventSource.error]):
                # Nothing to condition, already done.
                ret = ErrorCode.errOk
            elif (config.eventCondition.event in [EventSource.lowGTime, EventSource.highGTime,
                                                          EventSource.lowSlopeTime, EventSource.highSlopeTime,
                                                          EventSource.significantMotion, EventSource.tap,
                                                          EventSource.step, EventSource.gesture,
                                                          EventSource.activity, EventSource.lyingFlat,
                                                          EventSource.orientation]):
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

    def calibrate(self, calib):
        """Execute a calibration.
        
        The details for the calibration are given by the ``calib``
        parameter.
        
        Also see: :meth:`.Sensor.calibrate`, :class:`.Calibration`.

        :param Calibration calib: The calibration data.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if (calib.type == CalibrationType.default):
            ret = ErrorCode.errNotImplemented
        elif (calib.type == CalibrationType.trueValue):
            ret = ErrorCode.errNotImplemented
        else:
            ret = ErrorCode.errNotSupported
        return ret

    def getInfo(self):
        """Retrieve static information from the sensor chip.
        
        Supported information is
        :attr:`.Info.validModelID` and :attr:`.Info.validChipID`.
        
        Also see: :meth:`.Sensor.getInfo`.

        :return: The information object and an error code indicating either success or the reason of failure.
        :rtype: Info, ErrorCode
        """
        info = Info()
        
        # Model ID
        info.modelID = self._getFeatureWordAt( BMA456.BMA456_FSWBL_IDX_GENERAL_CONFIG_ID )
        info.validity |= Info.validModelID
        # Chip ID
        info.chipID, ret = self.readByteRegister( BMA456.BMA456_REG_CHIP_ID )
        info.validity |= Info.validChipID
        return info, ret

    def getStatus(self, statID):
        """Retrieve dynamic meta information from the sensor chip.
        
        The information requested is indicated by the parameter ``statID``. 
        The resulting status information is passed back as a part of the
        return value. The following information is available:
        
        :attr:`.accelerometer.StatusID.dieTemp`:
        The chip temperature as read from the register :attr:`.BMA456_REG_TEMPERATURE`
        is returned as an Q8.8 integer given in degree Celsius.
        
        :attr:`.accelerometer.StatusID.dataReady`:
        Returns a boolean to flag whether or not new data is available.
        For that, evaluates the ``DRDY_ACC`` bit in :attr:`.BMA456_REG_STATUS`
        
        :attr:`.accelerometer.StatusID.interrupt`:
        Give the pending interrupts by reading :attr:`.BMA456_REG_INT_STATUS`.
        This information is cleared until interrupt conditions are
        fulfilled anew.
        The result is given as an :class:`.acceleroometer.EventSource`
        bit mask. The mapping of hardware interrupt bits to event source
        flags is as follows:
        
        ===============  ==============
        Interrupt (Bit)  EventSource
        ===============  ==============
        ACC_DRDY         dataReady
        ACTIVITY         activity
        ANY_MOTION       highSlopeTime
        AUX_DRDY         none
        DBL_TAP          tap
        ERROR            error
        FIFO_FULL        fifoFull
        FIFO_WM          fifoWatermark
        HIGH_G           highGTime
        LOW_G            lowGTime
        NO_MOTION        lowSlopeTime
        ORIENT           orientation
        SIG_MOTION       significantMotion
        STEP_COUNT       step
        TAP_DETECT       tap
        WRIST_WKUP       gesture
        ===============  ==============
        
        :attr:`.accelerometer.StatusID.fifo`:
        Retrieve the FIFO length by reading :attr:`.BMA456_REG_FIFO_LENGTH`.
        The result is returned as an integer value.
        
        :attr:`.accelerometer.StatusID.error`:
        Gives the sensor health code as a 32-bit integer value, obtained
        by just concatenating the content of the registers
        :attr:`.BMA456_REG_INTERNAL_ERR`:
        :attr:`.BMA456_REG_INTERNAL_STATUS`:
        :attr:`.BMA456_REG_EVENT`:
        :attr:`.BMA456_REG_ERROR` in that order.
        
        :attr:`.accelerometer.StatusID.activity`:
        For the wearable and hearable feature set, read the current activity
        from the :attr:`.BMA456_FSWBL_REG_ACTIVITY_TYPE` register and
        return the result as an instance of :class:`.Activity`. Indicate
        a failure if another feature set is active. 
         
        :attr:`.accelerometer.StatusID.stepCount`:
        For the wearable and hearable feature set, return the current
        step count as read from the register
        :attr:`.BMA456_FSWBL_REG_STEP_COUNTER`. The result is given as
        a 32 bit integer number.
        
        :attr:`.accelerometer.StatusID.highG`:
        For the MM feature set, retrieve the axis information for a
        high-G event from the :attr:`.BMA456_FSMM_REG_HIGH_G_OUTPUT`
        register. The result is passed back as an :class:`.AxesSign` bit
        mask.
        
        :attr:`.accelerometer.StatusID.orientation`:
        For the MM feature set, retrieve the current orientation of the
        device as read from the :attr:`.BMA456_FSMM_REG_ORIENT_OUTPUT`
        register. The result is given as an :class:`.Orientation` bit
        mask.
        
        :attr:`.accelerometer.StatusID.tap`:
        For the hearable and MM feature set, give the type of the recently
        detected tap (single, double etc.) as a :class:`.Tap` bit mask
        after reading that information from the
        :attr:`.BMA456_FSHBL_REG_FEAT_OUT` and
        :attr:`.BMA456_FSMM_REG_MULTITAP_OUTPUT` registers, respectively.
        For the wearable feature set, there are dedicated interrupts for
        this information, which get cleared upon reading. That's why,
        :meth:`.getEventContext` should be intentionally used by the
        caller to retrieve this information.
        
         
        :attr:`.accelerometer.StatusID.sensorTime`:
        Retrieve the current sensor time in milli-seconds [ms]. The
        result is given as a Q24.8 integer value.
        
        Also see: :meth:`.Sensor.getStatus`.

        :param accelerometer.StatusID statID: Identifies the status information to be retrieved.
        :return: The status object and an error code indicating either success or the reason of failure.
        :rtype: Object, ErrorCode
        """
        ret = ErrorCode.errOk
        status = 0
    
        if (statID == StatusID.dieTemp):
            # Temperature in degree Celsius as Q8.8
            data, ret = self.readByteRegister( BMA456.BMA456_REG_TEMPERATURE )
            if (ret == ErrorCode.errOk):
                # sign-extend data
                if (data > 0x7F):
                    data = data - 0x100
                status = (data + BMA456.BMA456_TEMPERATURE_SHIFT) << 8
        elif (statID == StatusID.dataReady):
            # Just 0 or 1 to indicate if new data is ready
            data, ret = self.readByteRegister( BMA456.BMA456_REG_STATUS )
            if (ret == ErrorCode.errOk):
                status = ((data & BMA456.BMA456_CNT_STATUS_DRDY_ACC) != 0)
        elif (statID == StatusID.interrupt):
            # EventSource mask
            data, ret = self.readWordRegister( BMA456.BMA456_REG_INT_STATUS )
            if (ret == ErrorCode.errOk):
                status = self._bmaInt2accelEvtSrc( data )
        elif (statID == StatusID.fifo):
            # Number of elements in FIFO
            data, ret = self.readWordRegister( BMA456.BMA456_REG_FIFO_LENGTH )
            if (ret == ErrorCode.errOk):
                status = data
        elif (statID == StatusID.error):
            # Implementation-specific error/health code
            status = 0
            # Copy INTERNAL_ERROR 0x5F (int_err_2, int_err_1)
            if (ret == ErrorCode.errOk):
                data, ret = self.readByteRegister( BMA456.BMA456_REG_INTERNAL_ERR )
                status = (status << 8) | data
            # Copy INTERNAL_STATUS 0x2A (odr_high_error, odr_50hz_error, axes_remap_error, message)
            if (ret == ErrorCode.errOk):
                data, ret = self.readByteRegister( BMA456.BMA456_REG_INTERNAL_STATUS )
                status = (status << 8) | data
            # Copy EVENT 0x1B (por_detected)
            if (ret == ErrorCode.errOk):
                data, ret = self.readByteRegister( BMA456.BMA456_REG_EVENT )
                status = (status << 8) | data
            # Copy ERR_REG 0x02 (aux_err, fifo_err, error_code, cmd_err, fatal_err)
            if (ret == ErrorCode.errOk):
                data, ret = self.readByteRegister( BMA456.BMA456_REG_ERROR )
                status = (status << 8) | data
        elif (statID == StatusID.activity):
            # Activity
            if (self.featureSet in [BMA456.BMA456_FEATURE_SET_WEARABLE, BMA456.BMA456_FEATURE_SET_HEARABLE]):
                data, ret = self.readByteRegister( BMA456.BMA456_FSWBL_REG_ACTIVITY_TYPE )
                if (ret == ErrorCode.errOk):
                    if ((data & BMA456.BMA456_FSWBL_CNT_ACTIVITY_TYPE) == BMA456.BMA456_FSWBL_CNT_ACTIVITY_TYPE_UNKNOWN):
                        status = Activity.unknown
                    elif ((data & BMA456.BMA456_FSWBL_CNT_ACTIVITY_TYPE) == BMA456.BMA456_FSWBL_CNT_ACTIVITY_TYPE_STILL):
                        status = Activity.still
                    elif ((data & BMA456.BMA456_FSWBL_CNT_ACTIVITY_TYPE) == BMA456.BMA456_FSWBL_CNT_ACTIVITY_TYPE_WALK):
                        status = Activity.walking
                    elif ((data & BMA456.BMA456_FSWBL_CNT_ACTIVITY_TYPE) == BMA456.BMA456_FSWBL_CNT_ACTIVITY_TYPE_RUN):
                        status = Activity.running
                    else:
                        ret = ErrorCode.errCorruptData
            else:
                ret = ErrorCode.errNotSupported
        elif (statID == StatusID.stepCount):
            # Step count
            if (self.featureSet in [BMA456.BMA456_FEATURE_SET_WEARABLE, BMA456.BMA456_FEATURE_SET_HEARABLE]):
                status, ret = self.readDWordRegister( BMA456.BMA456_FSWBL_REG_STEP_COUNTER )
            else:
                ret = ErrorCode.errNotSupported
        elif (statID == StatusID.highG):
            # AxesSign
            if (self.featureSet == BMA456.BMA456_FEATURE_SET_MM):
                data, ret = self.readByteRegister( BMA456.BMA456_FSMM_REG_HIGH_G_OUTPUT )
                if (ret == ErrorCode.errOk):
                    status = AxesSign.none
                    if (data & BMA456.BMA456_FSMM_CNT_HIGH_G_OUTPUT_AXES_X ):
                        status |= AxesSign.x
                    if (data & BMA456.BMA456_FSMM_CNT_HIGH_G_OUTPUT_AXES_Y ):
                        status |= AxesSign.y
                    if (data & BMA456.BMA456_FSMM_CNT_HIGH_G_OUTPUT_AXES_Z ):
                        status |= AxesSign.z
                    if ((data & BMA456.BMA456_FSMM_CNT_HIGH_G_OUTPUT_SIGN) == BMA456.BMA456_FSMM_CNT_HIGH_G_OUTPUT_SIGN_POS ):
                        status |= AxesSign.signPos
                    else:
                        status |= AxesSign.signNeg
            else:
                ret = ErrorCode.errNotSupported
        elif (statID == StatusID.orientation):
            # accel_Orientation_t mask
            if (self.featureSet == BMA456.BMA456_FEATURE_SET_MM):
                data, ret = self.readByteRegister( BMA456.BMA456_FSMM_REG_ORIENT_OUTPUT )
                if (ret == ErrorCode.errOk):
                    if ((data & BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_STAND) == BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_STAND_PORT_UP):
                        status = Orientation.portraitUp
                    elif ((data & BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_STAND) == BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_STAND_PORT_DOWNUP):
                        status = Orientation.portraitDown
                    elif ((data & BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_STAND) == BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_STAND_LAND_LEFT):
                        status = Orientation.landscapeLeft
                    elif ((data & BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_STAND) == BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_STAND_LAND_RIGHT):
                        status = Orientation.landscapeRight
                    else:
                        # Should never reach here.
                        status = Orientation.portraitUp
                    # face up/down info
                    if ((data & BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_FACE) == BMA456.BMA456_FSMM_CNT_ORIENT_OUTPUT_FACE_UP):
                        status |= Orientation.faceUp
                    else:
                        status |= Orientation.faceDown
                    status |= Orientation.invalidTilt
            else:
                ret = ErrorCode.errNotSupported
        elif (statID == StatusID.tap):
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
                status = Tap.none
            elif (self.featureSet == BMA456.BMA456_FEATURE_SET_HEARABLE):
                data, ret = self.readByteRegister( BMA456.BMA456_FSHBL_REG_FEAT_OUT )
                if (ret == ErrorCode.errOk):
                    status = Tap.none
                    if (data & BMA456.BMA456_FSHBL_CNT_FEAT_OUT_STAP):
                        status |= Tap.single
                    if (data & BMA456.BMA456_FSHBL_CNT_FEAT_OUT_DTAP):
                        status |= Tap.double
                    if (data & BMA456.BMA456_FSHBL_CNT_FEAT_OUT_TTAP):
                        status |= Tap.triple
            elif (self.featureSet == BMA456.BMA456_FEATURE_SET_MM):
                data, ret = self.readByteRegister( BMA456.BMA456_FSMM_REG_MULTITAP_OUTPUT )
                if (ret == ErrorCode.errOk):
                    status = Tap.none
                    if (data & BMA456.BMA456_FSMM_CNT_MULTITAP_OUTPUT_STAP):
                        status |= Tap.single
                    if (data & BMA456.BMA456_FSMM_CNT_MULTITAP_OUTPUT_DTAP):
                        status |= Tap.double
                    if (data & BMA456.BMA456_FSMM_CNT_MULTITAP_OUTPUT_TTAP):
                        status |= Tap.triple
            else:
                ret = ErrorCode.errNotSupported
        elif (statID == StatusID.sensorTime):
            # Sensor time in ms as an unsigned Q24.8
            status, ret = self.readDWordRegister( BMA456.BMA456_REG_SENSOR_TIME )
            if (ret == ErrorCode.errOk):
                # Result's LSB is 625/16 = 39.0625 us (microseconds).
                # So we look for result * 625/16 * 256/1000 = result * 10.
                status = status * 10
        else:
            ret = ErrorCode.errNotSupported
        return status, ret


    def getLatestData(self):
        """Retrieve the most-recent available measurement data.
        
        This method is guaranteed to be non-blocking. Therefore, the
        data retrieved might be /old/ or /outdated/ to some extend.
        
        The result is given as a 3x1 list of signed integers,
        representing the acceleration in milli-G in the x, y and z
        direction, respectively.
        
        Also see: :meth:`.Sensor.getLatestData`.

        :return: The measurement data list and an error code indicating\
        either success or the reason of failure.
        :rtype: List(int), ErrorCode
        """
        buf, ret = self.readBufferRegister( BMA456.BMA456_REG_ACC_X, 6 )
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
        """Get the next-available measurement data.
        
        This method is guaranteed to produce up-to-date measurement
        data. This may come at the price of a blocking delay.
        
        As with :meth:`getLatestData`, the result is given as a list
        of integers representing the acceleration in x, y and z direction
        in milli-G.
        
        Also see: :meth:`.Sensor.getNextData`.

        :return: The measurement data list and an error code indicating\
        either success or the reason of failure.
        :rtype: List(int), ErrorCode
        """
        done = False
        while( not done ):
            stat, err = self.getStatus( StatusID.dataReady )
            done = (stat != 0) or (err != ErrorCode.errOk)
        if (err == ErrorCode.errOk):
            data, err = self.getLatestData()
        else:
            data = None
        return data, err


