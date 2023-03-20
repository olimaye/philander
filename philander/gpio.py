from systypes import ErrorCode
from Module import Module
from Interruptable import Interruptable
import warnings

class GPIO( Module, Interruptable ):

    _IMPLMOD_NONE       = 0
    _IMPLMOD_RPIGPIO    = 1
    _IMPLMOD_GPIOZERO   = 2
    _IMPLMOD_PERIPHERY  = 3
    _IMPLMOD_SIM        = 4

    DIRECTION_IN        = 1
    DIRECTION_OUT       = 2
    
    LEVEL_LOW           = 0
    LEVEL_HIGH          = 1
    
    PULL_UP             = 1
    PULL_DOWN           = 2
    PULL_NONE           = 3
    
    TRIGGER_EDGE_RISING = 1
    TRIGGER_EDGE_FALLING= 2
    TRIGGER_EDGE_ANY    = 3
    TRIGGER_LEVEL_HIGH  = 4
    TRIGGER_LEVEL_LOW   = 5
    
    BOUNCE_NONE         = 0
    BOUNCE_DEFAULT      = 200
    EVENT_DEFAULT       = "gpioFired"
    
    def __init__(self):
        self._factory = None
        self._implmod = self._detectDriverModule()
        self.pin = None
        self._dictDirection = {}
        self._dictLevel = {}
        self._dictPull = {}
        self._dictTrigger = {}
        self._designator = None
        self._direction = GPIO.DIRECTION_OUT
        self._trigger = GPIO.TRIGGER_EDGE_RISING
        Interruptable.__init__(self)
        
        
    def _detectDriverModule( self ):
        ret = GPIO._IMPLMOD_NONE
        try:
            from RPi.GPIO import GPIO as gpioFactory
            self._factory = gpioFactory
            self._dictDirection = {GPIO.DIRECTION_IN: gpioFactory.IN, GPIO.DIRECTION_OUT: gpioFactory.OUT}
            self._dictLevel     = {GPIO.LEVEL_LOW: gpioFactory.LOW, GPIO.LEVEL_HIGH: gpioFactory.HIGH}
            self._dictPull      = {GPIO.PULL_NONE: gpioFactory.PUD_NONE, GPIO.PULL_DOWN: gpioFactory.PUD_DOWN, GPIO.PULL_UP: gpioFactory.PUD_UP}
            self._dictTrigger   = {GPIO.TRIGGER_EDGE_RISING: gpioFactory.RISING, GPIO.TRIGGER_EDGE_FALLING: gpioFactory.FALLING, GPIO.TRIGGER_EDGE_ANY: gpioFactory.BOTH}
            ret = GPIO._IMPLMOD_RPIGPIO
        except ModuleNotFoundError:
            pass
        if (ret == GPIO._IMPLMOD_NONE):
            try:
                from gpiozero import  DigitalInputDevice, DigitalOutputDevice
                self._factory = None
                self._inFactory = DigitalInputDevice
                self._outFactory= DigitalOutputDevice
                ret = GPIO._IMPLMOD_GPIOZERO
            except ModuleNotFoundError:
                pass
        if (ret == GPIO._IMPLMOD_NONE):
            try:
                from periphery import GPIO as gpioFactory
                self._factory = gpioFactory
                ret = GPIO._IMPLMOD_PERIPHERY
            except ModuleNotFoundError:
                pass
        if (ret == GPIO._IMPLMOD_NONE):
            warnings.warn('Cannot find GPIO factory lib. Using SIM. Consider installing RPi.GPIO, gpiozero or periphery!')
            ret = GPIO._IMPLMOD_SIM
        return ret

    def _callback(self):
        self.eventEmitter.emit( GPIO.EVENT_DEFAULT, self._designator )
        return None
    
    # Initialize parameters with its defaults.
    # @param[in, out] paramDict The parameter structure to be initialized. Should not be NULL.
    # @return <code>None</code>
    @classmethod
    def Params_init(cls, paramDict):
        if not ("gpio.direction" in paramDict):
            paramDict["gpio.direction"] = GPIO.DIRECTION_OUT
        if not ("gpio.level" in paramDict):
            paramDict["gpio.level"] = GPIO.LEVEL_LOW
        if not ("gpio.pull" in paramDict):
            paramDict["gpio.pull"] = GPIO.PULL_NONE
        if not ("gpio.trigger" in paramDict):
            paramDict["gpio.trigger"] = GPIO.TRIGGER_EDGE_RISING
        if not ("gpio.bounce" in paramDict):
            paramDict["gpio.bounce"] = GPIO.BOUNCE_DEFAULT
        return None

    # Opens a specific instance and sets it in a usable state. Allocates necessary
    # hardware resources and configures user-adjustable parameters to meaningful defaults.
    # This function must be called prior to any further usage of the instance.
    # Involving it in the system ramp-up procedure could be a good choice.
    # After usage of this instance is finished, the application should call
    # #module_close.
    # @param[in] paramDicts The parameters to be used for configuration. If NULL, defaults
    # are applied. This is a dictionary containing key-value pairs that
    # configure the instance.
    # @return An <code>#ErrorCode</code> error code either indicating that this
    # call was successful or the reason why it failed.
    def open(self, paramDict):
        ret = ErrorCode.errOk
        # Retrieve defaults
        defaults = {}
        self.Params_init( defaults )
        # Scan parameters
        self._designator = paramDict.get( "gpio.pinDesignator", None )
        if (self._designator is None):
            ret = ErrorCode.errInvalidParameter
        self._direction = paramDict.get( "gpio.direction", defaults["gpio.direction"] )
        if (self._direction == GPIO.DIRECTION_OUT):
            level = paramDict.get( "gpio.level", defaults["gpio.level"] )
        else:
            pull  = paramDict.get( "gpio.pull", defaults["gpio.pull"] )
            self._trigger = paramDict.get( "gpio.trigger", defaults["gpio.trigger"] )
            bounce = paramDict.get( "gpio.bounce", defaults["gpio.bounce"] )
            handler = paramDict.get( "gpio.handler", None )
        if (ret == ErrorCode.errOk):
            if (self._implmod == GPIO._IMPLMOD_RPIGPIO):
                self._factory.setmode(self._factory.BOARD)
                self.pin = self._designator
                if (self._direction == GPIO.DIRECTION_OUT):
                    self._factory.setup( self._designator, self._factory.OUT, initial=self._dictLevel[level] )
                else:
                    self._factory.setup( self._designator, self._factory.IN, pull_up_down=self._dictPull[pull] )
                    self._factory.add_event_callback( self._designator, callback=self._callback, bouncetime=bounce)
                    if not(handler is None):
                        ret = self.registerInterruptHandler(handler)
            elif (self._implmod == GPIO._IMPLMOD_GPIOZERO):
                ret = ErrorCode.errNotImplemented
            elif (self._implmod == GPIO._IMPLMOD_PERIPHERY):
                ret = ErrorCode.errNotImplemented
            elif (self._implmod == GPIO._IMPLMOD_SIM):
                self._level = level
            else:
                ret = ErrorCode.errNotImplemented
        return ret

    # Closes this instance and releases associated hardware resources. This is the
    # counterpart of #open.
    # Upon return, further usage of this instance is prohibited and may lead to
    # unexpected results. The instance can be re-activated by calling #open,
    # again.
    # @return <code>None</code>
    def close(self):
        ret = ErrorCode.errOk
        if (self._implmod == GPIO._IMPLMOD_RPIGPIO):
            self._factory.cleanup( self._designator )
        elif (self._implmod == GPIO._IMPLMOD_GPIOZERO):
            ret = ErrorCode.errNotImplemented
        elif (self._implmod == GPIO._IMPLMOD_PERIPHERY):
            ret = ErrorCode.errNotImplemented
        elif (self._implmod == GPIO._IMPLMOD_SIM):
            pass
        else:
            ret = ErrorCode.errNotImplemented
        self.registerInterruptHandler(None)
        self.pin = None
        return ret

    # Switches the instance to one of the power-saving modes or recovers from
    # these modes. Situation-aware deployment of these modes can greatly reduce
    # the system's total power consumption.
    # @param[in] level <code>#RunLevel</code> The level to switch to.
    # @return An <code>#ErrorCode</code> error code either indicating that this
    # call was successful or the reason why it failed.
    def setRunLevel(self, level):
        return ErrorCode.errNotImplemented


    #
    #
    #
    def enableInterrupt(self):
        ret = ErrorCode.errOk
        if (self._implmod == GPIO._IMPLMOD_RPIGPIO):
            self._factory.add_event_detect( self._designator, self._trigger )
        elif (self._implmod == GPIO._IMPLMOD_GPIOZERO):
            ret = ErrorCode.errNotImplemented
        elif (self._implmod == GPIO._IMPLMOD_PERIPHERY):
            ret = ErrorCode.errNotImplemented
        else:
            ret = ErrorCode.errNotImplemented
        return ret
    
    #
    #
    #
    def disableInterrupt(self):
        ret = ErrorCode.errOk
        if (self._implmod == GPIO._IMPLMOD_RPIGPIO):
            self._factory.remove_event_detect( self._designator )
        elif (self._implmod == GPIO._IMPLMOD_GPIOZERO):
            ret = ErrorCode.errNotImplemented
        elif (self._implmod == GPIO._IMPLMOD_PERIPHERY):
            ret = ErrorCode.errNotImplemented
        else:
            ret = ErrorCode.errNotImplemented
        return ret

    #
    #
    #
    def get(self):
        ret = ErrorCode.errOk
        level = GPIO.LEVEL_LOW
        if (self._implmod == GPIO._IMPLMOD_RPIGPIO):
            status = self._factory.input( self._designator )
            cmpHi = self._factory.HIGH
        elif (self._implmod == GPIO._IMPLMOD_GPIOZERO):
            ret = ErrorCode.errNotImplemented
        elif (self._implmod == GPIO._IMPLMOD_PERIPHERY):
            ret = ErrorCode.errNotImplemented
        elif (self._implmod == GPIO._IMPLMOD_SIM):
            status = self._level
            cmpHi = GPIO.LEVEL_HIGH
        else:
            ret = ErrorCode.errNotImplemented
        if (ret == ErrorCode.errOk):
            if (status == cmpHi):
                level = GPIO.LEVEL_HIGH
            else:
                level = GPIO.LEVEL_LOW
        return level, ret
     
    #
    #
    #
    def set(self, newStat):
        ret = ErrorCode.errOk
        if (self._implmod == GPIO._IMPLMOD_RPIGPIO):
            self._factory.output( self._designator, self._dictLevel[newStat] )
        elif (self._implmod == GPIO._IMPLMOD_GPIOZERO):
            ret = ErrorCode.errNotImplemented
        elif (self._implmod == GPIO._IMPLMOD_PERIPHERY):
            ret = ErrorCode.errNotImplemented
        elif (self._implmod == GPIO._IMPLMOD_SIM):
            if (newStat == GPIO.LEVEL_HIGH):
                self._level = GPIO.LEVEL_HIGH
            else:
                self._level = GPIO.LEVEL_LOW
        else:
            ret = ErrorCode.errNotImplemented
        
        return ret