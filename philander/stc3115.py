"""A module to provide base classes and data types for gas gauge driver implementations.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["STC3115",]

from philander.stc3115_reg import STC3115_Reg as Register
from philander.stc311x import STC311x


class STC3115(STC311x):
    """Driver implementation for the stc3115 gas gauge.
    
    Info about this chip can be found at ST microelectronics
    https://www.st.com/en/power-management/stc3115.html
    """

    MODEL_ID = 3115

    def __init__(self):
        STC311x.__init__(self)
        self.REGISTER = Register()

    def _setupCurrentMonitoring(self):
        err = super()._setupCurrentMonitoring()
        if err.isOk():
            # REG_RELAX_MAX counter, LSB=4s, scaling = 1/4
            data = (self.relaxTimerCC2VM + 2) // 4
            err = self.writeByteRegister( self.REGISTER.REG_RELAX_MAX, data )
        return err
    
