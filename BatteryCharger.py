from InterruptSource import InterruptSource
from Configurable import Configurable

class BatteryCharger( InterruptSource, Configurable ):

    BAT_STATE_UNKNOWN       = 0 # Battery state is unavailable
    BAT_STATE_REMOVED       = 1 # Battery removed
    BAT_STATE_EMPTY         = 2 # Battery empty, deep discharge
    BAT_STATE_LOW           = 3 # Battery voltage low
    BAT_STATE_NORMAL        = 4 # Battery voltage ok
    BAT_STATE_OVERVOLTAGE   = 5 # Battery voltage greater than threshold
    BAT_STATE_OVERCURRENT   = 6 # Battery current to high
    BAT_STATE_TIME          = 7 # Charging takes (too) long; old/damaged battery

    chgState2Str = {
        BAT_STATE_UNKNOWN       : 'UNKNOWN',
        BAT_STATE_REMOVED       : 'REMOVED',
        BAT_STATE_EMPTY         : 'EMPTY',
        BAT_STATE_LOW           : 'LOW',
        BAT_STATE_NORMAL        : 'NORMAL',
        BAT_STATE_OVERVOLTAGE   : 'OVERVOLTAGE',
        BAT_STATE_OVERCURRENT   : 'OVERCURRENT',
        BAT_STATE_TIME          : 'TIME',
    }
    
    CHG_STATE_OFF        = 0  # Charger is off.
    CHG_STATE_PRECHARGE  = 1  # Precharge
    CHG_STATE_TRICKLE    = 2  # Trickle charge
    CHG_STATE_FASTCHARGE = 3  # Fast charge in general
    CHG_STATE_FAST_CC    = 4  # Fast charge, constant current phase
    CHG_STATE_FAST_CV    = 5  # Fast charge, constant voltage phase
    CHG_STATE_TOP_OFF    = 6  # Top-off phase
    CHG_STATE_DONE       = 7  # Charging done
    
    chgState2Str = {
        CHG_STATE_OFF        : 'OFF',
        CHG_STATE_PRECHARGE  : 'PRECHARGE',
        CHG_STATE_TRICKLE    : 'TRICKLE',
        CHG_STATE_FASTCHARGE : 'FASTCHARGE',
        CHG_STATE_FAST_CC    : 'FAST_CC',
        CHG_STATE_FAST_CV    : 'FAST_CV',
        CHG_STATE_TOP_OFF    : 'TOP_OFF',
        CHG_STATE_DONE       : 'DONE',
    }
    
    DC_STATE_OFF            = 0
    DC_STATE_UNDERVOLTAGE   = 1
    DC_STATE_VALID          = 2
    DC_STATE_OVERVOLTAGE    = 3

    dcState2Str = {
        DC_STATE_OFF            : 'OFF',
        DC_STATE_UNDERVOLTAGE   : 'UNDER',
        DC_STATE_VALID          : 'VALID',
        DC_STATE_OVERVOLTAGE    : 'OVER',
    }
        
    PWR_SRC_NONE     = 0  # unclear
    PWR_SRC_DC       = 1  # DC supply
    PWR_SRC_BAT      = 2  # Battery
    PWR_SRC_DC_BAT   = PWR_SRC_DC | PWR_SRC_BAT # Both, DC and Battery available

    pwrsrc2Str = {
        PWR_SRC_NONE     : 'NONE',
        PWR_SRC_DC       : 'DC',
        PWR_SRC_BAT      : 'BAT',
        PWR_SRC_DC_BAT   : 'DC+BAT',
    }
    
    TEMP_COLD        = 0  # Too cold
    TEMP_COOL        = 1  # Cool, but still operable
    TEMP_OK          = 2  # Just fine.
    TEMP_WARM        = 3  # Warm, but still within the limits
    TEMP_HOT         = 4  # Too hot.

    temp2Str = {
        TEMP_COLD        : 'COLD',
        TEMP_COOL        : 'COOL',
        TEMP_OK          : 'OK',
        TEMP_WARM        : 'WARM',
        TEMP_HOT         : 'HOT',
    }
    
    ERR_OK           = 0   # No error.
    ERR_CONFIG       = 10  # General configuration error
    ERR_TEMP         = 20  # General temperature error
    ERR_TEMP_CHG     = 21  # Charger (die) temperature out of range
    ERR_TEMP_BAT     = 22  # Battery temperature out of range
    ERR_DC           = 30  # General voltage error
    ERR_DC_HIGH      = 32  # Voltage too high error
    ERR_DC_LOW       = 31  # Low or no voltage error
    ERR_BAT          = 40  # General battery error
    ERR_BAT_LOW      = 41  # Battery level is too low
    ERR_BAT_BROKEN   = 42  # Battery is damaged.
    ERR_BAT_REMOVED  = 43  # Battery is removed.
    ERR_TIMER        = 50  # General timer error.
    
    err2Str = {
        ERR_OK           : 'OK',
        ERR_CONFIG       : 'CONFIG',
        ERR_TEMP         : 'TEMP',
        ERR_TEMP_CHG     : 'TEMP_CHG',
        ERR_TEMP_BAT     : 'TEMP_BAT',
        ERR_DC           : 'DC',
        ERR_DC_HIGH      : 'DC_HIGH',
        ERR_DC_LOW       : 'DC_LOW',
        ERR_BAT          : 'BAT',
        ERR_BAT_LOW      : 'BAT_LOW',
        ERR_BAT_BROKEN   : 'BAT_BROKEN',
        ERR_BAT_REMOVED  : 'BAT_REMOVED',
        ERR_TIMER        : 'TIMER',
    }
   
    # Interrupts
    INT_OTG_BUCK_BOOST      = 0x0001 # Internal fault, e.g. OTG fault or buck-boost fault.
    INT_CHARGER_ONOFF       = 0x0002 # Charger enable/disable state changed
    INT_INPUT_CURRENT_LIMIT = 0x0004 # Own input current limit reached
    INT_BATTERY_TEMPERATURE = 0x0008 # Battery temperature outside limits
    INT_STATE_CHANGED       = 0x0010 # Charger state changed, e.g. from pre- into fast-charge
    INT_BATTERY_OVERCURRENT = 0x0020 # Discharge current exceeds limit
    INT_CHARGER_INPUT       = 0x0040 # e.g. Input voltage applied / switched off
    INT_INCURR_LIM_BY_SRC   = 0x0080 # Input current limited by source; Voltage dropped.
    INT_SYSTEM_UNDERVOLTAGE = 0x0100 # System voltage too low
    INT_SYSTEM_OVERVOLTAGE  = 0x0200 # System voltage apllied to charger too high
    INT_THERMAL_SHUTDOWN    = 0x0400 # Charger temperature outside limits
    INT_ALL                 = 0x07FF

    int2Str = {
        INT_OTG_BUCK_BOOST      : 'BatteryCharger.OTG_BUCK_BOOST',
        INT_CHARGER_ONOFF       : 'BatteryCharger.CHARGER_ONOFF',
        INT_INPUT_CURRENT_LIMIT : 'BatteryCharger.INPUT_CURRENT_LIMIT',
        INT_BATTERY_TEMPERATURE : 'BatteryCharger.BATTERY_TEMPERATURE',
        INT_STATE_CHANGED       : 'BatteryCharger.STATE_CHANGED',
        INT_BATTERY_OVERCURRENT : 'BatteryCharger.BATTERY_OVERCURRENT',
        INT_CHARGER_INPUT       : 'BatteryCharger.CHARGER_INPUT',
        INT_INCURR_LIM_BY_SRC   : 'BatteryCharger.INCURR_LIM_BY_SRC',
        INT_SYSTEM_UNDERVOLTAGE : 'BatteryCharger.SYSTEM_UNDERVOLTAGE',
        INT_SYSTEM_OVERVOLTAGE  : 'BatteryCharger.SYSTEM_OVERVOLTAGE',
        INT_THERMAL_SHUTDOWN    : 'BatteryCharger.THERMAL_SHUTDOWN',
        INT_ALL                 : 'BatteryCharger.*',
    }

    #
    # Configurable API
    #
    
    def _scanParameters( self, paramDict ):
        # Scan parameters
        #if "BatteryCharger.Limit" in paramDict:
        #    self.limit = self._detectDriverModule( paramDict["BatteryCharger.Limit"] )
        pass
                                
    #
    # Initializes the object.
    # The only input parameter is a dictionary containing key-value pairs that
    # configure the instance. Key names and their meanings are:
    def __init__( self, paramDict ):
        # This class parameter
        Configurable.__init__( self, paramDict )

        # initialize local attributes
        

    #
    # Soft resets the device. The device is in some default state, afterwards and
    # must be re-configured according to the application's needs.
    #
    def reset(self):
        pass

    #
    # Returns the chip ID.
    #
    def getID(self):
        pass

    #
    # Reads the chip ID and verifies it against the
    # expected value.
    #
    def checkID(self):
        pass

    #
    # Tests the communication with the sensor device.
    #
    def testConnection(self):
        self.getID()
        
    #
    # Specific API
    #
    
    #
    # Checks, if the battery is present.
    # Returns TRUE if a battery is present, FALSE otherwise. The return value does not tell
    # about whether the battery is charged or not.
    # Raises RuntimeError in case the battery status cannot be determined.
    #
    def isBatteryPresent(self):
        pass
    
    #
    # Retrieves the number of battery cells configured.
    # Raises RuntimeError in case this information cannot be determined.
    #
    def getNumCells(self):
        pass
    
    #
    # Get the battery status.
    # Returns one of the BAT_STATE_xxx values to indicate battery voltage level or 
    # presence or health state.
    # Raises RuntimeError in case this information cannot be determined.
    #
    def getBatStatus(self):
        pass
    
    #
    # Retrieves the charge phase or status.
    # Returns one of the CHG_STATE_xxx values to indicate the current charge status.
    # Raises RuntimeError in case the charge status cannot be determined.
    #
    def getChgStatus(self):
        pass
    
    #
    # Retrieves the DC supply status.
    # Returns one of the DC_STATE_xxx values to indicate the DC supply status.
    # Raises RuntimeError in case the information cannot be determined.
    def getDCStatus(self):
        pass
    
    #
    # Retrieves the current power source.
    # Returns one of the PWRSRC_xxx values to indicate the current power source.
    # Raises RuntimeError in case the information cannot be determined.
    #
    def getPowerSrc(self):
        pass

    #
    # Retrieves the charger's temperature state.
    # Returns one of the TEMP_xxx values to indicate the temperature status.
    # Raises RuntimeError in case the information cannot be determined.
    #
    def getChargerTempState(self):
        pass


    #
    # Retrieves the battery's temperature state.
    # Returns one of the TEMP_xxx values to indicate the temperature status.
    # Raises RuntimeError in case the information cannot be determined.
    #
    def getBatteryTempState(self):
        pass

    #
    # Determines the error state, if one.
    # Returns one of the ERR_xxx values to indicate the error reason.
    # Raises RuntimeError in case the information cannot be determined.
    #
    def getError(self):
        pass

    #
    # Tries to restart the charging phase, e.g. after recovering from a thermal shutdown
    # Raises RuntimeError in case the procedure is not available.
    def restartCharging(self):
        pass

    