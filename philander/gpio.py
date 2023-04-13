"""General-purpose I/O abstraction module.

Provide a convergence layer API to abstract from several different
GPIO implementing driver modules possibly installed on the target
system.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["GPIO"]

import logging
from threading import Thread
import warnings

import interruptable
import module
from systypes import ErrorCode


class GPIO(module.Module, interruptable.Interruptable):
    """General-purpose I/O abstraction class.
    
    Provide access to and control over the underlying GPIO hardware. For
    that, an implementing driver module is used. Currently, RPi.GPIO,
    gpiozero and periphery are supported. As a convergence layer, this
    class is to hide specifics and level syntactic requirements of the
    implementing package.
    """
    
    _IMPLPAK_NONE = 0
    _IMPLPAK_RPIGPIO = 1
    _IMPLPAK_GPIOZERO = 2
    _IMPLPAK_PERIPHERY = 3
    _IMPLPAK_SIM = 4

    _POLL_TIMEOUT = 1

    PINNUMBERING_BCM = "BCM"    # Pin naming by GPIOx number
    PINNUMBERING_BOARD = "BOARD"    # Pin naming by number on header

    DIRECTION_IN = 1
    DIRECTION_OUT = 2

    LEVEL_LOW = 0
    LEVEL_HIGH = 1

    PULL_NONE = 0
    PULL_UP = 1
    PULL_DOWN = 2

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
        self._factory = None
        self.pin = None
        self._dictDirection = {}
        self._dictLevel = {}
        self._dictPull = {}
        self._dictTrigger = {}
        self._designator = None
        self._direction = GPIO.DIRECTION_OUT
        self._trigger = GPIO.TRIGGER_EDGE_RISING
        self._bounce = GPIO.BOUNCE_NONE
        self._fIntEnabled = False
        interruptable.Interruptable.__init__(self)
        self._implpak = self._detectDriverModule()
        self._worker = None
        self._workerDone = False

    # Figure out, which of the supported driver packages is installed.
    # Also, do the implementation-specific initialization, e.g. of
    # dictionaries.
    # Supported packages are (by priority):
    #   - RPi.GPIO
    #   - gpiozero
    #   - periphery
    # :return: One of the _IMPLPAK_xxx constants to indicate the
    #          implementation package. 
    # :rtype: int
    # :raise: warning in case that none of the supported packages could
    #        be found.
    def _detectDriverModule(self):
        ret = GPIO._IMPLPAK_NONE
        # Check for RPi.GPIO
        if ret == GPIO._IMPLPAK_NONE:
            try:
                import RPi.GPIO as gpioFactory
                self._factory = gpioFactory
                self._dictNumScheme = {
                    GPIO.PINNUMBERING_BCM: gpioFactory.BCM,
                    GPIO.PINNUMBERING_BOARD: gpioFactory.BOARD,
                }
                self._dictDirection = {
                    GPIO.DIRECTION_IN: gpioFactory.IN,
                    GPIO.DIRECTION_OUT: gpioFactory.OUT,
                }
                self._dictLevel = {
                    GPIO.LEVEL_LOW: gpioFactory.LOW,
                    GPIO.LEVEL_HIGH: gpioFactory.HIGH,
                }
                self._dictPull = {
                    GPIO.PULL_NONE: gpioFactory.PUD_OFF,
                    GPIO.PULL_DOWN: gpioFactory.PUD_DOWN,
                    GPIO.PULL_UP: gpioFactory.PUD_UP,
                }
                self._dictTrigger = {
                    GPIO.TRIGGER_EDGE_RISING: gpioFactory.RISING,
                    GPIO.TRIGGER_EDGE_FALLING: gpioFactory.FALLING,
                    GPIO.TRIGGER_EDGE_ANY: gpioFactory.BOTH,
                }
                ret = GPIO._IMPLPAK_RPIGPIO
            except ModuleNotFoundError:
                pass    # Suppress the exception, use return, instead.
        # Check for gpiozero
        if ret == GPIO._IMPLPAK_NONE:
            try:
                from gpiozero import DigitalInputDevice, DigitalOutputDevice
                self._inFactory = DigitalInputDevice
                self._outFactory = DigitalOutputDevice
                self._dictLevel = {GPIO.LEVEL_LOW: False, GPIO.LEVEL_HIGH: True}
                self._dictPull = {
                    GPIO.PULL_NONE: None,
                    GPIO.PULL_DOWN: False,
                    GPIO.PULL_UP: True,
                }
                ret = GPIO._IMPLPAK_GPIOZERO
            except ModuleNotFoundError:
                pass    # Suppress the exception, use return, instead.
        # Check for periphery
        if ret == GPIO._IMPLPAK_NONE:
            try:
                from periphery import GPIO as gpioFactory
                self._factory = gpioFactory
                self._dictDirection = {
                    GPIO.DIRECTION_IN: "in",
                    GPIO.DIRECTION_OUT: "out",
                }
                self._dictLevel = {GPIO.LEVEL_LOW: False, GPIO.LEVEL_HIGH: True}
                self._dictLevel2Dir = {GPIO.LEVEL_LOW: "low", GPIO.LEVEL_HIGH: "high"}
                self._dictPull = {
                    GPIO.PULL_NONE: "disable",
                    GPIO.PULL_DOWN: "pull_down",
                    GPIO.PULL_UP: "pull_up",
                }
                self._dictTrigger = {
                    GPIO.TRIGGER_EDGE_RISING: "rising",
                    GPIO.TRIGGER_EDGE_FALLING: "falling",
                    GPIO.TRIGGER_EDGE_ANY: "both",
                }
                ret = GPIO._IMPLPAK_PERIPHERY
            except ModuleNotFoundError:
                pass    # Suppress the exception, use return, instead.
        # Failure
        if ret == GPIO._IMPLPAK_NONE:
            warnings.warn(
                "Cannot find GPIO factory lib. Using SIM. Consider installing RPi.GPIO, gpiozero or periphery!"
            )
            self._dictLevel = {
                GPIO.LEVEL_LOW: GPIO.LEVEL_LOW,
                GPIO.LEVEL_HIGH: GPIO.LEVEL_HIGH,
            }
            ret = GPIO._IMPLPAK_SIM
        return ret

    # Interrupt handling routine called by the underlying implementation 
    # upon a gpio interrupt occurrence. Determine the source (pin) of
    # this interrupt and inform registrants by firing an event.
    #
    # :param handin: Parameter as provided by the underlying implementation
    # :type handin: implementation-specific 
    def _callback(self, handin):
        if self._implpak == GPIO._IMPLPAK_GPIOZERO:
            argDes = handin.pin.number
        else:
            argDes = handin
        super().fire(GPIO.EVENT_DEFAULT, argDes)
        return None

    # Thread working loop to poll for the pin state triggering an
    # interrupt. This is necessary in case interrupts are not natively
    # supported by the underlying implementation, such as for the
    # periphery package.
    def _workerLoop(self):
        logging.debug("gpio <%d> starts working loop.", self._designator)
        self._workerDone = False
        lastTime = 0
        while not self._workerDone:
            value = self.pin.poll(GPIO._POLL_TIMEOUT)
            if value:
                evt = self.pin.read_event()
                if (evt.timestamp - lastTime) > self._bounce * 1000000:
                    lastTime = evt.timestamp
                    logging.debug("gpio <%d> consumed event %s.", self._designator, evt)
                    self._callback(self._designator)
        logging.debug("gpio <%d> terminates working loop.", self._designator)

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
        The following options are supported.
        
        =================    ==============================================    =========================
        Key                  Range                                             Default
        =================    ==============================================    =========================
        gpio.pinNumbering    GPIO.PINNUMBERING_[BCM | BOARD]                   GPIO.PINNUMBERING_BCM
        gpio.direction       GPIO.DIRECTION_[IN | OUT]                         GPIO.DIRECTION_OUT
        gpio.level           GPIO.LEVEL_[LOW | HIGH]                           GPIO.LEVEL_LOW
        gpio.pull            GPIO.PULL_[NONE | UP | DOWN]                      GPIO.PULL_NONE
        gpio.trigger         GPIO.TRIGGER_EDGE_[RISING | FALLING | ANY]        GPIO.TRIGGER_EDGE_RISING
        gpio.bounce          integer number, delay in milliseconds [ms]        GPIO.BOUNCE_DEFAULT
        gpio.feedback        Arbitrary. Passed on to the interrupt handler.    None
        gpio.handler         Handling routine reference.                       None
        =================    ==============================================    =========================
        
        :param dict(str, object) paramDict: Configuration parameters as obtained from :meth:`Params_init`, possibly.
        :return: none
        :rtype: None
        """
        if not ("gpio.pinNumbering" in paramDict):
            paramDict["gpio.pinNumbering"] = GPIO.PINNUMBERING_BCM
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
        handler = None
        # Scan parameters
        self._designator = paramDict.get("gpio.pinDesignator", None)
        if self._designator is None:
            ret = ErrorCode.errInvalidParameter
        numScheme = paramDict.get("gpio.pinNumbering", defaults["gpio.pinNumbering"])
        self._direction = paramDict.get("gpio.direction", defaults["gpio.direction"])
        if self._direction == GPIO.DIRECTION_OUT:
            level = paramDict.get("gpio.level", defaults["gpio.level"])
        else:
            pull = paramDict.get("gpio.pull", defaults["gpio.pull"])
            self._trigger = paramDict.get("gpio.trigger", defaults["gpio.trigger"])
            self._bounce = paramDict.get("gpio.bounce", defaults["gpio.bounce"])
            feedback = paramDict.get("gpio.feedback", defaults["gpio.feedback"])
            handler = paramDict.get("gpio.handler", defaults["gpio.handler"])
        if ret == ErrorCode.errOk:
            if self._implpak == GPIO._IMPLPAK_RPIGPIO:
                self._factory.setmode(self._dictNumScheme[numScheme])
                if self._direction == GPIO.DIRECTION_OUT:
                    self._factory.setup(
                        self._designator,
                        self._factory.OUT,
                        initial=self._dictLevel[level],
                    )
                else:
                    self._factory.setup(
                        self._designator,
                        self._factory.IN,
                        pull_up_down=self._dictPull[pull],
                    )
            elif self._implpak == GPIO._IMPLPAK_GPIOZERO:
                if numScheme == GPIO.PINNUMBERING_BOARD:
                    self._designator = "BOARD" + str(self._designator)
                if self._direction == GPIO.DIRECTION_OUT:
                    self.pin = self._outFactory(
                        self._designator, initial_value=self._dictLevel[level]
                    )
                else:
                    if pull == GPIO.PULL_NONE:
                        actState = (self._trigger == GPIO.TRIGGER_EDGE_RISING) or (
                            self._trigger == GPIO.TRIGGER_LEVEL_HIGH
                        )
                    else:
                        actState = None
                    if self._bounce > 0:
                        self.pin = self._inFactory(
                            self._designator,
                            pull_up=self._dictPull[pull],
                            active_state=actState,
                            bounce_time=self._bounce,
                        )
                    else:
                        self.pin = self._inFactory(
                            self._designator,
                            pull_up=self._dictPull[pull],
                            active_state=actState,
                        )
            elif self._implpak == GPIO._IMPLPAK_PERIPHERY:
                if numScheme == GPIO.PINNUMBERING_BCM:
                    if self._direction == GPIO.DIRECTION_OUT:
                        self.pin = self._factory(
                            "/dev/gpiochip0",
                            self._designator,
                            self._dictLevel2Dir[level],
                        )
                    else:
                        self.pin = self._factory(
                            "/dev/gpiochip0",
                            self._designator,
                            self._dictDirection[GPIO.DIRECTION_IN],
                            bias=self._dictPull[pull],
                        )
                else:
                    ret = ErrorCode.errNotSupported
            elif self._implpak == GPIO._IMPLPAK_SIM:
                self._level = level
            else:
                ret = ErrorCode.errNotImplemented
        if ret == ErrorCode.errOk:
            if handler:
                ret = self.registerInterruptHandler(
                    GPIO.EVENT_DEFAULT, feedback, handler
                )
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
        ret = self.registerInterruptHandler(None)
        if self._implpak == GPIO._IMPLPAK_RPIGPIO:
            self._factory.cleanup(self._designator)
        elif self._implpak == GPIO._IMPLPAK_GPIOZERO:
            self.pin.close()
        elif self._implpak == GPIO._IMPLPAK_PERIPHERY:
            self._stopWorker()
            self.pin.close()
        elif self._implpak == GPIO._IMPLPAK_SIM:
            pass
        else:
            ret = ErrorCode.errNotImplemented
        self.pin = None
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
        if self._fIntEnabled:
            ret = ErrorCode.errOk
        else:
            if self._implpak == GPIO._IMPLPAK_RPIGPIO:
                if self._bounce > 0:
                    self._factory.add_event_detect(
                        self._designator,
                        self._dictTrigger[self._trigger],
                        callback=self._callback,
                        bouncetime=self._bounce,
                    )
                else:
                    self._factory.add_event_detect(
                        self._designator,
                        self._dictTrigger[self._trigger],
                        callback=self._callback,
                    )
                self._fIntEnabled = True
            elif self._implpak == GPIO._IMPLPAK_GPIOZERO:
                self.pin.when_activated = self._callback
                if self._trigger == GPIO.TRIGGER_EDGE_ANY:
                    self.pin.when_deactivated = self._callback
                self._fIntEnabled = True
            elif self._implpak == GPIO._IMPLPAK_PERIPHERY:
                self.pin.edge = self._dictTrigger[self._trigger]
                self._stopWorker()
                self._worker = Thread(target=self._workerLoop, name="GPIO worker")
                self._worker.start()
                self._fIntEnabled = True
            else:
                ret = ErrorCode.errNotImplemented
        return ret

    def disableInterrupt(self):
        """Disables the gpio interrupt for that pin.

        Immediately disables the interrupt for that pin. It will not
        fire an event anymore, unless :meth:`enableInterrupt` is called
        anew.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if self._fIntEnabled:
            if self._implpak == GPIO._IMPLPAK_RPIGPIO:
                self._factory.remove_event_detect(self._designator)
                self._fIntEnabled = False
            elif self._implpak == GPIO._IMPLPAK_GPIOZERO:
                from gpiozero import CallbackSetToNone

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=CallbackSetToNone)
                    self.pin.when_activated = None
                    self.pin.when_deactivated = None
                self._fIntEnabled = False
            elif self._implpak == GPIO._IMPLPAK_PERIPHERY:
                self._stopWorker()
                self.pin.edge = "none"
                self._fIntEnabled = False
            else:
                ret = ErrorCode.errNotImplemented
        else:
            ret = ErrorCode.errOk
        return ret

    def get(self):
        """Retrieve the pin level.

        Gives the pin level, independent of whether the pin direction
        is set to input or output.
        
        :return: GPIO.LEVEL_HIGH, if the pin is at high level. Otherwise, GPIO.LEVEL_LOW.
        :rtype: int
        """
        level = GPIO.LEVEL_LOW
        if self._implpak == GPIO._IMPLPAK_RPIGPIO:
            status = self._factory.input(self._designator)
        elif self._implpak == GPIO._IMPLPAK_GPIOZERO:
            status = self.pin.value
        elif self._implpak == GPIO._IMPLPAK_PERIPHERY:
            status = self.pin.read()
        elif self._implpak == GPIO._IMPLPAK_SIM:
            status = self._level
        else:
            status = 0

        if status == self._dictLevel[GPIO.LEVEL_HIGH]:
            level = GPIO.LEVEL_HIGH
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
        if self._implpak == GPIO._IMPLPAK_RPIGPIO:
            self._factory.output(self._designator, self._dictLevel[newLevel])
        elif self._implpak == GPIO._IMPLPAK_GPIOZERO:
            self.pin.value = self._dictLevel[newLevel]
        elif self._implpak == GPIO._IMPLPAK_PERIPHERY:
            self.pin.write(self._dictLevel[newLevel])
        elif self._implpak == GPIO._IMPLPAK_SIM:
            if newLevel == GPIO.LEVEL_HIGH:
                self._level = GPIO.LEVEL_HIGH
            else:
                self._level = GPIO.LEVEL_LOW
        else:
            ret = ErrorCode.errNotImplemented

        return ret
