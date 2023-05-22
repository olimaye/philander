from serialbus import SerialBusDevice
from charger import Charger
from Watchdog import Watchdog

class MAX77960( SerialBusDevice, Charger, Watchdog ):
    #
    # Protected / private attributes
    #
    
    #
    # The only address is 0x69. No alternative.
    _ADRESSES_ALLOWED = [0x69]

    # Definition of registers and register content.
    # TOP
    _REG_CID          = 0x00
    _CID_REVISION     = 0xE0 # Silicon Revision
    _CID_VERSION      = 0x1F # OTP Recipe Version
    _CID_REV_5        = 0xA0 # silicon revision = 5
    _CID_REV_6        = 0xC0 # silicon revision = 6
    _CID_REV_MIN      = _CID_REV_5 # Minimum known silicon revision that this driver is made for.
    _CID_REV_MAX      = _CID_REV_6 # Maximum known silicon revision that this driver is made for.
    _CID_MAX7796x     = _CID_REV_5 # MAX77960
    _CID_MAX7796xB    = _CID_REV_6 # MAX77960B
    
    _REG_SWRST        = 0x01
    _SWRST_TYPE_O     = 0xA5 # Reset Type O registers
    _SWRST_NONE       = 0x00 # No reset
    _SWRST_DEFAULT    = _SWRST_NONE
    
    _REG_TOP_INT      = 0x02
    _TSHDN_I          = 0x04 # Thermal shutdown interrupt
    _SYSOVLO_I        = 0x02 # SYSOVLO interrupt
    _SYSUVLO_I        = 0x01 # SYSUVLO interrupt
    
    _REG_TOP_INT_MASK = 0x03
    _TSHDN_M          = 0x04 # Thermal shutdown interrupt masked
    _SYSOVLO_M        = 0x02 # SYSOVLO interrupt masked
    _SYSUVLO_M        = 0x01 # SYSUVLO interrupt masked
    _TOP_INT_MASK_ALL = 0x07
    _TOP_INT_MASK_NONE= 0x00
    _TOP_INT_MASK_DEFAULT = 0xFF
    
    _REG_TOP_INT_OK   = 0x04
    _TSHDN_OK         = 0x04 # Device in thermal shutdown
    _SYSOVLO_OK       = 0x02 # SYS voltage above (0) / below (1) SYSOVLO
    _SYSUVLO_OK       = 0x01 # SYS coltage below (0) / above (1) SYSUVLO

    # CHARGER_FUNC
    _REG_CHG_INT      = 0x10
    _AICL_I           = 0x80 # AICL interrupt; AICL_OK changed since last read
    _CHGIN_I          = 0x40 # CHGIN interrupt; CHGIN_OK changed
    _B2SOVRC_I        = 0x20 # B2SOVRC interrupt; B2SOVRC changed
    _CHG_I            = 0x10 # Charger interrupt; CHG_OK changed
    _BAT_I            = 0x08 # Battery interrupt; BAT_OK changed
    _CHGINLIM_I       = 0x04 # CHGINLIM interrupt; CHGINLIM_OK changed
    _DISQBAT_I        = 0x02 # DISQBAT interrupt; DISQBAT_OK changed
    _OTG_PLIM_I       = 0x01 # OTG/PLIM interrupt; OTG_OK (Mode=0xA) or PLIM_OK changed
    
    _REG_CHG_INT_MASK = 0x11
    _AICL_M           = 0x80 # AICL interrupt masked
    _CHGIN_M          = 0x40 # CHGIN interrupt masked
    _B2SOVRC_M        = 0x20 # B2SOVRC interrupt masked
    _CHG_M            = 0x10 # Charger interrupt masked
    _BAT_M            = 0x08 # Battery interrupt masked
    _CHGINLIM_M       = 0x04 # CHGINLIM interrupt masked
    _DISQBAT_M        = 0x02 # DISQBAT interrupt masked
    _OTG_PLIM_M       = 0x01 # OTG/PLIM interrupt masked
    _CHG_INT_MASK_ALL = 0xFF
    _CHG_INT_MASK_NONE= 0x00
    _CHG_INT_MASK_DEFAULT = 0xFF
    
    _REG_CHG_INT_OK   = 0x12
    _AICL_OK          = 0x80 # Not in AICL mode
    _CHGIN_OK         = 0x40 # CHGIN input valid; CHGIN_DTLS=3
    _B2SOVRC_OK       = 0x20 # BATT to SYS within current limit
    _CHG_OK           = 0x10 # Charger OK or off
    _BAT_OK           = 0x08 # Battery OK; BAT_DTLS=0x03 or 0x07
    _CHGINLIM_OK      = 0x04 # CHGIN input within current limit
    _DISQBAT_OK       = 0x02 # DISQBAT low and DISIBS is 0 while QBAT is not disabled
    _OTG_PLIM_OK      = 0x01 # OTG operation OK (Mode=0x0A); Buck-boost within current limit.
    
    _REG_CHG_DETAILS_00 = 0x13
    _CHGIN_DTLS       = 0x60 # CHGIN Details as follows:
    _CHGIN_DTLS_TOO_LOW = 0x00 # VBUS is invalid; V_CHGIN < V_CHGIN_UVLO
    _CHGIN_DTLS_RSVD  = 0x20 # Reserved
    _CHGIN_DTLS_TOO_HIGH= 0x40 # VBUS is invalid; V_CHGIN > V_CHGIN_OVLO
    _CHGIN_DTLS_GOOD  = 0x60 # VBUS is valid; V_CHGIN_UVLO < V_CHGIN < V_CHGIN_OVLO
    _OTG_DTLS         = 0x18 # OTG Details as follows:
    _OTG_DTLS_UNDERVOLT = 0x00 # OTG output in undervoltage; V_CHGIN < V_OTG_UVLO
    _OTG_DTLS_OTG_GOOD  = 0x08 # OTG output within limit OTG_ILIM
    _OTG_DTLS_OVERVOLT= 0x10 # OTG output in overvoltage; V_CHGIN > V_OTG_OVLO
    _OTG_DTLS_ILIM    = 0x18 # OTG disabled or output is valid but not in current limit.
    _QB_DTLS          = 0x01 # QBAT details
    _QB_DTLS_ON       = 0x01 # QBAT is on.
    _QB_DTLS_OFF      = 0x00 # QBAT is off.
    
    _REG_CHG_DETAILS_01 = 0x14
    _TREG             = 0x80 # Temperature regulation status 
    _TREG_HIGH        = 0x80 # Junction temperature higher than REGTEMP; folding back charge current 
    _TREG_GOOD        = 0x00 # Junction temperature less than REGTEMP
    _BAT_DTLS         = 0x70 # Battery details as follows:
    _BAT_DTLS_REMOVAL = 0x00 # Battery removal detected on THM pin.
    _BAT_DTLS_BELOW_PREQ= 0x10 # V_BATT < V_PRECHG; below prequal.
    _BAT_DTLS_TIME_OUT= 0x20 # Charging takes longer than expected. Possibly due to high system currents, old/damaged battery. Charging suspended.
    _BAT_DTLS_OK      = 0x30 # Battery OK and (VSYSMIN - 500mV) < VBATT, QBAT is on and VSYS is approximately equal to VBATT.
    _BAT_DTLS_LOW_VOLT= 0x40 # Battery OK but its voltage is low: VPRECHG < VBATT < VSYSMIN - 500mV.
    _BAT_DTLS_OVR_VOLT= 0x50 # Battery voltage has been greater than the battery overvoltage threshold (CHG_CV_PRM + 240mV/cell) for the last 30ms. Valid input.
    _BAT_DTLS_OVR_CURR= 0x60 # Battery has been overcurrent for at least 3ms since the last time this register has been read.
    _BAT_DTLS_NO_LEVEL= 0x70 # Battery level not available. In battery only mode, all battery comparators are off except for B2SOVRC.
    _CHG_DTLS         = 0x0F # Charger details as follows:
    _CHG_DTLS_PRECHRG = 0x00 # Charger is in precharge or trickle charge mode CHG_OK = 1 and VBATT < VSYSMIN - 500mV and TJ < TSHDN
    _CHG_DTLS_FAST_CURR = 0x01 # Charger is in fast-charge constant current mode CHG_OK = 1 and VBATT < VBATTREG and TJ < TSHDN
    _CHG_DTLS_FAST_VOLT = 0x02 # Charger is in fast-charge constant voltage mode CHG_OK = 1 and VBATT = VBATTREG and TJ < TSHDN
    _CHG_DTLS_TOP_OFF = 0x03 # Charger is in top-off mode CHG_OK = 1 and VBATT = VBATTREG and TJ < TSHDN
    _CHG_DTLS_DONE    = 0x04 # Charger is in done mode CHG_OK = 0 and VBATT > VBATTREG - VRSTRT and TJ < TSHDN
    _CHG_DTLS_OFF_RESIST= 0x05 # Charger is off because at least one pin of INLIM, ITO, ISET, or VSET has invalid resistance. CHG_OK = 0
    _CHG_DTLS_E_TIMER = 0x06 # Charger is in timer fault mode. CHG_OK = 0 and if BAT_DTLS = 0b001 then VBATT < VSYSMIN - 500mV or VBATT < VPRECHG and TJ < TSHDN
    _CHG_DTLS_SUSP_QBAT = 0x07 # Charger is suspended because QBAT is disabled (DISQBAT = high or DISIBS = 1) CHG_OK = 0
    _CHG_DTLS_OFF_CHGIN = 0x08 # Charger is off, charger input invalid and/or charger is disabled CHG_OK = 1
    #_CHG_DTLS_RSV_9   = 0x09 # Reserved.
    _CHG_DTLS_OFF_TEMP= 0x0A # Charger is off and the junction temperature is > TSHDN CHG_OK = 0
    _CHG_DTLS_OFF_WDOG= 0x0B # Charger is off because the watchdog timer expired CHG_OK = 0
    _CHG_DTLS_SUSP_JEITA= 0x0C # Charger is suspended or charge current or voltage is reduced based on JEITA control. This condition is also reported in THM_DTLS. CHG_OK = 0
    _CHG_DTLS_SUSP_NOBAT= 0x0D # Charger is suspended because battery removal is detected on THM pin. This condition is also reported in THM_DTLS. CHG_OK = 0
    #_CHG_DTLS_RSV_E   = 0x0E # Reserved.
    #_CHG_DTLS_RSV_F   = 0x0F # Reserved.

    _REG_CHG_DETAILS_02 = 0x15
    _THM_DTLS         = 0x70 # Thermistor status details as follows:
    _THM_DTLS_COLD    = 0x00 # Low temperature and charging suspended
    _THM_DTLS_COOL    = 0x10 # Low temperature charging
    _THM_DTLS_NORMAL  = 0x20 # Normal temperature charging
    _THM_DTLS_WARM    = 0x30 # High temperature charging
    _THM_DTLS_HOT     = 0x40 # High temperature and charging suspended
    _THM_DTLS_BAT_RMVD= 0x50 # Battery removal detected on THM pin
    _THM_DTLS_DISABLED= 0x60 # Thermistor monitoring is disabled
    #_THM_DTLS_RSV_7   = 0x70 # Reserved.
    _APP_MODE_DTLS    = 0x08 # Application mode status as follows:
    _APP_MODE_DTLS_CONV = 0x00 # Operate as a standalone DC-DC converter
    _APP_MODE_DTLS_CHRG = 0x08 # Operate as a charger.
    _FSW_DTLS         = 0x06 # Programmed switching frequency details as follows:
    _FSW_DTLS_600K    = 0x00 # 600 kHz
    _FSW_DTLS_1200K   = 0x02 # 1.2 MHz; only from silicon rev. 6 on (MAX7796xB)
    #_FSW_DTLS_RSV_2   = 0x04 # Reserved.
    #_FSW_DTLS_RSV_3   = 0x06 # Reserved.
    _NUM_CELL_DTLS    = 0x01 # Number of serially connected battery cells as follows:
    _NUM_CELL_DTLS_2  = 0x00 # 2-cell battery
    _NUM_CELL_DTLS_3  = 0x01 # 3-cell battery
    
    _REG_CHG_CNFG_00    = 0x16
    _COMM_MODE          = 0x80 # I2C enable
    _COMM_MODE_AUTO     = 0x00 # Autonomous Mode defined by external resistors on INLIM, ISET, VSET and ITO pins. Writing 0 to COMM_MODE is ignored.
    _COMM_MODE_I2C      = 0x80 # I2C enabled. CHGIN_ILIM, CHGCC, CHG_CV_PRM and TO_ITH registers are programmed by I2C. Writing 1 to COMM_MODE is allowed.
    _COMM_MODE_DEFAULT  = _COMM_MODE_AUTO
    _DISIBS             = 0x40 # BATT to SYS FET Disable Control Read back value of DISIBS register bit reflects the actual DISIBS command or DISQBAT PIN state.
    _DISIBS_FET_PPSM    = 0x00 # BATT to SYS FET is controlled by the power path state machine.
    _DISIBS_FET_OFF     = 0x40 # BATT to SYS FET is forced off.
    _DISIBS_DEFAULT     = _DISIBS_FET_PPSM
    _STBY_EN            = 0x20 # CHGIN Standby Enable Read back value of the STBY_EN register bit reflects the actual CHGIN standby setting.
    _STBY_EN_DCDC_PPSM  = 0x00 # DC-DC is controlled by the power path state machine.
    _STBY_EN_DCDC_OFF   = 0x20 # Force DC-DC off. Device goes to CHGIN low quiescent current standby.
    _STBY_EN_DCDC_DEFAULT = _STBY_EN_DCDC_PPSM
    _WDTEN              = 0x10 # Watchdog Timer Enable.
    _WDTEN_OFF          = 0x00 # Watchdog timer disabled
    _WDTEN_ON           = 0x10 # Watchdog timer enabled
    _WDTEN_DEFAULT      = _WDTEN_OFF
    _MODE               = 0x0F # Smart Power Selector Configuration as follows:
    _MODE_ALL_OFF       = 0x00 # Charger = off, OTG = off, DC-DC = off. When the QBAT switch is on (DISQBAT = low and DISIBS = 0), the battery powers the system.
    _MODE_ALL_OFF_1     = 0x01 # Same as 0x00
    _MODE_ALL_OFF_2     = 0x02 # Same as 0x00
    _MODE_ALL_OFF_3     = 0x03 # Same as 0x00
    _MODE_DCDC_ONLY     = 0x04 # Charger = off, OTG = off, DC-DC = on. When there is a valid input, the DC-DC converter regulates the system voltage to be the maximum of (VSYSMIN and VBATT + 4%).
    _MODE_CHRG_DCDC     = 0x05 # Charger = on,OTG = off, DC-DC = on. When there is a valid input, the battery is charging. VSYS is the larger of VSYSMIN and ~VBATT + IBATT x RBAT2SYS.
    _MODE_CHRG_DCDC_6   = 0x06 # Same as 0x05
    _MODE_CHRG_DCDC_7   = 0x07 # Same as 0x05
    #_MODE_RSV_8         = 0x08 # Reserved.
    #_MODE_RSV_9         = 0x09 # Reserved.
    _MODE_OTG_ONLY      = 0x0A # Charger = off, OTG = on, DC-DC = off. QBAT is on to allow the battery to support the system, the charger's DC-DC operates in reverse mode as a buck converter.
    #_MODE_RSV_11        = 0x0B # Reserved.
    #_MODE_RSV_12        = 0x0C # Reserved.
    #_MODE_RSV_13        = 0x0D # Reserved.
    #_MODE_RSV_14        = 0x0E # Reserved.
    #_MODE_RSV_15        = 0x0F # Reserved.
    _MODE_DEFAULT       = _MODE_CHRG_DCDC

    _REG_CHG_CNFG_01    = 0x17
    _PQEN               = 0x80 # Low-Battery Prequalification Mode Enable
    _PQEN_OFF           = 0x00 # Low-Battery Prequalification mode is disabled.
    _PQEN_ON            = 0x80 # Low-Battery Prequalification mode is enabled.
    _PQEN_DEFAULT       = _PQEN_ON
    _LPM                = 0x40 # Low Power Mode control
    _LPM_NORMAL         = 0x00 # QBAT charge pump runs in Normal mode.
    _LPM_ON             = 0x40 # QBAT charge pump is in Low Power Mode.
    _LPM_DEFAULT        = _LPM_NORMAL
    _CHG_RSTRT          = 0x30 # Charger Restart Threshold
    _CHG_RSTRT_100      = 0x00 # 100mV/cell below the value programmed by CHG_CV_PRM
    _CHG_RSTRT_150      = 0x10 # 150mV/cell below the value programmed by CHG_CV_PRM
    _CHG_RSTRT_200      = 0x20 # 200mV/cell below the value programmed by CHG_CV_PRM
    _CHG_RSTRT_DISABLED = 0x30 # Disabled.
    _CHG_RSTRT_MIN      = _CHG_RSTRT_100
    _CHG_RSTRT_MAX      = _CHG_RSTRT_200
    _CHG_RSTRT_DEFAULT  = _CHG_RSTRT_150
    _STAT_EN            = 0x08 # Charge Indicator Output Enable
    _STAT_EN_OFF        = 0x00 # Disable STAT output
    _STAT_EN_ON         = 0x08 # Enable STAT output
    _STAT_EN_DEFAULT    = _STAT_EN_ON
    _FCHGTIME           = 0x07 # Fast-Charge Timer setting (tFC, hrs)
    _FCHGTIME_DISABLED  = 0x00 # Disabled.
    _FCHGTIME_3H        = 0x01 # 3 hours.
    _FCHGTIME_4H        = 0x02 # 4 hours.
    _FCHGTIME_5H        = 0x03 # 5 hours.
    _FCHGTIME_6H        = 0x04 # 6 hours.
    _FCHGTIME_7H        = 0x05 # 7 hours.
    _FCHGTIME_8H        = 0x06 # 8 hours.
    _FCHGTIME_10H       = 0x07 # 10 hours.
    _FCHGTIME_MIN       = _FCHGTIME_3H
    _FCHGTIME_MAX       = _FCHGTIME_10H
    _FCHGTIME_DEFAULT   = _FCHGTIME_3H
    
    _REG_CHG_CNFG_02    = 0x18
    _CHGCC              = 0x3F # Fast-Charge Current Selection (mA).
    _CHGCC_100          = 0x00 # 100 mA
    _CHGCC_150          = 0x01 # 150 mA
    _CHGCC_200          = 0x02 # 200 mA
    _CHGCC_250          = 0x03 # 250 mA
    _CHGCC_300          = 0x04 # 300 mA
    _CHGCC_350          = 0x05 # 350 mA
    _CHGCC_400          = 0x06 # 400 mA
    _CHGCC_450          = 0x07 # 450 mA
    _CHGCC_500          = 0x08 # 500 mA
    _CHGCC_600          = 0x09 # 600 mA
    _CHGCC_700          = 0x0A # 700 mA
    _CHGCC_800          = 0x0B # 800 mA
    _CHGCC_900          = 0x0C # 900 mA
    _CHGCC_1000         = 0x0D # 1000 mA
    _CHGCC_1100         = 0x0E # 1100 mA
    _CHGCC_1200         = 0x0F # 1200 mA
    _CHGCC_1300         = 0x10 # 1300 mA
    _CHGCC_1400         = 0x11 # 1400 mA
    _CHGCC_1500         = 0x12 # 1500 mA
    _CHGCC_1600         = 0x13 # 1600 mA
    _CHGCC_1700         = 0x14 # 1700 mA
    _CHGCC_1800         = 0x15 # 1800 mA
    _CHGCC_1900         = 0x16 # 1900 mA
    _CHGCC_2000         = 0x17 # 2000 mA
    _CHGCC_2100         = 0x18 # 2100 mA
    _CHGCC_2200         = 0x19 # 2200 mA
    _CHGCC_2300         = 0x1A # 2300 mA
    _CHGCC_2400         = 0x1B # 2400 mA
    _CHGCC_2500         = 0x1C # 2500 mA
    _CHGCC_2600         = 0x1D # 2600 mA
    _CHGCC_2700         = 0x1E # 2700 mA
    _CHGCC_2800         = 0x1F # 2800 mA
    _CHGCC_2900         = 0x20 # 2900 mA
    _CHGCC_3000         = 0x21 # 3000 mA
    _CHGCC_3100         = 0x22 # 3100 mA
    _CHGCC_3200         = 0x23 # 3200 mA
    _CHGCC_3300         = 0x24 # 3300 mA
    _CHGCC_3400         = 0x25 # 3400 mA
    _CHGCC_3500         = 0x26 # 3500 mA
    _CHGCC_3600         = 0x27 # 3600 mA
    _CHGCC_3700         = 0x28 # 3700 mA
    _CHGCC_3800         = 0x29 # 3800 mA
    _CHGCC_3900         = 0x2A # 3900 mA
    _CHGCC_4000         = 0x2B # 4000 mA
    _CHGCC_4100         = 0x2C # 4100 mA
    _CHGCC_4200         = 0x2D # 4200 mA
    _CHGCC_4300         = 0x2E # 4300 mA
    _CHGCC_4400         = 0x2F # 4400 mA
    _CHGCC_4500         = 0x30 # 4500 mA
    _CHGCC_4600         = 0x31 # 4600 mA
    _CHGCC_4700         = 0x32 # 4700 mA
    _CHGCC_4800         = 0x33 # 4800 mA
    _CHGCC_4900         = 0x34 # 4900 mA
    _CHGCC_5000         = 0x35 # 5000 mA
    _CHGCC_5100         = 0x36 # 5100 mA
    _CHGCC_5200         = 0x37 # 5200 mA
    _CHGCC_5300         = 0x38 # 5300 mA
    _CHGCC_5400         = 0x39 # 5400 mA
    _CHGCC_5500         = 0x3A # 5500 mA
    _CHGCC_5600         = 0x3B # 5600 mA
    _CHGCC_5700         = 0x3C # 5700 mA
    _CHGCC_5800         = 0x3D # 5800 mA
    _CHGCC_5900         = 0x3E # 5900 mA
    _CHGCC_6000         = 0x3F # 6000 mA
    _CHGCC_MIN          = _CHGCC_100
    _CHGCC_MAX          = _CHGCC_6000
    _CHGCC_DEFAULT      = _CHGCC_450
    
    _REG_CHG_CNFG_03    = 0x19
    _SYS_TRACK_DIS      = 0x80 # SYS Tracking Disable Control
    _SYS_TRACK_ENABLED  = 0x00 # SYS tracking enabled. SYS regulated to MAX(VBATT + 4%, VSYSMIN), even in Charge Done state.
    _SYS_TRACK_DISABLED = 0x80 # SYS tracking is disabled. SYS is regulated to VCHG_CV_PRM.
    _SYS_TRACK_DEFAULT  = _SYS_TRACK_DISABLED
    _B2SOVRC_DTC        = 0x40 # Battery to SYS Overcurrent Debounce Time Control.
    _B2SOVRC_DTC_6_MS   = 0x00 # tOCP = 6 ms
    _B2SOVRC_DTC_100_MS = 0x40 # tOCP = 100 ms
    _B2SOVRC_DTC_MIN    = _B2SOVRC_DTC_6_MS
    _B2SOVRC_DTC_MAX    = _B2SOVRC_DTC_100_MS
    _B2SOVRC_DTC_DEFAULT= _B2SOVRC_DTC_6_MS
    _TO_TIME            = 0x38 # Top-Off Timer Setting
    _TO_TIME_30_SEC     = 0x00 # 30 seconds
    _TO_TIME_10_MIN     = 0x08 # 10 minutes
    _TO_TIME_20_MIN     = 0x10 # 20 minutes
    _TO_TIME_30_MIN     = 0x18 # 30 minutes
    _TO_TIME_40_MIN     = 0x20 # 40 minutes
    _TO_TIME_50_MIN     = 0x28 # 50 minutes
    _TO_TIME_60_MIN     = 0x30 # 60 minutes
    _TO_TIME_70_MIN     = 0x38 # 70 minutes
    _TO_TIME_MIN        = _TO_TIME_30_SEC
    _TO_TIME_MAX        = _TO_TIME_70_MIN
    _TO_TIME_DEFAULT    = _TO_TIME_30_MIN
    _TO_ITH             = 0x07 # Top-Off Current Threshold (mA).
    _TO_ITH_100         = 0x00 # 100 mA
    _TO_ITH_200         = 0x01 # 200 mA
    _TO_ITH_300         = 0x02 # 300 mA
    _TO_ITH_400         = 0x03 # 400 mA
    _TO_ITH_500         = 0x04 # 500 mA
    _TO_ITH_600         = 0x05 # 600 mA
    _TO_ITH_600_6       = 0x06 # 600 mA
    _TO_ITH_600_7       = 0x07 # 600 mA
    _TO_ITH_MIN         = _TO_ITH_100
    _TO_ITH_MAX         = _TO_ITH_600
    _TO_ITH_DEFAULT     = _TO_ITH_100
    
    _REG_CHG_CNFG_04    = 0x1A
    _CHG_CV_PRM         = 0x3F # Charge Termination Voltage Setting (mV).
    # 2 cells:
    _CHG_CV_PRM_2C_8000 = 0x00 # 8000 mV
    _CHG_CV_PRM_2C_8020 = 0x01 # 8020 mV
    _CHG_CV_PRM_2C_8040 = 0x02 # 8040 mV
    _CHG_CV_PRM_2C_8060 = 0x03 # 8060 mV
    _CHG_CV_PRM_2C_8080 = 0x04 # 8080 mV
    _CHG_CV_PRM_2C_8100 = 0x05 # 8100 mV
    _CHG_CV_PRM_2C_8120 = 0x06 # 8120 mV
    _CHG_CV_PRM_2C_8140 = 0x07 # 8140 mV 
    _CHG_CV_PRM_2C_8160 = 0x08 # 8160 mV
    _CHG_CV_PRM_2C_8180 = 0x09 # 8180 mV
    _CHG_CV_PRM_2C_8200 = 0x0A # 8200 mV
    _CHG_CV_PRM_2C_8220 = 0x0B # 8220 mV
    _CHG_CV_PRM_2C_8240 = 0x0C # 8240 mV
    _CHG_CV_PRM_2C_8260 = 0x0D # 8260 mV
    _CHG_CV_PRM_2C_8280 = 0x0E # 8280 mV
    _CHG_CV_PRM_2C_8300 = 0x0F # 8300 mV
    _CHG_CV_PRM_2C_8320 = 0x10 # 8320 mV
    _CHG_CV_PRM_2C_8340 = 0x11 # 8340 mV
    _CHG_CV_PRM_2C_8360 = 0x12 # 8360 mV
    _CHG_CV_PRM_2C_8380 = 0x13 # 8380 mV
    _CHG_CV_PRM_2C_8400 = 0x14 # 8400 mV
    _CHG_CV_PRM_2C_8420 = 0x15 # 8420 mV
    _CHG_CV_PRM_2C_8440 = 0x16 # 8440 mV
    _CHG_CV_PRM_2C_8460 = 0x17 # 8460 mV
    _CHG_CV_PRM_2C_8480 = 0x18 # 8480 mV
    _CHG_CV_PRM_2C_8500 = 0x19 # 8500 mV
    _CHG_CV_PRM_2C_8520 = 0x1A # 8520 mV
    _CHG_CV_PRM_2C_8540 = 0x1B # 8540 mV
    _CHG_CV_PRM_2C_8560 = 0x1C # 8560 mV
    _CHG_CV_PRM_2C_8580 = 0x1D # 8680 mV
    _CHG_CV_PRM_2C_8600 = 0x1E # 8600 mV
    _CHG_CV_PRM_2C_8620 = 0x1F # 8620 mV
    _CHG_CV_PRM_2C_8640 = 0x20 # 8640 mV
    _CHG_CV_PRM_2C_8660 = 0x21 # 8660 mV
    _CHG_CV_PRM_2C_8680 = 0x22 # 8680 mV
    _CHG_CV_PRM_2C_8700 = 0x23 # 8700 mV
    _CHG_CV_PRM_2C_8720 = 0x24 # 8720 mV
    _CHG_CV_PRM_2C_8740 = 0x25 # 8740 mV
    _CHG_CV_PRM_2C_8760 = 0x26 # 8760 mV
    _CHG_CV_PRM_2C_8780 = 0x27 # 8780 mV
    _CHG_CV_PRM_2C_8800 = 0x28 # 8800 mV
    _CHG_CV_PRM_2C_8820 = 0x29 # 8820 mV
    _CHG_CV_PRM_2C_8840 = 0x2A # 8840 mV
    _CHG_CV_PRM_2C_8860 = 0x2B # 8860 mV
    _CHG_CV_PRM_2C_8880 = 0x2C # 8880 mV
    _CHG_CV_PRM_2C_8900 = 0x2D # 8900 mV
    _CHG_CV_PRM_2C_8920 = 0x2E # 8920 mV
    _CHG_CV_PRM_2C_8940 = 0x2F # 8940 mV
    _CHG_CV_PRM_2C_8960 = 0x30 # 8960 mV
    _CHG_CV_PRM_2C_8980 = 0x31 # 8980 mV
    _CHG_CV_PRM_2C_9000 = 0x32 # 9000 mV
    _CHG_CV_PRM_2C_9020 = 0x33 # 9020 mV
    _CHG_CV_PRM_2C_9040 = 0x34 # 9040 mV
    _CHG_CV_PRM_2C_9060 = 0x35 # 9060 mV
    _CHG_CV_PRM_2C_9080 = 0x36 # 9080 mV
    _CHG_CV_PRM_2C_9100 = 0x37 # 9100 mV
    _CHG_CV_PRM_2C_9120 = 0x38 # 9120 mV
    _CHG_CV_PRM_2C_9140 = 0x39 # 9140 mV
    _CHG_CV_PRM_2C_9160 = 0x3A # 9160 mV
    _CHG_CV_PRM_2C_9180 = 0x3B # 9180 mV
    _CHG_CV_PRM_2C_9200 = 0x3C # 9200 mV
    _CHG_CV_PRM_2C_9220 = 0x3D # 9220 mV
    _CHG_CV_PRM_2C_9240 = 0x3E # 9240 mV
    _CHG_CV_PRM_2C_9260 = 0x3F # 9260 mV
    _CHG_CV_PRM_2C_MIN  = _CHG_CV_PRM_2C_8000
    _CHG_CV_PRM_2C_MAX  = _CHG_CV_PRM_2C_9260
    _CHG_CV_PRM_2C_DEFAULT = _CHG_CV_PRM_2C_8000
    # 3 cells:
    _CHG_CV_PRM_3C_12000= 0x00 # 12000 mV
    _CHG_CV_PRM_3C_12030= 0x01 # 12030 mV
    _CHG_CV_PRM_3C_12060= 0x02 # 12060 mV
    _CHG_CV_PRM_3C_12090= 0x03 # 12090 mV
    _CHG_CV_PRM_3C_12120= 0x04 # 12120 mV
    _CHG_CV_PRM_3C_12150= 0x05 # 12150 mV
    _CHG_CV_PRM_3C_12180= 0x06 # 12180 mV
    _CHG_CV_PRM_3C_12210= 0x07 # 12210 mV
    _CHG_CV_PRM_3C_12240= 0x08 # 12240 mV
    _CHG_CV_PRM_3C_12270= 0x09 # 12270 mV
    _CHG_CV_PRM_3C_12300= 0x0A # 12300 mV
    _CHG_CV_PRM_3C_12330= 0x0B # 12330 mV
    _CHG_CV_PRM_3C_12360= 0x0C # 12360 mV
    _CHG_CV_PRM_3C_12390= 0x0D # 12390 mV
    _CHG_CV_PRM_3C_12420= 0x0E # 12420 mV
    _CHG_CV_PRM_3C_12450= 0x0F # 12450 mV
    _CHG_CV_PRM_3C_12480= 0x10 # 12480 mV
    _CHG_CV_PRM_3C_12510= 0x11 # 12510 mV
    _CHG_CV_PRM_3C_12540= 0x12 # 12540 mV
    _CHG_CV_PRM_3C_12570= 0x13 # 12570 mV
    _CHG_CV_PRM_3C_12600= 0x14 # 12600 mV
    _CHG_CV_PRM_3C_12630= 0x15 # 12630 mV
    _CHG_CV_PRM_3C_12660= 0x16 # 12660 mV
    _CHG_CV_PRM_3C_12690= 0x17 # 12690 mV
    _CHG_CV_PRM_3C_12720= 0x18 # 12720 mV
    _CHG_CV_PRM_3C_12750= 0x19 # 12750 mV
    _CHG_CV_PRM_3C_12780= 0x1A # 12780 mV
    _CHG_CV_PRM_3C_12810= 0x1B # 12810 mV
    _CHG_CV_PRM_3C_12840= 0x1C # 12840 mV
    _CHG_CV_PRM_3C_12870= 0x1D # 12870 mV
    _CHG_CV_PRM_3C_12900= 0x1E # 12900 mV
    _CHG_CV_PRM_3C_12930= 0x1F # 12930 mV
    _CHG_CV_PRM_3C_12960= 0x20 # 12960 mV
    _CHG_CV_PRM_3C_12990= 0x21 # 12990 mV
    _CHG_CV_PRM_3C_13020= 0x22 # 13020 mV
    _CHG_CV_PRM_3C_13050= 0x23 # 13050 mV
    _CHG_CV_PRM_3C_MIN  = _CHG_CV_PRM_3C_12000
    _CHG_CV_PRM_3C_MAX  = _CHG_CV_PRM_3C_13050
    _CHG_CV_PRM_3C_DEFAULT = _CHG_CV_PRM_3C_12000
    _CHG_CV_PRM_DEFAULT = _CHG_CV_PRM_2C_DEFAULT
    
    _REG_CHG_CNFG_05    = 0x1B
    _ITRICKLE           = 0x30 # Trickle Charge Current Selection (mA)
    _ITRICKLE_100       = 0x00 # 100 mA
    _ITRICKLE_200       = 0x10 # 200 mA
    _ITRICKLE_300       = 0x20 # 300 mA
    _ITRICKLE_400       = 0x30 # 400 mA
    _ITRICKLE_MIN       = _ITRICKLE_100
    _ITRICKLE_MAX       = _ITRICKLE_400
    _ITRICKLE_DEFAULT   = _ITRICKLE_100
    _B2SOVRC            = 0x0F # BATT to SYS Overcurrent Threshold (mA)
    _B2SOVRC_DISABLED   = 0x00 # Disabled
    _B2SOVRC_3000       = 0x01 # 3000 mA
    _B2SOVRC_3500       = 0x02 # 3500 mA
    _B2SOVRC_4000       = 0x03 # 4000 mA
    _B2SOVRC_4500       = 0x04 # 4500 mA
    _B2SOVRC_5000       = 0x05 # 5000 mA
    _B2SOVRC_5500       = 0x06 # 5500 mA
    _B2SOVRC_6000       = 0x07 # 6000 mA
    _B2SOVRC_6500       = 0x08 # 6500 mA
    _B2SOVRC_7000       = 0x09 # 7000 mA
    _B2SOVRC_7500       = 0x0A # 7500 mA
    _B2SOVRC_8000       = 0x0B # 8000 mA
    _B2SOVRC_8500       = 0x0C # 8500 mA
    _B2SOVRC_9000       = 0x0D # 9000 mA
    _B2SOVRC_9500       = 0x0E # 9500 mA
    _B2SOVRC_10000      = 0x0F # 10000 mA
    _B2SOVRC_MIN        = _B2SOVRC_3000
    _B2SOVRC_MAX        = _B2SOVRC_10000
    _B2SOVRC_DEFAULT    = _B2SOVRC_4500
    
    _REG_CHG_CNFG_06    = 0x1C
    _CHGPROT            = 0x0C # Charger Settings Protection Bits
    _CHGPROT_LOCK       = 0x00 # Write capability locked.
    _CHGPROT_LOCK_4     = 0x04 # Write capability locked.
    _CHGPROT_LOCK_8     = 0x08 # Write capability locked.
    _CHGPROT_UNLOCK     = 0x0C # Write capability unlocked.
    _CHGPROT_DEFAULT    = _CHGPROT_LOCK
    _WDTCLR             = 0x03 # Watchdog Timer Clear Bits
    _WDTCLR_DO_NOT_TOUCH= 0x00 # Watchdog is not cleared.
    _WDTCLR_DO_CLEAR    = 0x01 # Watchdog is cleared.
    _WDTCLR_DO_NOT_TOUCH_2= 0x02 # Watchdog is not cleared.
    _WDTCLR_DO_NOT_TOUCH_3= 0x03 # Watchdog is not cleared.
    _WDTCLR_DEFAULT     = _WDTCLR_DO_NOT_TOUCH
    
    _REG_CHG_CNFG_07    = 0x1D
    _JEITA_EN           = 0x80 # JEITA Enable
    _JEITA_EN_OFF       = 0x00 # JEITA disabled. Fast-charge current and charge termination voltage do not change based on thermistor temperature.
    _JEITA_EN_ON        = 0x80 # JEITA enabled. Fast-charge current and charge termination voltage change based on thermistor temperature.
    _JEITA_EN_DEFAULT   = _JEITA_EN_OFF
    _REGTEMP            = 0x78 # Junction Temperature Thermal Regulation (deg. C).
    _REGTEMP_85         = 0x00 # 85 deg. Celsius
    _REGTEMP_90         = 0x08 # 90 deg. Celsius
    _REGTEMP_95         = 0x10 # 95 deg. Celsius
    _REGTEMP_100        = 0x18 # 100 deg. Celsius
    _REGTEMP_105        = 0x20 # 105 deg. Celsius
    _REGTEMP_110        = 0x28 # 110 deg. Celsius
    _REGTEMP_115        = 0x30 # 115 deg. Celsius
    _REGTEMP_120        = 0x38 # 120 deg. Celsius
    _REGTEMP_125        = 0x40 # 125 deg. Celsius
    _REGTEMP_130        = 0x48 # 130 deg. Celsius
    _REGTEMP_MIN        = _REGTEMP_85
    _REGTEMP_MAX        = _REGTEMP_130
    _REGTEMP_DEFAULT    = _REGTEMP_115
    _VCHGCV_COOL        = 0x04 # JEITA-Controlled Battery Termination Voltage When Thermistor Temperature is Between TCOLD and TCOOL
    _VCHGCV_COOL_NORMAL = 0x00 # Battery termination voltage is set by CHG_CV_PRM.
    _VCHGCV_COOL_REDUCED= 0x04 # Battery termination voltage is set by (CHG_CV_PRM - 180mV/cell).
    _VCHGCV_COOL_DEFAULT= _VCHGCV_COOL_NORMAL
    _ICHGCC_COOL        = 0x02 # JEITA-Controlled Battery Fast-Charge Current When Thermistor Temperature is Between TCOLD and TCOOL
    _ICHGCC_COOL_NORMAL = 0x00 # Battery fast-charge current is set by CHGCC
    _ICHGCC_COOL_REDUCED= 0x02 # Battery fast-charge current is reduced to 50% of CHGCC
    _ICHGCC_COOL_DEFAULT= _ICHGCC_COOL_REDUCED
    _FSHIP_MODE         = 0x01 # Factory Ship Mode Enable
    _FSHIP_MODE_OFF     = 0x00 # Disable factory ship mode
    _FSHIP_MODE_ON      = 0x01 # Enable factory ship mode
    _FSHIP_MODE_DEFAULT = _FSHIP_MODE_OFF
    
    _REG_CHG_CNFG_08    = 0x1E
    _CHGIN_ILIM         = 0x7F # CHGIN Input Current Limit (mA).
    _CHGIN_ILIM_100     = 0x00 # 100 mA
    _CHGIN_ILIM_100_1   = 0x01 # 100 mA
    _CHGIN_ILIM_100_2   = 0x02 # 100 mA
    _CHGIN_ILIM_100_3   = 0x03 # 100 mA
    _CHGIN_ILIM_150     = 0x04 # 150 mA
    _CHGIN_ILIM_200     = 0x05 # 200 mA
    _CHGIN_ILIM_250     = 0x06 # 250 mA
    _CHGIN_ILIM_300     = 0x07 # 300 mA
    _CHGIN_ILIM_350     = 0x08 # 350 mA
    _CHGIN_ILIM_400     = 0x09 # 400 mA
    _CHGIN_ILIM_450     = 0x0A # 450 mA
    _CHGIN_ILIM_500     = 0x0B # 500 mA
    _CHGIN_ILIM_550     = 0x0C # 550 mA
    _CHGIN_ILIM_600     = 0x0D # 600 mA
    _CHGIN_ILIM_650     = 0x0E # 650 mA
    _CHGIN_ILIM_700     = 0x0F # 700 mA
    _CHGIN_ILIM_750     = 0x10 # 750 mA
    _CHGIN_ILIM_800     = 0x11 # 800 mA
    _CHGIN_ILIM_850     = 0x12 # 850 mA
    _CHGIN_ILIM_900     = 0x13 # 900 mA
    _CHGIN_ILIM_950     = 0x14 # 950 mA
    _CHGIN_ILIM_1000    = 0x15 # 1000 mA
    _CHGIN_ILIM_1050    = 0x16 # 1050 mA
    _CHGIN_ILIM_1100    = 0x17 # 1100 mA
    _CHGIN_ILIM_1150    = 0x18 # 1150 mA
    _CHGIN_ILIM_1200    = 0x19 # 1200 mA
    _CHGIN_ILIM_1250    = 0x1A # 1250 mA
    _CHGIN_ILIM_1300    = 0x1B # 1300 mA
    _CHGIN_ILIM_1350    = 0x1C # 1350 mA
    _CHGIN_ILIM_1400    = 0x1D # 1400 mA
    _CHGIN_ILIM_1450    = 0x1E # 1450 mA
    _CHGIN_ILIM_1500    = 0x1F # 1500 mA
    _CHGIN_ILIM_1550    = 0x20 # 1550 mA
    _CHGIN_ILIM_1600    = 0x21 # 1600 mA
    _CHGIN_ILIM_1650    = 0x22 # 1650 mA
    _CHGIN_ILIM_1700    = 0x23 # 1700 mA
    _CHGIN_ILIM_1750    = 0x24 # 1750 mA
    _CHGIN_ILIM_1800    = 0x25 # 1800 mA
    _CHGIN_ILIM_1850    = 0x26 # 1850 mA
    _CHGIN_ILIM_1900    = 0x27 # 1900 mA
    _CHGIN_ILIM_1950    = 0x28 # 1950 mA
    _CHGIN_ILIM_2000    = 0x29 # 2000 mA
    _CHGIN_ILIM_2050    = 0x2A # 2050 mA
    _CHGIN_ILIM_2100    = 0x2B # 2100 mA
    _CHGIN_ILIM_2150    = 0x2C # 2150 mA
    _CHGIN_ILIM_2200    = 0x2D # 2200 mA
    _CHGIN_ILIM_2250    = 0x2E # 2250 mA
    _CHGIN_ILIM_2300    = 0x2F # 2300 mA
    _CHGIN_ILIM_2350    = 0x30 # 2350 mA
    _CHGIN_ILIM_2400    = 0x31 # 2400 mA
    _CHGIN_ILIM_2450    = 0x32 # 2450 mA
    _CHGIN_ILIM_2500    = 0x33 # 2500 mA
    _CHGIN_ILIM_2550    = 0x34 # 2550 mA
    _CHGIN_ILIM_2600    = 0x35 # 2600 mA
    _CHGIN_ILIM_2650    = 0x36 # 2650 mA
    _CHGIN_ILIM_2700    = 0x37 # 2700 mA
    _CHGIN_ILIM_2750    = 0x38 # 2750 mA
    _CHGIN_ILIM_2800    = 0x39 # 2800 mA
    _CHGIN_ILIM_2850    = 0x3A # 2850 mA
    _CHGIN_ILIM_2900    = 0x3B # 2900 mA
    _CHGIN_ILIM_2950    = 0x3C # 2950 mA
    _CHGIN_ILIM_3000    = 0x3D # 3000 mA
    _CHGIN_ILIM_3050    = 0x3E # 3050 mA
    _CHGIN_ILIM_3100    = 0x3F # 3100 mA
    _CHGIN_ILIM_3150    = 0x40 # 3150 mA
    _CHGIN_ILIM_3200    = 0x41 # 3200 mA
    _CHGIN_ILIM_3250    = 0x42 # 3250 mA
    _CHGIN_ILIM_3300    = 0x43 # 3300 mA
    _CHGIN_ILIM_3350    = 0x44 # 3350 mA
    _CHGIN_ILIM_3400    = 0x45 # 3400 mA
    _CHGIN_ILIM_3450    = 0x46 # 3450 mA
    _CHGIN_ILIM_3500    = 0x47 # 3500 mA
    _CHGIN_ILIM_3550    = 0x48 # 3550 mA
    _CHGIN_ILIM_3600    = 0x49 # 3600 mA
    _CHGIN_ILIM_3650    = 0x4A # 3650 mA
    _CHGIN_ILIM_3700    = 0x4B # 3700 mA
    _CHGIN_ILIM_3750    = 0x4C # 3750 mA
    _CHGIN_ILIM_3800    = 0x4D # 3800 mA
    _CHGIN_ILIM_3850    = 0x4E # 3850 mA
    _CHGIN_ILIM_3900    = 0x4F # 3900 mA
    _CHGIN_ILIM_3950    = 0x50 # 3950 mA
    _CHGIN_ILIM_4000    = 0x51 # 4000 mA
    _CHGIN_ILIM_4050    = 0x52 # 4050 mA
    _CHGIN_ILIM_4100    = 0x53 # 4100 mA
    _CHGIN_ILIM_4150    = 0x54 # 4150 mA
    _CHGIN_ILIM_4200    = 0x55 # 4200 mA
    _CHGIN_ILIM_4250    = 0x56 # 4250 mA
    _CHGIN_ILIM_4300    = 0x57 # 4300 mA
    _CHGIN_ILIM_4350    = 0x58 # 4350 mA
    _CHGIN_ILIM_4400    = 0x59 # 4400 mA
    _CHGIN_ILIM_4450    = 0x5A # 4450 mA
    _CHGIN_ILIM_4500    = 0x5B # 4500 mA
    _CHGIN_ILIM_4550    = 0x5C # 4550 mA
    _CHGIN_ILIM_4600    = 0x5D # 4600 mA
    _CHGIN_ILIM_4650    = 0x5E # 4650 mA
    _CHGIN_ILIM_4700    = 0x5F # 4700 mA
    _CHGIN_ILIM_4750    = 0x60 # 4750 mA
    _CHGIN_ILIM_4800    = 0x61 # 4800 mA
    _CHGIN_ILIM_4850    = 0x62 # 4850 mA
    _CHGIN_ILIM_4900    = 0x63 # 4900 mA
    _CHGIN_ILIM_4950    = 0x64 # 4950 mA
    _CHGIN_ILIM_5000    = 0x65 # 5000 mA
    _CHGIN_ILIM_5050    = 0x66 # 5050 mA
    _CHGIN_ILIM_5100    = 0x67 # 5100 mA
    _CHGIN_ILIM_5150    = 0x68 # 5150 mA
    _CHGIN_ILIM_5200    = 0x69 # 5200 mA
    _CHGIN_ILIM_5250    = 0x6A # 5250 mA
    _CHGIN_ILIM_5300    = 0x6B # 5300 mA
    _CHGIN_ILIM_5350    = 0x6C # 5350 mA
    _CHGIN_ILIM_5400    = 0x6D # 5400 mA
    _CHGIN_ILIM_5450    = 0x6E # 5450 mA
    _CHGIN_ILIM_5500    = 0x6F # 5500 mA
    _CHGIN_ILIM_5550    = 0x70 # 5550 mA
    _CHGIN_ILIM_5600    = 0x71 # 5600 mA
    _CHGIN_ILIM_5650    = 0x72 # 5650 mA
    _CHGIN_ILIM_5700    = 0x73 # 5700 mA
    _CHGIN_ILIM_5750    = 0x74 # 5750 mA
    _CHGIN_ILIM_5800    = 0x75 # 5800 mA
    _CHGIN_ILIM_5850    = 0x76 # 5850 mA
    _CHGIN_ILIM_5900    = 0x77 # 5900 mA
    _CHGIN_ILIM_5950    = 0x78 # 5950 mA
    _CHGIN_ILIM_6000    = 0x79 # 6000 mA
    _CHGIN_ILIM_6050    = 0x7A # 6050 mA
    _CHGIN_ILIM_6100    = 0x7B # 6100 mA
    _CHGIN_ILIM_6150    = 0x7C # 6150 mA
    _CHGIN_ILIM_6200    = 0x7D # 6200 mA
    _CHGIN_ILIM_6250    = 0x7E # 6250 mA
    _CHGIN_ILIM_6300    = 0x7F # 6300 mA
    _CHGIN_ILIM_MIN     = _CHGIN_ILIM_100
    _CHGIN_ILIM_MAX     = _CHGIN_ILIM_6300
    _CHGIN_ILIM_DEFAULT = _CHGIN_ILIM_500
    
    _REG_CHG_CNFG_09    = 0x1F
    _INLIM_CLK          = 0xC0 # Input Current Limit Soft-Start Period (micro seconds) Between Consecutive Increments of 25mA
    _INLIM_CLK_8        = 0x00 # 8 us
    _INLIM_CLK_256      = 0x40 # 256 us
    _INLIM_CLK_1024     = 0x80 # 1024 us ~ 1 ms
    _INLIM_CLK_4096     = 0xC0 # 4096 us ~ 4 ms
    _INLIM_CLK_MIN      = _INLIM_CLK_8
    _INLIM_CLK_MAX      = _INLIM_CLK_4096
    _INLIM_CLK_DEFAULT  = _INLIM_CLK_1024
    _OTG_ILIM           = 0x38 # OTG Mode Current Limit Setting (mA)
    _OTG_ILIM_500       = 0x00 # 500 mA
    _OTG_ILIM_900       = 0x08 # 900 mA
    _OTG_ILIM_1200      = 0x10 # 1200 mA
    _OTG_ILIM_1500      = 0x18 # 1500 mA
    _OTG_ILIM_2000      = 0x20 # 2000 mA
    _OTG_ILIM_2250      = 0x28 # 2250 mA
    _OTG_ILIM_2500      = 0x30 # 2500 mA
    _OTG_ILIM_3000      = 0x38 # 3000 mA
    _OTG_ILIM_MIN       = _OTG_ILIM_500
    _OTG_ILIM_MAX       = _OTG_ILIM_3000
    _OTG_ILIM_DEFAULT   = _OTG_ILIM_1500
    _MINVSYS            = 0x07 # Minimum System Regulation Voltage (mV)
    # 2 cells:
    _MINVSYS_2C_5535    = 0x00 # 5535 mV
    _MINVSYS_2C_5740    = 0x01 # 5740 mV
    _MINVSYS_2C_5945    = 0x02 # 5945 mV
    _MINVSYS_2C_6150    = 0x03 # 6150 mV
    _MINVSYS_2C_6355    = 0x04 # 6355 mV
    _MINVSYS_2C_6560    = 0x05 # 6560 mV
    _MINVSYS_2C_6765    = 0x06 # 6765 mV
    _MINVSYS_2C_6970    = 0x07 # 6970 mV
    _MINVSYS_2C_MIN     = _MINVSYS_2C_5535
    _MINVSYS_2C_MAX     = _MINVSYS_2C_6970
    _MINVSYS_2C_DEFAULT = _MINVSYS_2C_6150
    # 3 cells:
    _MINVSYS_3C_8303    = 0x00 # 8303 mV
    _MINVSYS_3C_8610    = 0x01 # 8610 mV
    _MINVSYS_3C_8918    = 0x02 # 8918 mV
    _MINVSYS_3C_9225    = 0x03 # 9225 mV
    _MINVSYS_3C_9533    = 0x04 # 9533 mV
    _MINVSYS_3C_9840    = 0x05 # 9840 mV
    _MINVSYS_3C_10148   = 0x06 # 10148 mV
    _MINVSYS_3C_10455   = 0x07 # 10455 mV
    _MINVSYS_3C_MIN     = _MINVSYS_3C_8303
    _MINVSYS_3C_MAX     = _MINVSYS_3C_10455
    _MINVSYS_3C_DEFAULT = _MINVSYS_3C_9225
    _MINVSYS_DEFAULT    = _MINVSYS_2C_DEFAULT
    
    _REG_CHG_CNFG_10    = 0x20
    _VCHGIN_REG         = 0x3E # CHGIN Voltage Regulation Threshold (mV)
    _VCHGIN_REG_4025    = 0x00 # 4025 mV
    _VCHGIN_REG_4200    = 0x02 # 4200 mV
    _VCHGIN_REG_4375    = 0x04 # 4375 mV
    _VCHGIN_REG_4550    = 0x06 # 4550 mV
    _VCHGIN_REG_4725    = 0x08 # 4725 mV
    _VCHGIN_REG_4900    = 0x0A # 4900 mV
    _VCHGIN_REG_5425    = 0x0C # 5425 mV
    _VCHGIN_REG_5950    = 0x0E # 5950 mV
    _VCHGIN_REG_6475    = 0x10 # 6475 mV
    _VCHGIN_REG_7000    = 0x12 # 7000 mV
    _VCHGIN_REG_7525    = 0x14 # 7525 mV
    _VCHGIN_REG_8050    = 0x16 # 8050 mV
    _VCHGIN_REG_8575    = 0x18 # 8575 mV
    _VCHGIN_REG_9100    = 0x1A # 9100 mV
    _VCHGIN_REG_9625    = 0x1C # 9625 mV
    _VCHGIN_REG_10150   = 0x1E # 10150 mV
    _VCHGIN_REG_10675   = 0x20 # 10675 mV
    _VCHGIN_REG_10950    = 0x22 # 10950 mV
    _VCHGIN_REG_11550    = 0x24 # 11550 mV
    _VCHGIN_REG_12150    = 0x26 # 12150 mV
    _VCHGIN_REG_12750    = 0x28 # 12750 mV
    _VCHGIN_REG_13350    = 0x2A # 13350 mV
    _VCHGIN_REG_13950    = 0x2C # 13950 mV
    _VCHGIN_REG_14550    = 0x2E # 14550 mV
    _VCHGIN_REG_15150    = 0x30 # 15150 mV
    _VCHGIN_REG_15750    = 0x32 # 15750 mV
    _VCHGIN_REG_16350    = 0x34 # 16350 mV
    _VCHGIN_REG_16950    = 0x36 # 16950 mV
    _VCHGIN_REG_17550    = 0x38 # 17550 mV
    _VCHGIN_REG_18150    = 0x3A # 18150 mV
    _VCHGIN_REG_18750    = 0x3C # 18750 mV
    _VCHGIN_REG_19050    = 0x3E # 19050 mV
    _VCHGIN_REG_MIN      = _VCHGIN_REG_4025
    _VCHGIN_REG_MAX      = _VCHGIN_REG_19050
    _VCHGIN_REG_DEFAULT  = _VCHGIN_REG_4725
    _DISKIP              = 0x01 # Charger Skip Mode Disable
    _DISKIP_AUTO         = 0x00 # Autoskip mode
    _DISKIP_DISABLED     = 0x01 # Disable skip mode
    _DISKIP_DEFAULT      = _DISKIP_AUTO


    #
    # Public attributes
    #
    
    
    #
    # Register / Content descriptions
    #
    
    _registerMap = [
        [_REG_CID, 'CID', ([_CID_REVISION, 'REV'], [_CID_VERSION, 'VER'], [0xFF, 'ID'])],
        [_REG_SWRST, 'SWRST', ()],
        [_REG_TOP_INT, 'TOP_INT', ([_TSHDN_I, 'TSHDN_I'], [_SYSOVLO_I, 'SYSOVLO_I'], [_SYSUVLO_I, 'SYSUVLO_I'])],
        [_REG_TOP_INT_MASK, 'TOP_INT_MASK', ([_TSHDN_M, 'TSHDN_M'], [_SYSOVLO_M, 'SYSOVLO_M'], [_SYSUVLO_M, 'SYSUVLO_M'])],
        [_REG_TOP_INT_OK, 'TOP_INT_OK', ([_TSHDN_OK, 'TSHDN_OK'], [_SYSOVLO_OK, 'SYSOVLO_OK'], [_SYSUVLO_OK, 'SYSUVLO_OK'])],
        [_REG_CHG_INT, 'CHG_INT', ([_AICL_I, 'AICL_I'], [_CHGIN_I, 'CHGIN_I'], [_B2SOVRC_I, 'B2SOVRC_I'], [_CHG_I, '_CHG_I'],
            [_BAT_I, 'BAT_I'], [_CHGINLIM_I, 'CHGINLIM_I'], [_DISQBAT_I, 'DISQBAT_I'], [_OTG_PLIM_I, 'OTG_PLIM_I'])],
        [_REG_CHG_INT_MASK, 'CHG_INT_MASK', ([_AICL_M, 'AICL_M'], [_CHGIN_M, 'CHGIN_M'], [_B2SOVRC_M, 'B2SOVRC_M'],
            [_CHG_M, 'CHG_M'], [_BAT_M, 'BAT_M'], [_CHGINLIM_M, 'CHGINLIM_M'], [_DISQBAT_M, 'DISQBAT_M'], [_OTG_PLIM_M, 'OTG_PLIM_M'])],
        [_REG_CHG_INT_OK, 'CHG_INT_OK', ([_AICL_OK, 'AICL_OK'], [_CHGIN_OK, 'CHGIN_OK'], [_B2SOVRC_OK, 'B2SOVRC_OK'],
            [_CHG_OK, 'CHG_OK'], [_BAT_OK, 'BAT_OK'], [_CHGINLIM_OK, 'CHGINLIM_OK'], [_DISQBAT_OK, 'DISQBAT_OK'],
            [_OTG_PLIM_OK, 'OTG_PLIM_OK'])],
        [_REG_CHG_DETAILS_00, 'CHG_DETAILS_00', ([_CHGIN_DTLS, 'CHGIN_DTLS'], [_OTG_DTLS, 'OTG_DTLS'], [_QB_DTLS, 'QB_DTLS'])],
        [_REG_CHG_DETAILS_01, 'CHG_DETAILS_01', ([_TREG, 'TREG'], [_BAT_DTLS, 'BAT_DTLS'], [_CHG_DTLS, 'CHG_DTLS'])],
        [_REG_CHG_DETAILS_02, 'CHG_DETAILS_02', ([_THM_DTLS, 'THM_DTLS'], [_APP_MODE_DTLS, 'APP_MODE_DTLS'],
                                                 [_FSW_DTLS, 'FSW_DTLS'], [_NUM_CELL_DTLS, 'NUM_CELL_DTLS'])],
        [_REG_CHG_CNFG_00, 'CHG_CNFG_00', ([_COMM_MODE, 'COMM_MODE'], [_DISIBS, 'DISIBS'], [_STBY_EN, 'STBY_EN'],
                                           [_WDTEN, 'WDTEN'], [_MODE, 'MODE'])],
        [_REG_CHG_CNFG_01, 'CHG_CNFG_01', ([_PQEN, 'PQEN'], [_LPM, 'LPM'], [_CHG_RSTRT, 'CHG_RSTRT'], 
                                           [_STAT_EN, 'STAT_EN'], [_FCHGTIME, 'FCHGTIME'])],
        [_REG_CHG_CNFG_02, 'CHG_CNFG_02', ([_CHGCC, 'CHGCC'],)],
        [_REG_CHG_CNFG_03, 'CHG_CNFG_03', ([_SYS_TRACK_DIS, 'SYS_TRACK_DIS'], [_B2SOVRC_DTC, 'B2SOVRC_DTC'],
                                           [_TO_TIME, 'TO_TIME'], [_TO_ITH, 'TO_ITH'])],
        [_REG_CHG_CNFG_04, 'CHG_CNFG_04', ([_CHG_CV_PRM, 'CHG_CV_PRM'],)],
        [_REG_CHG_CNFG_05, 'CHG_CNFG_05', ([_ITRICKLE, 'ITRICKLE'], [_B2SOVRC, 'B2SOVRC'])],
        [_REG_CHG_CNFG_06, 'CHG_CNFG_06', ([_CHGPROT, 'CHGPROT'], [_WDTCLR, 'WDTCLR'])],
        [_REG_CHG_CNFG_07, 'CHG_CNFG_07', ([_JEITA_EN, 'JEITA_EN'], [_REGTEMP, 'REGTEMP'], [_VCHGCV_COOL, 'VCHGCV_COOL'],
                                           [_ICHGCC_COOL, 'ICHGCC_COOL'], [_FSHIP_MODE, 'FSHIP_MODE'])],
        [_REG_CHG_CNFG_08, 'CHG_CNFG_08', ([_CHGIN_ILIM, 'CHGIN_ILIM'],)],
        [_REG_CHG_CNFG_09, 'CHG_CNFG_09', ([_INLIM_CLK, 'INLIM_CLK'], [_OTG_ILIM, 'OTG_ILIM'], [_MINVSYS, 'MINVSYS'])],
        [_REG_CHG_CNFG_10, 'CHG_CNFG_10', ([_VCHGIN_REG, 'VCHGIN_REG'], [_DISKIP, 'DISKIP'])],
    ]
    
    def getRegisterMap(self):
        return self._registerMap
    
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
            cont = self.getReg( descr[0] )
            contStr = self.getRegContentStr( descr, cont )
            ret.append([descr[0], descr[1], cont, contStr])
        return ret
            
    #
    # Configurable API
    #
    
    CFG_COMM_MODE = 'Charger.Comm.Mode'
    CFG_COMM_MODE_AUTO = _COMM_MODE_AUTO
    CFG_COMM_MODE_I2C  = _COMM_MODE_I2C
    CFG_DISIBS = 'Charger.DisIBS'
    CFG_DISIBS_FET_PPSM = _DISIBS_FET_PPSM
    CFG_DISIBS_FET_OFF  = _DISIBS_FET_OFF
    CFG_MODE = 'Charger.Mode'
    CFG_MODE_ALL_OFF   = _MODE_ALL_OFF
    CFG_MODE_CHRG_DCDC = _MODE_CHRG_DCDC
    CFG_MODE_DCDC_ONLY = _MODE_DCDC_ONLY
    CFG_MODE_OTG_ONLY  = _MODE_OTG_ONLY
    CFG_PQEN = 'Charger.Prequal'
    CFG_PQEN_ON  = _PQEN_ON
    CFG_PQEN_OFF = _PQEN_OFF
    CFG_CHG_RSTRT = 'Charger.Restart'
    CFG_CHG_RSTRT_100 = _CHG_RSTRT_100
    CFG_CHG_RSTRT_150 = _CHG_RSTRT_150
    CFG_CHG_RSTRT_200 = _CHG_RSTRT_200
    CFG_CHG_RSTRT_DISABLED = _CHG_RSTRT_DISABLED
    CFG_STAT_EN = 'Charger.Stat'
    CFG_STAT_EN_ON  = _STAT_EN_ON
    CFG_STAT_EN_OFF = _STAT_EN_OFF
    CFG_FCHGTIME = 'Charger.Timer.FastCharge'
    CFG_FCHGTIME_DISABLED = _FCHGTIME_DISABLED
    CFG_FCHGTIME_3H = _FCHGTIME_3H
    CFG_FCHGTIME_4H = _FCHGTIME_4H
    CFG_FCHGTIME_5H = _FCHGTIME_5H
    CFG_FCHGTIME_6H = _FCHGTIME_6H
    CFG_FCHGTIME_7H = _FCHGTIME_7H
    CFG_FCHGTIME_8H = _FCHGTIME_8H
    CFG_FCHGTIME_10H= _FCHGTIME_10H
    CFG_CHGCC = 'Charger.Current.FastCharge'
    CFG_CHGCC_100  = _CHGCC_100
    CFG_CHGCC_150  = _CHGCC_150
    CFG_CHGCC_200  = _CHGCC_200
    CFG_CHGCC_250  = _CHGCC_250
    CFG_CHGCC_300  = _CHGCC_300
    CFG_CHGCC_350  = _CHGCC_350
    CFG_CHGCC_400  = _CHGCC_400
    CFG_CHGCC_450  = _CHGCC_450
    CFG_CHGCC_500  = _CHGCC_500
    CFG_CHGCC_600  = _CHGCC_600
    CFG_CHGCC_700  = _CHGCC_700
    CFG_CHGCC_800  = _CHGCC_800
    CFG_CHGCC_900  = _CHGCC_900
    CFG_CHGCC_1000  = _CHGCC_1000
    CFG_CHGCC_1100  = _CHGCC_1100
    CFG_CHGCC_1200  = _CHGCC_1200
    CFG_CHGCC_1300  = _CHGCC_1300
    CFG_CHGCC_1400  = _CHGCC_1400
    CFG_CHGCC_1500  = _CHGCC_1500
    CFG_CHGCC_1600  = _CHGCC_1600
    CFG_CHGCC_1700  = _CHGCC_1700
    CFG_CHGCC_1800  = _CHGCC_1800
    CFG_CHGCC_1900  = _CHGCC_1900
    CFG_CHGCC_2000  = _CHGCC_2000
    CFG_CHGCC_2100  = _CHGCC_2100
    CFG_CHGCC_2200  = _CHGCC_2200
    CFG_CHGCC_2300  = _CHGCC_2300
    CFG_CHGCC_2400  = _CHGCC_2400
    CFG_CHGCC_2500  = _CHGCC_2500
    CFG_CHGCC_2600  = _CHGCC_2600
    CFG_CHGCC_2700  = _CHGCC_2700
    CFG_CHGCC_2800  = _CHGCC_2800
    CFG_CHGCC_2900  = _CHGCC_2900
    CFG_CHGCC_3000  = _CHGCC_3000
    CFG_CHGCC_3100  = _CHGCC_3100
    CFG_CHGCC_3200  = _CHGCC_3200
    CFG_CHGCC_3300  = _CHGCC_3300
    CFG_CHGCC_3400  = _CHGCC_3400
    CFG_CHGCC_3500  = _CHGCC_3500
    CFG_CHGCC_3600  = _CHGCC_3600
    CFG_CHGCC_3700  = _CHGCC_3700
    CFG_CHGCC_3800  = _CHGCC_3800
    CFG_CHGCC_3900  = _CHGCC_3900
    CFG_CHGCC_4000  = _CHGCC_4000
    CFG_CHGCC_4100  = _CHGCC_4100
    CFG_CHGCC_4200  = _CHGCC_4200
    CFG_CHGCC_4300  = _CHGCC_4300
    CFG_CHGCC_4400  = _CHGCC_4400
    CFG_CHGCC_4500  = _CHGCC_4500
    CFG_CHGCC_4600  = _CHGCC_4600
    CFG_CHGCC_4700  = _CHGCC_4700
    CFG_CHGCC_4800  = _CHGCC_4800
    CFG_CHGCC_4900  = _CHGCC_4900
    CFG_CHGCC_5000  = _CHGCC_5000
    CFG_CHGCC_5100  = _CHGCC_5100
    CFG_CHGCC_5200  = _CHGCC_5200
    CFG_CHGCC_5300  = _CHGCC_5300
    CFG_CHGCC_5400  = _CHGCC_5400
    CFG_CHGCC_5500  = _CHGCC_5500
    CFG_CHGCC_5600  = _CHGCC_5600
    CFG_CHGCC_5700  = _CHGCC_5700
    CFG_CHGCC_5800  = _CHGCC_5800
    CFG_CHGCC_5900  = _CHGCC_5900
    CFG_CHGCC_6000  = _CHGCC_6000
    CFG_TO_TIME = 'Charger.Timer.Topoff'
    CFG_TO_TIME_30_SEC = _TO_TIME_30_SEC
    CFG_TO_TIME_10_MIN = _TO_TIME_10_MIN
    CFG_TO_TIME_20_MIN = _TO_TIME_20_MIN
    CFG_TO_TIME_30_MIN = _TO_TIME_30_MIN
    CFG_TO_TIME_40_MIN = _TO_TIME_40_MIN
    CFG_TO_TIME_50_MIN = _TO_TIME_50_MIN
    CFG_TO_TIME_60_MIN = _TO_TIME_60_MIN
    CFG_TO_TIME_70_MIN = _TO_TIME_70_MIN
    CFG_TO_ITH = 'Charger.Current.Topoff'
    CFG_TO_ITH_100 = _TO_ITH_100
    CFG_TO_ITH_200 = _TO_ITH_200
    CFG_TO_ITH_300 = _TO_ITH_300
    CFG_TO_ITH_400 = _TO_ITH_400
    CFG_TO_ITH_500 = _TO_ITH_500
    CFG_TO_ITH_600 = _TO_ITH_600
    CFG_CHG_CV_PRM = 'Charger.Voltage.ChargeTermination'
    CFG_CHG_CV_PRM_2C_8000 = _CHG_CV_PRM_2C_8000
    CFG_CHG_CV_PRM_2C_8020 = _CHG_CV_PRM_2C_8020
    CFG_CHG_CV_PRM_2C_8040 = _CHG_CV_PRM_2C_8040
    CFG_CHG_CV_PRM_2C_8060 = _CHG_CV_PRM_2C_8060
    CFG_CHG_CV_PRM_2C_8080 = _CHG_CV_PRM_2C_8080
    CFG_CHG_CV_PRM_2C_8100 = _CHG_CV_PRM_2C_8100
    CFG_CHG_CV_PRM_2C_8120 = _CHG_CV_PRM_2C_8120
    CFG_CHG_CV_PRM_2C_8130 = _CHG_CV_PRM_2C_8140
    CFG_CHG_CV_PRM_2C_8140 = _CHG_CV_PRM_2C_8160
    CFG_CHG_CV_PRM_2C_8150 = _CHG_CV_PRM_2C_8180
    CFG_CHG_CV_PRM_2C_8200 = _CHG_CV_PRM_2C_8200
    CFG_CHG_CV_PRM_2C_8220 = _CHG_CV_PRM_2C_8220
    CFG_CHG_CV_PRM_2C_8240 = _CHG_CV_PRM_2C_8240
    CFG_CHG_CV_PRM_2C_8260 = _CHG_CV_PRM_2C_8260
    CFG_CHG_CV_PRM_2C_8280 = _CHG_CV_PRM_2C_8280
    CFG_CHG_CV_PRM_2C_8300 = _CHG_CV_PRM_2C_8300
    CFG_CHG_CV_PRM_2C_8320 = _CHG_CV_PRM_2C_8320
    CFG_CHG_CV_PRM_2C_8340 = _CHG_CV_PRM_2C_8340
    CFG_CHG_CV_PRM_2C_8360 = _CHG_CV_PRM_2C_8360
    CFG_CHG_CV_PRM_2C_8380 = _CHG_CV_PRM_2C_8380
    CFG_CHG_CV_PRM_2C_8400 = _CHG_CV_PRM_2C_8400
    CFG_CHG_CV_PRM_2C_8420 = _CHG_CV_PRM_2C_8420
    CFG_CHG_CV_PRM_2C_8440 = _CHG_CV_PRM_2C_8440
    CFG_CHG_CV_PRM_2C_8460 = _CHG_CV_PRM_2C_8460
    CFG_CHG_CV_PRM_2C_8480 = _CHG_CV_PRM_2C_8480
    CFG_CHG_CV_PRM_2C_8500 = _CHG_CV_PRM_2C_8500
    CFG_CHG_CV_PRM_2C_8520 = _CHG_CV_PRM_2C_8520
    CFG_CHG_CV_PRM_2C_8540 = _CHG_CV_PRM_2C_8540
    CFG_CHG_CV_PRM_2C_8560 = _CHG_CV_PRM_2C_8560
    CFG_CHG_CV_PRM_2C_8580 = _CHG_CV_PRM_2C_8580
    CFG_CHG_CV_PRM_2C_8600 = _CHG_CV_PRM_2C_8600
    CFG_CHG_CV_PRM_2C_8620 = _CHG_CV_PRM_2C_8620
    CFG_CHG_CV_PRM_2C_8640 = _CHG_CV_PRM_2C_8640
    CFG_CHG_CV_PRM_2C_8660 = _CHG_CV_PRM_2C_8660
    CFG_CHG_CV_PRM_2C_8680 = _CHG_CV_PRM_2C_8680
    CFG_CHG_CV_PRM_2C_8700 = _CHG_CV_PRM_2C_8700
    CFG_CHG_CV_PRM_2C_8720 = _CHG_CV_PRM_2C_8720
    CFG_CHG_CV_PRM_2C_8740 = _CHG_CV_PRM_2C_8740
    CFG_CHG_CV_PRM_2C_8760 = _CHG_CV_PRM_2C_8760
    CFG_CHG_CV_PRM_2C_8780 = _CHG_CV_PRM_2C_8780
    CFG_CHG_CV_PRM_2C_8800 = _CHG_CV_PRM_2C_8800
    CFG_CHG_CV_PRM_2C_8820 = _CHG_CV_PRM_2C_8820
    CFG_CHG_CV_PRM_2C_8840 = _CHG_CV_PRM_2C_8840
    CFG_CHG_CV_PRM_2C_8860 = _CHG_CV_PRM_2C_8860
    CFG_CHG_CV_PRM_2C_8880 = _CHG_CV_PRM_2C_8880
    CFG_CHG_CV_PRM_2C_8900 = _CHG_CV_PRM_2C_8900
    CFG_CHG_CV_PRM_2C_8920 = _CHG_CV_PRM_2C_8920
    CFG_CHG_CV_PRM_2C_8940 = _CHG_CV_PRM_2C_8940
    CFG_CHG_CV_PRM_2C_8960 = _CHG_CV_PRM_2C_8960
    CFG_CHG_CV_PRM_2C_8980 = _CHG_CV_PRM_2C_8980
    CFG_CHG_CV_PRM_2C_9000 = _CHG_CV_PRM_2C_9000
    CFG_CHG_CV_PRM_2C_9020 = _CHG_CV_PRM_2C_9020
    CFG_CHG_CV_PRM_2C_9040 = _CHG_CV_PRM_2C_9040
    CFG_CHG_CV_PRM_2C_9060 = _CHG_CV_PRM_2C_9060
    CFG_CHG_CV_PRM_2C_9080 = _CHG_CV_PRM_2C_9080
    CFG_CHG_CV_PRM_2C_9100 = _CHG_CV_PRM_2C_9100
    CFG_CHG_CV_PRM_2C_9120 = _CHG_CV_PRM_2C_9120
    CFG_CHG_CV_PRM_2C_9140 = _CHG_CV_PRM_2C_9140
    CFG_CHG_CV_PRM_2C_9160 = _CHG_CV_PRM_2C_9160
    CFG_CHG_CV_PRM_2C_9180 = _CHG_CV_PRM_2C_9180
    CFG_CHG_CV_PRM_2C_9200 = _CHG_CV_PRM_2C_9200
    CFG_CHG_CV_PRM_2C_9220 = _CHG_CV_PRM_2C_9220
    CFG_CHG_CV_PRM_2C_9240 = _CHG_CV_PRM_2C_9240
    CFG_CHG_CV_PRM_2C_9260 = _CHG_CV_PRM_2C_9260
    CFG_CHG_CV_PRM_3C_12000 = _CHG_CV_PRM_3C_12000
    CFG_CHG_CV_PRM_3C_12030 = _CHG_CV_PRM_3C_12030
    CFG_CHG_CV_PRM_3C_12060 = _CHG_CV_PRM_3C_12060
    CFG_CHG_CV_PRM_3C_12090 = _CHG_CV_PRM_3C_12090
    CFG_CHG_CV_PRM_3C_12120 = _CHG_CV_PRM_3C_12120
    CFG_CHG_CV_PRM_3C_12150 = _CHG_CV_PRM_3C_12150
    CFG_CHG_CV_PRM_3C_12180 = _CHG_CV_PRM_3C_12180
    CFG_CHG_CV_PRM_3C_12210 = _CHG_CV_PRM_3C_12210
    CFG_CHG_CV_PRM_3C_12240 = _CHG_CV_PRM_3C_12240
    CFG_CHG_CV_PRM_3C_12270 = _CHG_CV_PRM_3C_12270
    CFG_CHG_CV_PRM_3C_12300 = _CHG_CV_PRM_3C_12300
    CFG_CHG_CV_PRM_3C_12330 = _CHG_CV_PRM_3C_12330
    CFG_CHG_CV_PRM_3C_12360 = _CHG_CV_PRM_3C_12360
    CFG_CHG_CV_PRM_3C_12390 = _CHG_CV_PRM_3C_12390
    CFG_CHG_CV_PRM_3C_12420 = _CHG_CV_PRM_3C_12420
    CFG_CHG_CV_PRM_3C_12450 = _CHG_CV_PRM_3C_12450
    CFG_CHG_CV_PRM_3C_12480 = _CHG_CV_PRM_3C_12480
    CFG_CHG_CV_PRM_3C_12510 = _CHG_CV_PRM_3C_12510
    CFG_CHG_CV_PRM_3C_12540 = _CHG_CV_PRM_3C_12540
    CFG_CHG_CV_PRM_3C_12570 = _CHG_CV_PRM_3C_12570
    CFG_CHG_CV_PRM_3C_12600 = _CHG_CV_PRM_3C_12600
    CFG_CHG_CV_PRM_3C_12630 = _CHG_CV_PRM_3C_12630
    CFG_CHG_CV_PRM_3C_12660 = _CHG_CV_PRM_3C_12660
    CFG_CHG_CV_PRM_3C_12690 = _CHG_CV_PRM_3C_12690
    CFG_CHG_CV_PRM_3C_12720 = _CHG_CV_PRM_3C_12720
    CFG_CHG_CV_PRM_3C_12750 = _CHG_CV_PRM_3C_12750
    CFG_CHG_CV_PRM_3C_12780 = _CHG_CV_PRM_3C_12780
    CFG_CHG_CV_PRM_3C_12810 = _CHG_CV_PRM_3C_12810
    CFG_CHG_CV_PRM_3C_12840 = _CHG_CV_PRM_3C_12840
    CFG_CHG_CV_PRM_3C_12870 = _CHG_CV_PRM_3C_12870
    CFG_CHG_CV_PRM_3C_12900 = _CHG_CV_PRM_3C_12900
    CFG_CHG_CV_PRM_3C_12930 = _CHG_CV_PRM_3C_12930
    CFG_CHG_CV_PRM_3C_12960 = _CHG_CV_PRM_3C_12960
    CFG_CHG_CV_PRM_3C_12990 = _CHG_CV_PRM_3C_12990
    CFG_CHG_CV_PRM_3C_13020 = _CHG_CV_PRM_3C_13020
    CFG_CHG_CV_PRM_3C_13050 = _CHG_CV_PRM_3C_13050
    CFG_ITRICKLE = 'Charger.Current.Trickle'
    CFG_ITRICKLE_100 = _ITRICKLE_100
    CFG_ITRICKLE_200 = _ITRICKLE_200
    CFG_ITRICKLE_300 = _ITRICKLE_300
    CFG_ITRICKLE_400 = _ITRICKLE_400
    CFG_B2SOVRC = 'Charger.Current.Batt2Sys'
    CFG_B2SOVRC_DISABLED = _B2SOVRC_DISABLED
    CFG_B2SOVRC_3000 = _B2SOVRC_3000
    CFG_B2SOVRC_3500 = _B2SOVRC_3500
    CFG_B2SOVRC_4000 = _B2SOVRC_4000
    CFG_B2SOVRC_4500 = _B2SOVRC_4500
    CFG_B2SOVRC_5000 = _B2SOVRC_5000
    CFG_B2SOVRC_5500 = _B2SOVRC_5500
    CFG_B2SOVRC_6000 = _B2SOVRC_6000
    CFG_B2SOVRC_6500 = _B2SOVRC_6500
    CFG_B2SOVRC_7000 = _B2SOVRC_7000
    CFG_B2SOVRC_7500 = _B2SOVRC_7500
    CFG_B2SOVRC_8000 = _B2SOVRC_8000
    CFG_B2SOVRC_8500 = _B2SOVRC_8500
    CFG_B2SOVRC_9000 = _B2SOVRC_9000
    CFG_B2SOVRC_9500 = _B2SOVRC_9500
    CFG_B2SOVRC_10000= _B2SOVRC_10000
    CFG_JEITA_EN = 'Charger.Jeita'
    CFG_JEITA_EN_ON  = _JEITA_EN_ON
    CFG_JEITA_EN_OFF = _JEITA_EN_OFF
    CFG_REGTEMP = 'Charger.Temp.Reg'
    CFG_REGTEMP_85  = _REGTEMP_85
    CFG_REGTEMP_90  = _REGTEMP_90
    CFG_REGTEMP_95  = _REGTEMP_95
    CFG_REGTEMP_100 = _REGTEMP_100
    CFG_REGTEMP_105 = _REGTEMP_105
    CFG_REGTEMP_110 = _REGTEMP_110
    CFG_REGTEMP_115 = _REGTEMP_115
    CFG_REGTEMP_120 = _REGTEMP_120
    CFG_REGTEMP_125 = _REGTEMP_125
    CFG_REGTEMP_130 = _REGTEMP_130
    CFG_VCHGCV_COOL = 'Charger.Voltage.Jeita.Term'
    CFG_VCHGCV_COOL_NORMAL  = _VCHGCV_COOL_NORMAL
    CFG_VCHGCV_COOL_REDUCED = _VCHGCV_COOL_REDUCED
    CFG_ICHGCC_COOL = 'Charger.Current.Jeita.FastCharge'
    CFG_ICHGCC_COOL_NORMAL  = _ICHGCC_COOL_NORMAL
    CFG_ICHGCC_COOL_REDUCED = _ICHGCC_COOL_REDUCED
    CFG_CHGIN_ILIM = 'Charger.Current.Input'
    CFG_OTG_ILIM = 'Charger.Current.OTG'
    CFG_OTG_ILIM_500 = _OTG_ILIM_500
    CFG_OTG_ILIM_900 = _OTG_ILIM_900
    CFG_OTG_ILIM_1200= _OTG_ILIM_1200
    CFG_OTG_ILIM_1500= _OTG_ILIM_1500
    CFG_OTG_ILIM_2000= _OTG_ILIM_2000
    CFG_OTG_ILIM_2250= _OTG_ILIM_2250
    CFG_OTG_ILIM_2500= _OTG_ILIM_2500
    CFG_OTG_ILIM_3000= _OTG_ILIM_3000
    CFG_MINVSYS = 'Charger.Voltage.MinVSys'
    CFG_MINVSYS_2C_5535 = _MINVSYS_2C_5535
    CFG_MINVSYS_2C_5740 = _MINVSYS_2C_5740
    CFG_MINVSYS_2C_5945 = _MINVSYS_2C_5945
    CFG_MINVSYS_2C_6150 = _MINVSYS_2C_6150
    CFG_MINVSYS_2C_6355 = _MINVSYS_2C_6355
    CFG_MINVSYS_2C_6560 = _MINVSYS_2C_6560
    CFG_MINVSYS_2C_6765 = _MINVSYS_2C_6765
    CFG_MINVSYS_2C_6970 = _MINVSYS_2C_6970
    CFG_MINVSYS_3C_8303 = _MINVSYS_3C_8303
    CFG_MINVSYS_3C_8610 = _MINVSYS_3C_8610
    CFG_MINVSYS_3C_8918 = _MINVSYS_3C_8918
    CFG_MINVSYS_3C_9225 = _MINVSYS_3C_9225
    CFG_MINVSYS_3C_9533 = _MINVSYS_3C_9533
    CFG_MINVSYS_3C_9840 = _MINVSYS_3C_9840
    CFG_MINVSYS_3C_10148= _MINVSYS_3C_10148
    CFG_MINVSYS_3C_10455= _MINVSYS_3C_10455
    CFG_VCHGIN_REG = 'Charger.Voltage.ChargeIn'
    CFG_VCHGIN_REG_4025 = _VCHGIN_REG_4025
    CFG_VCHGIN_REG_4200 = _VCHGIN_REG_4200
    CFG_VCHGIN_REG_4375 = _VCHGIN_REG_4375
    CFG_VCHGIN_REG_4550 = _VCHGIN_REG_4550
    CFG_VCHGIN_REG_4725 = _VCHGIN_REG_4725
    CFG_VCHGIN_REG_4900 = _VCHGIN_REG_4900
    CFG_VCHGIN_REG_5425 = _VCHGIN_REG_5425
    CFG_VCHGIN_REG_5950 = _VCHGIN_REG_5950
    CFG_VCHGIN_REG_6475 = _VCHGIN_REG_6475
    CFG_VCHGIN_REG_7000 = _VCHGIN_REG_7000
    CFG_VCHGIN_REG_7525 = _VCHGIN_REG_7525
    CFG_VCHGIN_REG_8050 = _VCHGIN_REG_8050
    CFG_VCHGIN_REG_8575 = _VCHGIN_REG_8575
    CFG_VCHGIN_REG_9100 = _VCHGIN_REG_9100
    CFG_VCHGIN_REG_9625 = _VCHGIN_REG_9625
    CFG_VCHGIN_REG_10150 = _VCHGIN_REG_10150
    CFG_VCHGIN_REG_10675 = _VCHGIN_REG_10675
    CFG_VCHGIN_REG_10950 = _VCHGIN_REG_10950
    CFG_VCHGIN_REG_11550 = _VCHGIN_REG_11550
    CFG_VCHGIN_REG_12150 = _VCHGIN_REG_12150
    CFG_VCHGIN_REG_12750 = _VCHGIN_REG_12750
    CFG_VCHGIN_REG_13350 = _VCHGIN_REG_13350
    CFG_VCHGIN_REG_13950 = _VCHGIN_REG_13950
    CFG_VCHGIN_REG_14550 = _VCHGIN_REG_14550
    CFG_VCHGIN_REG_15150 = _VCHGIN_REG_15150
    CFG_VCHGIN_REG_15750 = _VCHGIN_REG_15750
    CFG_VCHGIN_REG_16350 = _VCHGIN_REG_16350
    CFG_VCHGIN_REG_16950 = _VCHGIN_REG_16950
    CFG_VCHGIN_REG_17550 = _VCHGIN_REG_17550
    CFG_VCHGIN_REG_18150 = _VCHGIN_REG_18150
    CFG_VCHGIN_REG_18750 = _VCHGIN_REG_18750
    CFG_VCHGIN_REG_19050 = _VCHGIN_REG_19050

    _CONFIGURABLES = {CFG_COMM_MODE, CFG_DISIBS, CFG_MODE,
                      CFG_PQEN, CFG_CHG_RSTRT, CFG_STAT_EN, CFG_FCHGTIME,
                      CFG_CHGCC,
                      CFG_TO_TIME, CFG_TO_ITH,
                      CFG_CHG_CV_PRM,
                      CFG_ITRICKLE, CFG_B2SOVRC,
                      #skip config register 06
                      CFG_JEITA_EN, CFG_REGTEMP, CFG_VCHGCV_COOL, CFG_ICHGCC_COOL,
                      CFG_CHGIN_ILIM,
                      CFG_OTG_ILIM, CFG_MINVSYS,
                      CFG_VCHGIN_REG, }
    
    def _scanParameters( self, paramDict ):
        super()._scanParameters( paramDict )
        self._config = {}
        for key in paramDict:
            if key in MAX77960._CONFIGURABLES:
                self._config.update( {key: paramDict[key]} )

    #
    # Note that config registers #1, 2, 3, 4, 5, 7, 8, 9
    # are write protected (locked), while #0, 6, 10
    # are not.
    #
    def _applyConfiguration( self ):
        super()._applyConfiguration()
        if self._config:
            reg= [MAX77960._REG_CHG_CNFG_00, MAX77960._REG_CHG_CNFG_01, MAX77960._REG_CHG_CNFG_02, MAX77960._REG_CHG_CNFG_03,
                  MAX77960._REG_CHG_CNFG_04, MAX77960._REG_CHG_CNFG_05, MAX77960._REG_CHG_CNFG_06, MAX77960._REG_CHG_CNFG_07,
                  MAX77960._REG_CHG_CNFG_08, MAX77960._REG_CHG_CNFG_09, MAX77960._REG_CHG_CNFG_10]
            mask=[ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            data=[ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            for key in self._config:
                value = self._config[key]
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
    
            self.unlockRegisters()
            for idx in range( len( reg ) ):
                if mask[idx] != 0:
                    self.copyReg( reg[idx], mask[idx], data[idx] )
            self.lockRegisters()

    #
    # Constructor
    # The only input parameter is a dictionary containing key-value pairs that
    # configure the instance. Regarded key names and their meanings are:
    # busType      : One of the SerialDevice.BUSTYPE_xxx values.
    # busDesignator: The bus designator. May be a name or number, such as "/dev/i2c-3" or 1.
    # deviceAddress: The I2C address (0x69).
    def __init__( self, paramDict ):
        # Specific instance attributes
        self._config = None
        # Override default base class parameter: serial device
        if not ("SerialDevice.deviceAddress" in paramDict):
            paramDict["SerialDevice.deviceAddress"] = MAX77960._ADRESSES_ALLOWED[0]
        # Call constructors of the super class
        super().__init__(paramDict)

    def _preConfig(self):
        # Test address
        try:
            self.testConnection()
        except OSError:
            pass

    #
    # Initializes the device. Is automatically called while instantiating
    # a new object. Can be used to re-initialize a sensor, e.g. after
    # resetting.
    # Raises OSError in case of problems with the connection.
    #
    def init(self):
        super().init()
        
    #
    # Re-configures the instance according to the parameters provided.
    # As with the constructor, the only parameter is the configuration dictionary.
    #
    def configure(self, paramDict):
        Charger.configure( self, paramDict )
        Watchdog.configure( self, paramDict )
        # self.setReg( MAX77960._REG_CHG_CNFG_00,
        #              MAX77960._COMM_MODE_I2C |
        #              MAX77960._DISIBS_DEFAULT |
        #              MAX77960._STBY_EN_DCDC_DEFAULT |
        #              MAX77960._WDTEN_OFF |
        #              MAX77960._MODE_CHRG_DCDC )
    
    #
    # Just closes the device. Should be called at the end of a program.
    #
    def close(self):
        super().close()

    #
    # Soft resets the device. The device is in some default state, afterwards and
    # must be re-configured according to the application's needs.
    #
    def reset(self):
        self.setReg(MAX77960._REG_SWRST, MAX77960._SWRST_TYPE_O)

    #
    # Returns the chip ID.
    # Raises OSError, in case of problems with the connection.
    #
    def getID(self):
        chipID = self.getReg(MAX77960._REG_CID)
        return chipID

    #
    # Retrieves the silicon revision part of the chip ID.
    # 
    def _getSiliconRevision(self):
        chipID = self.getID()
        siliconRevision = chipID & MAX77960._CID_REVISION
        return siliconRevision
        
    #
    # Reads the chip ID and verifies it against the
    # expected value.
    # Raises OSError, in case of problems with the connection.
    #        ValueError, if chip ID is not as expected
    #
    def checkID(self):
        sr = self._getSiliconRevision()
        if (sr < MAX77960._CID_REV_MIN) or (sr > MAX77960._CID_REV_MAX):
            raise ValueError('Unsupported silicon revision (' + str(sr) + ')!')

    #
    # Tests the communication with the sensor device.
    # Raises OSError, in case of problems with the connection.
    def testConnection(self):
        self.getID()

    #
    # Charger API
    #
    
    #
    # Checks, if the battery is present.
    # Returns TRUE if a battery is present, FALSE otherwise. The return value does not tell
    # about whether the battery is charged or not.
    # Raises RuntimeError in case the battery status cannot be determined.
    #
    def isBatteryPresent(self):
        data = self.getReg( MAX77960._REG_CHG_DETAILS_01 )
        data = data & MAX77960._BAT_DTLS
        return (data != MAX77960._BAT_DTLS_REMOVAL)
    
    #
    # Retrieves the number of battery cells configured.
    # Raises RuntimeError in case the battery status cannot be determined.
    #
    def getNumCells(self):
        data = self.getReg( MAX77960._REG_CHG_DETAILS_02 )
        data = data & MAX77960._NUM_CELL_DTLS
        if data == MAX77960._NUM_CELL_DTLS_3:
            ret = 3
        else:
            ret = 2
        return ret
    
    #
    # Get the battery status.
    # Returns one of the BAT_STATE_xxx values to indicate battery voltage level or 
    # presence or health state.
    # Raises RuntimeError in case this information cannot be determined.
    #
    def getBatStatus(self):
        data = self.getReg( MAX77960._REG_CHG_DETAILS_01 )
        ds = data & MAX77960._BAT_DTLS
        ret = Charger.BAT_STATE_UNKNOWN
        if ds == MAX77960._BAT_DTLS_REMOVAL:
            ret = Charger.BAT_STATE_REMOVED
        elif ds == MAX77960._BAT_DTLS_BELOW_PREQ:
            ret = Charger.BAT_STATE_EMPTY
        elif ds == MAX77960._BAT_DTLS_TIME_OUT:
            ret = Charger.BAT_STATE_TIME
        elif ds == MAX77960._BAT_DTLS_OK:
            ret = Charger.BAT_STATE_NORMAL
        elif ds == MAX77960._BAT_DTLS_LOW_VOLT:
            ret = Charger.BAT_STATE_LOW
        elif ds == MAX77960._BAT_DTLS_OVR_VOLT:
            ret = Charger.BAT_STATE_OVERVOLTAGE
        elif ds == MAX77960._BAT_DTLS_OVR_CURR:
            ret = Charger.BAT_STATE_OVERCURRENT
        else:
            ret = Charger.BAT_STATE_UNKNOWN
        return ret
    
    #
    # Retrieves the charge phase or status.
    # Returns one of the STATE_xxx values to indicate the current charge status.
    # Raises RuntimeError in case the charge status cannot be determined.
    #
    def getChgStatus(self):
        data = self.getReg( MAX77960._REG_CHG_DETAILS_01 )
        cd = data & MAX77960._CHG_DTLS
        ret = Charger.CHG_STATE_OFF
        if cd == MAX77960._CHG_DTLS_PRECHRG:
            bd = data & MAX77960._BAT_DTLS
            if bd == MAX77960._BAT_DTLS_BELOW_PREQ:
                ret = Charger.CHG_STATE_PRECHARGE
            else:
                ret = Charger.CHG_STATE_TRICKLE
        elif cd == MAX77960._CHG_DTLS_FAST_CURR:
            ret = Charger.CHG_STATE_FAST_CC
        elif cd == MAX77960._CHG_DTLS_FAST_VOLT:
            ret = Charger.CHG_STATE_FAST_CV
        elif cd == MAX77960._CHG_DTLS_TOP_OFF:
            ret = Charger.CHG_STATE_TOP_OFF
        elif cd == MAX77960._CHG_DTLS_DONE:
            ret = Charger.CHG_STATE_DONE
        else:
            ret = Charger.CHG_STATE_OFF
        return ret
    
    #
    # Retrieves the DC supply status.
    # Returns one of the DC_STATE_xxx values to indicate the DC supply status.
    # Raises RuntimeError in case the information cannot be determined.
    def getDCStatus(self):
        data = self.getReg( MAX77960._REG_CHG_DETAILS_00 )
        ds = data & MAX77960._CHGIN_DTLS
        ret = Charger.DC_STATE_OFF
        if ds == MAX77960._CHGIN_DTLS_GOOD:
            ret = Charger.DC_STATE_VALID
        elif ds == MAX77960._CHGIN_DTLS_TOO_LOW:
            ret = Charger.DC_STATE_UNDERVOLTAGE
        elif ds == MAX77960._CHGIN_DTLS_TOO_HIGH:
            ret = Charger.DC_STATE_OVERVOLTAGE
        else:
            ret = Charger.CHG_STATE_OFF
        return ret
      
    #
    # Retrieves the current power source.
    # Returns one of the PWRSRC_xxx values to indicate the current power source.
    # Raises RuntimeError in case the information cannot be determined.
    #
    def getPowerSrc(self):
        ret = Charger.PWR_SRC_NONE
        dtls0 = self.getReg( MAX77960._REG_CHG_DETAILS_00 )
        chgin = dtls0 & MAX77960._CHGIN_DTLS
        qbat = dtls0 & MAX77960._QB_DTLS
        if chgin == MAX77960._CHGIN_DTLS_GOOD:
            # Valid CHGIN, so external power is the primary source
            ret = ret | Charger.PWR_SRC_DC
        if qbat:
            ret = ret | Charger.PWR_SRC_BAT
        return ret

    #
    # Retrieves the charger's temperature state.
    # Returns one of the TEMP_xxx values to indicate the temperature status.
    # Raises RuntimeError in case the information cannot be determined.
    #
    def getChargerTempStatus(self):
        ret = Charger.TEMP_OK
        dtls1 = self.getReg( MAX77960._REG_CHG_DETAILS_01 )
        chg = dtls1 & MAX77960._CHG_DTLS
        if chg == MAX77960._CHG_DTLS_OFF_TEMP:
            ret = Charger.TEMP_HOT
        else:
            treg = dtls1 & MAX77960._TREG
            if treg:
                ret = Charger.TEMP_WARM
            else:
                ret = Charger.TEMP_OK
        return ret

    #
    # Retrieves the battery's temperature state.
    # Returns one of the TEMP_xxx values to indicate the temperature status.
    # Raises RuntimeError in case the information cannot be determined.
    #
    def getBatteryTempStatus(self):
        ret = Charger.TEMP_COLD
        dtls2 = self.getReg( MAX77960._REG_CHG_DETAILS_02 )
        thm = dtls2 & MAX77960._THM_DTLS
        if thm == MAX77960._THM_DTLS_COLD:
            ret = Charger.TEMP_COLD
        elif thm == MAX77960._THM_DTLS_COOL:
            ret = Charger.TEMP_COOL
        elif thm == MAX77960._THM_DTLS_NORMAL:
            ret = Charger.TEMP_OK
        elif thm == MAX77960._THM_DTLS_WARM:
            ret = Charger.TEMP_WARM
        elif thm == MAX77960._THM_DTLS_HOT:
            ret = Charger.TEMP_HOT
        else:
            raise RuntimeError('Thermistor disabled or battery removed.')
        return ret

    #
    # Determines the error state, if one.
    # Returns one of the ERR_xxx values to indicate the error reason.
    # Raises RuntimeError in case the information cannot be determined.
    #
    def getError(self):
        ret = Charger.ERR_OK
        dtls1 = self.getReg( MAX77960._REG_CHG_DETAILS_01 )
        chg = dtls1 & MAX77960._CHG_DTLS
        if chg == MAX77960._CHG_DTLS_OFF_RESIST:
            ret = Charger.ERR_CONFIG
        elif chg == MAX77960._CHG_DTLS_E_TIMER:
            ret = Charger.ERR_TIMER
        elif chg == MAX77960._CHG_DTLS_SUSP_QBAT:
            ret = Charger.ERR_BAT_BROKEN
        elif chg == MAX77960._CHG_DTLS_OFF_CHGIN:
            dtls0 = self.getReg( MAX77960._REG_CHG_DETAILS_00 )
            chgin = dtls0 & MAX77960._CHG_DTLS
            if chgin == MAX77960._CHGIN_DTLS_TOO_HIGH:
                ret = Charger.ERR_DC_HIGH
            elif chgin == MAX77960._CHGIN_DTLS_TOO_LOW:
                ret = Charger.ERR_DC_LOW
            else:
                ret = Charger.ERR_DC
        elif chg == MAX77960._CHG_DTLS_OFF_TEMP:
            ret = Charger.ERR_TEMP_CHG
        elif chg == MAX77960._CHG_DTLS_OFF_WDOG:
            ret = Charger.ERR_CONFIG
        elif chg == MAX77960._CHG_DTLS_SUSP_JEITA:
            ret = Charger.ERR_TEMP_BAT
        elif chg == MAX77960._CHG_DTLS_SUSP_NOBAT:
            ret = Charger.ERR_BAT_REMOVED
        else:
            ret = Charger.ERR_OK
        return ret

    #
    # Tries to restart the charging phase, e.g. after recovering from a thermal shutdown
    # Raises RuntimeError in case the procedure is not available.
    #
    def restartCharging(self):
        # To recover from timer fault, switch charger off...
        self.setReg( MAX77960._REG_CHG_CNFG_00,
                     MAX77960._COMM_MODE_I2C | MAX77960._DISIBS_FET_PPSM | MAX77960._STBY_EN_DCDC_PPSM |
                     MAX77960._WDTEN_OFF | MAX77960._MODE_DCDC_ONLY )
        # ... and on again.
        self.setReg( MAX77960._REG_CHG_CNFG_00,
                     MAX77960._COMM_MODE_I2C | MAX77960._DISIBS_FET_PPSM | MAX77960._STBY_EN_DCDC_PPSM |
                     MAX77960._WDTEN_OFF | MAX77960._MODE_CHRG_DCDC )

    #
    # Event Publisher API (Interrupts)
    #
    
    # This class integer mask is a 16 bit word containing the TOP_INT in the high-byte
    # and the CHG_INT as low-byte.
    def _mapIntApi2Impl( self, apiMask ):
        chgMask = apiMask & MAX77960._CHG_INT_MASK_ALL
        topMask = (apiMask >> 8) & MAX77960._TOP_INT_MASK_ALL
        return [topMask, chgMask]
            
        
    def _mapIntImpl2Api( self, topMask, chgMask ):
        intMask = (topMask & MAX77960._TOP_INT_MASK_ALL) << 8
        intMask = intMask | (chgMask & MAX77960._CHG_INT_MASK_ALL)
        return intMask

    def getEventContext(self):
        topStatus = ~self.getReg( MAX77960._REG_TOP_INT_OK )
        chgStatus = ~self.getReg( MAX77960._REG_CHG_INT_OK )
        apiStatus = self._mapIntImpl2Api( topStatus, chgStatus )
        return apiStatus
    
    def getInt(self):
        topStatus = self.getReg( MAX77960._REG_TOP_INT )
        chgStatus = self.getReg( MAX77960._REG_CHG_INT )
        apiStatus = self._mapIntImpl2Api( topStatus, chgStatus )
        return apiStatus
    
    def registerInterruptHandler(self, apiMask, handler=None ):
        # Register handler
        if handler:
            if apiMask & Charger.INT_OTG_BUCK_BOOST:
                self.eventEmitter.on( Charger.INT_OTG_BUCK_BOOST, handler )
            if apiMask & Charger.INT_CHARGER_ONOFF:
                self.eventEmitter.on( Charger.INT_CHARGER_ONOFF, handler )
            if apiMask & Charger.INT_INPUT_CURRENT_LIMIT:
                self.eventEmitter.on( Charger.INT_INPUT_CURRENT_LIMIT, handler )
            if apiMask & Charger.INT_BATTERY_TEMPERATURE:
                self.eventEmitter.on( Charger.INT_BATTERY_TEMPERATURE, handler )
            if apiMask & Charger.INT_STATE_CHANGED:
                self.eventEmitter.on( Charger.INT_STATE_CHANGED, handler )
            if apiMask & Charger.INT_BATTERY_OVERCURRENT:
                self.eventEmitter.on( Charger.INT_BATTERY_OVERCURRENT, handler )
            if apiMask & Charger.INT_CHARGER_INPUT:
                self.eventEmitter.on( Charger.INT_CHARGER_INPUT, handler )
            if apiMask & Charger.INT_INCURR_LIM_BY_SRC:
                self.eventEmitter.on( Charger.INT_INCURR_LIM_BY_SRC, handler )
            if apiMask & Charger.INT_SYSTEM_UNDERVOLTAGE:
                self.eventEmitter.on( Charger.INT_SYSTEM_UNDERVOLTAGE, handler )
            if apiMask & Charger.INT_SYSTEM_OVERVOLTAGE:
                self.eventEmitter.on( Charger.INT_SYSTEM_OVERVOLTAGE, handler )
            if apiMask & Charger.INT_THERMAL_SHUTDOWN:
                self.eventEmitter.on( Charger.INT_THERMAL_SHUTDOWN, handler )
        # Clear current interrupts
        self.getInt()
        # Unmask specified interrupts
        [topMask, chgMask] = self._mapIntApi2Impl(apiMask)
        self.setReg( MAX77960._REG_TOP_INT_MASK, ~topMask )
        self.setReg( MAX77960._REG_CHG_INT_MASK, ~chgMask )
    
    #
    # The Watchdog API
    #
    
    def enable(self):
        self.enableReg( MAX77960._REG_CHG_CNFG_00, MAX77960._WDTEN )
    
    def disable(self):
        self.disableReg( MAX77960._REG_CHG_CNFG_00, MAX77960._WDTEN )
    
    def isRunning(self):
        data = self.getReg( MAX77960._REG_CHG_CNFG_00 )
        ret = (data & MAX77960._WDTEN) == MAX77960._WDTEN_ON
        return ret

    def clear(self):
        self.copyReg( MAX77960._REG_CHG_CNFG_06, MAX77960._WDTCLR, MAX77960._WDTCLR_DO_CLEAR )

    def isElapsed(self):
        dtls1 = self.getReg( MAX77960._REG_CHG_DETAILS_01 )
        ret = (dtls1 & MAX77960._CHG_DTLS) == MAX77960._CHG_DTLS_OFF_WDOG
        return ret

    def clearElapsed(self):
        self.clear()
    
    
    #
    # Specific public functions
    #
    
    def lockRegisters(self):
        self.setReg( MAX77960._REG_CHG_CNFG_06, MAX77960._CHGPROT_LOCK | MAX77960._WDTCLR_DO_NOT_TOUCH )

    def unlockRegisters(self):
        self.setReg( MAX77960._REG_CHG_CNFG_06, MAX77960._CHGPROT_UNLOCK | MAX77960._WDTCLR_DO_NOT_TOUCH )

    def dcStandby(self, enable=False ):
        if enable:
            self.enableReg( MAX77960._REG_CHG_CNFG_00, MAX77960._STBY_EN )
        else:
            self.disableReg( MAX77960._REG_CHG_CNFG_00, MAX77960._STBY_EN )
            
