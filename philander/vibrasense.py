"""Support module for the Mikro-e Vibra sense click board.

This board carries a Sencera 801S vibration spring device as its core
element. 
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["VibraSense"]
from pymitter import EventEmitter

from philander.gpio import GPIO
from philander.interruptable import Interruptable
from philander.sensor import Sensor
from philander.systypes import ErrorCode


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
    
    DEBOUNCE_MS     = GPIO.BOUNCE_NONE
    
    def __init__(self):
        self.gpioEnable = None
        self.gpioSignal = None
        EventEmitter.__init__(self)
        Sensor.__init__(self)
        Interruptable.__init__(self)
    
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
        VibraSense.int.gpio.*            configuration of the INT pin, as documented at :meth:`.GPIO.Params_init`, overrides VibraSense.slot
        VibraSense.enable.gpio.*         configuration of the EN pin, as documented at :meth:`.GPIO.Params_init`, optional.
        VibraSense.slot                  ``int=[1|2]`` the click board's slot, alternative for int+enable pin configuration; :attr:`SLOT_DEFAULT`.
        =============================    ==========================================================================================================
        
        Also see: :meth:`.Sensor.Params_init`, :meth:`.SerialBusDevice.Params_init`. 
        """
        if "VibraSense.int.gpio.pinDesignator" in paramDict:
            paramDict["VibraSense.int.gpio.direction"] = GPIO.DIRECTION_IN
            if not "VibraSense.int.gpio.bounce" in paramDict:
                paramDict["VibraSense.int.gpio.bounce"] = VibraSense.DEBOUNCE_MS
            if "VibraSense.enable.gpio.pinDesignator" in paramDict:
                paramDict["VibraSense.enable.gpio.direction"] = GPIO.DIRECTION_OUT
        else:
            slot = paramDict.get("VibraSense.slot", VibraSense.SLOT_DEFAULT)
            slot = VibraSense.SLOT_DEFAULT if not slot in (1,2) else slot
            paramDict["VibraSense.slot"] = slot
            gpioEnaParams = {
                "VibraSense.enable.gpio.pinNumbering" :   GPIO.PINNUMBERING_BOARD,
                "VibraSense.enable.gpio.pinDesignator":   VibraSense.SLOT1_PIN_ENABLE if (slot==1) else VibraSense.SLOT2_PIN_ENABLE,
                "VibraSense.enable.gpio.direction"    :   GPIO.DIRECTION_OUT,
                "VibraSense.enable.gpio.level"        :   GPIO.LEVEL_HIGH,
                }
            gpioIntParams = {
                "VibraSense.int.gpio.pinNumbering" :   GPIO.PINNUMBERING_BOARD,
                "VibraSense.int.gpio.pinDesignator":   VibraSense.SLOT1_PIN_SIGNAL if (slot==1) else VibraSense.SLOT2_PIN_SIGNAL,
                "VibraSense.int.gpio.direction"    :   GPIO.DIRECTION_IN,
                "VibraSense.int.gpio.pull"         :   GPIO.PULL_DOWN,
                "VibraSense.int.gpio.trigger"      :   GPIO.TRIGGER_EDGE_RISING,
                "VibraSense.int.gpio.bounce"       :   VibraSense.DEBOUNCE_MS,
                }
            paramDict.update( gpioEnaParams )
            paramDict.update( gpioIntParams )
            
        Sensor.Params_init(paramDict)
        return None

    def open(self, paramDict):
        ret = ErrorCode.errOk
        VibraSense.Params_init(paramDict)
        prefix = "VibraSense.int."
        gpioIntParams = dict( [(k.replace(prefix, ""),v) for k,v in paramDict.items() if k.startswith(prefix)] )
        gpioIntParams["gpio.handler"] = self._intHandler
        if "VibraSense.enable.gpio.pinDesignator" in paramDict:
            prefix = "VibraSense.enable."
            gpioEnaParams = dict( [(k.replace(prefix, ""),v) for k,v in paramDict.items() if k.startswith(prefix)] )
        else:
            gpioEnaParams = None
        # Setup the enable pin
        if ret.isOk() and gpioEnaParams:
            self.gpioEnable = GPIO.getGPIO()
            ret = self.gpioEnable.open(gpioEnaParams)
            if ret.isOk():
                ret = self.gpioEnable.set( GPIO.LEVEL_HIGH )
        # Setup the signal pin
        if ret.isOk():
            self.gpioSignal = GPIO.getGPIO()
            ret = self.gpioSignal.open(gpioIntParams)
        return ret
    
    def close(self):
        ret = ErrorCode.errOk
        if self.gpioSignal:
            ret = self.gpioSignal.close()
            self.gpioSignal = None
        if self.gpioEnable:
            self.gpioEnable.set( GPIO.LEVEL_LOW )
            ret = self.gpioEnable.close()
            self.gpioEnable = None
        return ret

    #
    # Sensor API
    #
    
    def _intHandler(self, *arg):
        self.emit(GPIO.EVENT_DEFAULT, *arg)
    
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
    
