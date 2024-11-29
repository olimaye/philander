"""A module to provide base classes and data types for gas gauge driver implementations.
"""
__author__ = "Carl Bellgardt"
__version__ = "0.1"
__all__ = ["STC3117",]

from philander.gasgauge import SOCChangeRate
from philander.primitives import Current
from philander.stc3117_reg import STC3117_Reg as Register
from philander.stc311x import STC311x, OperatingMode
from philander.systypes import ErrorCode


class STC3117(STC311x):
    """Driver implementation for the stc3117 gas gauge.
    
    Info about this chip can be found at ST microelectronics
    https://www.st.com/en/power-management/stc3117.html
    """
    
    MODEL_ID = 3117

    def __init__(self):
        STC311x.__init__(self)
        self.REGISTER = Register()


    #
    # Gasgauge API
    #

    @staticmethod
    def _transferChangeRate(data):
        # LSB is 8.789 mC, scaling factor is 8.789 = 8789/1000
        ret = (data * 8789 + 500) / 1000
        return ret

    def getChangeRate(self):
        """Retrieves the SOC change rate in milli C.

        Remember that 1C = 100% in 1 hour. This information may be used
        to estimate the remaining stamina or how long the charging
        process will still take.
        :return: A SOC change rate (non-negative) or :attr:'SOCChangeRate.invalid`\
        to indicate that this information could not be retrieved.
        :rtype: SOCChangeRate
        """
        opMode = self._getOperatingMode()
        if opMode == opMode.opModeVoltage:
            data, err = self.readWordRegister(self.REGISTER.REG_AVG_CURRENT)
            if err.isOk():
                ret = self._transferChangeRate(data)
            else:
                ret = SOCChangeRate.invalid
        else:
            ret = SOCChangeRate.invalid
        return ret


    def _transferCurrentAvg(self, data):
        # Again, we actually read out the voltage drop over the sense resistor.
        # LSB is 1.47V, partial scaling factor is 1.47 = 147/100
        # Value is signed!
        # Total scaling factor is: 147 / 100 * 1000 / Rs = 147 * 10 / Rs = 1470 / rs.
        if data >= 0:
            ret = (data * 1470 + self.RSense/2) / self.RSense
        else:
            ret = (data * 1470 - self.RSense/2) / self.RSense
        ret = Current(ret)
        return ret

    def getBatteryCurrentAvg(self):
        """Retrieves the average battery current.
        
        The average is taken over some time interval, e.g. 2 seconds.
        The length of the time window is at the discretion of the
        implementation and cannot be adjusted by the caller.
        
        See also: :meth:`getBatteryCurrent`

        :return: A non-negative integer value [micro A] or :attr:`Current.invalid`\
        to indicate that this information could not be retrieved.
        :rtype: Current
        """
        ret = Current.invalid
        if self._getOperatingMode() == OperatingMode.opModeMixed:
            data, err = self.readWordRegister(self.REGISTER.REG_AVG_CURRENT)
            if err.isOk():
                ret = self._transferCurrentAvg(data)
        return ret

    def _setupCurrentMonitoring(self):
        err = super()._setupCurrentMonitoring()
        if err.isOk():
            # REG_CMONIT_MAX counter, LSB=4s, scaling = 1/4
            data = (self.relaxTimerCC2VM + 2) // 4
            err = self.writeByteRegister( self.REGISTER.REG_CMONIT_MAX, data )
        return err
    
