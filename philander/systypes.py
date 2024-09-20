"""Data types commonly used throughout the system and not associated with any specific module.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["ErrorCode", "RunLevel", "Info",]

class ErrorCode():
    """Data type to indicate either a successful completion or the\
    reason why some function or operation failed.
    """
    
    class Value():
        """Helper class to encapsulate the error code data type.
        
        This is to make the ErrorCode class attributes be objects that
        provide methods like isOk(). 
        """
        def __init__(self, value):
            self.value = value

        def isOk(self):
            return self.value == ErrorCode.errOk.value
        
        def __str__(self):
            valdict = {
                ErrorCode.errOk.value:                  "errOk",
                ErrorCode.errInvalidParameter.value:    "errInvalidParameter",
                ErrorCode.errInadequate.value:          "errInadequate",
                ErrorCode.errNotImplemented.value:      "errNotImplemented",
                ErrorCode.errNotSupported.value:        "errNotSupported",
                ErrorCode.errInternal.value:            "errInternal",
                ErrorCode.errMoreData.value:            "errMoreData",
                ErrorCode.errFewData.value:             "errFewData",
                ErrorCode.errExhausted.value:           "errExhausted",
                ErrorCode.errBusy.value:                "errBusy",
                ErrorCode.errUnavailable.value:         "errUnavailable",
                ErrorCode.errSpecRange.value:           "errSpecRange",
                ErrorCode.errResourceConflict.value:    "errResourceConflict",
                ErrorCode.errCorruptData.value:         "errCorruptData",
                ErrorCode.errOverflow.value:            "errOverflow",
                ErrorCode.errUnderrun.value:            "errUnderrun",
                ErrorCode.errPreProc.value:             "errPreProc",
                ErrorCode.errPostProc.value:            "errPostProc",
                ErrorCode.errCancelled.value:           "errCancelled",
                ErrorCode.errSuspended.value:           "errSuspended",
                ErrorCode.errFailure.value:             "errFailure",
                ErrorCode.errMalfunction.value:         "errMalfunction",
            }
            vstr = valdict.get( self.value, str(self.value) )
            ret = "ErrorCode." + vstr
            return ret

    errOk				= Value(0)		# No error, success.
    errInvalidParameter	= Value(1)		# Parameter is NULL or out of range.
    errInadequate		= Value(2)		# Senseless function call or parameter value.
    errNotImplemented	= Value(3)		# Function is not (yet) implemented.
    errNotSupported		= Value(4)		# Feature is not supported by hardware.
    errInternal			= Value(5)		# Internal inconsistency or bug.
    errMoreData			= Value(6)		# Buffer too short, more data available.
    errFewData			= Value(7)		# Too few or no data, e.g. to receive.
    errExhausted		= Value(8)		# Resource exhausted.
    errBusy				= Value(9)		# Resource (HW) is busy.
    errUnavailable		= Value(10)     # Resource (HW) cannot be reached.
    errSpecRange		= Value(11)     # HW (Sensor) out of specified range.
    errResourceConflict	= Value(12)	    # Tried to allocate occupied resource.
    errCorruptData		= Value(13)	    # UART framing/parity or I2C bus error.
    errOverflow			= Value(14)	    # Buffer or arithmetic overflow.
    errUnderrun			= Value(15)	    # Buffer under-run, arithmetically indefinite.
    errPreProc			= Value(16)	    # Data needs/has (wrong) pre-processing.
    errPostProc			= Value(17)	    # Data needs (no) further processing.
    errCancelled		= Value(18)	    # Action aborted, cancelled, finally terminated.
    errSuspended		= Value(19)	    # Action suspended, interrupted (may be resumed).
    errFailure			= Value(20)	    # Action failed, but might be successful in next trials.
    errMalfunction		= Value(21)	    # (Persistent) defect of underlying HW.


class RunLevel():
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

