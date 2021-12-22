from Configurable import Configurable

class Sensor( Configurable ):

    def _scanParameters( self, paramDict ):
        if "Sensor.dataRange" in paramDict:
            self.dataRange = paramDict["Sensor.dataRange"]
        if "Sensor.dataRate" in paramDict:
            self.dataRate  = paramDict["Sensor.dataRate"]
    
    def _applyConfiguration( self ):
        self.setRange( self.dataRange )
        self.setDataRate( self.dataRate )

    #
    # Initializes the sensor.
    # The only input parameter is a dictionary containing key-value pairs that
    # configure the instance. Key names and their meanings are:
    # Sensor.dataRange    : A value to describe the range.
    # Sensor.dataRate     : A value to set the frequency.
    def __init__( self, paramDict ):
        # Set defaults
        self.dataRange = 1
        self.dataRate = 0
        Configurable.__init__( self, paramDict )

 
    #
    # Soft resets the sensor. The device is in some default state, afterwards and
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
    # Retrieves the next data, possibly waiting (blocking) depending on the
    # data rate configured.
    # Always returns with fresh, new data, never read before.
    #
    def nextData(self):
        pass

    #
    # Retrieves the most recent data available and returns immediately.
    # This function will never block, but may read data that has been
    # read before.
    #
    def lastData(self):
        pass

    #
    # Configures the data range.
    # newRange: The new range to set.
    #
    def setRange( self, newRange ):
        self.dataRange = newRange

    #
    # Configures the data update rate.
    # newRate: The new data rate.
    #
    def setDataRate( self, newRate ):
        self.dataRate = newRate
