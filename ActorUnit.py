from Configurable import Configurable
from EventHandler import EventHandler
from pymitter import EventEmitter

from bleak import BleakClient, BleakScanner, BleakError
from bleak.exc import BleakDBusError
from threading import Thread, Lock
import asyncio
import logging


#
# Implementation of the vibration belt driver, also called actor unit
#
class ActorUnit( Configurable, EventHandler, EventEmitter ):

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
    PULSE_PERIOD_DEFAULT    = 200  # ms
    # Pulse ON duration in milliseconds 0...65535 (0xFFFF). Must be less than the period.
    PULSE_ON_DEFAULT        = 120   # ms; 60% duty cycle
    # Total number of pulses 0...255. Zero (0) means infinitely.
    PULSE_COUNT_DEFAULT     = 3     #
    # Intensity of the ON phase vibration [0...100]
    PULSE_INTENSITY_DEFAULT = 80    # 80% strength
    # Motor selection used for vibration [0...3]: Motors #1, or #2 or both.
    ACTUATORS_DEFAULT       = MOTORS_ALL # All motors

    # BLE defaults
    BLE_DEVICE_UUID         = '0000fa01-0000-1000-8000-00805f9b34fb'
    BLE_CHARACTERISTIC_UUID = '0000fa61-0000-1000-8000-00805f9b34fb'
    BLE_DISCOVERY_TIMEOUT   = 5.0
    
    # BLE Connection states
    BLE_CONN_STATE_DISCONNECTED = 0
    BLE_CONN_STATE_DISCOVERING  = 1
    BLE_CONN_STATE_CONNECTED    = 2
    
    connState2Str = {
        BLE_CONN_STATE_DISCONNECTED : 'Disconnected',
        BLE_CONN_STATE_DISCOVERING  : 'Discovering',
        BLE_CONN_STATE_CONNECTED    : 'Connected',
    }
    
    # Events
    EVT_CUE_STANDARD   = 1
    EVT_CUE_STOP       = 2
    EVT_BLE_DISCOVERING = "ActorUnit.discovering"
    EVT_BLE_CONNECTED   = "ActorUnit.connected"
    EVT_BLE_DISCONNECTED= "ActorUnit.disconnected"
    
    #
    # Private attributes
    #
    
    _CMD_START         = 0x01
    _CMD_STOP          = 0x02
    _CMD_SET_DEFAULT   = 0x03
    _CMD_GET_DEFAULT   = 0x04
    _CMD_START_DEFAULT = 0x05
    
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
    # ActorUnit.BLE.discovery.timeout: Timeout for the BLE discovery phase, given in seconds.
    # ActorUnit.BLE.callback  : Callback routine to be executed on the change of the BLE connection status.
    #
    def __init__( self, paramDict ):
        # Create instance attributes
        self.delay = ActorUnit.DELAY_DEFAULT
        self.pulsePeriod = ActorUnit.PULSE_PERIOD_DEFAULT
        self.pulseOn = ActorUnit.PULSE_ON_DEFAULT
        self.pulseCount = ActorUnit.PULSE_COUNT_DEFAULT
        self.pulseIntensity = ActorUnit.PULSE_INTENSITY_DEFAULT
        self.actuators = ActorUnit.ACTUATORS_DEFAULT
        self.cmdStart = bytearray([ActorUnit._CMD_START_DEFAULT])
        self.cmdStop = bytearray([ActorUnit._CMD_STOP])
        self.bleDiscoveryTimeout = ActorUnit.BLE_DISCOVERY_TIMEOUT
        self._bleClient = 0
        self._bleChar = 0
        self._bleConnectionState = ActorUnit.BLE_CONN_STATE_DISCONNECTED
        self._bleLock = Lock()
        self._evtLoop = asyncio.new_event_loop()
        self._worker = None
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
        if not "ActorUnit.BLE.discovery.timeout" in paramDict:
            paramDict["ActorUnit.BLE.discovery.timeout"] = ActorUnit.BLE_DISCOVERY_TIMEOUT
        Configurable.__init__( self, paramDict )
        EventEmitter.__init__( self, wildcard=True )
    
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
        if "ActorUnit.BLE.discovery.timeout" in paramDict:
            val = paramDict["ActorUnit.BLE.discovery.timeout"]
            if val>=0:
                self.bleDiscoveryTimeout = val
    
    #
    # Apply the new configuration.
    #
    def _applyConfiguration( self ):
        # self.cmdStart[0] = ActorUnit._CMD_START
        # self.cmdStart[1] = self.pulseOn & 0xFF
        # self.cmdStart[2] = self.pulseOn >> 8
        # self.cmdStart[3] = self.pulsePeriod & 0xFF
        # self.cmdStart[4] = self.pulsePeriod >> 8
        # self.cmdStart[5] = self.delay & 0xFF
        # self.cmdStart[6] = self.delay >> 8
        # self.cmdStart[7] = self.pulseCount
        # self.cmdStart[8] = self.pulseIntensity
        # self.cmdStart[9] = self.actuators
        # self.cmdStart[10] = ActorUnit._TIMER_RESET
        pass
        
    #
    # Initializes the instance. Must be called once, before the features of
    # this module can be used.
    #
    def init(self):
        Configurable.init(self)
        self.couple()

    # 
    # Shuts down the instance safely.
    #
    def close(self):
        if self.isCoupled():
            self.decouple()
        elif self._worker:
            if self._worker.is_alive():
                self._worker.join()
            self._worker = None
    
    #
    # EventHandler API
    #
    
    #
    # Event handling routine.
    # Input: One of the EVT_CUE_xxx event identifiers.
    # Returns nothing.
    #
    def handleEvent(self, eventParam=None):
        if eventParam is None:
            self.startCueing()
        elif eventParam == ActorUnit.EVT_CUE_STANDARD:
            self.startCueing()
        elif eventParam == ActorUnit.EVT_CUE_STOP:
            self.stopCueing()
            
    
    #
    # Specific private API
    #
    
    #
    # Sets the BLE discovery timout, given in seconds.
    #
    def setBLEDiscoveryTimeout( self, to ):
        self.bleDiscoveryTimeout = to
    
    #
    # Retrieves the current BLE connection state, which
    # is one of ActorUnit.BLE_CONN_STATE_xxx values.
    #
    def getBLEConnectionState( self ):
        return self._bleConnectionState

    #
    # Informs the caller on whether or not the connection with the
    # actuator unit has been established and is still intact.
    # Returns a boolean success-or-failure indicator.
    # 
    def isCoupled(self):
        self._bleLock.acquire()
        ret = (self._bleConnectionState == ActorUnit.BLE_CONN_STATE_CONNECTED)
        self._bleLock.release()
        return ret

    #
    # Triggers the procedure to establish a BLE connection.
    # Returns a success-or-failure indicator for this triggering,
    # i.e. gives True, if the procedure launched, and False e.g.
    # when it is already running.
    # Notice on the result of the coupling is given via subscription
    # on the EVT_BLE_DISCOVERING and EVT_BLE_CONNECTED event.
    #
    def couple(self):
        ret = False
        if self._bleConnectionState == ActorUnit.BLE_CONN_STATE_DISCONNECTED:
            self._worker = Thread( target=self._bleWorker, name='AU coupling', args=(self._couplingRoutine(), ) )
            self._worker.start()
            ret = True
        return ret
    
    
    #
    # Triggers the procedure to close a BLE connection.
    # Returns a success-or-failure indicator for this triggering,
    # i.e. gives True, if the procedure launched, and False e.g.
    # when the AU is not coupled.
    # Notice on the result of the decoupling is given via
    # subscription to the EVT_BLE_DISCONNECTED event.
    #
    def decouple(self):
        ret = False
        if self._bleConnectionState == ActorUnit.BLE_CONN_STATE_CONNECTED:
            try:
                self._evtLoop.run_until_complete( self._decouplingRoutine() )
            except Exception as exc:
                logging.exception(exc)
            ret = True
        return ret
    
    #
    # Issues a start command to the actuator unit.
    #    
    def startCueing(self):
        if self._bleConnectionState == ActorUnit.BLE_CONN_STATE_CONNECTED:
            try:
                if self._evtLoop.is_running():
                    self._evtLoop.create_task( self._sendRoutine( self.cmdStart ) )
                else:
                    self._evtLoop.run_until_complete( self._sendRoutine( self.cmdStart ) )
            except Exception as exc:
                logging.exception(exc)
                
    
    #
    # Issues a stop command to the actuator unit.
    #
    def stopCueing(self):
        if self._bleConnectionState == ActorUnit.BLE_CONN_STATE_CONNECTED:
            try:
                if self._evtLoop.is_running():
                    self._evtLoop.create_task( self._sendRoutine( self.cmdStop ) )
                else:
                    self._evtLoop.run_until_complete( self._sendRoutine( self.cmdStop ) )
            except Exception as exc:
                logging.exception(exc)
    

    #
    # Internal helper functions
    #
    

    def _setState(self, newState ):
        self._bleLock.acquire()
        self._bleConnectionState = newState
        self._bleLock.release()
        self._emitState( newState )
        
        
    def _changeState( self, toState, fromState=None ):
        ret = False
        
        self._bleLock.acquire()
        if fromState is None:
            ret = (self._bleConnectionState != toState)
        else:
            ret = (self._bleConnectionState == fromState)
        if ret:
            self._bleConnectionState = toState
        self._bleLock.release()

        if ret:
            self._emitState( toState )
        return ret
        
        
    def _emitState(self, newState):
        stateXevt = {
            ActorUnit.BLE_CONN_STATE_DISCONNECTED:  ActorUnit.EVT_BLE_DISCONNECTED,
            ActorUnit.BLE_CONN_STATE_CONNECTED:     ActorUnit.EVT_BLE_CONNECTED,
            ActorUnit.BLE_CONN_STATE_DISCOVERING:   ActorUnit.EVT_BLE_DISCOVERING,
        }
        self.emit( stateXevt.get( newState, ActorUnit.EVT_BLE_DISCONNECTED ) )
        
        
    def _handleDisconnected( self, client ):
        self._setState( ActorUnit.BLE_CONN_STATE_DISCONNECTED )
    
    
    #
    # Establishes a connection with the first available actuator unit,
    # i.e. does the BlueTooth coupling
    # Returns nothing, but executes the EVT_BLE_DISCOVERING,
    # EVT_BLE_CONNECTED or EVT_BLE_DISCONNECTED events, as a side-effect.
    #
    async def _couplingRoutine(self):
        # Discovering
        if self._changeState( ActorUnit.BLE_CONN_STATE_DISCOVERING ):
            try:
                devices = await BleakScanner.discover( timeout=self.bleDiscoveryTimeout, filters={'UUIDs': [ActorUnit.BLE_DEVICE_UUID]} )
                if devices:
                    # Try to connect
                    self.bleClient = BleakClient( devices[0] )
                    self.bleClient.set_disconnected_callback( self._handleDisconnected )
                    success = await self.bleClient.connect()
                    if success:
                        svcColl = await self.bleClient.get_services()
                        self.bleChar = svcColl.get_characteristic( ActorUnit.BLE_CHARACTERISTIC_UUID )
                        self._setState( ActorUnit.BLE_CONN_STATE_CONNECTED )
                    else:
                        self._setState( ActorUnit.BLE_CONN_STATE_DISCONNECTED )
                else:
                    self._setState( ActorUnit.BLE_CONN_STATE_DISCONNECTED )
            except Exception as exc:
                logging.warning( self._couplingRoutine.__name__ + ' caught ' + type(exc).__name__ + ' ' + str(exc) )
                self._setState( ActorUnit.BLE_CONN_STATE_DISCONNECTED )

    #
    # Closes a BLE connection.
    # Returns nothing, but emits the EVT_BLE_DISCONNECTED event, as a side-effect.
    #
    async def _decouplingRoutine(self):
        if self.bleClient:
            try:
                await self.bleClient.disconnect()
            except Exception as exc:
                logging.warning( self._decouplingRoutine.__name__ + ' caught ' + type(exc).__name__ + ' ' + str(exc) )
        self._setState( ActorUnit.BLE_CONN_STATE_DISCONNECTED )


    async def _sendRoutine(self, cmdData):
        try:
            await self.bleClient.write_gatt_char( self.bleChar, cmdData, response=True )
        except BleakDBusError as err: # In Progress
            logging.warning( self._sendRoutine.__name__ + ' caught ' + type(err).__name__ + ' ' + err.dbus_error_details )
        except Exception as exc:
            logging.warning( self._sendRoutine.__name__ + ' caught ' + type(exc).__name__ + ' ' + str(exc) )


    def _bleWorker( self, routine ):
        try:
            if self._evtLoop.is_closed():
                pass
            elif self._evtLoop.is_running():
                self._evtLoop.create_task( routine )
            else:
                self._evtLoop.run_until_complete( routine )
        except Exception as exc:
                logging.exception(exc)

