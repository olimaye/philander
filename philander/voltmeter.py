# -*- coding: utf-8 -*-
"""Driver implementation for a simple ADC-based voltage monitor and gas-gauge.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Voltmeter"]

from .gasgauge import GasGauge
from .gpio import GPIO
from .module import Module
from .systypes import ErrorCode


class Voltmeter( Module, GasGauge ):
    """Driver for a generic ADC-based voltmeter.
    """
    
    DEFAULT_RANGE_MAX   = 3300
    DEFAULT_RANGE_MIN   = 2500
    
    @classmethod
    def Params_init(cls, paramDict):
        """Initialize parameters with their defaults.

        The following settings are supported:
        
        =============================    ==========================================================================================================
        Key name                         Value type, meaning and default
        =============================    ==========================================================================================================
        Voltmeter.range.max              ``int`` Maximum voltage in mV, maps to 100%; default is :attr:`DEFAULT_RANGE_MAX`.
        Voltmeter.range.min              ``int`` Minimum voltage in mV, mapped to 0%; default is :attr:`DEFAULT_RANGE_MIN`.
        Voltmeter.gpio.direction         see :meth:`.GPIO.Params_init`; default is :attr:`.GPIO.DIRECTION_IN`.
        Voltmeter.gpio.trigger           see :meth:`.GPIO.Params_init`; default is :attr:`.GPIO.TRIGGER_EDGE_FALLING`.
        Voltmeter.gpio.bounce            see :meth:`.GPIO.Params_init`; default is :attr:`.GPIO.BOUNCE_NONE`.
        All other Voltmeter.gpio.*       as documented at :meth:`.GPIO.Params_init`.
        =============================    ==========================================================================================================
        
        Also see: :meth:`.Module.Params_init`.
        
        :param dict(str, object) paramDict: Dictionary of settings.
        :returns: none
        :rtype: None
        """
        if not "Voltmeter.range.max" in paramDict:
            paramDict["Voltmeter.range.max"] = Voltmeter.DEFAULT_RANGE_MAX
        if not "Voltmeter.range.min" in paramDict:
            paramDict["Voltmeter.range.min"] = Voltmeter.DEFAULT_RANGE_MIN
        # Add gpio parameters
        paramDict["Voltmeter.gpio.direction"] = GPIO.DIRECTION_IN
        if not ("Voltmeter.gpio.trigger" in paramDict):
            paramDict["Voltmeter.gpio.trigger"] = GPIO.TRIGGER_EDGE_FALLING
        if not ("Voltmeter.gpio.bounce" in paramDict):
            paramDict["Voltmeter.gpio.bounce"] = GPIO.BOUNCE_NONE
        gpioParams = {}
        GPIO.Params_init( gpioParams )
        gp = dict( [("Voltmeter."+k,v) for k,v in gpioParams.items()] )
        for key, value in gp.items():
            if not( key in paramDict):
                paramDict[key] = value
        return None
    
    def __init__( self, paramDict ):
        # Initialize attributes
        defDict = {}
        Voltmeter.Params_init(defDict)
        self._rangeMax = defDict["Voltmeter.range.max"]
        self._rangeMin = defDict["Voltmeter.range.min"]
        # This is also to indicate whether or not open() was called
        self._pin = None

    def open( self, paramDict ):
        """Initialize an instance and prepare it for use.

        Also see: :meth:`.Module.open`.
        
        :param dict(str, object) paramDict: Configuration parameters as\
        possibly obtained from :meth:`Params_init`.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        if not (self._pin is None):
            result = ErrorCode.errResourceConflict
        else:
            defDict = {}
            Voltmeter.Params_init(defDict)
            if "Voltmeter.range.max" in paramDict:
                self._rangeMax = paramDict["Voltmeter.range.max"]
            else:
                self._rangeMax = defDict["Voltmeter.range.max"]
            if "Voltmeter.range.min" in paramDict:
                self._rangeMin = paramDict["Voltmeter.range.min"]
            else:
                self._rangeMin = defDict["Voltmeter.range.min"]
            paramDict["Voltmeter.gpio.direction"] = GPIO.DIRECTION_IN
            gpioParams = dict( [(k.replace("Voltmeter.gpio", "gpio"),v) for k,v in paramDict.items() if k.startswith("Voltmeter.gpio")] )
            self._pin = GPIO.getGPIO()
            result = self._pin.open(gpioParams)
        return result
    
    def close(self):
        """Close this instance and release hardware resources.
        
        Also see: :meth:`.Module.close`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        if not (self._pin is None):
            result = self._pin.close()
            self._pin = None
        return result
 
    
    #
    # GasGauge API
    #
    
    # Not yet implemented.
    
    
    