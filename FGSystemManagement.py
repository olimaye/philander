from threading import Thread
from MAX77960 import MAX77960 as power
from BatteryCharger import BatteryCharger

import time

# The fastGait power management and user interface thread
class FGSystemManagement( Thread ):
    
    def __init__(self, paramDict):
        Thread.__init__(self, name='System Management')
        self.done = False
        self.pm = power( paramDict )
        self.pm.init()

    def run( self ):
        print('System management thread is running')
        batStatus = self.pm.getBatStatus()
        chgStatus = self.pm.getChgStatus()
        dcStatus  = self.pm.getDCStatus()
        batTempStatus = self.pm.getBatteryTempState()
        chgTempStatus = self.pm.getChargerTempState()
        powerSrc  = self.pm.getPowerSrc()
        error     = self.pm.getError()
        sBatStatus = BatteryCharger.batState2Str.get( batStatus, 'UNKNOWN' )
        sChgStatus = BatteryCharger.chgState2Str.get( chgStatus, 'UNKNOWN' )
        sDCStatus  = BatteryCharger.dcState2Str.get(  dcStatus, 'UNKNOWN' )
        sBatTempStatus = BatteryCharger.temp2Str.get( batTempStatus, 'UNKNOWN' )
        sChgTempStatus = BatteryCharger.temp2Str.get( chgTempStatus, 'UNKNOWN' )
        sPowerSrc  = BatteryCharger.pwrsrc2Str.get( powerSrc, 'UNKNOWN' )
        sError     = BatteryCharger.err2Str.get( error, 'UNKNOWN' )
        print(f'Bat.state: {sBatStatus:10}   Chg.state: {sChgStatus}')
        print(f' DC.state: {sDCStatus:10}    PowerSrc: {sPowerSrc}')
        print(f'Chg.temp : {sChgTempStatus:10}    Bat.temp: {sBatTempStatus}')
        print(f'   Error : {sError:10}')

        while not self.done:
            try:
                val = self.pm.getBatStatus()
                if val != batStatus:
                    print('Bat.state changed from ',
                              BatteryCharger.batState2Str.get( batStatus, 'UNKNOWN' ), 'to',
                              BatteryCharger.batState2Str.get( val, 'UNKNOWN' ) )
                    batStatus = val
                val = self.pm.getChgStatus()
                if val != chgStatus:
                    print('Chg.state changed from ',
                              BatteryCharger.chgState2Str.get( chgStatus, 'UNKNOWN' ), 'to',
                              BatteryCharger.chgState2Str.get( val, 'UNKNOWN' ) )
                    chgStatus = val
                val  = self.pm.getDCStatus()
                if val != dcStatus:
                    print('DC.state changed from ',
                              BatteryCharger.dcState2Str.get( dcStatus, 'UNKNOWN' ), 'to',
                              BatteryCharger.dcState2Str.get( val, 'UNKNOWN' ) )
                    dcStatus = val
                if batStatus != BatteryCharger.BAT_STATE_REMOVED:
                    val = self.pm.getBatteryTempState()
                    if val != batTempStatus:
                        print('Bat.temp changed from ',
                                  BatteryCharger.temp2Str.get( batTempStatus, 'UNKNOWN' ), 'to',
                                  BatteryCharger.temp2Str.get( val, 'UNKNOWN' ) )
                        batTempStatus = val
                val = self.pm.getChargerTempState()
                if val != chgTempStatus:
                    print('Chg.temp changed from ',
                              BatteryCharger.temp2Str.get( chgTempStatus, 'UNKNOWN' ), 'to',
                              BatteryCharger.temp2Str.get( val, 'UNKNOWN' ) )
                    chgTempStatus = val
                val  = self.pm.getPowerSrc()
                if val != powerSrc:
                    print('PowerSrc changed from ',
                              BatteryCharger.pwrsrc2Str.get( powerSrc, 'UNKNOWN' ), 'to',
                              BatteryCharger.pwrsrc2Str.get( val, 'UNKNOWN' ) )
                    powerSrc = val
                val     = self.pm.getError()
                if val != error:
                    print('Error changed from ',
                              BatteryCharger.err2Str.get( error, 'UNKNOWN' ), 'to',
                              BatteryCharger.err2Str.get( val, 'UNKNOWN' ) )
                    error = val
            except RuntimeError as exc:
                print(exc)
            time.sleep(0.5)
        print('System management thread stopped.')


    def terminate( self ):
        self.done = True
    
