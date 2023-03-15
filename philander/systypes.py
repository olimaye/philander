from enum import Enum

class ErrorCode(Enum):
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


class RunLevel(Enum):
	runLevelActive			 = 0	# Active mode, normal operation
	runLevelIdle			 = 1	# Low power mode, may save some power
	runLevelRelax			 = 2	# Low power mode, may save some more power
	runLevelSnooze			 = 3	# Low power mode, may save some more power
	runLevelNap				 = 4	# Low power mode, may save some more power
	runLevelSleep			 = 5	# Low power mode, may save some more power
	runLevelDeepSleep		 = 6	# Low power mode, may save some more power
	runLevelShutdown		 = 7	# Low power mode, saves most power
	
	runLevelStandby			 = runLevelSnooze,   # Synonym for stand by
	runLevelLeastPowerSave	 = runLevelIdle,     # Generic synonym
	runLevelMostPowerSave	 = runLevelShutdown, # Generic synonym
	runLevelLeastFunctional	 = runLevelShutdown, # Generic synonym
	runLevelMostFunctional	 = runLevelIdle,     # Generic synonym
