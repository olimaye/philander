# -*- coding: utf-8 -*-
"""A module to provide base classes and data types for the FastGait ActorUnit driver implementations.

In case of FOG, the ActorUnit is alerted via BlueTooth and starts
vibrating in pulses, giving the patient a haptic cueing impulse.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Event", "ConnectionState", "ActorUnit",]
from interruptable import Interruptable
from module import Module
from systypes import ErrorCode

from enum import auto, unique, Enum
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakDBusError
from threading import Thread, Lock
import asyncio
import logging

@unique
class Event( Enum ):
    """Data class to represent events, that the ActorUnit emits or handles.
    """
    cueStandard    = auto()
    cueStop        = auto()
    bleDiscovering = auto()
    bleConnected   = auto()
    bleDisconnected= auto()

    toStr = {
        bleDiscovering  : 'ActorUnit.discovering',
        bleConnected    : 'ActorUnit.connected',
        bleDisconnected : 'ActorUnit.disconnected',
    }
    
@unique
class ConnectionState( Enum ):
    """Data class to represent BLE connection states
    """
    disconnected = auto()
    discovering  = auto()
    connected    = auto()
    
    toStr = {
        disconnected : 'Disconnected',
        discovering  : 'Discovering',
        connected    : 'Connected',
    }
        
    
class ActorUnit( Module, Interruptable ):
    """Implementation of the vibration belt driver, also called ActorUnit.
    """

    #
    # Public attributes
    #
    
    MOTORS_1 = 1
    """First actuator"""
    MOTORS_2 = 2
    """Second actuator"""
    MOTORS_NONE = 0
    """Mnemonics for no actuator"""
    MOTORS_ALL  = MOTORS_1 | MOTORS_2
    """Mnemonics for all actuators"""
    
    
    #
    # Pulses are emitted periodically in rectangle form and the low-level
    # API allows to configure:
    #   - the length of one period,
    #   - the length of the on-part,
    #   - an initial delay and
    #   - the number of periods to run.
    #
    #            |< PULSE ON >|
    #            _____________       _____________       ______     ON
    # ...........|            |______|            |______|     ...  OFF
    #
    #|<  DELAY  >|<   PULSE PERIOD  >|
    #
    
    DELAY_DEFAULT           = 0     # immediately
    """Delay of the first pulse, given in milliseconds 0...65535 (0xFFFF). Zero (0) to start cueing immediately."""
    PULSE_PERIOD_DEFAULT    = 200  # ms
    """Pulse period in milliseconds 0...65535 (0xFFFF)."""
    PULSE_ON_DEFAULT        = 120   # ms; 60% duty cycle
    """Pulse ON duration in milliseconds 0...65535 (0xFFFF). Must be less than the period."""
    PULSE_COUNT_DEFAULT     = 3
    """Total number of pulses 0...255. Zero (0) means infinitely."""
    PULSE_INTENSITY_DEFAULT = 80    # 80% strength
    """Intensity of the ON phase vibration [0...100]."""
    ACTUATORS_DEFAULT       = MOTORS_ALL # All motors
    """Motor selection used for vibration [0...3]: Motors #1, or #2 or both."""

    # BLE defaults
    BLE_DEVICE_UUID         = '0000fa01-0000-1000-8000-00805f9b34fb'
    BLE_CHARACTERISTIC_UUID = '0000fa61-0000-1000-8000-00805f9b34fb'
    BLE_DISCOVERY_TIMEOUT   = 5.0   # in seconds
    
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
    # Module API
    #

    def __init__( self ):
        # Create instance attributes
        defDict = {}
        ActorUnit.Params_init(defDict)
        self.delay = defDict["ActorUnit.delay"]
        self.pulsePeriod = defDict["ActorUnit.pulsePeriod"]
        self.pulseOn = defDict["ActorUnit.pulseOn"]
        self.pulseCount = defDict["ActorUnit.pulseCount"]
        self.pulseIntensity = defDict["ActorUnit.pulseIntensity"]
        self.actuators = defDict["ActorUnit.actuators"]
        self.bleDiscoveryTimeout = defDict["ActorUnit.BLE.discovery.timeout"]
        self.cmdStart = bytearray([ActorUnit._CMD_START_DEFAULT])
        self.cmdStop = bytearray([ActorUnit._CMD_STOP])
        self._bleClient = 0
        self._bleChar = 0
        self._bleConnectionState = ConnectionState.disconnected
        self._bleLock = Lock()
        self._evtLoop = asyncio.new_event_loop()
        self._worker = None

    @classmethod
    def Params_init( cls, paramDict ):
        """Initialize parameters with their defaults.
        
        The following settings are supported:
        
        ===============================    ==========================================================================================================
        Key name                           Value type, meaning and default
        ===============================    ==========================================================================================================
        ActorUnit.delay                    ``int`` [0...65535] Initial delay in ms; :attr:`DELAY_DEFAULT`
        ActorUnit.pulsePeriod              ``int`` [0...65535] Length of one period in ms; :attr:`PULSE_PERIOD_DEFAULT`
        ActorUnit.pulseOn                  ``int`` [0...pulsePeriod] Length of the active part in that period in ms; :attr:`PULSE_ON_DEFAULT`
        ActorUnit.pulseCount               ``int`` [0...255] Number of pulses. Zero (0) means infinite pulses. :attr:`PULSE_COUNT_DEFAULT`
        ActorUnit.pulseIntensity           ``int`` [0...100] Intensity of the pulses given as a percentage %. :attr:`PULSE_INTENSITY_DEFAULT`
        ActorUnit.actuators                Motors to be used for the pulses [0...3] meaning none, left, right, both motors; :attr:`ACTUATORS_DEFAULT`
        ActorUnit.BLE.discovery.timeout    ``int`` or ``float`` Timeout for the BLE discovery phase, given in seconds. :attr:`BLE_DISCOVERY_TIMEOUT`
        ActorUnit.BLE.callback             Callback routine to be executed on the change of the BLE connection status. No default.
        ===============================    ==========================================================================================================

        Also see: :meth:`.Module.Params_init`.
        
        :param dict(str, object) paramDict: The configuration dictionary.
        :returns: none
        :rtype: None
        """
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
        return None
    
    def open( self, paramDict ):
        """Initialize an instance and prepare it for use.

        Also see: :meth:`.Module.open`.
        
        :param dict(str, object) paramDict: Configuration parameters as\
        possibly obtained from :meth:`Params_init`.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
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
        if "ActorUnit.BLE.callback" in paramDict:
            val = paramDict["ActorUnit.BLE.callback"]
            self.bleCallback = val
    
        # Create start-cueing-command buffer
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
        
        #self.couple()
        return result

    def close(self):
        """Shuts down the instance safely.

        Also see: :meth:`.Module.close`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        if self.isCoupled():
            self.decouple()
        elif self._worker:
            if self._worker.is_alive():
                self._worker.join()
            self._worker = None
    
    #
    # Interruptable API
    #
    
    def handleEvent(self, eventParam=None):
        """Event handling routine.

        Can be registered with event emmitters to be called, e.g. on
        cueing events.
        
        :param Event eventParam: An Event instance to tell what happened.
        :return: None
        :rtype: None
        """
        if eventParam is None:
            self.startCueing()
        elif eventParam == Event.cueStandard:
            self.startCueing()
        elif eventParam == Event.cueStop:
            self.stopCueing()
        return None
    
    #
    # Specific public API
    #
    
    def setBLEDiscoveryTimeout( self, timeOut ):
        """Set the BLE discovery timeout.

        Discovery phase will definitely end, after the given time has elapsed.
        
        :param timeOut: The timeout, given in seconds.
        :type timeOut: int or float
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        self.bleDiscoveryTimeout = timeOut
        return ErrorCode.errOk
    
    def getBLEConnectionState( self ):
        """Retrieve the current BLE connection state.
        
        :return: The current connection state.
        :rtype: ConnectionState
        """
        return self._bleConnectionState

    def isCoupled(self):
        """Tell the current coupling status of this instance.
        
        Informs the caller on whether or not the connection with the
        actuator unit has been established via BLE and is still intact.
        
        Returns :attr:`.ErrorCode.errOk` if the unit is coupled,
        :attr:`.ErrorCode.errUnavailable` if it is not coupled
        and any other value to indicate the reason, why this information
        could not be retrieved.

        :return: An error code.
        :rtype: ErrorCode
        """
        result = ErrorCode.errFailure
        self._bleLock.acquire()
        if (self._bleConnectionState == ConnectionState.connected):
            result = ErrorCode.errOk
        else:
            result = ErrorCode.errUnavailable
        self._bleLock.release()
        return result

    def couple(self):
        """Trigger the procedure to establish a BLE connection.
        
        Return quickly with a success-or-failure indicator for this
        triggering.
        Notice on the result of the coupling is given via subscription
        on the :attr:`Event.bleDiscovering` and
        :attr:`Event.bleConnected` event.

        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if self._bleConnectionState == ConnectionState.disconnected:
            self._worker = Thread( target=self._bleWorker, name='AU coupling', args=(self._couplingRoutine(), ) )
            self._worker.start()
            ret = True
        return ret
    
    
    def decouple(self):
        """Trigger the procedure to close a BLE connection.
        
        Return quickly with a success-or-failure indicator for this
        triggering, i.e. gives :attr:`.ErrorCode.errOk`, if the procedure
        launched, and a failure e.g. when the AU is not coupled.
        Notice on the result of the decoupling is given via
        subscription to the :attr:`Event.bleDisconnected` event.

        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if (self._bleConnectionState == ConnectionState.connected):
            try:
                self._evtLoop.run_until_complete( self._decouplingRoutine() )
            except Exception as exc:
                logging.exception(exc)
            ret = ErrorCode.errOk
        else:
            ret = ErrorCode.errInadequate
        return ret
    
    def startCueing(self):
        """Issue a start command to the actuator unit.

        Make the actor unit start cueing.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        if (self._bleConnectionState == ConnectionState.connected):
            try:
                if self._evtLoop.is_running():
                    self._evtLoop.create_task( self._sendRoutine( self.cmdStart ) )
                else:
                    self._evtLoop.run_until_complete( self._sendRoutine( self.cmdStart ) )
            except Exception as exc:
                logging.exception(exc)
            result = ErrorCode.errOk
        else:
            result = ErrorCode.errUnavailable
        return result
    
    def stopCueing(self):
        """Issue a stop command to the actuator unit.

        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        if (self._bleConnectionState == ConnectionState.connected):
            try:
                if self._evtLoop.is_running():
                    self._evtLoop.create_task( self._sendRoutine( self.cmdStop ) )
                else:
                    self._evtLoop.run_until_complete( self._sendRoutine( self.cmdStop ) )
            except Exception as exc:
                logging.exception(exc)
            result = ErrorCode.errOk
        else:
            result = ErrorCode.errUnavailable
        return result
    

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
            ConnectionState.disconnected:  Event.bleDisconnected,
            ConnectionState.connected:     Event.bleConnected,
            ConnectionState.discovering:   Event.bleDiscovering,
        }
        self.emit( stateXevt.get( newState, Event.bleDisconnected ) )
        
        
    def _handleDisconnected( self, client ):
        self._setState( ConnectionState.disconnected )
        logging.info('Unsolicited disconnect: ' + client.address )
    
    async def _couplingRoutine(self):
        """Establish a connection with the first available actuator unit.
        
        Do the BlueTooth coupling.
        Returns nothing, but executes the bleDiscovering,
        bleConnected or bleDisconnected events, as a side-effect.

        :return: None
        :rtype: None
        """
        # Discovering
        if self._changeState( ConnectionState.discovering ):
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
                        self._setState( ConnectionState.connected )
                    else:
                        self._setState( ConnectionState.disconnected )
                else:
                    self._setState( ConnectionState.disconnected )
            except Exception as exc:
                logging.warning( self._couplingRoutine.__name__ + ' caught ' + type(exc).__name__ + ' ' + str(exc) )
                self._setState( ConnectionState.disconnected )
        return None

    async def _decouplingRoutine(self):
        """Close a BLE connection.
        
        Returns nothing, but emits the :attr:`.Event.bleDisconnected`
        event, as a side-effect.

        :return: None
        :rtype: None
        """
        if self.bleClient:
            try:
                await self.bleClient.disconnect()
            except Exception as exc:
                logging.warning( self._decouplingRoutine.__name__ + ' caught ' + type(exc).__name__ + ' ' + str(exc) )
        self._setState( ConnectionState.disconnected )
        return None


    async def _sendRoutine(self, cmdData):
        try:
            await self.bleClient.write_gatt_char( self.bleChar, cmdData, response=True )
        except BleakDBusError as err: # In Progress
            logging.warning( self._sendRoutine.__name__ + ' caught ' + type(err).__name__ + ' ' + err.dbus_error_details )
        except Exception as exc:
            logging.warning( self._sendRoutine.__name__ + ' caught ' + type(exc).__name__ + ' ' + str(exc) )
        return None


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
        return None

