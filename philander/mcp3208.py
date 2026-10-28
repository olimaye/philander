"""ADC implementation for the MCP3204 and MCP3208 A/D converter chips by Microchip.

Although this chip has a digital interface, there is no way to detect
the exact chip model. So the number of available channels must be
configured elsewhere or known by the application.
The MCP3204 is used on the Pi3 click shield by mikroe, for example.

More information on this chip can be found at
https://www.microchip.com/en-us/product/mcp3204

"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["MCP3208"]

from philander.adc import ADC
from philander.serialbus import SerialBusDevice, SerialBusType
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

class MCP3208( ADC, SerialBusDevice ):
    """Implementation of the abstract ADC interface for the digital ADC device.
    """

    # Overwrite implementation-specific constants
    DIGITAL_MAX = 0x0FFF        # Maximum digital value
    
    DEFAULT_CHANNEL = 0
    
    USE_CONFIGURED_CHANNEL = 8
    
    DIFF_MODE_NONE  = 0
    DIFF_MODE_POS   = 1
    DIFF_MODE_NEG   = 2
    
    def __init__(self):
        """Initialize the instance with defaults.
        """
        ADC.__init__(self)
        SerialBusDevice.__init__(self)
        self.provider = SysProvider.COMPOSITE
        self._differentialMode = MCP3208.DIFF_MODE_NONE

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
        adc.differential.mode        False: single mode; True or "positive" or "negative" for diff. mode
        =========================    ===================================================================
        
        If differential mode is selected, the digital output will
        represent the difference between channel pairs 0 and 1, 2 and 3
        and so on. On differential.mode=True, the positive mode will be
        used by default (Ch1-Ch0), (Ch3-Ch2) etc. On "negative" mode,
        the difference will be reversed, i.e. (Ch0-Ch1), (Ch2-Ch3).
        
        :param dict(str, object) paramDict: Configuration parameters as obtained from :meth:`Params_init`, possibly.
        :return: none
        :rtype: None
        """
        paramDict["SerialBus.type"] = SerialBusType.SPI
        ADC.Params_init( paramDict )
        SerialBusDevice.Params_init( paramDict )
        defaults = {
            "adc.channel":  cls.DEFAULT_CHANNEL,
            "adc.differential.mode":    False,
        }
        # Add defaults to paramDict
        cls._aggregateParams( paramDict, defaults )
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
        if ret.isOk():
            diffMode = paramDict.get("adc.differential.mode", False)
            if not diffMode:
                self._differentialMode = MCP3208.DIFF_MODE_NONE
            elif not isinstance(diffMode, str):
                self._differentialMode = MCP3208.DIFF_MODE_POS
            elif diffMode.lower().startswith("neg"):
                self._differentialMode = MCP3208.DIFF_MODE_NEG
            else:
                self._differentialMode = MCP3208.DIFF_MODE_POS
                
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
            else:
                outBuf = [0, 0, 0]
                outBuf[0] = 0x04    # Start bit
                if self._differentialMode == MCP3208.DIFF_MODE_NONE:
                    outBuf[0] |= 0x02   # Single/Diff bit
                elif self._differentialMode == MCP3208.DIFF_MODE_POS:
                    channel |= 0x01
                elif self._differentialMode == MCP3208.DIFF_MODE_NEG:
                    channel &= 0x0E
                outBuf[0] |= channel >> 2
                outBuf[1] = channel << 6
                data, err = self.writeReadBuffer( outBuf, 2)
            if err.isOk():
                val = ((data[0] & 0x0F) << 8) | data[1]
        else:
            val = 0
            err = ErrorCode.errResourceConflict
        return val, err


