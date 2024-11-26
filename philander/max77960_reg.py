"""Register definition for the MAX77960 USB battery charger.
    
Definition of registers, content masks and default values for the
above mentioined chip.
Externalized, just for clarity of the source code.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["MAX77960_Reg"]


class MAX77960_Reg:

    # Definition of registers and register content.
    # TOP
    REG_CID          = 0x00
    CID_REVISION     = 0xE0 # Silicon Revision
    CID_VERSION      = 0x1F # OTP Recipe Version
    CID_REV_5        = 0xA0 # silicon revision = 5
    CID_REV_6        = 0xC0 # silicon revision = 6
    CID_REV_MIN      = CID_REV_5 # Minimum known silicon revision that this driver is made for.
    CID_REV_MAX      = CID_REV_6 # Maximum known silicon revision that this driver is made for.
    CID_MAX7796x     = CID_REV_5 # MAX77960
    CID_MAX7796xB    = CID_REV_6 # MAX77960B
    
    REG_SWRST        = 0x01
    SWRST_TYPE_O     = 0xA5 # Reset Type O registers
    SWRST_NONE       = 0x00 # No reset
    SWRST_DEFAULT    = SWRST_NONE
    
    REG_TOP_INT      = 0x02
    TSHDN_I          = 0x04 # Thermal shutdown interrupt
    SYSOVLO_I        = 0x02 # SYSOVLO interrupt
    SYSUVLO_I        = 0x01 # SYSUVLO interrupt
    
    REG_TOP_INT_MASK = 0x03
    TSHDN_M          = 0x04 # Thermal shutdown interrupt masked
    SYSOVLO_M        = 0x02 # SYSOVLO interrupt masked
    SYSUVLO_M        = 0x01 # SYSUVLO interrupt masked
    TOP_INT_MASK_ALL = 0x07
    TOP_INT_MASK_NONE= 0x00
    TOP_INT_MASK_DEFAULT = 0xFF
    
    REG_TOP_INT_OK   = 0x04
    TSHDN_OK         = 0x04 # Device in thermal shutdown
    SYSOVLO_OK       = 0x02 # SYS voltage above (0) / below (1) SYSOVLO
    SYSUVLO_OK       = 0x01 # SYS coltage below (0) / above (1) SYSUVLO

    # CHARGER_FUNC
    REG_CHG_INT      = 0x10
    AICL_I           = 0x80 # AICL interrupt; AICL_OK changed since last read
    CHGIN_I          = 0x40 # CHGIN interrupt; CHGIN_OK changed
    B2SOVRC_I        = 0x20 # B2SOVRC interrupt; B2SOVRC changed
    CHG_I            = 0x10 # Charger interrupt; CHG_OK changed
    BAT_I            = 0x08 # Battery interrupt; BAT_OK changed
    CHGINLIM_I       = 0x04 # CHGINLIM interrupt; CHGINLIM_OK changed
    DISQBAT_I        = 0x02 # DISQBAT interrupt; DISQBAT_OK changed
    OTG_PLIM_I       = 0x01 # OTG/PLIM interrupt; OTG_OK (Mode=0xA) or PLIM_OK changed
    
    REG_CHG_INT_MASK = 0x11
    AICL_M           = 0x80 # AICL interrupt masked
    CHGIN_M          = 0x40 # CHGIN interrupt masked
    B2SOVRC_M        = 0x20 # B2SOVRC interrupt masked
    CHG_M            = 0x10 # Charger interrupt masked
    BAT_M            = 0x08 # Battery interrupt masked
    CHGINLIM_M       = 0x04 # CHGINLIM interrupt masked
    DISQBAT_M        = 0x02 # DISQBAT interrupt masked
    OTG_PLIM_M       = 0x01 # OTG/PLIM interrupt masked
    CHG_INT_MASK_ALL = 0xFF
    CHG_INT_MASK_NONE= 0x00
    CHG_INT_MASK_DEFAULT = 0xFF
    
    REG_CHG_INT_OK   = 0x12
    AICL_OK          = 0x80 # Not in AICL mode
    CHGIN_OK         = 0x40 # CHGIN input valid; CHGIN_DTLS=3
    B2SOVRC_OK       = 0x20 # BATT to SYS within current limit
    CHG_OK           = 0x10 # Charger OK or off
    BAT_OK           = 0x08 # Battery OK; BAT_DTLS=0x03 or 0x07
    CHGINLIM_OK      = 0x04 # CHGIN input within current limit
    DISQBAT_OK       = 0x02 # DISQBAT low and DISIBS is 0 while QBAT is not disabled
    OTG_PLIM_OK      = 0x01 # OTG operation OK (Mode=0x0A); Buck-boost within current limit.
    
    REG_CHG_DETAILS_00 = 0x13
    CHGIN_DTLS       = 0x60 # CHGIN Details as follows:
    CHGIN_DTLS_TOO_LOW = 0x00 # VBUS is invalid; V_CHGIN < V_CHGIN_UVLO
    CHGIN_DTLS_RSVD  = 0x20 # Reserved
    CHGIN_DTLS_TOO_HIGH= 0x40 # VBUS is invalid; V_CHGIN > V_CHGIN_OVLO
    CHGIN_DTLS_GOOD  = 0x60 # VBUS is valid; V_CHGIN_UVLO < V_CHGIN < V_CHGIN_OVLO
    OTG_DTLS         = 0x18 # OTG Details as follows:
    OTG_DTLS_UNDERVOLT = 0x00 # OTG output in undervoltage; V_CHGIN < V_OTG_UVLO
    OTG_DTLS_OTG_GOOD  = 0x08 # OTG output within limit OTG_ILIM
    OTG_DTLS_OVERVOLT= 0x10 # OTG output in overvoltage; V_CHGIN > V_OTG_OVLO
    OTG_DTLS_ILIM    = 0x18 # OTG disabled or output is valid but not in current limit.
    QB_DTLS          = 0x01 # QBAT details
    QB_DTLS_ON       = 0x01 # QBAT is on.
    QB_DTLS_OFF      = 0x00 # QBAT is off.
    
    REG_CHG_DETAILS_01 = 0x14
    TREG             = 0x80 # Temperature regulation status 
    TREG_HIGH        = 0x80 # Junction temperature higher than REGTEMP; folding back charge current 
    TREG_GOOD        = 0x00 # Junction temperature less than REGTEMP
    BAT_DTLS         = 0x70 # Battery details as follows:
    BAT_DTLS_REMOVAL = 0x00 # Battery removal detected on THM pin.
    BAT_DTLS_BELOW_PREQ= 0x10 # V_BATT < V_PRECHG; below prequal.
    BAT_DTLS_TIME_OUT= 0x20 # Charging takes longer than expected. Possibly due to high system currents, old/damaged battery. Charging suspended.
    BAT_DTLS_OK      = 0x30 # Battery OK and (VSYSMIN - 500mV) < VBATT, QBAT is on and VSYS is approximately equal to VBATT.
    BAT_DTLS_LOW_VOLT= 0x40 # Battery OK but its voltage is low: VPRECHG < VBATT < VSYSMIN - 500mV.
    BAT_DTLS_OVR_VOLT= 0x50 # Battery voltage has been greater than the battery overvoltage threshold (CHG_CV_PRM + 240mV/cell) for the last 30ms. Valid input.
    BAT_DTLS_OVR_CURR= 0x60 # Battery has been overcurrent for at least 3ms since the last time this register has been read.
    BAT_DTLS_NO_LEVEL= 0x70 # Battery level not available. In battery only mode, all battery comparators are off except for B2SOVRC.
    CHG_DTLS         = 0x0F # Charger details as follows:
    CHG_DTLS_PRECHRG = 0x00 # Charger is in precharge or trickle charge mode CHG_OK = 1 and VBATT < VSYSMIN - 500mV and TJ < TSHDN
    CHG_DTLS_FAST_CURR = 0x01 # Charger is in fast-charge constant current mode CHG_OK = 1 and VBATT < VBATTREG and TJ < TSHDN
    CHG_DTLS_FAST_VOLT = 0x02 # Charger is in fast-charge constant voltage mode CHG_OK = 1 and VBATT = VBATTREG and TJ < TSHDN
    CHG_DTLS_TOP_OFF = 0x03 # Charger is in top-off mode CHG_OK = 1 and VBATT = VBATTREG and TJ < TSHDN
    CHG_DTLS_DONE    = 0x04 # Charger is in done mode CHG_OK = 0 and VBATT > VBATTREG - VRSTRT and TJ < TSHDN
    CHG_DTLS_OFF_RESIST= 0x05 # Charger is off because at least one pin of INLIM, ITO, ISET, or VSET has invalid resistance. CHG_OK = 0
    CHG_DTLS_E_TIMER = 0x06 # Charger is in timer fault mode. CHG_OK = 0 and if BAT_DTLS = 0b001 then VBATT < VSYSMIN - 500mV or VBATT < VPRECHG and TJ < TSHDN
    CHG_DTLS_SUSP_QBAT = 0x07 # Charger is suspended because QBAT is disabled (DISQBAT = high or DISIBS = 1) CHG_OK = 0
    CHG_DTLS_OFF_CHGIN = 0x08 # Charger is off, charger input invalid and/or charger is disabled CHG_OK = 1
    #_CHG_DTLS_RSV_9   = 0x09 # Reserved.
    CHG_DTLS_OFF_TEMP= 0x0A # Charger is off and the junction temperature is > TSHDN CHG_OK = 0
    CHG_DTLS_OFF_WDOG= 0x0B # Charger is off because the watchdog timer expired CHG_OK = 0
    CHG_DTLS_SUSP_JEITA= 0x0C # Charger is suspended or charge current or voltage is reduced based on JEITA control. This condition is also reported in THM_DTLS. CHG_OK = 0
    CHG_DTLS_SUSP_NOBAT= 0x0D # Charger is suspended because battery removal is detected on THM pin. This condition is also reported in THM_DTLS. CHG_OK = 0
    #_CHG_DTLS_RSV_E   = 0x0E # Reserved.
    #_CHG_DTLS_RSV_F   = 0x0F # Reserved.

    REG_CHG_DETAILS_02 = 0x15
    THM_DTLS         = 0x70 # Thermistor status details as follows:
    THM_DTLS_COLD    = 0x00 # Low temperature and charging suspended
    THM_DTLS_COOL    = 0x10 # Low temperature charging
    THM_DTLS_NORMAL  = 0x20 # Normal temperature charging
    THM_DTLS_WARM    = 0x30 # High temperature charging
    THM_DTLS_HOT     = 0x40 # High temperature and charging suspended
    THM_DTLS_BAT_RMVD= 0x50 # Battery removal detected on THM pin
    THM_DTLS_DISABLED= 0x60 # Thermistor monitoring is disabled
    #_THM_DTLS_RSV_7   = 0x70 # Reserved.
    APP_MODE_DTLS    = 0x08 # Application mode status as follows:
    APP_MODE_DTLS_CONV = 0x00 # Operate as a standalone DC-DC converter
    APP_MODE_DTLS_CHRG = 0x08 # Operate as a charger.
    FSW_DTLS         = 0x06 # Programmed switching frequency details as follows:
    FSW_DTLS_600K    = 0x00 # 600 kHz
    FSW_DTLS_1200K   = 0x02 # 1.2 MHz; only from silicon rev. 6 on (MAX7796xB)
    #_FSW_DTLS_RSV_2   = 0x04 # Reserved.
    #_FSW_DTLS_RSV_3   = 0x06 # Reserved.
    NUM_CELL_DTLS    = 0x01 # Number of serially connected battery cells as follows:
    NUM_CELL_DTLS_2  = 0x00 # 2-cell battery
    NUM_CELL_DTLS_3  = 0x01 # 3-cell battery
    
    REG_CHG_CNFG_00    = 0x16
    COMM_MODE          = 0x80 # I2C enable
    COMM_MODE_AUTO     = 0x00 # Autonomous Mode defined by external resistors on INLIM, ISET, VSET and ITO pins. Writing 0 to COMM_MODE is ignored.
    COMM_MODE_I2C      = 0x80 # I2C enabled. CHGIN_ILIM, CHGCC, CHG_CV_PRM and TO_ITH registers are programmed by I2C. Writing 1 to COMM_MODE is allowed.
    COMM_MODE_DEFAULT  = COMM_MODE_AUTO
    DISIBS             = 0x40 # BATT to SYS FET Disable Control Read back value of DISIBS register bit reflects the actual DISIBS command or DISQBAT PIN state.
    DISIBS_FET_PPSM    = 0x00 # BATT to SYS FET is controlled by the power path state machine.
    DISIBS_FET_OFF     = 0x40 # BATT to SYS FET is forced off.
    DISIBS_DEFAULT     = DISIBS_FET_PPSM
    STBY_EN            = 0x20 # CHGIN Standby Enable Read back value of the STBY_EN register bit reflects the actual CHGIN standby setting.
    STBY_EN_DCDC_PPSM  = 0x00 # DC-DC is controlled by the power path state machine.
    STBY_EN_DCDC_OFF   = 0x20 # Force DC-DC off. Device goes to CHGIN low quiescent current standby.
    STBY_EN_DCDC_DEFAULT = STBY_EN_DCDC_PPSM
    WDTEN              = 0x10 # Watchdog Timer Enable.
    WDTEN_OFF          = 0x00 # Watchdog timer disabled
    WDTEN_ON           = 0x10 # Watchdog timer enabled
    WDTEN_DEFAULT      = WDTEN_OFF
    MODE               = 0x0F # Smart Power Selector Configuration as follows:
    MODE_ALL_OFF       = 0x00 # Charger = off, OTG = off, DC-DC = off. When the QBAT switch is on (DISQBAT = low and DISIBS = 0), the battery powers the system.
    MODE_ALL_OFF_1     = 0x01 # Same as 0x00
    MODE_ALL_OFF_2     = 0x02 # Same as 0x00
    MODE_ALL_OFF_3     = 0x03 # Same as 0x00
    MODE_DCDC_ONLY     = 0x04 # Charger = off, OTG = off, DC-DC = on. When there is a valid input, the DC-DC converter regulates the system voltage to be the maximum of (VSYSMIN and VBATT + 4%).
    MODE_CHRG_DCDC     = 0x05 # Charger = on,OTG = off, DC-DC = on. When there is a valid input, the battery is charging. VSYS is the larger of VSYSMIN and ~VBATT + IBATT x RBAT2SYS.
    MODE_CHRG_DCDC_6   = 0x06 # Same as 0x05
    MODE_CHRG_DCDC_7   = 0x07 # Same as 0x05
    #_MODE_RSV_8         = 0x08 # Reserved.
    #_MODE_RSV_9         = 0x09 # Reserved.
    MODE_OTG_ONLY      = 0x0A # Charger = off, OTG = on, DC-DC = off. QBAT is on to allow the battery to support the system, the charger's DC-DC operates in reverse mode as a buck converter.
    #_MODE_RSV_11        = 0x0B # Reserved.
    #_MODE_RSV_12        = 0x0C # Reserved.
    #_MODE_RSV_13        = 0x0D # Reserved.
    #_MODE_RSV_14        = 0x0E # Reserved.
    #_MODE_RSV_15        = 0x0F # Reserved.
    MODE_DEFAULT       = MODE_CHRG_DCDC

    REG_CHG_CNFG_01    = 0x17
    PQEN               = 0x80 # Low-Battery Prequalification Mode Enable
    PQEN_OFF           = 0x00 # Low-Battery Prequalification mode is disabled.
    PQEN_ON            = 0x80 # Low-Battery Prequalification mode is enabled.
    PQEN_DEFAULT       = PQEN_ON
    LPM                = 0x40 # Low Power Mode control
    LPM_NORMAL         = 0x00 # QBAT charge pump runs in Normal mode.
    LPM_ON             = 0x40 # QBAT charge pump is in Low Power Mode.
    LPM_DEFAULT        = LPM_NORMAL
    CHG_RSTRT          = 0x30 # Charger Restart Threshold
    CHG_RSTRT_100      = 0x00 # 100mV/cell below the value programmed by CHG_CV_PRM
    CHG_RSTRT_150      = 0x10 # 150mV/cell below the value programmed by CHG_CV_PRM
    CHG_RSTRT_200      = 0x20 # 200mV/cell below the value programmed by CHG_CV_PRM
    CHG_RSTRT_DISABLED = 0x30 # Disabled.
    CHG_RSTRT_MIN      = CHG_RSTRT_100
    CHG_RSTRT_MAX      = CHG_RSTRT_200
    CHG_RSTRT_DEFAULT  = CHG_RSTRT_150
    STAT_EN            = 0x08 # Charge Indicator Output Enable
    STAT_EN_OFF        = 0x00 # Disable STAT output
    STAT_EN_ON         = 0x08 # Enable STAT output
    STAT_EN_DEFAULT    = STAT_EN_ON
    FCHGTIME           = 0x07 # Fast-Charge Timer setting (tFC, hrs)
    FCHGTIME_DISABLED  = 0x00 # Disabled.
    FCHGTIME_3H        = 0x01 # 3 hours.
    FCHGTIME_4H        = 0x02 # 4 hours.
    FCHGTIME_5H        = 0x03 # 5 hours.
    FCHGTIME_6H        = 0x04 # 6 hours.
    FCHGTIME_7H        = 0x05 # 7 hours.
    FCHGTIME_8H        = 0x06 # 8 hours.
    FCHGTIME_10H       = 0x07 # 10 hours.
    FCHGTIME_MIN       = FCHGTIME_3H
    FCHGTIME_MAX       = FCHGTIME_10H
    FCHGTIME_DEFAULT   = FCHGTIME_3H
    
    REG_CHG_CNFG_02    = 0x18
    CHGCC              = 0x3F # Fast-Charge Current Selection (mA).
    CHGCC_100          = 0x00 # 100 mA
    CHGCC_150          = 0x01 # 150 mA
    CHGCC_200          = 0x02 # 200 mA
    CHGCC_250          = 0x03 # 250 mA
    CHGCC_300          = 0x04 # 300 mA
    CHGCC_350          = 0x05 # 350 mA
    CHGCC_400          = 0x06 # 400 mA
    CHGCC_450          = 0x07 # 450 mA
    CHGCC_500          = 0x08 # 500 mA
    CHGCC_600          = 0x09 # 600 mA
    CHGCC_700          = 0x0A # 700 mA
    CHGCC_800          = 0x0B # 800 mA
    CHGCC_900          = 0x0C # 900 mA
    CHGCC_1000         = 0x0D # 1000 mA
    CHGCC_1100         = 0x0E # 1100 mA
    CHGCC_1200         = 0x0F # 1200 mA
    CHGCC_1300         = 0x10 # 1300 mA
    CHGCC_1400         = 0x11 # 1400 mA
    CHGCC_1500         = 0x12 # 1500 mA
    CHGCC_1600         = 0x13 # 1600 mA
    CHGCC_1700         = 0x14 # 1700 mA
    CHGCC_1800         = 0x15 # 1800 mA
    CHGCC_1900         = 0x16 # 1900 mA
    CHGCC_2000         = 0x17 # 2000 mA
    CHGCC_2100         = 0x18 # 2100 mA
    CHGCC_2200         = 0x19 # 2200 mA
    CHGCC_2300         = 0x1A # 2300 mA
    CHGCC_2400         = 0x1B # 2400 mA
    CHGCC_2500         = 0x1C # 2500 mA
    CHGCC_2600         = 0x1D # 2600 mA
    CHGCC_2700         = 0x1E # 2700 mA
    CHGCC_2800         = 0x1F # 2800 mA
    CHGCC_2900         = 0x20 # 2900 mA
    CHGCC_3000         = 0x21 # 3000 mA
    CHGCC_3100         = 0x22 # 3100 mA
    CHGCC_3200         = 0x23 # 3200 mA
    CHGCC_3300         = 0x24 # 3300 mA
    CHGCC_3400         = 0x25 # 3400 mA
    CHGCC_3500         = 0x26 # 3500 mA
    CHGCC_3600         = 0x27 # 3600 mA
    CHGCC_3700         = 0x28 # 3700 mA
    CHGCC_3800         = 0x29 # 3800 mA
    CHGCC_3900         = 0x2A # 3900 mA
    CHGCC_4000         = 0x2B # 4000 mA
    CHGCC_4100         = 0x2C # 4100 mA
    CHGCC_4200         = 0x2D # 4200 mA
    CHGCC_4300         = 0x2E # 4300 mA
    CHGCC_4400         = 0x2F # 4400 mA
    CHGCC_4500         = 0x30 # 4500 mA
    CHGCC_4600         = 0x31 # 4600 mA
    CHGCC_4700         = 0x32 # 4700 mA
    CHGCC_4800         = 0x33 # 4800 mA
    CHGCC_4900         = 0x34 # 4900 mA
    CHGCC_5000         = 0x35 # 5000 mA
    CHGCC_5100         = 0x36 # 5100 mA
    CHGCC_5200         = 0x37 # 5200 mA
    CHGCC_5300         = 0x38 # 5300 mA
    CHGCC_5400         = 0x39 # 5400 mA
    CHGCC_5500         = 0x3A # 5500 mA
    CHGCC_5600         = 0x3B # 5600 mA
    CHGCC_5700         = 0x3C # 5700 mA
    CHGCC_5800         = 0x3D # 5800 mA
    CHGCC_5900         = 0x3E # 5900 mA
    CHGCC_6000         = 0x3F # 6000 mA
    CHGCC_MIN          = CHGCC_100
    CHGCC_MAX          = CHGCC_6000
    CHGCC_DEFAULT      = CHGCC_450
    
    REG_CHG_CNFG_03    = 0x19
    SYS_TRACK_DIS      = 0x80 # SYS Tracking Disable Control
    SYS_TRACK_ENABLED  = 0x00 # SYS tracking enabled. SYS regulated to MAX(VBATT + 4%, VSYSMIN), even in Charge Done state.
    SYS_TRACK_DISABLED = 0x80 # SYS tracking is disabled. SYS is regulated to VCHG_CV_PRM.
    SYS_TRACK_DEFAULT  = SYS_TRACK_DISABLED
    B2SOVRC_DTC        = 0x40 # Battery to SYS Overcurrent Debounce Time Control.
    B2SOVRC_DTC_6_MS   = 0x00 # tOCP = 6 ms
    B2SOVRC_DTC_100_MS = 0x40 # tOCP = 100 ms
    B2SOVRC_DTC_MIN    = B2SOVRC_DTC_6_MS
    B2SOVRC_DTC_MAX    = B2SOVRC_DTC_100_MS
    B2SOVRC_DTC_DEFAULT= B2SOVRC_DTC_6_MS
    TO_TIME            = 0x38 # Top-Off Timer Setting
    TO_TIME_30_SEC     = 0x00 # 30 seconds
    TO_TIME_10_MIN     = 0x08 # 10 minutes
    TO_TIME_20_MIN     = 0x10 # 20 minutes
    TO_TIME_30_MIN     = 0x18 # 30 minutes
    TO_TIME_40_MIN     = 0x20 # 40 minutes
    TO_TIME_50_MIN     = 0x28 # 50 minutes
    TO_TIME_60_MIN     = 0x30 # 60 minutes
    TO_TIME_70_MIN     = 0x38 # 70 minutes
    TO_TIME_MIN        = TO_TIME_30_SEC
    TO_TIME_MAX        = TO_TIME_70_MIN
    TO_TIME_DEFAULT    = TO_TIME_30_MIN
    TO_ITH             = 0x07 # Top-Off Current Threshold (mA).
    TO_ITH_100         = 0x00 # 100 mA
    TO_ITH_200         = 0x01 # 200 mA
    TO_ITH_300         = 0x02 # 300 mA
    TO_ITH_400         = 0x03 # 400 mA
    TO_ITH_500         = 0x04 # 500 mA
    TO_ITH_600         = 0x05 # 600 mA
    TO_ITH_600_6       = 0x06 # 600 mA
    TO_ITH_600_7       = 0x07 # 600 mA
    TO_ITH_MIN         = TO_ITH_100
    TO_ITH_MAX         = TO_ITH_600
    TO_ITH_DEFAULT     = TO_ITH_100
    
    REG_CHG_CNFG_04    = 0x1A
    CHG_CV_PRM         = 0x3F # Charge Termination Voltage Setting (mV).
    # 2 cells:
    CHG_CV_PRM_2C_8000 = 0x00 # 8000 mV
    CHG_CV_PRM_2C_8020 = 0x01 # 8020 mV
    CHG_CV_PRM_2C_8040 = 0x02 # 8040 mV
    CHG_CV_PRM_2C_8060 = 0x03 # 8060 mV
    CHG_CV_PRM_2C_8080 = 0x04 # 8080 mV
    CHG_CV_PRM_2C_8100 = 0x05 # 8100 mV
    CHG_CV_PRM_2C_8120 = 0x06 # 8120 mV
    CHG_CV_PRM_2C_8140 = 0x07 # 8140 mV 
    CHG_CV_PRM_2C_8160 = 0x08 # 8160 mV
    CHG_CV_PRM_2C_8180 = 0x09 # 8180 mV
    CHG_CV_PRM_2C_8200 = 0x0A # 8200 mV
    CHG_CV_PRM_2C_8220 = 0x0B # 8220 mV
    CHG_CV_PRM_2C_8240 = 0x0C # 8240 mV
    CHG_CV_PRM_2C_8260 = 0x0D # 8260 mV
    CHG_CV_PRM_2C_8280 = 0x0E # 8280 mV
    CHG_CV_PRM_2C_8300 = 0x0F # 8300 mV
    CHG_CV_PRM_2C_8320 = 0x10 # 8320 mV
    CHG_CV_PRM_2C_8340 = 0x11 # 8340 mV
    CHG_CV_PRM_2C_8360 = 0x12 # 8360 mV
    CHG_CV_PRM_2C_8380 = 0x13 # 8380 mV
    CHG_CV_PRM_2C_8400 = 0x14 # 8400 mV
    CHG_CV_PRM_2C_8420 = 0x15 # 8420 mV
    CHG_CV_PRM_2C_8440 = 0x16 # 8440 mV
    CHG_CV_PRM_2C_8460 = 0x17 # 8460 mV
    CHG_CV_PRM_2C_8480 = 0x18 # 8480 mV
    CHG_CV_PRM_2C_8500 = 0x19 # 8500 mV
    CHG_CV_PRM_2C_8520 = 0x1A # 8520 mV
    CHG_CV_PRM_2C_8540 = 0x1B # 8540 mV
    CHG_CV_PRM_2C_8560 = 0x1C # 8560 mV
    CHG_CV_PRM_2C_8580 = 0x1D # 8680 mV
    CHG_CV_PRM_2C_8600 = 0x1E # 8600 mV
    CHG_CV_PRM_2C_8620 = 0x1F # 8620 mV
    CHG_CV_PRM_2C_8640 = 0x20 # 8640 mV
    CHG_CV_PRM_2C_8660 = 0x21 # 8660 mV
    CHG_CV_PRM_2C_8680 = 0x22 # 8680 mV
    CHG_CV_PRM_2C_8700 = 0x23 # 8700 mV
    CHG_CV_PRM_2C_8720 = 0x24 # 8720 mV
    CHG_CV_PRM_2C_8740 = 0x25 # 8740 mV
    CHG_CV_PRM_2C_8760 = 0x26 # 8760 mV
    CHG_CV_PRM_2C_8780 = 0x27 # 8780 mV
    CHG_CV_PRM_2C_8800 = 0x28 # 8800 mV
    CHG_CV_PRM_2C_8820 = 0x29 # 8820 mV
    CHG_CV_PRM_2C_8840 = 0x2A # 8840 mV
    CHG_CV_PRM_2C_8860 = 0x2B # 8860 mV
    CHG_CV_PRM_2C_8880 = 0x2C # 8880 mV
    CHG_CV_PRM_2C_8900 = 0x2D # 8900 mV
    CHG_CV_PRM_2C_8920 = 0x2E # 8920 mV
    CHG_CV_PRM_2C_8940 = 0x2F # 8940 mV
    CHG_CV_PRM_2C_8960 = 0x30 # 8960 mV
    CHG_CV_PRM_2C_8980 = 0x31 # 8980 mV
    CHG_CV_PRM_2C_9000 = 0x32 # 9000 mV
    CHG_CV_PRM_2C_9020 = 0x33 # 9020 mV
    CHG_CV_PRM_2C_9040 = 0x34 # 9040 mV
    CHG_CV_PRM_2C_9060 = 0x35 # 9060 mV
    CHG_CV_PRM_2C_9080 = 0x36 # 9080 mV
    CHG_CV_PRM_2C_9100 = 0x37 # 9100 mV
    CHG_CV_PRM_2C_9120 = 0x38 # 9120 mV
    CHG_CV_PRM_2C_9140 = 0x39 # 9140 mV
    CHG_CV_PRM_2C_9160 = 0x3A # 9160 mV
    CHG_CV_PRM_2C_9180 = 0x3B # 9180 mV
    CHG_CV_PRM_2C_9200 = 0x3C # 9200 mV
    CHG_CV_PRM_2C_9220 = 0x3D # 9220 mV
    CHG_CV_PRM_2C_9240 = 0x3E # 9240 mV
    CHG_CV_PRM_2C_9260 = 0x3F # 9260 mV
    CHG_CV_PRM_2C_MIN  = CHG_CV_PRM_2C_8000
    CHG_CV_PRM_2C_MAX  = CHG_CV_PRM_2C_9260
    CHG_CV_PRM_2C_DEFAULT = CHG_CV_PRM_2C_8000
    # 3 cells:
    CHG_CV_PRM_3C_12000= 0x00 # 12000 mV
    CHG_CV_PRM_3C_12030= 0x01 # 12030 mV
    CHG_CV_PRM_3C_12060= 0x02 # 12060 mV
    CHG_CV_PRM_3C_12090= 0x03 # 12090 mV
    CHG_CV_PRM_3C_12120= 0x04 # 12120 mV
    CHG_CV_PRM_3C_12150= 0x05 # 12150 mV
    CHG_CV_PRM_3C_12180= 0x06 # 12180 mV
    CHG_CV_PRM_3C_12210= 0x07 # 12210 mV
    CHG_CV_PRM_3C_12240= 0x08 # 12240 mV
    CHG_CV_PRM_3C_12270= 0x09 # 12270 mV
    CHG_CV_PRM_3C_12300= 0x0A # 12300 mV
    CHG_CV_PRM_3C_12330= 0x0B # 12330 mV
    CHG_CV_PRM_3C_12360= 0x0C # 12360 mV
    CHG_CV_PRM_3C_12390= 0x0D # 12390 mV
    CHG_CV_PRM_3C_12420= 0x0E # 12420 mV
    CHG_CV_PRM_3C_12450= 0x0F # 12450 mV
    CHG_CV_PRM_3C_12480= 0x10 # 12480 mV
    CHG_CV_PRM_3C_12510= 0x11 # 12510 mV
    CHG_CV_PRM_3C_12540= 0x12 # 12540 mV
    CHG_CV_PRM_3C_12570= 0x13 # 12570 mV
    CHG_CV_PRM_3C_12600= 0x14 # 12600 mV
    CHG_CV_PRM_3C_12630= 0x15 # 12630 mV
    CHG_CV_PRM_3C_12660= 0x16 # 12660 mV
    CHG_CV_PRM_3C_12690= 0x17 # 12690 mV
    CHG_CV_PRM_3C_12720= 0x18 # 12720 mV
    CHG_CV_PRM_3C_12750= 0x19 # 12750 mV
    CHG_CV_PRM_3C_12780= 0x1A # 12780 mV
    CHG_CV_PRM_3C_12810= 0x1B # 12810 mV
    CHG_CV_PRM_3C_12840= 0x1C # 12840 mV
    CHG_CV_PRM_3C_12870= 0x1D # 12870 mV
    CHG_CV_PRM_3C_12900= 0x1E # 12900 mV
    CHG_CV_PRM_3C_12930= 0x1F # 12930 mV
    CHG_CV_PRM_3C_12960= 0x20 # 12960 mV
    CHG_CV_PRM_3C_12990= 0x21 # 12990 mV
    CHG_CV_PRM_3C_13020= 0x22 # 13020 mV
    CHG_CV_PRM_3C_13050= 0x23 # 13050 mV
    CHG_CV_PRM_3C_MIN  = CHG_CV_PRM_3C_12000
    CHG_CV_PRM_3C_MAX  = CHG_CV_PRM_3C_13050
    CHG_CV_PRM_3C_DEFAULT = CHG_CV_PRM_3C_12000
    CHG_CV_PRM_DEFAULT = CHG_CV_PRM_2C_DEFAULT
    
    REG_CHG_CNFG_05    = 0x1B
    ITRICKLE           = 0x30 # Trickle Charge Current Selection (mA)
    ITRICKLE_100       = 0x00 # 100 mA
    ITRICKLE_200       = 0x10 # 200 mA
    ITRICKLE_300       = 0x20 # 300 mA
    ITRICKLE_400       = 0x30 # 400 mA
    ITRICKLE_MIN       = ITRICKLE_100
    ITRICKLE_MAX       = ITRICKLE_400
    ITRICKLE_DEFAULT   = ITRICKLE_100
    B2SOVRC            = 0x0F # BATT to SYS Overcurrent Threshold (mA)
    B2SOVRC_DISABLED   = 0x00 # Disabled
    B2SOVRC_3000       = 0x01 # 3000 mA
    B2SOVRC_3500       = 0x02 # 3500 mA
    B2SOVRC_4000       = 0x03 # 4000 mA
    B2SOVRC_4500       = 0x04 # 4500 mA
    B2SOVRC_5000       = 0x05 # 5000 mA
    B2SOVRC_5500       = 0x06 # 5500 mA
    B2SOVRC_6000       = 0x07 # 6000 mA
    B2SOVRC_6500       = 0x08 # 6500 mA
    B2SOVRC_7000       = 0x09 # 7000 mA
    B2SOVRC_7500       = 0x0A # 7500 mA
    B2SOVRC_8000       = 0x0B # 8000 mA
    B2SOVRC_8500       = 0x0C # 8500 mA
    B2SOVRC_9000       = 0x0D # 9000 mA
    B2SOVRC_9500       = 0x0E # 9500 mA
    B2SOVRC_10000      = 0x0F # 10000 mA
    B2SOVRC_MIN        = B2SOVRC_3000
    B2SOVRC_MAX        = B2SOVRC_10000
    B2SOVRC_DEFAULT    = B2SOVRC_4500
    
    REG_CHG_CNFG_06    = 0x1C
    CHGPROT            = 0x0C # Charger Settings Protection Bits
    CHGPROT_LOCK       = 0x00 # Write capability locked.
    CHGPROT_LOCK_4     = 0x04 # Write capability locked.
    CHGPROT_LOCK_8     = 0x08 # Write capability locked.
    CHGPROT_UNLOCK     = 0x0C # Write capability unlocked.
    CHGPROT_DEFAULT    = CHGPROT_LOCK
    WDTCLR             = 0x03 # Watchdog Timer Clear Bits
    WDTCLR_DO_NOT_TOUCH= 0x00 # Watchdog is not cleared.
    WDTCLR_DO_CLEAR    = 0x01 # Watchdog is cleared.
    WDTCLR_DO_NOT_TOUCH_2= 0x02 # Watchdog is not cleared.
    WDTCLR_DO_NOT_TOUCH_3= 0x03 # Watchdog is not cleared.
    WDTCLR_DEFAULT     = WDTCLR_DO_NOT_TOUCH
    
    REG_CHG_CNFG_07    = 0x1D
    JEITA_EN           = 0x80 # JEITA Enable
    JEITA_EN_OFF       = 0x00 # JEITA disabled. Fast-charge current and charge termination voltage do not change based on thermistor temperature.
    JEITA_EN_ON        = 0x80 # JEITA enabled. Fast-charge current and charge termination voltage change based on thermistor temperature.
    JEITA_EN_DEFAULT   = JEITA_EN_OFF
    REGTEMP            = 0x78 # Junction Temperature Thermal Regulation (deg. C).
    REGTEMP_85         = 0x00 # 85 deg. Celsius
    REGTEMP_90         = 0x08 # 90 deg. Celsius
    REGTEMP_95         = 0x10 # 95 deg. Celsius
    REGTEMP_100        = 0x18 # 100 deg. Celsius
    REGTEMP_105        = 0x20 # 105 deg. Celsius
    REGTEMP_110        = 0x28 # 110 deg. Celsius
    REGTEMP_115        = 0x30 # 115 deg. Celsius
    REGTEMP_120        = 0x38 # 120 deg. Celsius
    REGTEMP_125        = 0x40 # 125 deg. Celsius
    REGTEMP_130        = 0x48 # 130 deg. Celsius
    REGTEMP_MIN        = REGTEMP_85
    REGTEMP_MAX        = REGTEMP_130
    REGTEMP_DEFAULT    = REGTEMP_115
    VCHGCV_COOL        = 0x04 # JEITA-Controlled Battery Termination Voltage When Thermistor Temperature is Between TCOLD and TCOOL
    VCHGCV_COOL_NORMAL = 0x00 # Battery termination voltage is set by CHG_CV_PRM.
    VCHGCV_COOL_REDUCED= 0x04 # Battery termination voltage is set by (CHG_CV_PRM - 180mV/cell).
    VCHGCV_COOL_DEFAULT= VCHGCV_COOL_NORMAL
    ICHGCC_COOL        = 0x02 # JEITA-Controlled Battery Fast-Charge Current When Thermistor Temperature is Between TCOLD and TCOOL
    ICHGCC_COOL_NORMAL = 0x00 # Battery fast-charge current is set by CHGCC
    ICHGCC_COOL_REDUCED= 0x02 # Battery fast-charge current is reduced to 50% of CHGCC
    ICHGCC_COOL_DEFAULT= ICHGCC_COOL_REDUCED
    FSHIP_MODE         = 0x01 # Factory Ship Mode Enable
    FSHIP_MODE_OFF     = 0x00 # Disable factory ship mode
    FSHIP_MODE_ON      = 0x01 # Enable factory ship mode
    FSHIP_MODE_DEFAULT = FSHIP_MODE_OFF
    
    REG_CHG_CNFG_08    = 0x1E
    CHGIN_ILIM         = 0x7F # CHGIN Input Current Limit (mA).
    CHGIN_ILIM_100     = 0x00 # 100 mA
    CHGIN_ILIM_100_1   = 0x01 # 100 mA
    CHGIN_ILIM_100_2   = 0x02 # 100 mA
    CHGIN_ILIM_100_3   = 0x03 # 100 mA
    CHGIN_ILIM_150     = 0x04 # 150 mA
    CHGIN_ILIM_200     = 0x05 # 200 mA
    CHGIN_ILIM_250     = 0x06 # 250 mA
    CHGIN_ILIM_300     = 0x07 # 300 mA
    CHGIN_ILIM_350     = 0x08 # 350 mA
    CHGIN_ILIM_400     = 0x09 # 400 mA
    CHGIN_ILIM_450     = 0x0A # 450 mA
    CHGIN_ILIM_500     = 0x0B # 500 mA
    CHGIN_ILIM_550     = 0x0C # 550 mA
    CHGIN_ILIM_600     = 0x0D # 600 mA
    CHGIN_ILIM_650     = 0x0E # 650 mA
    CHGIN_ILIM_700     = 0x0F # 700 mA
    CHGIN_ILIM_750     = 0x10 # 750 mA
    CHGIN_ILIM_800     = 0x11 # 800 mA
    CHGIN_ILIM_850     = 0x12 # 850 mA
    CHGIN_ILIM_900     = 0x13 # 900 mA
    CHGIN_ILIM_950     = 0x14 # 950 mA
    CHGIN_ILIM_1000    = 0x15 # 1000 mA
    CHGIN_ILIM_1050    = 0x16 # 1050 mA
    CHGIN_ILIM_1100    = 0x17 # 1100 mA
    CHGIN_ILIM_1150    = 0x18 # 1150 mA
    CHGIN_ILIM_1200    = 0x19 # 1200 mA
    CHGIN_ILIM_1250    = 0x1A # 1250 mA
    CHGIN_ILIM_1300    = 0x1B # 1300 mA
    CHGIN_ILIM_1350    = 0x1C # 1350 mA
    CHGIN_ILIM_1400    = 0x1D # 1400 mA
    CHGIN_ILIM_1450    = 0x1E # 1450 mA
    CHGIN_ILIM_1500    = 0x1F # 1500 mA
    CHGIN_ILIM_1550    = 0x20 # 1550 mA
    CHGIN_ILIM_1600    = 0x21 # 1600 mA
    CHGIN_ILIM_1650    = 0x22 # 1650 mA
    CHGIN_ILIM_1700    = 0x23 # 1700 mA
    CHGIN_ILIM_1750    = 0x24 # 1750 mA
    CHGIN_ILIM_1800    = 0x25 # 1800 mA
    CHGIN_ILIM_1850    = 0x26 # 1850 mA
    CHGIN_ILIM_1900    = 0x27 # 1900 mA
    CHGIN_ILIM_1950    = 0x28 # 1950 mA
    CHGIN_ILIM_2000    = 0x29 # 2000 mA
    CHGIN_ILIM_2050    = 0x2A # 2050 mA
    CHGIN_ILIM_2100    = 0x2B # 2100 mA
    CHGIN_ILIM_2150    = 0x2C # 2150 mA
    CHGIN_ILIM_2200    = 0x2D # 2200 mA
    CHGIN_ILIM_2250    = 0x2E # 2250 mA
    CHGIN_ILIM_2300    = 0x2F # 2300 mA
    CHGIN_ILIM_2350    = 0x30 # 2350 mA
    CHGIN_ILIM_2400    = 0x31 # 2400 mA
    CHGIN_ILIM_2450    = 0x32 # 2450 mA
    CHGIN_ILIM_2500    = 0x33 # 2500 mA
    CHGIN_ILIM_2550    = 0x34 # 2550 mA
    CHGIN_ILIM_2600    = 0x35 # 2600 mA
    CHGIN_ILIM_2650    = 0x36 # 2650 mA
    CHGIN_ILIM_2700    = 0x37 # 2700 mA
    CHGIN_ILIM_2750    = 0x38 # 2750 mA
    CHGIN_ILIM_2800    = 0x39 # 2800 mA
    CHGIN_ILIM_2850    = 0x3A # 2850 mA
    CHGIN_ILIM_2900    = 0x3B # 2900 mA
    CHGIN_ILIM_2950    = 0x3C # 2950 mA
    CHGIN_ILIM_3000    = 0x3D # 3000 mA
    CHGIN_ILIM_3050    = 0x3E # 3050 mA
    CHGIN_ILIM_3100    = 0x3F # 3100 mA
    CHGIN_ILIM_3150    = 0x40 # 3150 mA
    CHGIN_ILIM_3200    = 0x41 # 3200 mA
    CHGIN_ILIM_3250    = 0x42 # 3250 mA
    CHGIN_ILIM_3300    = 0x43 # 3300 mA
    CHGIN_ILIM_3350    = 0x44 # 3350 mA
    CHGIN_ILIM_3400    = 0x45 # 3400 mA
    CHGIN_ILIM_3450    = 0x46 # 3450 mA
    CHGIN_ILIM_3500    = 0x47 # 3500 mA
    CHGIN_ILIM_3550    = 0x48 # 3550 mA
    CHGIN_ILIM_3600    = 0x49 # 3600 mA
    CHGIN_ILIM_3650    = 0x4A # 3650 mA
    CHGIN_ILIM_3700    = 0x4B # 3700 mA
    CHGIN_ILIM_3750    = 0x4C # 3750 mA
    CHGIN_ILIM_3800    = 0x4D # 3800 mA
    CHGIN_ILIM_3850    = 0x4E # 3850 mA
    CHGIN_ILIM_3900    = 0x4F # 3900 mA
    CHGIN_ILIM_3950    = 0x50 # 3950 mA
    CHGIN_ILIM_4000    = 0x51 # 4000 mA
    CHGIN_ILIM_4050    = 0x52 # 4050 mA
    CHGIN_ILIM_4100    = 0x53 # 4100 mA
    CHGIN_ILIM_4150    = 0x54 # 4150 mA
    CHGIN_ILIM_4200    = 0x55 # 4200 mA
    CHGIN_ILIM_4250    = 0x56 # 4250 mA
    CHGIN_ILIM_4300    = 0x57 # 4300 mA
    CHGIN_ILIM_4350    = 0x58 # 4350 mA
    CHGIN_ILIM_4400    = 0x59 # 4400 mA
    CHGIN_ILIM_4450    = 0x5A # 4450 mA
    CHGIN_ILIM_4500    = 0x5B # 4500 mA
    CHGIN_ILIM_4550    = 0x5C # 4550 mA
    CHGIN_ILIM_4600    = 0x5D # 4600 mA
    CHGIN_ILIM_4650    = 0x5E # 4650 mA
    CHGIN_ILIM_4700    = 0x5F # 4700 mA
    CHGIN_ILIM_4750    = 0x60 # 4750 mA
    CHGIN_ILIM_4800    = 0x61 # 4800 mA
    CHGIN_ILIM_4850    = 0x62 # 4850 mA
    CHGIN_ILIM_4900    = 0x63 # 4900 mA
    CHGIN_ILIM_4950    = 0x64 # 4950 mA
    CHGIN_ILIM_5000    = 0x65 # 5000 mA
    CHGIN_ILIM_5050    = 0x66 # 5050 mA
    CHGIN_ILIM_5100    = 0x67 # 5100 mA
    CHGIN_ILIM_5150    = 0x68 # 5150 mA
    CHGIN_ILIM_5200    = 0x69 # 5200 mA
    CHGIN_ILIM_5250    = 0x6A # 5250 mA
    CHGIN_ILIM_5300    = 0x6B # 5300 mA
    CHGIN_ILIM_5350    = 0x6C # 5350 mA
    CHGIN_ILIM_5400    = 0x6D # 5400 mA
    CHGIN_ILIM_5450    = 0x6E # 5450 mA
    CHGIN_ILIM_5500    = 0x6F # 5500 mA
    CHGIN_ILIM_5550    = 0x70 # 5550 mA
    CHGIN_ILIM_5600    = 0x71 # 5600 mA
    CHGIN_ILIM_5650    = 0x72 # 5650 mA
    CHGIN_ILIM_5700    = 0x73 # 5700 mA
    CHGIN_ILIM_5750    = 0x74 # 5750 mA
    CHGIN_ILIM_5800    = 0x75 # 5800 mA
    CHGIN_ILIM_5850    = 0x76 # 5850 mA
    CHGIN_ILIM_5900    = 0x77 # 5900 mA
    CHGIN_ILIM_5950    = 0x78 # 5950 mA
    CHGIN_ILIM_6000    = 0x79 # 6000 mA
    CHGIN_ILIM_6050    = 0x7A # 6050 mA
    CHGIN_ILIM_6100    = 0x7B # 6100 mA
    CHGIN_ILIM_6150    = 0x7C # 6150 mA
    CHGIN_ILIM_6200    = 0x7D # 6200 mA
    CHGIN_ILIM_6250    = 0x7E # 6250 mA
    CHGIN_ILIM_6300    = 0x7F # 6300 mA
    CHGIN_ILIM_MIN     = CHGIN_ILIM_100
    CHGIN_ILIM_MAX     = CHGIN_ILIM_6300
    CHGIN_ILIM_DEFAULT = CHGIN_ILIM_500
    CHGIN_ILIM_DEFAULT_VALUE = 500
    
    REG_CHG_CNFG_09    = 0x1F
    INLIM_CLK          = 0xC0 # Input Current Limit Soft-Start Period (micro seconds) Between Consecutive Increments of 25mA
    INLIM_CLK_8        = 0x00 # 8 us
    INLIM_CLK_256      = 0x40 # 256 us
    INLIM_CLK_1024     = 0x80 # 1024 us ~ 1 ms
    INLIM_CLK_4096     = 0xC0 # 4096 us ~ 4 ms
    INLIM_CLK_MIN      = INLIM_CLK_8
    INLIM_CLK_MAX      = INLIM_CLK_4096
    INLIM_CLK_DEFAULT  = INLIM_CLK_1024
    OTG_ILIM           = 0x38 # OTG Mode Current Limit Setting (mA)
    OTG_ILIM_500       = 0x00 # 500 mA
    OTG_ILIM_900       = 0x08 # 900 mA
    OTG_ILIM_1200      = 0x10 # 1200 mA
    OTG_ILIM_1500      = 0x18 # 1500 mA
    OTG_ILIM_2000      = 0x20 # 2000 mA
    OTG_ILIM_2250      = 0x28 # 2250 mA
    OTG_ILIM_2500      = 0x30 # 2500 mA
    OTG_ILIM_3000      = 0x38 # 3000 mA
    OTG_ILIM_MIN       = OTG_ILIM_500
    OTG_ILIM_MAX       = OTG_ILIM_3000
    OTG_ILIM_DEFAULT   = OTG_ILIM_1500
    MINVSYS            = 0x07 # Minimum System Regulation Voltage (mV)
    # 2 cells:
    MINVSYS_2C_5535    = 0x00 # 5535 mV
    MINVSYS_2C_5740    = 0x01 # 5740 mV
    MINVSYS_2C_5945    = 0x02 # 5945 mV
    MINVSYS_2C_6150    = 0x03 # 6150 mV
    MINVSYS_2C_6355    = 0x04 # 6355 mV
    MINVSYS_2C_6560    = 0x05 # 6560 mV
    MINVSYS_2C_6765    = 0x06 # 6765 mV
    MINVSYS_2C_6970    = 0x07 # 6970 mV
    MINVSYS_2C_MIN     = MINVSYS_2C_5535
    MINVSYS_2C_MAX     = MINVSYS_2C_6970
    MINVSYS_2C_DEFAULT = MINVSYS_2C_6150
    # 3 cells:
    MINVSYS_3C_8303    = 0x00 # 8303 mV
    MINVSYS_3C_8610    = 0x01 # 8610 mV
    MINVSYS_3C_8918    = 0x02 # 8918 mV
    MINVSYS_3C_9225    = 0x03 # 9225 mV
    MINVSYS_3C_9533    = 0x04 # 9533 mV
    MINVSYS_3C_9840    = 0x05 # 9840 mV
    MINVSYS_3C_10148   = 0x06 # 10148 mV
    MINVSYS_3C_10455   = 0x07 # 10455 mV
    MINVSYS_3C_MIN     = MINVSYS_3C_8303
    MINVSYS_3C_MAX     = MINVSYS_3C_10455
    MINVSYS_3C_DEFAULT = MINVSYS_3C_9225
    MINVSYS_DEFAULT    = MINVSYS_2C_DEFAULT
    
    REG_CHG_CNFG_10    = 0x20
    VCHGIN_REG         = 0x3E # CHGIN Voltage Regulation Threshold (mV)
    VCHGIN_REG_4025    = 0x00 # 4025 mV
    VCHGIN_REG_4200    = 0x02 # 4200 mV
    VCHGIN_REG_4375    = 0x04 # 4375 mV
    VCHGIN_REG_4550    = 0x06 # 4550 mV
    VCHGIN_REG_4725    = 0x08 # 4725 mV
    VCHGIN_REG_4900    = 0x0A # 4900 mV
    VCHGIN_REG_5425    = 0x0C # 5425 mV
    VCHGIN_REG_5950    = 0x0E # 5950 mV
    VCHGIN_REG_6475    = 0x10 # 6475 mV
    VCHGIN_REG_7000    = 0x12 # 7000 mV
    VCHGIN_REG_7525    = 0x14 # 7525 mV
    VCHGIN_REG_8050    = 0x16 # 8050 mV
    VCHGIN_REG_8575    = 0x18 # 8575 mV
    VCHGIN_REG_9100    = 0x1A # 9100 mV
    VCHGIN_REG_9625    = 0x1C # 9625 mV
    VCHGIN_REG_10150   = 0x1E # 10150 mV
    VCHGIN_REG_10675   = 0x20 # 10675 mV
    VCHGIN_REG_10950    = 0x22 # 10950 mV
    VCHGIN_REG_11550    = 0x24 # 11550 mV
    VCHGIN_REG_12150    = 0x26 # 12150 mV
    VCHGIN_REG_12750    = 0x28 # 12750 mV
    VCHGIN_REG_13350    = 0x2A # 13350 mV
    VCHGIN_REG_13950    = 0x2C # 13950 mV
    VCHGIN_REG_14550    = 0x2E # 14550 mV
    VCHGIN_REG_15150    = 0x30 # 15150 mV
    VCHGIN_REG_15750    = 0x32 # 15750 mV
    VCHGIN_REG_16350    = 0x34 # 16350 mV
    VCHGIN_REG_16950    = 0x36 # 16950 mV
    VCHGIN_REG_17550    = 0x38 # 17550 mV
    VCHGIN_REG_18150    = 0x3A # 18150 mV
    VCHGIN_REG_18750    = 0x3C # 18750 mV
    VCHGIN_REG_19050    = 0x3E # 19050 mV
    VCHGIN_REG_MIN      = VCHGIN_REG_4025
    VCHGIN_REG_MAX      = VCHGIN_REG_19050
    VCHGIN_REG_DEFAULT  = VCHGIN_REG_4725
    DISKIP              = 0x01 # Charger Skip Mode Disable
    DISKIP_AUTO         = 0x00 # Autoskip mode
    DISKIP_DISABLED     = 0x01 # Disable skip mode
    DISKIP_DEFAULT      = DISKIP_AUTO

    #
    # Register / Content descriptions
    #
    
    registerMap = [
        [REG_CID, 'CID', ([CID_REVISION, 'REV'], [CID_VERSION, 'VER'], [0xFF, 'ID'])],
        [REG_SWRST, 'SWRST', ()],
        [REG_TOP_INT, 'TOP_INT', ([TSHDN_I, 'TSHDN_I'], [SYSOVLO_I, 'SYSOVLO_I'], [SYSUVLO_I, 'SYSUVLO_I'])],
        [REG_TOP_INT_MASK, 'TOP_INT_MASK', ([TSHDN_M, 'TSHDN_M'], [SYSOVLO_M, 'SYSOVLO_M'], [SYSUVLO_M, 'SYSUVLO_M'])],
        [REG_TOP_INT_OK, 'TOP_INT_OK', ([TSHDN_OK, 'TSHDN_OK'], [SYSOVLO_OK, 'SYSOVLO_OK'], [SYSUVLO_OK, 'SYSUVLO_OK'])],
        [REG_CHG_INT, 'CHG_INT', ([AICL_I, 'AICL_I'], [CHGIN_I, 'CHGIN_I'], [B2SOVRC_I, 'B2SOVRC_I'], [CHG_I, '_CHG_I'],
                                  [BAT_I, 'BAT_I'], [CHGINLIM_I, 'CHGINLIM_I'], [DISQBAT_I, 'DISQBAT_I'], [OTG_PLIM_I, 'OTG_PLIM_I'])],
        [REG_CHG_INT_MASK, 'CHG_INT_MASK', ([AICL_M, 'AICL_M'], [CHGIN_M, 'CHGIN_M'], [B2SOVRC_M, 'B2SOVRC_M'],
                                            [CHG_M, 'CHG_M'], [BAT_M, 'BAT_M'], [CHGINLIM_M, 'CHGINLIM_M'], [DISQBAT_M, 'DISQBAT_M'], [OTG_PLIM_M, 'OTG_PLIM_M'])],
        [REG_CHG_INT_OK, 'CHG_INT_OK', ([AICL_OK, 'AICL_OK'], [CHGIN_OK, 'CHGIN_OK'], [B2SOVRC_OK, 'B2SOVRC_OK'],
                                        [CHG_OK, 'CHG_OK'], [BAT_OK, 'BAT_OK'], [CHGINLIM_OK, 'CHGINLIM_OK'], [DISQBAT_OK, 'DISQBAT_OK'],
                                        [OTG_PLIM_OK, 'OTG_PLIM_OK'])],
        [REG_CHG_DETAILS_00, 'CHG_DETAILS_00', ([CHGIN_DTLS, 'CHGIN_DTLS'], [OTG_DTLS, 'OTG_DTLS'], [QB_DTLS, 'QB_DTLS'])],
        [REG_CHG_DETAILS_01, 'CHG_DETAILS_01', ([TREG, 'TREG'], [BAT_DTLS, 'BAT_DTLS'], [CHG_DTLS, 'CHG_DTLS'])],
        [REG_CHG_DETAILS_02, 'CHG_DETAILS_02', ([THM_DTLS, 'THM_DTLS'], [APP_MODE_DTLS, 'APP_MODE_DTLS'],
                                                 [FSW_DTLS, 'FSW_DTLS'], [NUM_CELL_DTLS, 'NUM_CELL_DTLS'])],
        [REG_CHG_CNFG_00, 'CHG_CNFG_00', ([COMM_MODE, 'COMM_MODE'], [DISIBS, 'DISIBS'], [STBY_EN, 'STBY_EN'],
                                           [WDTEN, 'WDTEN'], [MODE, 'MODE'])],
        [REG_CHG_CNFG_01, 'CHG_CNFG_01', ([PQEN, 'PQEN'], [LPM, 'LPM'], [CHG_RSTRT, 'CHG_RSTRT'], 
                                           [STAT_EN, 'STAT_EN'], [FCHGTIME, 'FCHGTIME'])],
        [REG_CHG_CNFG_02, 'CHG_CNFG_02', ([CHGCC, 'CHGCC'],)],
        [REG_CHG_CNFG_03, 'CHG_CNFG_03', ([SYS_TRACK_DIS, 'SYS_TRACK_DIS'], [B2SOVRC_DTC, 'B2SOVRC_DTC'],
                                           [TO_TIME, 'TO_TIME'], [TO_ITH, 'TO_ITH'])],
        [REG_CHG_CNFG_04, 'CHG_CNFG_04', ([CHG_CV_PRM, 'CHG_CV_PRM'],)],
        [REG_CHG_CNFG_05, 'CHG_CNFG_05', ([ITRICKLE, 'ITRICKLE'], [B2SOVRC, 'B2SOVRC'])],
        [REG_CHG_CNFG_06, 'CHG_CNFG_06', ([CHGPROT, 'CHGPROT'], [WDTCLR, 'WDTCLR'])],
        [REG_CHG_CNFG_07, 'CHG_CNFG_07', ([JEITA_EN, 'JEITA_EN'], [REGTEMP, 'REGTEMP'], [VCHGCV_COOL, 'VCHGCV_COOL'],
                                           [ICHGCC_COOL, 'ICHGCC_COOL'], [FSHIP_MODE, 'FSHIP_MODE'])],
        [REG_CHG_CNFG_08, 'CHG_CNFG_08', ([CHGIN_ILIM, 'CHGIN_ILIM'],)],
        [REG_CHG_CNFG_09, 'CHG_CNFG_09', ([INLIM_CLK, 'INLIM_CLK'], [OTG_ILIM, 'OTG_ILIM'], [MINVSYS, 'MINVSYS'])],
        [REG_CHG_CNFG_10, 'CHG_CNFG_10', ([VCHGIN_REG, 'VCHGIN_REG'], [DISKIP, 'DISKIP'])],
    ]
    

