"""GPIO implementation using the periphery lib.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_GPIO_Periphery"]

import logging
from periphery import GPIO as PerGPIO, GPIOError as PerGPIOError
from threading import Thread

from philander.gpio import GPIO
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode


class _GPIO_Periphery( GPIO ):
    """Implementation of the GPIO abstract interface for the periphery lib.
    """
    
    def __init__(self):
        """Initialize the instance with defaults.
        """
        super().__init__()
        self._dictDirection = {
            GPIO.DIRECTION_IN: "in",
            GPIO.DIRECTION_OUT: "out",
        }
        self._dictLevel = {GPIO.LEVEL_LOW: False, GPIO.LEVEL_HIGH: True}
        self._dictLevel2Dir = {GPIO.LEVEL_LOW: "low", GPIO.LEVEL_HIGH: "high"}
        self._dictPull = {
            GPIO.PULL_DEFAULT: "default",
            GPIO.PULL_NONE: "disable",
            GPIO.PULL_DOWN: "pull_down",
            GPIO.PULL_UP: "pull_up",
        }
        self._dictTrigger = {
            GPIO.TRIGGER_EDGE_RISING: "rising",
            GPIO.TRIGGER_EDGE_FALLING: "falling",
            GPIO.TRIGGER_EDGE_ANY: "both",
        }
        self._worker = None
        self._workerDone = False
        self.chippath = None
        self.pin = None
        self.provider = SysProvider.PERIPHERY


    def _callback(self, handin):
        if self._softDebounce and (self._bounce > 0):
            evt = self.pin.read_event()
            now = evt.timestamp / 1000000
            if (now - self._lastEventTime) > self._bounce: 
                self._lastEventTime = now
                self._fire(GPIO.EVENT_DEFAULT, handin)
        else:
            self._fire(GPIO.EVENT_DEFAULT, handin)
        return None

    # Thread working loop to poll for the pin state triggering an
    # interrupt. This is necessary in case interrupts are not natively
    # supported by the underlying implementation, such as for the
    # periphery package.
    def _workerLoop(self):
        logging.debug("_GPIO_Periphery #%d starts working loop.", self.designator)
        self._workerDone = False
        while not self._workerDone:
            value = self.pin.poll(GPIO._POLL_TIMEOUT)
            if value:
                self._callback(self.pin)
        logging.debug("_GPIO_Periphery #%d terminates working loop.", self.designator)

    # Stop the worker thread, if appropriate.
    def _stopWorker(self):
        if self._worker:
            if self._worker.is_alive():
                self._workerDone = True
                self._worker.join()
            self._worker = None


    @classmethod
    def Params_init(cls, paramDict):
        """Initialize parameters with their defaults.

        The given dictionary should not be None, on entry.
        Options not present in the dictionary will be added and set to
        their defaults on return.
        Additionally to the super class parameters, the following
        options are supported.
        
        ==================    ==============================================    =========================
        Key                   Range                                             Default
        ==================    ==============================================    =========================
        gpio.chippath         GPIO chip character device path as a string.      "/dev/gpiochip0"
        ==================    ==============================================    =========================
        
        :param dict(str, object) paramDict: Configuration parameters as obtained from :meth:`Params_init`, possibly.
        :return: none
        :rtype: None
        """
        super().Params_init( paramDict )
        if not ("gpio.chippath" in paramDict):
            paramDict["gpio.chippath"] = "/dev/gpiochip0"
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
            self.chippath = paramDict.get("gpio.chippath", defaults["gpio.chippath"])
            if self.numScheme == GPIO.PINNUMBERING_BCM:
                if self.direction == GPIO.DIRECTION_OUT:
                    level = paramDict.get("gpio.level", defaults["gpio.level"])
                    try:
                        self.pin = PerGPIO( self.chippath, self.designator,
                                            self._dictLevel2Dir[level] )
                    except PerGPIOError as e:
                        logging.debug("_GPIO_Periphery.open() failed. chip: %s, designator: %s, error: %s.",
                                      self.chippath, self.designator, e)
                        ret = ErrorCode.errInitFailed
                else:
                    pull = paramDict.get("gpio.pull", defaults["gpio.pull"])
                    feedback = paramDict.get("gpio.feedback", defaults["gpio.feedback"])
                    handler = paramDict.get("gpio.handler", defaults["gpio.handler"])
                    self.pin = PerGPIO( self.chippath, self.designator,
                                        self._dictDirection[GPIO.DIRECTION_IN],
                                        bias=self._dictPull[pull] )
                    if handler:
                        ret = self.registerInterruptHandler( GPIO.EVENT_DEFAULT, feedback, handler )
            else:
                ret = ErrorCode.errNotSupported
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
            self._stopWorker()
            if self.pin:
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
            self.pin.edge = self._dictTrigger[self.trigger]
            self._stopWorker()
            self._worker = Thread(target=self._workerLoop, name="GPIO worker")
            self._worker.start()
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
            self._stopWorker()
            self.pin.edge = "none"
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
            level = GPIO.LEVEL_HIGH if self.pin.read() == self._dictLevel[GPIO.LEVEL_HIGH] else GPIO.LEVEL_LOW
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
            self.pin.write( self._dictLevel[newLevel] )
            ret = ErrorCode.errOk
        return ret
