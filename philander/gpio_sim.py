"""GPIO implementation using the built-in simulation model.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_GPIO_Sim"]

import logging
from threading import Thread
import time

from philander.gpio import GPIO
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode


class _GPIO_Sim( GPIO ):
    """Implementation of the GPIO abstract interface using the built-in simulation.
    """
    
    def __init__(self):
        """Initialize the instance with defaults.
        """
        super().__init__()
        self._dictLevel = {
            GPIO.LEVEL_LOW: GPIO.LEVEL_LOW,
            GPIO.LEVEL_HIGH: GPIO.LEVEL_HIGH,
        }
        self._level = GPIO.LEVEL_LOW
        self._worker = None
        self._workerDone = False
        self.provider = SysProvider.SIM


    # _callback() is intentionally ommitted here, to activate super class method.

    # Thread working loop to poll for the pin state triggering an
    # interrupt. This is necessary in case interrupts are not natively
    # supported by the underlying implementation, such as for the
    # periphery package.
    def _workerLoop(self):
        logging.debug("gpio <%d> starts working loop.", self.designator)
        self._workerDone = False
        lastLevel = self.get()
        while not self._workerDone:
            newLevel = self.get()
            if self.trigger == GPIO.TRIGGER_EDGE_RISING:
                alarm = (lastLevel==GPIO.LEVEL_LOW) and (newLevel==GPIO.LEVEL_HIGH)
            elif self.trigger == GPIO.TRIGGER_EDGE_FALLING:
                alarm = (lastLevel==GPIO.LEVEL_HIGH) and (newLevel==GPIO.LEVEL_LOW)
            elif self.trigger == GPIO.TRIGGER_EDGE_ANY:
                alarm = (lastLevel != newLevel)
            elif self.trigger == GPIO.TRIGGER_LEVEL_HIGH:
                alarm = (newLevel==GPIO.LEVEL_HIGH)
            elif self.trigger == GPIO.TRIGGER_LEVEL_LOW:
                alarm = (newLevel==GPIO.LEVEL_LOW)
            lastLevel = newLevel
            if alarm:
                self._callback(self._pin)
        logging.debug("gpio <%d> terminates working loop.", self.designator)

    # Stop the worker thread, if appropriate.
    def _stopWorker(self):
        if self._worker:
            if self._worker.is_alive():
                self._workerDone = True
                self._worker.join()
            self._worker = None



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

            if self.direction == GPIO.DIRECTION_OUT:
                self._level = paramDict.get("gpio.level", defaults["gpio.level"])
            else:
                feedback = paramDict.get("gpio.feedback", defaults["gpio.feedback"])
                handler = paramDict.get("gpio.handler", defaults["gpio.handler"])
                if handler:
                    ret = self.registerInterruptHandler( GPIO.EVENT_DEFAULT, feedback, handler )
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
            if self.direction == GPIO.DIRECTION_OUT:
                level = self._dictLevel[self._level]
            else:
                value = time.time()
                value = int(value) % 3
                level = GPIO.LEVEL_HIGH if value==0 else GPIO.LEVEL_LOW
                level = self._dictLevel[level]
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
            self._level = self._dictLevel.get( newLevel, GPIO.LEVEL_LOW )
            ret = ErrorCode.errOk
        return ret
