"""Data types commonly used throughout the system and not associated with any specific module.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["ErrorCode", "RunLevel", "Info",]
from enum import Enum

class ErrorCode(Enum):
    """Data type to indicate either a successful completion or the\
    reason why some function or operation failed.
    """
    errOk				= 0		# No error, success.
    errInvalidParameter	= 1		# Parameter is NULL or out of range.
    errInadequate		= 2		# Senseless function call or parameter value.
    errNotImplemented	= 3		# Function is not (yet) implemented.
    errNotSupported		= 4		# Feature is not supported by hardware.
    errInternal			= 5		# Internal inconsistency or bug.
    errMoreData			= 6		# Buffer too short, more data available.
    errFewData			= 7		# Too few or no data, e.g. to receive.
    errExhausted		= 8		# Resource exhausted.
    errBusy				= 9		# Resource (HW) is busy.
    errUnavailable		= 10	# Resource (HW) cannot be reached.
    errSpecRange		= 11	# HW (Sensor) out of specified range.
    errResourceConflict	= 12	# Tried to allocate occupied resource.
    errCorruptData		= 13	# UART framing/parity or I2C bus error.
    errOverflow			= 14	# Buffer or arithmetic overflow.
    errUnderrun			= 15	# Buffer under-run, arithmetically indefinite.
    errPreProc			= 16	# Data needs/has (wrong) pre-processing.
    errPostProc			= 17	# Data needs (no) further processing.
    errCancelled		= 18	# Action aborted, cancelled, finally terminated.
    errSuspended		= 19	# Action suspended, interrupted (may be resumed).
    errFailure			= 20	# Action failed, but might be successful in next trials.
    errMalfunction		= 21	# (Persistent) defect of underlying HW.

    def isOk(self):
        return self == ErrorCode.errOk


class RunLevel(Enum):
    """Operating mode that the CPU may run in.
    
    Includes the normal (active) mode as well as a bunch of
    power-saving run levels.
    """
    active			 = 0	# Active mode, normal operation
    idle			 = 1	# Low power mode, may save some power
    relax			 = 2	# Low power mode, may save some more power
    snooze			 = 3	# Low power mode, may save some more power
    nap				 = 4	# Low power mode, may save some more power
    sleep			 = 5	# Low power mode, may save some more power
    deepSleep		 = 6	# Low power mode, may save some more power
    shutdown		 = 7	# Low power mode, saves most power

    standby			 = snooze   # Synonym for stand by
    leastPowerSave	 = idle     # Generic synonym
    mostPowerSave	 = shutdown # Generic synonym
    leastFunctional	 = shutdown # Generic synonym
    mostFunctional	 = idle     # Generic synonym

class Info:
    """Container type to wrap chip information data as retrieved from\
    calls of :meth:`Sensor.getInfo`.
    
    This is rather static information not changing too much over time.
    """
    
    validChipID    = 0x01  # The chipID is valid
    validRevMajor  = 0x02  # Major revision is valid.
    validRevMinor  = 0x04  # Minor revision is valid.
    validModelID   = 0x08  # Valid module identification.
    validManufacID = 0x10  # Valid manufacturer ID
    validSerialNum = 0x20  # Serial number is valid.
    validNothing   = 0x00  # No attribute valid.
    validAnything  = 0xFF  # All attributes are valid.

    def __init__(self):
        self.validity = Info.validNothing
        self.chipID = 0
        self.revMajor = 0
        self.revMinor = 0
        self.modelID = 0
        self.manufacturerID = 0
        self.serialNumber = 0

