"""Abstraction module for analogue-to-digital conversion.

Provide a convergence layer API to abstract from several different
ADC implementing driver modules possibly installed on the target
system.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["ADC"]

import logging

from philander.module import Module
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode


class ADC( Module ):
    """Analogue-to-digital converter abstraction class.
    
    Provide access to and control over the underlying ADC hardware. For
    that, an implementing driver module is used. As a convergence layer,
    this class is to hide specifics and to level syntactic requirements
    of the implementing package.
    """
    
    DIGITAL_MAX = 0xFFFF        # Maximum digital value

    DEFAULT_SAMPLING_TIME = 100 # default sampling time in microseconds
    DEFAULT_VREF_LOWER = 0      # default lower reference Voltage VRef-
    DEFAULT_VREF_UPPER = 3000   # default upper reference Voltage VRef+
    
    def __init__(self):
        """Initialize the instance with defaults.
        
        Note that just after construction, the instance is not
        operable, yet. Call :meth:`open` to configure it and set it
        into a functional state.
        """
        self._adc = None
        self.designator = None
        self.isOpen = False
        self.provider = SysProvider.NONE
        self.samplingTime = 0                   # show it's not set
        self.vref_lower = ADC.DEFAULT_VREF_LOWER
        self.vref_upper = ADC.DEFAULT_VREF_UPPER

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
        
        ==================    ==============================================    =========================
        Key                   Range                                             Default
        ==================    ==============================================    =========================
        adc.pinDesignator     pin name or channel number (e.g. 2 or "2")        None
        adc.samplingTime      Sampling time in microseconds; integer>=0         None
        adc.vref.lower        lower reference voltage in mV; integer            :attr:`DEFAULT_VREF_LOWER`
        adc.vref.upper        upper reference voltage in mV; integer            :attr:`DEFAULT_VREF_UPPER`
        ==================    ==============================================    =========================
        
        :param dict(str, object) paramDict: Configuration parameters as obtained from :meth:`Params_init`, possibly.
        :return: none
        :rtype: None
        """
        defaults = {
            "adc.vref.lower": ADC.DEFAULT_VREF_LOWER,
            "adc.vref.upper": ADC.DEFAULT_VREF_UPPER,
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
        # Retrieve defaults
        defaults = {}
        self.Params_init(defaults)
        # Scan parameters
        self.designator = paramDict.get("adc.pinDesignator", None)
        if self.designator is None:
            ret = ErrorCode.errInvalidParameter
        else:
            if not isinstance( self.designator, int ):
                try:
                    num = int(self.designator)
                    self.designator = num
                except ValueError:
                    pass
            self.samplingTime = paramDict.get("adc.samplingTime", 0)
            self.vref_lower = paramDict.get("adc.vref.lower", defaults["adc.vref.lower"])
            self.vref_upper = paramDict.get("adc.vref.upper", defaults["adc.vref.upper"])
            if self.vref_lower < self.vref_upper:
                self.isOpen = True
            else:
                ret = ErrorCode.errInvalidParameter
        logging.debug("ADC base> open <%s> returns %s.", self.designator, ret)
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
            self.isOpen = False
        else:
            ret = ErrorCode.errResourceConflict
        logging.debug("ADC base> close <%s> returns %s.", self.designator, ret)
        return ret

    def setRunLevel(self, level):
        """Select the power-saving operation mode.

        Switches the instance to one of the power-saving modes or
        recovers from these modes. Situation-aware deployment of these
        modes can greatly reduce the system's total power consumption.
        
        :param RunLevel level: The level to switch to.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del level
        return ErrorCode.errNotImplemented

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
        err = ErrorCode.errNotImplemented
        val = 0
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
        val = self.vref_lower
        dval, err = self.getDigital()
        if err.isOk():
            val, err = self.toVoltage( dval )
        return val, err

    def toVoltage(self, digital):
        """Convert a digital value to its corresponding voltage in mV.
        
        Map the digital sample value to the range of [vref_lower, vref_upper]
        and return the corresponding voltage expressed in millivolts [mV].

        :param int digital: The digital value to convert. Must be in [0, 0xFFFF].
        :return: A mV-value in the range [vref_lower, vref_upper] and\
        an error code indicating either success or the reason of failure.
        :rtype: int, ErrorCode
        """
        err = ErrorCode.errOk
        val = self.vref_lower
        if not self.isOpen:
            err = ErrorCode.errResourceConflict
        elif not isinstance(digital, int):
            err = ErrorCode.errInvalidParameter
        elif (digital < 0) or (digital > 0xFFFF):
            err = ErrorCode.errSpecRange
        else:
            val = digital * (self.vref_upper-self.vref_lower)
            val = (val + (ADC.DIGITAL_MAX // 2)) // ADC.DIGITAL_MAX
            val = val + self.vref_lower
        return val, err
