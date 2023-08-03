"""Abstract base types for implementations of battery chargers.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Status", "DCStatus", "PowerSrc", "TemperatureRating",\
           "ChargerError", "EventSource", "EventContext",\
           "Charger"]
from dataclasses import dataclass
from enum import unique, auto, Enum, Flag

from .battery import Status as BatStatus
from .interruptable import EventContext as IntEventContext
from .systypes import ErrorCode, Info


@unique
class Status(Enum):
    """Data class to describe the status or mode of a charging circuitry.\
    This is mainly specified by the phase of a charging cycle.
    """
    
    off        = auto()  # Charger is off.
    preCharge  = auto()  # Pre-charge phase
    trickle    = auto()  # Trickle charge
    fastCharge = auto()  # Fast charge in general
    fastChargeConstCurrent  = auto()  # Fast charge, constant current phase
    fastChargeConstVoltage  = auto()  # Fast charge, constant voltage phase
    topOff     = auto()  # Top-off phase
    done       = auto()  # Charging done
    unknown    = auto()  # Status information unavailable, cannot be determined. 
    
    toStr = {
        off        : 'off',
        preCharge  : 'preCharge',
        trickle    : 'trickle',
        fastCharge : 'fastCharge',
        fastChargeConstCurrent    : 'fastChargeConstCurrent',
        fastChargeConstVoltage    : 'fastChargeConstVoltage',
        topOff    : 'topOff',
        done       : 'done',
        unknown    : 'unknown',
    }
    
@unique
class DCStatus(Enum):
    """Wrapper to hold status information of a DC supply.
    """
    
    off            = auto() # Off, no input supply attached.
    undervoltage   = auto() # Input supply is present, but does not suffice to operate charging circuitry.
    valid          = auto() # A valid input supply is attached, voltage within range.
    overvoltage    = auto() # Input supply present but voltage is way too high.
    unknown        = auto() # Status is unknown, cannot be determined

    toStr = {
        off            : 'off',
        undervoltage   : 'under',
        valid          : 'valid',
        overvoltage    : 'over',
    }

class PowerSrc(Flag):
    """A power source describes a supplier of electrical energy that can\
    be used, e.g. to drive the system.
    """
    
    unknown  = 0  # Power source is unknown, unclear, cannot be determined
    dc       = auto()  # dc supply
    bat      = auto()  # Battery
    dcBat    = dc | bat # Both, dc and Battery available

    toStr = {
        unknown  : 'unknown',
        dc       : 'dc',
        bat      : 'bat',
        dcBat   : 'dc+bat',
    }

class TemperatureRating( Enum ):
    """This type qualitatively describes a temperature, e.g. of a chip.
    """
    
    cold        = 0x02  # Too cold
    cool        = 0x01  # Cool, but still operable
    ok          = 0x00  # Just fine.
    warm        = 0x10  # Warm, but still within the limits
    hot         = 0x20  # Too hot.
    coolOrWarm = (cool | warm)    # Not normal, but within range.
    coldOrHot  = (cold | hot)     # Outside the limits.
    unknown      = 0xFF             # Temperature is unknown, cannot be determined

    toStr = {
        cold        : 'cold',
        cool        : 'cool',
        ok          : 'ok',
        warm        : 'warm',
        hot         : 'hot',
        coolOrWarm  : 'cool or warm',
        coldOrHot   : 'cold or hot',
        unknown     : 'unknown'
    }
    
@unique
class ChargerError(Enum):
    """A type to describe the charger's error condition more precisely.
    
    This is to detail the reason, why charging was stopped or is not
    going to start.
    """

    ok           = 0   # No error.
    config       = 10  # General configuration error
    temp         = 20  # General temperature error
    tempChg      = 21  # Charger (die) temperature out of range
    tempBat      = 22  # Battery temperature out of range
    dc           = 30  # General voltage error
    dcHigh       = 32  # Voltage too high error
    dcLow        = 31  # Low or no voltage error
    bat          = 40  # General battery error
    batLow       = 41  # Battery level is too low
    batBroken    = 42  # Battery is damaged.
    batRemoved   = 43  # Battery is removed.
    timer        = 50  # General timer error.
    unknown      = auto()
    
    toStr = {
        ok           : 'ok',
        config       : 'config',
        temp         : 'temp',
        tempChg      : 'tempChg',
        tempBat      : 'tempBat',
        dc           : 'dc',
        dcHigh       : 'dcHigh',
        dcLow        : 'dcLow',
        bat          : 'bat',
        batLow       : 'batLow',
        batBroken    : 'batBroken',
        batRemoved   : 'batRemoved',
        timer        : 'timer',
        unknown      : 'unknown',
    }

@unique
class EventSource(Flag):
    """Event source type to detail the reason for an interrupt occurrence.
    
    It's ok for an implementation to not support every type of interrupt.
    """
    
    internal                = auto() # Internal fault, e.g. OTG fault or buck-boost fault.
    onOff                   = auto() # Charger enable/disable state changed
    chargingPhase           = auto() # Charger phase/status changed, e.g. from pre- into fast-charge
    inputVoltage            = auto() # e.g. Input voltage applied / switched off
    inputCurrentLimitOwn    = auto() # Own input current limit reached
    inputCurrentLimitSrc    = auto() # Input current limited by source; Voltage dropped.
    batteryTemperature      = auto() # Battery temperature outside limits
    batteryOvercurrent      = auto() # Discharge current exceeds limit
    systemUndervoltage      = auto() # System voltage too low
    systemOvervoltage       = auto() # System voltage applied to charger too high
    thermalShutdown         = auto() # Charger temperature outside limits
    all                     = 0x07FF
    none                    = 0x0000 # No interrupt fired
    unknown                 = 0x8000 # Unknown reason

    int2Str = {
        internal             : 'internal',
        onOff                : 'onOff',
        chargingPhase        : 'chargingPhase',
        inputVoltage         : 'inputVoltage',
        inputCurrentLimitOwn : 'inputCurrentLimitOwn',
        inputCurrentLimitSrc : 'inputCurrentLimitSrc',
        batteryTemperature   : 'batteryTemperature',
        batteryOvercurrent   : 'batteryOvercurrent',
        systemUndervoltage   : 'systemUndervoltage',
        systemOvervoltage    : 'systemOvervoltage',
        thermalShutdown      : 'thermalShutdown',
        all                  : 'all',
        none                 : 'none',
        unknown              : 'unknown',
    }
    
@dataclass
class EventContext( IntEventContext ):
    """Data class holding the context information of an event (interrupt).
    
    Use the :attr:`source` attribute to de-multiplex the inner data items.
    """
    source:     EventSource = EventSource.none
    
class Charger:
    """Abstract base class to describe a battery charger.
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
        """Retrieves an information block from the charging device.
        
        Typically, this kind of information is rather static in that,
        it does not change over time. Usually, this information is
        somewhat unique for the charger origin, manufacturing date,
        hardware/firmware revision, product/model ID, chip series and alike.
        For that reason, this function can be used to see,
        if communication works reliably.

        :return: The information object and an error code indicating either success or the reason of failure.
        :rtype: Info, ErrorCode
        """
        info = Info()
        ret = ErrorCode.errOk
        return info, ret

    def isBatteryPresent(self):
        """Checks, if the battery is present.
        
        This does not tell anything about whether the battery is charged
        or not.
        
        Returns :attr:`ErrorCode.errOk` if a battery is present,
        :attr:`ErrorCode.errUnavailable` if the battery is not present
        and any other value to indicate the reason, why this information
        could not be retrieved.
        
        See also: :meth:`getChgStatus`.

        :return: An error code.
        :rtype: ErrorCode
        """
        return ErrorCode.errNotImplemented
    
    def getNumCells(self):
        """Retrieves the number of battery cells configured.
        
        Returns the number of battery cells or a negative number if this
        information could not be retrieved.

        :return: The number of cells.
        :rtype: int
        """
        return -1
    
    def getBatStatus(self):
        """Get the battery status to tell about the health and state of the battery.
        
        Returns one of the :class:`.battery.Status` values to indicate
        battery voltage level or presence or health state.

        :return: The battery state.
        :rtype: battery.Status
        """
        return BatStatus.unknown
    
    def getChgStatus(self):
        """Retrieves the charging phase or status.
        
        :return: A charger status code to indicate the current charger status.
        :rtype: charger.Status
        """
        return Status.unknown
    
    def getDCStatus(self):
        """Retrieves the DC supply status.

        :return: A status code to indicate the DC supply status.
        :rtype: DCStatus
        """
        return DCStatus.unknown
    
    def getPowerSrc(self):
        """Retrieves the power source, that presumably drives the\
        system at the moment that this function is executed.
        
        :return: A code to indicate the power source.
        :rtype: PowerSrc
        """
        return PowerSrc.unknown

    def getChargerTempStatus(self):
        """Retrieves the charger's temperature state.

        :return: A rating code to indicate the temperature rating of the charger chip.
        :rtype: TemperatureRating
        """
        return TemperatureRating.unknown


    def getBatteryTempStatus(self):
        """Retrieves the battery's temperature status.

        :return: A rating code to indicate the temperature rating of the battery element.
        :rtype: TemperatureRating
        """
        return TemperatureRating.unknown

    def getError(self):
        """Determines the error state for the charger chip, if one.

        :return: A charger error code to further describe reason for the error.
        :rtype: ChargerError
        """
        return ChargerError.unknown

    def restartCharging(self):
        """Tries to restart the charging phase.
        
        This could be necessary, e.g. after recovering from a thermal
        shutdown.

        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errNotImplemented

    