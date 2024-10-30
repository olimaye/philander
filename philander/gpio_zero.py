"""GPIO implementation using the gpiozero lib.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_GPIO_Zero"]

from gpiozero import DigitalInputDevice, DigitalOutputDevice, CallbackSetToNone
import warnings

from philander.gpio import GPIO
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode


class _GPIO_Zero( GPIO ):
    """Implementation of the GPIO abstract interface for the gpiozero lib.
    """
    
    def __init__(self):
        """Initialize the instance with defaults.
        """
        super().__init__()
        self._dictLevel = {GPIO.LEVEL_LOW: False, GPIO.LEVEL_HIGH: True}
        self._dictPull = {
            GPIO.PULL_DEFAULT: None,
            GPIO.PULL_NONE: None,
            GPIO.PULL_DOWN: False,
            GPIO.PULL_UP: True,
        }
        self._softDebounce = False
        self.provider = SysProvider.GPIOZERO


    def _callback(self, handin):
        super()._callback( handin.pin )
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
        if self.isOpen:
            ret = ErrorCode.errResourceConflict
        else:
            ret = super().open( paramDict )
        if ret.isOk():
            # Retrieve defaults
            defaults = {}
            self.Params_init(defaults)

            if self.numScheme == GPIO.PINNUMBERING_BOARD:
                self.designator = "BOARD" + str(self.designator)
            if self.direction == GPIO.DIRECTION_OUT:
                level = paramDict.get("gpio.level", defaults["gpio.level"])
                self.pin = DigitalOutputDevice( self.designator, initial_value=self._dictLevel[level] )
            else:
                pull = paramDict.get("gpio.pull", defaults["gpio.pull"])
                feedback = paramDict.get("gpio.feedback", defaults["gpio.feedback"])
                handler = paramDict.get("gpio.handler", defaults["gpio.handler"])
                actState = (self.trigger in [GPIO.TRIGGER_EDGE_RISING, GPIO.TRIGGER_LEVEL_HIGH])
                actState = (actState != self.inverted) if pull == GPIO.PULL_NONE else None
                btime = self.bounce if self.bounce > 0 else None
                self.pin = DigitalInputDevice(
                                        self.designator,
                                        pull_up=self._dictPull[pull],
                                        active_state=actState,
                                        bounce_time=btime )
                if handler:
                    ret = self.registerInterruptHandler( GPIO.EVENT_DEFAULT, feedback, handler )
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
        ret = super().close()
        if ret.isOk():
            self.pin.close()
            self.pin = None
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
            self.pin.when_activated = self._callback
            if self.trigger == GPIO.TRIGGER_EDGE_ANY:
                self.pin.when_deactivated = self._callback
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
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=CallbackSetToNone)
                self.pin.when_activated = None
                self.pin.when_deactivated = None
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
            level = GPIO.LEVEL_HIGH if self.pin.value == self._dictLevel[GPIO.LEVEL_HIGH] else GPIO.LEVEL_LOW
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
            self.pin.value = self._dictLevel[newLevel]
            ret = ErrorCode.errOk
        return ret
