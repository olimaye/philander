from pymitter import EventEmitter
from threading import Thread, Lock
from Configurable import Configurable
from MAX77960 import MAX77960 as Charger
from BatteryCharger import BatteryCharger
from ActorUnit import ActorUnit
from SmartButton import SmartButton
from SmartLED import SmartLED

import time, logging

# The fastGait power management and user interface
class FGSystemManagement( Configurable, EventEmitter ):
    
    #
    # Public class attributes
    #
    EVT_DELIMITER           = '.'
    EVT_MASK                = 'SystemManagement'
    EVT_BLE_CONNECTED       = EVT_MASK + EVT_DELIMITER + 'ble' + EVT_DELIMITER + 'connected'
    EVT_BLE_DISCONNECTED    = EVT_MASK + EVT_DELIMITER + 'ble' + EVT_DELIMITER + 'disconnected'
    EVT_DC_PLUGGED          = EVT_MASK + EVT_DELIMITER + 'dc' + EVT_DELIMITER + 'plugged'
    EVT_DC_UNPLUGGED        = EVT_MASK + EVT_DELIMITER + 'dc' + EVT_DELIMITER + 'unplugged'
    EVT_BUTTON_PRESSED      = EVT_MASK + EVT_DELIMITER + 'ui' + EVT_DELIMITER + 'button' + EVT_DELIMITER + 'pressed'
    EVT_TEMP_CRITICAL       = EVT_MASK + EVT_DELIMITER + 'temp' + EVT_DELIMITER + 'critical'
    EVT_TEMP_NORMAL         = EVT_MASK + EVT_DELIMITER + 'temp' + EVT_DELIMITER + 'normal'
    
    
    #
    # Private class attributes
    #
    
    #_INFOCAT_AUX       = 2
    _INFOCAT_TEMP      = 3
    _INFOCAT_BAT_STATE = 4
    _INFOCAT_BLE       = 5
    _INFOCAT_DC_SUPPLY = 6
    _INFOCAT_CHG_STATE = 7
    
    _SYSJOB_NONE      = 0x00
    _SYSJOB_AU_COUPLE = 0x01
    _SYSJOB_ANY       = 0xFFFF
    
    _CRITICAL_TEMPERATURES = (BatteryCharger.TEMP_COLD, BatteryCharger.TEMP_HOT)
    
    #
    # The Configurable API
    #
    
    #
    # Initializes the sensor.
    # The only input parameter is a dictionary containing key-value pairs that
    # configure the instance. Key names and their meanings are:
    # UI.LED.tmp.pin         : Pin of the temperature LED, such as 17 or 'GPIO17'
    # UI.LED.tmp.activeHigh  : True, if high-state makes the LED shine, False otherwise
    # UI.LED.bat.pin         : Pin of the battery status LED
    # UI.LED.bat.activeHigh  : True, if high-state makes the LED shine, False otherwise
    # UI.LED.ble.pin         : Pin of the BLE connection status LED
    # UI.LED.ble.activeHigh  : True, if high-state makes the LED shine, False otherwise
    # UI.LED.dc.pin          : Pin of the DC supply status LED
    # UI.LED.dc.activeHigh   : True, if high-state makes the LED shine, False otherwise
    # UI.LED.chg.pin         : Pin of the charger status LED
    # UI.LED.chg.activeHigh  : True, if high-state makes the LED shine, False otherwise
    #
    def __init__(self, paramDict):
        # Create instance attributes
        self._systemJob = FGSystemManagement._SYSJOB_NONE
        self._sysjobLock = Lock()
        self.done = False
        self.charger = Charger( paramDict )
        self.actorUnit = ActorUnit( paramDict )
        self.tmpLED = None
        self._tmpLEDpin = None
        self._tmpLEDactHi = True
        self.batLED = None
        self._batLEDpin = None
        self._batLEDactHi = True
        self.bleLED = None
        self._bleLEDpin = None
        self._bleLEDactHi = True
        self.dcLED = None
        self._dcLEDpin = None
        self._dcLEDactHi = True
        self.chgLED = None
        self._chgLEDpin = None
        self._chgLEDactHi = True
        self.aux0LED = None
        self._aux0LEDpin = None
        self._aux0LEDactHi = True
        self.aux1LED = None
        self._aux1LEDpin = None
        self._aux1LEDactHi = True
        self.cmdBtn = None
        self._cmdBtnPin = None
        self._cmdBtnActHi = True
        self.monitor = Thread( target=self.manageSystem, name='System Management' )
        # Set defaults
        if not "UI.LED.tmp.pin" in paramDict:
            paramDict["UI.LED.tmp.pin"] = None
        if not "UI.LED.tmp.activeHigh" in paramDict:
            paramDict["UI.LED.tmp.activeHigh"] = True
        if not "UI.LED.bat.pin" in paramDict:
            paramDict["UI.LED.bat.pin"] = None
        if not "UI.LED.bat.activeHigh" in paramDict:
            paramDict["UI.LED.bat.activeHigh"] = True
        if not "UI.LED.ble.pin" in paramDict:
            paramDict["UI.LED.ble.pin"] = None
        if not "UI.LED.ble.activeHigh" in paramDict:
            paramDict["UI.LED.ble.activeHigh"] = True
        if not "UI.LED.dc.pin" in paramDict:
            paramDict["UI.LED.dc.pin"] = None
        if not "UI.LED.dc.activeHigh" in paramDict:
            paramDict["UI.LED.dc.activeHigh"] = True
        if not "UI.LED.chg.pin" in paramDict:
            paramDict["UI.LED.chg.pin"] = None
        if not "UI.LED.chg.activeHigh" in paramDict:
            paramDict["UI.LED.chg.activeHigh"] = True
        if not "UI.LED.0.pin" in paramDict:
            paramDict["UI.LED.0.pin"] = None
        if not "UI.LED.0.activeHigh" in paramDict:
            paramDict["UI.LED.0.activeHigh"] = True
        if not "UI.LED.1.pin" in paramDict:
            paramDict["UI.LED.1.pin"] = None
        if not "UI.LED.1.activeHigh" in paramDict:
            paramDict["UI.LED.1.activeHigh"] = True
        if not "UI.Button.cmd.pin" in paramDict:
            paramDict["UI.Button.cmd.pin"] = None
        if not "UI.Button.cmd.activeHigh" in paramDict:
            paramDict["UI.Button.cmd.activeHigh"] = True
        Configurable.__init__( self, paramDict )
        EventEmitter.__init__( self, wildcard=True, delimiter=FGSystemManagement.EVT_DELIMITER)

    #
    # Scans the parameters for known keys.
    #
    def _scanParameters( self, paramDict ):
        if "UI.LED.tmp.pin" in paramDict:
            self._tmpLEDpin = paramDict["UI.LED.tmp.pin"]
        if "UI.LED.tmp.activeHigh" in paramDict:
            self._tmpLEDactHi = paramDict["UI.LED.tmp.activeHigh"]
        if "UI.LED.bat.pin" in paramDict:
            self._batLEDpin = paramDict["UI.LED.bat.pin"]
        if "UI.LED.bat.activeHigh" in paramDict:
            self._batLEDactHi = paramDict["UI.LED.bat.activeHigh"]
        if "UI.LED.ble.pin" in paramDict:
            self._bleLEDpin = paramDict["UI.LED.ble.pin"]
        if "UI.LED.ble.activeHigh" in paramDict:
            self._bleLEDactHi = paramDict["UI.LED.ble.activeHigh"]
        if "UI.LED.dc.pin" in paramDict:
            self._dcLEDpin = paramDict["UI.LED.dc.pin"]
        if "UI.LED.dc.activeHigh" in paramDict:
            self._dcLEDactHi = paramDict["UI.LED.dc.activeHigh"]
        if "UI.LED.chg.pin" in paramDict:
            self._chgLEDpin = paramDict["UI.LED.chg.pin"]
        if "UI.LED.chg.activeHigh" in paramDict:
            self._chgLEDactHi = paramDict["UI.LED.chg.activeHigh"]
        if "UI.LED.0.pin" in paramDict:
            self._aux0LEDpin = paramDict["UI.LED.0.pin"]
        if "UI.LED.0.activeHigh" in paramDict:
            self._aux0LEDactHi = paramDict["UI.LED.0.activeHigh"]
        if "UI.LED.1.pin" in paramDict:
            self._aux1LEDpin = paramDict["UI.LED.1.pin"]
        if "UI.LED.1.activeHigh" in paramDict:
            self._aux1LEDactHi = paramDict["UI.LED.1.activeHigh"]
        if "UI.Button.cmd.pin" in paramDict:
            self._cmdBtnPin = paramDict["UI.Button.cmd.pin"]
        if "UI.Button.cmd.activeHigh" in paramDict:
            self._cmdBtnActHi = paramDict["UI.Button.cmd.activeHigh"]
                
    #
    # Apply the new configuration.
    #
    #def _applyConfiguration( self ):

    #
    # Initializes the instance. Must be called once, before the features of
    # this module can be used.
    #
    def init(self):
        self.charger.init()
        super().init()
        if self._tmpLEDpin:
            self.tmpLED = SmartLED( pin=self._tmpLEDpin, active_high=self._tmpLEDactHi )
        if self._batLEDpin:
            self.batLED = SmartLED( pin=self._batLEDpin, active_high=self._batLEDactHi )
        if self._bleLEDpin:
            self.bleLED = SmartLED( pin=self._bleLEDpin, active_high=self._bleLEDactHi )
        if self._dcLEDpin:
            self.dcLED = SmartLED( pin=self._dcLEDpin, active_high=self._dcLEDactHi )
        if self._chgLEDpin:
            self.chgLED = SmartLED( pin=self._chgLEDpin, active_high=self._chgLEDactHi )
        if self._aux0LEDpin:
            self.aux0LED = SmartLED( pin=self._aux0LEDpin, active_high=self._aux0LEDactHi )
        if self._aux1LEDpin:
            self.aux1LED = SmartLED( pin=self._aux1LEDpin, active_high=self._aux1LEDactHi )
        if self._cmdBtnPin:
            btnName = 'ButtonCMD'
            self.cmdBtn = SmartButton( pin=self._cmdBtnPin, active_high=self._cmdBtnActHi, label=btnName )
            self.cmdBtn.on( btnName, func=self.uiHandleButtonPressed )
            self.cmdBtn.asyncWait4Press()
        self.monitor.start()
        self.actorUnit.on( ActorUnit.EVT_BLE_DISCOVERING, self.bleHandleDiscovering )
        self.actorUnit.on( ActorUnit.EVT_BLE_CONNECTED, self.bleHandleConnected )
        self.actorUnit.on( ActorUnit.EVT_BLE_DISCONNECTED, self.bleHandleDisconnected )
        self.actorUnit.init()

    # 
    # Shuts down the instance safely.
    #
    def close(self):
        self.done = True
        self.charger.close()
        self.actorUnit.close()
        if self.tmpLED:
            self.tmpLED.close()
            self.tmpLED = None
        if self.batLED:
            self.batLED.close()
            self.batLED = None
        if self.bleLED:
            self.bleLED.close()
            self.bleLED = None
        if self.dcLED:
            self.dcLED.close()
            self.dcLED = None
        if self.chgLED:
            self.chgLED.close()
            self.chgLED = None
        if self.aux0LED:
            self.aux0LED.close()
            self.aux0LED = None
        if self.aux1LED:
            self.aux1LED.close()
            self.aux1LED = None
        if self.cmdBtn:
            self.cmdBtn.close()
            self.cmdBtn = None

    #
    # Own, specific API
    #
            
    def manageSystem( self ):
        logging.info('FGSystemManagement> Management thread is running.')
        self._sysjobLock.acquire()
        self._systemJob = FGSystemManagement._SYSJOB_NONE
        self._sysjobLock.release()

        # Note that the BLE status is maintained in a separate loop
        batStatus = -1
        tmpStatus = -1
        dcStatus  = -1
        chgStatus = -1

        while not self.done:
            try:
                # Battery status is not available during battery-only mode.
                # So this is not a helpful battery level information.
                val = self.charger.getBatStatus()
                if val != batStatus:
                    batStatus = val
                    self._displayStatusChange( FGSystemManagement._INFOCAT_BAT_STATE, batStatus )
                
                val = self.charger.getChargerTempState()
                if batStatus != BatteryCharger.BAT_STATE_REMOVED:
                    val1 = self.charger.getBatteryTempState()
                    val = self._combineTempStatus( val, val1 )
                if val != tmpStatus:
                    oldStatus = tmpStatus
                    tmpStatus = val
                    self._displayStatusChange( FGSystemManagement._INFOCAT_TEMP, tmpStatus )
                    if val in FGSystemManagement._CRITICAL_TEMPERATURES:
                        self.emit( FGSystemManagement.EVT_TEMP_CRITICAL )
                    elif oldStatus in FGSystemManagement._CRITICAL_TEMPERATURES:
                        self.emit( FGSystemManagement.EVT_TEMP_NORMAL )
                
                val  = self.charger.getDCStatus()
                if val != dcStatus:
                    dcStatus = val
                    self._displayStatusChange( FGSystemManagement._INFOCAT_DC_SUPPLY, dcStatus )
                    if dcStatus == BatteryCharger.DC_STATE_VALID:
                        self.emit( FGSystemManagement.EVT_DC_PLUGGED )
                    else:
                        self.emit( FGSystemManagement.EVT_DC_UNPLUGGED )
                        
                val = self.charger.getChgStatus()
                if val != chgStatus:
                    chgStatus = val
                    self._displayStatusChange( FGSystemManagement._INFOCAT_CHG_STATE, chgStatus )

                self._executeSystemJobs()
            except RuntimeError as exc:
                logging.exception(exc)
            time.sleep(0.5)
        logging.info('FGSystemManagement> Management thread stopped.')
    
    
    def _combineTempStatus( self, tempStatus1, tempStatus2 ):
        if tempStatus1 < tempStatus2:
            low = tempStatus1
            high = tempStatus2
        else:
            high = tempStatus1
            low = tempStatus2
        ret = BatteryCharger.TEMP_OK
        if high == BatteryCharger.TEMP_HOT:
            ret = high
        elif low==BatteryCharger.TEMP_COLD:
            ret = low
        elif high == BatteryCharger.TEMP_WARM:
            ret = high
        elif low==BatteryCharger.TEMP_COOL:
            ret = low
        else:
            ret = high
        return ret
        
    def _executeSystemJobs( self ):
        if self._systemJob & FGSystemManagement._SYSJOB_AU_COUPLE:
            self.actorUnit.couple()
            self._sysjobLock.acquire()
            self._systemJob &= ~FGSystemManagement._SYSJOB_AU_COUPLE
            self._sysjobLock.release()
            
    def _displayStatusChange( self, infoCat, newStatus ):
        if infoCat == FGSystemManagement._INFOCAT_TEMP:
            logging.info('FGSystemManagement> TMP state: %s', BatteryCharger.temp2Str.get( newStatus, 'UNKNOWN' ))
            if self.tmpLED:
                if newStatus == BatteryCharger.TEMP_OK:
                    self.tmpLED.off()
                elif (newStatus==BatteryCharger.TEMP_WARM) or (newStatus==BatteryCharger.TEMP_COOL):
                    self.tmpLED.blink()
                else:
                    self.tmpLED.on()
        elif infoCat == FGSystemManagement._INFOCAT_BAT_STATE:
            logging.info('FGSystemManagement> BAT state: %s', BatteryCharger.batState2Str.get( newStatus, 'UNKNOWN' ))
            if self.batLED:
                if newStatus == BatteryCharger.BAT_STATE_NORMAL:
                    self.batLED.on()
                elif newStatus == BatteryCharger.BAT_STATE_LOW:
                    self.batLED.blink()
                elif newStatus == BatteryCharger.BAT_STATE_EMPTY:
                    self.batLED.blink( cycle_length=SmartLED.CYCLEN_FAST )
                else:
                    self.batLED.off()
        elif infoCat == FGSystemManagement._INFOCAT_BLE:
            logging.info('FGSystemManagement> BLE state: %s', ActorUnit.connState2Str.get( newStatus, 'UNKNOWN'))
            if self.bleLED:
                if newStatus == ActorUnit.BLE_CONN_STATE_CONNECTED:
                    self.bleLED.on()
                elif newStatus == ActorUnit.BLE_CONN_STATE_DISCOVERING:
                    self.bleLED.blink( cycle_length=SmartLED.CYCLEN_NORMAL )
                else:
                    self.bleLED.off()
        elif infoCat == FGSystemManagement._INFOCAT_DC_SUPPLY:
            logging.info('FGSystemManagement>  DC state: %s', BatteryCharger.dcState2Str.get( newStatus, 'UNKNOWN' ))
            if self.dcLED:
                if newStatus == BatteryCharger.DC_STATE_VALID:
                    self.dcLED.on()
                elif newStatus == BatteryCharger.DC_STATE_OFF:
                    self.dcLED.off()
                else:
                    self.dcLED.blink()
        elif infoCat == FGSystemManagement._INFOCAT_CHG_STATE:
            logging.info('FGSystemManagement> CHG state: %s', BatteryCharger.chgState2Str.get( newStatus, 'UNKNOWN' ))
            if self.chgLED:
                if newStatus in {BatteryCharger.CHG_STATE_DONE, BatteryCharger.CHG_STATE_TOP_OFF}:
                    self.chgLED.on()
                elif newStatus in {BatteryCharger.CHG_STATE_FASTCHARGE, BatteryCharger.CHG_STATE_FAST_CC, BatteryCharger.CHG_STATE_FAST_CV}:
                    self.chgLED.blink( cycle_length=SmartLED.CYCLEN_FAST )
                elif newStatus in {BatteryCharger.CHG_STATE_PRECHARGE, BatteryCharger.CHG_STATE_TRICKLE}:
                    self.chgLED.blink()
                else:
                    self.chgLED.off()
        
    #
    #
    #
    def bleHandleDiscovering( self ):
        self._displayStatusChange( FGSystemManagement._INFOCAT_BLE, ActorUnit.BLE_CONN_STATE_DISCOVERING )
        
    def bleHandleConnected( self ):
        self._displayStatusChange( FGSystemManagement._INFOCAT_BLE, ActorUnit.BLE_CONN_STATE_CONNECTED )
        self.emit( FGSystemManagement.EVT_BLE_CONNECTED )
        
    def bleHandleDisconnected( self ):
        self._displayStatusChange( FGSystemManagement._INFOCAT_BLE, ActorUnit.BLE_CONN_STATE_DISCONNECTED )
        self.emit( FGSystemManagement.EVT_BLE_DISCONNECTED )
        # Start re-discovering
        if not self.done:
            self._sysjobLock.acquire()
            self._systemJob = self._systemJob | FGSystemManagement._SYSJOB_AU_COUPLE
            self._sysjobLock.release()
            
    def uiHandleButtonPressed( self ):
        self.emit( FGSystemManagement.EVT_BUTTON_PRESSED )
        
        
        