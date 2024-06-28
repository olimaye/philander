"""Driver implementation for the L6924 battery chargers.

More information on the functionality of the chip can be found at
the ST website under e.g. https://www.st.com/en/power-management/l6942d.html
"""
__author__ = "Carl Bellgardt"
__version__ = "0.1"
__all__ = ["L6924"]

from .charger import Charger, Status, ChargerError
from .battery import Status as BatStatus
from .gpio import GPIO
from .systypes import ErrorCode

class L6924(Charger):
    """L6924 driver implementation.
    This implementation was ttested using STEVAL-ISA076V1 board (based on L6924D) but also should work for other devices.
    """

    def __init__(self):
        self._pinSt1 = None
        self._pinSt2 = None

    @classmethod
    def Params_init(cls, paramDict):
        """Initializes configuration parameters with defaults.
        
        The following settings are supported:
        
        =================================    ==========================================================================================================
        Key name                             Value type, meaning and default
        =================================    ==========================================================================================================
        All L6924.[St1 | St2].gpio.* settings as documented at :meth:`.GPIO.Params_init`.
        ===============================================================================================================================================
        
        Also see: :meth:`.Charger.Params_init`, :meth:`.SerialBusDevice.Params_init`, :meth:`.GPIO.Params_init`. 
        """
        gpio_dict = {
            "gpio.direction": GPIO.DIRECTION_IN,
            "gpio.pull": GPIO.PULL_UP
            }
        GPIO.Params_init(gpio_dict)
        for key, value in gpio_dict.items():
            for pin in ["L6924.St1.", "L6924.St2."]:
                if not ((pin + key) in paramDict.keys()):
                    paramDict[pin + key] = value
        return paramDict

    def open(self, paramDict):
        """Opens the instance and sets it in a usable state.

        Allocate necessary hardware resources and configure
        user-adjustable parameters to meaningful defaults.
        This function must be called prior to any further usage of the
        instance. Involving it in the system ramp-up procedure could be
        a good choice. After usage of this instance is finished, the
        application should call :meth:`close`.
        
        :param paramDict(str, object) paramDict: Configuration parameters as obtained from :meth:`Params_init`, possibly.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        err = ErrorCode.errOk
        self.Params_init(paramDict)
        # init St1 and St2
        self._pinSt1 = GPIO()
        self._pinSt2 = GPIO()
        St1_params = {"gpio.pull": GPIO.PULL_UP} # collector requires pull-up to be readable
        St2_params = {"gpio.pull": GPIO.PULL_UP}
        for key, value in paramDict.items():
            if key.startswith("L6924.St1"):
                St1_params[key.replace("L6924.St1.", '')] = value
            elif key.startswith("L6924.St2"):
                St2_params[key.replace("L6924.St2.", '')] = value
        # check if mandatory parameter are given
        for param in ["gpio.pinDesignator", "gpio.direction"]:
            for pin_params in [St1_params, St2_params]:
                if param not in pin_params.keys():
                    err = ErrorCode.errInvalidParameter
                    break
        # open GPIO pins
        if err == ErrorCode.errOk:
            err = self._pinSt1.open(St1_params)
        if err == ErrorCode.errOk:
            err = self._pinSt2.open(St2_params)
        return err
        
    def close(self):
        """Shut down the device after usage.
        
        This method should be called when the device is not used, anymore,
        e.g. as part of the application exit procedure.
        The following steps are executed:
        
        * close GPIO pins for st1 and st1
        
        After return, the device can still be re-used, by calling
        :meth:`.open` again.
        
        Also see: :meth:`.GPIO.close`, :meth:`.Module.close`.
        """
        err = self._pinSt1.close()
        if err == ErrorCode.errOk:
            err = self._pinSt2.close()
        return err

    def reset(self):
        """Soft resets the device.
        
        The device is in some default state, afterwards and must be
        re-configured according to the application's needs.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errNotImplemented
    
    def getInfo(self):
        """Retrieves an information block from the charging device.
        
        This device does not report any static information.

        :return: The information object and an error code indicating either success or the reason of failure.
        :rtype: Info, ErrorCode
        """
        return ErrorCode.errNotImplemented
    
    def isBatteryPresent(self):
        """Checks, if the battery is present.
        
        This does not tell anything about whether the battery is charged
        or not.
        
        Returns :attr:`ErrorCode.errOk` if a battery is present,
        :attr:`ErrorCode.errUnavailable` if the battery could possibly not be present.\
        This can not be exactly determined, because there is only one error state,\
        which could indicate that the battery is not present, but which also could indicate\
        another problem.
        
        See also: :meth:`getChgStatus`.

        :return: An error code.
        :rtype: ErrorCode
        """
        return ErrorCode.errOk if getChgStatus() != Status.unknown else Error.errUnavailable
    
    def getNumCells(self):
        """Retrieves the number of battery cells configured.
        
        This board only supports one cell.

        :return: The number of cells.
        :rtype: int
        """
        return 1
    
    def getBatStatus(self):
        """Get the battery status to tell about the health and state of the battery.
        
        Returns one of the :class:`.battery.Status` values to indicate
        battery voltage level or presence or health state.
        Because of the very limited output, this will only return the states\
        Status.normal (charging, etc.) and Status.problemPhysical (Battery absent, too hot, etc.)

        :return: The battery state.
        :rtype: battery.Status
        """
        return BatStatus.normal if getChgStatus() != Status.unknown else BatStatus.problemPhysical
    
    def getChgStatus(self):
        """Retrieves the charging phase or status.
        
        :return: A charger status code to indicate the current charger status.
        :rtype: charger.Status
        """
        st1 = not self._pinSt1.get() # collector state is the inverted state of internal transistor
        st2 = not self._pinSt2.get() # (see data sheet table for possible states)
        
        if not any((st1, st2)):
            status = Status.off
        elif not st1 and st2:
            status = Status.done
        elif st1 and not st2:
            status = Status.fastCharge # The board only outputs a general charging status, thus this could mean any kind of charging
        else:
            status = Status.unknown # this could indicate any error
        return status

    def getDCStatus(self):
        """Retrieves the DC supply status.

        This device does not indicate it's status.

        :return: A status code to indicate the DC supply status.
        :rtype: DCStatus
        """
        return DCStatus.unknown
    
    def getPowerSrc(self):
        """Retrieves the power source, that presumably drives the\
        system at the moment that this function is executed.
        
        This device does not report it's power source.
        
        :return: A code to indicate the power source.
        :rtype: PowerSrc
        """
        return PowerSrc.unknown

    def getChargerTempStatus(self):
        """Retrieves the charger's temperature state.

        This device does not report it's temperature.

        :return: A rating code to indicate the temperature rating of the charger chip.
        :rtype: TemperatureRating
        """
        return TemperatureRating.unknown


    def getBatteryTempStatus(self):
        """Retrieves the battery's temperature status.

        This device does not report on the battery's temperature.

        :return: A rating code to indicate the temperature rating of the battery element.
        :rtype: TemperatureRating
        """
        return TemperatureRating.unknown

    def getError(self):
        """Determines the error state for the charger chip, if one.

        Because this device only has one error status, ChargerError.bat could indicate any kind of error\
        e.g. thermal problems, battery absent or timer expired.

        :return: A charger error code to further describe reason for the error.
        :rtype: ChargerError
        """
        return ChargerError.ok if getChgStatus() != Status.unknown else ChargerError.bat 

    def restartCharging(self):
        """Tries to restart the charging phase.
        
        This device does not support manual control of the charging process.

        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errNotImplemented

    