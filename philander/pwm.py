"""Abstraction module for the pulse-width-modulation feature.

Provide a convergence layer API to abstract from several different
PWM implementing driver modules provided on the target system.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["PWM"]

import logging

from philander.gpio import GPIO
from philander.module import Module
from philander.sysfactory import SysProvider, SysFactory
from philander.systypes import ErrorCode


class PWM( Module ):
    """Pulse-width-modulation abstraction class.
    
    Provide access to and control over the underlying PWM hardware. For
    that, an implementing driver module is used. As a convergence layer,
    this class is to hide specifics and to level syntactic requirements
    of the implementing package.
    """

    # Static constants, independent from the implementation
    
    # State of the PWM output
    OFF = 0     # PWM output is off             
    ON  = 1     # PWM output is working

    DEFAULT_FREQUENCY = 100000  # default pulse frequency in Hertz
    DEFAULT_DUTY = 50           # default relative pulse width in percent.

    
    @staticmethod
    def getPWM( provider=SysProvider.AUTO ):
        """Generates a PWM implementation according to the requested provider.
        
        :param SysProvider provider: The low-level lib to rely on, or AUTO\
        for automatic detection.
        :return: A PWM implementation object, or None in case of an error.
        :rtype: PWM
        """
        deps = [(SysProvider.MICROPYTHON, "machine", "PWM"),
                (SysProvider.PERIPHERY, "periphery", "PWM"),
                (SysProvider.RPIGPIO, "RPi.GPIO", "PWM"),
                ]
        impls = {
                  SysProvider.MICROPYTHON:  ("philander.pwm_micropython", "_PWM_Micropython"),
                  SysProvider.PERIPHERY:    ("philander.pwm_periphery", "_PWM_Periphery"),
                  SysProvider.RPIGPIO:      ("philander.pwm_rpi", "_PWM_RPi"),
                }
        if provider == SysProvider.AUTO:
            provider = SysFactory.autoDetectProvider( deps )
        ret = SysFactory.createInstance( provider, impls )
        return ret

    
    def __init__(self):
        """Initialize the instance with defaults.
        
        Note that just after construction, the instance is not
        operable, yet. Call :meth:`open` to configure it and set it
        into a functional state.
        """
        self._pwm = None
        self.duty = PWM.DEFAULT_DUTY
        self.frequency = PWM.DEFAULT_FREQUENCY
        self.isOpen = False
        self.numScheme = GPIO.PINNUMBERING_BCM
        self.pin = None
        self.provider = SysProvider.NONE
        self.state = PWM.OFF

    #
    # Module API
    #

    @classmethod
    def Params_init(cls, paramDict):
        """Initialize parameters with their defaults.

        The given dictionary should not be None, on entry.
        Options not present in the dictionary will be added and set to
        their defaults on return.
        The following options are supported.
        
        ==================    ==============================================    ===============================
        Key                   Range                                             Default
        ==================    ==============================================    ===============================
        pwm.pinNumbering      GPIO.PINNUMBERING_[BCM | BOARD]                   GPIO.PINNUMBERING_BCM
        pwm.pinDesignator     pin name or number (e.g. 2 or "2")                None
        pwm.frequency         pulse frequency in Hz; integer                    :attr:`DEFAULT_FREQUENCY`
        pwm.duty              duty cycle in percent [%]; integer                :attr:`DEFAULT_DUTY`
        ==================    ==============================================    ===============================
        
        :param dict(str, object) paramDict: Configuration parameters as obtained from :meth:`Params_init`, possibly.
        :return: none
        :rtype: None
        """
        defaults = {
            "pwm.pinNumbering": GPIO.PINNUMBERING_BCM,
            "pwm.frequency":    PWM.DEFAULT_FREQUENCY,
            "pwm.duty":         PWM.DEFAULT_DUTY,
        }
        for key, value in defaults.items():
            if not key in paramDict:
                paramDict[key] = value
        return None


    def open(self, paramDict):
        """Opens the instance and sets it in a usable state.

        Allocate necessary hardware resources and configure
        user-adjustable parameters to meaningful defaults.
        This function must be called prior to any further usage of the
        instance. Involving it in the system ramp-up procedure could be
        a good choice. After usage of this instance is finished, the
        application should call :meth:`close`.
        
        :param dict(str, object) paramDict: Configuration parameters as\
        obtained from :meth:`Params_init`, possibly.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        # Retrieve defaults
        self.Params_init(paramDict)
        # Scan parameters
        self.pin = paramDict.get("pwm.pinDesignator", None)
        if self.pin is None:
            ret = ErrorCode.errFewData
        else:
            if not isinstance( self.pin, int ):
                try:
                    num = int(self.pin)
                    self.pin = num
                except ValueError:
                    pass
            self.state = PWM.OFF
            self.numScheme = paramDict.get("pwm.pinNumbering")
            val = paramDict.get("pwm.frequency")
            if isinstance(val, int) and (0 < val):
                self.frequency = val
            else:
                ret = ErrorCode.errInvalidParameter
            if ret.isOk():
                val = paramDict.get("pwm.duty")
                if isinstance(val, int) and (0 <= val) and (val <= 100):
                    self.duty = val
                else:
                    ret = ErrorCode.errInvalidParameter
        if ret.isOk():
            self.isOpen = True
        logging.debug("PWM base> open <%s> returns %s.", self.pin, ret)
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
            self.stop()
            self.isOpen = False
            self._pwm = None
        else:
            ret = ErrorCode.errResourceConflict
        logging.debug("PWM base> close <%s> returns %s.", self.pin, ret)
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

    #
    # PWM specific API
    #

    def getState(self):
        """Retrieve the state of this PWM instance.

        Gives :attr:`PWM.ON` if this instance is up and running
        (started) or :attr:`PWM.OFF` otherwise.
        
        :return: A status value [PWM.ON | PWM.OFF] and\
        an error code indicating either success or the reason of failure.
        :rtype: int, ErrorCode
        """
        err = ErrorCode.errOk
        if not self.isOpen:
            err = ErrorCode.errResourceConflict
        return self.state, err

    def setFrequency(self, frequency):
        """Set the new base frequency. Does not alter the on/off state.

        Just update the frequency value.
        If the PWM is off, it stays off and just stores the new frequency.
        When starting the PWM at a later point, the signal will have
        this new base frequency.
        If the PWM is running (on) while calling this method, the new
        frequency will immediately affect the output signal.
        
        It's at the discretion of the implementation whether or not
        special values (e.g. 0) will cause side effects, like
        switching the PWM off or on. The caller should not rely on this
        kind of side effects, but use :meth:`start` or :meth:`stop`,
        instead.      
        
        :param int frequency: Positive int value giving the new frequency in Hertz [Hz].
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        err = ErrorCode.errOk
        if not self.isOpen:
            err = ErrorCode.errResourceConflict
        # Type checking
        elif not isinstance(frequency, int):
            try:
                fval = float(frequency)
                frequency = int( fval + 0.5 )
            except ValueError:
                err = ErrorCode.errInvalidParameter
        # Range checking
        if err.isOk():
            if (frequency < 1):
                err = ErrorCode.errSpecRange
            else:
                self.frequency = frequency
        return err

    def setDuty(self, duty):
        """Set the new duty cycle percentage without altering the on/off state.

        Just update the duty value.
        If the PWM is off, it stays off and just stores the new duty cycle.
        When starting the PWM again, the signal will show this new duty
        cycle.
        If the PWM is running while calling this method, the new
        duty value will immediately affect the output signal.
        
        A duty cycle of 0 or 100 will effectively switch the PWM off. 
        Still, the caller should prefer using :meth:`start` or
        :meth:`stop` for this purpose, instead.
        
        
        :param int duty: A value [0...100] giving the new duty cycle as\
        a percentage [%].
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        err = ErrorCode.errOk
        if not self.isOpen:
            err = ErrorCode.errResourceConflict
        # Type checking
        elif not isinstance(duty, int):
            try:
                duty = int( duty + 0.5 )
            except ValueError:
                err = ErrorCode.errInvalidParameter
        # Range checking
        if err.isOk():
            self.duty = 0 if (duty<0) else 100 if (duty>100) else duty
        return err

    def start(self, duty=None):
        """Switch output of the PWM signal on.
        
        If the status is currently OFF, the output starts immediately
        and the status turns to ON. If no parameter is given, the
        configured duty value is used. Alternatively, the new
        duty percentage can be specified as a parameter.
        If the PWM is already running (ON), the output signal is just
        updated. If a new duty value is given, it will apply to the
        relative pulse width. Otherwise, the output signal will not
        change.
        
        Note that setting the duty value to zero or 100 will effectively
        turn the PWM off.

        :param int duty: The new relative pulse width as a percentage in [0, 100].
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        err = ErrorCode.errOk
        if not self.isOpen:
            err = ErrorCode.errResourceConflict
        elif duty is not None:
            err = self.setDuty(duty)
        if err.isOk():
            self.state = PWM.ON
        return err

    def stop(self):
        """Switch output of the PWM signal off.
        
        Immediately stops the output of the PWM signal.
        The configured duty value is not modified.
        Operation can be re-started by calling :meth:`start`.

        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        err = ErrorCode.errOk
        if not self.isOpen:
            err = ErrorCode.errResourceConflict
        else:
            self.state = PWM.OFF
        return err
