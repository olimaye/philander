class Configurable:

    #
    # Just scans the parameters for known keys and copies the values to
    # instance-local shadow variables.
    # Does not apply the new configuration.
    #
    def _scanParameters( self, paramDict ):
        pass
    
    #
    # Apply the new configuration.
    #
    def _applyConfiguration( self ):
        pass
    
    #
    # Initializes the object.
    # The only input parameter is a dictionary containing key-value pairs that
    # configure the instance. 
    # 
    def __init__( self, paramDict ):
        # Scan the parameters dictionary
        self._scanParameters( paramDict )

    #
    # Initializes the instance. Must be called once, before the features of
    # this module can be used.
    #
    def init(self):
        self._applyConfiguration()

    #
    # Configures the instance.
    #
    def configure( self, paramDict ):
        self._scanParameters( paramDict )
        self._applyConfiguration()
    
    # 
    # Shuts down the instance safely.
    #
    def close(self):
        pass

    