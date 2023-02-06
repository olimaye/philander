class AnalogueVoltmeter( Configurable, FuelGauge ):
    
    #
    # Configurable API
    #

    #
    # Initializes the sensor.
    # The only input parameter is a dictionary containing key-value pairs that
    # configure the instance. Key names and their meanings are:
    # AnalogueVoltmeter.ADC.pin   : Pin of the ADC, such as 17, 'GPIO17' or 'BOARD11'
    # AnalogueVoltmeter.range.max : Maximum voltage in mV, mapped to 100%
    # AnalogueVoltmeter.range.min : Minimum voltage in mV, mapped to 0%
    # 
    def __init__( self, paramDict ):
        # Create instance attributes
        self._rangeMin = 2500
        self._rangeMax = 3300
        self._adcPin = None
        # Set defaults
        if not "AnalogueVoltmeter.ADC.pin" in paramDict:
            paramDict["AnalogueVoltmeter.ADC.pin"] = None
        if not "AnalogueVoltmeter.range.max" in paramDict:
            paramDict["AnalogueVoltmeter.range.max"] = self._rangeMax
        if not "AnalogueVoltmeter.range.min" in paramDict:
            paramDict["AnalogueVoltmeter.range.min"] = self._rangeMin
        super().__init__( paramDict )

    #
    # Just scans the parameters for known keys and copies the values to
    # instance-local shadow variables.
    # Does not apply the new configuration.
    #
    def _scanParameters( self, paramDict ):
        if "AnalogueVoltmeter.ADC.pin" in paramDict:
            self._adcPin = paramDict["AnalogueVoltmeter.ADC.pin"]
        if "AnalogueVoltmeter.range.max" in paramDict:
            self._rangeMax = paramDict["AnalogueVoltmeter.range.max"]
        if "AnalogueVoltmeter.range.min" in paramDict:
            self._rangeMin = paramDict["AnalogueVoltmeter.range.min"]
    
    #
    # Initializes the instance. Must be called once, before the features of
    # this module can be used.
    #
    def init(self):
        super().init()
        # Code initialize the ADC interface
    
    # 
    # Shuts down the instance safely.
    #
    def close(self):
        pass

 
    
    #
    # FuelGauge API
    #
    
    #
    # Retrieves the remaining capacity as a continous
    # value in [0, ..., 100].
    #
    def getRemainingCapacity( self ):
        # Guess a dummy value, replace with serious code!
        return 50
    
    
    