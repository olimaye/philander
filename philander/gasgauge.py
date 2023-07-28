# -*- coding: utf-8 -*-
"""A module to provide base classes and data types for gas gauge driver implementations.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["GasGauge","SOCChangeRate", "EventSource", "EventContext",\
           "StatusID",]
from dataclasses import dataclass
from enum import unique, Enum, auto

from .battery import Status as BatStatus, Level as BatLevel
from .primitives import Current, Voltage, Percentage
from .systypes import ErrorCode, Info


@dataclass
class SOCChangeRate(int):
    """State of charge (SOC) change rate, given in milli-C rate [mC].

    Remember 1C = 100% per 1 hour.
    """

    invalid = 0xFFFF

@unique
class EventSource(Enum):
    """ * Event source type to detail the reason for an interrupt occurrence.
    
    Not all implementations will support all types of interrupt.
    """

    none            = auto(),
    """No event reason"""
    lowSOC          = auto(),
    """SOC dropped below a threshold"""
    highSOC          = auto(),
    """SOC reached a high/full info level"""
    lowVolt         = auto(),
    """Battery voltage dropped below a threshold"""
    batFail         = auto(),
    """General battery failure, e.g. battery swapped"""
    undervoltage    = auto(),
    """Brown-out/Lockout due to low voltage"""
    hardReset       = auto(),
    """Power-on reset detected"""
    unknown         = auto(),
    """Unknown event reason"""

@dataclass
class EventContext:
    """Event context type to detail the context information for an interrupt occurrence.
    """
    source: EventSource = EventSource.none
    soc:    Percentage = Percentage.invalid
    voltage:  Voltage = Voltage.invalid
    batStatus:  BatStatus = BatStatus.unknown

@unique
class StatusID(Enum):
    """Data class to comprise different types of status information.
    """
    batTemp     = auto()
    dieTemp     = auto()

class GasGauge():
    """This is a driver base class for a gas gauge IC.
    
    A gas gauge allows to keep track of the state of charge
    (SOC), remaining capacity, current voltage etc. of a battery.
    """

    def reset(self):
        """Soft resets the device.
        
        The device is in some default state, afterwards and must be
        re-configured according to the application's needs.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errNotImplemented
    
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
        ret = ErrorCode.errOk
        return info, ret

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


    
    def getStateOfCharge( self ):
        """Retrieves the state of charge.
        
        That is the fraction of electric energy from the total capacity,
        that is still or already stored in the battery. This information
        is valid for both, the charging as well as the discharging process.
        
        :return: A percentage [0...100] value or :attr:`Percentage.invalid`\
        to indicate that this information could not be retrieved.
        :rtype: Percentage
        """
        return Percentage.invalid

    def getChangeRate( self ):
        """Retrieves the SOC change rate in milli C.
        
        Remember that 1C = 100% in 1 hour. This information may be used
        to estimate the remaining stamina or how long the charging
        process will still take.
        :return: A SOC change rate (non-negative) or :attr:'SOCChangeRate.invalid`\
        to indicate that this information could not be retrieved.
        :rtype: SOCChangeRate
        """
        return SOCChangeRate.invalid
    
    def getBatteryVoltage( self ):
        """Retrieves the battery voltage in milli Volt.
        
        :return: A on-negative integer value [mV] or :attr:`Voltage.invalid`\
        to indicate that this information could not be retrieved.
        :rtype: Voltage
        """
        return Voltage.invalid

    def getBatteryCurrent( self ):
        """Retrieves the battery current in micro Ampere at the time this\
        function is executed.
        
        See also: :meth:`getBatteryCurrentAvg`
        
        :return: A on-negative integer value [µA] or :attr:`Current.invalid`\
        to indicate that this information could not be retrieved.
        :rtype: Current
        """
        return Current.invalid

    def getBatteryCurrentAvg( self ):
        """Retrieves the average battery current.
        
        The average is taken over some time interval, e.g. 2 seconds.
        The length of the time window is at the discretion of the
        implementation and cannot be adjusted by the caller.
        
        See also: :meth:`getBatteryCurrent`
        
        :return: A on-negative integer value [�A] or :attr:`Current.invalid`\
        to indicate that this information could not be retrieved.
        :rtype: Current
        """
        return Current.invalid


    def rateSOC( self, soc ):
        """Convert a continuous SOC percentage into its next-lower battery level predicate.
        
        Does not retrieve any information from the underlying hardware.

        :param Percentage soc: The state of charge, given in percent.
        :return: The next-lower battery level mnemonic.
        :rtype: battery.Level
        """
        ret = BatLevel.medium
        if soc >= BatLevel.full:
            ret = BatLevel.full
        elif soc >= BatLevel.good:
            ret = BatLevel.good
        elif soc >= BatLevel.medium:
            ret = BatLevel.medium
        elif soc >= BatLevel.low:
            ret = BatLevel.low
        elif soc >= BatLevel.empty:
            ret = BatLevel.empty
        else:
            ret = BatLevel.deepDischarge
        return ret
    
    def getRatedSOC( self ):
        """Retrieve the current state of charge as a discrete battery level predicate.

        :return: The next-lower battery level corresponding to the current SOC.
        :rtype: battery.Level
        """
        soc = self.getStateOfCharge()
        lvl = self.rateSOC( soc )
        return lvl
    
    def getRatedSOCStr( self ):
        """Retrieve the remaining capacity as a battery level string.

        :return: The next-lower battery level corresponding to the current SOC.
        :rtype: String
        """
        lvl = self.getRatedSOC()
        lvlStr = BatLevel.toStr.get( lvl, 'unknown' )
        return lvlStr

