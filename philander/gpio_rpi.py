"""GPIO implementation using the RPi.GPIO lib.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_GPIO_RPi"]

import logging
import RPi.GPIO as RPiGPIO

from philander.gpio import GPIO
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

# Disable RuntimeWarning: This channel is already in use ...
RPiGPIO.setwarnings(False)

class _GPIO_RPi( GPIO ):
    """Implementation of the GPIO abstract interface for the RPi.GPIO lib.
    """
    
    def __init__(self):
        """Initialize the instance with defaults.
        """
        super().__init__()
        self._dictNumScheme = {
            GPIO.PINNUMBERING_BCM: RPiGPIO.BCM,
            GPIO.PINNUMBERING_BOARD: RPiGPIO.BOARD,
        }
        self._dictDirection = {
            GPIO.DIRECTION_IN: RPiGPIO.IN,
            GPIO.DIRECTION_OUT: RPiGPIO.OUT,
        }
        self._dictLevel = {
            GPIO.LEVEL_LOW: RPiGPIO.LOW,
            GPIO.LEVEL_HIGH: RPiGPIO.HIGH,
        }
        self._dictPull = {
            GPIO.PULL_DEFAULT: RPiGPIO.PUD_OFF,
            GPIO.PULL_NONE: RPiGPIO.PUD_OFF,
            GPIO.PULL_DOWN: RPiGPIO.PUD_DOWN,
            GPIO.PULL_UP: RPiGPIO.PUD_UP,
        }
        self._dictTrigger = {
            GPIO.TRIGGER_EDGE_RISING: RPiGPIO.RISING,
            GPIO.TRIGGER_EDGE_FALLING: RPiGPIO.FALLING,
            GPIO.TRIGGER_EDGE_ANY: RPiGPIO.BOTH,
        }
        self._softDebounce = False
        self.provider = SysProvider.RPIGPIO


    # _callback() is intentionally ommitted here, to activate super class method.


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
            logging.warning("GPIO_RPi:open> pin #%s already open.", self.designator)
            ret = ErrorCode.errResourceConflict
        else:
            ret = super().open( paramDict )
        if ret.isOk():
            # Retrieve defaults
            defaults = {}
            self.Params_init(defaults)

            # With RPi.GPIO, it may happen that abandoned references to instances
            # of this class still block hardware resources. This results in a
            # RuntimeWarning: This channel is already in use, continuing anyway...
            RPiGPIO.setmode( self._dictNumScheme[self.numScheme] )
            if self.direction == GPIO.DIRECTION_OUT:
                logging.debug("GPIO_RPi:open> pin #%s is output.", self.designator)
                level = paramDict.get("gpio.level", defaults["gpio.level"])
                RPiGPIO.setup( self.designator, RPiGPIO.OUT, initial=self._dictLevel[level] )
            else:
                pull = paramDict.get("gpio.pull", defaults["gpio.pull"])
                feedback = paramDict.get("gpio.feedback", defaults["gpio.feedback"])
                handler = paramDict.get("gpio.handler", defaults["gpio.handler"])
                logging.debug("GPIO_RPi:open> pin #%s is input, pull=%s.", self.designator, self._dictPull[pull])
                RPiGPIO.setup( self.designator, RPiGPIO.IN, pull_up_down=self._dictPull[pull] )
                # Kill zombie registrations that may exist
                RPiGPIO.remove_event_detect(self.designator)
                if handler:
                    ret = self.registerInterruptHandler( GPIO.EVENT_DEFAULT, feedback, handler )
        logging.info("GPIO_RPi:open> pin #%s returns %s.", self.designator, ret)
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
            if not self.designator is None:
                logging.debug("GPIO_RPi:close> pin #%s, direction=%s.",
                              self.designator, self.direction)
                RPiGPIO.cleanup(self.designator)
        logging.info("GPIO_RPi:close> pin #%s returns %s.", self.designator, ret)
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
            logging.warning("GPIO_RPi:enableInterrupt> pin #%s not open.", self.designator)
            ret = ErrorCode.errResourceConflict
        elif self.isIntEnabled:
            logging.warning("GPIO_RPi:enableInterrupt> pin #%s INT already enabled.", self.designator)
            ret = ErrorCode.errOk
        else:
            logging.debug("GPIO_RPi:enableInterrupt> pin #%s, bounce=%s.", self.designator, self.bounce)
            if self.bounce > 0:
                RPiGPIO.add_event_detect( self.designator,
                                          self._dictTrigger[self.trigger],
                                          callback=self._callback,
                                          bouncetime=self.bounce )
            else:
                RPiGPIO.add_event_detect( self.designator,
                                          self._dictTrigger[self.trigger],
                                          callback=self._callback )
            self.isIntEnabled = True
        logging.info("GPIO_RPi:enableInterrupt> pin #%s returns %s.", self.designator, ret)
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
            logging.warning("GPIO_RPi:disableInterrupt> pin #%s not open.", self.designator)
            ret = ErrorCode.errResourceConflict
        elif not self.isIntEnabled:
            logging.warning("GPIO_RPi:disableInterrupt> pin #%s INT not enabled.", self.designator)
            ret = ErrorCode.errOk
        else:
            logging.debug("GPIO_RPi:disableInterrupt> pin #%s disabling INT.", self.designator)
            # At RPi.GPIO v0.7.1a4, this seems to be buggy, as it produces "Speicherzugriffsfehler"
            # RPiGPIO.remove_event_detect( self.designator )
            self.isIntEnabled = False
        logging.info("GPIO_RPi:disableInterrupt> pin #%s returns %s.", self.designator, ret)
        return ret

    def get(self):
        """Retrieve the pin level.

        Gives the pin level, independent of whether the pin direction
        is set to input or output.
        
        :return: GPIO.LEVEL_HIGH, if the pin is at high level. Otherwise, GPIO.LEVEL_LOW.
        :rtype: int
        """
        if self.isOpen:
            value = RPiGPIO.input(self.designator)
            level = GPIO.LEVEL_HIGH if value == self._dictLevel[GPIO.LEVEL_HIGH] else GPIO.LEVEL_LOW
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
            RPiGPIO.output( self.designator, self._dictLevel[newLevel] )
            ret = ErrorCode.errOk
        return ret
