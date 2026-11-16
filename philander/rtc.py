"""Abstraction module for real-time clocks.

Provide a convergence layer API to abstract from several different
RTC implementing driver modules possibly installed on the target
system.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["RTC"]

import logging

from .module import Module
from .sysfactory import SysProvider, SysFactory
from .systypes import ErrorCode

logger = logging.getLogger(__name__)

    
class RTC( Module ):
    """Real-time clock abstraction class.
    
    Provide access to and control over the underlying RTC hardware. For
    that, an implementing driver module is used. As a convergence layer,
    this class is to hide specifics and to level syntactic requirements
    of the implementing package.
    
    Date and time information is mainly handled as a tuple of integers.
    That tuple has the following order, i.e. elements have the following
    meaning:
    
    =====  =============  ====================================================
    Index  Name           Range, Meaning
    =====  =============  ====================================================
      0    year           should be positive, read as AC
      1    month          [1, 12], 1=January
      2    day            [1, 31]
      3    hour           [0, 23]
      4    minute         [0, 59]
      5    second         [0, 61] for compatibility with time.strftime()
      6    microsecond    [0, 999.999]
      7    tzinfo         timezone info, currently optional and ignored.
    =====  =============  ====================================================
    
    """
    
    MODULE_PARAM_PREFIX = "rtc" # Prefix for module parameters
    DATETIME_TUPLE_LEN  = 8 # (Minimum) length of a date/time tuple
    
    # Status masks
    STATUS_ALARM_0  = 0x0001    
    STATUS_ALARM_1  = 0x0002    
    STATUS_ALARM_2  = 0x0004    
    STATUS_ALARM_3  = 0x0008    
    STATUS_TIMER_0  = 0x0010
    STATUS_TIMER_1  = 0x0020
    STATUS_TIMER_2  = 0x0040
    STATUS_TIMER_3  = 0x0080
    STATUS_OSC_FAIL = 0x0100
    STATUS_BAT_LOW  = 0x0200
    STATUS_STOPPED  = 0x0400
    STATUS_ALARM_ANY = (STATUS_ALARM_0 | STATUS_ALARM_1 | STATUS_ALARM_2 | STATUS_ALARM_3)
    STATUS_TIMER_ANY = (STATUS_TIMER_0 | STATUS_TIMER_1 | STATUS_TIMER_2 | STATUS_TIMER_3)
    
    # Repetition time units
    REPT_NONE        = 0
    REPT_MILLISECOND = 1    
    REPT_SECOND      = 2    
    REPT_MINUTE      = 3    
    REPT_HOUR        = 4    
    REPT_DAY         = 5    
    REPT_WEEK        = 6    
    REPT_MONTH       = 7    
    REPT_YEAR        = 8    
    
    @staticmethod
    def getRTC( provider=SysProvider.AUTO ):
        """Generates an RTC implementation according to the requested provider.
        
        :param SysProvider provider: The low-level lib to rely on, or AUTO\
        for automatic detection.
        :return: An implementation object, or None in case of an error.
        :rtype: RTC
        """
        deps = [(SysProvider.MICROPYTHON, "machine", "RTC"),
                 (SysProvider.COMPOSITE,   "philander.m41t82", "M41T82"),
                ]
        impls = {
                  SysProvider.MICROPYTHON:  ("philander.rtc_micropython", "_RTC_Micropython"),
                  SysProvider.COMPOSITE:    ("philander.m41t82", "M41T82"),
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
        self.numAlarms      = 0     # Number of alarms (ids) provided
        self.numTimers      = 0     # Number of timers (ids) provided
        self.lenUserData    = 0     # Number of bytes than can be stored as user data
        self.supportedStatus =0     # Mask of STAUS_ bits supported
        self.isOpen = False
        self.provider = SysProvider.NONE


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
        
        :param dict(str, object) paramDict: Configuration parameters as obtained from :meth:`Params_init`, possibly.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if self.isOpen:
            ret = ErrorCode.errResourceConflict
        if ret.isOk():
            # Retrieve defaults
            self.Params_init( paramDict )
            self.isOpen = True
        
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
        if self.isOpen:
            self.isOpen = False
        else:
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
        if not self.isOpen:
            ret = ErrorCode.errResourceConflict
        else:
            ret = ErrorCode.errNotImplemented
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
        if not self.isOpen:
            ret = ErrorCode.errResourceConflict
        elif not dateTime or not isinstance(dateTime, tuple) or \
            len(dateTime < RTC.DATETIME_TUPLE_LEN):
            ret = ErrorCode.errInvalidParameter
        else:
            ret = ErrorCode.errNotImplemented
        logger.debug("dateTime=%s, ret=%s.", dateTime, ret)
        return ret

    def getStatus(self):
        """Reads the status from the RTC.

        The returned information is an integer representing a bit pattern.
        That pattern can be matched against the RTC.STATUS_ masks to
        reveal the information of interest.
        
        Use the :attr:`self.supportedStatus` mask to know, which bits
        of information are supported by the underlying implementation or
        hardware. 
        
        Reading the status may clear the corresponding status bits in the
        underlying hardware. So, retrieving this information consecutively,
        will certainly yield different results.
        
        :return: An integer bit pattern representing the RTC status\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        val = 0
        if not self.isOpen:
            ret = ErrorCode.errResourceConflict
        else:
            ret = ErrorCode.errNotImplemented
        logger.debug("val=%s, ret=%s.", val, ret)
        return val, ret
    
    def setAlarm(self, alarmID, dateTime, reptPeriod=0, reptUnit=REPT_NONE ):
        """Set an RTC alarm time.
    
        The attribute :attr:`self.numAlarms' tells, how many alarms are
        supported, if at all. Note that alarm IDs are zero-based. So,
        valid IDs range from zero (0) to :attr:`self.numAlarms`-1.
        
        The underlying implementation or hardware fires an alarm at the
        given absolute date/time.
        
        If supported by the implementation, an alarm can be
        repeated, automatically. Repetition period and time unit are given
        by the corresponding parameters. `reptPeriod` must be a non-negative
        integer, while `reptUnit` must be one of the :attr:`RTC.REPT_SECOND`
        or similar unit identifiers. Both, a period of zero and the unit
        `RTC.REPT_NONE` indicate, that the alarm will not be repeated
        but only fired once.
         
        If alarms are supported, the implementation is expected
        to behave as an ```pymitter.EventEmitter```.
        Refer to https://pypi.org/project/pymitter/
        for information on registering alarm handling routines.
        
        :param int alarmID: Zero-based numeric ID of the alarm to set.
        :param Tuple dateTime: The absolute date and time of the alarm.
        :param int reptPeriod: Period for alarm repetition.
        :param int reptUnit: Time unit for alarm repetition.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        del reptUnit
        ret = ErrorCode.errOk
        if self.numAlarms < 1:
            ret = ErrorCode.errNotSupported
        elif not self.isOpen:
            ret = ErrorCode.errResourceConflict
        elif (alarmID >= self.numAlarms) or not dateTime or \
            not isinstance(dateTime, tuple) or \
            len(dateTime < RTC.DATETIME_TUPLE_LEN) or \
            not isinstance(reptPeriod, int) or (reptPeriod<0):
            ret = ErrorCode.errInvalidParameter
        else:
            ret = ErrorCode.errNotImplemented
        logger.debug("alarmID=%s, dateTime=%s, reptPeriod=%s, reptUnit=%s, ret=%s.",
                     alarmID, dateTime, reptPeriod, reptUnit, ret)
        return ret

    def cancelAlarm(self, alarmID):
        """Clears an RTC alarm.
    
        An alarm possibly set is cleared and will not fire anymore.
        
        :param int alarmID: Zero-based numeric ID of the alarm to clear.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if self.numAlarms < 1:
            ret = ErrorCode.errNotSupported
        elif not self.isOpen:
            ret = ErrorCode.errResourceConflict
        elif not isinstance(alarmID, int) or (alarmID<0) or (alarmID >= self.numAlarms):
            ret = ErrorCode.errInvalidParameter
        else:
            ret = ErrorCode.errNotImplemented
        logger.debug("alarmID=%s, ret=%s.", alarmID, ret)
        return ret
    

    def setTimer(self, timerID, period, unit=REPT_MILLISECOND, repeat=False):
        """Set an RTC timer interval.
    
        The attribute :attr:`self.numTimers' tells, how many alarms are
        supported, if at all. Note that timer IDs are zero-based. So,
        valid IDs range from zero (0) to :attr:`self.numTimers`-1.
        
        The underlying implementation or hardware fires an alarm at the
        given period and unit from *now* on. If ```repeat``` is set
        to ```True```, the alarm is repeated automatically at the given
        interval rate.
        
        `period`should not be zero and `unit` should not be RTC.REPT_NONE.
        It's at the discretion of the implementation, which combinations
        of ```period```and ```unit``` are actually supported. Especially
        for long intervals (e.g. 3 hours plus 7 milliseconds, given as a
        period of 1'800'007 ms) non-matching periods may be silently mapped
        to the next matching one, without indicating an error. 
        
        If the underlying implementation supports timers, it is expected
        to implement ```pymitter.EventEmitter```.
        Refer to https://pypi.org/project/pymitter/
        for information on registering alarm handling routines.
                 
        :param int timerID: Zero-based numeric ID of the timer to set.
        :param int period: The period of time until the alarm is raised.
        :param int unit: The unit of time until the alarm is raised.
        :param bool repeat: True, if the alarm is to be repeated, False otherwise.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        del unit
        ret = ErrorCode.errOk
        if self.numTimers < 1:
            ret = ErrorCode.errNotSupported
        elif not self.isOpen:
            ret = ErrorCode.errResourceConflict
        elif (timerID >= self.NUM_ALARMS) or \
            not isinstance(period, int) or (period <= 0) or \
            (unit == RTC.REPT_NONE) or \
            not isinstance(repeat, (bool, int)):
            ret = ErrorCode.errInvalidParameter
        else:
            ret = ErrorCode.errNotImplemented
        logger.debug("timerID=%s, period=%s, unit=%s, repeat=%s, ret=%s.",
                     timerID, period, unit, repeat, ret)
        return ret

    def cancelTimer(self, timerID):
        """Clears an RTC timer.
    
        A timer possibly set is cleared and will not fire anymore.
        
        :param int timerID: Zero-based numeric ID of the timer to clear.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if self.numTimers < 1:
            ret = ErrorCode.errNotSupported
        elif not self.isOpen:
            ret = ErrorCode.errResourceConflict
        elif not isinstance(timerID, int) or (timerID<0) or (timerID >= self.numTimers):
            ret = ErrorCode.errInvalidParameter
        else:
            ret = ErrorCode.errNotImplemented
        logger.debug("timerID=%s, ret=%s.", timerID, ret)
        return ret
    
    def readUserData(self, length):
        """Reads the first given number of bytes from the user data space.

        Some RTC implementations provide a few bytes of user data, that
        may be stored along the date and time. It is supposed to survive
        a voltage outage and can be recovered using this function.
        The exact size of this user data space is given by
        :attr:`self.lenUserData`.
        
        Note that the size and location of the user data space may depend
        on the configuration. So, the result of reading the same device
        under different configurations may be different! The application
        must ensure consistent configuration between writing and reading
        user data.
         
        The resulting buffer is only valid, if the error code
        indicates a non-failing execution.
        
        :param int length: The number of bytes to read from the user\
        data space. Should be greater than zero.
        :return: A buffer of the indicated length holding the response\
        and an error code indicating success or the reason of failure.
        :rtype: int[], ErrorCode
        """
        data = []
        if self.lenUserData < 1:
            ret = ErrorCode.errNotSupported
        elif not self.isOpen:
            ret = ErrorCode.errResourceConflict
        elif not isinstance(length, int) or \
            (length<1) or (length>self.lenUserData):
            ret = ErrorCode.errInvalidParameter
        else:
            ret = ErrorCode.errNotImplemented
        logger.debug("length=%s, data=%s, ret=%s.", length, data, ret)
        return data, ret

    def writeUserData(self, buffer):
        """Write the given buffer to the user data space.

        The given buffer must not be None. If the length of the given
        buffer exceeds  :attr:`self.lenUserData`, only the first
        :attr:`self.lenUserData` bytes are written to memory and the
        function returns ErrorCode.errOverflow.
        If the buffer length is shorter, only those bytes are written,
        but no padding is done. So, the remaining memory is left
        untouched.
        
        :param int[] buffer: The data to store.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if self.lenUserData < 1:
            ret = ErrorCode.errNotSupported
        elif not self.isOpen:
            ret = ErrorCode.errResourceConflict
        elif buffer is None:
            ret = ErrorCode.errInvalidParameter
        elif len(buffer) > 0:
            ret = ErrorCode.errNotImplemented
        logger.debug("buffer=%s, ret=%s.", buffer, ret)
        return ret

