"""Implementation of the PWM API for the Periphery lib.

An application should never use this module directly. Instead, the
system factory will provide suitable instances.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_PWM_Periphery"]

from philander.pwm import PWM
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

from periphery import PWM as Driver, PWMError as DriverError


class _PWM_Periphery( PWM ):
    """Implementation of the PWM interface for the Periphery lib.
    """

    def __init__(self):
        """Initialize the instance with defaults.
        """
        super().__init__()
        self.chippath = None
        self.provider = SysProvider.PERIPHERY


    #
    # Module API
    #

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
        pwm.chippath          GPIO chip character device path as a string.      "/dev/gpiochip0"
        ==================    ==============================================    =========================
        
        :param dict(str, object) paramDict: Configuration parameters as obtained from :meth:`Params_init`, possibly.
        :return: none
        :rtype: None
        """
        super().Params_init( paramDict )
        defaults = {
            "pwm.chippath":     "/dev/gpiochip0",
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
        
        :param dict(str, object) paramDict: Configuration parameters as obtained from :meth:`Params_init`, possibly.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        if self.isOpen:
            ret = ErrorCode.errResourceConflict
        else:
            ret = super().open( paramDict )
            if ret.isOk():
                self.chippath = paramDict.get("gpio.chippath")
                try:
                    self._pwm = Driver( self.chippath, self.pin )
                    self._pwm.frequency = self.frequency
                    self._pwm.duty_cycle = self.duty / 100
                except DriverError:
                    ret = ErrorCode.errLowLevelFail
                except (TypeError, ValueError):
                    ret = ErrorCode.errInvalidParameter
                except LookupError:
                    ret = ErrorCode.errUnavailable
                except TimeoutError:
                    ret = ErrorCode.errInitFailed
            if ret.isOk() and (self._pwm is None):
                ret = ErrorCode.errLowLevelFail
            self.isOpen = ret.isOk()
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
            self._pwm.close()
        ret = super().close()
        return ret


    #
    # PWM specific API
    #

    def setFrequency(self, frequency):
        """Set the new duty frequency. Does not alter the on/off state.

        Just update the frequency value.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        err = super().setFrequency( frequency )
        if err.isOk():
            try:
                self._pwm.frequency = self.frequency
            except DriverError:
                err = ErrorCode.errLowLevelFail
            except TypeError:
                err = ErrorCode.errInvalidParameter
        return err
                

    def setDuty(self, duty):
        """Set the new duty cycle percentage without altering the on/off state.

        Just update the duty value.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        err = super().setDuty( duty )
        if err.isOk():
            try:
                self._pwm.duty_cycle = self.duty / 100
            except DriverError:
                err = ErrorCode.errLowLevelFail
            except (TypeError, ValueError):
                err = ErrorCode.errInvalidParameter
        return err

    def start(self, duty=None):
        """Switch output of the PWM signal on.
        
        :param int duty: The new relative pulse width as a percentage in [0, 100].
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        err = super().start( duty=duty )
        if err.isOk():
            try:
                self._pwm.duty_cycle = self.duty / 100
                self._pwm.enable()
            except DriverError:
                err = ErrorCode.errLowLevelFail
            except (TypeError, ValueError):
                err = ErrorCode.errInvalidParameter
        return err

    def stop(self):
        """Switch output of the PWM signal off.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        err = super().stop()
        if err.isOk():
            self._pwm.disable()
        return err
