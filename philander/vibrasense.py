"""Support module for the Mikro-e Vibra sense click board.

This board carries a Sencera 801S vibration spring device as its core
element. 
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["VibraSense"]
from pymitter import EventEmitter

from .gpio import GPIO
from .interruptable import Interruptable
from .sensor import Sensor
from .systypes import ErrorCode


class VibraSense( EventEmitter, Sensor, Interruptable):
    """Vibra sense driver implementation.
    
    More information on the Mikroelektronika Vibra sense click
    (MIKROE-1927) board are available at:
    https://www.mikroe.com/vibra-sense-click

    The functional core element is a Sencera 801S vibration spring.
    More information on that device can be found at:
    https://www.tme.eu/de/details/sens-801s/drucksensoren/sencera/801s/
    """
    
    SLOT_DEFAULT = 1
    
    SLOT1_PIN_ENABLE = 29  # P1.29 = GPIO:5 = RST
    SLOT1_PIN_SIGNAL = 31  # P1.31 = GPIO:6 = INT
    SLOT2_PIN_ENABLE = 32  # P1.32 = GPIO:12 = RST
    SLOT2_PIN_SIGNAL = 37  # P1.37 = GPIO:26 = INT
    
    DEBOUNCE_MS     = 10
    
    def __init__(self):
        self.gpioEnable = None
        self.gpioSignal = None
    
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
        Sensor.dataRate                  ``int`` Data rate in Hz; default is set by :meth:`.Sensor.Params_init`.
        VibraSense.slot                  ``int=[1|2]`` the slot that this board is plugged in. :attr:`SLOT_DEFAULT`.
        =============================    ==========================================================================================================
        
        Also see: :meth:`.Sensor.Params_init`, :meth:`.SerialBusDevice.Params_init`. 
        """
        if not ("VibraSense.slot" in paramDict):
            paramDict["VibraSense.slot"] = VibraSense.SLOT_DEFAULT
        super().Params_init(paramDict)
        return None

    def open(self, paramDict):
        ret = ErrorCode.errOk
        defaults = {}
        VibraSense.Params_init(defaults)
        gpioParams = {}
        slot = paramDict.get( "VibraSense.slot", defaults["VibraSense.slot"])
        gpioParams["gpio.pinNumbering"] = GPIO.PINNUMBERING_BOARD
        # Setup the enable pin
        if (slot == 1):
            gpioParams["gpio.pinDesignator"] = VibraSense.SLOT1_PIN_ENABLE
        elif (slot == 2):
            gpioParams["gpio.pinDesignator"] = VibraSense.SLOT2_PIN_ENABLE
        else:
            ret = ErrorCode.errInvalidParameter
        if (ret == ErrorCode.errOk):
            gpioParams["gpio.direction"] = GPIO.DIRECTION_OUT
            gpioParams["gpio.level"] = GPIO.LEVEL_HIGH
            self.gpioEnable = GPIO()
            ret = self.gpioEnable.open(gpioParams)
        # Setup the signal pin
        if (ret == ErrorCode.errOk):
            if (slot == 1):
                gpioParams["gpio.pinDesignator"] = VibraSense.SLOT1_PIN_SIGNAL
            elif (slot == 2):
                gpioParams["gpio.pinDesignator"] = VibraSense.SLOT2_PIN_SIGNAL
            gpioParams["gpio.direction"] = GPIO.DIRECTION_IN
            gpioParams["gpio.pull"] = GPIO.PULL_DOWN
            gpioParams["gpio.trigger"] = GPIO.TRIGGER_EDGE_RISING
            gpioParams["gpio.bounce"] = VibraSense.DEBOUNCE_MS
            gpioParams["gpio.handler"] = self._intHandler
            ret = self.gpioSignal.open(gpioParams)
        return ret
    
    def close(self):
        ret = ErrorCode.errOk
        if self.gpioEnable:
            ret = self.gpioEnable.close()
            self.gpioEnable = None
        if self.gpioSignal:
            ret = self.gpioSignal.close()
            self.gpioSignal = None
        return ret

    #
    # Sensor API
    #
    
    def _intHandler(self):
        self.emit(GPIO.EVENT_DEFAULT)
    
    def getLatestData(self):
        return self.getNextData()

    def getNextData(self):
        err = ErrorCode.errOk
        value = 0
        if self.gpioSignal:
            value = self.gpioSignal.get()
            err = ErrorCode.errOk
        else:
            err = ErrorCode.errUnavailable
        return value, err
    
