"""ADC implementation for the ADC1283 A/D converter chip by ST micro.

More information on this chip can be found at
https://www.st.com/en/data-converters/adc1283.html

"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_ADC_STADC1283"]

from philander.adc import ADC
from philander.serialbus import SerialBusDevice, SerialBusType
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

class STADC1283( ADC, SerialBusDevice ):
    """Implementation of the abstract ADC interface for the digital ADC device.
    """

    # Overwrite implementation-specific constants
    DIGITAL_MAX = 0x0FFF        # Maximum digital value
    
    DEFAULT_CHANNEL = 0
    
    USE_CONFIGURED_CHANNEL = 8
    
    def __init__(self):
        """Initialize the instance with defaults.
        """
        ADC.__init__(self)
        SerialBusDevice.__init__(self)
        self.provider = SysProvider.COMPOSITE

    #
    # Module API
    #

    @classmethod
    def Params_init(cls, paramDict):
        """Initialize parameters with their defaults.

        The given dictionary should not be None, on entry.
        Options not present in the dictionary will be added and set to
        their defaults on return.
        The following options are supported.
        
        =========================    ===================================================================
        Key                          Range, meaning and default
        =========================    ===================================================================
        SerialBusDevice.*            Serial bus configuration; See :meth:`.SerialBusDevice.Params_init`.
        adc.*                        ADC configuration; See :meth:`.ADC.Params_init`.
        =========================    ===================================================================
        
        :param dict(str, object) paramDict: Configuration parameters as obtained from :meth:`Params_init`, possibly.
        :return: none
        :rtype: None
        """
        paramDict["SerialBus.type"] = SerialBusType.SPI
        ADC.Params_init( paramDict )
        SerialBusDevice.Params_init( paramDict )
        defaults = {
            "adc.channel":  cls.DEFAULT_CHANNEL,
        }
        for key, value in defaults.items():
            if not key in paramDict:
                paramDict[key] = value
        return None

    def open(self, paramDict):
        """Opens the instance and sets it in a usable state.

        Allocate necessary hardware resources and configure
        user-adjustable parameters to meaningful defaults.
        This function must be called prior to any further usage of the
        instance. Involving it in the system ramp-up procedure could be
        a good choice. After usage of this instance is finished, the
        application should call :meth:`close`.
        
        :param dict(str, object) paramDict: Configuration parameters as obtained from :meth:`Params_init`, possibly.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        defaults = {}
        self.Params_init( defaults )
        if self.isOpen:
            ret = ErrorCode.errResourceConflict
        if ret.isOk():
            ret = ADC.open( self, paramDict )
        if ret.isOk() and ((self.channel < 0) or (self.channel > 7)):
                ret = ErrorCode.errInvalidParameter
        if ret.isOk():
            self._adc = 1
            paramDict["SerialBus.type"] = defaults["SerialBus.type"]
            ret = SerialBusDevice.open( self, paramDict )

        self.isOpen = ret.isOk()
        return ret

    def close(self):
        """Closes this instance and releases associated hardware resources.

        This is the counterpart of :meth:`open`. Upon return, further
        usage of this instance is prohibited and may lead to unexpected
        results. The instance can be re-activated by calling :meth:`open`,
        again.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if self.isOpen:
            ret = SerialBusDevice.close(self)
            err = ADC.close(self)
            if ret.isOk():
                ret = err
            self.isOpen = False
        else:
            ret = ErrorCode.errResourceConflict
        #logging.debug("STADC1283> close <%s> returns %s.", self.channel, ret)
        return ret

    #
    # ADC specific API
    #

    def getDigital(self, channel=USE_CONFIGURED_CHANNEL):
        """Retrieve a sample and return its digital value.

        Gives the most recent sample as a digital value between zero and
        the maximum digital value [0...DIGITAL_MAX].
        
        :return: A value in the range [0, DIGITAL_MAX] and an error code\
        indicating either success or the reason of failure.
        :rtype: int, ErrorCode
        """
        val = 0
        err = ErrorCode.errOk
        if self.isOpen:
            if channel == self.USE_CONFIGURED_CHANNEL:
                channel = self.channel
            if (channel<0) or (channel>7) or not isinstance(channel, int):
                err = ErrorCode.errInvalidParameter
            elif channel == self.DEFAULT_CHANNEL:
                outBuf = [channel, 0]
                data, err = self.writeReadBuffer( outBuf, 2)
            else:
                cb = channel << 3
                outBuf = [cb, 0, 0, 0]
                data, err = self.writeReadBuffer( outBuf, 2)
            if err.isOk():
                val = (data[0] << 8) + data[1]
        else:
            val = 0
            err = ErrorCode.errResourceConflict
        return val, err

    def getVoltage(self, channel=USE_CONFIGURED_CHANNEL):
        """Retrieve a sample and return it as a voltage in mV.

        Also see :meth:`.ADC.getVoltage`
        
        :return: A mV-value in the range [vref_lower, vref_upper] and\
        an error code indicating either success or the reason of failure.
        :rtype: int, ErrorCode
        """
        val = self.vref_lower
        dval, err = self.getDigital(channel)
        if err.isOk():
            val, err = self.toVoltage( dval )
        return val, err

