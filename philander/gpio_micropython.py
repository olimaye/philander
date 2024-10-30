"""GPIO implementation for the Micropython environment.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_GPIO_Micropython"]

from machine import Pin
import time

from philander.gpio import GPIO
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode


class _GPIO_Micropython( GPIO ):
    """Implementation of the GPIO abstract interface for the Micropython environment.
    """
    
    def __init__(self):
        """Initialize the instance with defaults.
        """
        super().__init__()
        self._dictDirection = {
            GPIO.DIRECTION_IN: Pin.IN,
            GPIO.DIRECTION_OUT: Pin.OUT,
        }
        self._dictLevel = {GPIO.LEVEL_LOW: 0, GPIO.LEVEL_HIGH: 1}
        self._dictPull = {
            GPIO.PULL_DEFAULT: None,
            GPIO.PULL_NONE: None,
            GPIO.PULL_DOWN: Pin.PULL_DOWN,
            GPIO.PULL_UP: Pin.PULL_UP,
        }
        self._dictTrigger = {
            GPIO.TRIGGER_EDGE_RISING: Pin.IRQ_RISING,
            GPIO.TRIGGER_EDGE_FALLING: Pin.IRQ_FALLING,
            GPIO.TRIGGER_EDGE_ANY: (Pin.IRQ_RISING | Pin.IRQ_FALLING),
            #GPIO.TRIGGER_LEVEL_HIGH: Pin.IRQ_HIGH_LEVEL,
            #GPIO.TRIGGER_LEVEL_LOW: Pin.IRQ_LOW_LEVEL,
        }
        self._irq = None
        self.provider = SysProvider.MICROPYTHON


    def _callback(self, handin):
        if self.bounce > 0:
            now = time.ticks_ms()
            if time.ticks_diff(now, self._lastEventTime) > self.bounce:
                self._lastEventTime = now
                self._fire(GPIO.EVENT_DEFAULT, handin)
        else:
            self._fire(GPIO.EVENT_DEFAULT, handin)
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
        wasOpen = self.isOpen
        ret = super().open( paramDict )
        if ret.isOk():
            # Retrieve defaults
            defaults = {}
            self.Params_init(defaults)

            if self.direction == GPIO.DIRECTION_IN:
                pull = paramDict.get("gpio.pull", defaults["gpio.pull"])
                feedback = paramDict.get("gpio.feedback", defaults["gpio.feedback"])
                handler = paramDict.get("gpio.handler", defaults["gpio.handler"])
                if wasOpen:
                    self.pin.init( mode = self._dictDirection[self.direction],
                                   pull = self._dictPull[pull]  )
                else:
                    self.pin = Pin( self.designator,
                                    mode = self._dictDirection[self.direction],
                                    pull = self._dictPull[pull]  )
                if handler:
                    ret = self.registerInterruptHandler( GPIO.EVENT_DEFAULT, feedback, handler )
            else:
                level = paramDict.get("gpio.level", defaults["gpio.level"])
                if wasOpen:
                    self.pin.init( mode = self._dictDirection[self.direction],
                                   value= level )
                else:
                    self.pin = Pin( self.designator,
                                    mode = self._dictDirection[self.direction],
                                    value= level )
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
            ret = self.registerInterruptHandler(None)
            # self.pin = None
            # Don't do so, as to allow for re-opening the same instance. 
        else:
            ret = ErrorCode.errResourceConflict
        return ret

    def enableInterrupt(self):
        """Enables the gpio interrupt for that pin.

        If the pin is configured for input, enables the interrupt for
        that pin. Depending on the trigger configured during :meth:`open`,
        an event will be fired the next time when the condition is
        satisfied.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if not self.isOpen:
            ret = ErrorCode.errResourceConflict
        elif self.isIntEnabled:
            ret = ErrorCode.errOk
        else:
            self._irq = self.pin.irq( handler=self._callback, trigger=self._dictTrigger[self.trigger] )
            self.isIntEnabled = True
        return ret

    def disableInterrupt(self):
        """Disables the gpio interrupt for that pin.

        Immediately disables the interrupt for that pin. It will not
        _fire an event anymore, unless :meth:`enableInterrupt` is called
        anew.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if not self.isOpen:
            ret = ErrorCode.errResourceConflict
        elif not self.isIntEnabled:
            ret = ErrorCode.errOk
        else:
            self.pin.irq( handler=None )
            self._irq = None
            self.isIntEnabled = False
        return ret

    def get(self):
        """Retrieve the pin level.

        Gives the pin level, independent of whether the pin direction
        is set to input or output.
        
        :return: GPIO.LEVEL_HIGH, if the pin is at high level. Otherwise, GPIO.LEVEL_LOW.
        :rtype: int
        """
        if self.isOpen:
            level = GPIO.LEVEL_HIGH if self.pin.value() == self._dictLevel[GPIO.LEVEL_HIGH] else GPIO.LEVEL_LOW
        else:
            level = GPIO.LEVEL_LOW
        return level

    def set(self, newLevel):
        """Sets the pin to the given level.

        Outputs the given level at this pin. Does not work, if this pin
        is set to input direction.
        
        :param int newLevel: The new level to set this pin to. Must be one of GPIO.LEVEL_[HIGH | LOW].
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if not self.isOpen:
            ret = ErrorCode.errResourceConflict
        else:
            self.pin.value( self._dictLevel[newLevel] )
            ret = ErrorCode.errOk
        return ret
