"""General-purpose I/O abstraction module.

Provide a convergence layer API to abstract from several different
GPIO implementing driver modules possibly installed on the target
system.
"""
__author__ = "Oliver Maye"
__version__ = "0.2"
__all__ = ["GPIO"]

import logging
import time

from philander.interruptable import Interruptable
from philander.module import Module
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode


class GPIO( Module, Interruptable ):
    """General-purpose I/O abstraction class.
    
    Provide access to and control over the underlying GPIO hardware. For
    that, an implementing driver module is used. As a convergence layer, this
    class is to hide specifics and level syntactic requirements of the
    implementing package.
    """
    
    _POLL_TIMEOUT = 1

    PINNUMBERING_BCM = "BCM"    # Pin naming by GPIOx number
    PINNUMBERING_BOARD = "BOARD"    # Pin naming by number on header

    DIRECTION_IN = 1
    DIRECTION_OUT = 2

    LEVEL_LOW = 0
    LEVEL_HIGH = 1

    PULL_DEFAULT = 0    # Don't touch, leave resistance as is
    PULL_NONE = 1       # Disable resistance
    PULL_UP = 2
    PULL_DOWN = 3

    TRIGGER_EDGE_RISING = 1
    TRIGGER_EDGE_FALLING = 2
    TRIGGER_EDGE_ANY = 3
    TRIGGER_LEVEL_HIGH = 4
    TRIGGER_LEVEL_LOW = 5

    BOUNCE_NONE = 0         # Disable de-bouncing.
    BOUNCE_DEFAULT = 200    # Default de-bounce interval in ms.

    EVENT_DEFAULT = "gpioFired"  # Specific event fired on interrupt.

    def __init__(self):
        """Initialize the instance with defaults.
        
        As part of the construction, the underlying implementation is
        determined. So, at this time, one of the supported gpio packages
        will be accessed.
        Still, note that just after construction, the instance is not
        operable, yet. Call open() to configure it and set it into a
        functional state.
        """
        self._dictDirection = {}
        self._dictLevel = {}
        self._dictPull = {}
        self._dictTrigger = {}
        self._lastEventTime = 0
        self._pin = None
        self._softDebounce = True
        self.bounce = GPIO.BOUNCE_NONE
        self.designator = None
        self.direction = GPIO.DIRECTION_OUT
        self.inverted = False
        self.isIntEnabled = False
        self.isOpen = False
        self.numScheme = GPIO.PINNUMBERING_BCM
        self.provider = SysProvider.NONE
        self.trigger = GPIO.TRIGGER_EDGE_RISING
        Interruptable.__init__(self)


    # Interrupt handling routine called by the underlying implementation 
    # upon a gpio interrupt occurrence.
    # Inform registrants by firing an event.
    #
    # :param handin: Parameter as provided by the underlying implementation
    # :type handin: implementation-specific 
    # :rtype: None
    def _callback(self, handin):
        if self._softDebounce and (self.bounce > 0):
            now = time.time() * 1000
            if (now - self._lastEventTime) > self.bounce: 
                self._lastEventTime = now
                self._fire(GPIO.EVENT_DEFAULT, handin)
        else:
            self._fire(GPIO.EVENT_DEFAULT, handin)
        return None


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
        gpio.pinNumbering     GPIO.PINNUMBERING_[BCM | BOARD]                   GPIO.PINNUMBERING_BCM
        gpio.pinDesignator    pin name or number (e.g. 17 or "GPIO17")          None
        gpio.direction        GPIO.DIRECTION_[IN | OUT]                         GPIO.DIRECTION_OUT
        gpio.inverted         [True | False]                                    False
        gpio.level            GPIO.LEVEL_[LOW | HIGH]                           GPIO.LEVEL_LOW
        gpio.pull             GPIO.PULL_[DEFAULT | NONE | UP | DOWN]            GPIO.PULL_DEFAULT (NONE)
        gpio.trigger          GPIO.TRIGGER_EDGE_[RISING | FALLING | ANY]        GPIO.TRIGGER_EDGE_RISING
        gpio.bounce           integer number, delay in milliseconds [ms]        GPIO.BOUNCE_DEFAULT
        gpio.feedback         Arbitrary. Passed on to the interrupt handler.    None
        gpio.handler          Handling routine reference.                       None
        ==================    ==============================================    =========================
        
        :param dict(str, object) paramDict: Configuration parameters as obtained from :meth:`Params_init`, possibly.
        :return: none
        :rtype: None
        """
        if not ("gpio.pinNumbering" in paramDict):
            paramDict["gpio.pinNumbering"] = GPIO.PINNUMBERING_BCM
        if not ("gpio.direction" in paramDict):
            paramDict["gpio.direction"] = GPIO.DIRECTION_OUT
        if not ("gpio.inverted" in paramDict):
            paramDict["gpio.inverted"] = False
        if not ("gpio.level" in paramDict):
            paramDict["gpio.level"] = GPIO.LEVEL_LOW
        if not ("gpio.pull" in paramDict):
            paramDict["gpio.pull"] = GPIO.PULL_DEFAULT
        if not ("gpio.trigger" in paramDict):
            paramDict["gpio.trigger"] = GPIO.TRIGGER_EDGE_RISING
        if not ("gpio.bounce" in paramDict):
            paramDict["gpio.bounce"] = GPIO.BOUNCE_DEFAULT
        if not ("gpio.feedback" in paramDict):
            paramDict["gpio.feedback"] = None
        if not ("gpio.handler" in paramDict):
            paramDict["gpio.handler"] = None
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
        self.designator = paramDict.get("gpio.pinDesignator", None)
        if self.designator is None:
            ret = ErrorCode.errInvalidParameter
        else:
            if not isinstance( self.designator, int ):
                try:
                    num = int(self.designator)
                    self.designator = num
                except ValueError:
                    pass
            self.numScheme = paramDict.get("gpio.pinNumbering", defaults["gpio.pinNumbering"])
            self.direction = paramDict.get("gpio.direction", defaults["gpio.direction"])
            self.inverted = paramDict.get("gpio.inverted", defaults["gpio.inverted"])
            if self.inverted:
                # If inverted, simply swap the entries of the level-dictionary
                self._dictLevel[GPIO.LEVEL_LOW], self._dictLevel[GPIO.LEVEL_HIGH] = self._dictLevel[GPIO.LEVEL_HIGH], self._dictLevel[GPIO.LEVEL_LOW]
            if self.direction == GPIO.DIRECTION_IN:
                self.trigger = paramDict.get("gpio.trigger", defaults["gpio.trigger"])
                self.bounce = paramDict.get("gpio.bounce", defaults["gpio.bounce"])
            self.isOpen = True
        logging.debug("GPIO base> open <%s> returns %s.", self.designator, ret)
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
        if self.isOpen:
            ret = self.registerInterruptHandler(None)
            self.isOpen = False
        else:
            ret = ErrorCode.errResourceConflict
        logging.debug("GPIO base> close <%s> returns %s.", self.designator, ret)
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
            ret = ErrorCode.errNotImplemented
        logging.debug("GPIO base> enable int for <%s> returns %s.", self.designator, ret)
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
            ret = ErrorCode.errNotImplemented
        logging.debug("GPIO base> disable int for <%s> returns %s.", self.designator, ret)
        return ret

    def get(self):
        """Retrieve the pin level.

        Gives the pin level, independent of whether the pin direction
        is set to input or output.
        
        :return: GPIO.LEVEL_HIGH, if the pin is at high level. Otherwise, GPIO.LEVEL_LOW.
        :rtype: int
        """
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
            del newLevel
            ret = ErrorCode.errNotImplemented
        return ret
