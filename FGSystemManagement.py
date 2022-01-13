from threading import Thread, Lock
from Configurable import Configurable
from MAX77960 import MAX77960 as Charger
from BatteryCharger import BatteryCharger
from ActorUnit import ActorUnit
from gpiozero import LED, PWMLED

import time

# The fastGait power management and user interface
class FGSystemManagement( Configurable ):
    
    #
    # Public class attributes
    #
        
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
    
    #
    # The Configurable API
    #
    
    #
    # Initializes the sensor.
    # The only input parameter is a dictionary containing key-value pairs that
    # configure the instance. Key names and their meanings are:
    # UI.LED.tmp.pin         : Pin of the temperature LED, such as 17 or 'GPIO17'
    # UI.LED.bat.pin         : Pin of the battery status LED
    # UI.LED.ble.pin         : Pin of the BLE connection status LED
    # UI.LED.dc.pin          : Pin of the DC supply status LED
    # UI.LED.chg.pin         : Pin of the charger status LED
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
        self.batLED = None
        self._batLEDpin = None
        self.bleLED = None
        self._bleLEDpin = None
        self.dcLED = None
        self._dcLEDpin = None
        self.chgLED = None
        self._chgLEDpin = None
        self.monitor = Thread( target=self.manageSystem, name='System Management' )
        # Set defaults
        if not "UI.LED.tmp.pin" in paramDict:
            paramDict["UI.LED.tmp.pin"] = None
        if not "UI.LED.bat.pin" in paramDict:
            paramDict["UI.LED.bat.pin"] = None
        if not "UI.LED.ble.pin" in paramDict:
            paramDict["UI.LED.ble.pin"] = None
        if not "UI.LED.dc.pin" in paramDict:
            paramDict["UI.LED.dc.pin"] = None
        if not "UI.LED.chg.pin" in paramDict:
            paramDict["UI.LED.chg.pin"] = None

    #
    # Scans the parameters for known keys.
    #
    def _scanParameters( self, paramDict ):
        if "UI.LED.tmp.pin" in paramDict:
            self._tmpLEDpin = paramDict["UI.LED.tmp.pin"]
        if "UI.LED.bat.pin" in paramDict:
            self._batLEDpin = paramDict["UI.LED.bat.pin"]
        if "UI.LED.ble.pin" in paramDict:
            self._bleLEDpin = paramDict["UI.LED.ble.pin"]
        if "UI.LED.dc.pin" in paramDict:
            self._dcLEDpin = paramDict["UI.LED.dc.pin"]
        if "UI.LED.chg.pin" in paramDict:
            self._chgLEDpin = paramDict["UI.LED.chg.pin"]
                
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
            self.tmpLED = LED( self._tmpLEDpin )
        if self._batLEDpin:
            self.batLED = LED( self._batLEDpin )
        if self._bleLEDpin:
            self.bleLED = LED( self._bleLEDpin )
        if self._dcLEDpin:
            self.dcLED = LED( self._dcLEDpin )
        if self._chgLEDpin:
            self.chgLED = LED( self._chgLEDpin )
        self.monitor.start()
        self.actorUnit.setBLECallback( self.bleCallBack )
        self.actorUnit.init()

    # 
    # Shuts down the instance safely.
    #
    def close(self):
        self.done = True
        self.charger.close()
        self.actorUnit.close()
        if self.tmpLED:
            self.tmpLED.off()
            self.tmpLED.close()
        if self.batLED:
            self.batLED.off()
            self.batLED.close()
        if self.bleLED:
            self.bleLED.off()
            self.bleLED.close()
        if self.dcLED:
            self.dcLED.off()
            self.dcLED.close()
        if self.chgLED:
            self.chgLED.off()
            self.chgLED.close()

    #
    # Own, specific API
    #
            
    def manageSystem( self ):
        print('System management thread is running')
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
                val = self.charger.getBatStatus()
                if val != batStatus:
                    batStatus = val
                    self._displayStatusChange( FGSystemManagement._INFOCAT_BAT_STATE, batStatus )
                
                val = self.charger.getChargerTempState()
                if batStatus != BatteryCharger.BAT_STATE_REMOVED:
                    val1 = self.charger.getBatteryTempState()
                    val = self._joinTempStatus( val, val1 )
                if val != tmpStatus:
                    tmpStatus = val
                    self._displayStatusChange( FGSystemManagement._INFOCAT_TEMP, tmpStatus )
                
                val  = self.charger.getDCStatus()
                if val != dcStatus:
                    dcStatus = val
                    self._displayStatusChange( FGSystemManagement._INFOCAT_DC_SUPPLY, dcStatus )
                val = self.charger.getChgStatus()
                if val != chgStatus:
                    chgStatus = val
                    self._displayStatusChange( FGSystemManagement._INFOCAT_CHG_STATE, chgStatus )

                self._executeSystemJobs()
            except RuntimeError as exc:
                print(exc)
            time.sleep(0.5)
        print('System management thread stopped.')
    
    def _joinTempStatus( self, tempStatus1, tempStatus2 ):
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
            print('TMP state:', BatteryCharger.temp2Str.get( newStatus, 'UNKNOWN' ))
            if self.tmpLED:
                if newStatus == BatteryCharger.TEMP_OK:
                    self.tmpLED.off()
                elif (newStatus==BatteryCharger.TEMP_WARM) or (newStatus==BatteryCharger.TEMP_COOL):
                    self.tmpLED.blink( on_time=0.5, off_time=0.5 )
                else:
                    self.tmpLED.on()
        elif infoCat == FGSystemManagement._INFOCAT_BAT_STATE:
            print('BAT state:', BatteryCharger.batState2Str.get( newStatus, 'UNKNOWN' ))
            if self.batLED:
                if newStatus == BatteryCharger.BAT_STATE_NORMAL:
                    self.batLED.on()
                elif newStatus == BatteryCharger.BAT_STATE_LOW:
                    self.batLED.blink( on_time=0.5, off_time=0.5 )
                else:
                    self.batLED.off()
        elif infoCat == FGSystemManagement._INFOCAT_BLE:
            print('BLE state:', ActorUnit.connState2Str.get( newStatus, 'UNKNOWN'))
            if self.bleLED:
                if newStatus == ActorUnit.BLE_CONN_STATE_CONNECTED:
                    self.bleLED.on()
                elif newStatus == ActorUnit.BLE_CONN_STATE_DISCOVERING:
                    self.bleLED.blink( on_time=0.25, off_time=0.25 )
                else:
                    self.bleLED.off()
        elif infoCat == FGSystemManagement._INFOCAT_DC_SUPPLY:
            print(' DC state:', BatteryCharger.dcState2Str.get( newStatus, 'UNKNOWN' ))
            if self.dcLED:
                if newStatus == BatteryCharger.DC_STATE_VALID:
                    self.dcLED.on()
                elif newStatus == BatteryCharger.DC_STATE_OFF:
                    self.dcLED.off()
                else:
                    self.dcLED.blink( on_time=0.5, off_time=0.5 )
        elif infoCat == FGSystemManagement._INFOCAT_CHG_STATE:
            print('CHG state:', BatteryCharger.chgState2Str.get( newStatus, 'UNKNOWN' ))
            if self.chgLED:
                if newStatus in {BatteryCharger.CHG_STATE_DONE, BatteryCharger.CHG_STATE_TOP_OFF}:
                    self.chgLED.on()
                elif newStatus in {BatteryCharger.CHG_STATE_FASTCHARGE, BatteryCharger.CHG_STATE_FAST_CC, BatteryCharger.CHG_STATE_FAST_CV}:
                    self.chgLED.blink( on_time=0.25, off_time=0.25 )
                elif newStatus in {BatteryCharger.CHG_STATE_PRECHARGE, BatteryCharger.CHG_STATE_TRICKLE}:
                    self.chgLED.blink( on_time=0.5, off_time=0.5 )
                else:
                    self.chgLED.off()
        
    #
    #
    #
    def bleCallBack( self, newState ):
        self._displayStatusChange( FGSystemManagement._INFOCAT_BLE, newState )
        if newState == ActorUnit.BLE_CONN_STATE_DISCONNECTED:
            # Start re-discovering
            if not self.done:
                self._sysjobLock.acquire()
                self._systemJob = self._systemJob | FGSystemManagement._SYSJOB_AU_COUPLE
                self._sysjobLock.release()
            
