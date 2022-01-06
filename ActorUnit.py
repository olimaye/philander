from Configurable import Configurable
from EventHandler import EventHandler
#
# Implementation of the vibration belt driver, also called actor unit
#
class ActorUnit( Configurable, EventHandler ):

    #
    # Public attributes
    #
    
    MOTORS_1 = 1 # First actuator
    MOTORS_2 = 2 # Second actuator
    MOTORS_NONE = 0
    MOTORS_ALL  = MOTORS_1 | MOTORS_2
    
    
    #
    # Pulse are emitted periodically in rectangle form and the API allows
    # to configure: the length of one period, the length of the on-part
    # as well as an initial delay and the number of periods.
    #
    #            |< PULSE ON >|
    #            _____________       _____________       ______     ON
    # ...........|            |______|            |______|     ...  OFF
    #
    #|<  DELAY  >|<   PULSE PERIOD  >|
    #
    
    # Delay of the first pulse, given in milliseconds 0...65535 (0xFFFF). Zero (0) to startCueing immediately-
    DELAY_DEFAULT           = 0     # immediately
    # Pulse period in milliseconds 0...65535 (0xFFFF)
    PULSE_PERIOD_DEFAULT    = 1000  # ms
    # Pulse ON duration in milliseconds 0...65535 (0xFFFF). Must be less than the period.
    PULSE_ON_DEFAULT        = 600   # ms; 60% duty cycle
    # Total number of pulses 0...255. Zero (0) means infinitely.
    PULSE_COUNT_DEFAULT     = 3     #
    # Intensity of the ON phase vibration [0...100]
    PULSE_INTENSITY_DEFAULT = 80    # 80% strength
    # Motor selection used for vibration [0...3]: Motors #1, or #2 or both.
    ACTUATORS_DEFAULT       = MOTORS_ALL # All motors

    # Events
    EVT_CUE_STANDARD   = 1
    EVT_CUE_STOP       = 2
    
    #
    # Private attributes
    #
    
    _CMD_START   = 0x01
    _CMD_STOP    = 0x02
    _TIMER_KEEP  = 0x00
    _TIMER_RESET = 0x01
    
    #
    # Configurable API
    #

    #
    # Initializes the sensor.
    # The only input parameter is a dictionary containing key-value pairs that
    # configure the instance. Key names and their meanings are:
    # ActorUnit.delay         : Initial delay [0...65535]ms
    # ActorUnit.pulsePeriod   : Length of one period [0...65535]ms
    # ActorUnit.pulseOn       : Length of the active part in that period [0...pulsePeriod]ms
    # ActorUnit.pulseCount    : Number of pulses [0...255]. Zero (0) means infinite pulses.
    # ActorUnit.pulseIntensity: Intensity of the pulses [0...100]%
    # ActorUnit.actuators     : Motors to be used for the pulses [0...3] meaning none, left, right, both motors
    #
    def __init__( self, paramDict ):
        # Create instance attributes
        self.delay = ActorUnit.DELAY_DEFAULT
        self.pulsePeriod = ActorUnit.PULSE_PERIOD_DEFAULT
        self.pulseOn = ActorUnit.PULSE_ON_DEFAULT
        self.pulseCount = ActorUnit.PULSE_COUNT_DEFAULT
        self.pulseIntensity = ActorUnit.PULSE_INTENSITY_DEFAULT
        self.actuators = ActorUnit.ACTUATORS_DEFAULT
        self.cmdStart = bytearray(11)
        self.cmdStart[0] = ActorUnit._CMD_START
        self.cmdStop = bytearray([ActorUnit._CMD_STOP])
        # Set defaults
        if not "ActorUnit.delay" in paramDict:
            paramDict["ActorUnit.delay"] = ActorUnit.DELAY_DEFAULT
        if not "ActorUnit.pulsePeriod" in paramDict:
            paramDict["ActorUnit.pulsePeriod"] = ActorUnit.PULSE_PERIOD_DEFAULT
        if not "ActorUnit.pulseOn" in paramDict:
            paramDict["ActorUnit.pulseOn"] = ActorUnit.PULSE_ON_DEFAULT
        if not "ActorUnit.pulseCount" in paramDict:
            paramDict["ActorUnit.pulseCount"] = ActorUnit.PULSE_COUNT_DEFAULT
        if not "ActorUnit.pulseIntensity" in paramDict:
            paramDict["ActorUnit.pulseIntensity"] = ActorUnit.PULSE_INTENSITY_DEFAULT
        if not "ActorUnit.actuators" in paramDict:
            paramDict["ActorUnit.actuators"] = ActorUnit.ACTUATORS_DEFAULT
        Configurable.__init__( self, paramDict )
    
    #
    # Just scans the parameters for known keys and copies the values to
    # instance-local shadow variables.
    # Does not apply the new configuration.
    #
    def _scanParameters( self, paramDict ):
        if "ActorUnit.delay" in paramDict:
            val = paramDict["ActorUnit.delay"]
            if (val>=0) and (val<=0xFFFF):
                self.delay = val
        if "ActorUnit.pulsePeriod" in paramDict:
            val = paramDict["ActorUnit.pulsePeriod"]
            if (val>=0) and (val<=0xFFFF):
                self.pulsePeriod = val
        if "ActorUnit.pulseOn" in paramDict:
            val = paramDict["ActorUnit.pulseOn"]
            if (val>=0) and (val<=self.pulsePeriod):
                self.pulseOn = val
        if "ActorUnit.pulseCount" in paramDict:
            val = paramDict["ActorUnit.pulseCount"]
            if (val>=0) and (val<=0xFF):
                self.pulseCount = val
        if "ActorUnit.pulseIntensity" in paramDict:
            val = paramDict["ActorUnit.pulseIntensity"]
            if (val>=0) and (val<=100):
                self.pulseIntensity = val
        if "ActorUnit.actuators" in paramDict:
            val = paramDict["ActorUnit.actuators"]
            if (val>=ActorUnit.MOTORS_NONE) and (val<=ActorUnit.MOTORS_ALL):
                self.actuators = val
    
    #
    # Apply the new configuration.
    #
    def _applyConfiguration( self ):
        #self.cmdStart[0] = ActorUnit._CMD_START
        self.cmdStart[1] = self.pulseOn & 0xFF
        self.cmdStart[2] = self.pulseOn >> 8
        self.cmdStart[3] = self.pulsePeriod & 0xFF
        self.cmdStart[4] = self.pulsePeriod >> 8
        self.cmdStart[5] = self.delay & 0xFF
        self.cmdStart[6] = self.delay >> 8
        self.cmdStart[7] = self.pulseCount
        self.cmdStart[8] = self.pulseIntensity
        self.cmdStart[9] = self.actuators
        self.cmdStart[10] = ActorUnit._TIMER_RESET
        
    #
    # Initializes the instance. Must be called once, before the features of
    # this module can be used.
    #
    def init(self):
        Configurable.init(self)
        self.unitCouple()

    # 
    # Shuts down the instance safely.
    #
    def close(self):
        self.unitDecouple()
    
    #
    # EventHandler API
    #
    
    #
    # Event handling routine
    # Returns nothing.
    #
    def handleEvent(self, eventParam=None):
        if eventParam is None:
            self.startCueing()
        elif eventParam == ActorUnit.EVT_CUE_STOP:
            self.stopCueing()
        else:
            self.startCueing()
            
    
    #
    # Specific private API
    #
    
    #
    # Establishes a connection with the first available actuator unit,
    # i.e. does the BlueTooth coupling
    # Returns a boolean success-or-failure indicator.
    #
    def unitCouple(self):
        pass
    
    #
    # Decouples from the actuator unit.
    # Returns nothing
    #
    def unitDecouple(self):
        pass
    
    #
    # Informs the caller on whether or not the connection with the
    # actuator unit has been established and is still intact.
    # Returns a boolean success-or-failure indicator.
    # 
    def unitIsCoupled(self):
        return False

    #
    # Issues a start command to the actuator unit.
    #    
    def startCueing(self):
        print('Vibration START:', self.cmdStart)
    
    #
    # Issues a stop command to the actuator unit.
    #
    def stopCueing(self):
        print('Vibration STOP.')
    
    