from SerialDevice import SerialDevice
from BatteryCharger import BatteryCharger

class MAX77960( SerialDevice, BatteryCharger ):
    #
    # Protectd / private attributes
    #
    
    #
    # The only address is 0x69. No alternative.
    _ADRESSES_ALLOWED = [0x69]

    # Definition of registers and register content.
    # TOP
    _REG_CID          = 0x00
    _CID_REVISION     = 0xE0 # Silicon Revision
    _CID_VERSION      = 0x1F # OTP Recipe Version
    _CID_DEFAULT      = 0xA0

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
    _TOP_INT_MASK_ALL = 0xFF
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
    _QB_DTLS          = 0x01 # QBAT is on.
    
    _REG_CHG_DETAILS_01 = 0x14
    _TREG             = 0x80 # Junction temperature higher than REGTEMP; folding back charge current 
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
    #_FSW_DTLS_RSV_1   = 0x02 # Reserved.
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
    _CHG_CV_PRM_8000_12000 = 0x00 # 8000 mV (2 cells) / 12000 mV (3 cells) 
    _CHG_CV_PRM_8020_12030 = 0x01 # 8000 mV (2 cells) / 12030 mV (3 cells) 
    _CHG_CV_PRM_8040_12060 = 0x02 # 8000 mV (2 cells) / 12060 mV (3 cells) 
    _CHG_CV_PRM_8060_12090 = 0x03 # 8000 mV (2 cells) / 12090 mV (3 cells) 
    _CHG_CV_PRM_8080_12120 = 0x04 # 8000 mV (2 cells) / 12120 mV (3 cells) 
    _CHG_CV_PRM_8100_12150 = 0x05 # 8000 mV (2 cells) / 12150 mV (3 cells) 
    _CHG_CV_PRM_8120_12180 = 0x06 # 8000 mV (2 cells) / 12180 mV (3 cells) 
    _CHG_CV_PRM_8140_12210 = 0x07 # 8000 mV (2 cells) / 12210 mV (3 cells) 
    _CHG_CV_PRM_8160_12240 = 0x08 # 8000 mV (2 cells) / 12240 mV (3 cells) 
    _CHG_CV_PRM_8180_12270 = 0x09 # 8000 mV (2 cells) / 12270 mV (3 cells) 
    _CHG_CV_PRM_8200_12300 = 0x0A # 8000 mV (2 cells) / 12300 mV (3 cells) 
    _CHG_CV_PRM_8220_12330 = 0x0B # 8000 mV (2 cells) / 12330 mV (3 cells) 
    _CHG_CV_PRM_8240_12360 = 0x0C # 8000 mV (2 cells) / 12360 mV (3 cells) 
    _CHG_CV_PRM_8260_12390 = 0x0D # 8000 mV (2 cells) / 12390 mV (3 cells) 
    _CHG_CV_PRM_8280_12420 = 0x0E # 8000 mV (2 cells) / 12420 mV (3 cells) 
    _CHG_CV_PRM_8300_12450 = 0x0F # 8000 mV (2 cells) / 12450 mV (3 cells) 
    _CHG_CV_PRM_8320_12480 = 0x10 # 8000 mV (2 cells) / 12480 mV (3 cells) 
    _CHG_CV_PRM_8340_12510 = 0x11 # 8000 mV (2 cells) / 12510 mV (3 cells) 
    _CHG_CV_PRM_8360_12540 = 0x12 # 8000 mV (2 cells) / 12540 mV (3 cells) 
    _CHG_CV_PRM_8380_12570 = 0x13 # 8000 mV (2 cells) / 12570 mV (3 cells) 
    _CHG_CV_PRM_8400_12600 = 0x14 # 8000 mV (2 cells) / 12600 mV (3 cells) 
    _CHG_CV_PRM_8420_12630 = 0x15 # 8000 mV (2 cells) / 12630 mV (3 cells) 
    _CHG_CV_PRM_8440_12660 = 0x16 # 8000 mV (2 cells) / 12660 mV (3 cells) 
    _CHG_CV_PRM_8460_12690 = 0x17 # 8000 mV (2 cells) / 12690 mV (3 cells) 
    _CHG_CV_PRM_8480_12720 = 0x18 # 8000 mV (2 cells) / 12720 mV (3 cells) 
    _CHG_CV_PRM_8500_12750 = 0x19 # 8000 mV (2 cells) / 12750 mV (3 cells) 
    _CHG_CV_PRM_8520_12780 = 0x1A # 8000 mV (2 cells) / 12780 mV (3 cells) 
    _CHG_CV_PRM_8540_12810 = 0x1B # 8000 mV (2 cells) / 12810 mV (3 cells) 
    _CHG_CV_PRM_8560_12840 = 0x1C # 8000 mV (2 cells) / 12840 mV (3 cells) 
    _CHG_CV_PRM_8580_12870 = 0x1D # 8000 mV (2 cells) / 12870 mV (3 cells) 
    _CHG_CV_PRM_8600_12900 = 0x1E # 8000 mV (2 cells) / 12900 mV (3 cells) 
    _CHG_CV_PRM_8620_12930 = 0x1F # 8000 mV (2 cells) / 12930 mV (3 cells) 
    _CHG_CV_PRM_8640_12960 = 0x20 # 8000 mV (2 cells) / 12960 mV (3 cells) 
    _CHG_CV_PRM_8660_12990 = 0x21 # 8000 mV (2 cells) / 12990 mV (3 cells) 
    _CHG_CV_PRM_8680_13020 = 0x22 # 8000 mV (2 cells) / 13020 mV (3 cells) 
    _CHG_CV_PRM_8700_13050 = 0x23 # 8000 mV (2 cells) / 13050 mV (3 cells) 
    _CHG_CV_PRM_8720       = 0x24 # 8000 mV (2 cells)
    _CHG_CV_PRM_8740       = 0x25 # 8000 mV (2 cells)
    _CHG_CV_PRM_8760       = 0x26 # 8000 mV (2 cells)
    _CHG_CV_PRM_8780       = 0x27 # 8000 mV (2 cells)
    _CHG_CV_PRM_8800       = 0x28 # 8000 mV (2 cells)
    _CHG_CV_PRM_8820       = 0x29 # 8000 mV (2 cells)
    _CHG_CV_PRM_8840       = 0x2A # 8000 mV (2 cells)
    _CHG_CV_PRM_8860       = 0x2B # 8000 mV (2 cells)
    _CHG_CV_PRM_8880       = 0x2C # 8000 mV (2 cells)
    _CHG_CV_PRM_8900       = 0x2D # 8000 mV (2 cells)
    _CHG_CV_PRM_8920       = 0x2E # 8000 mV (2 cells)
    _CHG_CV_PRM_8940       = 0x2F # 8000 mV (2 cells)
    _CHG_CV_PRM_8960       = 0x30 # 8000 mV (2 cells)
    _CHG_CV_PRM_8980       = 0x31 # 8000 mV (2 cells)
    _CHG_CV_PRM_9000       = 0x32 # 8000 mV (2 cells)
    _CHG_CV_PRM_9020       = 0x33 # 8000 mV (2 cells)
    _CHG_CV_PRM_9040       = 0x34 # 8000 mV (2 cells)
    _CHG_CV_PRM_9060       = 0x35 # 8000 mV (2 cells)
    _CHG_CV_PRM_9080       = 0x36 # 8000 mV (2 cells)
    _CHG_CV_PRM_9100       = 0x37 # 8000 mV (2 cells)
    _CHG_CV_PRM_9120       = 0x38 # 8000 mV (2 cells)
    _CHG_CV_PRM_9140       = 0x39 # 8000 mV (2 cells)
    _CHG_CV_PRM_9160       = 0x3A # 8000 mV (2 cells)
    _CHG_CV_PRM_9180       = 0x3B # 8000 mV (2 cells)
    _CHG_CV_PRM_9200       = 0x3C # 8000 mV (2 cells)
    _CHG_CV_PRM_9220       = 0x3D # 8000 mV (2 cells)
    _CHG_CV_PRM_9240       = 0x3E # 8000 mV (2 cells)
    _CHG_CV_PRM_9260       = 0x3F # 8000 mV (2 cells)
    _CHG_CV_PRM_MIN        = _CHG_CV_PRM_8000_12000
    _CHG_CV_PRM_MAX        = _CHG_CV_PRM_9260
    _CHG_CV_PRM_DEFAULT    = _CHG_CV_PRM_8000_12000
    
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
    _REGTEMP            = 0x38 # Junction Temperature Thermal Regulation (deg. C).
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
    _MINVSYS_5535_8303  = 0x00 # 5535 mV (2 cells) / 8303 mV (3 cells)
    _MINVSYS_5740_8610  = 0x01 # 5740 mV (2 cells) / 8610 mV (3 cells)
    _MINVSYS_5945_8918  = 0x02 # 5945 mV (2 cells) / 8918 mV (3 cells)
    _MINVSYS_6150_9225  = 0x03 # 6150 mV (2 cells) / 9225 mV (3 cells)
    _MINVSYS_6355_9533  = 0x04 # 6355 mV (2 cells) / 9533 mV (3 cells)
    _MINVSYS_6560_9840  = 0x05 # 6560 mV (2 cells) / 9840 mV (3 cells)
    _MINVSYS_6765_10148 = 0x06 # 6765 mV (2 cells) / 10148 mV (3 cells)
    _MINVSYS_6970_10455 = 0x07 # 6970 mV (2 cells) / 10455 mV (3 cells)
    _MINVSYS_MIN        = _MINVSYS_5535_8303
    _MINVSYS_MAX        = _MINVSYS_6970_10455
    _MINVSYS_DEFAULT    = _MINVSYS_6150_9225
    
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
    
    EXPECTED_ID         = _CID_DEFAULT
    
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
    # Constructor
    # The only input parameter is a dictionary containing key-value pairs that
    # configure the instance. Regarded key names and their meanings are:
    # busType      : One of the SerialDevice.BUSTYPE_xxx values.
    # busDesignator: The bus designator. May be a name or number, such as "/dev/i2c-3" or 1.
    # deviceAddress: The I2C address (0x69).
    def __init__( self, paramDict ):
        # Set defaults, where necessary
        # Base class parameter: serial device
        if not ("busType" in paramDict):
            paramDict["busType"] = SerialDevice.BUSTYPE_I2C
        if not ("busDesignator" in paramDict):
            paramDict["busDesignator"] = "/dev/i2c-1"
        if not ("deviceAddress" in paramDict):
            paramDict["deviceAddress"] = MAX77960._ADRESSES_ALLOWED[0]
        # This class parameter

        # initialize local attributes
        
        # Call constructors of the super class
        SerialDevice.__init__(self, paramDict)

    #
    # Initializes the device. Is automatically called while instantiating
    # a new object. Can be used to re-initialize a sensor, e.g. after
    # resetting.
    # Raises OSError in case of problems with the connection.
    #
    def init(self):
        # Call serial driver's init  method to finalize communication setup
        SerialDevice.init(self)
        
        # Test address
        try:
            self.testConnection()
        except OSError:
            pass
        
    #
    # Just closes the device. Should be called at the end of a program.
    #
    def close(self):
        SerialDevice.close(self)

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
    # Reads the chip ID and verifies it against the
    # expected value.
    # Raises OSError, in case of problems with the connection.
    #        ValueError, if chip ID is not as expected
    #
    def checkID(self):
        chipID = self.getID()
        if ( chipID != MAX77960.EXPECTED_ID ):
            raise ValueError('Chip ID (' + str(chipID) + ') does not match the expected value (' + str(MAX77960.EXPECTED_ID) + ')!')

    #
    # Tests the communication with the sensor device.
    # Raises OSError, in case of problems with the connection.
    def testConnection(self):
        self.getID()

    #
    # BatteryCharger API
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
    # Retrieves the charge phase or status.
    # Returns one of the STATE_xxx values to indicate the current charge status.
    # Raises RuntimeError in case the charge status cannot be determined.
    #
    def getChgStatus(self):
        data = self.getReg( MAX77960._REG_CHG_DETAILS_01 )
        cd = data & MAX77960._CHG_DTLS
        ret = BatteryCharger.STATE_OFF
        if cd == MAX77960._CHG_DTLS_PRECHRG:
            bd = data & MAX77960._BAT_DTLS
            if bd == MAX77960._BAT_DTLS_BELOW_PREQ:
                ret = BatteryCharger.STATE_PRECHARGE
            else:
                ret = BatteryCharger.STATE_TRICKLE
        elif cd == MAX77960._CHG_DTLS_FAST_CURR:
            ret = BatteryCharger.STATE_FAST_CC
        elif cd == MAX77960._CHG_DTLS_FAST_VOLT:
            ret = BatteryCharger.STATE_FAST_CV
        elif cd == MAX77960._CHG_DTLS_TOP_OFF:
            ret = BatteryCharger.STATE_TOP_OFF
        elif cd == MAX77960._CHG_DTLS_DONE:
            ret = BatteryCharger.STATE_DONE
        else:
            ret = BatteryCharger.STATE_OFF
        return ret
    
  
    #
    # Retrieves the current power source.
    # Returns one of the PWRSRC_xxx values to indicate the current power source.
    # Raises RuntimeError in case the information cannot be determined.
    #
    def getPowerSrc(self):
        data = self.getReg( MAX77960._REG_CHG_DETAILS_00 )
        data = data & MAX77960._CHGIN_DTLS
        if data == MAX77960._CHGIN_DTLS_GOOD:
            ret = BatteryCharger.PWR_SRC_DC_BAT
        else:
            ret = BatteryCharger.PWR_SRC_BAT_ONLY

    #
    # Retrieves the charger's temperature state.
    # Returns one of the TEMP_xxx values to indicate the temperature status.
    # Raises RuntimeError in case the information cannot be determined.
    #
    def getChargerTempState(self):
        pass


    #
    # Retrieves the battery's temperature state.
    # Returns one of the TEMP_xxx values to indicate the temperature status.
    # Raises RuntimeError in case the information cannot be determined.
    #
    def getBatteryTempState(self):
        pass

    #
    # Determines the error state, if one.
    # Returns one of the ERR_xxx values to indicate the error reason.
    # Raises RuntimeError in case the information cannot be determined.
    #
    def getError(self):
        pass

    #
    # Tries to restart the charging phase, e.g. after recovering from a thermal shutdown
    # Raises RuntimeError in case the procedure is not available.
    def restartCharging(self):
        pass

    #
    # Re-configures the instance according to the parameters provided.
    # As with the constructor, the only parameter is the configuration dictionary.
    #
    def configure(self, paramDict):
        pass
    
    # Interrupts
    
    # This class integer mask is a 16 bit word containing the TOP_INT in the high-byte
    # and the CHG_INT as low-byte.
    def _mapIntApi2Impl( self, apiMask ):
        topMask = MAX77960._TOP_INT_MASK_NONE
        chgMask = MAX77960._CHG_INT_MASK_NONE
        
        if apiMask & BatteryCharger.INT_REASON_1:
            topMask |= MAX77960._CHG_INT_MASK_ALL
        
        return [topMask, chgMask]
            
        
    def _mapIntImpl2Api( self, topMask, chgMask ):
        intMask = (top << 8) | (chgMask & 0xFF)
        intMask = intMask & MAX77960.INT_ALL
        return intMask

    def getIntMask(self):
        topMask = self.getReg( MAX77960._REG_TOP_INT_MASK )
        chgMask = self.getReg( MAX77960._REG_CHG_INT_MASK )
        apiMask = self._mapIntImpl2Api( topMask, chgMask )
        return apiMask
    
    def setIntMask(self, intMask):
        [topMask, chgMask] = self._mapIntApi2Impl( intMask )
        self.setReg( MAX77960._REG_TOP_INT_MASK, topMask )
        self.setReg( MAX77960._REG_CHG_INT_MASK, chgMask )
        
    def enableInt( self, intMask ):
        [topMask, chgMask] = self._mapIntApi2Impl( intMask )
        self.enableReg( MAX77960._REG_TOP_INT_MASK, topMask )
        self.enableReg( MAX77960._REG_CHG_INT_MASK, chgMask )

    def disableInt( self, intMask ):
        [topMask, chgMask] = self._mapIntApi2Impl( intMask )
        self.disableReg( MAX77960._REG_TOP_INT_MASK, topMask )
        self.disableReg( MAX77960._REG_CHG_INT_MASK, chgMask )
    
    def getIntStatus(self):
        topStatus = ~self.getReg( MAX77960._REG_TOP_INT_OK )
        chgStatus = ~self.getReg( MAX77960._REG_CHG_INT_OK )
        apiStatus = self._mapIntImpl2Api( topStatus, chgStatus )
        return apiStatus
        pass
    
    #
    # Specific public functions
    #
    
    def lockRegisters(self):
        self.writeReg( MAX77960._REG_CHG_CNFG_06, MAX77960._CHGPROT_LOCK | MAX77960._WDTCLR_DO_NOT_TOUCH )

    def unlockRegisters(self):
        self.writeReg( MAX77960._REG_CHG_CNFG_06, MAX77960._CHGPROT_UNLOCK | MAX77960._WDTCLR_DO_NOT_TOUCH )

