"""RTC implementation for the M41T82 RTC by ST.

Detailed technical information for this chip can be found at:
https://www.st.com/en/clocks-and-timers/m41t82.html

Note that this chip provides alarms and a timer, but no interrupts!
So, the status of alarms and timer must be determined by polling the
:meth:`RTC.getStatus` function and matching the result against the
bit mask of interest.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["M41T82"]

import logging

from .rtc import RTC
from .serialbus import SerialBusDevice, SerialBusType, SerialBus
from .sysfactory import SysProvider
from .systypes import ErrorCode
from .watchdog import Watchdog

logger = logging.getLogger(__name__)

    
class M41T82( RTC, Watchdog ):
    """Implement both, the RTC- as well as the Watchdog-API.
    """
    
    ADDRESSES_ALLOWED = [0x68,]

    # Calibration techniques
    CALIB_TECH_ANALOGUE   = 1
    CALIB_TECH_DIGITAL    = 2
    CALIB_TECH_BOTH       = 3
    
    # Calibration limits, given in ppm
    CALIB_ANALOGUE_LIMIT_LOWER  = -15
    CALIB_ANALOGUE_LIMIT_UPPER  = 95
    CALIB_DIGITAL_LIMIT_LOWER  = -63
    CALIB_DIGITAL_LIMIT_UPPER  = 126
    
    
    def __init__(self):
        """Initialize the instance with defaults.
        """
        super().__init__()
        # Attributes of the super class
        self.numAlarms      = 2     # Number of alarms (ids) provided
        self.numTimers      = 1     # Number of timers (ids) provided
        self.lenUserData    = 7     # Number of bytes than can be stored as user data
        self.supportedStatus = RTC.STATUS_ALARM_0 | RTC.STATUS_ALARM_1 | \
                               RTC.STATUS_TIMER_0 | RTC.STATUS_OSC_FAIL | \
                               RTC.STATUS_BAT_LOW | RTC.STATUS_STOPPED
        self.provider = SysProvider.COMPOSITE
        # Attributes of this class
        # Date and time tuple of last access before most-recent power-down
        self.lastKnownAlive = None 
        self._serbusdev = None  # SerialBusDevice instance
        self._wdData = 0        # Watchdog register data
        self._bitFT = False     # FT shadow
        
    @classmethod
    def _getWatchdogData(cls, paramDict):
        ret = ErrorCode.errOk
        interval = paramDict.get("watchdog.interval", Watchdog.INTERVAL_MS_DEFAULT)
        if not isinstance( interval, int ):
            try:
                interval = int(interval)
            except ValueError as err:
                logger.debug("watchdog.interval=%s cannot be converted to int: %s",
                             interval, err)
                interval = 0
                ret = ErrorCode.errInvalidParameter
        if interval == 0:
            wdData = 0x03   # Counter=0, lowest frequency
        else:
            # (upper limit[ms], f.numerator[Hz], f.denominator, RB1:0)
            settings = ( (1968, 16, 1000, 0), (7875, 4, 1000, 1),
                         (31500, 1, 1000, 2), (126000, 1, 4000, 3) )
            tval = 0
            tcfg = settings[-1][3]  # lowest frequency
            if (interval < 31) or (interval > settings[-1][0]):
                ret = ErrorCode.errSpecRange
            else:
                for data in settings:
                    if interval <= data[0]: # Upper limit
                        tval = (interval * data[1] + data[2]//2) // data[2] 
                        if tval > 0x1F:
                            tval = 0x1F
                        tcfg = data[3]    # RB1:0
                        break
            wdData = (tval << 2) | tcfg
        logger.debug("interval=%s, wdData=0x%02x, ret=%s", interval, wdData, err)
        return wdData, ret

    #
    # For mapping the capacitive load correction x[pF] to the resulting
    # calibration value in analogue calibration, the corresponding
    # mapping function is roughly: y[ppm] = a*x / (b+x) + c*x
    # with a=-127, b=38, c=1.06, when x in pF.
    # For the register content analog = 4*x: a->a, b->4*b, c->c/4
    # So: a=-127, b=152, c=0.265=53/200
    #
    # ppm = -127*analog / (152+analog) + 53*analog/200
    #     = (-127*analog*200 + 53*analog*(152+analog)) / ((152+analog)*200)
    #     = analog*(-127*200 + 53*(152+analog)) / ((152+analog)*200)
    #     = analog*(-127*200 + 53*152 + 53*analog) / ((152+analog)*200)
    #     = analog*(53*analog-17344) / ((152+analog)*200)
    #     = _aNumerator(analog) / _aDenominator(analog)
    #

    @classmethod
    def _aNumerator(cls, k):
        return k * (53 * k - 17344)

    @classmethod
    def _aDenominator(cls, k):
        return 200 * (152 + k)


    @classmethod
    def _calibAnalogReg2ppm(cls, analog):
        """Calculate effective calibration in ppm from a given analogue register content.
        
        :param int analog: Unsigned content of the analogue calibration register ACS:AC6-0
        :return: The total calibration expresed in ppm and\
        An error code indicating either success or the reason of failure.
        :rtype: int, ErrorCode
        """
        ppm=0
        ret = ErrorCode.errOk
        if (analog > 0xFF):
            ret = ErrorCode.errSpecRange
        else:
            if analog & 0x80:   # ACS=1 -> Positive calibration, but negative capacitive offset
                analog = -(analog & 0x7F)
            # Now we have the capacitive offset in 1/4 pF
            # Apply range limits -18 ... +9.75 pF
            analog = -72 if (analog < -72) else 39 if (analog > 39) else analog
            divisor = cls._aDenominator(analog)
            ppm = (cls._aNumerator(analog) + divisor//2) // divisor
        return ppm, ret

    @classmethod
    def _calibDigitalReg2ppm(cls, digital):
        """Calculate effective calibration in ppm from a given digital register content.
        
        :param int digital: Unsigned content of the digital calibration register DCS:DC4-0
        :return: The total calibration expresed in ppm and\
        An error code indicating either success or the reason of failure.
        :rtype: int, ErrorCode
        """
        ppm=0
        ret = ErrorCode.errOk
        if (digital > 0x3F):
            ret = ErrorCode.errSpecRange
        else:
            if digital & 0x20:  # DCS=1 -> Positive calibration!
                # Factor: 1'000'000 / (8*60 * 512) = 3125 / 768 ~ 4.069
                ppm = ((digital & 0x1F) * 3125 + 384) // 768
            else:   # DCS=0 -> Negative calibration!
                # Factor: 1'000'000 / (16*60 * 512) = 3125 / 1536 ~ 2.0345
                ppm = -((digital * 3125 + 768) // 1536)
        return  ppm, ret

    @classmethod
    def _calibPPM2AnalogReg(cls, ppm):
        """Calculate analog calibration register content from a ppm value.        
        
        :param int ppm: The calibration expressed in ppm.
        :return: The analog unsigned content of the calibration register ACS:AC6-0 and\
        An error code indicating either success or the reason of failure.
        :rtype: int, ErrorCode
        """
        analog = 0
        ret = ErrorCode.errOk
        if (ppm < M41T82.CALIB_ANALOGUE_LIMIT_LOWER) or (ppm > M41T82.CALIB_ANALOGUE_LIMIT_UPPER):
            ret = ErrorCode.errSpecRange
        else:
            # Binary search (Bisection)
            lowerBound = -72
            upperBound = 39
            
            # ppm(reg) falls steadily
            while lowerBound < upperBound:
                mid = (lowerBound + upperBound) // 2
                if ppm * cls._aDenominator(mid) < cls._aNumerator(mid):
                    lowerBound = mid + 1
                else:
                    upperBound = mid
            # True value is in [lowerBound-1, lowerBound]
            # Pick the better one.
            analog = lowerBound
            if lowerBound > -72:
                err_left  = abs(ppm * cls._aDenominator(lowerBound-1) - cls._aNumerator(lowerBound-1))
                err_right = abs(ppm * cls._aDenominator(lowerBound) - cls._aNumerator(lowerBound))
                if err_left * cls._aDenominator(lowerBound) <= err_right * cls._aDenominator(lowerBound-1):
                    analog -= 1
            # Encode according to register spec
            analog = (-analog | 0x80) if analog < 0 else analog
        return analog, ret

    @classmethod
    def _calibPPM2DigitalReg(cls, ppm):
        """Calculate digital calibration register content from a ppm value.        
        
        :param int ppm: The calibration expressed in ppm.
        :return: The digital unsigned content of the calibration register DCS:DC4-0 and\
        An error code indicating either success or the reason of failure.
        :rtype: int, ErrorCode
        """
        digital = 0
        ret = ErrorCode.errOk
        if (ppm < M41T82.CALIB_DIGITAL_LIMIT_LOWER) or (ppm > M41T82.CALIB_DIGITAL_LIMIT_UPPER):
            ret = ErrorCode.errSpecRange
        else:
            if ppm > 0:
                digital = (ppm * 768 + 1562) // 3125
                digital |= 0x20
            else:
                digital = ((-ppm) * 1536 + 1562) // 3125
        return digital, ret

    #
    # Module API
    #

    @classmethod
    def Params_init( cls, paramDict ):
        """Initialize parameters with default values.
        
        Supported key names and their meanings are:

        ===========================    ===============================================================================================
        Key                            Range(Default), Meaning 
        ===========================    ===============================================================================================
        rtc.alarm2.enable              {True|False} (True) Either use Alarm2 or increase user data space.
        rtc.ft.enable                  {True|False} (False) If True, set the FT bit and enable frequency output on FT/RST pin.
        rtc.SerialBusDevice.*          Serial bus device config; See :meth:`.SerialBusDevice.Params_init`.
        rtc.SerialBus.*                Serial bus configuration; See :meth:`.SerialBus.Params_init`.
        watchdog.*                     Any watchdog-related settings.
        ===========================    ===============================================================================================
        
        :param dict(str, object) paramDict: Dictionary of configuration settings.
        :return: none
        :rtype: None
        """
        prefix = cls.MODULE_PARAM_PREFIX + "."
        serDict = cls._extractParams( paramDict, prefix)
        # Add mandatory settings
        serDict[SerialBus.MODULE_PARAM_PREFIX + ".type"] = SerialBusType.I2C
        serDict[SerialBusDevice.MODULE_PARAM_PREFIX + ".address"] = cls.ADDRESSES_ALLOWED[0]
        # Add defaults for other modules
        SerialBus.Params_init(serDict)
        SerialBusDevice.Params_init(serDict)
        
        cls._aggregateParams( paramDict, serDict, prefix )
        #Add this module's defaults
        defaults = {
            "alarm2.enable":    True,
            "ft.enable":        False,
            }
        cls._aggregateParams( paramDict, defaults, prefix )
        RTC.Params_init(paramDict)
        Watchdog.Params_init(paramDict)
        

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
        ret = super().open( paramDict )
        if ret.isOk() and self._serbusdev:
            self.isOpen = True
            ret = ErrorCode.errResourceConflict
        if ret.isOk():
            prefixMod = self.MODULE_PARAM_PREFIX + "."
            # Extract serial bus parameters
            sparams = self._extractParams( paramDict, prefixMod )
            self._serbusdev = SerialBusDevice()
            if not self._serbusdev:
                self.isOpen = False
                ret = ErrorCode.errInitFailed
        if ret.isOk():
            ret = self._serbusdev.open(sparams)
        if ret.isOk():
            self.isOpen = True
            # Read date+time of last access
            self.lastKnownAlive, ret = self.getDateTime()
            # Clear halt bit HT, now.
            val, ret = self._serbusdev.readByteRegister( 0x0C )
            val &= ~0x40    # clear HT
            ret = self._serbusdev.writeByteRegister(0x0C, val)
        if ret.isOk():
            # Kick-start oscillator by cycling ST
            # But first avoid a roll-over in the milliseconds
            val = 0xFF
            while ((val & 0xFF) > 0x40) and ret.isOk():
                val, ret = self._serbusdev.readWordRegister( 0x00 )
            val = val >> 8
            ret = self._serbusdev.writeByteRegister(0x01, val | 0x80 )
            ret = self._serbusdev.writeByteRegister(0x01, val & 0x7F )
        if ret.isOk():
            # Set or clear FT
            self._bitFT = sparams.get("ft.enable", False)
            val, ret = self._serbusdev.readByteRegister( 0x08 )
            val = (val | 0x40) if self._bitFT else (val & ~0x40)
            ret = self._serbusdev.writeByteRegister( 0x08, val )
        if ret.isOk():
            # Set or clear AL2E
            flag = sparams.get("alarm2.enable", True)
            self.numAlarms = 2 if flag else 1
            self.supportedStatus = (self.supportedStatus | RTC.STATUS_ALARM_1) if flag else \
                                    (self.supportedStatus & ~RTC.STATUS_ALARM_1)
            self.lenUserData = 7 if flag else 12
            ret = self._serbusdev.writeByteRegister(0x13, 2 if flag else 0)
        if ret.isOk():
            # Set watchdog data
            self._wdData, ret = self._getWatchdogData( paramDict )
        logger.debug("ret=%s.", ret)
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
        if self._serbusdev:
            ret = self._serbusdev.close()
            self._serbusdev = None
            self.isOpen = False
        else:
            self.isOpen = False
            ret = ErrorCode.errResourceConflict
        logger.debug("ret=%s.", ret)
        return ret


    #
    # RTC specific API
    #

    def getDateTime(self):
        """Retrieve the current date and time information.

        Gives the most recent date and time information. Note that the
        returned data is only valid, if the error code indicates
        that function execution was ok.
        
        :return: A date/time tuple and an error code\
        indicating either success or the reason of failure.
        :rtype: DateTime, ErrorCode
        """
        val = None
        ret = ErrorCode.errOk
        if not self._serbusdev:
            ret = ErrorCode.errResourceConflict
        else:
            data, ret = self._serbusdev.readBufferRegister(0, 8)
            logger.debug("data=%s, ret=%s", data, ret)
        if ret.isOk():
            if data is None or not isinstance(data, (tuple,list)) or \
                len(data < 8):
                ret = ErrorCode.errFewData
        if ret.isOk():
            # Grab information
            year = 2000 + 100*(data[3]>>6) + 10*(data[7]>>4) + (data[7] & 0x0F)
            month = 10*(data[6]>>4) + (data[6] & 0x0F)
            day = 10*(data[5]>>4) + (data[5] & 0x0F)
            # Ignore day of week in data[4]
            hour = 10*((data[3] & 0x30)>>4) + (data[3] & 0x0F)
            minute = 10*(data[2]>>4) + (data[2] & 0x0F)
            second = 10*((data[1] & 0x70)>>4) + (data[1] & 0x0F)
            micro = 100000*(data[0]>>4) + 10000(data[0] & 0x0F)
            tzinfo = 0  # time zone info
            val = (year, month, day, hour, minute, second, micro, tzinfo)
        logger.debug("val=%s, ret=%s.", val, ret)
        return val, ret

    def setDateTime(self, dateTime):
        """Set the RTC to the given date and time.

        Adjust the RTC according to the given date/time tuple.
        This must neither be None nor empty!
        Note that there might be a small, hardware-dependent deficiency
        between calling this function and when the RTC is actually set. 
        
        :param Tuple dateTime: The date and time to set the RTC to. 
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        # Check parameter
        ret = super().setDateTime(dateTime)
        if ret.isOk() or ret == ErrorCode.errNotImplemented:
            ret = ErrorCode.errOk
            hundredths = (dateTime[6] + 5000) // 10000
            hundredths = ((hundredths // 10) << 4) | (hundredths % 10)
            # Clear stop bit ST 
            second = ((dateTime[5] // 10) << 4) | (dateTime[5] % 10)
            minute = ((dateTime[4] // 10) << 4) | (dateTime[4] % 10)
            hour = ((dateTime[3] // 10) << 4) | (dateTime[3] % 10)
            # Also set century bits CB1-0
            hour |= (((dateTime[0]-2000) // 100) & 0x03) << 6 
            weekday = 0 # Just insert dummy as we don't know day of week
            day = ((dateTime[2] // 10) << 4) | (dateTime[2] % 10)
            month = ((dateTime[1] // 10) << 4) | (dateTime[1] % 10)
            year =  ((dateTime[0] // 10) << 4) | (dateTime[0] % 10)
                     
            data = [ hundredths, second, minute, hour,
                     weekday, day, month, year ]
            ret = self._serbusdev.writeBufferRegister(0, data)
            logger.debug("data=%s, ret=%s.", data, ret)
        logger.debug("dateTime=%s, ret=%s.", dateTime, ret)
        return ret

    def getStatus(self):
        """Reads the status from the RTC.
        
        Beware of the fact that in this chip, the watch dog flag is 
        part of the status register! So either getting the status or
        checking the watch dog flag will leave all flags cleared.
        Consider this, when using this class as RTC and Watchdog,
        simultaneously! 
        
        :return: An integer bit pattern representing the RTC status\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        val = 0
        if not self.isOpen:
            ret = ErrorCode.errResourceConflict
        else:
            flags, ret = self._serbusdev.readByteRegister(0x0F)
            logger.debug("flags=0x%02x, ret=%s", flags, ret)
        if ret.isOk():
            val |= RTC.STATUS_ALARM_0 if flags & 0x40 else 0
            if self.numAlarms > 1:
                val |= RTC.STATUS_ALARM_1 if flags & 0x20 else 0
            val |= RTC.STATUS_TIMER_0 if flags & 0x08 else 0
            val |= RTC.STATUS_OSC_FAIL if flags & 0x04 else 0
            val |= RTC.STATUS_BAT_LOW if flags & 0x10 else 0
            seconds, ret = self._serbusdev.readByteRegister(0x01)
            logger.debug("seconds=0x%02x, ret=%s", seconds, ret)
        if ret.isOk():
            val |= RTC.STATUS_STOPPED if seconds & 0x80 else 0
        logger.debug("val=0x%04x, ret=%s.", val, ret)
        return val, ret
    
    def setAlarm(self, alarmID, dateTime, reptPeriod=0, reptUnit=RTC.REPT_NONE ):
        """Set an RTC alarm time.
    
        From the given date/time tuple, only the ``month``, ``day``,
        ``hour``, ``minute`` and ``second`` elements are considered.
        So, the ``year``, ``microsecond`` and other elements are ignored.
         
        :param int alarmID: Zero-based numeric ID of the alarm to set.
        :param Tuple dateTime: The absolute date and time of the alarm.
        :param int reptPeriod: Period for alarm repetition.
        :param int reptUnit: Time unit for alarm repetition.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        # Check parameter
        ret = super().setAlarm( alarmID, dateTime, reptPeriod, reptUnit )
        if ret.isOk() or ret == ErrorCode.errNotImplemented:
            ret = ErrorCode.errOk
            if not reptPeriod:
                reptUnit = RTC.REPT_NONE
            elif not reptUnit in [RTC.REPT_NONE, RTC.REPT_SECOND, RTC.REPT_MINUTE,
                                  RTC.REPT_HOUR, RTC.REPT_DAY, RTC.REPT_MONTH,
                                  RTC.REPT_YEAR]:
                ret = ErrorCode.errNotSupported
            elif (reptPeriod!=1) and (reptUnit!=RTC.REPT_NONE):
                ret = ErrorCode.errNotSupported
        if ret.isOk():
            month = ((dateTime[1] // 10) << 4) | (dateTime[1] % 10)
            day = ((dateTime[2] // 10) << 4) | (dateTime[2] % 10)
            hour = ((dateTime[3] // 10) << 4) | (dateTime[3] % 10)
            minute = ((dateTime[4] // 10) << 4) | (dateTime[4] % 10)
            second = ((dateTime[5] // 10) << 4) | (dateTime[5] % 10)

            if (reptUnit!=RTC.REPT_NONE) and (reptUnit!=RTC.REPT_YEAR):
                day |= 0x40                         # RPTx5
                if reptUnit != RTC.REPT_MONTH:
                    day |= 0x80                     # RPTx4
                    if reptUnit != RTC.REPT_DAY:
                        hour |= 0x80                # RPTx3
                        if reptUnit != RTC.REPT_HOUR:
                            minute |= 0x80          # RPTx2
                            if reptUnit != RTC.REPT_MINUTE:
                                second |= 0x80      # RPTx1

            data = [ month, day, hour, minute, second ]
            if alarmID == 0:
                data[0] |= 0x20     # set ABE
                reg = 0x0A
            else:
                al1Mon, ret = self._serbusdev.readByteRegister( 0x0A )
                al1Mon |= 0x20      # set ABE
                ret = self._serbusdev.writeByteRegister( 0x0A, al1Mon )
                reg = 0x14
            ret = self._serbusdev.writeBufferRegister(reg, data)
            
        logger.debug("alarmID=%s, dateTime=%s, reptPeriod=%s, reptUnit=%s, ret=%s.",
                     alarmID, dateTime, reptPeriod, reptUnit, ret)
        return ret

    def cancelAlarm(self, alarmID):
        """Clears an RTC alarm.
    
        An alarm possibly set is cleared and will not fire.
        
        :param int alarmID: Zero-based numeric ID of the alarm to clear.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        # Check parameter
        ret = super().cancelAlarm( alarmID )
        if ret.isOk() or ret == ErrorCode.errNotImplemented:
            ret = ErrorCode.errOk
            data = [0] * 5
            if alarmID == 0:
                data[0] |= 0x20     # keep ABE set
                reg = 0x0A
            else:
                reg = 0x14
            ret = self._serbusdev.writeBufferRegister(reg, data)
        logger.debug("alarmID=%s, ret=%s.", alarmID, ret)
        return ret
    

    def setTimer(self, timerID, period, unit=RTC.REPT_MILLISECOND, repeat=False):
        """Set an RTC timer interval.

        Actually, the following periods can be executed exactly:
        
        ============================    ================================
        Periods                         Resolution (Timer Frequency)
        ============================    ================================
        1, 2, 3, ... , 61, 62 [ms]      ~1 ms  (4096 Hz)
        63, 78, 94, ... 3984 [ms]       15.625 ms  (64 Hz)
        4, 5, 6, ... , 255 [s]          1 s  (1 Hz)
        300, 360, ..., 15300 [s]        60 s  (1/60 Hz)
        ============================    ================================

        Period values falling in between any two of the given exact values
        will be mapped to the nearest matching one. So, e.g. 67 will be
        mapped to 63 and 4382 to 4000.
        
        This implementation supports only a repeating timer. If the
        argument ```repeat``` is False, this function will return an
        appropriate error code.

        :param int timerID: Zero-based numeric ID of the alarm to set.
        :param int msPeriod: The period of time in milliseconds until the alarm is raised.
        :param int unit: The unit of time until the alarm is raised.
        :param bool repeat: True, if the alarm is to be repeated, False otherwise.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        # Check parameter
        ret = super().setTimer( timerID, period, repeat )
        if ret.isOk() or ret == ErrorCode.errNotImplemented:
            ret = ErrorCode.errOk
        if ret.isOk():
            if not unit in [RTC.REPT_MILLISECOND, RTC.REPT_SECOND,
                            RTC.REPT_MINUTE, RTC.REPT_HOUR] or \
                not repeat:
                ret = ErrorCode.errInvalidParameter
        if ret.isOk():
            # Account for the given unit
            if unit == RTC.REPT_SECOND:
                period *= 1000
            elif unit == RTC.REPT_MINUTE:
                period *= 60000
            elif unit == RTC.REPT_HOUR:
                period *=3600000
            # (upper limit[ms], f.numerator[Hz], f.denominator, TD1-0)
            settings = ( (62, 4096, 1000, 0), (3992, 64, 1000, 1),
                         (277500, 1, 1000, 2), (15330000, 1, 60000, 3) )
            if period > settings[-1][0]:
                ret = ErrorCode.errSpecRange
            else:
                for data in settings:
                    if period <= data[0]: # Upper limit
                        tval = (period * data[1] + data[2]//2) // data[2] 
                        if tval > 0xFF:
                            tval = 0xFF
                        tcfg = data[3]    # TD1-0
                        break
                tcfg |= 0x80    # Enable timer: TE=1
                ret = self._serbusdev.writeWordRegister( 0x10, ((tcfg<<8) | tval))
        logger.debug("timerID=%s, period=%s, unit=%s, repeat=%s, ret=%s.",
                     timerID, period, unit, repeat, ret)
        return ret

    def cancelTimer(self, timerID):
        """Clears an RTC timer.
    
        An alarm or timer possibly set is cleared and will not fire.
        
        :param int alarmID: Zero-based numeric ID of the alarm to clear.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        # Check parameter
        ret = super().cancelAlarmTimer( timerID )
        if ret.isOk() or ret == ErrorCode.errNotImplemented:
            ret = ErrorCode.errOk
        if ret.isOk():
            # Reg. 10h: Clear timer value (FF)
            # Reg. 11h: Disable timer, timer freq = 1/60 Hz (lowest)
            ret = self._serbusdev.writeWordRegister( 0x10, 0x03FF )
        logger.debug("timerID=%s, ret=%s.", timerID, ret)
        return ret
    
    def readUserData(self, length):
        """Reads the first given number of bytes from the user data space.

        :param int length: The number of bytes to read from the user\
        data space. Should be greater than zero.
        :return: A buffer of the indicated length holding the response\
        and an error code indicating success or the reason of failure.
        :rtype: int[], ErrorCode
        """
        data = []
        # Check parameter
        ret = super().readUserData( length )
        if ret.isOk() or (ret == ErrorCode.errNotImplemented):
            reg = 0x19 if self.numAlarms > 1 else 0x14
            data, ret = self._serbusdev.readBufferRegister( reg, length)
        logger.debug("length=%s, data=%s, ret=%s.", length, data, ret)
        return data, ret

    def writeUserData(self, buffer):
        """Write the given buffer to the user data space.

        :param int[] buffer: The data to store.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        # Check parameter
        ret = super().writeUserData( buffer )
        if ret.isOk() or (ret == ErrorCode.errNotImplemented):
            ret = ErrorCode.errOk
            if len(buffer) > self.lenUserData:
                buffer = buffer[:self.lenUserData]
            reg = 0x19 if self.numAlarms > 1 else 0x14
            self._serbusdev.writeBufferRegister( reg, buffer )
        logger.debug("buffer=%s, ret=%s.", buffer, ret)
        return ret

    def getCalibration(self, tech=CALIB_TECH_BOTH):
        """Retrieve the current calibration value in ppm.
        
        :param int tech: Optional selector for analogue or digital calibration value.
        :return: The signed total calibration value in ppm and\
        An error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        ret = ErrorCode.errOk
        val = 0
        if not self.isOpen:
            ret = ErrorCode.errResourceConflict
        elif not tech in (M41T82.CALIB_TECH_ANALOGUE, M41T82.CALIB_TECH_DIGITAL, M41T82.CALIB_TECH_BOTH):
            ret = ErrorCode.errInvalidParameter
        else:
            if tech in (M41T82.CALIB_TECH_ANALOGUE, M41T82.CALIB_TECH_BOTH):
                analog, ret = self._serbusdev.readByteRegister( 0x12 )
                ppm, ret = self._calibAnalogReg2ppm(analog)
                logger.debug("analog=0x%02x, ppm=%s, ret=%s.", analog, ppm, ret)
                val = ppm
            if tech in (M41T82.CALIB_TECH_DIGITAL, M41T82.CALIB_TECH_BOTH):
                digital, ret = self._serbusdev.readByteRegister( 0x08 )
                digital &= 0x3F
                ppm, ret = self._calibDigitalReg2ppm(digital)
                logger.debug("digital=0x%02x, ppm=%s, ret=%s.", digital, ppm, ret)
                if ret.isOk():
                    val += ppm
        logger.debug("val=%s, ret=%s.", val, ret)
        return val, ret
    
    def setCalibration(self, ppmValue, tech=CALIB_TECH_BOTH):
        """Set and apply a calibration to the RTC.
        
        The calibration value is a corrective factor applied to the clock
        frequency. This value is signed, so it can also be a  negative
        number. It is expressed as ppm, which is parts-per-million or
        1:1'000'000.

        The given value is an absolute bias to the RTC. So, calling this
        function sequentially will not accumulated the given values.
        Instead, a call of this function replaces the RTC calibration
        value of the previous call. So the corrective :attr:```ppmValue```
        is meant relative to the device default clock rate.
        
        If both, analogue and digital calibration techniques are selected,
        analogue calibration is used to its full extend before digital
        calibration gets involved.
         
        :param int tech: Optional selector for analogue or digital calibration technique.
        :param int ppmValue: The calibration value to apply.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if not self.isOpen:
            ret = ErrorCode.errResourceConflict
        elif not tech in (M41T82.CALIB_TECH_ANALOGUE, M41T82.CALIB_TECH_DIGITAL, M41T82.CALIB_TECH_BOTH):
            ret = ErrorCode.errInvalidParameter
        else:
            if tech in (M41T82.CALIB_TECH_ANALOGUE, M41T82.CALIB_TECH_BOTH):
                ppm = ppmValue
                if tech == M41T82.CALIB_TECH_BOTH:
                    if ppm < M41T82.CALIB_ANALOGUE_LIMIT_LOWER:
                        ppm = M41T82.CALIB_ANALOGUE_LIMIT_LOWER 
                    elif ppm > M41T82.CALIB_ANALOGUE_LIMIT_UPPER:
                        ppm = M41T82.CALIB_ANALOGUE_LIMIT_UPPER
                analog, ret = self._calibPPM2AnalogReg(ppm)
                ret = self._serbusdev.writeByteRegister( 0x12, analog )
                ppmValue -= ppm
                logger.debug("ppm=%s, analog=0x%02x, ret=%s.", ppm, analog, ret)
            if tech in (M41T82.CALIB_TECH_DIGITAL, M41T82.CALIB_TECH_BOTH):
                ppm = ppmValue
                digital, ret = self._calibPPM2DigitalReg(ppm)
                digital |= 0x40 if self._bitFT else 0
                ret = self._serbusdev.writeByteRegister( 0x08, digital )
                logger.debug("ppm=%s, digital=0x%02x, ret=%s.", ppm, digital, ret)
        logger.debug("ppmValue=%s, ret=%s.", ppmValue, ret)
        return ret
    
    
    #
    # Watchdog API
    #

    def enableWatchdog(self):
        """Enable and restart the watch dog.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = self._serbusdev.writeByteRegister( 0x09, self._wdData )
        return ret
    
    def disableWatchdog(self):
        """Disable the watch dog and stop it from running, immediately.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = self._serbusdev.writeByteRegister( 0x09, 0x03 )
        return ret
    
    def isWatchdogRunning(self):
        """Check, whether the watchdog is currently running or not.
        
        Returns :attr:`.ErrorCode.errOk`, if the watch dog is running,
        :attr:`.ErrorCode.errUnavailable`, if it is not running and
        any other value to indicate the reason, why this information
        could not be retrieved.
        
        :return: An error code indicating the result.
        :rtype: ErrorCode
        """
        data, ret = self._serbusdev.readByteRegister( 0x09 )
        if ret.isOk():
            if (data & 0x83) == 0:
                ret = ErrorCode.errUnavailable
        return ret

    def clearWatchdog(self):
        """Clear the watch dog.
        
        This is the implementation of the acknowledge mechanism.
        Calling this function is necessary for an application to prevent
        the watch dog from elapsing.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = self._serbusdev.writeByteRegister( 0x09, self._wdData )
        return ret

    def isWatchdogElapsed(self):
        """Check, whether the configured time interval has expired, or not.
        
        By calling this function, an application may observe the
        expiration without using the interrupt mechanism.
        Note, that this flag is not cleared automatically. The caller
        would have to use :meth:`clearWatchdogElapsed` for this purpose.

        Beware of the fact that in this chip, the watch dog flag is 
        part of the status register! So either getting the status or
        checking the watch dog flag will leave all flags cleared.
        Consider this, when using this class as RTC and Watchdog,
        simultaneously! 

        Returns :attr:`.ErrorCode.errOk`, if the watch dog has elapsed,
        :attr:`.ErrorCode.errUnavailable`, if it is not elapsed, yet, and
        any other value to indicate the reason, why this information
        could not be retrieved.
        
        :return: An error code indicating the result.
        :rtype: ErrorCode
        """
        if not self.isOpen:
            ret = ErrorCode.errResourceConflict
        else:
            flags, ret = self._serbusdev.readByteRegister(0x0F)
            logger.debug("flags=0x%02x, ret=%s", flags, ret)
        if ret.isOk():
            if not (flags & 0x80):
                ret = ErrorCode.errUnavailable
        logger.debug("ret=%s.", ret)
        return ret

    def clearWatchdogElapsed(self):
        """Clear the elapsed flag.
        
        The application should call this function after it observed that
        the watch dog interval time expired.
        
        Also see: :meth:`isWatchdogElapsed`.

        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errOk
    
