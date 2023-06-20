# -*- coding: utf-8 -*-
"""Module to describe objects that provide wath dog capabilities.

"""
from systypes import ErrorCode
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Watchdog"]

class Watchdog:
    """Interface to define watch dog related methods.
    
    """
    
    INTERVAL_MS_DEFAULT = 1000  # Default time interval in milliseconds
    
    @classmethod
    def Params_init(cls, paramDict):
        """Initialize parameters with their defaults.

        If the implementing class supports the :class:`.Module` interface,
        it can use this method to fill commonly supported options. 
        
        The following settings are supported:
        
        =============================    ==========================================================================================================
        Key name                         Value type, meaning and default
        =============================    ==========================================================================================================
        Watchdog.Interval                ``int`` Watch dog interval in milliseconds; default is :attr:`INTERVAL_MS_DEFAULT`.
        =============================    ==========================================================================================================
        
        Also see: :meth:`.Module.Params_init`. 
        
        :param dict(str, object) paramDict: Dictionary mapping option\
        names to their respective values.
        :returns: none
        :rtype: None
        """
        
        if not ("Watchdog.Interval" in paramDict):
            paramDict["Watchdog.Interval"] = Watchdog.INTERVAL_MS_DEFAULT
        return None
                                


    def enableWatchdog(self):
        """Enable and restart the watch dog.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errNotImplemented
    
    def disableWatchdog(self):
        """Disable the watch dog and stop it from running, immediately.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errNotImplemented
    
    def isWatchdogRunning(self):
        """Check, whether the watchdog is currently running or not.
        
        Returns :attr:`.ErrorCode.errOk`, if the watch dog is running,
        :attr:`.ErrorCode.errUnavailable`, if it is not running and
        any other value to indicate the reason, why this information
        could not be retrieved.
        
        :return: An error code indicating the result.
        :rtype: ErrorCode
        """
        return ErrorCode.errNotImplemented

    def clearWatchdog(self):
        """Clear the watch dog.
        
        This is the implementation of the acknowledge mechanism.
        Calling this function is necessary for an application to prevent
        the watch dog from elapsing.
        Note that this method does not start the watch dog, when it is
        disabled.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errNotImplemented

    def isWatchdogElapsed(self):
        """Check, whether the configured time interval has expired, or not.
        
        By calling this function, an application may observe the
        expiration without using the interrupt mechanism.
        Note, that this flag is not cleared automatically. The caller
        would have to use :meth:`clearWatchdogElapsed` for this purpose.

        Returns :attr:`.ErrorCode.errOk`, if the watch dog has elapsed,
        :attr:`.ErrorCode.errUnavailable`, if it is not elapsed, yet, and
        any other value to indicate the reason, why this information
        could not be retrieved.
        
        :return: An error code indicating the result.
        :rtype: ErrorCode
        """
        return ErrorCode.errNotImplemented

    def clearWatchdogElapsed(self):
        """Clear the elapsed flag.
        
        The application should call this function after it observed that
        the watch dog interval time expired.
        
        Also see: :meth:`isWatchdogElapsed`.

        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errNotImplemented
    
