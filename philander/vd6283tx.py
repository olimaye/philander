"""Driver implementation for the VD6283TX ambient light sensor by ST micro.

More information on the functionality of the chip can be found at
the ST site:
https://www.st.com/en/imaging-and-photonics-solutions/vd6283tx.html
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["VD6283TX"]

import logging

from .configurable import ConfigItem, Configuration
from .dictionary import Dictionary
from .gpio import GPIO
from .penum import dataclass
from .sensor import SelfTest, Sensor
from .serialbus import SerialBusDevice, SerialBus, SerialBusType
from .systypes import ErrorCode, Info, RunLevel

class VD6283TX(Sensor, SerialBusDevice):
    """VD6283TX driver implementation.
    
    This sensor is a matrix of 5x5 photo diodes providing six different
    light channels as follows:
    - Red. 3 diodes, 550...700nm, peak 610nm
    - Green. 5 diodes, 420...650nm, peak 550nm
    - Blue. 3 diodes, 380...550nm, peak 460nm
    - IR. 4 diodes, 600...1000nm, peak 850 nm
    - Visible. 3 diodes, 370...700nm, peak 540nm
    - Clear. 5 diodes, 350...1050nm, peak 550-680nm
    - Dark. 2 blind diodes, only internal channel.
    """

    MODULE_PARAM_PREFIX = "light"

    ADDRESSES_ALLOWED = [0x20]
    """The only address is 0x20.
    """
    
    #
    # Hardware register definitions.
    #
    REG_DEVICE_ID       = 0x00
    DEVICE_ID           = 0x70
    
    REG_REVISION_ID     = 0x01
    REVISION_ID_2_2     = 0xBC
    REVISION_ID_2_3     = 0xBD

    REG_INTERRUPT_CTRL  = 0x02
    INTR_ST             = 0x02
    CLR_INTR            = 0x01
    
    REG_ALS_CTRL        = 0x03
    ALS_MODE_SINGLE     = 0x00
    ALS_MODE_CONT       = 0x06
    ALS_EN              = 0x01
    
    REG_ALS_PERIOD      = 0x04  # Periods of 20.5 ms (=LSB)

    REG_ALS_CHX_DATA    = 0x06
    # REG_ALS_CH1_DATA_H  = 0x06
    # REG_ALS_CH1_DATA_M  = 0x07
    # REG_ALS_CH1_DATA_L  = 0x08
    # REG_ALS_CH2_DATA_H  = 0x0A
    # REG_ALS_CH2_DATA_M  = 0x0B
    # REG_ALS_CH2_DATA_L  = 0x0C
    # REG_ALS_CH3_DATA_H  = 0x0E
    # REG_ALS_CH3_DATA_M  = 0x0F
    # REG_ALS_CH3_DATA_L  = 0x10
    # REG_ALS_CH4_DATA_H  = 0x12
    # REG_ALS_CH4_DATA_M  = 0x13
    # REG_ALS_CH4_DATA_L  = 0x14
    # REG_ALS_CH5_DATA_H  = 0x16
    # REG_ALS_CH5_DATA_M  = 0x17
    # REG_ALS_CH5_DATA_L  = 0x18
    # REG_ALS_CH6_DATA_H  = 0x1A
    # REG_ALS_CH6_DATA_M  = 0x1B
    # REG_ALS_CH6_DATA_L  = 0x1C
    
    REG_ALS_EXPOSURE    = 0x1D
    # REG_ALS_EXPOSURE_M  = 0x1D
    # REG_ALS_EXPOSURE_L  = 0x1E
    # EXPOSURE_DEFAULT    = 0x0032    # Intervals of 1.6 ms 
    
    REG_ALS_GAIN_CHX    = 0x25
    # REG_ALS_GAIN_CH1    = 0x25
    # REG_ALS_GAIN_CH2    = 0x26
    # REG_ALS_GAIN_CH3    = 0x27
    # REG_ALS_GAIN_CH4    = 0x28
    # REG_ALS_GAIN_CH5    = 0x29
    # REG_ALS_GAIN_CH6    = 0x2A
    # ALS_GAIN_66p6   = 0x01
    # ALS_GAIN_50     = 0x02
    # ALS_GAIN_33     = 0x03
    # ALS_GAIN_25     = 0x04
    # ALS_GAIN_16     = 0x05
    # ALS_GAIN_10     = 0x06
    # ALS_GAIN_7p1    = 0x07
    # ALS_GAIN_5      = 0x08
    # ALS_GAIN_3p33   = 0x09
    # ALS_GAIN_2p5    = 0x0A
    # ALS_GAIN_1p67   = 0x0B
    # ALS_GAIN_1p25   = 0x0C
    # ALS_GAIN_1      = 0x0D
    # ALS_GAIN_0p83   = 0x0E
    # ALS_GAIN_0p71   = 0x0F
    
    REG_CHANNEL6_ENABLE = 0x2D
    CH6_EN          = 0x01

    REG_ALS_CHANNEL_ENABLE = 0x2E
    ALS_CH_EN_NONE  = 0x00
    ALS_CH_EN_1     = 0x01
    ALS_CH_EN_2     = 0x02
    ALS_CH_EN_3     = 0x04
    ALS_CH_EN_4     = 0x08
    ALS_CH_EN_5     = 0x10
    ALS_CH_EN_ALL   = 0x1F

    REG_AC_MODE_CTRL    = 0x31
    PEDESTAL_DIS    = 0x40
    AC_OUT_SEL      = 0x10
    AC_CH_SEL_NONE  = 0x00
    AC_CH_SEL_1     = 0x04
    AC_CH_SEL_2     = 0x06
    AC_CH_SEL_3     = 0x08
    AC_CH_SEL_4     = 0x0A
    AC_CH_SEL_5     = 0x0C
    AC_CH_SEL_6     = 0x02
    AC_FREQEXT_EN   = 0x01

    REG_PEDESTAL_VALUE  = 0x32
    PEDESTAL_DEFAULT= 0x05
    
    REG_SDA_DRV_CFG     = 0x3C
    SDA_LOAD        = 0x08
    SDA_DRV         = 0x07
    SDA_DRV_LOWEST  = 0x00
    SDA_DRV_DEFAULT = 0x01
    SDA_DRV_HIGHEST = 0x04
    
    REG_GPIO1_DRV_CFG   = 0x41
    GPIO1_CFG_OD    = 0x00  # Open drain
    GPIO1_CFG_PUSH_PULL = 0x01  # Push-pull
    GPIO1_CFG_ANALOGUE  = 0x02  # Analog output via 200 Ohm series resistor
    GPIO1_CFG_DEFAULT   = 0x00

    CHANNEL_NUM         = 6
    CHANNEL_NONE        = 0
    CHANNEL_IDX_1_RED   = 1
    CHANNEL_IDX_2_VISIBLE   = 2
    CHANNEL_IDX_3_BLUE  = 3
    CHANNEL_IDX_4_GREEN = 4
    CHANNEL_IDX_5_IR    = 5
    CHANNEL_IDX_6_CLEAR = 6
    
    CHANNEL_NAME = ["0-unassigned",
                    "red", "visible", "blue", "green", "ir", "clear"]
    CHANNEL_IDX = {
        CHANNEL_NAME[CHANNEL_IDX_1_RED]:        CHANNEL_IDX_1_RED,
        CHANNEL_NAME[CHANNEL_IDX_2_VISIBLE]:    CHANNEL_IDX_2_VISIBLE,
        CHANNEL_NAME[CHANNEL_IDX_3_BLUE]:       CHANNEL_IDX_3_BLUE,
        CHANNEL_NAME[CHANNEL_IDX_4_GREEN]:      CHANNEL_IDX_4_GREEN,
        CHANNEL_NAME[CHANNEL_IDX_5_IR]:         CHANNEL_IDX_5_IR,
        CHANNEL_NAME[CHANNEL_IDX_6_CLEAR]:      CHANNEL_IDX_6_CLEAR,
        }
    
    @dataclass
    class Channel():
        """Data structure to represent internal details of a channel.
        """
        index:          int
        sensitivity:    float # Scaling factor for mapping into intensity [uW/cm^2] 
        maskAlsEnable:  int
        maskAcModeCtrl: int
        isEnabled:      bool = False
        hasFlicker:     bool = False

    #
    # Internal helpers
    #
    def _syncShadows(self):
        data, ret = self.readByteRegister(VD6283TX.REG_ALS_CTRL)
        logging.debug("VD6283TX._syncShadows> read REG_ALS_CTRL: data=x%02x, err=%s.", data, ret)
        if ret.isOk():
            self._shadowAlsCtrl = data
            data, ret = self.readByteRegister(VD6283TX.REG_CHANNEL6_ENABLE)
            logging.debug("VD6283TX._syncShadows> read REG_CHANNEL6_ENABLE: data=x%02x, err=%s.", data, ret)
        if ret.isOk():
            for ch in self._channel:
                if ch.index == 6:
                    ch.isEnabled = ch.maskAlsEnable & data
            data, ret = self.readByteRegister(VD6283TX.REG_ALS_CHANNEL_ENABLE)
            logging.debug("VD6283TX._syncShadows> read REG_ALS_CHANNEL_ENABLE: data=x%02x, err=%s.", data, ret)
        if ret.isOk():
            for ch in self._channel:
                if ch.index != 6:
                    ch.isEnabled = ch.maskAlsEnable & data
            data, ret = self.readByteRegister(VD6283TX.REG_AC_MODE_CTRL)
            logging.debug("VD6283TX._syncShadows> read REG_AC_MODE_CTRL: data=x%02x, err=%s.", data, ret)
        if ret.isOk():
            self._shadowAcModeCtrl = data
            for ch in self._channel:
                ch.hasFlicker = ((data & 0x0E) == ch.maskAcModeCtrl)
        return ret
    
    def _setGain(self, value, register):
        gainDict  = Dictionary( {15:0.71, 14:0.83, 13:1, 
                                 12:1.25, 11:1.67, 10:2.5, 9:3.33, 
                                 8:5, 7:7.1, 6:10, 5:16, 
                                 4:25, 3:33, 2:50, 1:66.6 } )
        ret = ErrorCode.errOk
        data = None
        if (value is not None) and isinstance(value, (int, float)):
            data, ret = gainDict.findKey( value )
            if ret.isOk():
                ret = self.writeByteRegister( register, data )
        logging.debug("VD6283TX._setGain> write register x%02x: %s, value=%s, data=%s",
                      register, ret, value, data)
        return ret
    
    def _transferToIntensity( self, adcCounts, channel ):
        """Translate digital measurement value into intensity.
        
        :param int adcCounts: 24bit digital register reading
        :param Channel channel: The channel for which to compute the intensity. 
        :returns: The corresponding intensity value in uW/cm^2 as int \
        and an error code to indicate success or the reason of failure.
        :rtype: int, ErrorCode
        """
        err = ErrorCode.errOk
        if channel is None:
            ret = 0
            err = ErrorCode.errInvalidParameter
        else:
            ret = adcCounts * channel.sensitivity
            err = ErrorCode.errOk
        return ret, err


    def __init__(self):
        # Create instance attributes
        self.pinInt = None
        # Shadow / copies of register contents
        self._shadowAlsCtrl = 0     # copy of REG_ALS_CTRL
        self._shadowAcModeCtrl = 0  # copy of REG_AC_MODE_CTRL
        self._channel = [ None,     # Fake for index=0
            VD6283TX.Channel( index=1, sensitivity=14.6,
                              maskAlsEnable=VD6283TX.ALS_CH_EN_1,
                              maskAcModeCtrl=VD6283TX.AC_CH_SEL_1 ),
            VD6283TX.Channel( index=2, sensitivity=49.7,
                              maskAlsEnable=VD6283TX.ALS_CH_EN_2,
                              maskAcModeCtrl=VD6283TX.AC_CH_SEL_2 ),
            VD6283TX.Channel( index=3, sensitivity=14.6,
                              maskAlsEnable=VD6283TX.ALS_CH_EN_3,
                              maskAcModeCtrl=VD6283TX.AC_CH_SEL_3 ),
            VD6283TX.Channel( index=4, sensitivity=29.5,
                              maskAlsEnable=VD6283TX.ALS_CH_EN_4,
                              maskAcModeCtrl=VD6283TX.AC_CH_SEL_4 ),
            VD6283TX.Channel( index=5, sensitivity=86.0,
                              maskAlsEnable=VD6283TX.ALS_CH_EN_5,
                              maskAcModeCtrl=VD6283TX.AC_CH_SEL_5 ),
            VD6283TX.Channel( index=6, sensitivity=62.3,
                              maskAlsEnable=VD6283TX.CH6_EN,
                              maskAcModeCtrl=VD6283TX.AC_CH_SEL_6 ),
            ]
        Sensor.__init__(self)
        SerialBusDevice.__init__(self)


    #
    # Module API
    #
 
    @classmethod
    def Params_init( cls, paramDict ):
        """Initializes parameters to their default values.
        The following settings are supported:
        
        =====================================    ==================================================================================================================
        Key name                                 Value type, meaning and default
        =====================================    ==================================================================================================================
        light.SerialBusDevice.address            ``int`` I2C serial device address, one of :attr:`ADDRESSES_ALLOWED`; default is :attr:`ADDRESSES_ALLOWED` ``[0]``.
        light.SerialBus.*                        optional: serial bus configuration; See :meth:`serialbus.SerialBus.Params_init`.
        light.SerialBusDevice.*                  serial bus configuration; See :meth:`serialbus.SerialBusDevice.Params_init`.
        light.int.gpio.*                         GPIO1 pin configuration; See :meth:`.GPIO.Params_init`.
        light.int.cfg                            GPIO1 Interrupt pin configuration, VD6283TX.GPIO1_CFG_[OD | PUSH_PULL | ANALOGUE]
        light.sda.highcap                        SDA line capacitive load > 95pF, bool [True | False]
        light.sda.drv                            SDA current drive strength, low to high, int [1, ..., 5]
        light.Sensor.exposure                    Exposure time in [2, ..., 1638] milliseconds
        light.Sensor.interval                    Inter-measurement period in [0, ..., 5237] milliseconds. Only valid for continuous mode!
        light.Sensor.mode                        VD6283TX.ALS_MODE_[SINGLE | CONT], single-shot or continuous measurement+handshake mode. 
        light.Sensor.red.enable                  Enable the Red channel measurements. bool [True | False]
        light.Sensor.red.gain                    Red channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.green.enable                Enable the Green channel measurements. bool [True | False]
        light.Sensor.green.gain                  Green channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.blue.enable                 Enable the Blue channel measurements. bool [True | False]
        light.Sensor.blue.gain                   Blue channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.ir.enable                   Enable the IR channel measurements. bool [True | False]
        light.Sensor.ir.gain                     IR channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.visible.enable              Enable the Visible light channel measurements. bool [True | False]
        light.Sensor.visible.gain                Visible channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.clear.enable                Enable the Clear un-filtered light channel measurements. bool [True | False]
        light.Sensor.clear.gain                  Clear channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.flicker.bias.enable         Enable/Disable pedestal value feature, bool [True | False].
        light.Sensor.flicker.bias.value          Pedestal value for flicker output, int [0...7].
        light.Sensor.flicker.channel             Flicker operation channel; VD6283TX.CHANNEL_[NONE | FIRST | IDX_[RED | GREEN | BLUE | IR | VISIBLE | CLEAR]]
        light.Sensor.flicker.enable              Enable the frequency extraction feature. bool [True | False]
        light.Sensor.flicker.outport             GPIO output port for the flicker PDM signal; int [1 | 2]
        ===========================================================================================================================================================
        
        Also see: :meth:`.SerialBusDevice.Params_init`. 
        
        :param dict(str, object) paramDict: Dictionary mapping option\
        names to their respective values.
        :returns: none
        :rtype: None
        """
        prefix = cls.MODULE_PARAM_PREFIX + "."

        # Setup defaults
        defaults = {
            "light.SerialBusDevice.address": cls.ADDRESSES_ALLOWED[0],
            "light.int.gpio.direction":         GPIO.DIRECTION_IN,
            "light.int.cfg":                    VD6283TX.GPIO1_CFG_OD,
            "light.sda.highcap":                True, 
            "light.sda.drv":                    2,
            "light.Sensor.exposure":            80,
            "light.Sensor.interval":            700,
            "light.Sensor.mode":                VD6283TX.ALS_MODE_SINGLE,
            "light.Sensor.red.enable":          True,
            "light.Sensor.red.gain":            1,
            "light.Sensor.green.enable":        True,
            "light.Sensor.green.gain":          1,
            "light.Sensor.blue.enable":         True,
            "light.Sensor.blue.gain":           1,
            "light.Sensor.ir.enable":           True,
            "light.Sensor.ir.gain":             1,
            "light.Sensor.visible.enable":      True,
            "light.Sensor.visible.gain":        1,
            "light.Sensor.clear.enable":        True,
            "light.Sensor.clear.gain":          1,
            "light.Sensor.flicker.bias.enable": True,
            "light.Sensor.flicker.bias.value":  3,
            "light.Sensor.flicker.channel":     2,
            "light.Sensor.flicker.enable":      True,
            "light.Sensor.flicker.outport":     2
        }
        # Add defaults to paramDict
        cls._aggregateParams( paramDict, defaults )
        
        localParams = cls._extractParams( paramDict, prefix)
        SerialBus.Params_init(localParams)
        SerialBusDevice.Params_init(localParams)
        Sensor.Params_init(localParams)
        gpioParams = cls._extractParams( localParams, prefix+"int.")
        GPIO.Params_init( gpioParams )
        cls._aggregateParams( paramDict, localParams, prefix )
        cls._aggregateParams( paramDict, gpioParams, prefix+"int." )
        return None


    def open(self, paramDict):
        ret = ErrorCode.errOk
        self.Params_init(paramDict)
        localParams = self._extractParams( paramDict, self.MODULE_PARAM_PREFIX + ".")
        logging.debug("VD6283TX.open> Params: %s.", localParams)
        # Open serial connection
        if ret.isOk():
            ret = SerialBusDevice.open(self, localParams)
            logging.debug("VD6283TX.open> SerialBusDevice.open: %s.", ret)
        # Open GPIO(1) pin
        if ret.isOk():
            self.pinInt = GPIO.getGPIO()
            gpioParams = self._extractParams( localParams, "int.")
            ret = self.pinInt.open( gpioParams )
            logging.debug("VD6283TX.open> GPIO.open: %s.", ret)
        # Execute simple self-test
        if ret.isOk():
            ret = self.selfTest( SelfTest.CONNECTION )
            logging.debug("VD6283TX.open> selfTest: %s.", ret)
        # Read register shadows
        if ret.isOk():
            ret = self._syncShadows()
        # Configure
        if ret.isOk():
            cfg = Configuration( item=ConfigItem.multisetting,
                                 setting=paramDict )
            ret = self.configure(cfg)
            logging.debug("VD6283TX.open> configure: %s.", ret)
        # Activate
        if ret.isOk():
            ret = self.setRunLevel( RunLevel.active )
            logging.debug("VD6283TX.open> run level active: %s.", ret)
        
        return ret

    def close(self):
        ret = self.setRunLevel( RunLevel.shutdown )
        logging.debug("VD6283TX.close> run level shutdown: %s.", ret)
        err = super().close()
        logging.debug("VD6283TX.close> super.close: %s.", err)
        if ret.isOk():
            ret = err
        err = self.pinInt.close()
        logging.debug("VD6283TX.close> gpio.close: %s.", err)
        if ret.isOk():
            ret = err
        return ret


    def setRunLevel(self, level):
        ret = self.isAttached()
        if ret.isOk():
            dataALS = self._shadowAlsCtrl
            dataFLK = self._shadowAcModeCtrl
            if level == RunLevel.active:
                # Set enable bit
                dataALS |= VD6283TX.ALS_EN     
                dataFLK |= VD6283TX.AC_FREQEXT_EN
            else:
                # Wipe-out enable bit
                dataALS &= ~VD6283TX.ALS_EN
                dataFLK &= ~VD6283TX.AC_FREQEXT_EN
            ret = self.writeByteRegister( VD6283TX.REG_ALS_CTRL, dataALS )
            logging.debug("VD6283TX.setRunLevel> write REG_ALS_CTRL(x%02x): %s.",
                          dataALS, ret)
            if ret.isOk():
                self._shadowAlsCtrl = dataALS
                ret = self.writeByteRegister( VD6283TX.REG_AC_MODE_CTRL, dataFLK )
                logging.debug("VD6283TX.setRunLevel> write REG_AC_MODE_CTRL(x%02x): %s.",
                              dataFLK, ret)
                if ret.isOk():
                    self._shadowAcModeCtrl = dataFLK
        else:
            logging.debug("VD6283TX.setRunLevel> serial bus not attached: %s.", ret)
        return ret

    #
    # Sensor API
    #
    
    def selfTest(self, tests):
        ret = ErrorCode.errOk
        if tests & SelfTest.CONNECTION:
            data, ret = self.readByteRegister( VD6283TX.REG_DEVICE_ID )
            logging.debug("VD6283TX.selfTest> read REG_DEVICE_ID: x%02x, %s.",
                          data, ret)
            if ret.isOk() and (data != VD6283TX.DEVICE_ID):
                ret = ErrorCode.errFailure
        else:
            logging.debug("VD6283TX.selfTest> invalid tests: x%04x.", tests)
        return ret


    def reset(self):
        # Re-read register shadows
        ret = self._syncShadows()
        return ret


    def configure(self, cfg):
        """Configures the sensor device as described by the given configuration data.
        
        Note the ``cfg`` data is a multi-compound data class. Its ``item``
        attribute must be set to ``multisetting``. The configuration
        data is passed as a string-to-value dictionary in the
        ``cfg.setting`` attribute. This is pretty much like the initial
        parameters are passed to :meth:`open`.
        
        The following settings (keys) are supported:
        
        =====================================    ==========================================================================================================
        Key name                                 Value type, meaning and default
        =====================================    ==========================================================================================================
        light.int.cfg                            GPIO1 Interrupt pin configuration, VD6283TX.GPIO1_CFG_[OD | PUSH_PULL | ANALOGUE]
        light.sda.highcap                        SDA line capacitive load > 95pF, bool [True | False]
        light.sda.drv                            SDA current drive strength, low to high, int [1, ..., 5]
        light.Sensor.exposure                    Exposure time in [2, ..., 1638] milliseconds
        light.Sensor.interval                    Inter-measurement period in [0, ..., 5237] milliseconds. Only valid for continuous mode!
        light.Sensor.mode                        VD6283TX.ALS_MODE_[SINGLE | CONT], single-shot or continuous measurement+handshake mode. 
        light.Sensor.red.enable                  Enable the Red channel measurements. bool [True | False]
        light.Sensor.red.gain                    Red channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.green.enable                Enable the Green channel measurements. bool [True | False]
        light.Sensor.green.gain                  Green channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.blue.enable                 Enable the Blue channel measurements. bool [True | False]
        light.Sensor.blue.gain                   Blue channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.ir.enable                   Enable the IR channel measurements. bool [True | False]
        light.Sensor.ir.gain                     IR channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.visible.enable              Enable the Visible light channel measurements. bool [True | False]
        light.Sensor.visible.gain                Visible channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.clear.enable                Enable the Clear un-filtered light channel measurements. bool [True | False]
        light.Sensor.clear.gain                  Clear channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.flicker.bias.enable         Enable/Disable pedestal value feature, bool [True | False].
        light.Sensor.flicker.bias.value          Pedestal value for flicker output, int [0...7].
        light.Sensor.flicker.channel             Flicker operation channel; VD6283TX.CHANNEL_[NONE | IDX_1_RED ... IDX_6_CLEAR]
        light.Sensor.flicker.enable              Enable the frequency extraction feature. bool [True | False]
        light.Sensor.flicker.outport             GPIO output port for the flicker PDM signal; int [1 | 2]
        ===================================================================================================================================================
        
        Also see: :meth:`Params_init`, :class:`.configurable.Configuration`.        
        
        :param .configurable.Configuration cfg: Configuration data. 
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        if (not cfg) or (cfg.item != ConfigItem.multisetting) or \
            (not cfg.setting) or (not isinstance(cfg.setting, dict)):
            logging.debug("VD6283TX.configure> cfg.item=%s, cfg.setting=%s.", cfg.item, cfg.setting)
            return ErrorCode.errInvalidParameter
        
        ret = ErrorCode.errOk
        prefix = self.MODULE_PARAM_PREFIX + "."
        cs = cfg.setting
        
        # light.int.cfg  -->  REG_GPIO1_DRV_CFG
        value = cs.get(prefix + "int.cfg", None)
        if ret.isOk() and (value is not None) and isinstance(value, int):
            data = value if (value >= 0) and (value <= 2) else VD6283TX.GPIO1_CFG_DEFAULT
            ret = self.writeByteRegister( VD6283TX.REG_GPIO1_DRV_CFG, data )
            logging.debug("VD6283TX.configure> write REG_GPIO1_DRV_CFG: %s, value=x%02x, data=x%02x", ret, value, data)
       
        # light.sda:highcap, drv  -->  REG_SDA_DRV_CFG
        data = None
        value = cs.get(prefix + "sda.highcap", None)
        if ret.isOk() and (value is not None):
            data, ret = self.readByteRegister( VD6283TX.REG_SDA_DRV_CFG )
            data = (data | VD6283TX.SDA_LOAD) if value else (data & ~VD6283TX.SDA_LOAD)
        value = cs.get(prefix + "sda.drv", None)
        if ret.isOk() and (value is not None) and isinstance(value, int):
            if not data:
                data, ret = self.readByteRegister( VD6283TX.REG_SDA_DRV_CFG )
            data = data & ~VD6283TX.SDA_DRV
            data |= (value-1) if (value>0) and (value<=5) else VD6283TX.SDA_DRV_DEFAULT
        if ret.isOk() and data:
            ret = self.writeByteRegister( VD6283TX.REG_SDA_DRV_CFG, data )
            logging.debug("VD6283TX.configure> write REG_SDA_DRV_CFG: %s, data=x%02x", ret, data)
        
        prefix += "Sensor" + "."
        # light.Sensor.exposure  -->  REG_ALS_EXPOSURE
        value = cs.get(prefix + "exposure", None)
        if ret.isOk() and (value is not None) and isinstance(value, (int, float)):
            value = value if (value >= 1) and (value <= 1638) else 80
            data = int(value * 10 + 8) // 16 - 1
            data = ((data & 0xFF00) >> 8) | ((data & 0xFF) << 8) # swap endianess
            ret = self.writeWordRegister( VD6283TX.REG_ALS_EXPOSURE, data )
            logging.debug("VD6283TX.configure> write REG_ALS_EXPOSURE: %s, value=%s, data=%s", ret, value, data)
        # light.Sensor.interval  -->  REG_ALS_PERIOD
        value = cs.get(prefix + "interval", None)
        if ret.isOk() and (value is not None) and isinstance(value, (int, float)):
            value = value if (value >= 0) and (value <= 5237) else 0
            data = int(value * 2 + 20) // 41
            ret = self.writeByteRegister( VD6283TX.REG_ALS_PERIOD, data )
            logging.debug("VD6283TX.configure> write REG_ALS_PERIOD: %s, value=%s, data=%s", ret, value, data)
        # light.Sensor.mode  -->  REG_ALS_CTRL
        value = cs.get(prefix + "mode", None)
        if ret.isOk() and (value is not None) and \
            value in [VD6283TX.ALS_MODE_SINGLE, VD6283TX.ALS_MODE_CONT]:
            data = value | (self._shadowAlsCtrl & VD6283TX.ALS_EN) 
            ret = self.writeByteRegister( VD6283TX.REG_ALS_CTRL, data )
            logging.debug("VD6283TX.configure> write REG_ALS_CTRL: %s, value=%s, data=x%02x", ret, value, data)
        
        # light.Sensor.x.enable  -->  REG_ALS_CHANNEL_ENABLE
        data = None
        if ret.isOk():
            for ch in self._channel:
                if ch.index != 6:
                    value = cs.get(prefix + ch.name + ".enable", None)
                    if value is not None:
                        ch.isEnabled = bool(value)
                        if data is None:
                            data = ch.maskAlsEnable if value else VD6283TX.ALS_CH_EN_NONE
                        elif value:
                            data |= ch.maskAlsEnable
            if data:
                ret = self.writeByteRegister( VD6283TX.REG_ALS_CHANNEL_ENABLE, data )
                logging.debug("VD6283TX.configure> write REG_ALS_CHANNEL_ENABLE: %s, data=x%02x", ret, data)
        
        # light.Sensor.clear.enable  -->  REG_CHANNEL6_ENABLE
        value = cs.get(prefix + "clear.enable", None)
        if ret.isOk() and (value is not None):
            for ch in self._channel:
                if ch.index == 6:
                    ch.isEnabled = bool(value)
                    data = ch.maskAlsEnable if value else 0
                    ret = self.writeByteRegister( VD6283TX.REG_CHANNEL6_ENABLE, data )
                    logging.debug("VD6283TX.configure> write REG_CHANNEL6_ENABLE: %s, value=%s, data=x%02x", ret, value, data)
        
        # light.Sensor.x.gain  -->  REG_ALS_GAIN_CHX
        for ch in self._channel:
            if ret.isOk():
                value = cs.get(prefix + ch.name + ".gain", None)
                reg = VD6283TX.REG_ALS_GAIN_CHX + ch.index - 1
                ret = self._setGain( value, reg )
        
        # light.Sensor.flicker.bias.value  -->  REG_PEDESTAL_VALUE
        value = cs.get(prefix + "flicker.bias.value", None)
        if ret.isOk() and (value is not None) and isinstance(value, int):
            data = value & 0x07
            ret = self.writeByteRegister( VD6283TX.REG_PEDESTAL_VALUE, data )
            logging.debug("VD6283TX.configure> write REG_PEDESTAL_VALUE: %s, value=%s, data=x%02x", ret, value, data)

        # light.Sensor.flicker:bias.enable, channel, enable, outport  -->  REG_AC_MODE_CTRL
        setFeature = lambda ind, dat, pos, msk: dat if ind is None else ((dat & ~msk) | pos) if ind else (dat & ~msk)
        clrFeature = lambda ind, dat, pos, msk: dat if ind is None else (dat & ~msk) if ind else ((dat & ~msk) | pos) 
        data = self._shadowAcModeCtrl
        if ret.isOk():
            value = cs.get(prefix + "flicker.bias.enable", None)
            data = clrFeature( value, data, VD6283TX.PEDESTAL_DIS, VD6283TX.PEDESTAL_DIS )
            value = cs.get(prefix + "flicker.channel", None)
            if (value is not None) and isinstance( value, int) and (value>=1) and (value<=6):
                data &= ~0x0E
                for ch in self._channel:
                    if ch.index == value:
                        ch.hasFlicker = True
                        data |= ch.maskAcModeCtrl
                    else:
                        ch.hasFlicker = False
            value = cs.get(prefix + "flicker.enable", None)
            data = setFeature( value, data, VD6283TX.AC_FREQEXT_EN, VD6283TX.AC_FREQEXT_EN )
            value = cs.get(prefix + "flicker.outport", None)
            if value is not None:
                if value==1:
                    data &= ~VD6283TX.AC_OUT_SEL
                else: 
                    data |= VD6283TX.AC_OUT_SEL
            if data != self._shadowAcModeCtrl:
                ret = self.writeByteRegister( VD6283TX.REG_AC_MODE_CTRL, data )
                logging.debug("VD6283TX.configure> write REG_AC_MODE_CTRL: %s, data=x%02x", ret, data)
            else:
                logging.debug("VD6283TX.configure> no change for REG_AC_MODE_CTRL, data=x%02x.", data)

        return ret


    def getInfo(self):
        info = Info()
        data, ret = self.readByteRegister( VD6283TX.REG_ID )
        logging.debug("VD6283TX.getInfo> read REG_ID: data=x%02x, err=%s.", data, ret)
        if ret.isOk():
            info.validity |= Info.validChipID
            info.chipID = data
        data, ret = self.readByteRegister( VD6283TX.REG_REVISION_ID )
        logging.debug("VD6283TX.getInfo> read REG_REVISION_ID: data=x%02x, err=%s.", data, ret)
        if ret.isOk():
            info.validity |= Info.validRevMajor
            info.revMajor = data

        return info, ret


    def getStatus(self, statusID):
        del statusID
        status, ret = self.readByteRegister( VD6283TX.REG_INTERRUPT_CTRL )
        logging.debug("VD6283TX.getStatus> read REG_INTERRUPT_CTRL: data=x%02x, err=%s.", status, ret)
        return status, ret


    def getLatestData(self):
        data = dict()
        ret = ErrorCode.errOk
        
        for ch in self._channel:
            # Read out raw data
            if ch.isEnabled and not ch.hasFlicker:
                reg = VD6283TX.REG_ALS_CHX_DATA + (ch.index - 1)*4
                value, ret = self.readWordRegister( reg )
                if ret.isOk():
                    value, ret = self._transferToIntensity( value, ch )
                if ret.isOk():
                    name = VD6283TX.CHANNEL_NAME[ch.index]
                    data[name] = value
        if not data:
            ret = ErrorCode.errFewData
        return data, ret
    

    def getNextData(self):
        data = None
        ret = ErrorCode.errOk
        done = False
        loopCount = 0
        maxLoops = 10
        
        while ret.isOk() and not done and loopCount < maxLoops:
            intr, ret = self.getStatus( None )
            done = intr & VD6283TX.INTR_ST
            loopCount += 1
            
        if ret.isOk():
            if done:
                data, ret = self.getLatestData()
            else:
                ret = ErrorCode.errUnavailable

        if ret.isOk():
            ret = self.writeByteRegister( VD6283TX.REG_INTERRUPT_CTRL, VD6283TX.CLR_INTR )
            ret = self.writeByteRegister( VD6283TX.REG_INTERRUPT_CTRL, 0 )
            logging.debug("VD6283TX.getNextData> write REG_INTERRUPT_CTRL: %s.", ret)
            
        return data, ret
