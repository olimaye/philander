# -*- coding: utf-8 -*-
"""Support module for the MAX77960 USB battery charger.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["MAX77960"]

from .battery import Status as BatStatus
from .charger import Charger, Status as ChgStatus, DCStatus, PowerSrc,\
    TemperatureRating, ChargerError, EventSource
from .configurable import ConfigItem, Configurable
from .gpio import GPIO
from .imath import *
from .interruptable import Event, Interruptable, EventContextControl
from .max77960_reg import MAX77960_Reg
from .serialbus import SerialBusDevice
from .systypes import ErrorCode, Info, RunLevel
from .watchdog import Watchdog


class MAX77960( MAX77960_Reg, SerialBusDevice, Charger, Configurable, Interruptable, Watchdog ):
    """Driver implementation for the MAX77960 USB battery charger.
    
    More information on the functionality of the chip can be found at
    the Analog site:
    https://www.analog.com/en/products/max77960.html
    """
        
    # The only address is 0x69. No alternative.
    ADRESSES_ALLOWED = [0x69]

    # The watch dog time interval t(WD)as defined in the data sheet
    WATCHDOG_INTERVAL_MS = 80000

    def getRegisterMap(self):
        return self._registerMap
    
    def getRegContentStr( self, regDescr, content ):
        ret=''
        if not regDescr[2]:    # No description of components/bits given
            ret = hex(content)
        else:
            for frag in regDescr[2]:
                shift = self._lowestBitNum( frag[0] )
                fragVal = (content & frag[0]) >> shift
                ret = ret + frag[1] + '=' + str(fragVal) + ' '
        return ret


    def getAllRegistersStr(self):
        ret = []
        for descr in self._registerMap:
            cont, err = self.readByteRegister( descr[0] )
            if (err == ErrorCode.errOk):
                contStr = self.getRegContentStr( descr, cont )
            else:
                cont = 0
                contStr = f"Read error: {err}"
            ret.append([descr[0], descr[1], cont, contStr])
        return ret

    def _lowestBitNum( self, x ):
        ret = 0
        if x==0:
            ret = -1
        else:
            mask = 1
            while not (x & mask):
                ret = ret + 1
                mask = mask << 1
        return ret
            
            
    #
    # Configurable options
    #
    
    CFG_COMM_MODE = 'Charger.Comm.Mode'
    CFG_COMM_MODE_AUTO = MAX77960_Reg._COMM_MODE_AUTO
    CFG_COMM_MODE_I2C  = MAX77960_Reg._COMM_MODE_I2C
    CFG_COMM_MODE_DEFAULT = MAX77960_Reg._COMM_MODE_DEFAULT
    CFG_DISIBS = 'Charger.DisIBS'
    CFG_DISIBS_FET_PPSM = MAX77960_Reg._DISIBS_FET_PPSM
    CFG_DISIBS_FET_OFF  = MAX77960_Reg._DISIBS_FET_OFF
    CFG_DISIBS_DEFAULT  = MAX77960_Reg._DISIBS_DEFAULT
    CFG_MODE = 'Charger.Mode'
    CFG_MODE_ALL_OFF   = MAX77960_Reg._MODE_ALL_OFF
    CFG_MODE_CHRG_DCDC = MAX77960_Reg._MODE_CHRG_DCDC
    CFG_MODE_DCDC_ONLY = MAX77960_Reg._MODE_DCDC_ONLY
    CFG_MODE_OTG_ONLY  = MAX77960_Reg._MODE_OTG_ONLY
    CFG_MODE_DEFAULT   = MAX77960_Reg._MODE_DEFAULT
    CFG_PQEN = 'Charger.Prequal'
    CFG_PQEN_ON  = MAX77960_Reg._PQEN_ON
    CFG_PQEN_OFF = MAX77960_Reg._PQEN_OFF
    CFG_PQEN_DEFAULT = MAX77960_Reg._PQEN_DEFAULT
    CFG_CHG_RSTRT = 'Charger.Restart'
    CFG_CHG_RSTRT_100 = MAX77960_Reg._CHG_RSTRT_100
    CFG_CHG_RSTRT_150 = MAX77960_Reg._CHG_RSTRT_150
    CFG_CHG_RSTRT_200 = MAX77960_Reg._CHG_RSTRT_200
    CFG_CHG_RSTRT_DISABLED = MAX77960_Reg._CHG_RSTRT_DISABLED
    CFG_CHG_RSTRT_DEFAULT  = MAX77960_Reg._CHG_RSTRT_DEFAULT
    CFG_STAT_EN = 'Charger.Stat'
    CFG_STAT_EN_ON  = MAX77960_Reg._STAT_EN_ON
    CFG_STAT_EN_OFF = MAX77960_Reg._STAT_EN_OFF
    CFG_STAT_EN_DEFAULT = MAX77960_Reg._STAT_EN_DEFAULT
    CFG_FCHGTIME = 'Charger.Timer.FastCharge'
    CFG_FCHGTIME_DISABLED = MAX77960_Reg._FCHGTIME_DISABLED
    CFG_FCHGTIME_3H = MAX77960_Reg._FCHGTIME_3H
    CFG_FCHGTIME_4H = MAX77960_Reg._FCHGTIME_4H
    CFG_FCHGTIME_5H = MAX77960_Reg._FCHGTIME_5H
    CFG_FCHGTIME_6H = MAX77960_Reg._FCHGTIME_6H
    CFG_FCHGTIME_7H = MAX77960_Reg._FCHGTIME_7H
    CFG_FCHGTIME_8H = MAX77960_Reg._FCHGTIME_8H
    CFG_FCHGTIME_10H= MAX77960_Reg._FCHGTIME_10H
    CFG_FCHGTIME_DEFAULT = MAX77960_Reg._FCHGTIME_DEFAULT
    CFG_CHGCC = 'Charger.Current.FastCharge'
    CFG_CHGCC_100  = MAX77960_Reg._CHGCC_100
    CFG_CHGCC_150  = MAX77960_Reg._CHGCC_150
    CFG_CHGCC_200  = MAX77960_Reg._CHGCC_200
    CFG_CHGCC_250  = MAX77960_Reg._CHGCC_250
    CFG_CHGCC_300  = MAX77960_Reg._CHGCC_300
    CFG_CHGCC_350  = MAX77960_Reg._CHGCC_350
    CFG_CHGCC_400  = MAX77960_Reg._CHGCC_400
    CFG_CHGCC_450  = MAX77960_Reg._CHGCC_450
    CFG_CHGCC_500  = MAX77960_Reg._CHGCC_500
    CFG_CHGCC_600  = MAX77960_Reg._CHGCC_600
    CFG_CHGCC_700  = MAX77960_Reg._CHGCC_700
    CFG_CHGCC_800  = MAX77960_Reg._CHGCC_800
    CFG_CHGCC_900  = MAX77960_Reg._CHGCC_900
    CFG_CHGCC_1000  = MAX77960_Reg._CHGCC_1000
    CFG_CHGCC_1100  = MAX77960_Reg._CHGCC_1100
    CFG_CHGCC_1200  = MAX77960_Reg._CHGCC_1200
    CFG_CHGCC_1300  = MAX77960_Reg._CHGCC_1300
    CFG_CHGCC_1400  = MAX77960_Reg._CHGCC_1400
    CFG_CHGCC_1500  = MAX77960_Reg._CHGCC_1500
    CFG_CHGCC_1600  = MAX77960_Reg._CHGCC_1600
    CFG_CHGCC_1700  = MAX77960_Reg._CHGCC_1700
    CFG_CHGCC_1800  = MAX77960_Reg._CHGCC_1800
    CFG_CHGCC_1900  = MAX77960_Reg._CHGCC_1900
    CFG_CHGCC_2000  = MAX77960_Reg._CHGCC_2000
    CFG_CHGCC_2100  = MAX77960_Reg._CHGCC_2100
    CFG_CHGCC_2200  = MAX77960_Reg._CHGCC_2200
    CFG_CHGCC_2300  = MAX77960_Reg._CHGCC_2300
    CFG_CHGCC_2400  = MAX77960_Reg._CHGCC_2400
    CFG_CHGCC_2500  = MAX77960_Reg._CHGCC_2500
    CFG_CHGCC_2600  = MAX77960_Reg._CHGCC_2600
    CFG_CHGCC_2700  = MAX77960_Reg._CHGCC_2700
    CFG_CHGCC_2800  = MAX77960_Reg._CHGCC_2800
    CFG_CHGCC_2900  = MAX77960_Reg._CHGCC_2900
    CFG_CHGCC_3000  = MAX77960_Reg._CHGCC_3000
    CFG_CHGCC_3100  = MAX77960_Reg._CHGCC_3100
    CFG_CHGCC_3200  = MAX77960_Reg._CHGCC_3200
    CFG_CHGCC_3300  = MAX77960_Reg._CHGCC_3300
    CFG_CHGCC_3400  = MAX77960_Reg._CHGCC_3400
    CFG_CHGCC_3500  = MAX77960_Reg._CHGCC_3500
    CFG_CHGCC_3600  = MAX77960_Reg._CHGCC_3600
    CFG_CHGCC_3700  = MAX77960_Reg._CHGCC_3700
    CFG_CHGCC_3800  = MAX77960_Reg._CHGCC_3800
    CFG_CHGCC_3900  = MAX77960_Reg._CHGCC_3900
    CFG_CHGCC_4000  = MAX77960_Reg._CHGCC_4000
    CFG_CHGCC_4100  = MAX77960_Reg._CHGCC_4100
    CFG_CHGCC_4200  = MAX77960_Reg._CHGCC_4200
    CFG_CHGCC_4300  = MAX77960_Reg._CHGCC_4300
    CFG_CHGCC_4400  = MAX77960_Reg._CHGCC_4400
    CFG_CHGCC_4500  = MAX77960_Reg._CHGCC_4500
    CFG_CHGCC_4600  = MAX77960_Reg._CHGCC_4600
    CFG_CHGCC_4700  = MAX77960_Reg._CHGCC_4700
    CFG_CHGCC_4800  = MAX77960_Reg._CHGCC_4800
    CFG_CHGCC_4900  = MAX77960_Reg._CHGCC_4900
    CFG_CHGCC_5000  = MAX77960_Reg._CHGCC_5000
    CFG_CHGCC_5100  = MAX77960_Reg._CHGCC_5100
    CFG_CHGCC_5200  = MAX77960_Reg._CHGCC_5200
    CFG_CHGCC_5300  = MAX77960_Reg._CHGCC_5300
    CFG_CHGCC_5400  = MAX77960_Reg._CHGCC_5400
    CFG_CHGCC_5500  = MAX77960_Reg._CHGCC_5500
    CFG_CHGCC_5600  = MAX77960_Reg._CHGCC_5600
    CFG_CHGCC_5700  = MAX77960_Reg._CHGCC_5700
    CFG_CHGCC_5800  = MAX77960_Reg._CHGCC_5800
    CFG_CHGCC_5900  = MAX77960_Reg._CHGCC_5900
    CFG_CHGCC_6000  = MAX77960_Reg._CHGCC_6000
    CFG_CHGCC_DEFAULT = MAX77960_Reg._CHGCC_DEFAULT
    CFG_TO_TIME = 'Charger.Timer.Topoff'
    CFG_TO_TIME_30_SEC = MAX77960_Reg._TO_TIME_30_SEC
    CFG_TO_TIME_10_MIN = MAX77960_Reg._TO_TIME_10_MIN
    CFG_TO_TIME_20_MIN = MAX77960_Reg._TO_TIME_20_MIN
    CFG_TO_TIME_30_MIN = MAX77960_Reg._TO_TIME_30_MIN
    CFG_TO_TIME_40_MIN = MAX77960_Reg._TO_TIME_40_MIN
    CFG_TO_TIME_50_MIN = MAX77960_Reg._TO_TIME_50_MIN
    CFG_TO_TIME_60_MIN = MAX77960_Reg._TO_TIME_60_MIN
    CFG_TO_TIME_70_MIN = MAX77960_Reg._TO_TIME_70_MIN
    CFG_TO_TIME_DEFAULT = MAX77960_Reg._TO_TIME_DEFAULT
    CFG_TO_ITH = 'Charger.Current.Topoff'
    CFG_TO_ITH_100 = MAX77960_Reg._TO_ITH_100
    CFG_TO_ITH_200 = MAX77960_Reg._TO_ITH_200
    CFG_TO_ITH_300 = MAX77960_Reg._TO_ITH_300
    CFG_TO_ITH_400 = MAX77960_Reg._TO_ITH_400
    CFG_TO_ITH_500 = MAX77960_Reg._TO_ITH_500
    CFG_TO_ITH_600 = MAX77960_Reg._TO_ITH_600
    CFG_TO_ITH_DEFAULT = MAX77960_Reg._TO_ITH_DEFAULT
    CFG_CHG_CV_PRM = 'Charger.Voltage.ChargeTermination'
    CFG_CHG_CV_PRM_2C_8000 = MAX77960_Reg._CHG_CV_PRM_2C_8000
    CFG_CHG_CV_PRM_2C_8020 = MAX77960_Reg._CHG_CV_PRM_2C_8020
    CFG_CHG_CV_PRM_2C_8040 = MAX77960_Reg._CHG_CV_PRM_2C_8040
    CFG_CHG_CV_PRM_2C_8060 = MAX77960_Reg._CHG_CV_PRM_2C_8060
    CFG_CHG_CV_PRM_2C_8080 = MAX77960_Reg._CHG_CV_PRM_2C_8080
    CFG_CHG_CV_PRM_2C_8100 = MAX77960_Reg._CHG_CV_PRM_2C_8100
    CFG_CHG_CV_PRM_2C_8120 = MAX77960_Reg._CHG_CV_PRM_2C_8120
    CFG_CHG_CV_PRM_2C_8130 = MAX77960_Reg._CHG_CV_PRM_2C_8140
    CFG_CHG_CV_PRM_2C_8140 = MAX77960_Reg._CHG_CV_PRM_2C_8160
    CFG_CHG_CV_PRM_2C_8150 = MAX77960_Reg._CHG_CV_PRM_2C_8180
    CFG_CHG_CV_PRM_2C_8200 = MAX77960_Reg._CHG_CV_PRM_2C_8200
    CFG_CHG_CV_PRM_2C_8220 = MAX77960_Reg._CHG_CV_PRM_2C_8220
    CFG_CHG_CV_PRM_2C_8240 = MAX77960_Reg._CHG_CV_PRM_2C_8240
    CFG_CHG_CV_PRM_2C_8260 = MAX77960_Reg._CHG_CV_PRM_2C_8260
    CFG_CHG_CV_PRM_2C_8280 = MAX77960_Reg._CHG_CV_PRM_2C_8280
    CFG_CHG_CV_PRM_2C_8300 = MAX77960_Reg._CHG_CV_PRM_2C_8300
    CFG_CHG_CV_PRM_2C_8320 = MAX77960_Reg._CHG_CV_PRM_2C_8320
    CFG_CHG_CV_PRM_2C_8340 = MAX77960_Reg._CHG_CV_PRM_2C_8340
    CFG_CHG_CV_PRM_2C_8360 = MAX77960_Reg._CHG_CV_PRM_2C_8360
    CFG_CHG_CV_PRM_2C_8380 = MAX77960_Reg._CHG_CV_PRM_2C_8380
    CFG_CHG_CV_PRM_2C_8400 = MAX77960_Reg._CHG_CV_PRM_2C_8400
    CFG_CHG_CV_PRM_2C_8420 = MAX77960_Reg._CHG_CV_PRM_2C_8420
    CFG_CHG_CV_PRM_2C_8440 = MAX77960_Reg._CHG_CV_PRM_2C_8440
    CFG_CHG_CV_PRM_2C_8460 = MAX77960_Reg._CHG_CV_PRM_2C_8460
    CFG_CHG_CV_PRM_2C_8480 = MAX77960_Reg._CHG_CV_PRM_2C_8480
    CFG_CHG_CV_PRM_2C_8500 = MAX77960_Reg._CHG_CV_PRM_2C_8500
    CFG_CHG_CV_PRM_2C_8520 = MAX77960_Reg._CHG_CV_PRM_2C_8520
    CFG_CHG_CV_PRM_2C_8540 = MAX77960_Reg._CHG_CV_PRM_2C_8540
    CFG_CHG_CV_PRM_2C_8560 = MAX77960_Reg._CHG_CV_PRM_2C_8560
    CFG_CHG_CV_PRM_2C_8580 = MAX77960_Reg._CHG_CV_PRM_2C_8580
    CFG_CHG_CV_PRM_2C_8600 = MAX77960_Reg._CHG_CV_PRM_2C_8600
    CFG_CHG_CV_PRM_2C_8620 = MAX77960_Reg._CHG_CV_PRM_2C_8620
    CFG_CHG_CV_PRM_2C_8640 = MAX77960_Reg._CHG_CV_PRM_2C_8640
    CFG_CHG_CV_PRM_2C_8660 = MAX77960_Reg._CHG_CV_PRM_2C_8660
    CFG_CHG_CV_PRM_2C_8680 = MAX77960_Reg._CHG_CV_PRM_2C_8680
    CFG_CHG_CV_PRM_2C_8700 = MAX77960_Reg._CHG_CV_PRM_2C_8700
    CFG_CHG_CV_PRM_2C_8720 = MAX77960_Reg._CHG_CV_PRM_2C_8720
    CFG_CHG_CV_PRM_2C_8740 = MAX77960_Reg._CHG_CV_PRM_2C_8740
    CFG_CHG_CV_PRM_2C_8760 = MAX77960_Reg._CHG_CV_PRM_2C_8760
    CFG_CHG_CV_PRM_2C_8780 = MAX77960_Reg._CHG_CV_PRM_2C_8780
    CFG_CHG_CV_PRM_2C_8800 = MAX77960_Reg._CHG_CV_PRM_2C_8800
    CFG_CHG_CV_PRM_2C_8820 = MAX77960_Reg._CHG_CV_PRM_2C_8820
    CFG_CHG_CV_PRM_2C_8840 = MAX77960_Reg._CHG_CV_PRM_2C_8840
    CFG_CHG_CV_PRM_2C_8860 = MAX77960_Reg._CHG_CV_PRM_2C_8860
    CFG_CHG_CV_PRM_2C_8880 = MAX77960_Reg._CHG_CV_PRM_2C_8880
    CFG_CHG_CV_PRM_2C_8900 = MAX77960_Reg._CHG_CV_PRM_2C_8900
    CFG_CHG_CV_PRM_2C_8920 = MAX77960_Reg._CHG_CV_PRM_2C_8920
    CFG_CHG_CV_PRM_2C_8940 = MAX77960_Reg._CHG_CV_PRM_2C_8940
    CFG_CHG_CV_PRM_2C_8960 = MAX77960_Reg._CHG_CV_PRM_2C_8960
    CFG_CHG_CV_PRM_2C_8980 = MAX77960_Reg._CHG_CV_PRM_2C_8980
    CFG_CHG_CV_PRM_2C_9000 = MAX77960_Reg._CHG_CV_PRM_2C_9000
    CFG_CHG_CV_PRM_2C_9020 = MAX77960_Reg._CHG_CV_PRM_2C_9020
    CFG_CHG_CV_PRM_2C_9040 = MAX77960_Reg._CHG_CV_PRM_2C_9040
    CFG_CHG_CV_PRM_2C_9060 = MAX77960_Reg._CHG_CV_PRM_2C_9060
    CFG_CHG_CV_PRM_2C_9080 = MAX77960_Reg._CHG_CV_PRM_2C_9080
    CFG_CHG_CV_PRM_2C_9100 = MAX77960_Reg._CHG_CV_PRM_2C_9100
    CFG_CHG_CV_PRM_2C_9120 = MAX77960_Reg._CHG_CV_PRM_2C_9120
    CFG_CHG_CV_PRM_2C_9140 = MAX77960_Reg._CHG_CV_PRM_2C_9140
    CFG_CHG_CV_PRM_2C_9160 = MAX77960_Reg._CHG_CV_PRM_2C_9160
    CFG_CHG_CV_PRM_2C_9180 = MAX77960_Reg._CHG_CV_PRM_2C_9180
    CFG_CHG_CV_PRM_2C_9200 = MAX77960_Reg._CHG_CV_PRM_2C_9200
    CFG_CHG_CV_PRM_2C_9220 = MAX77960_Reg._CHG_CV_PRM_2C_9220
    CFG_CHG_CV_PRM_2C_9240 = MAX77960_Reg._CHG_CV_PRM_2C_9240
    CFG_CHG_CV_PRM_2C_9260 = MAX77960_Reg._CHG_CV_PRM_2C_9260
    CFG_CHG_CV_PRM_3C_12000 = MAX77960_Reg._CHG_CV_PRM_3C_12000
    CFG_CHG_CV_PRM_3C_12030 = MAX77960_Reg._CHG_CV_PRM_3C_12030
    CFG_CHG_CV_PRM_3C_12060 = MAX77960_Reg._CHG_CV_PRM_3C_12060
    CFG_CHG_CV_PRM_3C_12090 = MAX77960_Reg._CHG_CV_PRM_3C_12090
    CFG_CHG_CV_PRM_3C_12120 = MAX77960_Reg._CHG_CV_PRM_3C_12120
    CFG_CHG_CV_PRM_3C_12150 = MAX77960_Reg._CHG_CV_PRM_3C_12150
    CFG_CHG_CV_PRM_3C_12180 = MAX77960_Reg._CHG_CV_PRM_3C_12180
    CFG_CHG_CV_PRM_3C_12210 = MAX77960_Reg._CHG_CV_PRM_3C_12210
    CFG_CHG_CV_PRM_3C_12240 = MAX77960_Reg._CHG_CV_PRM_3C_12240
    CFG_CHG_CV_PRM_3C_12270 = MAX77960_Reg._CHG_CV_PRM_3C_12270
    CFG_CHG_CV_PRM_3C_12300 = MAX77960_Reg._CHG_CV_PRM_3C_12300
    CFG_CHG_CV_PRM_3C_12330 = MAX77960_Reg._CHG_CV_PRM_3C_12330
    CFG_CHG_CV_PRM_3C_12360 = MAX77960_Reg._CHG_CV_PRM_3C_12360
    CFG_CHG_CV_PRM_3C_12390 = MAX77960_Reg._CHG_CV_PRM_3C_12390
    CFG_CHG_CV_PRM_3C_12420 = MAX77960_Reg._CHG_CV_PRM_3C_12420
    CFG_CHG_CV_PRM_3C_12450 = MAX77960_Reg._CHG_CV_PRM_3C_12450
    CFG_CHG_CV_PRM_3C_12480 = MAX77960_Reg._CHG_CV_PRM_3C_12480
    CFG_CHG_CV_PRM_3C_12510 = MAX77960_Reg._CHG_CV_PRM_3C_12510
    CFG_CHG_CV_PRM_3C_12540 = MAX77960_Reg._CHG_CV_PRM_3C_12540
    CFG_CHG_CV_PRM_3C_12570 = MAX77960_Reg._CHG_CV_PRM_3C_12570
    CFG_CHG_CV_PRM_3C_12600 = MAX77960_Reg._CHG_CV_PRM_3C_12600
    CFG_CHG_CV_PRM_3C_12630 = MAX77960_Reg._CHG_CV_PRM_3C_12630
    CFG_CHG_CV_PRM_3C_12660 = MAX77960_Reg._CHG_CV_PRM_3C_12660
    CFG_CHG_CV_PRM_3C_12690 = MAX77960_Reg._CHG_CV_PRM_3C_12690
    CFG_CHG_CV_PRM_3C_12720 = MAX77960_Reg._CHG_CV_PRM_3C_12720
    CFG_CHG_CV_PRM_3C_12750 = MAX77960_Reg._CHG_CV_PRM_3C_12750
    CFG_CHG_CV_PRM_3C_12780 = MAX77960_Reg._CHG_CV_PRM_3C_12780
    CFG_CHG_CV_PRM_3C_12810 = MAX77960_Reg._CHG_CV_PRM_3C_12810
    CFG_CHG_CV_PRM_3C_12840 = MAX77960_Reg._CHG_CV_PRM_3C_12840
    CFG_CHG_CV_PRM_3C_12870 = MAX77960_Reg._CHG_CV_PRM_3C_12870
    CFG_CHG_CV_PRM_3C_12900 = MAX77960_Reg._CHG_CV_PRM_3C_12900
    CFG_CHG_CV_PRM_3C_12930 = MAX77960_Reg._CHG_CV_PRM_3C_12930
    CFG_CHG_CV_PRM_3C_12960 = MAX77960_Reg._CHG_CV_PRM_3C_12960
    CFG_CHG_CV_PRM_3C_12990 = MAX77960_Reg._CHG_CV_PRM_3C_12990
    CFG_CHG_CV_PRM_3C_13020 = MAX77960_Reg._CHG_CV_PRM_3C_13020
    CFG_CHG_CV_PRM_3C_13050 = MAX77960_Reg._CHG_CV_PRM_3C_13050
    CFG_CHG_CV_PRM_DEFAULT  = MAX77960_Reg._CHG_CV_PRM_DEFAULT
    CFG_ITRICKLE = 'Charger.Current.Trickle'
    CFG_ITRICKLE_100 = MAX77960_Reg._ITRICKLE_100
    CFG_ITRICKLE_200 = MAX77960_Reg._ITRICKLE_200
    CFG_ITRICKLE_300 = MAX77960_Reg._ITRICKLE_300
    CFG_ITRICKLE_400 = MAX77960_Reg._ITRICKLE_400
    CFG_ITRICKLE_DEFAULT = MAX77960_Reg._ITRICKLE_DEFAULT
    CFG_B2SOVRC = 'Charger.Current.Batt2Sys'
    CFG_B2SOVRC_DISABLED = MAX77960_Reg._B2SOVRC_DISABLED
    CFG_B2SOVRC_3000 = MAX77960_Reg._B2SOVRC_3000
    CFG_B2SOVRC_3500 = MAX77960_Reg._B2SOVRC_3500
    CFG_B2SOVRC_4000 = MAX77960_Reg._B2SOVRC_4000
    CFG_B2SOVRC_4500 = MAX77960_Reg._B2SOVRC_4500
    CFG_B2SOVRC_5000 = MAX77960_Reg._B2SOVRC_5000
    CFG_B2SOVRC_5500 = MAX77960_Reg._B2SOVRC_5500
    CFG_B2SOVRC_6000 = MAX77960_Reg._B2SOVRC_6000
    CFG_B2SOVRC_6500 = MAX77960_Reg._B2SOVRC_6500
    CFG_B2SOVRC_7000 = MAX77960_Reg._B2SOVRC_7000
    CFG_B2SOVRC_7500 = MAX77960_Reg._B2SOVRC_7500
    CFG_B2SOVRC_8000 = MAX77960_Reg._B2SOVRC_8000
    CFG_B2SOVRC_8500 = MAX77960_Reg._B2SOVRC_8500
    CFG_B2SOVRC_9000 = MAX77960_Reg._B2SOVRC_9000
    CFG_B2SOVRC_9500 = MAX77960_Reg._B2SOVRC_9500
    CFG_B2SOVRC_10000= MAX77960_Reg._B2SOVRC_10000
    CFG_B2SOVRC_DEFAULT = MAX77960_Reg._B2SOVRC_DEFAULT
    CFG_JEITA_EN = 'Charger.Jeita'
    CFG_JEITA_EN_ON  = MAX77960_Reg._JEITA_EN_ON
    CFG_JEITA_EN_OFF = MAX77960_Reg._JEITA_EN_OFF
    CFG_JEITA_EN_DEFAULT = MAX77960_Reg._JEITA_EN_DEFAULT
    CFG_REGTEMP = 'Charger.Temp.Reg'
    CFG_REGTEMP_85  = MAX77960_Reg._REGTEMP_85
    CFG_REGTEMP_90  = MAX77960_Reg._REGTEMP_90
    CFG_REGTEMP_95  = MAX77960_Reg._REGTEMP_95
    CFG_REGTEMP_100 = MAX77960_Reg._REGTEMP_100
    CFG_REGTEMP_105 = MAX77960_Reg._REGTEMP_105
    CFG_REGTEMP_110 = MAX77960_Reg._REGTEMP_110
    CFG_REGTEMP_115 = MAX77960_Reg._REGTEMP_115
    CFG_REGTEMP_120 = MAX77960_Reg._REGTEMP_120
    CFG_REGTEMP_125 = MAX77960_Reg._REGTEMP_125
    CFG_REGTEMP_130 = MAX77960_Reg._REGTEMP_130
    CFG_REGTEMP_DEFAULT = MAX77960_Reg._REGTEMP_DEFAULT
    CFG_VCHGCV_COOL = 'Charger.Voltage.Jeita.Term'
    CFG_VCHGCV_COOL_NORMAL  = MAX77960_Reg._VCHGCV_COOL_NORMAL
    CFG_VCHGCV_COOL_REDUCED = MAX77960_Reg._VCHGCV_COOL_REDUCED
    CFG_VCHGCV_COOL_DEFAULT = MAX77960_Reg._VCHGCV_COOL_DEFAULT
    CFG_ICHGCC_COOL = 'Charger.Current.Jeita.FastCharge'
    CFG_ICHGCC_COOL_NORMAL  = MAX77960_Reg._ICHGCC_COOL_NORMAL
    CFG_ICHGCC_COOL_REDUCED = MAX77960_Reg._ICHGCC_COOL_REDUCED
    CFG_ICHGCC_COOL_DEFAULT = MAX77960_Reg._ICHGCC_COOL_DEFAULT
    CFG_CHGIN_ILIM = 'Charger.Current.Input'
    CFG_CHGIN_ILIM_DEFAULT = MAX77960_Reg._CHGIN_ILIM_DEFAULT_VALUE
    CFG_OTG_ILIM = 'Charger.Current.OTG'
    CFG_OTG_ILIM_500 = MAX77960_Reg._OTG_ILIM_500
    CFG_OTG_ILIM_900 = MAX77960_Reg._OTG_ILIM_900
    CFG_OTG_ILIM_1200= MAX77960_Reg._OTG_ILIM_1200
    CFG_OTG_ILIM_1500= MAX77960_Reg._OTG_ILIM_1500
    CFG_OTG_ILIM_2000= MAX77960_Reg._OTG_ILIM_2000
    CFG_OTG_ILIM_2250= MAX77960_Reg._OTG_ILIM_2250
    CFG_OTG_ILIM_2500= MAX77960_Reg._OTG_ILIM_2500
    CFG_OTG_ILIM_3000= MAX77960_Reg._OTG_ILIM_3000
    CFG_OTG_ILIM_DEFAULT = MAX77960_Reg._OTG_ILIM_DEFAULT
    CFG_MINVSYS = 'Charger.Voltage.MinVSys'
    CFG_MINVSYS_2C_5535 = MAX77960_Reg._MINVSYS_2C_5535
    CFG_MINVSYS_2C_5740 = MAX77960_Reg._MINVSYS_2C_5740
    CFG_MINVSYS_2C_5945 = MAX77960_Reg._MINVSYS_2C_5945
    CFG_MINVSYS_2C_6150 = MAX77960_Reg._MINVSYS_2C_6150
    CFG_MINVSYS_2C_6355 = MAX77960_Reg._MINVSYS_2C_6355
    CFG_MINVSYS_2C_6560 = MAX77960_Reg._MINVSYS_2C_6560
    CFG_MINVSYS_2C_6765 = MAX77960_Reg._MINVSYS_2C_6765
    CFG_MINVSYS_2C_6970 = MAX77960_Reg._MINVSYS_2C_6970
    CFG_MINVSYS_3C_8303 = MAX77960_Reg._MINVSYS_3C_8303
    CFG_MINVSYS_3C_8610 = MAX77960_Reg._MINVSYS_3C_8610
    CFG_MINVSYS_3C_8918 = MAX77960_Reg._MINVSYS_3C_8918
    CFG_MINVSYS_3C_9225 = MAX77960_Reg._MINVSYS_3C_9225
    CFG_MINVSYS_3C_9533 = MAX77960_Reg._MINVSYS_3C_9533
    CFG_MINVSYS_3C_9840 = MAX77960_Reg._MINVSYS_3C_9840
    CFG_MINVSYS_3C_10148= MAX77960_Reg._MINVSYS_3C_10148
    CFG_MINVSYS_3C_10455= MAX77960_Reg._MINVSYS_3C_10455
    CFG_MINVSYS_DEFAULT = MAX77960_Reg._MINVSYS_DEFAULT
    CFG_VCHGIN_REG = 'Charger.Voltage.ChargeIn'
    CFG_VCHGIN_REG_4025 = MAX77960_Reg._VCHGIN_REG_4025
    CFG_VCHGIN_REG_4200 = MAX77960_Reg._VCHGIN_REG_4200
    CFG_VCHGIN_REG_4375 = MAX77960_Reg._VCHGIN_REG_4375
    CFG_VCHGIN_REG_4550 = MAX77960_Reg._VCHGIN_REG_4550
    CFG_VCHGIN_REG_4725 = MAX77960_Reg._VCHGIN_REG_4725
    CFG_VCHGIN_REG_4900 = MAX77960_Reg._VCHGIN_REG_4900
    CFG_VCHGIN_REG_5425 = MAX77960_Reg._VCHGIN_REG_5425
    CFG_VCHGIN_REG_5950 = MAX77960_Reg._VCHGIN_REG_5950
    CFG_VCHGIN_REG_6475 = MAX77960_Reg._VCHGIN_REG_6475
    CFG_VCHGIN_REG_7000 = MAX77960_Reg._VCHGIN_REG_7000
    CFG_VCHGIN_REG_7525 = MAX77960_Reg._VCHGIN_REG_7525
    CFG_VCHGIN_REG_8050 = MAX77960_Reg._VCHGIN_REG_8050
    CFG_VCHGIN_REG_8575 = MAX77960_Reg._VCHGIN_REG_8575
    CFG_VCHGIN_REG_9100 = MAX77960_Reg._VCHGIN_REG_9100
    CFG_VCHGIN_REG_9625 = MAX77960_Reg._VCHGIN_REG_9625
    CFG_VCHGIN_REG_10150 = MAX77960_Reg._VCHGIN_REG_10150
    CFG_VCHGIN_REG_10675 = MAX77960_Reg._VCHGIN_REG_10675
    CFG_VCHGIN_REG_10950 = MAX77960_Reg._VCHGIN_REG_10950
    CFG_VCHGIN_REG_11550 = MAX77960_Reg._VCHGIN_REG_11550
    CFG_VCHGIN_REG_12150 = MAX77960_Reg._VCHGIN_REG_12150
    CFG_VCHGIN_REG_12750 = MAX77960_Reg._VCHGIN_REG_12750
    CFG_VCHGIN_REG_13350 = MAX77960_Reg._VCHGIN_REG_13350
    CFG_VCHGIN_REG_13950 = MAX77960_Reg._VCHGIN_REG_13950
    CFG_VCHGIN_REG_14550 = MAX77960_Reg._VCHGIN_REG_14550
    CFG_VCHGIN_REG_15150 = MAX77960_Reg._VCHGIN_REG_15150
    CFG_VCHGIN_REG_15750 = MAX77960_Reg._VCHGIN_REG_15750
    CFG_VCHGIN_REG_16350 = MAX77960_Reg._VCHGIN_REG_16350
    CFG_VCHGIN_REG_16950 = MAX77960_Reg._VCHGIN_REG_16950
    CFG_VCHGIN_REG_17550 = MAX77960_Reg._VCHGIN_REG_17550
    CFG_VCHGIN_REG_18150 = MAX77960_Reg._VCHGIN_REG_18150
    CFG_VCHGIN_REG_18750 = MAX77960_Reg._VCHGIN_REG_18750
    CFG_VCHGIN_REG_19050 = MAX77960_Reg._VCHGIN_REG_19050
    CFG_VCHGIN_REG_DEFAULT = MAX77960_Reg._VCHGIN_REG_DEFAULT

    _CONFIGURABLES = {
        CFG_COMM_MODE   : CFG_COMM_MODE_DEFAULT,
        CFG_DISIBS      : CFG_DISIBS_DEFAULT,
        CFG_MODE        : CFG_MODE_DEFAULT,
        CFG_PQEN        : CFG_PQEN_DEFAULT,
        CFG_CHG_RSTRT   : CFG_CHG_RSTRT_DEFAULT,
        CFG_STAT_EN     : CFG_STAT_EN_DEFAULT,
        CFG_FCHGTIME    : CFG_FCHGTIME_DEFAULT,
        CFG_CHGCC       : CFG_CHGCC_DEFAULT,
        CFG_TO_TIME     : CFG_TO_TIME_DEFAULT,
        CFG_TO_ITH      : CFG_TO_ITH_DEFAULT,
        CFG_CHG_CV_PRM  : CFG_CHG_CV_PRM_DEFAULT,
        CFG_ITRICKLE    : CFG_ITRICKLE_DEFAULT,
        CFG_B2SOVRC     : CFG_B2SOVRC_DEFAULT,
        #skip config register 06
        CFG_JEITA_EN    : CFG_JEITA_EN_DEFAULT,
        CFG_REGTEMP     : CFG_REGTEMP_DEFAULT,
        CFG_VCHGCV_COOL : CFG_VCHGCV_COOL_DEFAULT,
        CFG_ICHGCC_COOL : CFG_ICHGCC_COOL_DEFAULT,
        CFG_CHGIN_ILIM  : CFG_CHGIN_ILIM_DEFAULT,
        CFG_OTG_ILIM    : CFG_OTG_ILIM_DEFAULT,
        CFG_MINVSYS     : CFG_MINVSYS_DEFAULT,
        CFG_VCHGIN_REG  : CFG_VCHGIN_REG_DEFAULT,
    }
    
    def __init__( self ):
        # Specific instance attributes
        self.pinInt = None
        # Call constructors of the super class
        super().__init__()

    #
    # Helper functions
    #
    
    def checkID(self):
        """Reads the chip ID and verifies it against the expected value.
        """
        info, err = self.getInfo()
        if (err == ErrorCode.errOk):
            if (info.revMajor < MAX77960._CID_REV_MIN) or \
               (info.revMajor > MAX77960._CID_REV_MAX):
                err = ErrorCode.errSpecRange
        return err
    
    def _lockRegisters(self):
        self.writeByteRegister( MAX77960._REG_CHG_CNFG_06, MAX77960._CHGPROT_LOCK | MAX77960._WDTCLR_DO_NOT_TOUCH )

    def _unlockRegisters(self):
        self.writeByteRegister( MAX77960._REG_CHG_CNFG_06, MAX77960._CHGPROT_UNLOCK | MAX77960._WDTCLR_DO_NOT_TOUCH )


    #
    # Module API
    #

    @classmethod
    def Params_init(cls, paramDict):
        """Initializes configuration parameters with defaults.
        
        The following settings are supported:
        
        =================================    ==========================================================================================================
        Key name                             Value type, meaning and default
        =================================    ==========================================================================================================
        SerialBusDevice.deviceAddress        ``int`` I2C serial device address; default is :attr:`ADDRESSES_ALLOWED` [0].
        Charger.Comm.Mode                    ``int`` Communication mode; default is :attr:`.CFG_COMM_MODE_DEFAULT`.
        Charger.DisIBS                       ``int`` ; default is :attr:`.CFG_DISIBS_DEFAULT`.
        Charger.Mode                         ``int`` ; default is :attr:`.CFG_MODE_DEFAULT`.
        Charger.Prequal                      ``int`` ; default is :attr:`.CFG_PQEN_DEFAULT`.
        Charger.Restart                      ``int`` ; default is :attr:`.CFG_CHG_RSTRT_DEFAULT`.
        Charger.Stat                         ``int`` ; default is :attr:`.CFG_STAT_EN_DEFAULT`.
        Charger.Timer.FastCharge             ``int`` ; default is :attr:`.CFG_FCHGTIME_DEFAULT`.
        Charger.Current.FastCharge           ``int`` ; default is :attr:`.CFG_CHGCC_DEFAULT`.
        Charger.Timer.Topoff                 ``int`` ; default is :attr:`.CFG_TO_TIME_DEFAULT`.
        Charger.Current.Topoff               ``int`` ; default is :attr:`.CFG_TO_ITH_DEFAULT`.
        Charger.Voltage.ChargeTermination    ``int`` ; default is :attr:`.CFG_CHG_CV_PRM_DEFAULT`.
        Charger.Current.Trickle              ``int`` ; default is :attr:`.CFG_ITRICKLE_DEFAULT`.
        Charger.Current.Batt2Sys             ``int`` ; default is :attr:`.CFG_B2SOVRC_DEFAULT`.
        Charger.Jeita                        ``int`` ; default is :attr:`.CFG_JEITA_EN_DEFAULT`.
        Charger.Temp.Reg                     ``int`` ; default is :attr:`.CFG_REGTEMP_DEFAULT`.
        Charger.Voltage.Jeita.Term           ``int`` ; default is :attr:`.CFG_VCHGCV_COOL_DEFAULT`.
        Charger.Current.Jeita.FastCharge     ``int`` ; default is :attr:`.CFG_ICHGCC_COOL_DEFAULT`.
        Charger.Current.Input                ``int`` ; default is :attr:`.CFG_CHGIN_ILIM_DEFAULT`.
        Charger.Current.OTG                  ``int`` ; default is :attr:`.CFG_OTG_ILIM_DEFAULT`.
        Charger.Voltage.MinVSys              ``int`` ; default is :attr:`.CFG_MINVSYS_DEFAULT`.
        Charger.Voltage.ChargeIn             ``int`` ; default is :attr:`.CFG_VCHGIN_REG_DEFAULT`.
        All MAX77960.int.gpio.* settings as documented at :meth:`.GPIO.Params_init`.
        ===============================================================================================================================================
        
        Also see: :meth:`.Charger.Params_init`, :meth:`.SerialBusDevice.Params_init`, :meth:`.GPIO.Params_init`. 
        """
        # Override default base class parameter: serial bus device address
        paramDict["SerialBusDevice.deviceAddress"] = MAX77960.ADRESSES_ALLOWED[0]
        # Add charger configurables
        for key in MAX77960._CONFIGURABLES:
            if not key in paramDict:
                paramDict[key] = MAX77960._CONFIGURABLES[key]
        # Add interrupt pin /gpio specifics
        paramDict["MAX77960.int.gpio.direction"] = GPIO.DIRECTION_IN
        if not ("MAX77960.int.gpio.trigger" in paramDict):
            paramDict["MAX77960.int.gpio.trigger"] = GPIO.TRIGGER_EDGE_FALLING
        if not ("MAX77960.int.gpio.bounce" in paramDict):
            paramDict["MAX77960.int.gpio.bounce"] = GPIO.BOUNCE_NONE
        gpioParams = {}
        GPIO.Params_init( gpioParams )
        gp = dict( [("MAX77960.int."+k,v) for k,v in gpioParams.items()] )
        for key, value in gp.items():
            if not( key in paramDict):
                paramDict[key] = value
        # Let the base class(es) do the rest
        super().Params_init(paramDict)
        return None


    def open(self, paramDict):
        # Open the bus device
        paramDict["SerialBusDevice.deviceAddress"] = MAX77960.ADRESSES_ALLOWED[0]
        ret = SerialBusDevice.open(self, paramDict)
        # Configure the sensor
        if (ret == ErrorCode.errOk):
            # Note that config registers #1, 2, 3, 4, 5, 7, 8, 9
            # are write protected (locked), while #0, 6, 10 are not.
            reg= [MAX77960._REG_CHG_CNFG_00, MAX77960._REG_CHG_CNFG_01,
                  MAX77960._REG_CHG_CNFG_02, MAX77960._REG_CHG_CNFG_03,
                  MAX77960._REG_CHG_CNFG_04, MAX77960._REG_CHG_CNFG_05,
                  MAX77960._REG_CHG_CNFG_06, MAX77960._REG_CHG_CNFG_07,
                  MAX77960._REG_CHG_CNFG_08, MAX77960._REG_CHG_CNFG_09,
                  MAX77960._REG_CHG_CNFG_10]
            mask=[ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            data=[ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            for key in paramDict:
                if (key in MAX77960._CONFIGURABLES) and \
                   (paramDict[key] != MAX77960._CONFIGURABLES[key]):
                    value = paramDict[key]
                    if key==MAX77960.CFG_COMM_MODE:
                        mask[0] |= MAX77960._COMM_MODE
                        data[0] |= value
                    if key==MAX77960.CFG_DISIBS:
                        mask[0] |= MAX77960._DISIBS
                        data[0] |= value
                    if key==MAX77960.CFG_MODE:
                        mask[0] |= MAX77960._MODE
                        data[0] |= value
                    if key==MAX77960.CFG_PQEN:
                        mask[1] |= MAX77960._PQEN
                        data[1] |= value
                    if key==MAX77960.CFG_CHG_RSTRT:
                        mask[1] |= MAX77960._CHG_RSTRT
                        data[1] |= value
                    if key==MAX77960.CFG_STAT_EN:
                        mask[1] |= MAX77960._STAT_EN
                        data[1] |= value
                    if key==MAX77960.CFG_FCHGTIME:
                        mask[1] |= MAX77960._FCHGTIME
                        data[1] |= value
                    if key==MAX77960.CFG_CHGCC:
                        mask[2] = MAX77960._CHGCC
                        data[2] = value
                    if key==MAX77960.CFG_TO_TIME:
                        mask[3] |= MAX77960._TO_TIME
                        data[3] |= value
                    if key==MAX77960.CFG_TO_ITH:
                        mask[3] |= MAX77960._TO_ITH
                        data[3] |= value
                    if key==MAX77960.CFG_CHG_CV_PRM:
                        mask[4] = MAX77960._CHG_CV_PRM
                        data[4] = value
                    if key==MAX77960.CFG_ITRICKLE:
                        mask[5] |= MAX77960._ITRICKLE
                        data[5] |= value
                    if key==MAX77960.CFG_B2SOVRC:
                        mask[5] |= MAX77960._B2SOVRC
                        data[5] |= value
                    if key==MAX77960.CFG_JEITA_EN:
                        mask[7] |= MAX77960._JEITA_EN
                        data[7] |= value
                    if key==MAX77960.CFG_REGTEMP:
                        mask[7] |= MAX77960._REGTEMP
                        data[7] |= value
                    if key==MAX77960.CFG_VCHGCV_COOL:
                        mask[7] |= MAX77960._VCHGCV_COOL
                        data[7] |= value
                    if key==MAX77960.CFG_ICHGCC_COOL:
                        mask[7] |= MAX77960._ICHGCC_COOL
                        data[7] |= value
                    if key==MAX77960.CFG_CHGIN_ILIM:
                        mask[8] = MAX77960._CHGIN_ILIM
                        if value < 100:
                            data[8] = MAX77960._CHGIN_ILIM_100
                        elif value > 6300:
                            data[8] = MAX77960._CHGIN_ILIM_6300
                        else:
                            data[8] = value // 50 + 1
                    if key==MAX77960.CFG_OTG_ILIM:
                        mask[9] |= MAX77960._OTG_ILIM
                        data[9] |= value
                    if key==MAX77960.CFG_MINVSYS:
                        mask[9] |= MAX77960._MINVSYS
                        data[9] |= value
                    if key==MAX77960.CFG_VCHGIN_REG:
                        mask[10] |= MAX77960._VCHGIN_REG
                        data[10] |= value
        
            self._unlockRegisters()
            for idx in range( len( reg ) ):
                if mask[idx] != 0:
                    # Copy masked bits to the register content
                    value, _ = self.readByteRegister( reg[idx] )
                    value = value & ~mask[idx]
                    value = value | data[idx]
                    ret = self.writeByteRegister(reg[idx], value)
            self._lockRegisters()
        # Setup interrupt related stuff.
        if (ret == ErrorCode.errOk):
            if ("MAX77960.int.gpio.pinDesignator" in paramDict):
                paramDict["MAX77960.int.gpio.direction"] = GPIO.DIRECTION_IN
                gpioParams = dict( [(k.replace("MAX77960.int.", ""),v) for k,v in paramDict.items() if k.startswith("MAX77960.int.")] )
                self.pinInt = GPIO()
                ret = self.pinInt.open( gpioParams )
                self.enableInterrupt()
        return ret


    def close(self):
        if not (self.pinInt is None):
            self.pinInt.close()
            self.pinInt = None
        ret = super().close()
        return ret

    def setRunLevel(self, level):
        ret = ErrorCode.errOk
        if (level <= RunLevel.snooze):
            data, ret = self.readByteRegister( MAX77960._REG_CHG_CNFG_00 )
            if (ret == ErrorCode.errOk):
                data &= ~MAX77960._STBY_EN
                ret = self.writeByteRegister( MAX77960._REG_CHG_CNFG_00, data )
        else:
            data, ret = self.readByteRegister( MAX77960._REG_CHG_CNFG_00 )
            if (ret == ErrorCode.errOk):
                data |= MAX77960._STBY_EN
                ret = self.writeByteRegister( MAX77960._REG_CHG_CNFG_00, data )
        return ret

    #
    # Charger API
    #
    
    def reset(self):
        err = self.writeByteRegister(MAX77960._REG_SWRST, MAX77960._SWRST_TYPE_O)
        return err

    def getInfo(self):
        info = Info()
        # Chip ID, silicon revision and OTP recipe version
        info.chipID, ret = self.readByteRegister(MAX77960.REG_CID)
        if (ret == ErrorCode.errOk):
            # Get silicon revision from the same register
            info.revMajor = (info.chipID & MAX77960._CID_REVISION) >> 5
            info.revMinor = info.chipID & MAX77960._CID_VERSION
            info.validity = info.validChipID \
                            | info.validRevMajor | info.validRevMinor
        return info, ret

    def isBatteryPresent(self):
        data, ret = self.readByteRegister( MAX77960._REG_CHG_DETAILS_01 )
        if (ret == ErrorCode.errOk):
            data = data & MAX77960._BAT_DTLS
            if (data == MAX77960._BAT_DTLS_REMOVAL):
                ret = ErrorCode.errUnavailable
        elif (ret == ErrorCode.errUnavailable):
            ret = ErrorCode.errMalfunction
        return ret
    
    def getNumCells(self):
        ret = -1
        data, err = self.readByteRegister( MAX77960._REG_CHG_DETAILS_02 )
        if (err == ErrorCode.errOk):
            data = data & MAX77960._NUM_CELL_DTLS
            if data == MAX77960._NUM_CELL_DTLS_3:
                ret = 3
            else:
                ret = 2
        return ret
    
    def getBatStatus(self):
        ret = BatStatus.unknown
        data, err = self.readByteRegister( MAX77960._REG_CHG_DETAILS_01 )
        if (err == ErrorCode.errOk):
            ds = data & MAX77960._BAT_DTLS
            if ds == MAX77960._BAT_DTLS_REMOVAL:
                ret = BatStatus.removed
            elif ds == MAX77960._BAT_DTLS_BELOW_PREQ:
                ret = BatStatus.empty
            elif ds == MAX77960._BAT_DTLS_TIME_OUT:
                ret = BatStatus.broken
            elif ds == MAX77960._BAT_DTLS_OK:
                ret = BatStatus.normal
            elif ds == MAX77960._BAT_DTLS_LOW_VOLT:
                ret = BatStatus.low
            elif ds == MAX77960._BAT_DTLS_OVR_VOLT:
                ret = BatStatus.overvoltage
            elif ds == MAX77960._BAT_DTLS_OVR_CURR:
                ret = BatStatus.overcurrent
        return ret
    
    def getChgStatus(self):
        ret = ChgStatus.unknown
        data, err = self.readByteRegister( MAX77960._REG_CHG_DETAILS_01 )
        if (err == ErrorCode.errOk):
            cd = data & MAX77960._CHG_DTLS
            if cd == MAX77960._CHG_DTLS_PRECHRG:
                bd = data & MAX77960._BAT_DTLS
                if bd == MAX77960._BAT_DTLS_BELOW_PREQ:
                    ret = ChgStatus.preCharge
                else:
                    ret = ChgStatus.trickle
            elif cd == MAX77960._CHG_DTLS_FAST_CURR:
                ret = ChgStatus.fastChargeConstCurrent
            elif cd == MAX77960._CHG_DTLS_FAST_VOLT:
                ret = ChgStatus.fastChargeConstVoltage
            elif cd == MAX77960._CHG_DTLS_TOP_OFF:
                ret = ChgStatus.topOff
            elif cd == MAX77960._CHG_DTLS_DONE:
                ret = ChgStatus.done
            else:
                ret = ChgStatus.off
        return ret
    
    def getDCStatus(self):
        ret = DCStatus.unknown
        data, err = self.readByteRegister( MAX77960._REG_CHG_DETAILS_00 )
        if (err == ErrorCode.errOk):
            ds = data & MAX77960._CHGIN_DTLS
            if ds == MAX77960._CHGIN_DTLS_GOOD:
                ret = DCStatus.valid
            elif ds == MAX77960._CHGIN_DTLS_TOO_LOW:
                ret = DCStatus.undervoltage
            elif ds == MAX77960._CHGIN_DTLS_TOO_HIGH:
                ret = DCStatus.overvoltage
        return ret
      
    def getPowerSrc(self):
        ret = PowerSrc.unknown
        data, err = self.readByteRegister( MAX77960._REG_CHG_DETAILS_00 )
        if (err == ErrorCode.errOk):
            chgin = data & MAX77960._CHGIN_DTLS
            qbat = data & MAX77960._QB_DTLS
            if (chgin == MAX77960._CHGIN_DTLS_GOOD):
                # Valid CHGIN, so external power is the primary source
                ret |= PowerSrc.dc
            if (qbat == MAX77960._QB_DTLS_ON):
                ret |= PowerSrc.bat
        return ret

    def getChargerTempStatus(self):
        ret = TemperatureRating.unknown
        data, err = self.readByteRegister( MAX77960._REG_CHG_DETAILS_01 )
        if (err == ErrorCode.errOk):
            chg = data & MAX77960._CHG_DTLS
            if chg == MAX77960._CHG_DTLS_OFF_TEMP:
                ret = TemperatureRating.hot
            else:
                treg = data & MAX77960._TREG
                if (treg == MAX77960._TREG_HIGH):
                    ret = TemperatureRating.warm
                else:
                    ret = TemperatureRating.ok
        return ret

    def getBatteryTempStatus(self):
        ret = TemperatureRating.unknown
        data, err = self.readByteRegister( MAX77960._REG_CHG_DETAILS_02 )
        if (err == ErrorCode.errOk):
            thm = data & MAX77960._THM_DTLS
            if thm == MAX77960._THM_DTLS_COLD:
                ret = TemperatureRating.cold
            elif thm == MAX77960._THM_DTLS_COOL:
                ret = TemperatureRating.cool
            elif thm == MAX77960._THM_DTLS_NORMAL:
                ret = TemperatureRating.ok
            elif thm == MAX77960._THM_DTLS_WARM:
                ret = TemperatureRating.warm
            elif thm == MAX77960._THM_DTLS_HOT:
                ret = TemperatureRating.hot
            else:   # Battery removed or temperature monitoring disabled.
                ret = TemperatureRating.unknown
        return ret

    def getError(self):
        ret = ChargerError.unknown
        data, err = self.readByteRegister( MAX77960._REG_CHG_DETAILS_01 )
        if (err == ErrorCode.errOk):
            chg = data & MAX77960._CHG_DTLS
            if chg == MAX77960._CHG_DTLS_OFF_RESIST:
                ret = ChargerError.config
            elif chg == MAX77960._CHG_DTLS_E_TIMER:
                ret = ChargerError.timer
            elif chg == MAX77960._CHG_DTLS_SUSP_QBAT:
                ret = ChargerError.batBroken
            elif chg == MAX77960._CHG_DTLS_OFF_CHGIN:
                data, err = self.readByteRegister( MAX77960._REG_CHG_DETAILS_00 )
                if (err == ErrorCode.errOk):
                    chgin = data & MAX77960._CHG_DTLS
                    if chgin == MAX77960._CHGIN_DTLS_TOO_HIGH:
                        ret = ChargerError.dcHigh
                    elif chgin == MAX77960._CHGIN_DTLS_TOO_LOW:
                        ret = ChargerError.dcLow
                    else:
                        ret = ChargerError.dc
            elif chg == MAX77960._CHG_DTLS_OFF_TEMP:
                ret = ChargerError.tempChg
            elif chg == MAX77960._CHG_DTLS_OFF_WDOG:
                ret = ChargerError.config
            elif chg == MAX77960._CHG_DTLS_SUSP_JEITA:
                ret = ChargerError.tempBat
            elif chg == MAX77960._CHG_DTLS_SUSP_NOBAT:
                ret = ChargerError.batRemoved
            else:
                ret = ChargerError.ok
        return ret

    def restartCharging(self):
        # To recover from timer fault, switch charger off...
        data = MAX77960._COMM_MODE_I2C | MAX77960._DISIBS_FET_PPSM | \
               MAX77960._STBY_EN_DCDC_PPSM | MAX77960._WDTEN_OFF 
        ret = self.writeByteRegister( MAX77960._REG_CHG_CNFG_00,
                                      data | MAX77960._MODE_DCDC_ONLY )
        # ... and on again.
        if (ret == ErrorCode.errOk):
            ret = self.writeByteRegister( MAX77960._REG_CHG_CNFG_00,
                                          data | MAX77960._MODE_CHRG_DCDC )
        return ret

    #
    # Interruptable API
    #
    
    def registerInterruptHandler(self, onEvent=None, callerFeedBack=None, handler=None ):
        ret = ErrorCode.errOk
        if ((onEvent == Event.evtInt1) or (onEvent == Event.evtAny)) and not (self.pinInt is None):
            self.pinInt.registerInterruptHandler( GPIO.EVENT_DEFAULT, callerFeedBack, handler )
            ret = self.enableInterrupt()
        else:
            ret = ErrorCode.errExhausted
        return ret
        
    def _mapIntApi2Impl( self, apiMask ):
        """Maps API :class:`.charger.EventSource` to the \
        implementation-level interrupts as follows:
        
            REG_TOP_INT: :attr:`.MAX7760._TSHDN_I`      <-> :attr:`.charger.EventSource.thermalShutdown`
            REG_TOP_INT: :attr:`.MAX7760._SYSOVLO_I`    <-> :attr:`.charger.EventSource.systemOvervoltage`
            REG_TOP_INT: :attr:`.MAX7760._SYSUVLO_I`    <-> :attr:`.charger.EventSource.systemUndervoltage`
            REG_CHG_INT: :attr:`.MAX7760._AICL_I`       <-> :attr:`.charger.EventSource.inputCurrentLimitSrc`
            REG_CHG_INT: :attr:`.MAX7760._CHGIN_I`      <-> :attr:`.charger.EventSource.inputVoltage`
            REG_CHG_INT: :attr:`.MAX7760._B2SOVRC_I`    <-> :attr:`.charger.EventSource.batteryOvercurrent`
            REG_CHG_INT: :attr:`.MAX7760._CHG_I`        <-> :attr:`.charger.EventSource.chargingPhase`
            REG_CHG_INT: :attr:`.MAX7760._BAT_I`        <-> :attr:`.charger.EventSource.batteryTemperature`
            REG_CHG_INT: :attr:`.MAX7760._CHGINLIM_I`   <-> :attr:`.charger.EventSource.inputCurrentLimitOwn`
            REG_CHG_INT: :attr:`.MAX7760._DISQBAT_I`    <-> :attr:`.charger.EventSource.onOff`
            REG_CHG_INT: :attr:`.MAX7760._OTG_PLIM_I`   <-> :attr:`.charger.EventSource.internal`
            
        """
        topMask = 0
        chgMask = 0
        
        if (apiMask & EventSource.thermalShutdown):
            topMask = topMask | MAX77960._TSHDN_M
        if (apiMask & EventSource.systemOvervoltage):
            topMask = topMask | MAX77960._SYSOVLO_M
        if (apiMask & EventSource.systemUndervoltage):
            topMask = topMask | MAX77960._SYSUVLO_M

        if (apiMask & EventSource.inputCurrentLimitSrc):
            chgMask = chgMask | MAX77960._AICL_M
        if (apiMask & EventSource.inputVoltage):
            chgMask = chgMask | MAX77960._CHGIN_M
        if (apiMask & EventSource.batteryOvercurrent):
            chgMask = chgMask | MAX77960._B2SOVRC_M
        if (apiMask & EventSource.chargingPhase):
            chgMask = chgMask | MAX77960._CHG_M
        if (apiMask & EventSource.batteryTemperature):
            chgMask = chgMask | MAX77960._BAT_M
        if (apiMask & EventSource.inputCurrentLimitOwn):
            chgMask = chgMask | MAX77960._CHGINLIM_M
        if (apiMask & EventSource.onOff):
            chgMask = chgMask | MAX77960._DISQBAT_M
        if (apiMask & EventSource.internal):
            chgMask = chgMask | MAX77960._OTG_PLIM_M
        return [topMask, chgMask]
            
        
    def _mapIntImpl2Api( self, topMask, chgMask ):
        """Maps implementation-level interrupts to API event sources.
        
        For the detailed mapping, see :meth:`_mapIntApi2Impl`.
        """
        intMask = EventSource.none
        if (topMask & MAX77960._TSHDN_M):
            intMask = intMask | EventSource.thermalShutdown
        if (topMask & MAX77960._SYSOVLO_M):
            intMask = intMask | EventSource.systemOvervoltage
        if (topMask & MAX77960._SYSUVLO_M):
            intMask = intMask | EventSource.systemUndervoltage
        
        if (chgMask & MAX77960._AICL_M):
            intMask = intMask | EventSource.inputCurrentLimitSrc
        if (chgMask & MAX77960._CHGIN_M):
            intMask = intMask | EventSource.inputVoltage
        if (chgMask & MAX77960._B2SOVRC_M):
            intMask = intMask | EventSource.batteryOvercurrent
        if (chgMask & MAX77960._CHG_M):
            intMask = intMask | EventSource.chargingPhase
        if (chgMask & MAX77960._BAT_M):
            intMask = intMask | EventSource.batteryTemperature
        if (chgMask & MAX77960._CHGINLIM_M):
            intMask = intMask | EventSource.inputCurrentLimitOwn
        if (chgMask & MAX77960._DISQBAT_M):
            intMask = intMask | EventSource.onOff
        if (chgMask & MAX77960._OTG_PLIM_M):
            intMask = intMask | EventSource.internal
        return intMask

    def enableInterrupt(self):
        return ErrorCode.errOk

    def disableInterrupt(self):
        return ErrorCode.errOk

    def getEventContext(self, event, context):
        """Retrieve more detailed information on an event.
        
        The ``event`` parameter should be :attr:`.interruptable.Event.evtInt1`,
        as there is only this one interrupt line.
        On return, the ``context`` parameter carries the resulting
        information. It must be an instance of :class:`.charger.EventContext`,
        which is semantically multiplexed by its :attr:`.charger.EventContext.source`
        attribute. 
        
        Also see: :meth:`.Interruptable.getEventContext`.

        :param int event: The original event occurred.
        :param .charger.EventContext context: Context information. 
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        
        if (context is None):
            ret = ErrorCode.errInvalidParameter
        elif( not self.isAttached() ):
            ret = ErrorCode.errResourceConflict
        elif( event == Event.evtNone ):
            ret = ErrorCode.errFewData
        elif ((event == Event.evtInt1) or (event == Event.evtAny)):
            ret = ErrorCode.errOk
            # Retrieving the interrupt status resets all bits in these registers!
            if( context.control == EventContextControl.evtCtxtCtrl_clearAll ):
                _, ret = self.readByteRegister( MAX77960._REG_TOP_INT )
                _, ret = self.readByteRegister( MAX77960._REG_CHG_INT )
                context.remainInt = 0;
                context.source = EventSource.none
            else:
                if (context.control == EventContextControl.evtCtxtCtrl_getFirst):
                    topStatus, ret = self.readByteRegister( MAX77960._REG_TOP_INT )
                    chgStatus, ret = self.readByteRegister( MAX77960._REG_CHG_INT )
                    context.remainInt = self._mapIntImpl2Api( topStatus, chgStatus )
                    context.control = EventContextControl.evtCtxtCtrl_getNext
                elif (context.control == EventContextControl.evtCtxtCtrl_getLast):
                    topStatus, ret = self.readByteRegister( MAX77960._REG_TOP_INT )
                    chgStatus, ret = self.readByteRegister( MAX77960._REG_CHG_INT )
                    context.remainInt = self._mapIntImpl2Api( topStatus, chgStatus )
                    context.control = EventContextControl.evtCtxtCtrl_getPrevious
                if (ret == ErrorCode.errOk):
                    if (context.remainInt == 0):
                        ret = ErrorCode.errFewData
                    else:
                        if (context.control == EventContextControl.evtCtxtCtrl_getNext):
                            # Find value of highest bit:
                            context.source = imath.iprevpowtwo( context.remainInt )
                        else:
                            # Find (value of) least bit set:
                            context.source = imath.vlbs( context.remainInt )
                        context.remainInt &= ~context.source
                        if ((ret == ErrorCode.errOk) and (context.remainInt != 0) ):
                            ret = ErrorCode.errMoreData
        else:
            ret = ErrorCode.errInvalidParameter
        return ret
    
    #
    # Configurable API
    #
    
    def configure(self, configData):
        ret = ErrorCode.errNotSupported
        if (configData.type == ConfigItem.eventArm):
            # Clear current interrupts
            self.readByteRegister( MAX77960._REG_TOP_INT )
            self.readByteRegister( MAX77960._REG_CHG_INT )
            # Un-mask specified interrupts
            [topMask, chgMask] = self._mapIntApi2Impl(configData.value)
            self.writeByteRegister( MAX77960._REG_TOP_INT_MASK, ~topMask )
            ret = self.writeByteRegister( MAX77960._REG_CHG_INT_MASK, ~chgMask )
        return ret
    
    
    #
    # The Watchdog API
    #
    
    def enableWatchdog(self):
        ret = self.enableReg( MAX77960._REG_CHG_CNFG_00, MAX77960._WDTEN )
        return ret
    
    def disableWatchdog(self):
        ret = self.disableReg( MAX77960._REG_CHG_CNFG_00, MAX77960._WDTEN )
        return ret
    
    def isWatchdogRunning(self):
        data, ret = self.readByteRegister( MAX77960._REG_CHG_CNFG_00 )
        if (ret == ErrorCode.errOk):
            if (data & MAX77960._WDTEN) == MAX77960._WDTEN_ON:
                ret = ErrorCode.errOk
            else:
                ret = ErrorCode.errUnavailable
        return ret

    def clearWatchdog(self):
        data, ret = self.readByteRegister( MAX77960._REG_CHG_CNFG_06 )
        if (ret == ErrorCode.errOk):
            data = (data & ~MAX77960._WDTCLR) | MAX77960._WDTCLR_DO_CLEAR
            ret = self.writeByteRegister( MAX77960._REG_CHG_CNFG_06, data )
        return ret

    def isWatchdogElapsed(self):
        data, ret = self.readByteRegister( MAX77960._REG_CHG_DETAILS_01 )
        if (ret == ErrorCode.errOk):
            if (data & MAX77960._CHG_DTLS) == MAX77960._CHG_DTLS_OFF_WDOG:
                ret = ErrorCode.errOk
            else:
                ret = ErrorCode.errUnavailable
        return ret

    def clearWatchdogElapsed(self):
        # Restart the charger by clearing the WD flag.
        ret = self.clearWatchdog()
        return ret
