"""Implementation of the PWM API for the RPi.GPIO lib.

An application should never use this module directly. Instead, the
system factory will provide suitable instances.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_PWM_RPi"]

from philander.gpio import GPIO
from philander.pwm import PWM
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

import RPi.GPIO as RPiGPIO


class _PWM_RPi( PWM ):
    """Implementation of the PWM interface for the GPIO.RPi lib.
    """

    def __init__(self):
        """Initialize the instance with defaults.
        """
        super().__init__()
        self._dictNumScheme = {
            GPIO.PINNUMBERING_BCM: RPiGPIO.BCM,
            GPIO.PINNUMBERING_BOARD: RPiGPIO.BOARD,
        }
        self.provider = SysProvider.RPIGPIO

    
    #
    # Module API
    #


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
        if self.isOpen:
            ret = ErrorCode.errResourceConflict
        else:
            ret = super().open( paramDict )
            if ret.isOk():
                RPiGPIO.setmode( self._dictNumScheme[self.numScheme] )
                RPiGPIO.setup( self.pinDesignator, RPiGPIO.OUT )
                self._pwm = RPiGPIO.PWM( self.pinDesignator, self.frequency )
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
        ret = super().close()
        if ret.isOk():
            RPiGPIO.cleanup(self.pinDesignator)
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
            self._pwm.ChangeFrequency( self.frequency )
        return err

    def setDuty(self, duty):
        """Set the new duty cycle percentage without altering the on/off state.

        Just update the duty value.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        err = super().setDuty( duty )
        if err.isOk():
            self._pwm.ChangeDutyCycle( self.duty )
        return err

    def start(self, duty=None):
        """Switch output of the PWM signal on.
        
        :param int duty: The new relative pulse width as a percentage in [0, 100].
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        err = super().start( duty=duty )
        if err.isOk():
            self._pwm.start( self.duty )
        return err

    def stop(self):
        """Switch output of the PWM signal off.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        err = super().stop()
        if err.isOk():
            self._pwm.stop()
        return err
