# -*- coding: utf-8 -*-
"""Support module for the MAX77960 USB battery charger.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["MAX77960"]

from philander.max77960_reg import MAX77960_Reg

from philander.battery import Status as BatStatus
from philander.charger import Charger, Status as ChgStatus, DCStatus, PowerSrc,\
    TemperatureRating, ChargerError, EventSource
from philander.configurable import ConfigItem, Configurable
from philander.gpio import GPIO
from philander.imath import ctz, iprevpowtwo, vlbs
from philander.interruptable import Event, Interruptable, EventContextControl
from philander.serialbus import SerialBusDevice
from philander.sysfactory import SysFactory
from philander.systypes import ErrorCode, Info, RunLevel
from philander.watchdog import Watchdog


class MAX77960( MAX77960_Reg, SerialBusDevice, Charger, Configurable, Interruptable, Watchdog ):
    """Driver implementation for the MAX77960 USB battery charger.
    
    More information on the functionality of the chip can be found at
    the Analog site:
    https://www.analog.com/en/products/max77960.html
    """
        
    # The only address is 0x69. No alternative.
    ADDRESSES_ALLOWED = [0x69]

    # The watch dog time interval t(WD)as defined in the data sheet
    WATCHDOG_INTERVAL_MS = 80000
    
    # Revision tags, as translated from chip ID
    # to be compared with the result of getInfo()
    REVISION_MAJOR_5    = 5
    REVISION_MAJOR_6    = 6
    REVISION_MAJOR_MIN  = REVISION_MAJOR_5
    REVISION_MAJOR_MAX  = REVISION_MAJOR_6
    REVISION_MAJOR_MAX7796x = REVISION_MAJOR_5
    REVISION_MAJOR_MAX7796xB= REVISION_MAJOR_6
    REVISION_MINOR_MIN  = 0
    REVISION_MINOR_MAX  = 0x1F
    
    def getRegisterMap(self):
        return self._registerMap
    
    def getRegContentStr( self, regDescr, content ):
        ret=''
        if not regDescr[2]:    # No description of components/bits given
            ret = hex(content)
        else:
            for frag in regDescr[2]:
                shift = ctz( frag[0] )
                fragVal = (content & frag[0]) >> shift
                ret = ret + frag[1] + '=' + str(fragVal) + ' '
        return ret


    def getAllRegistersStr(self):
        ret = []
        for descr in self._registerMap:
            cont, err = self.readByteRegister( descr[0] )
            if (err == ErrorCode.errOk):
                contStr = self.getRegContentStr( descr, cont )
            else:
                cont = 0
                contStr = f"Read error: {err}"
            ret.append([descr[0], descr[1], cont, contStr])
        return ret

            
    #
    # Configurable options
    #
    
    CFG_COMM_MODE = 'Charger.Comm.Mode'
    CFG_DISIBS = 'Charger.DisIBS'
    CFG_MODE = 'Charger.Mode'
    CFG_PQEN = 'Charger.Prequal'
    CFG_CHG_RSTRT = 'Charger.Restart'
    CFG_STAT_EN = 'Charger.Stat'
    CFG_FCHGTIME = 'Charger.Timer.FastCharge'
    CFG_CHGCC = 'Charger.Current.FastCharge'
    CFG_TO_TIME = 'Charger.Timer.Topoff'
    CFG_TO_ITH = 'Charger.Current.Topoff'
    CFG_CHG_CV_PRM = 'Charger.Voltage.ChargeTermination'
    CFG_ITRICKLE = 'Charger.Current.Trickle'
    CFG_B2SOVRC = 'Charger.Current.Batt2Sys'
    CFG_JEITA_EN = 'Charger.Jeita'
    CFG_REGTEMP = 'Charger.Temp.Reg'
    CFG_VCHGCV_COOL = 'Charger.Voltage.Jeita.Term'
    CFG_ICHGCC_COOL = 'Charger.Current.Jeita.FastCharge'
    CFG_CHGIN_ILIM = 'Charger.Current.Input'
    CFG_OTG_ILIM = 'Charger.Current.OTG'
    CFG_MINVSYS = 'Charger.Voltage.MinVSys'
    CFG_VCHGIN_REG = 'Charger.Voltage.ChargeIn'

    _CONFIGURABLES = {
        # cfg string    : (register offset, register bit mask, default value) 
        CFG_COMM_MODE   : (0, MAX77960_Reg.COMM_MODE,   MAX77960_Reg.COMM_MODE_DEFAULT),
        CFG_DISIBS      : (0, MAX77960_Reg.DISIBS,      MAX77960_Reg.DISIBS_DEFAULT),
        CFG_MODE        : (0, MAX77960_Reg.MODE,        MAX77960_Reg.MODE_DEFAULT),
        CFG_PQEN        : (1, MAX77960_Reg.PQEN,        MAX77960_Reg.PQEN_DEFAULT),
        CFG_CHG_RSTRT   : (1, MAX77960_Reg.CHG_RSTRT,   MAX77960_Reg.CHG_RSTRT_DEFAULT),
        CFG_STAT_EN     : (1, MAX77960_Reg.STAT_EN,     MAX77960_Reg.STAT_EN_DEFAULT),
        CFG_FCHGTIME    : (1, MAX77960_Reg.FCHGTIME,    MAX77960_Reg.FCHGTIME_DEFAULT),
        CFG_CHGCC       : (2, MAX77960_Reg.CHGCC,       MAX77960_Reg.CHGCC_DEFAULT),
        CFG_TO_TIME     : (3, MAX77960_Reg.TO_TIME,     MAX77960_Reg.TO_TIME_DEFAULT),
        CFG_TO_ITH      : (3, MAX77960_Reg.TO_ITH,      MAX77960_Reg.TO_ITH_DEFAULT),
        CFG_CHG_CV_PRM  : (4, MAX77960_Reg.CHG_CV_PRM,  MAX77960_Reg.CHG_CV_PRM_DEFAULT),
        CFG_ITRICKLE    : (5, MAX77960_Reg.ITRICKLE,    MAX77960_Reg.ITRICKLE_DEFAULT),
        CFG_B2SOVRC     : (5, MAX77960_Reg.B2SOVRC,     MAX77960_Reg.B2SOVRC_DEFAULT),
        #skip config register 06
        CFG_JEITA_EN    : (7, MAX77960_Reg.JEITA_EN,    MAX77960_Reg.JEITA_EN_DEFAULT),
        CFG_REGTEMP     : (7, MAX77960_Reg.REGTEMP,     MAX77960_Reg.REGTEMP_DEFAULT),
        CFG_VCHGCV_COOL : (7, MAX77960_Reg.VCHGCV_COOL, MAX77960_Reg.VCHGCV_COOL_DEFAULT),
        CFG_ICHGCC_COOL : (7, MAX77960_Reg.ICHGCC_COOL, MAX77960_Reg.ICHGCC_COOL_DEFAULT),
        CFG_CHGIN_ILIM  : (8, MAX77960_Reg.CHGIN_ILIM,  MAX77960_Reg.CHGIN_ILIM_DEFAULT),
        CFG_OTG_ILIM    : (9, MAX77960_Reg.OTG_ILIM,    MAX77960_Reg.OTG_ILIM_DEFAULT),
        CFG_MINVSYS     : (9, MAX77960_Reg.MINVSYS,     MAX77960_Reg.MINVSYS_DEFAULT),
        CFG_VCHGIN_REG  : (10, MAX77960_Reg.VCHGIN_REG, MAX77960_Reg.VCHGIN_REG_DEFAULT),
    }
    
    def __init__( self ):
        # Specific instance attributes
        self.pinInt = None
        # Call constructors of the super class
        super().__init__()

    #
    # Helper functions
    #
    
    def checkID(self):
        """Reads the chip ID and verifies it against the expected value.
        """
        info, err = self.getInfo()
        if (err == ErrorCode.errOk):
            if (info.revMajor < MAX77960.REVISION_MAJOR_MIN) or \
               (info.revMajor > MAX77960.REVISION_MAJOR_MAX) or \
               (info.revMinor < MAX77960.REVISION_MINOR_MIN) or \
               (info.revMinor > MAX77960.REVISION_MINOR_MAX):
                err = ErrorCode.errSpecRange
        return err
    
    def _lockRegisters(self):
        self.writeByteRegister( MAX77960_Reg.REG_CHG_CNFG_06, MAX77960_Reg.CHGPROT_LOCK | MAX77960_Reg.WDTCLR_DO_NOT_TOUCH )

    def _unlockRegisters(self):
        self.writeByteRegister( MAX77960_Reg.REG_CHG_CNFG_06, MAX77960_Reg.CHGPROT_UNLOCK | MAX77960_Reg.WDTCLR_DO_NOT_TOUCH )


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
        Charger.Comm.Mode                    ``int`` Communication mode; default is :attr:`.COMM_MODE_DEFAULT`.
        Charger.DisIBS                       ``int`` ; default is :attr:`.DISIBS_DEFAULT`.
        Charger.Mode                         ``int`` ; default is :attr:`.MODE_DEFAULT`.
        Charger.Prequal                      ``int`` ; default is :attr:`.PQEN_DEFAULT`.
        Charger.Restart                      ``int`` ; default is :attr:`.CHG_RSTRT_DEFAULT`.
        Charger.Stat                         ``int`` ; default is :attr:`.STAT_EN_DEFAULT`.
        Charger.Timer.FastCharge             ``int`` ; default is :attr:`.FCHGTIME_DEFAULT`.
        Charger.Current.FastCharge           ``int`` ; default is :attr:`.CHGCC_DEFAULT`.
        Charger.Timer.Topoff                 ``int`` ; default is :attr:`.TO_TIME_DEFAULT`.
        Charger.Current.Topoff               ``int`` ; default is :attr:`.TO_ITH_DEFAULT`.
        Charger.Voltage.ChargeTermination    ``int`` ; default is :attr:`.CHG_CV_PRM_DEFAULT`.
        Charger.Current.Trickle              ``int`` ; default is :attr:`.ITRICKLE_DEFAULT`.
        Charger.Current.Batt2Sys             ``int`` ; default is :attr:`.B2SOVRC_DEFAULT`.
        Charger.Jeita                        ``int`` ; default is :attr:`.JEITA_EN_DEFAULT`.
        Charger.Temp.Reg                     ``int`` ; default is :attr:`.REGTEMP_DEFAULT`.
        Charger.Voltage.Jeita.Term           ``int`` ; default is :attr:`.VCHGCV_COOL_DEFAULT`.
        Charger.Current.Jeita.FastCharge     ``int`` ; default is :attr:`.ICHGCC_COOL_DEFAULT`.
        Charger.Current.Input                ``int`` ; default is :attr:`.CHGIN_ILIM_DEFAULT`.
        Charger.Current.OTG                  ``int`` ; default is :attr:`.OTG_ILIM_DEFAULT`.
        Charger.Voltage.MinVSys              ``int`` ; default is :attr:`.MINVSYS_DEFAULT`.
        Charger.Voltage.ChargeIn             ``int`` ; default is :attr:`.VCHGIN_REG_DEFAULT`.
        All Charger.int.gpio.* settings as documented at :meth:`.GPIO.Params_init`.
        ===============================================================================================================================================
        
        Also see: :meth:`.Charger.Params_init`, :meth:`.SerialBusDevice.Params_init`, :meth:`.GPIO.Params_init`. 
        """
        # Override default base class parameter: serial bus device address
        paramDict["SerialBusDevice.address"] = cls.ADDRESSES_ALLOWED[0]
        # Add interrupt pin /gpio specifics
        paramDict["Charger.int.gpio.direction"] = GPIO.DIRECTION_IN
        # If not present, add settings different from hardware reset values
        defaults = {
            "Charger.Comm.Mode" :           MAX77960_Reg.COMM_MODE_I2C,
            "Charger.int.gpio.trigger":    GPIO.TRIGGER_EDGE_FALLING,
            "Charger.int.gpio.bounce" :    GPIO.BOUNCE_NONE,
            }
        for key, value in defaults.items():
            if not key in paramDict:
                paramDict[key] = value
        # Add other charger configurables (defaults)
        for key, (_, _, dflt) in MAX77960._CONFIGURABLES.items():
            if not key in paramDict:
                paramDict[key] = dflt
        
        gpioParams = {}
        GPIO.Params_init( gpioParams )
        gp = dict( [("Charger.int."+k,v) for k,v in gpioParams.items()] )
        for key, value in gp.items():
            if not( key in paramDict):
                paramDict[key] = value
        # Let the base class(es) do the rest
        SerialBusDevice.Params_init(paramDict)
        Watchdog.Params_init(paramDict)
        return None


    def open(self, paramDict):
        # Get default parameters
        defParam = {}
        MAX77960.Params_init( defParam )
        # Open the bus device
        paramDict["SerialBusDevice.address"] = MAX77960.ADDRESSES_ALLOWED[0]
        ret = SerialBusDevice.open(self, paramDict)
        # Configure the sensor
        if (ret == ErrorCode.errOk):
            # Account for defaults different from hardware-resets
            for key in (MAX77960.CFG_COMM_MODE,):
                if not key in paramDict:
                    paramDict[key] = defParam[key]
            # Note that config registers #1, 2, 3, 4, 5, 7, 8, 9
            # are write protected (locked), while #0, 6, 10 are not.
            # REG_CHG_CNFG_00, 01, 02, 03, ...
            mask=[ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            data=[ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            for key, (regoff, msk, dflt) in MAX77960._CONFIGURABLES.items():
                if (key in paramDict) and (paramDict[key] != dflt):
                    value = paramDict[key]
                    if key==MAX77960.CFG_CHGIN_ILIM:
                        if value < 100:
                            value = MAX77960_Reg.CHGIN_ILIM_100
                        elif value > 6300:
                            value = MAX77960_Reg.CHGIN_ILIM_6300
                        else:
                            value = value // 50 + 1
                    mask[regoff] |= msk
                    data[regoff] |= value
        
            self._unlockRegisters()
            for idx in range( 11 ):
                if mask[idx] != 0:
                    reg = MAX77960_Reg.REG_CHG_CNFG_00 + idx
                    # Copy masked bits to the register content
                    value, _ = self.readByteRegister( reg )
                    value = value & ~mask[idx]
                    value = value | data[idx]
                    ret = self.writeByteRegister(reg, value)
            self._lockRegisters()
        # Setup interrupt related stuff.
        if (ret == ErrorCode.errOk):
            if ("Charger.int.gpio.pinDesignator" in paramDict):
                paramDict["Charger.int.gpio.direction"] = GPIO.DIRECTION_IN
                gpioParams = dict( [(k.replace("Charger.int.", ""),v) for k,v in paramDict.items() if k.startswith("Charger.int.")] )
                self.pinInt = SysFactory.getGPIO()
                ret = self.pinInt.open( gpioParams )
                self.enableInterrupt()
        return ret


    def close(self):
        if not (self.pinInt is None):
            self.pinInt.close()
            self.pinInt = None
        ret = super().close()
        return ret

    def setRunLevel(self, level):
        ret = ErrorCode.errOk
        if (level <= RunLevel.snooze):
            data, ret = self.readByteRegister( MAX77960_Reg.REG_CHG_CNFG_00 )
            if (ret == ErrorCode.errOk):
                data &= ~MAX77960_Reg.STBY_EN
                ret = self.writeByteRegister( MAX77960_Reg.REG_CHG_CNFG_00, data )
        else:
            data, ret = self.readByteRegister( MAX77960_Reg.REG_CHG_CNFG_00 )
            if (ret == ErrorCode.errOk):
                data |= MAX77960_Reg.STBY_EN
                ret = self.writeByteRegister( MAX77960_Reg.REG_CHG_CNFG_00, data )
        return ret

    #
    # Charger API
    #
    
    def reset(self):
        err = self.writeByteRegister(MAX77960_Reg.REG_SWRST, MAX77960_Reg.SWRST_TYPE_O)
        return err

    def getInfo(self):
        info = Info()
        # Chip ID, silicon revision and OTP recipe version
        info.chipID, ret = self.readByteRegister(MAX77960_Reg.REG_CID)
        if (ret.isOk()):
            # Get silicon revision from the same register
            info.revMajor = (info.chipID & MAX77960_Reg.CID_REVISION) >> 5
            info.revMinor = info.chipID & MAX77960_Reg.CID_VERSION
            info.validity = info.validChipID \
                            | info.validRevMajor | info.validRevMinor
        return info, ret

    def isBatteryPresent(self):
        data, ret = self.readByteRegister( MAX77960_Reg.REG_CHG_DETAILS_01 )
        if (ret.isOk()):
            data = data & MAX77960_Reg.BAT_DTLS
            if (data == MAX77960_Reg.BAT_DTLS_REMOVAL):
                ret = ErrorCode.errUnavailable
        elif (ret == ErrorCode.errUnavailable):
            ret = ErrorCode.errMalfunction
        return ret
    
    def getNumCells(self):
        ret = -1
        data, err = self.readByteRegister( MAX77960_Reg.REG_CHG_DETAILS_02 )
        if (err.isOk()):
            data = data & MAX77960_Reg.NUM_CELL_DTLS
            if data == MAX77960_Reg.NUM_CELL_DTLS_3:
                ret = 3
            else:
                ret = 2
        return ret
    
    def getBatStatus(self):
        ret = BatStatus.unknown
        data, err = self.readByteRegister( MAX77960_Reg.REG_CHG_DETAILS_01 )
        if (err.isOk()):
            ds = data & MAX77960_Reg.BAT_DTLS
            if ds == MAX77960_Reg.BAT_DTLS_REMOVAL:
                ret = BatStatus.removed
            elif ds == MAX77960_Reg.BAT_DTLS_BELOW_PREQ:
                ret = BatStatus.empty
            elif ds == MAX77960_Reg.BAT_DTLS_TIME_OUT:
                ret = BatStatus.broken
            elif ds == MAX77960_Reg.BAT_DTLS_OK:
                ret = BatStatus.normal
            elif ds == MAX77960_Reg.BAT_DTLS_LOW_VOLT:
                ret = BatStatus.low
            elif ds == MAX77960_Reg.BAT_DTLS_OVR_VOLT:
                ret = BatStatus.overvoltage
            elif ds == MAX77960_Reg.BAT_DTLS_OVR_CURR:
                ret = BatStatus.overcurrent
        return ret
    
    def getChgStatus(self):
        ret = ChgStatus.unknown
        data, err = self.readByteRegister( MAX77960_Reg.REG_CHG_DETAILS_01 )
        if (err.isOk()):
            cd = data & MAX77960_Reg.CHG_DTLS
            if cd == MAX77960_Reg.CHG_DTLS_PRECHRG:
                bd = data & MAX77960_Reg.BAT_DTLS
                if bd == MAX77960_Reg.BAT_DTLS_BELOW_PREQ:
                    ret = ChgStatus.preCharge
                else:
                    ret = ChgStatus.trickle
            elif cd == MAX77960_Reg.CHG_DTLS_FAST_CURR:
                ret = ChgStatus.fastChargeConstCurrent
            elif cd == MAX77960_Reg.CHG_DTLS_FAST_VOLT:
                ret = ChgStatus.fastChargeConstVoltage
            elif cd == MAX77960_Reg.CHG_DTLS_TOP_OFF:
                ret = ChgStatus.topOff
            elif cd == MAX77960_Reg.CHG_DTLS_DONE:
                ret = ChgStatus.done
            else:
                ret = ChgStatus.off
        return ret
    
    def getDCStatus(self):
        ret = DCStatus.unknown
        data, err = self.readByteRegister( MAX77960_Reg.REG_CHG_DETAILS_00 )
        if (err.isOk()):
            ds = data & MAX77960_Reg.CHGIN_DTLS
            if ds == MAX77960_Reg.CHGIN_DTLS_GOOD:
                ret = DCStatus.valid
            elif ds == MAX77960_Reg.CHGIN_DTLS_TOO_LOW:
                ret = DCStatus.undervoltage
            elif ds == MAX77960_Reg.CHGIN_DTLS_TOO_HIGH:
                ret = DCStatus.overvoltage
        return ret
      
    def getPowerSrc(self):
        ret = PowerSrc.unknown
        data, err = self.readByteRegister( MAX77960_Reg.REG_CHG_DETAILS_00 )
        if (err.isOk()):
            chgin = data & MAX77960_Reg.CHGIN_DTLS
            qbat = data & MAX77960_Reg.QB_DTLS
            if (chgin == MAX77960_Reg.CHGIN_DTLS_GOOD):
                # Valid CHGIN, so external power is the primary source
                ret |= PowerSrc.dc
            if (qbat == MAX77960_Reg.QB_DTLS_ON):
                ret |= PowerSrc.bat
        return ret

    def getChargerTempStatus(self):
        ret = TemperatureRating.unknown
        data, err = self.readByteRegister( MAX77960_Reg.REG_CHG_DETAILS_01 )
        if (err.isOk()):
            chg = data & MAX77960_Reg.CHG_DTLS
            if chg == MAX77960_Reg.CHG_DTLS_OFF_TEMP:
                ret = TemperatureRating.hot
            else:
                treg = data & MAX77960_Reg.TREG
                if (treg == MAX77960_Reg.TREG_HIGH):
                    ret = TemperatureRating.warm
                else:
                    ret = TemperatureRating.ok
        return ret

    def getBatteryTempStatus(self):
        ret = TemperatureRating.unknown
        data, err = self.readByteRegister( MAX77960_Reg.REG_CHG_DETAILS_02 )
        if (err.isOk()):
            thm = data & MAX77960_Reg.THM_DTLS
            if thm == MAX77960_Reg.THM_DTLS_COLD:
                ret = TemperatureRating.cold
            elif thm == MAX77960_Reg.THM_DTLS_COOL:
                ret = TemperatureRating.cool
            elif thm == MAX77960_Reg.THM_DTLS_NORMAL:
                ret = TemperatureRating.ok
            elif thm == MAX77960_Reg.THM_DTLS_WARM:
                ret = TemperatureRating.warm
            elif thm == MAX77960_Reg.THM_DTLS_HOT:
                ret = TemperatureRating.hot
            else:   # Battery removed or temperature monitoring disabled.
                ret = TemperatureRating.unknown
        return ret

    def getError(self):
        ret = ChargerError.unknown
        data, err = self.readByteRegister( MAX77960_Reg.REG_CHG_DETAILS_01 )
        if (err.isOk()):
            chg = data & MAX77960_Reg.CHG_DTLS
            if chg == MAX77960_Reg.CHG_DTLS_OFF_RESIST:
                ret = ChargerError.config
            elif chg == MAX77960_Reg.CHG_DTLS_E_TIMER:
                ret = ChargerError.timer
            elif chg == MAX77960_Reg.CHG_DTLS_SUSP_QBAT:
                ret = ChargerError.batBroken
            elif chg == MAX77960_Reg.CHG_DTLS_OFF_CHGIN:
                data, err = self.readByteRegister( MAX77960_Reg.REG_CHG_DETAILS_00 )
                if (err.isOk()):
                    chgin = data & MAX77960_Reg.CHG_DTLS
                    if chgin == MAX77960_Reg.CHGIN_DTLS_TOO_HIGH:
                        ret = ChargerError.dcHigh
                    elif chgin == MAX77960_Reg.CHGIN_DTLS_TOO_LOW:
                        ret = ChargerError.dcLow
                    else:
                        ret = ChargerError.dc
            elif chg == MAX77960_Reg.CHG_DTLS_OFF_TEMP:
                ret = ChargerError.tempChg
            elif chg == MAX77960_Reg.CHG_DTLS_OFF_WDOG:
                ret = ChargerError.config
            elif chg == MAX77960_Reg.CHG_DTLS_SUSP_JEITA:
                ret = ChargerError.tempBat
            elif chg == MAX77960_Reg.CHG_DTLS_SUSP_NOBAT:
                ret = ChargerError.batRemoved
            else:
                ret = ChargerError.ok
        return ret

    def restartCharging(self):
        # To recover from timer fault, switch charger off...
        data = MAX77960_Reg.COMM_MODE_I2C | MAX77960_Reg.DISIBS_FET_PPSM | \
               MAX77960_Reg.STBY_EN_DCDC_PPSM | MAX77960_Reg.WDTEN_OFF 
        ret = self.writeByteRegister( MAX77960_Reg.REG_CHG_CNFG_00,
                                      data | MAX77960_Reg.MODE_DCDC_ONLY )
        # ... and on again.
        if (ret.isOk()):
            ret = self.writeByteRegister( MAX77960_Reg.REG_CHG_CNFG_00,
                                          data | MAX77960_Reg.MODE_CHRG_DCDC )
        return ret

    #
    # Interruptable API
    #
    
    def registerInterruptHandler(self, onEvent=None, callerFeedBack=None, handler=None ):
        ret = ErrorCode.errOk
        if ((onEvent == Event.evtInt1) or (onEvent == Event.evtAny)) and not (self.pinInt is None):
            self.pinInt.registerInterruptHandler( GPIO.EVENT_DEFAULT, callerFeedBack, handler )
            ret = self.enableInterrupt()
        else:
            ret = ErrorCode.errExhausted
        return ret
        
    def _mapIntApi2Impl( self, apiMask ):
        """Maps API :class:`.charger.EventSource` to the \
        implementation-level interrupts as follows:
        
            REG_TOP_INT: :attr:`.MAX7760._TSHDN_I`      <-> :attr:`.charger.EventSource.thermalShutdown`
            REG_TOP_INT: :attr:`.MAX7760._SYSOVLO_I`    <-> :attr:`.charger.EventSource.systemOvervoltage`
            REG_TOP_INT: :attr:`.MAX7760._SYSUVLO_I`    <-> :attr:`.charger.EventSource.systemUndervoltage`
            REG_CHG_INT: :attr:`.MAX7760._AICL_I`       <-> :attr:`.charger.EventSource.inputCurrentLimitSrc`
            REG_CHG_INT: :attr:`.MAX7760._CHGIN_I`      <-> :attr:`.charger.EventSource.inputVoltage`
            REG_CHG_INT: :attr:`.MAX7760._B2SOVRC_I`    <-> :attr:`.charger.EventSource.batteryOvercurrent`
            REG_CHG_INT: :attr:`.MAX7760._CHG_I`        <-> :attr:`.charger.EventSource.chargingPhase`
            REG_CHG_INT: :attr:`.MAX7760._BAT_I`        <-> :attr:`.charger.EventSource.batteryTemperature`
            REG_CHG_INT: :attr:`.MAX7760._CHGINLIM_I`   <-> :attr:`.charger.EventSource.inputCurrentLimitOwn`
            REG_CHG_INT: :attr:`.MAX7760._DISQBAT_I`    <-> :attr:`.charger.EventSource.onOff`
            REG_CHG_INT: :attr:`.MAX7760._OTG_PLIM_I`   <-> :attr:`.charger.EventSource.internal`
            
        """
        topMask = 0
        chgMask = 0
        
        if (apiMask & EventSource.thermalShutdown):
            topMask = topMask | MAX77960_Reg.TSHDN_M
        if (apiMask & EventSource.systemOvervoltage):
            topMask = topMask | MAX77960_Reg.SYSOVLO_M
        if (apiMask & EventSource.systemUndervoltage):
            topMask = topMask | MAX77960_Reg.SYSUVLO_M

        if (apiMask & EventSource.inputCurrentLimitSrc):
            chgMask = chgMask | MAX77960_Reg.AICL_M
        if (apiMask & EventSource.inputVoltage):
            chgMask = chgMask | MAX77960_Reg.CHGIN_M
        if (apiMask & EventSource.batteryOvercurrent):
            chgMask = chgMask | MAX77960_Reg.B2SOVRC_M
        if (apiMask & EventSource.chargingPhase):
            chgMask = chgMask | MAX77960_Reg.CHG_M
        if (apiMask & EventSource.batteryTemperature):
            chgMask = chgMask | MAX77960_Reg.BAT_M
        if (apiMask & EventSource.inputCurrentLimitOwn):
            chgMask = chgMask | MAX77960_Reg.CHGINLIM_M
        if (apiMask & EventSource.onOff):
            chgMask = chgMask | MAX77960_Reg.DISQBAT_M
        if (apiMask & EventSource.internal):
            chgMask = chgMask | MAX77960_Reg.OTG_PLIM_M
        return [topMask, chgMask]
            
        
    def _mapIntImpl2Api( self, topMask, chgMask ):
        """Maps implementation-level interrupts to API event sources.
        
        For the detailed mapping, see :meth:`_mapIntApi2Impl`.
        """
        intMask = EventSource.none
        if (topMask & MAX77960_Reg.TSHDN_M):
            intMask = intMask | EventSource.thermalShutdown
        if (topMask & MAX77960_Reg.SYSOVLO_M):
            intMask = intMask | EventSource.systemOvervoltage
        if (topMask & MAX77960_Reg.SYSUVLO_M):
            intMask = intMask | EventSource.systemUndervoltage
        
        if (chgMask & MAX77960_Reg.AICL_M):
            intMask = intMask | EventSource.inputCurrentLimitSrc
        if (chgMask & MAX77960_Reg.CHGIN_M):
            intMask = intMask | EventSource.inputVoltage
        if (chgMask & MAX77960_Reg.B2SOVRC_M):
            intMask = intMask | EventSource.batteryOvercurrent
        if (chgMask & MAX77960_Reg.CHG_M):
            intMask = intMask | EventSource.chargingPhase
        if (chgMask & MAX77960_Reg.BAT_M):
            intMask = intMask | EventSource.batteryTemperature
        if (chgMask & MAX77960_Reg.CHGINLIM_M):
            intMask = intMask | EventSource.inputCurrentLimitOwn
        if (chgMask & MAX77960_Reg.DISQBAT_M):
            intMask = intMask | EventSource.onOff
        if (chgMask & MAX77960_Reg.OTG_PLIM_M):
            intMask = intMask | EventSource.internal
        return intMask

    def enableInterrupt(self):
        return ErrorCode.errOk

    def disableInterrupt(self):
        return ErrorCode.errOk

    def getEventContext(self, event, context):
        """Retrieve more detailed information on an event.
        
        The ``event`` parameter should be :attr:`.interruptable.Event.evtInt1`,
        as there is only this one interrupt line.
        On return, the ``context`` parameter carries the resulting
        information. It must be an instance of :class:`.charger.EventContext`,
        which is semantically multiplexed by its :attr:`.charger.EventContext.source`
        attribute. 
        
        Also see: :meth:`.Interruptable.getEventContext`.

        :param int event: The original event occurred.
        :param .charger.EventContext context: Context information. 
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        
        if (context is None):
            ret = ErrorCode.errInvalidParameter
        elif( not self.isAttached() ):
            ret = ErrorCode.errResourceConflict
        elif( event == Event.evtNone ):
            ret = ErrorCode.errFewData
        elif ((event == Event.evtInt1) or (event == Event.evtAny)):
            ret = ErrorCode.errOk
            # Retrieving the interrupt status resets all bits in these registers!
            if( context.control == EventContextControl.clearAll ):
                _, ret = self.readByteRegister( MAX77960_Reg.REG_TOP_INT )
                _, ret = self.readByteRegister( MAX77960_Reg.REG_CHG_INT )
                context.remainInt = 0;
                context.source = EventSource.none
            else:
                if (context.control == EventContextControl.getFirst):
                    topStatus, ret = self.readByteRegister( MAX77960_Reg.REG_TOP_INT )
                    chgStatus, ret = self.readByteRegister( MAX77960_Reg.REG_CHG_INT )
                    context.remainInt = self._mapIntImpl2Api( topStatus, chgStatus )
                    context.control = EventContextControl.getNext
                elif (context.control == EventContextControl.getLast):
                    topStatus, ret = self.readByteRegister( MAX77960_Reg.REG_TOP_INT )
                    chgStatus, ret = self.readByteRegister( MAX77960_Reg.REG_CHG_INT )
                    context.remainInt = self._mapIntImpl2Api( topStatus, chgStatus )
                    context.control = EventContextControl.getPrevious
                if (ret.isOk()):
                    if (context.remainInt == 0):
                        ret = ErrorCode.errFewData
                    else:
                        if (context.control == EventContextControl.getNext):
                            # Find value of highest bit:
                            context.source = iprevpowtwo( context.remainInt )
                        else:
                            # Find (value of) least bit set:
                            context.source = vlbs( context.remainInt )
                        context.remainInt &= ~context.source
                        if ((ret.isOk()) and (context.remainInt != 0)):
                            ret = ErrorCode.errMoreData
        else:
            ret = ErrorCode.errInvalidParameter
        return ret
    
    #
    # Configurable API
    #
    
    def configure(self, configData):
        ret = ErrorCode.errNotSupported
        if (configData.item == ConfigItem.eventArm):
            # Clear current interrupts
            self.readByteRegister( MAX77960_Reg.REG_TOP_INT )
            self.readByteRegister( MAX77960_Reg.REG_CHG_INT )
            # Un-mask specified interrupts
            [topMask, chgMask] = self._mapIntApi2Impl(configData.value)
            self.writeByteRegister( MAX77960_Reg.REG_TOP_INT_MASK, ~topMask )
            ret = self.writeByteRegister( MAX77960_Reg.REG_CHG_INT_MASK, ~chgMask )
        return ret
    
    
    #
    # The Watchdog API
    #
    
    def enableWatchdog(self):
        ret = self.enableReg( MAX77960_Reg.REG_CHG_CNFG_00, MAX77960_Reg.WDTEN )
        return ret
    
    def disableWatchdog(self):
        ret = self.disableReg( MAX77960_Reg.REG_CHG_CNFG_00, MAX77960_Reg.WDTEN )
        return ret
    
    def isWatchdogRunning(self):
        data, ret = self.readByteRegister( MAX77960_Reg.REG_CHG_CNFG_00 )
        if (ret.isOk()):
            if (data & MAX77960_Reg.WDTEN) == MAX77960_Reg.WDTEN_ON:
                ret = ErrorCode.errOk
            else:
                ret = ErrorCode.errUnavailable
        return ret

    def clearWatchdog(self):
        data, ret = self.readByteRegister( MAX77960_Reg.REG_CHG_CNFG_06 )
        if (ret.isOk()):
            data = (data & ~MAX77960_Reg.WDTCLR) | MAX77960_Reg.WDTCLR_DO_CLEAR
            ret = self.writeByteRegister( MAX77960_Reg.REG_CHG_CNFG_06, data )
        return ret

    def isWatchdogElapsed(self):
        data, ret = self.readByteRegister( MAX77960_Reg.REG_CHG_DETAILS_01 )
        if (ret.isOk()):
            if (data & MAX77960_Reg.CHG_DTLS) == MAX77960_Reg.CHG_DTLS_OFF_WDOG:
                ret = ErrorCode.errOk
            else:
                ret = ErrorCode.errUnavailable
        return ret

    def clearWatchdogElapsed(self):
        # Restart the charger by clearing the WD flag.
        ret = self.clearWatchdog()
        return ret
