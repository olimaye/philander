"""ADC implementation with a built-in simulation.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_ADC_Sim"]

from philander.adc import ADC
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

class _ADC_Sim( ADC ):
    """Implementation of the abstract ADC interface for the Micropython environment.
    """
    
    def __init__(self):
        """Initialize the instance with defaults.
        """
        super().__init__()
        self.provider = SysProvider.SIM
        self.simValue = 0

    #
    # Module API
    #


    #
    # ADC specific API
    #

    def getDigital(self):
        """Retrieve a sample and return its digital value.

        Gives the most recent sample as a digital value between zero and
        the maximum digital value [0...DIGITAL_MAX].
        
        :return: A value in the range [0, DIGITAL_MAX] and an error code\
        indicating either success or the reason of failure.
        :rtype: int, ErrorCode
        """
        if self.isOpen:
            val = self.simValue
            err = ErrorCode.errOk
            self.simValue = self.simValue + 0x21D
        else:
            val = 0
            err = ErrorCode.errResourceConflict
        return val, err

