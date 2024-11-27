# TODO: all the comments

# -*- coding: utf-8 -*-
"""A module to provide base classes and data types for gas gauge driver implementations.
"""
__author__ = "Carl Bellgardt"
__version__ = "0.1"
__all__ = ["STC311x", "ChipType"]

from philander.penum import Enum, unique, auto, idiotypic

from philander.battery import Status as BatStatus, Level as BatLevel
from philander.gasgauge import GasGauge, SOCChangeRate
from philander.gpio import GPIO
from philander.interruptable import Interruptable, Event
from philander.primitives import Current, Voltage, Percentage, Temperature
from philander.serialbus import SerialBusDevice
from philander.stc311x_reg import _STC311x_Reg, STC3115_Reg, STC3117_Reg, ChipType
from philander.sysfactory import SysFactory
from philander.systypes import ErrorCode, RunLevel, Info


@unique
@idiotypic
class OperatingMode(Enum):
    opModeUnknown = auto()
    opModeStandby = auto()
    opModeVoltage = auto()
    opModeMixed = auto()


class STC311x(GasGauge, SerialBusDevice, Interruptable):
    """Driver implementation for the stc3117 and stc3118 gas gauge chips by ST microelectronics.
    
    A gas gauge allows to keep track of the state of charge
    (SOC), remaining capacity, current voltage etc. of a battery.
    Info about the specific gas gauge ICs can be found at https://www.st.com/en/power-management/stc3117.html
    This class was tested using a STC3117 but should also work for STC3118 and possibly other similar chips.
    """

    ADDRESSES_ALLOWED = [0x70]

    def __init__(self):
        SerialBusDevice.__init__(self)
        Interruptable.__init__(self)
        self.REGISTER = None  # chip specific register information, set in open() via a parameter
        self.pinInt = None

    @classmethod
    def Params_init(cls, paramDict):
        """Initializes configuration parameters with defaults.
        
        The following settings are supported:
        
        =================================    ==========================================================================================================
        Key name                             Value type, meaning and default
        =================================    ==========================================================================================================
        SerialBusDevice.address              ``int`` I2C serial device address; default is :attr:`ADDRESSES_ALLOWED` [0].
        Gasgauge.ChipType                    ``ChipType`` identifies STC3115 or STC3117 chip; default is ``ChipType.STC3115``
        Gasgauge.SenseResistor               ``int`` Current sense resistor Rs in mOhm [5...50]; default is ``_STC311x_Reg.CONFIG_RSENSE_DEFAULT``
        All other Gasgauge.int.gpio.* settings as documented at :meth:`.GPIO.Params_init`.
        ===============================================================================================================================================
        
        Also see: :meth:`.Gasgauge.Params_init`, :meth:`.SerialBusDevice.Params_init`, :meth:`.GPIO.Params_init`.
        """
        def_dict = {
            "SerialBusDevice.address": cls.ADDRESSES_ALLOWED[0],
            "Gasgauge.ChipType": ChipType.STC3115,  # TODO: implement auto
            "Gasgauge.SenseResistor": _STC311x_Reg.CONFIG_RSENSE_DEFAULT,  # Sense resistor in milli Ohm
            # "Gasgauge.cc_cnf": _STC311x_Reg.CC_CNF_DEFAULT,  # Coulomb-counter mode configuration
            # "Gasgauge.vm_cnf": _STC311x_Reg.VM_CNF_DEFAULT,  # Voltage mode configuration
            # "Gasgauge.alarm_soc": _STC311x_Reg.ALARM_SOC_DEFAULT,  # SOC lower threshold; SOC alarm level [0.5%]
            # "Gasgauge.alarm_voltage": _STC311x_Reg.ALARM_VOLTAGE_DEFAULT,  # Voltage lower threshold; 3.0 V
            # "Gasgauge.current_thres": _STC311x_Reg.CURRENT_THRES_DEFAULT,  # Current monitoring threshold; +/-470 V drop
            # "Gasgauge.cmonit_max": _STC311x_Reg.CMONIT_MAX_DEFAULT  # Monitoring timing threshold; CC-VM: 4 minutes; VM->CC: 1 minute
            "Gasgauge.int.gpio.direction":  GPIO.DIRECTION_IN,
            "Gasgauge.int.gpio.trigger":    GPIO.TRIGGER_EDGE_FALLING,
            "Gasgauge.int.gpio.bounce" :    GPIO.BOUNCE_NONE,
        }
        def_dict.update(paramDict)
        paramDict.update(def_dict)  # update again to apply changes to original reference
        return None

    def open(self, paramDict):
        """Opens the instance and sets it in a usable state.

        Allocate necessary hardware resources and configure
        user-adjustable parameters to meaningful defaults.
        In this case the registers for the specific chip are defined
        and optionally the GPIO-Pin for interrupts is initialized.
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
        if paramDict["Gasgauge.ChipType"] == ChipType.STC3115:
            self.REGISTER = STC3115_Reg(paramDict)
        elif paramDict["Gasgauge.ChipType"] == ChipType.STC3117:
            self.REGISTER = STC3117_Reg(paramDict)
        else:
            err = ErrorCode.errInvalidParameter
        if err.isOk():
            err = SerialBusDevice.open(self, paramDict)
        if err.isOk():
            self._setup()
        if err.isOk() and ("Gasgauge.int.gpio.pinDesignator" in paramDict):
            # Setup GPIO pin for interrupts
            prefix = "Gasgauge.int."
            gpioParams = dict( [(k.replace(prefix, ""),v) for k,v in paramDict.items() if k.startswith(prefix)] )
            self.pinInt = SysFactory.getGPIO()
            # open GPIO pin
            err = self.pinInt.open(gpioParams)
            self.enableInterrupt()
        return err

    def close(self):
        """Shut down the device after usage.
        
        This method should be called when the device is not used, anymore,
        e.g. as part of the application exit procedure.
        The following steps are executed:

        * close I2C-Bus connection
        * close GPIO pin for interrupts
        
        After return, the device can still be re-used, by calling
        :meth:`.open` again.
        
        Also see: :meth:`.GPIO.close`, :meth:`.Module.close`.
        """
        self.setRunLevel(RunLevel.shutdown)
        err = SerialBusDevice.close(self)
        if self.pinInt is not None:
            err2 = self.pinInt.close()
            self.pinInt = None
            if err.isOk():
                err = err2
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
        if err.isOk():
            info.chipID = chip_id
            if chip_id == self.REGISTER.CHIP_ID:
                info.validity = Info.validChipID
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
        return None, ErrorCode.errNotSupported

    def getBatteryVoltage(self):
        """Retrieves the battery voltage in milli Volt.
        
        :return: A on-negative integer value [mV] or :attr:`Voltage.invalid`\
        to indicate that this information could not be retrieved.
        :rtype: Voltage
        """
        voltage, err = self.readWordRegister(self.REGISTER.REG_VOLTAGE)
        if err.isOk():
            ret = self._transferVoltage(voltage)
        else:
            ret = Voltage.invalid
        return ret

    def getBatteryCurrent(self):
        """Retrieves the battery current in micro Ampere at the time this\
        function is executed.
        
        See also: :meth:`getBatteryCurrentAvg`
        
        :return: A non-negative integer value [micro A] or :attr:`Current.invalid`\
        to indicate that this information could not be retrieved.
        :rtype: Current
        """
        current, err = self.readWordRegister(self.REGISTER.REG_CURRENT)
        if err.isOk():
            ret = self._transferCurrent(current)
        else:
            ret = Current.invalid
        return ret

    def getBatteryCurrentAvg(self):
        """Retrieves the average battery current.
        
        The average is taken over some time interval, e.g. 2 seconds.
        The length of the time window is at the discretion of the
        implementation and cannot be adjusted by the caller.
        
        See also: :meth:`getBatteryCurrent`

        :return: A non-negative integer value [micro A] or :attr:`Current.invalid`\
        to indicate that this information could not be retrieved.
        :rtype: Current
        """
        ret = Current.invalid
        if self.REGISTER.CHIP_TYPE == ChipType.STC3117:  # Function is STC3117 exclusive
            if self._getOperatingMode() == OperatingMode.opModeMixed:
                data, err = SerialBusDevice.readWordRegister(self, self.REGISTER.REG_AVG_CURRENT)  # TODO: implement this register properly
                if err.isOk():
                    ret = self._transferCurrentAvg(data)
        return ret

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

    def _transferCurrent(self, data):
        # Actually, we read out the voltage drop over the sense resistor.
        # LSB is 5.88V, so first scaling factor is 5.88 = 294/50
        # Value is signed!
        # R = U/I  so we get I = U/R; Note that R is given in milliOhm!
        # So, finally we scale by 294 / 50 * 1000 / rs = 294 * 20 / rs = 5880 / rs.
        rs = self.REGISTER.CONFIG_GASGAUGE_0_RSENSE
        if data >= 0:
            ret = (data * 5880 + (rs / 2)) / rs
        else:
            ret = (data * 5880 - (rs / 2)) / rs
        return ret

    # /**
    #  * AVG_CURRENT transfer function
    #  */
    def _transferCurrentAvg(self, data):  # STC3117 exclusive
        if self.REGISTER.CHIP_TYPE is not ChipType.STC3117:
            ret = Current.invalid  # Function is not implemented for this chip
        else:
            # Again, we actually read out the voltage drop over the sense resistor.
            # LSB is 1.47V, partial scaling factor is 1.47 = 147/100
            # Value is signed!
            # Total scaling factor is: 147 / 100 * 1000 / rs = 147 * 10 / rs = 1470 / rs.
            rs = self.REGISTER.CONFIG_GASGAUGE_0_RSENSE
            if data >= 0:
                ret = (data * 1470 + rs/2) / rs
            else:
                ret = (data * 1470 - rs/2) / rs
            ret = Current(ret)
        return ret

    @staticmethod
    def _transferTemperature(data):
        # LSB is 1 °C, so we don't need any scaling.
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
        # check if RAM test register value is correct
        if len(data) < length or data[self.REGISTER.IDX_RAM_TEST] != self.REGISTER.RAM_TEST:
            ret = ErrorCode.errCorruptData
        else:
            code = self._crc(data, self.REGISTER.RAM_SIZE - 1)
            if code != data[self.REGISTER.IDX_RAM_CRC]:
                ret = ErrorCode.errCorruptData
            else:
                ret = ErrorCode.errOk
        return ret

    def _getOperatingMode(self):
        data, err = SerialBusDevice.readByteRegister(self,  self.REGISTER.REG_MODE)
        if err.isOk():
            if data and self.REGISTER.MODE_GG_RUN:
                if data and self.REGISTER.MODE_VMODE:
                    ret = OperatingMode.opModeVoltage
                else:
                    ret = OperatingMode.opModeMixed
            else:
                ret = OperatingMode.opModeStandby
        else:
            ret = OperatingMode.opModeUnknown
        return ret

    def _checkID(self):
        data, err = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_ID)
        if err.isOk():
            err = ErrorCode.errOk if (data == self.REGISTER.CHIP_ID) else ErrorCode.errFailure
        return err

    def _setup(self):  # TODO: implement this function into open()?
        # TODO: this function is still Work In Progress and will not work at all
        return ErrorCode.errNotImplemented
        ramContent = None  # TODO: where does RAM content come from?
        params = None  # TODO: insert according confs where params is used
        memset = None  # TODO: see original implementation
        buffer = None  # TODO: see original implementation

        # check communication
        err = self._checkID()
        # read RAM
        if err.isOk():
            data, err = SerialBusDevice.readWriteBuffer(self, self.REGISTER.RAM_SIZE, 1)
        # check RAM consistency
        canRestore = False  # disable RAM restoration
        if err.isOk():
            err = self._checkRamConsistency(ramContent, self.REGISTER.RAM_SIZE)
            if err.isOk():
                # check CTRL_PORDET and CTRL_BATFAIL
                data, err = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_CTRL)
                if err.isOk():
                    if data & (self.REGISTER.CTRL_BATFAIL | self.REGISTER.CTRL_PORDET):
                        # battery removed / voltage dropped below threshold
                        # no restoration, start anew, instead!
                        canRestore = False
            else:
                canRestore = False
                err = ErrorCode.errOk
        if err.isOk():
            # common steps (pre-phase)
            if canRestore:
                # restore configuration from RAM
                # ensure that GG_RUN is cleared
                SerialBusDevice.writeByteRegister(self, self.REGISTER.REG_MODE, self.REGISTER.MODE_OFF)
                # restore REG_CC_CNF
                data16 = (ramContent[self.REGISTER.IDX_RAM_CC_CNF_H] << 8) | ramContent[self.REGISTER.IDX_RAM_CC_CNF_L]
                SerialBusDevice.writeWordRegister(self, self.REGISTER.REG_CC_CNF, data16)
                # restore REG_VM_CNF
                data16 = (ramContent[self.REGISTER.IDX_RAM_VM_CNF_H] << 8) | ramContent[self.REGISTER.IDX_RAM_VM_CNF_L]
                SerialBusDevice.writeWordRegister(self, self.REGISTER.REG_VM_CNF, data16)
                # restore REG_SOC
                data16 = (ramContent[self.REGISTER.IDX_RAM_SOC_H] << 8) | ramContent[self.REGISTER.IDX_RAM_SOC_L]
                SerialBusDevice.writeWordRegister(self, self.REGISTER.REG_SOC, data16)
            else:
                # initialize configuration with defaults
                # run gas gauge to get first OCV and current measurement
                data8 = self.REGISTER.MODE_OFF | self.REGISTER.MODE_GG_RUN |self.REGISTER.MODE_FORCE_CC
                SerialBusDevice.writeByteRegister(self, self.REGISTER.REG_MODE, data8)
                # read OCV
                data, _ = SerialBusDevice.readWordRegister(self, self.REGISTER.REG_OCV)
                ocv = self._transfertOCV(data)
                # read current
                data, _ = SerialBusDevice.readWordRegister(self, self.REGISTER.REG_CURRENT)
                current = self._transferCurrent(data)
                # ensure that GG_RUN is cleared
                SerialBusDevice.writeByteRegister(self, self.REGISTER.REG_MODE, self.REGISTER.MODE_OFF)
                # REG_CC_CNF
                SerialBusDevice.writeWordRegister(self, self.REGISTER.REG_CC_CNF, params.regCCcnf)  # TODO: get from params
                # REG_VM_CNF
                SerialBusDevice.writeWordRegister(self, self.REGISTER.REG_VM_CNF, params.regVMcnf)  # TODO: same as above
                # compensate OCV
                if current > 1000000:
                    current /= 1000
                    ocv = ocv - current * CFG_SUBSECTATR( BATTERY, CONFIG_GASGAUGE_0_BATTERY_IDX, IMPEDANCE ) / 1000
                else:
                    ocv = ocv - current * CFG_SUBSECTATR(BATTERY, CONFIG_GASGAUGE_0_BATTERY_IDX, IMPEDANCE) / (1000 * 1000)
                data16 = self._invTransferOCV(ocv)
                # write OCV back
                SerialBusDevice.writeWordRegister(self, self.REGISTER.REG_OCV, data16)
                # wait 1ßßms to get valid SOC
                data, _ = SerialBusDevice.readWordRegister(self, self.REGISTER.REG_SOC)
                # store new backup to RAM
                memset(ramContent, 0, self.REGISTER.RAM_SIZE)
                ramContent[self.REGISTER.IDX_RAM_TEST] = self.REGISTER.RAM_TEST
                ramContent[self.REGISTER.IDX_RAM_SOC_L] = data16 & 0xFF
                ramContent[self.REGISTER.IDX_RAM_SOC_H] = data16 >> 8
                ramContent[self.REGISTER.IDX_RAM_CC_CNF_L] = params.regCCcnf & 0xFF
                ramContent[self.REGISTER.IDX_RAM_CC_CNF_H] = params.regCCcnf >> 8
                ramContent[self.REGISTER.IDX_RAM_VM_CNF_L] = params.regVMcnf & 0xFF
                ramContent[self.REGISTER.IDX_RAM_VM_CNF_H] = params.regVMcnf >> 8
                ramContent[self.REGISTER.IDX_RAM_CRC] = crc(ramContent, self.REGISTER.RAM_SIZE - 1)
                buffer[0] = self.REGISTER.REG_RAM_FIRST
                SerialBusDevice.writeBuffer(self, self.REGISTER.RAM_SIZE + 1)

    # API functions exported to the outside

    def _setRunLevel(self, level):
        mode = self.REGISTER.MODE_OFF
        if level in [RunLevel.active, RunLevel.idle]:  # TODO: not sure if this is the best "pythonic^TM" way
            # Mixed mode: coulomb counter + voltage gas gauge -> Leave VMODE off
            mode = self.REGISTER.MODE_OFF | self.REGISTER.MODE_GG_RUN | self.REGISTER.MODE_FORCE_CC
            if self.pinInt._fIntEnabled:
                mode |= self.REGISTER.MODE_ALM_ENA
            ret = ErrorCode.errOk
        elif level in [RunLevel.relax, RunLevel.snooze, RunLevel.nap, RunLevel.sleep, RunLevel.deepSleep]:
            # Power saving mode: voltage gas gauge, only. -> VMODE = 1
            mode = self.REGISTER.MODE_OFF | self.REGISTER.MODE_VMODE | self.REGISTER.MODE_GG_RUN | self.REGISTER.MODE_FORCE_VM
            if self.pinInt._fIntEnabled:
                mode |= self.REGISTER.MODE_ALM_ENA
            ret = ErrorCode.errOk
        elif level == RunLevel.shutdown:
            # ret = backupRam(self)
            mode = self.REGISTER.MODE_VMODE | self.REGISTER.MODE_FORCE_VM
            ret = ErrorCode.errOk
        else:
            ret = ErrorCode.errNotSupported
        # set mode and return ErrorCode
        if ret.isOk():
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
        mode_data, err = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_MODE)
        if err.isOk() and not (mode_data & self.REGISTER.MODE_GG_RUN):
            mode_data |= self.REGISTER.MODE_GG_RUN
            err = SerialBusDevice.writeByteRegister(self, self.REGISTER.REG_MODE, mode_data)
            # same applies for beneath
        # Do a soft reset by asserting CTRL:PORDET
        if err.isOk():
            # TODO: consider adding a set_ctrl / get_ctrl / add_ctrl method for this purpose; same for mdoe
            ctrl_data = self.REGISTER.CTRL_IO0DATA | self.REGISTER.CTRL_GG_RST | self.REGISTER.CTRL_PORDET
            err = SerialBusDevice.writeByteRegister(self, self.REGISTER.REG_CTRL, ctrl_data)
        # Delay: Loop until we see the MODE_GG_RUN bit cleared:
        if err.isOk():
            has_timed_out = True
            for i in range(self.REGISTER.POR_DELAY_LOOPS_MAX):
                mode_data, err = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_MODE)
                if not (err.isOk() and (mode_data & self.REGISTER.MODE_GG_RUN)):
                    has_timed_out = False  # loop ended before i == POR_DELAY_LOOPS_MAY
                    break
            if has_timed_out:
                err = ErrorCode.errMalfunction
        # Then, re-initialize the device
        if err.isOk():
            STC311x._setup(self)
        return err

    def getID(self):
        data, err = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_ID)
        ret = data if err.isOk() else err
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
        if err.isOk():
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
                data, err = SerialBusDevice.readWordRegister(self, self.REGISTER.REG_AVG_CURRENT)
                if err.isOk():
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
        if err.isOk():
            ret = self._transferTemperature(data)
        else:
            ret = Temperature.invalid
        return ret

    # Interruptable API implementation

    def registerInterruptHandler(self, onEvent=Event.evtInt1, callerFeedBack=None, handler=None):
        if handler is not None:  # Enable; from app (=sink) to hardware (=source)
            self.pinInt.registerInterruptHandler(onEvent, callerFeedBack, handler)
            err = self.pinInt.enableInterrupt()
            if err.isOk():
                data, err = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_MODE)
                if err.isOk():
                    data |= self.REGISTER.MODE_ALM_ENA
                    err = SerialBusDevice.writeByteRegister(self, self.REGISTER.REG_MODE, data)
                if err.isOk():  # check if there already is an interrupt present
                    data, err = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_CTRL)
                    if data & self.REGISTER.CTRL_IO0DATA:
                        handler(Event.evtInt1, callerFeedBack)
                else:
                    self.disableInterrupt()
            else:
                err = ErrorCode.errInvalidParameter  # TODO: is this the right error code?
        else:  # Disable; from hardware to app.
            data, err = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_MODE)
            if err.isOk():
                data &= ~self.REGISTER.MODE_ALM_ENA  # TODO: ModeValues class need to be adjusted to work with all binary operations as expected
                err = SerialBusDevice.writeByteRegister(self, self.REGISTER.REG_MODE, data)
            self.disableInterrupt()
        return err

    def enableInterrupt(self):
        # err = GPIO.enableInterrupt(self, self.REGISTER.CONFIG_GASGAUGE_0_GPIO_ALARM)  # TODO: implement GPIO interrupt, check if it does infact return an error (not sure)
        # if err.is_ok():  # TODO: do we really want these lines to override this error, and not just return the given error?
        #     ret = ErrorCode.errOk
        # else:
        #     ret = ErrorCode.errInvalidParameter
        # return ret
        return ErrorCode.errOk  # TODO: why doesn't this function do anything (see max77960)

    def disableInterrupt(self):
        # err = GPIO_disableInterrupt(self)  # TODO: implement GPIO interrupt, check if it does infact return an error (not sure)
        # if err.is_ok():  # TODO: do we really want these lines to override this error, and not just return the given error?
        #     ret = ErrorCode.errOk
        # else:
        #     ret = ErrorCode.errInvalidParameter
        # return ret
        return ErrorCode.errOk  # TODO: why doesn't this function do anything (see max77960)

    def _getEventContext(self, event):
        pass  # TODO: this function, see original implementation
