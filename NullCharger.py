from BatteryCharger import BatteryCharger

class NullCharger( BatteryCharger ):

    def init( self ):
        pass
    
    def close(self):
        pass
        
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
        return False
    
    #
    # Retrieves the number of battery cells configured.
    # Raises RuntimeError in case this information cannot be determined.
    #
    def getNumCells(self):
        return 0
    
    #
    # Get the battery status.
    # Returns one of the BAT_STATE_xxx values to indicate battery voltage level or 
    # presence or health state.
    # Raises RuntimeError in case this information cannot be determined.
    #
    def getBatStatus(self):
        return BatteryCharger.BAT_STATE_REMOVED
    
    #
    # Retrieves the charge phase or status.
    # Returns one of the CHG_STATE_xxx values to indicate the current charge status.
    # Raises RuntimeError in case the charge status cannot be determined.
    #
    def getChgStatus(self):
        return BatteryCharger.CHG_STATE_OFF
    
    #
    # Retrieves the DC supply status.
    # Returns one of the DC_STATE_xxx values to indicate the DC supply status.
    # Raises RuntimeError in case the information cannot be determined.
    def getDCStatus(self):
        return BatteryCharger.DC_STATE_VALID
    
    #
    # Retrieves the current power source.
    # Returns one of the PWRSRC_xxx values to indicate the current power source.
    # Raises RuntimeError in case the information cannot be determined.
    #
    def getPowerSrc(self):
        return BatteryCharger.PWR_SRC_DC

    #
    # Retrieves the charger's temperature state.
    # Returns one of the TEMP_xxx values to indicate the temperature status.
    # Raises RuntimeError in case the information cannot be determined.
    #
    def getChargerTempState(self):
        return BatteryCharger.TEMP_OK


    #
    # Retrieves the battery's temperature state.
    # Returns one of the TEMP_xxx values to indicate the temperature status.
    # Raises RuntimeError in case the information cannot be determined.
    #
    def getBatteryTempState(self):
        return BatteryCharger.TEMP_OK

    #
    # Determines the error state, if one.
    # Returns one of the ERR_xxx values to indicate the error reason.
    # Raises RuntimeError in case the information cannot be determined.
    #
    def getError(self):
        return BatteryCharger.ERR_OK

    #
    # Tries to restart the charging phase, e.g. after recovering from a thermal shutdown
    # Raises RuntimeError in case the procedure is not available.
    def restartCharging(self):
        pass

