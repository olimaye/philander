class FuelGauge():
    
    CAP_LVL_MIN    = 0
    CAP_LVL_DEEP_DISCHARGE = CAP_LVL_MIN
    CAP_LVL_EMPTY  = 5
    CAP_LVL_LOW    = 10
    CAP_LVL_MEDIUM = 30
    CAP_LVL_GOOD   = 70
    CAP_LVL_FULL   = 90
    CAP_LVL_MAX    = 100
    
    capLevel2Str = {
        CAP_LVL_DEEP_DISCHARGE : 'Deep Discharge',
        CAP_LVL_EMPTY  : 'empty',
        CAP_LVL_LOW    : 'low',
        CAP_LVL_MEDIUM : 'medium',
        CAP_LVL_GOOD   : 'good',
        CAP_LVL_FULL   : 'full',
    }
    
    #
    # Retrieves the remaining capacity as a continous
    # value in [0, ..., 100].
    #
    def getRemainingCapacity( self ):
        pass
    
    #
    # Converts a capacity value into its level predicate.
    # Does not retrieve any information from the underlying
    # hardware.
    #
    def cap2level( self, capacity ):
        ret = FuelGauge.CAP_LVL_MEDIUM
        if capacity >= FuelGauge.CAP_LVL_FULL:
            ret = FuelGauge.CAP_LVL_FULL
        elif capacity >= FuelGauge.CAP_LVL_GOOD:
            ret = FuelGauge.CAP_LVL_GOOD
        elif capacity >= FuelGauge.CAP_LVL_MEDIUM:
            ret = FuelGauge.CAP_LVL_MEDIUM
        elif capacity >= FuelGauge.CAP_LVL_LOW:
            ret = FuelGauge.CAP_LVL_LOW
        elif capacity >= FuelGauge.CAP_LVL_EMPTY:
            ret = FuelGauge.CAP_LVL_EMPTY
        else:
            ret = FuelGauge.CAP_LVL_DEEP_DISCHARGE
        return ret
    
    #
    # Retrieves the remaining capacity as a discrete
    # level predicate, expressed as one of the
    # CAP_LVL_xxx values.
    #
    def getRemainingCapacityLevel( self ):
        val = self.getRemainingCapacity()
        lvl = self.cap2level( val )
        return lvl
    
    #
    # Retrieves the remaining capacity as a level string.
    #
    def getRemainingCapacityStr( self ):
        lvl = self.getRemainingCapacityLevel()
        lvlStr = FuelGauge.capLevel2Str.get( lvl, 'unknown' )
        return lvlStr

