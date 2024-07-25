"""Abstract interface for sub-systems connected via BlueTooth Low Energy (BLE).

Provide an API to abstract from any type of BLE subsystem.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Event", "ConnectionState", "BLE"]

import asyncio
from dataclasses import dataclass
from enum import Enum, unique, auto
import logging
from threading import Thread, Lock

from bleak import BleakClient, BleakScanner, BleakGATTCharacteristic
from bleak.exc import BleakDBusError

from .interruptable import Interruptable
from .module import Module
from .systypes import ErrorCode


@dataclass
class Event:
    """Data class to represent events, emitted by the BLE device.
    """
    bleDisconnected= "ble.disconnected"
    bleDiscovering = "ble.discovering"
    bleConnected   = "ble.connected"

@unique
class ConnectionState( Enum ):
    """Data class to represent BLE connection states
    """
    disconnected = auto()
    discovering  = auto()
    connected    = auto()
    

class BLE( Module, Interruptable ):
    """Implementation of an BLE device or subsystem.
    """

    DISCOVERY_TIMEOUT   = 5.0
    """Timeout for the discovery phase, given in seconds."""
    WRITE_NOTIFICATION_TIMEOUT  = 0.5
    """Timeout for a notification response after a GATT write, given in seconds.""" 
    
    
    def __init__( self ):
        # Initialize base class attributes
        super().__init__()
        # Create instance attributes
        defDict = {}
        BLE.Params_init(defDict)
        self.bleDiscoveryTimeout = defDict["BLE.discovery.timeout"]
        self.bleClientName = None
        self.bleCharacteristicUUID = None
        self._bleClient = None
        self._bleCharacteristic = None
        self._bleConnectionState = ConnectionState.disconnected
        self._connectionStateLock = Lock()
        self._notificationData = bytearray()
        self._notificationLock = Lock()
        self._writeLock = Lock()
        self._acceptNotificationLock = Lock()
        self._notificationReceivedLock = Lock()
        self._asyncError = ErrorCode.errOk
        self._evtLoop = asyncio.new_event_loop()
        self._evtEnabled = True
        self._worker = None

    @classmethod
    def Params_init( cls, paramDict ):
        """Initialize parameters with their defaults.
        
        The following settings are supported:
        
        =======================    ==========================================================================================================
        Key name                   Value type, meaning and default
        =======================    ==========================================================================================================
        BLE.discovery.timeout      ``int`` or ``float`` Timeout for the BLE discovery phase, given in seconds. :attr:`DISCOVERY_TIMEOUT`
        BLE.client.name            ``string`` Name of the client device to connect to, given as a string. No default.
        BLE.characteristic.uuid    ``string`` UUID of the client characteristic, given as a string. No default.
        =======================    ==========================================================================================================

        Also see: :meth:`.Module.Params_init`.
        
        :param dict(str, object) paramDict: The configuration dictionary.
        :returns: none
        :rtype: None
        """
        if not "BLE.discovery.timeout" in paramDict:
            paramDict["BLE.discovery.timeout"] = BLE.DISCOVERY_TIMEOUT
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
        val = paramDict.get("BLE.discovery.timeout", BLE.DISCOVERY_TIMEOUT )
        if not isinstance(val, int):
            try:
                val = float( val )
            except ValueError as e:
                val = BLE.DISCOVERY_TIMEOUT
                result = ErrorCode.errInvalidParameter
        if val < 0:
            val = BLE.DISCOVERY_TIMEOUT
        paramDict["BLE.discovery.timeout"] = val
        self.bleDiscoveryTimeout = val

        self.bleClientName = paramDict.get("BLE.client.name")
        if not self.bleClientName:
            result = ErrorCode.errInvalidParameter

        self.bleCharacteristicUUID = paramDict.get("BLE.characteristic.uuid")
        if not self.bleCharacteristicUUID:
            result = ErrorCode.errInvalidParameter
            
        if (self.isCoupled().isOk()):
            result = self.decouple()
        
        self._evtEnabled = True
        
        #self.couple()
        return result

    def close(self):
        """Shuts down the instance safely.

        Also see: :meth:`.Module.close`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        if (self.isCoupled().isOk()):
            result = self.decouple()
        elif self._worker:
            if self._worker.is_alive():
                self._worker.join()
            self._worker = None
        return result
    
    #
    # Interruptable API
    #
    
    def enableInterrupt(self):
        """Enables the interrupt(s) of the implementing device.

        :return: An error code indicating either success or the reason\
        of failure.
        :rtype: ErrorCode
        """
        self._evtEnabled = True
        return ErrorCode.errOk
    
    def disableInterrupt(self):
        """Disables the interrupt(s) of the implementing device.

        :return: An error code indicating either success or the reason\
        of failure.
        :rtype: ErrorCode
        """
        self._evtEnabled = False
        return ErrorCode.errOk
    
    def getEventContext(self, event, context):
        """Retrieves more detailed information on an interrupt / event.
        """
        return ErrorCode.errFewData
        
    #
    # Specific public API
    #
    
    def setDiscoveryTimeout( self, timeOut ):
        """Set the BLE discovery timeout.

        Discovery phase will definitely end, after the given time has elapsed.
        
        :param timeOut: The timeout, given in seconds.
        :type timeOut: int or float
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        self.bleDiscoveryTimeout = timeOut
        return ErrorCode.errOk
    
    def getConnectionState( self ):
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

        :return: An error code to indicate, if the remote device is coupled or not. 
        :rtype: ErrorCode
        """
        result = ErrorCode.errFailure
        with self._connectionStateLock:
            if (self._bleConnectionState == ConnectionState.connected):
                result = ErrorCode.errOk
            else:
                result = ErrorCode.errUnavailable
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
            self._worker = Thread( target=self._bleWorker, name='BLE coupling', args=(self._couplingRoutine(), ) )
            self._worker.start()
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

    def writeCharacteristic(self, data: bytearray, readResponse = False ):
        """Write data to the remote BLE characteristic.
        
        The instance must be coupled to a device, before using this
        function.
        The notification content is only valid if requested by ``readResponse=True``
        and the error code indicates a successful operation.
        
        :param bytearray data: The content to write to the characteristic.
        :param bool readResponse: Whether or not to read back the response notification.
        :return: A tuple of an error code indicating either success or the reason of failure and the notification data.
        :rtype: ErrorCode, bytearray
        """
        result = ErrorCode.errOk
        if (self._bleConnectionState == ConnectionState.connected):
            try:
                if self._evtLoop.is_running():
                    self._evtLoop.create_task( self._sendRoutine( data, readResponse ) )
                else:
                    self._evtLoop.run_until_complete( self._sendRoutine( data, readResponse ) )
                if readResponse:
                    result = self._asyncError
            except Exception as exc:
                logging.exception(exc)
                result = ErrorCode.errFailure
        else:
            result = ErrorCode.errUnavailable
        return result, self._notificationData
    
    #
    # Internal helper functions
    #
    

    def _setState(self, newState ):
        with self._connectionStateLock:
            self._bleConnectionState = newState
        self._emitState( newState )
        return None
        
    def _changeState( self, toState, fromState=None ):
        ret = False
        
        with self._connectionStateLock:
            if fromState is None:
                ret = (self._bleConnectionState != toState)
            else:
                ret = (self._bleConnectionState == fromState)
            if ret:
                self._bleConnectionState = toState

        if ret:
            self._emitState( toState )
        return ret
        
        
    def _emitState(self, newState):
        stateXevt = {
            ConnectionState.disconnected:  Event.bleDisconnected,
            ConnectionState.connected:     Event.bleConnected,
            ConnectionState.discovering:   Event.bleDiscovering,
        }
        if self._evtEnabled:
            evt = stateXevt.get( newState, Event.bleDisconnected )
            self._fire( evt )
        return None
        
    def _handleDisconnected( self, client ):
        self._setState( ConnectionState.disconnected )
        logging.info('Unsolicited disconnect: ' + client.address )
        return None
    
    async def _decouplingRoutine(self):
        """Close a BLE connection.
        
        Returns nothing, but emits the :attr:`.Event.bleDisconnected`
        event, as a side-effect.

        :return: None
        :rtype: None
        """
        if self._bleClient:
            try:
                await self._bleClient.disconnect()
                self._bleClient = None
            except Exception as exc:
                logging.warning( self._decouplingRoutine.__name__ + ' caught ' + type(exc).__name__ + ' ' + str(exc) )
        #self._setState( ConnectionState.disconnected )
        return None

    async def _couplingRoutine(self):
        """Establish a connection with the first available matching device.
        
        Do the BlueTooth coupling.
        Returns nothing, but executes the bleDiscovering,
        bleConnected or bleDisconnected events, as a side-effect.

        :return: None
        :rtype: None
        """
        # Discovering
        if self._changeState( ConnectionState.discovering ):
            try:
                device = await BleakScanner.find_device_by_name(
                                    name = self.bleClientName,
                                    timeout=self.bleDiscoveryTimeout )
                if device is None:
                    self._setState( ConnectionState.disconnected )
                else:
                    logging.info( self._couplingRoutine.__name__ + " found BLE device:" +
                                  " name=" + device.name +
                                  " address=" + device.address +
                                  " RSSI=" + str(device.details["props"]["RSSI"]) )
                    # Try to connect
                    self._bleClient = BleakClient( device, disconnected_callback=self._handleDisconnected )
                    success = await self._bleClient.connect()
                    if success:
                        logging.info( self._couplingRoutine.__name__ + " BLE connected." )
                        svcColl = self._bleClient.services
                        self._bleCharacteristic = svcColl.get_characteristic( self.bleCharacteristicUUID )
                        self._setState( ConnectionState.connected )
                    else:
                        logging.info( self._couplingRoutine.__name__ + " BLE could not connect." )
                        self._setState( ConnectionState.disconnected )
            except Exception as exc:
                logging.warning( self._couplingRoutine.__name__ + ' caught ' + type(exc).__name__ + ': ' + str(exc) )
                self._setState( ConnectionState.disconnected )
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

    def _handleNotification( self, sender: BleakGATTCharacteristic, data: bytearray):
        del sender
        with self._notificationLock:
            if self._acceptNotificationLock.locked():
                self._notificationData[:] = data
                try:
                    self._notificationReceivedLock.release()
                except RuntimeError as rte:
                    logging.debug( self._handleNotification.__name__ + ' caught ' + type(rte).__name__ + ': ' + str(rte) )
        return None
    

    async def _sendRoutine(self, cmdData, readResponse=False):
        with self._writeLock:
            if self._bleClient:
                try:
                    if readResponse:
                        flag = False
                        await self._bleClient.start_notify( self._bleCharacteristic, self._handleNotification )
                        with self._acceptNotificationLock:
                            self._notificationReceivedLock.acquire()
                            await self._bleClient.write_gatt_char( self._bleCharacteristic, cmdData, response=True )
                            flag = self._notificationReceivedLock.acquire(blocking=True, timeout=BLE.WRITE_NOTIFICATION_TIMEOUT)
                            await self._bleClient.stop_notify( self._bleCharacteristic )
                        try:
                            self._notificationReceivedLock.release()
                        except RuntimeError:
                            flag = not flag
                        finally:
                            if flag:
                                self._asyncError = ErrorCode.errOk
                            else:
                                self._asyncError = ErrorCode.errFewData
                    else:
                        await self._bleClient.write_gatt_char( self._bleCharacteristic, cmdData, response=True )
                except BleakDBusError as err: # In Progress
                    self._asyncError = ErrorCode.errFailure
                    logging.warning( self._sendRoutine.__name__ + ' caught ' + type(err).__name__ + ': ' + err.dbus_error_details )
                except Exception as exc:
                    self._asyncError = ErrorCode.errFailure
                    logging.warning( self._sendRoutine.__name__ + ' caught ' + type(exc).__name__ + ': ' + str(exc) )
        return None

