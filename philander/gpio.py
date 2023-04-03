"""General-purpose I/O abstraction module.

Provide a convergence layer API to abstract from several different
GPIO implementing driver modules possibly installed on the target
system.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["GPIO"]

from systypes import ErrorCode
from Module import Module
from Interruptable import Interruptable
from threading import Thread
import logging
import warnings


class GPIO(Module, Interruptable):
    """General-purpose I/O abstraction class.
    
    Provide access to and control over the underlying GPIO hardware. For
    that, an implementing driver module is used. Currently, RPi.gpio,
    gpiozero and periphery are supported. As a convergence layer, this
    class is to hide specifics and level syntactic requirements of the
    implementing module.
    """
    
    _IMPLMOD_NONE = 0
    _IMPLMOD_RPIGPIO = 1
    _IMPLMOD_GPIOZERO = 2
    _IMPLMOD_PERIPHERY = 3
    _IMPLMOD_SIM = 4

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
        
        Note that just after construction, the instance is not operable,
        yet. Call open() to configure it and set it into a functional
        state.
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
        Interruptable.__init__(self)
        self._implmod = self._detectDriverModule()
        self._worker = None
        self._workerDone = False

    # Figure out, which of the supported driver packages is installed.
    # Also, do the implementation-specific initialization, e.g. of
    # dictionaries.
    # Supported packages are (by priority):
    #   - RPi.GPIO
    #   - gpiozero
    #   - periphery
    # :return: One of the One of the _IMPLMOD_xxx constants to
    #          indicate the implementation package. 
    # :rtype: int
    def _detectDriverModule(self):
        ret = GPIO._IMPLMOD_NONE
        # Check for RPi.GPIO
        if ret == GPIO._IMPLMOD_NONE:
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
                ret = GPIO._IMPLMOD_RPIGPIO
            except ModuleNotFoundError:
                pass    # Suppress the exception, use return, instead.
        # Check for gpiozero
        if ret == GPIO._IMPLMOD_NONE:
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
                # self._dictTrigger = {GPIO.TRIGGER_EDGE_RISING: gpioFactory.RISING, GPIO.TRIGGER_EDGE_FALLING: gpioFactory.FALLING, GPIO.TRIGGER_EDGE_ANY: gpioFactory.BOTH}
                ret = GPIO._IMPLMOD_GPIOZERO
            except ModuleNotFoundError:
                pass    # Suppress the exception, use return, instead.
        # Check for periphery
        if ret == GPIO._IMPLMOD_NONE:
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
                ret = GPIO._IMPLMOD_PERIPHERY
            except ModuleNotFoundError:
                pass    # Suppress the exception, use return, instead.
        # Failure
        if ret == GPIO._IMPLMOD_NONE:
            warnings.warn(
                "Cannot find GPIO factory lib. Using SIM. Consider installing RPi.GPIO, gpiozero or periphery!"
            )
            self._dictLevel = {
                GPIO.LEVEL_LOW: GPIO.LEVEL_LOW,
                GPIO.LEVEL_HIGH: GPIO.LEVEL_HIGH,
            }
            ret = GPIO._IMPLMOD_SIM
        return ret

    #
    #
    #
    def _callback(self, param):
        if self._implmod == GPIO._IMPLMOD_GPIOZERO:
            argDes = param.pin.number
        else:
            argDes = param
        super().fire(GPIO.EVENT_DEFAULT, argDes)
        return None

    #
    #
    #
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

    #
    def _stopWorker(self):
        if self._worker:
            if self._worker.is_alive():
                self._workerDone = True
                self._worker.join()
            self._worker = None

    # Initialize parameters with its defaults.
    # @param[in, out] paramDict The parameter structure to be initialized. Should not be NULL.
    # @return <code>None</code>
    @classmethod
    def Params_init(cls, paramDict):
        """[Brief]

        [Description]
        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        :raises [ErrorType]: [ErrorDescription]
        :return: [ReturnDescription]
        :rtype: [ReturnType]
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
            if self._implmod == GPIO._IMPLMOD_RPIGPIO:
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
            elif self._implmod == GPIO._IMPLMOD_GPIOZERO:
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
            elif self._implmod == GPIO._IMPLMOD_PERIPHERY:
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
            elif self._implmod == GPIO._IMPLMOD_SIM:
                self._level = level
            else:
                ret = ErrorCode.errNotImplemented
        if ret == ErrorCode.errOk:
            if handler:
                ret = self.registerInterruptHandler(
                    GPIO.EVENT_DEFAULT, feedback, handler
                )
        return ret

    # Closes this instance and releases associated hardware resources. This is the
    # counterpart of #open.
    # Upon return, further usage of this instance is prohibited and may lead to
    # unexpected results. The instance can be re-activated by calling #open,
    # again.
    # @return <code>None</code>
    def close(self):
        ret = ErrorCode.errOk
        ret = self.registerInterruptHandler(None)
        if self._implmod == GPIO._IMPLMOD_RPIGPIO:
            self._factory.cleanup(self._designator)
        elif self._implmod == GPIO._IMPLMOD_GPIOZERO:
            self.pin.close()
        elif self._implmod == GPIO._IMPLMOD_PERIPHERY:
            self._stopWorker()
            self.pin.close()
        elif self._implmod == GPIO._IMPLMOD_SIM:
            pass
        else:
            ret = ErrorCode.errNotImplemented
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
        if self._fIntEnabled:
            ret = ErrorCode.errOk
        else:
            if self._implmod == GPIO._IMPLMOD_RPIGPIO:
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
            elif self._implmod == GPIO._IMPLMOD_GPIOZERO:
                self.pin.when_activated = self._callback
                if self._trigger == GPIO.TRIGGER_EDGE_ANY:
                    self.pin.when_deactivated = self._callback
                self._fIntEnabled = True
            elif self._implmod == GPIO._IMPLMOD_PERIPHERY:
                self.pin.edge = self._dictTrigger[self._trigger]
                self._stopWorker()
                self._worker = Thread(target=self._workerLoop, name="GPIO worker")
                self._worker.start()
                self._fIntEnabled = True
            else:
                ret = ErrorCode.errNotImplemented
        return ret

    #
    #
    #
    def disableInterrupt(self):
        ret = ErrorCode.errOk
        if self._fIntEnabled:
            if self._implmod == GPIO._IMPLMOD_RPIGPIO:
                self._factory.remove_event_detect(self._designator)
                self._fIntEnabled = False
            elif self._implmod == GPIO._IMPLMOD_GPIOZERO:
                from gpiozero import CallbackSetToNone

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=CallbackSetToNone)
                    self.pin.when_activated = None
                    self.pin.when_deactivated = None
                self._fIntEnabled = False
            elif self._implmod == GPIO._IMPLMOD_PERIPHERY:
                self._stopWorker()
                self.pin.edge = "none"
                self._fIntEnabled = False
            else:
                ret = ErrorCode.errNotImplemented
        else:
            ret = ErrorCode.errOk
        return ret

    #
    #
    #
    def get(self):
        level = GPIO.LEVEL_LOW
        if self._implmod == GPIO._IMPLMOD_RPIGPIO:
            status = self._factory.input(self._designator)
        elif self._implmod == GPIO._IMPLMOD_GPIOZERO:
            status = self.pin.value
        elif self._implmod == GPIO._IMPLMOD_PERIPHERY:
            status = self.pin.read()
        elif self._implmod == GPIO._IMPLMOD_SIM:
            status = self._level
        else:
            status = 0

        if status == self._dictLevel[GPIO.LEVEL_HIGH]:
            level = GPIO.LEVEL_HIGH
        else:
            level = GPIO.LEVEL_LOW
        return level

    #
    #
    #
    def set(self, newStat):
        ret = ErrorCode.errOk
        if self._implmod == GPIO._IMPLMOD_RPIGPIO:
            self._factory.output(self._designator, self._dictLevel[newStat])
        elif self._implmod == GPIO._IMPLMOD_GPIOZERO:
            self.pin.value = self._dictLevel[newStat]
        elif self._implmod == GPIO._IMPLMOD_PERIPHERY:
            self.pin.write(self._dictLevel[newStat])
        elif self._implmod == GPIO._IMPLMOD_SIM:
            if newStat == GPIO.LEVEL_HIGH:
                self._level = GPIO.LEVEL_HIGH
            else:
                self._level = GPIO.LEVEL_LOW
        else:
            ret = ErrorCode.errNotImplemented

        return ret
