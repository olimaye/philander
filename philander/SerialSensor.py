from SerialDevice import SerialDevice
from Sensor import Sensor

class SerialSensor( SerialDevice, Sensor ):

    def _scanParameters( self, paramDict ):
        SerialDevice._scanParameters( self, paramDict )
        if "Sensor.dataRange" in paramDict:
            self.dataRange = paramDict["Sensor.dataRange"]
        if "Sensor.dataRate" in paramDict:
            self.dataRate  = paramDict["Sensor.dataRate"]
    
    def _applyConfiguration( self ):
        SerialDevice._applyConfiguration( self )
        self.setRange( self.dataRange )
        self.setDataRate( self.dataRate )

    #
    # Initializes the sensor.
    # The only input parameter is a dictionary containing key-value pairs that
    # configure the instance. Key names and their meanings are:
    # Sensor.dataRange    : A value to describe the range.
    # Sensor.dataRate     : A value to set the frequency.
    def __init__( self, paramDict ):
        # Create instance attributes
        Sensor.__init__( self )
        if not ("Sensor.dataRange" in paramDict):
            paramDict["Sensor.dataRange"] = self.dataRange
        if not ("Sensor.dataRate" in paramDict):
            paramDict["Sensor.dataRate"] = self.dataRate
        SerialDevice.__init__( self, paramDict )

