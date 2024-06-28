"""Driver implementation for the L6924D/U battery chargers.

More information on the functionality of the chip can be found at
the ST website under e.g. https://www.st.com/en/power-management/l6942d.html
"""
__author__ = "Carl Bellgardt"
__version__ = "0.1"
__all__ = ["L6924"]

from .charger import Charger, Status, ChargerError, TemperatureRating
from .battery import Status as BatStatus
from .gpio import GPIO
from .systypes import ErrorCode

class L6924(Charger):
    """L6924 driver implementation.

    This implementation was tested using STEVAL-ISA076V1 board (based on L6924D) but also should work for other devices.
    This implementation does only read information on two gpio pins, and thus cannot communicate with the charger in any way.
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
            "gpio.pull": GPIO.PULL_UP,
            "gpio.inverted": True
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
        In this case the two GPIO-Pins for reading the charger status
        are initialized.
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
        st1_params = {} # collector requires pull-up to be readable
        st2_params = {}
        for key, value in paramDict.items():
            if key.startswith("L6924.St1"):
                st1_params[key.replace("L6924.St1.", '')] = value
            elif key.startswith("L6924.St2"):
                st2_params[key.replace("L6924.St2.", '')] = value
        # open GPIO pins
        if err == ErrorCode.errOk:
            err = self._pinSt1.open(st1_params)
        if err == ErrorCode.errOk:
            err = self._pinSt2.open(st2_params)
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
        
        As there is nothing to reset, this routine does not execute an actual reset.
        It is just here to fulfill the interface.
        
        The device is in some default state, afterwards and must be
        re-configured according to the application's needs.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errOk # nothing to do here
    
    def getInfo(self):
        """Retrieves an information block from the charging device.
        
        This device does not report any static information.

        :return: The information object and an error code indicating either success or the reason of failure.
        :rtype: Info, ErrorCode
        """
        return None, ErrorCode.errOk
    
    def isBatteryPresent(self):
        """Checks, if the battery is present.
        
        Because there is only one error code without any differentiation,
        if Error.errUnavailable is returned, it could be the case, that there is no battery present.
        Specifically the following is true:
        If there is no battery present, this function will return Error.errUnavailable.
        If the function returns Error.errUnavailable, the reason could also be a high/low temperature, a faulty battery
        or that the time limit has elapsed.
        If the chip is not powered, it will always return ErrorCode.errOk, guessing that there is a battery present.
        
        Returns :attr:`ErrorCode.errOk` if a battery is present,
        :attr:`ErrorCode.errUnavailable` if the battery could possibly not be present.\
        This can not be exactly determined, because there is only one error state,\
        which could indicate that the battery is not present, but which also could indicate\
        another problem.
        
        See also: :meth:`getChgStatus`.

        :return: An error code.
        :rtype: ErrorCode
        """
        err = ErrorCode.errOk if getChgStatus() != Status.unknown else Error.errUnavailable
        return err
    
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
        chg_status = getChgStatus()
        if chg_status == Status.off:
            status = BatStatus.unknown
        elif chg_status == Status.fastCharge:
            status = BatStatus.low | BatStatus.empty
        elif chg_status == Status.done:
            status = BatStatus.nomal
        else:
            status = BatStatus.removed | BatStatus.broken | BatStatus.problemThermal
        return status
    
    def getChgStatus(self):
        """Retrieves the charging phase or status.
        
        :return: A charger status code to indicate the current charger status.
        :rtype: charger.Status
        """
        st1 = self._pinSt1.get() # collector state is the inverted state of internal transistor (GPIO.inverted should be true)
        st2 = self._pinSt2.get() # (see data sheet table for possible states)
        
        if not (st1 or st2):
            status = Status.off
        elif (not st1) and st2:
            status = Status.done
        elif st1 and (not st2):
            status = Status.fastCharge # The board only outputs a general charging status, thus this could mean any kind of charging
        else:
            status = Status.unknown # this could indicate any error
        return status

    def getDCStatus(self):
        """Retrieves the DC supply status.

        This device does not indicate it's status.
        The given status is guessed based on the ChgStatus.

        :return: A status code to indicate the DC supply status.
        :rtype: DCStatus
        """
        chg_status = getChgStatus()
        if chg_status == Status.off:
            status = DCStatus.off
        elif chg_status == Status.fastCharge:
            status = DCStatus.valid
        elif chg_status == Status.done:
            status = DCStatus.nomal
        else:
            status = DCStatus.unknown
        return status
    
    def getPowerSrc(self):
        """Retrieves the power source, that presumably drives the\
        system at the moment that this function is executed.
        
        This device does not report it's power source.
        The given status is guessed based on the ChgStatus.
        
        :return: A code to indicate the power source.
        :rtype: PowerSrc
        """
        chg_status = getChgStatus()
        if chg_status == Status.off:
            status = PowerSrc.bat
        elif chg_status == Status.fastCharge:
            status = PowerSrc.dc
        elif chg_status == Status.done:
            status = PowerSrc.dcBat
        else:
            status = PowerSrc.unknown
        return status

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
        The given status is guessed based on the ChgStatus.
        If the charger status is ok, the battery temperature is assumed to be ok too.
        If the charger status is indicating any problem, the temperature rating is assumed to be unknown.

        :return: A rating code to indicate the temperature rating of the battery element.
        :rtype: TemperatureRating
        """
        chg_status = getChgStatus()
        if chg_status == Status.unknown:
            status = TemperatureRating.unknown
        else:
            status = TemperatureRating.ok
        return status

    def getError(self):
        """Determines the error state for the charger chip, if one.

        Because this device only has one error status, ChargerError.bat indicates any kind of error
        e.g. thermal problems, battery absent or charge timer expired.

        :return: A charger error code to further describe reason for the error.
        :rtype: ChargerError
        """
        err = ChargerError.ok if getChgStatus() != Status.unknown else ChargerError.bat 
        return err

    def restartCharging(self):
        """Tries to restart the charging phase.
        
        This device does not support manual control of the charging process.

        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errOk # nothing to do here

    