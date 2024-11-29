"""A module to provide base classes and data types for ST gas gauge driver implementations.
"""
__author__ = "Carl Bellgardt"
__version__ = "0.1"
__all__ = ["STC311x", "OperatingMode"]

import time
from philander.penum import Enum, unique, auto, idiotypic

from philander.battery import Status as BatStatus, Level as BatLevel
from philander.gasgauge import GasGauge, SOCChangeRate, StatusID
from philander.gpio import GPIO
from philander.interruptable import Interruptable, Event
from philander.primitives import Current, Voltage, Percentage, Temperature
from philander.serialbus import SerialBusDevice
from philander.stc311x_reg import STC311x_Reg
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
    """Base implementation for the stc311x gas gauge chip family.
    
    A gas gauge allows to keep track of the state of charge
    (SOC), remaining capacity, current voltage etc. of a battery.
    Info about the specific gas gauge ICs can be found at
    https://www.st.com/en/power-management/stc3115.html or
    https://www.st.com/en/power-management/stc3117.html
    """

    ADDRESSES_ALLOWED = [0x70]
    
    MODEL_ID = None     # to be defined in sub-classes

    RSENSE_DEFAULT = 10          # default Rsense, in mOhm
    BAT_CAPACITY_DEFAULT = 800   # default battery capacity in mAh
    BAT_IMPEDANCE_DEFAULT= 200   # default battery impedance in mOhm
    ALARM_SOC_DEFAULT = 1        # default SOC alarm threshold [%]
    ALARM_VOLTAGE_DEFAULT = 3000 # default voltage alarm threshold [mV]
    RELAX_CURRENT_DEFAULT = 5000 # default current monitoring threshold [uA]
    RELAX_TIMER_DEFAULT   = 480  # default current monitoring timer [s]
    
    # Constants needed only for the implementation
    POR_TIMEOUT = 3  # POR timeout i seconds


    def __init__(self):
        SerialBusDevice.__init__(self)
        Interruptable.__init__(self)
        self.REGISTER = None  # chip specific register information
        self.pinInt = None
        self.RSense = None          # Sense resistor in milli Ohm
        self.batCapacity = None     # Battery capacity in mAh
        self.batImpedance= None     # Battery impedance in mOhm.
        self.alarmSOC = None        # SOC alarm threshold [%]
        self.alarmVoltage = None    # Voltage alarm threshold [mV]
        self.relaxCurrent = None    # Current monitoring threshold [uA]
        self.relaxTimerCC2VM = None # Current monitor timing CC->VM [s]

    def _getOperatingMode(self):
        data, err = self.readByteRegister(self.REGISTER.REG_MODE)
        if err.isOk():
            if data & self.REGISTER.MODE_GG_RUN:
                if data & self.REGISTER.MODE_VMODE:
                    ret = OperatingMode.opModeVoltage
                else:
                    ret = OperatingMode.opModeMixed
            else:
                ret = OperatingMode.opModeStandby
        else:
            ret = OperatingMode.opModeUnknown
        return ret

    #
    # Module API
    #

    @classmethod
    def Params_init(cls, paramDict):
        """Initializes configuration parameters with defaults.
        
        The following settings are supported:
        
        =================================    ==========================================================================================================
        Key name                             Value type, meaning and default
        =================================    ==========================================================================================================
        SerialBusDevice.address              ``int`` I2C serial device address; default is :attr:`ADDRESSES_ALLOWED` [0].
        Gasgauge.SenseResistor               ``int`` Current sense resistor Rs in mOhm [5...50]; default is ``RSENSE_DEFAULT``
        Gasgauge.battery.capacity            ``int`` Battery capacity in mAh; default is ``BAT_CAPACITY_DEFAULT``
        Gasgauge.battery.impedance           ``int`` Battery impedance in mOhm; default is ``BAT_IMPEDANCE_DEFAULT``
        Gasgauge.alarm.soc                   ``int`` SOC alarm threshold [%]; default is ``ALARM_SOC_DEFAULT``
        Gasgauge.alarm.voltage               ``int`` Voltage alarm threshold [mV]; default is ``ALARM_VOLTAGE_DEFAULT``
        Gasgauge.relax.current               ``int`` Current monitoring threshold [uA]; default is ``RELAX_CURRENT_DEFAULT``
        Gasgauge.relax.timer                 ``int`` Current monitoring timer count [s]; default is ``RELAX_TIMER_DEFAULT``
        Gasgauge.int.gpio.*                  ALM pin configuration; See :meth:`.GPIO.Params_init`.
        ===============================================================================================================================================
        
        Also see: :meth:`.Gasgauge.Params_init`, :meth:`.SerialBusDevice.Params_init`, :meth:`.GPIO.Params_init`.
        """
        def_dict = {
            "SerialBusDevice.address":      cls.ADDRESSES_ALLOWED[0],
            "Gasgauge.SenseResistor":       cls.RSENSE_DEFAULT,
            "Gasgauge.battery.capacity":    cls.BAT_CAPACITY_DEFAULT,
            "Gasgauge.battery.impedance":   cls.BAT_IMPEDANCE_DEFAULT,
            "Gasgauge.alarm.soc":           cls.ALARM_SOC_DEFAULT,
            "Gasgauge.alarm.voltage":       cls.ALARM_VOLTAGE_DEFAULT,
            "Gasgauge.relax.current":       cls.RELAX_CURRENT_DEFAULT,
            "Gasgauge.relax.timer":         cls.RELAX_TIMER_DEFAULT,
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
        if err.isOk():
            err = SerialBusDevice.open(self, paramDict)
        if err.isOk():
            self.RSense = paramDict["Gasgauge.SenseResistor"]
            self.batCapacity = paramDict["Gasgauge.battery.capacity"]
            self.batImpedance = paramDict["Gasgauge.battery.impedance"]
            self.alarmSOC = paramDict["Gasgauge.alarm.soc"]
            self.alarmVoltage = paramDict["Gasgauge.alarm.voltage"]
            self.relaxCurrent = paramDict["Gasgauge.relax.current"]
            self.relaxTimerCC2VM = paramDict["Gasgauge.relax.timer"]
            err = self._setup()
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

    def setRunLevel(self, level):
        """Select the power-saving operation mode.

        Switches the instance to one of the power-saving modes or
        recovers from these modes. Situation-aware deployment of these
        modes can greatly reduce the system's total power consumption.
        
        :param RunLevel level: The level to switch to.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        mode = self.REGISTER.MODE_OFF
        if level in [RunLevel.active, RunLevel.idle]:
            # Mixed mode: coulomb counter + voltage gas gauge -> Leave VMODE off
            mode = self.REGISTER.MODE_OFF | self.REGISTER.MODE_GG_RUN | self.REGISTER.MODE_FORCE_CC
            if self.pinInt:
                mode |= self.REGISTER.MODE_ALM_ENA
        elif level in [RunLevel.relax, RunLevel.snooze, RunLevel.nap, RunLevel.sleep, RunLevel.deepSleep]:
            # Power saving mode: voltage gas gauge, only. -> VMODE = 1
            mode = self.REGISTER.MODE_OFF | self.REGISTER.MODE_VMODE | self.REGISTER.MODE_GG_RUN | self.REGISTER.MODE_FORCE_VM
            if self.pinInt:
                mode |= self.REGISTER.MODE_ALM_ENA
        elif level == RunLevel.shutdown:
            # ret = backupRam(self)
            mode = self.REGISTER.MODE_VMODE | self.REGISTER.MODE_FORCE_VM
        else:
            ret = ErrorCode.errNotSupported
        # set mode and return ErrorCode
        if ret.isOk():
            ret = SerialBusDevice.writeByteRegister(self,  self.REGISTER.REG_MODE, mode)
        return ret
    
    #
    # Gasgauge API
    #

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
        # Do a soft reset by asserting CTRL_PORDET
        if err.isOk():
            # TODO: consider adding a set_ctrl / get_ctrl / add_ctrl method for this purpose; same for mode
            ctrl_data = self.REGISTER.CTRL_IO0DATA | self.REGISTER.CTRL_GG_RST | self.REGISTER.CTRL_PORDET
            err = SerialBusDevice.writeByteRegister(self, self.REGISTER.REG_CTRL, ctrl_data)
        # Delay: Loop until we see the MODE_GG_RUN bit cleared:
        if err.isOk():
            t0 = time.time()
            done = False
            bootFinished = False
            while not done:
                mode_data, err = SerialBusDevice.readByteRegister(self, self.REGISTER.REG_MODE)
                tNow = time.time()
                bootFinished = err.isOk() and not (mode_data & self.REGISTER.MODE_GG_RUN)
                done = bootFinished or (tNow - t0 > STC311x.POR_TIMEOUT)
            if not bootFinished:
                err = ErrorCode.errMalfunction
        # Then, re-initialize the device
        if err.isOk():
            self._setup()
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
        if not self.MODEL_ID is None:
            info.modelID = self.MODEL_ID
            info.validity = (info.validity | Info.validModelID)
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
        data = None
        if statusID == StatusID.dieTemp:
            data, err = self.readByteRegister(self.REGISTER.REG_TEMPERATURE)
            # LSB is 1 °C, so we don't need any scaling.
        else:
            data = None
            err = ErrorCode.errNotSupported
        return data, err

    @staticmethod
    def _transferSOC(data):
        # LSB is 1/512 %, so shift by 9 bits.
        # Add 1/2 for correct rounding
        ret = data + 0x0100 >> 9
        return Percentage(ret)

    def getStateOfCharge( self ):
        """Retrieves the state of charge.
        
        That is the fraction of electric energy from the total capacity,
        that is still or already stored in the battery. This information
        is valid for both, the charging as well as the discharging process.
        
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

    @staticmethod
    def _transferVoltage(data):
        # LSB is 2.2mV, so scale by factor 2.20 = 22/10
        ret = (data * 22 + 5) // 10
        return Voltage(ret)

    def getBatteryVoltage(self):
        """Retrieves the battery voltage in milli Volt.
        
        :return: A on-negative integer value [mV] or :attr:`Voltage.invalid`\
        to indicate that this information could not be retrieved.
        :rtype: Voltage
        """
        data, err = self.readWordRegister(self.REGISTER.REG_VOLTAGE)
        if err.isOk():
            ret = self._transferVoltage(data)
        else:
            ret = Voltage.invalid
        return ret

    def _transferCurrent(self, data):
        # Actually, we read out the voltage drop over the sense resistor.
        # LSB is 5.88V, so first scaling factor is 5.88 = 294/50
        # Value is signed!
        # R = U/I  so we get I = U/R; Note that R is given in milliOhm!
        # So, finally we scale by 294 / 50 * 1000 / rs = 294 * 20 / rs = 5880 / rs.
        if data >= 0:
            ret = (data * 5880 + (self.RSense // 2)) // self.RSense
        else:
            ret = (data * 5880 - (self.RSense // 2)) // self.RSense
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

    # Local functions for internal use

    @staticmethod
    def _transferOCV(data):
        # LSB is 0.55 mV, so scale by factor 0.55 = 55/100 = 11/20.
        ret = (data * 11 + 10) // 20
        return Voltage(ret)

    @staticmethod
    def _invTransferOCV(value):
        # LSB is 0.55 mV, so scale by factor 1/0.55 = 100/55 = 20/11.
        ret = (value * 20 + 5) // 11
        return ret

    @staticmethod
    def _crc(data, length):
        ret = 0
        for idx in range(length):
            ret ^= data[idx]
        return ret

    def _checkRamConsistency(self, data):
        # check if RAM test register value is correct
        if (len(data) < self.REGISTER.RAM_SIZE) or \
           (data[self.REGISTER.IDX_RAM_TEST] != self.REGISTER.RAM_TEST):
            ret = ErrorCode.errCorruptData
        else:
            code = self._crc(data, self.REGISTER.RAM_SIZE - 1)
            if code != data[self.REGISTER.IDX_RAM_CRC]:
                ret = ErrorCode.errCorruptData
            else:
                ret = ErrorCode.errOk
        return ret

# UNUSED static ErrorCode_t updateRamWord( const Device_Index_t devIdx, const unsigned int ramIndex, const uint16_t newData )
# {
#     ErrorCode_t ret = errOk;
#     uint8_t buffer[RAM_SIZE + 1];
#     uint8_t *ramContent;
#     uint8_t data8;
#
#     ramContent = &buffer[1];
#     data8 = REG_RAM_FIRST;
#     ret = Serial_Bus_read_write_Buffer( &dContext[devIdx].sdev, ramContent, RAM_SIZE, &data8, 1);
#
#     if( ret == errOk )
#     {
#         ret = checkRamConsistency( ramContent, RAM_SIZE );
#     }
#     if( ret == errOk )
#     {
#         ramContent[ramIndex] = newData & 0xFF;
#         ramContent[ramIndex+1] = newData >> 8;
#         ramContent[IDX_RAM_CRC] = crc( ramContent, RAM_SIZE-1 );
#         buffer[0] = REG_RAM_FIRST;
#         ret = Serial_Bus_write_Buffer( &dContext[devIdx].sdev, buffer, RAM_SIZE + 1 );
#     }
#     return ret;
# }
#
# UNUSED static ErrorCode_t backupRam( const Device_Index_t devIdx )
# {
#     ErrorCode_t ret = errOk;
#     uint8_t buffer[RAM_SIZE + 1];
#     uint8_t *ramContent;
#     uint16_t data16;
#
#     ramContent = &buffer[1];
#     memset( ramContent, 0, RAM_SIZE );
#     ramContent[IDX_RAM_TEST] = RAM_TEST;
#     ret = Serial_Bus_read_Reg_Word( &dContext[devIdx].sdev, REG_SOC, &data16 );
#     ramContent[IDX_RAM_SOC_L]= data16 & 0xFF;
#     ramContent[IDX_RAM_SOC_H]= data16 >> 8;
#     ret = Serial_Bus_read_Reg_Word( &dContext[devIdx].sdev, REG_CC_CNF, &data16 );
#     ramContent[IDX_RAM_CC_CNF_L]= data16 & 0xFF;
#     ramContent[IDX_RAM_CC_CNF_H]= data16 >> 8;
#     ret = Serial_Bus_read_Reg_Word( &dContext[devIdx].sdev, REG_VM_CNF, &data16 );
#     ramContent[IDX_RAM_VM_CNF_L]= data16 & 0xFF;
#     ramContent[IDX_RAM_VM_CNF_H]= data16 >> 8;
#     ramContent[IDX_RAM_CRC] =   crc( ramContent, RAM_SIZE - 1 );
#     buffer[0] = REG_RAM_FIRST;
#     Serial_Bus_write_Buffer(&dContext[devIdx].sdev, buffer, RAM_SIZE + 1 );
#
#     return ret;
# }

    def _setupAlarm(self):
        # REG_ALARM_SOC, LSB=0,5%, scaling = 2.
        data = self.alarmSOC * 2
        err = self.writeByteRegister( self.REGISTER.REG_ALARM_SOC, data)
        if err.isOk():
            # REG_ALARM_VOLTAGE, LSB=17,6mV, scaling = 10/176 = 5/88
            data = (self.alarmVoltage * 5 + 44) // 88
            err = self.writeByteRegister( self.REGISTER.REG_ALARM_VOLTAGE, data)
        return err
    
    def _setupCurrentMonitoring(self):
        # REG_CURRENT_THRES, LSB=47,04µV
        # scaling = 1/47040 as relax current is in micro Ampere!
        data = (self.relaxCurrent * self.batImpedance + 23520) // 47040
        err = self.writeByteRegister( self.REGISTER.REG_CURRENT_THRES, data )
        # Sub classes must handle their REG_RELAX_MAX / REG_CMONIT_MAX counters
        return err
    
    def _setup(self):
        # Check communication
        data, err = self.readByteRegister(self.REGISTER.REG_ID)
        if err.isOk():
            err = ErrorCode.errOk if (data == self.REGISTER.CHIP_ID) else ErrorCode.errResourceConflict
        # Read RAM content
        if err.isOk():
            ramContent, err = self.readBufferRegister(self.REGISTER.REG_RAM_FIRST, self.REGISTER.RAM_SIZE)
        # Check RAM consistency
        canRestore = False  # Set True to enable RAM restoration
        if err.isOk():
            err = self._checkRamConsistency(ramContent)
            if err.isOk():
                # check CTRL_PORDET and CTRL_BATFAIL
                data, err = self.readByteRegister(self.REGISTER.REG_CTRL)
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
                self.writeByteRegister(self.REGISTER.REG_MODE, self.REGISTER.MODE_OFF)
                # restore REG_CC_CNF
                data = (ramContent[self.REGISTER.IDX_RAM_CC_CNF_H] << 8) | ramContent[self.REGISTER.IDX_RAM_CC_CNF_L]
                self.writeWordRegister(self.REGISTER.REG_CC_CNF, data)
                # restore REG_VM_CNF
                data = (ramContent[self.REGISTER.IDX_RAM_VM_CNF_H] << 8) | ramContent[self.REGISTER.IDX_RAM_VM_CNF_L]
                self.writeWordRegister(self.REGISTER.REG_VM_CNF, data)
                # restore REG_SOC
                data = (ramContent[self.REGISTER.IDX_RAM_SOC_H] << 8) | ramContent[self.REGISTER.IDX_RAM_SOC_L]
                self.writeWordRegister(self.REGISTER.REG_SOC, data)
            else:
                # initialize configuration with defaults
                # run gas gauge to get first OCV and current measurement
                data = self.REGISTER.MODE_OFF | self.REGISTER.MODE_GG_RUN |self.REGISTER.MODE_FORCE_CC
                self.writeByteRegister(self.REGISTER.REG_MODE, data)
                # read OCV
                data, _ = self.readWordRegister(self.REGISTER.REG_OCV)
                ocv = self._transferOCV(data)
                # read current
                data, _ = self.readWordRegister(self.REGISTER.REG_CURRENT)
                current = self._transferCurrent(data)
                # ensure that GG_RUN is cleared
                self.writeByteRegister(self.REGISTER.REG_MODE, self.REGISTER.MODE_OFF)
                # Determine and write the content of REG_CC_CNF
                # Following the STC3115 data sheet, chapter 6.2.1. on coulomb counter,
                # this register "scales the charge integrated by the
                # sigma delta converter into a percentage value of the battery capacity"
                # It depends on the battery capacity (Cnom) and the current sense resistor (Rsense) as follows:
                # REG_CC_CNF = Rsense [mOhm] * Cnom [mAh] ⁄ 49,556
                # Scaling factor: 1/49,556 = 1000/49556 = 250/12389
                cnfCC = (self.RSense * self.batCapacity * 250 + 6194) // 12389
                self.writeWordRegister(self.REGISTER.REG_CC_CNF, cnfCC)
                # Determine and write the content of REG_VM_CNF
                # Following to chapter 6.2.2, this register "configures the parameter used by the algorithm".
                # It is calculated from the battery's impedance (Ri) and apacity (Cnom) as follows:
                # REG_VM_CNF = Ri [mOhm] * Cnom [mAh] ⁄ 977,78
                # Scaling factor: 1/977.78 = 100/97778 = 50/48889
                cnfVM = (self.batImpedance * self.batCapacity * 50 + 24444) // 48889
                self.writeWordRegister(self.REGISTER.REG_VM_CNF, cnfVM)
                # compensate OCV
                if current > 1000000:
                    current //= 1000
                    ocv = ocv - current * self.batImpedance // 1000
                else:
                    ocv = ocv - current * self.batImpedance // (1000 * 1000)
                data = self._invTransferOCV(ocv)
                # write OCV back
                self.writeWordRegister(self.REGISTER.REG_OCV, data)
                # wait 100ms to get valid SOC
                if hasattr(time, "sleep_ms"):
                    time.sleep_ms(100)
                else:
                    time.sleep(0.1)
                data, _ = self.readWordRegister(self.REGISTER.REG_SOC)
                # store new backup to RAM
                ramContent = [0] * self.REGISTER.RAM_SIZE
                ramContent[self.REGISTER.IDX_RAM_TEST] = self.REGISTER.RAM_TEST
                ramContent[self.REGISTER.IDX_RAM_SOC_L] = data & 0xFF
                ramContent[self.REGISTER.IDX_RAM_SOC_H] = data >> 8
                ramContent[self.REGISTER.IDX_RAM_CC_CNF_L] = cnfCC & 0xFF
                ramContent[self.REGISTER.IDX_RAM_CC_CNF_H] = cnfCC >> 8
                ramContent[self.REGISTER.IDX_RAM_VM_CNF_L] = cnfVM & 0xFF
                ramContent[self.REGISTER.IDX_RAM_VM_CNF_H] = cnfVM >> 8
                ramContent[self.REGISTER.IDX_RAM_CRC] = self._crc(ramContent, self.REGISTER.RAM_SIZE - 1)
                self.writeBufferRegister(self.REGISTER.REG_RAM_FIRST, ramContent)
            
            # Common steps (post-phase)
            self._setupAlarm()
            self._setupCurrentMonitoring()
            
            # Clear interrupts
            # IO0DATA = 1 to see alarm conditions on the ALM pin
            # GG_RST  = 1 do reset the conversion counter
            # GG_VM   = 0, cannot be written
            # BATFAIL = 0 to clear this flag
            # PORDET  = 0 to clear the POR detection flag
            # ALM_SOC = 0 to clear low-SOC condition
            # ALM_VOLT= 0 to clear low voltage condition
            # UVLOD   = 0 to clear UVLO event.
            data = (self.REGISTER.CTRL_IO0DATA | self.REGISTER.CTRL_GG_RST)
            err = self.writeByteRegister( self.REGISTER.REG_CTRL, data )
    
            # Run the gas gauge
            err = self.setRunLevel( RunLevel.active )
    
        return err



    #
    # Interruptable API
    #

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
        if self.pinInt:
            err = self.pinInt.enableInterrupt()
        else:
            err = ErrorCode.errUnavailable
        return err

    def disableInterrupt(self):
        if self.pinInt:
            err = self.pinInt.disableInterrupt()
        else:
            err = ErrorCode.errUnavailable
        return err

    def _getEventContext(self, event):
        pass  # TODO: this function, see original implementation

    # ErrorCode_t stc311x_getEventContext( const Device_Index_t devIdx,
    #                                      const gasgauge_Event_t event,
    #                                       gasgauge_EventContext_t *context )
    # {
    #     ErrorCode_t ret = errOk;
    #     uint8_t data8=0, clear8;
    #
    #     if( (devIdx == DEVICE_INDEX_INVALID) || (devIdx >= CONFIG_GASGAUGE_COUNT) || (context == NULL) )
    #     {
    #         ret = errInvalidParameter;
    #     } else if( event == gasgauge_EvtNone ) {
    #         ret = errFewData;
    #     } else if( event != gasgauge_EvtInt1 ) {
    #         ret = errCorruptData;
    #     } else {
    #
    #         ret = Serial_Bus_read_Reg_Byte( &dContext[devIdx].sdev, REG_CTRL, &data8 );
    #         if( ret == errOk )
    #         {
    #             context->source = gasgauge_EvtSrcUnknown;
    #     #if defined(CONFIG_GASGAUGE_IS_STC3117)
    #             clear8 = CTRL_IO0DATA | CTRL_BATFAIL | CTRL_ALM_SOC | CTRL_ALM_VOLT | CTRL_UVLOD;
    #     #else
    #             clear8 = CTRL_IO0DATA | CTRL_BATFAIL | CTRL_ALM_SOC | CTRL_ALM_VOLT;
    #     #endif
    #
    #             // Highest priority, as by reading, PORDET was cleared, so we don't get it another time!
    #             if( data8 & CTRL_PORDET )
    #             {
    #                 context->source = gasgauge_EvtSrcPOR;
    #             } else if( data8 & CTRL_ALM_VOLT )
    #             {
    #                 context->source = gasgauge_EvtSrcLowVolt;
    #                 context->detail.voltage = stc311x_getBatteryVoltage( devIdx );
    #                 clear8 &= ~CTRL_ALM_VOLT;
    #             } else if( data8 & CTRL_ALM_SOC )
    #             {
    #                 context->source = gasgauge_EvtSrcLowSOC;
    #                 context->detail.soc = stc311x_getStateOfCharge( devIdx );
    #                 clear8 &= ~CTRL_ALM_SOC;
    #             } else if( data8 & CTRL_BATFAIL )
    #             {
    #                 context->source = gasgauge_EvtSrcBatFail;
    #                 clear8 &= ~CTRL_BATFAIL;
    #             }
    #     #if defined(CONFIG_GASGAUGE_IS_STC3117)
    #             else if( data8 & CTRL_UVLOD )
    #             {
    #                 context->source = stc311x_EvtSrcUndervoltage;
    #                 clear8 &= ~CTRL_UVLOD;
    #             }
    #     #endif
    #
    #             if( context->source != gasgauge_EvtSrcUnknown )
    #             {
    #                 ret = Serial_Bus_write_Reg_Byte( &dContext[devIdx].sdev, REG_CTRL, clear8 );
    #             }
    #         }
    #     }
    #     return ret;
    # }

