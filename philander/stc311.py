# TODO: all the comments

# -*- coding: utf-8 -*-
"""A module to provide base classes and data types for gas gauge driver implementations.
"""
__author__ = "Carl Bellgardt"
__version__ = "0.1"
__all__ = ["STC311", "ChipType"]

from enum import auto
from .serialbus import SerialBusDevice
from .gasgauge import GasGauge, SOCChangeRate
from .battery import Status as BatStatus, Level as BatLevel
from .primitives import Current, Voltage, Percentage, Temperature
from .systypes import ErrorCode, RunLevel, Info, Enum
from .stc311_reg import STC3115_Reg, STC3117_Reg, ModeValues, CtrlValues


class ChipType(Enum):
    STC3115 = auto()
    STC3117 = auto()


class OperatingMode(Enum):
    opModeUnknown = auto()
    opModeStandby = auto()
    opModeVoltage = auto()
    opModeMixed = auto()


class STC311(GasGauge, SerialBusDevice):
    """This is a driver base class for a gas gauge IC.
    
    A gas gauge allows to keep track of the state of charge
    (SOC), remaining capacity, current voltage etc. of a battery.
    """

    REGISTER = None
    ADDRESSES_ALLOWED = [0x70]

    @classmethod
    def Params_init(cls, paramDict):
        """Initializes configuration parameters with defaults.
        
        The following settings are supported:
        
        =================================    ==========================================================================================================
        Key name                             Value type, meaning and default
        =================================    ==========================================================================================================
        See def_dict
        ===============================================================================================================================================
        
        Also see: :meth:`.Charger.Params_init`, :meth:`.SerialBusDevice.Params_init`, :meth:`.GPIO.Params_init`. 
        """
        def_dict = {
            "Gausgauge.chip_type": ChipType.STC3115,
            "SerialBusDevice.address": cls.ADDRESSES_ALLOWED[0],
            "Gasgauge.gpio_alarm_idx": None,
            "Gasgauge.gpio_cd_idx": None,
            "Gasgauge.senseResistor": 10,  # Sense resistor in milli Ohm
            "Gasgauge.cc_cnf": 395,
            "Gasgauge.vm_cnf": 321,
            "Gasgauge.alarm_soc": 2,  # SOC alarm level [0.5%]
            "Gasgauge.alarm_voltage": 170,  # 3.0 V
            "Gasgauge.current_thres": 10,  # +/-470 V drop
            "Gasgauge.cmonit_max": 120,  # CC-VM: 4 minutes; VM->CC: 1 minute
            "Gasgauge.battery_idx": None
        }
        def_dict.update(paramDict)
        paramDict.update(def_dict)  # update again to apply changes to original reference
        return None

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
        self.Params_init(paramDict)
        err = ErrorCode.errOk
        if paramDict["Gasgauge.chip_type"] == ChipType.STC3115:
            self.REGISTER = STC3115_Reg  # TODO: make this dynamic, maybe via a conf?
        elif paramDict["Gasgauge.chip_type"] == ChipType.STC3117:
            self.REGISTER = STC3117_Reg
        else:
            err = ErrorCode.errInvalidParameter
        self._initialize()
        if err == ErrorCode.errOk:  # Extend ErrorCode class to have a ok() function to replace all these occurrences
            err = SerialBusDevice.open(self, {"SerialBusDevice.address": self.ADDRESSES_ALLOWED[0]})
        if err == ErrorCode.errOk:  # TODO: should I check for err or use .isAttached?
            # SerialBusDevice is attached
            self.callback = None  # TODO: implement callback functionality here
            # TODO: init gpio with params etc
            # TODO: gpio set callback
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
        self.setRunLevel(RunLevel.shutdown)
        err = SerialBusDevice.close(self)
        # TODO: also call close for GPIO (interrupt stuff).
        return err

    def getInfo(self):
        """Retrieves an information block from the gas gauge device.
        
        Typically, this kind of information is rather static in that,
        it does not change over time. Usually, this information is
        somewhat unique for the charger origin, manufacturing date,
        hardware/firmware revision, product/model ID, chip series and alike.
        For that reason, this function can be used to see,
        if communication works reliably.

        For more dynamic meta-information see :meth:`getStatus`.
        
        The method returns both, an instance of :class:`Info`, carrying
        the information block as well as an error code, indicating
        success or failure. The info block shall be evaluated only, if
        the method returned successfully.
        Even then, the caller should still evaluate the ``validity``
        attribute of the returned info block to find out, which of the
        information is actually valid.
        
        :return: The information object and an error code indicating either success or the reason of failure.
        :rtype: Info, ErrorCode
        """
        info = Info()
        chip_id, err = self.readByteRegister(self.REGISTER.REG_ID)
        return info, err

    def getStatus(self, statusID):
        """Retrieves status data from the device.
        
        Typically, this kind of information is more dynamic in that, it
        changes (much) over time. Usually, it further describes the
        IC's current shape and condition, such as the availability of
        new data, the cause of an interrupt or the status of
        certain hardware functions. Also, secondary measurements such as
        the die temperature could be subject to status data.
        
        For more static meta-information see :meth:`getInfo`.
        
        The given ``statusID`` parameter specifies, exactly which status
        information should be retrieved. Its type and interpretation
        depends on the implementation.
        
        The method returns both, resulting status data and an error code
        indicating success or failure. The status data should be considered
        valid only, if the error code indicates a successful execution
        of this method.
        
        The type and interpretation of the status data depends on the
        specific implementation.

        :param int statusID: Identifies the status information to be retrieved.
        :return: The status object and an error code indicating either success or the reason of failure.
        :rtype: Object, ErrorCode
        """
        del statusID
        # TODO: not implemented yet
        return None, ErrorCode.errNotSupported

    def getBatteryVoltage(self):
        """Retrieves the battery voltage in milli Volt.
        
        :return: A on-negative integer value [mV] or :attr:`Voltage.invalid`\
        to indicate that this information could not be retrieved.
        :rtype: Voltage
        """
        voltage, err = self.readWordRegister( self.REGISTER.REG_VOLTAGE)
        ret = Voltage(voltage) if (err == ErrorCode.errOk) else Voltage.invalid
        return ret

    def getBatteryCurrent(self):
        """Retrieves the battery current in micro Ampere at the time this\
        function is executed.
        
        See also: :meth:`getBatteryCurrentAvg`
        
        :return: A on-negative integer value [µA] or :attr:`Current.invalid`\
        to indicate that this information could not be retrieved.
        :rtype: Current
        """
        current, err = self.readWordRegister( self.REGISTER.REG_CURRENT)
        ret = Current(current) if (err == ErrorCode.errOk) else Current.invalid
        return ret

    def getBatteryCurrentAvg(self):
        """Retrieves the average battery current.
        
        The average is taken over some time interval, e.g. 2 seconds.
        The length of the time window is at the discretion of the
        implementation and cannot be adjusted by the caller.
        
        See also: :meth:`getBatteryCurrent`

        TODO: what non-ascii sign is supposed to be there
        :return: A on-negative integer value [�A] or :attr:`Current.invalid`\
        to indicate that this information could not be retrieved.
        :rtype: Current
        """
        # TODO: not implemented yet
        return Current.invalid

    def rateSOC(self, soc):
        """Convert a continuous SOC percentage into its next-lower battery level predicate.
        
        Does not retrieve any information from the underlying hardware.

        :param Percentage soc: The state of charge, given in percent.
        :return: The next-lower battery level mnemonic.
        :rtype: battery.Level
        """
        blvl = BatLevel(soc)
        if blvl >= BatLevel.full:
            ret = BatLevel.full
        elif blvl >= BatLevel.good:
            ret = BatLevel.good
        elif blvl >= BatLevel.medium:
            ret = BatLevel.medium
        elif blvl >= BatLevel.low:
            ret = BatLevel.low
        elif blvl >= BatLevel.empty:
            ret = BatLevel.empty
        else:
            ret = BatLevel.deepDischarge
        return ret

    def getRatedSOC(self):
        """Retrieve the current state of charge as a discrete battery level predicate.

        :return: The next-lower battery level corresponding to the current SOC.
        :rtype: battery.Level
        """
        soc = self.getStateOfCharge()
        lvl = self.rateSOC(soc)
        return lvl

    def getRatedSOCStr(self):
        """Retrieve the remaining capacity as a battery level string.

        :return: The next-lower battery level corresponding to the current SOC.
        :rtype: String
        """
        lvl = self.getRatedSOC()
        lvl_str = str(lvl)
        return lvl_str

    def alarmCallback(self, pinIndex):
        # TODO: not implemented yet
        # TODO:? how exactly should the alarm callback functionality be implemented?: implement interruptable
        # see alarmCallback from original implementation and max77960
        pass

    # Local functions for internal use

    @staticmethod
    def _transferSOC(data):
        # LSB is 1/512 %, so shift by 9 bits.
        ret = data + 0x0100 >> 9
        return Percentage(ret)

    @staticmethod
    def _transferChangeRate(data):  # STC3117 exclusive
        # LSB is 8.789 mC, scaling factor is 8.789 = 8789/1000
        ret = (data * 8789 + 500) / 1000
        return ret

    @staticmethod
    def _transferVoltage(data):
        # LSB is 2.2mV, so scale by factor 2.20 = 22/10
        ret = (data * 22 + 5) / 10
        return Voltage(ret)

    @staticmethod
    def _transferCurrent(data):
        # Actually, we read out the voltage drop over the sense resistor.
        # LSB is 5.88V, so first scaling factor is 5.88 = 294/50
        # Value is signed!
        # R = U/I  so we get I = U/R; Note that R is given in milliOhm!
        # So, finally we scale by 294 / 50 * 1000 / rs = 294 * 20 / rs = 5880 / rs.
        rs = None  # TODO:? rs is stored in the device context (original implementation), how should this be done now?: rs = sContext[devIdx].senseResistor
        # -> give as configuration parameter and store in object
        if data >= 0:
            ret = (data * 5880 + (rs / 2)) / rs
        else:
            ret = (data * 5880 - (rs / 2)) / rs
        return ret

    # TODO: STC3117 exclusive
    # /**
    #  * AVG_CURRENT transfer function
    #  */
    def _transferCurrentAvg(self, data):
        # Again, we actually read out the voltage drop over the sense resistor.
        # LSB is 1.47V, partial scaling factor is 1.47 = 147/100
        # Value is signed!
        # Total scaling factor is: 147 / 100 * 1000 / rs = 147 * 10 / rs = 1470 / rs.
        # TODO: rs = sContext[devIdx].senseResistor;
        rs = None
        if data >= 0:
            ret = (data * 1470 + rs/2) / rs
        else:
            ret = (data * 1470 - rs/2) / rs
        return ret

    @staticmethod
    def _transferTemperature(data):
        # LSB is 1C, so we don't need any scaling.
        return Temperature(data)

    @staticmethod
    def _transfertOCV(data):
        # LSB is 0.55 mV, so scale by factor 0.55 = 55/100 = 11/20.
        ret = (data * 11 + 10) / 20
        return Voltage(ret)

    @staticmethod
    def _invTransferOCV(value):
        # LSB is 0.55 mV, so scale by factor 1/0.55 = 100/55 = 20/11.
        ret = (value * 20 + 5) / 11
        return ret

    @staticmethod
    def _crc(data, length):
        ret = 0
        for idx in range(length):
            ret ^= data[idx]
        return ret

    @staticmethod
    def _checkRamConsistency(self, data, length):
        # TODO: why is length never used? Refer to original implementation to see, what it does
        IDX_RAM_CRC = None  # TODO: should this be part of STC3115_Reg?
        # check if RAM test register value is correct
        if data[self.REGISTER.IDX_RAM_TEST] != self.REGISTER.RAM_TEST:
            ret = ErrorCode.errCorruptData
        else:
            code = self._crc(data, self.REGISTER.RAM_SIZE - 1)
            if code != data[IDX_RAM_CRC]:
                ret = ErrorCode.errCorruptData
            else:
                ret = ErrorCode.errOk
        return ret

    def _getOperatingMode(self):
        # TODO: read about and understand modes and mode config
        err, data = SerialBusDevice.readByteRegister(self,  self.REGISTER.REG_MODE)
        if err == ErrorCode.errOk:
            if data and ModeValues.GG_RUN:
                if data and ModeValues.VMODE:
                    ret = OperatingMode.opModeVoltage
                else:
                    ret = OperatingMode.opModeMixed
            else:
                ret = OperatingMode.opModeStandby
        else:
            ret = OperatingMode.opModeUnknown
        return ret

    def _checkID(self):
        CHIP_ID = self.REGISTER.CHIP_ID
        err, data = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_ID)
        if err == ErrorCode.errOk:
            err = ErrorCode.errOk if (data == CHIP_ID) else ErrorCode.errFailure
        return err

    #
    # /**
    #  * Start-up the chip and fill/restore configuration registers
    #  */
    def _initialize(self):
        pass  # TODO: implement

    # API functions exported to the outside

    def _setRunLevel(self, level):
        mode = ModeValues.OFF
        if level in [RunLevel.active, RunLevel.idle]:  # TODO: not sure if this is the best "pythonic^TM" way
            # Mixed mode: coloumb counter + voltage gas gauge -> Leave VMODE off
            mode = ModeValues.OFF | ModeValues.GG_RUN | ModeValues.FORCE_CC  # TODO: figure out where to put those modes (are they in systypes or smth?)
            if self.callbackfunction is not None:
                mode |= ModeValues.ALM_ENA
            ret = ErrorCode.errOk
        elif level in [RunLevel.relax, RunLevel.snooze, RunLevel.nap, RunLevel.sleep, RunLevel.deepSleep]:
            # Power saving mode: voltage gas gauge, only. -> VMODE = 1
            mode = ModeValues.OFF | ModeValues.VMODE | ModeValues.GG_RUN | ModeValues.FORCE_VM
            if self.callbackfunction is not None:  # TODO: implement proper callback functionality
                mode |= ModeValues.ALM_ENA
            ret = ErrorCode.errOk
        elif level == RunLevel.shutdown:
            # ret = backupRam(self)
            mode = ModeValues.VMODE | ModeValues.FORCE_VM
            ret = ErrorCode.errOk
        else:
            ret = ErrorCode.errNotSupported
        # set mode and return ErrorCode
        if ret == ErrorCode.errOk:
            ret = SerialBusDevice.writeByteRegister(self,  self.REGISTER.REG_MODE, mode)
        return ret

    # Gas gauge specific API implementation

    def reset(self):
        """Soft resets the device.

        The device is in some default state, afterwards and must be
        re-configured according to the application's needs.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        # UNDOCUMENTED: At the end of the reset phase, the MODE_GG_RUN bit is cleared.
        # In order to detect this, we have to set it, first:
        data, err = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_MODE)
        if err == ErrorCode.errOk and not (data & ModeValues.GG_RUN):
            err, data = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_MODE)
            data |= ModeValues.GG_RUN  # TODO:? do not understand what this does
            # -> read again, this is a write, not read
            # same applies for beneath
        # Do a soft reset by asserting CTRL:PORDET
        if err == ErrorCode.errOk:
            err, data = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_CTRL)
            # TODO:? do not understand at all what is happening here :( Isn't there supposed to be a reference given? Why then is there this logic in the original implementation at that place?
        # Delay: Loop until we see the MODE_GG_RUN bit cleared:
        if err == ErrorCode.errOk:
            # TODO:? how should this waiting loop be implemented?
            pass
        # Then, re-initialize the device
        if err == ErrorCode.errOk:
            err = STC311._initialize(self)
        return err

    def getID(self):
        data, err = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_ID)
        ret = data if err == ErrorCode.errOk else err
        return ret

    def getStateOfCharge(self):
        """Retrieves the state of charge.
        That is the fraction of electric energy from the total capacity,
        that is still or already stored in the battery. This information
        is valid for both, the charging and the discharging process.

        :return: A percentage [0...100] value or :attr:`Percentage.invalid`\
        to indicate that this information could not be retrieved.
        :rtype: Percentage
        """
        # SOC is a 16bit value with LSB = 1/512 %
        # But reading just the high-byte results in an inconsistent response.
        # So, read the full word.
        data, err = SerialBusDevice.readWordRegister(self, self.REGISTER.REG_SOC)
        if err == ErrorCode.errOk:
            ret = self._transferSOC(data)
            # future RAM-functions could be implemented here
            # if ret != Percentage.invalid:
            #    updateRamWord(self,  self.REGISTER._IDX_RAM_SOC)
        else:
            ret = Percentage.invalid
        return ret

    def getChangeRate(self):  # function is STC3117 exclusive
        """Retrieves the SOC change rate in milli C.

        Remember that 1C = 100% in 1 hour. This information may be used
        to estimate the remaining stamina or how long the charging
        process will still take.
        :return: A SOC change rate (non-negative) or :attr:'SOCChangeRate.invalid`\
        to indicate that this information could not be retrieved.
        :rtype: SOCChangeRate
        """
        if self.REGISTER.CHIP_TYPE != ChipType.STC3117:  # STC3117 exclusive
            ret = SOCChangeRate.invalid
        else:
            opMode = self._getOperatingMode()
            if opMode == opMode.opModeVoltage:
                data, err = SerialBusDevice.readWordRegister(self, self.REGISTER._REG_AVG_CURRENT)
                if err == ErrorCode.errOk:
                    ret = self._transferChangeRate(data)
                else:
                    ret = SOCChangeRate.invalid
            else:
                ret = SOCChangeRate.invalid
        return ret

    def getBatteryTemperature(self):
        # This device does not measure any temperature data
        return Temperature.invalid

    def getChipTemperature(self):
        """Retrieve the current temperature of the chip.

        :return: Temperature value.
        :rtype: Temperature
        """
        data, err = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_TEMPERATURE)
        if err == ErrorCode.errOk:
            ret = self._transferTemperature(data)
        else:
            ret = Temperature.invalid
        return ret

    # Interruptable API implementation

    def _registerInterruptHandler(self, callback):
        if self.callback is not None:  # Enable; from app (=sink) to hardware (=source)
            self.callback = callback
            self._enableInterrupt()
            data, err = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_MODE)
            if err == ErrorCode.errOk:
                data |= ModeValues.ALM_ENA
                err = SerialBusDevice.writeByteRegister(self, self.REGISTER.REG_MODE, data)
            if err == ErrorCode.errOk:
                data, err = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_CTRL)
                if data & self.REGISTER.CTRL_IO0DATA:  # TODO: check where this reg control data should be defined
                    callback(gasgauge_EvtInt1)  # TODO: what does this do?
            else:
                self.callback = None
                self._disableInterrupt()
        else:  # Disable; from hardware to app.
            data, err = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_MODE)
            if err == ErrorCode.errOk:
                data &= ~ModeValues.ALM_ENA  # TODO: ModeValues class need to be adjusted to work with all binary operations as expected
                err = SerialBusDevice.writeByteRegister(self, self.REGISTER.REG_MODE, data)
            self._disableInterrupt()
            self.callback = None
        return err

    def _enableInterrupt(self):
        err = GPIO_enableInterrupt(self, gpio_alarm_idx)  # TODO: implement GPIO interrupt, check if it does infact return an error (not sure)
        if err == ErrorCode.errOk:  # TODO: do we really want these lines to override this error, and not just return the given error?
            ret = ErrorCode.errOk
        else:
            ret = ErrorCode.errInvalidParameter
        return ret

    def _disableInterrupt(self):
        err = GPIO_disableInterrupt(self)  # TODO: implement GPIO interrupt, check if it does infact return an error (not sure)
        if err == ErrorCode.errOk:  # TODO: do we really want these lines to override this error, and not just return the given error?
            ret = ErrorCode.errOk
        else:
            ret = ErrorCode.errInvalidParameter
        return ret

    def _getEventContext(self, event):
        pass  # TODO: this function, see original implementation
