"""RTC implementation for the Micropython environment.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_RTC_Micropython"]

import logging
from machine import RTC as mpRTC

from .rtc import RTC
from .sysfactory import SysProvider
from .systypes import ErrorCode

logger = logging.getLogger(__name__)

    
class _RTC_Micropython( RTC ):
    """Implementation of the RTC API under Micropython.
    """
    
    def __init__(self):
        """Initialize the instance with defaults.
        """
        super().__init__()
        self.numAlarms      = 4     # Number of alarms (ids) provided
        self.numTimers      = 4     # Number of timers (ids) provided
        self.lenUserData    = 2048  # Number of bytes than can be stored as user data
        self.provider = SysProvider.MICROPYTHON
        self._implrtc = None


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
        ret = super().open( paramDict )
        if ret.isOk():
            if self._implrtc:
                self.isOpen = True
                ret = ErrorCode.errResourceConflict
            else:
                self._implrtc = mpRTC()
                self.isOpen = (self._implrtc is not None)
                ret = ErrorCode.errOk if self.isOpen else ErrorCode.errInitFailed
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
        if self._implrtc:
            self._implrtc = None
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
        ret = ErrorCode.errOk
        if self._implrtc:
            mpdata = self._implrtc.datetime()
            logger.debug("mpdata=%s.", mpdata)
            if mpdata is None or not isinstance(mpdata, tuple) or \
                len(mpdata < 8):
                ret = ErrorCode.errFewData
            else:
                # Ignore weekday and append tzinfo
                val = mpdata[0:3] + mpdata[4:8] + (0,)
        else:
            ret = ErrorCode.errResourceConflict
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
            # Insert dummy weekday (0) and strip tzinfo
            mpdata = dateTime[0:3] + (0,) + dateTime[3:7]
            logger.debug("mpdata=%s.", mpdata)
            self._implrtc.datetime( mpdata )
        logger.debug("dateTime=%s, ret=%s.", dateTime, ret)
        return ret

    def getStatus(self):
        """Reads the status from the RTC.

        :return: An integer bit pattern representing the RTC status\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        val = 0
        if not self.isOpen:
            ret = ErrorCode.errResourceConflict
        else:
            ret = ErrorCode.errOk
        logger.debug("val=%s, ret=%s.", val, ret)
        return val, ret
    
    def setAlarm(self, alarmID, dateTime, reptPeriod=0, reptUnit=RTC.REPT_NONE ):
        """Set an RTC alarm time.
    
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
            if (reptPeriod!=0) and (reptUnit!=RTC.REPT_NONE):
                ret = ErrorCode.errNotSupported 
        if ret.isOk():
            self._implrtc.alarm( alarmID, dateTime )
        logger.debug("alarmID=%s, dateTime=%s, reptPeriod=%s, reptUnit=%s, ret=%s.",
                     alarmID, dateTime, reptPeriod, reptUnit, ret)
        return ret

    def cancelAlarm(self, alarmID):
        """Clears an RTC alarm .
    
        An alarm possibly set is cleared and will not fire.
        
        :param int alarmID: Zero-based numeric ID of the alarm to clear.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        # Check parameter
        ret = super().cancelAlarm( alarmID )
        if ret.isOk() or ret == ErrorCode.errNotImplemented:
            ret = ErrorCode.errOk
            self._implrtc.alarm_cancel( alarmID )
        logger.debug("alarmID=%s, ret=%s.", alarmID, ret)
        return ret
    
    def setTimer(self, timerID, period, unit=RTC.REPT_MILLISECOND, repeat=False):
        """Set an RTC alarm time.
    
        :param int timerID: Zero-based numeric ID of the timer to set.
        :param int period: The period of time until the alarm is raised.
        :param int unit: The unit of time until the alarm is raised.
        :param bool repeat: True, if the alarm is to be repeated, False otherwise.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        # Check parameter
        ret = super().setTimer( timerID, period, unit, repeat )
        if ret.isOk() or ret == ErrorCode.errNotImplemented:
            ret = ErrorCode.errOk
            if unit != RTC.REPT_MILLISECONDS:
                ret = ErrorCode.errNotSupported
        if ret.isOk():
            self._implrtc.alarm( timerID, period, repeat )
        logger.debug("timerID=%s, period=%s, unit=%s, repeat=%s, ret=%s.",
                     timerID, period, unit, repeat, ret)
        return ret

    def cancelTimer(self, timerID):
        """Clears an RTC timer.
    
        An timer possibly set is cleared and will not fire.
        
        :param int timerID: Zero-based numeric ID of the timer to clear.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        # Check parameter
        ret = super().cancelTimer( timerID )
        if ret.isOk() or ret == ErrorCode.errNotImplemented:
            ret = ErrorCode.errOk
            self._implrtc.alarm_cancel( timerID )
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
        if ret.isOk() or ret == ErrorCode.errNotImplemented:
            ret = ErrorCode.errOk
            data = self._implrtc.memory()
            if data and (length < len(data)):
                data = data[:length]
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
        if ret.isOk() or ret == ErrorCode.errNotImplemented:
            ret = ErrorCode.errOk
            self._implrtc.memory( buffer )
        logger.debug("buffer=%s, ret=%s.", buffer, ret)
        return ret

    