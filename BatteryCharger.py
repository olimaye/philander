class BatteryCharger:


    STATE_OFF        = 0  # Charger is off.
    STATE_PRECHARGE  = 1  # Precharge
    STATE_TRICKLE    = 2  # Trickle charge
    STATE_FASTCHARGE = 3  # Fast charge in general
    STATE_FAST_CC    = 4  # Fast charge, constant current phase
    STATE_FAST_CV    = 5  # Fast charge, constant voltage phase
    STATE_TOP_OFF    = 6  # Top-off phase
    STATE_DONE       = 7  # Charging done
    
    PWR_SRC_NONE     = 0  # unclear
    PWR_SRC_DC_ONLY  = 1  # Only DC supply
    PWR_SRC_DC_BAT   = 2  # Both, DC and Battery available
    PWR_SRC_BAT_ONLY = 3  # Battery only, no DC
    
    TEMP_COLD        = 0  # Too cold
    TEMP_COOL        = 1  # Cool, but still operable
    TEMP_OK          = 2  # Just fine.
    TEMP_WARM        = 3  # Warm, but still within the limits
    TEMP_HOT         = 4  # Too hot.
    
    ERR_OK           = 0
    ERR_TEMP_CHG     = 1
    ERR_TEMP_BAT     = 2
    ERR_DC_HIGH      = 3
    ERR_DC_LOW       = 4
    ERR_BAT_LOW      = 5
    ERR_BAT_BROKEN   = 6
    
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
    INT_RSV_11              = 0x0800
    INT_RSV_12              = 0x1000
    INT_RSV_13              = 0x2000
    INT_RSV_14              = 0x4000
    INT_RSV_15              = 0x8000
    INT_NONE                = 0x0000
    INT_ALL                 = 0x07FF


    #
    # Initializes the object.
    # The only input parameter is a dictionary containing key-value pairs that
    # configure the instance. Key names and their meanings are:
    def __init__( self, paramDict ):
        # This class parameter

        # initialize local attributes
        self.intHandler = None
        

    #
    # Initializes the instance. Is automatically called while instantiating
    # a new object. Can be used to re-initialize a sensor, e.g. after
    # resetting.
    #
    def init(self):
        pass

    #
    # Just closes the object. Should be called at the end of a program.
    #
    def close(self):
        pass

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
    # Raises RuntimeError in case the battery status cannot be determined.
    #
    def getNumCells(self):
        pass
    
    #
    # Retrieves the charge phase or status.
    # Returns one of the STATE_xxx values to indicate the current charge status.
    # Raises RuntimeError in case the charge status cannot be determined.
    #
    def getChgStatus(self):
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

    #
    # Re-configures the instance according to the parameters provided.
    # As with the constructor, the only parameter is the configuration dictionary.
    #
    def configure(self, paramDict):
        pass
    
    #
    # Registers a notification Handler. The given handler routine will
    # be called everytime an interrupt occurs. Note that just one handling routine
    # may be registered. So consecutive calls of this function overwrite previous registrations.
    # The intMask parameter is a bitmask combined from the INT_xxx values to indicate,
    # which notifications are to be passed to the given handling routine. 
    # The given function should expect a single integer argument indicating the reason
    # for notification. This will be one of the INT_xxx values.
    # <<  def chargerHandler( intID )  >>
    #
    def registerIntHandler(self, intMask, func):
        self.intHandler = func
    
    #
    # Retrieves the bitmask of interrupts registered for notification.
    #
    def getIntMask(self):
        pass
    
    #
    # Sets the mask of interrupt reasons to fire the notification handler.
    #
    def setIntMask(self, intMask):
        pass
        
    #
    # Just enables one or more interrupts while leaving the others untouched.
    #
    def enableInt( self, intMask ):
        pass

    #
    # Disables one or more interrupts while leaving the others untouched.
    #
    def disableInt( self, intMask ):
        pass
    
    #
    # Gives the status of each interruptp condition, independently of whether
    # the condition is registered as a source of notification, or not.
    #
    def getIntStatus(self):
        pass
