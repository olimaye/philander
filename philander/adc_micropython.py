"""ADC implementation for the Micropython environment.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_ADC_Micropython"]

from philander.adc import ADC
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

from machine import ADC as Driver

class _ADC_Micropython( ADC ):
    """Implementation of the abstract ADC interface for the Micropython environment.
    """

    # Overwrite implementation-specific constants
    DIGITAL_MAX = 0xFFFF        # Maximum digital value
    
    def __init__(self):
        """Initialize the instance with defaults.
        """
        super().__init__()
        self.provider = SysProvider.MICROPYTHON

    #
    # Module API
    #

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
        if self.isOpen:
            if not hasattr( Driver, 'init'):
                ret = ErrorCode.errResourceConflict
            else:
                ret = super().open( paramDict )
            if ret.isOk():
                if self.samplingTime > 0:
                    try:
                        self._adc.init( sample_ns=self.samplingTime*1000 )
                    except TypeError:   # keyword argument 'sample_ns' not supported
                        ret = ErrorCode.errInvalidParameter
                else:
                    self._adc.init()
        else:
            ret = super().open( paramDict )
            if ret.isOk():
                if self.channel == ADC.CHANNEL_DIE_TEMP:
                    if not hasattr( Driver, 'CORE_TEMP'):
                        ret = ErrorCode.errInvalidParameter
                    else:
                        self.channel = Driver.CORE_TEMP
            if ret.isOk():
                if self.samplingTime > 0:
                    try:
                        self._adc = Driver( self.channel, sample_ns=self.samplingTime*1000 )
                    except TypeError:   # keyword argument 'sample_ns' not supported
                        ret = ErrorCode.errInvalidParameter
                else:
                    self._adc = Driver( self.channel )
            if ret.isOk() and (self._adc is None):
                ret = ErrorCode.errLowLevelFail
            self.isOpen = ret.isOk()
        return ret

    #
    # ADC specific API
    #

    def getDigital(self):
        """Retrieve a sample and return its digital value.

        Gives the most recent sample as a digital value between zero and
        the maximum digital value [0...DIGITAL_MAX].
        
        :return: A value in the range [0, DIGITAL_MAX] and an error code\
        indicating either success or the reason of failure.
        :rtype: int, ErrorCode
        """
        if self.isOpen:
            val = self._adc.read_u16()
            err = ErrorCode.errOk
        else:
            val = 0
            err = ErrorCode.errResourceConflict
        return val, err

    def getVoltage(self):
        """Retrieve a sample and return it as a voltage in mV.

        Gives the most recent sample as a voltage value between
        the lower and upper reference voltage, expressed as milli Volts.
        Calibration and temperature correction is at the discretion of
        the implementation and hence, cannot be assured.
        
        :return: A mV-value in the range [vref_lower, vref_upper] and\
        an error code indicating either success or the reason of failure.
        :rtype: int, ErrorCode
        """
        if not self.isOpen:
            val = self.vref_lower
            err = ErrorCode.errResourceConflict
        elif not hasattr( self._adc, "read_uv"):
            val, err = super().getVoltage()
        else:
            val = self._adc.read_uv()
            if( val >= 0):
                val = (val + 500) // 1000
            else:
                val = (val - 500) // 1000
            err = ErrorCode.errOk
        return val, err

