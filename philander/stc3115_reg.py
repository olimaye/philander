"""Register definition for the STC3115 battery gas gauge.
    
Definition of registers and default values for the
above mentioined chip.
Externalized, just for clarity of the source code.
"""
__author__ = "Carl Bellgardt"
__version__ = "0.1"
__all__ = ["STC3115_Reg"]

from .systypes import Enum

class STC3115_Reg():

    #def __init__(chip_id):
        #self.chip_id = chip_id

    # Definition of registers and register content.
    _MODE = 0 # mode register (e.g. Coulomb counter, power saving voltage mode)    
    class _MODE_VALUES( Enum ):
        """This type describes diffrent operating modes.
        """
        VMODE = 0x01 # mixed mode
        CLR_VM_ADJ = 0x02 # clear ACC_VM_ADJ and REG_VM_ADJ
        CLR_CC_ADJ = 0x04 # clear ACC_CC_ADJ and REG_CC_ADJ
        ALM_ENA = 0x08 # enable alarm function
        GG_RUN = 0x10 # standy / operating mode
        FORCE_CC = 0x20 # forces the relaxation timer to switch to the couomb counter (CC) state
        FORCE_VM = 0x40 # forces the relatxation timer to switch to voltage mode (VM) state
        DEFAULT = VMODE or ALM_ENA
        OFF = 0
        
    
    _REG_CTRL = 1 # control and status register
    class _CTRL_VALUES( Enum ):
        """This type describes diffrent control commands.
        """
        IO02DATA = 0x01 # ALM pin status / ALM pin output drive
        GG_RST = 0x02 # resets the conversion counter GG_RST  is a self-clearing bit
        GG_VM = 0x04 # Coulomb counter mode / Voltage mode active
        BATFAIL = 0x08 # battery removal (BATD hight)
        PORDET = 0x10 # power on reset (POR) detection
        ALM_SOC = 0x20 # set with a low-SOC condition
        ALM_VOLT = 0x40 # set with a log-voltage condition
        DEFAULT = IO02DATA
    
    _REG_SOC_L = 2
    _REG_SOC_H = 3
    _REG_SOC = _REG_SOC_L # battery state of charge (SOC)
    
    _REG_COUNTER_L = 4
    _REG_COUNTER_H = 5
    _REG_COUNTER_ = _REG_COUNTER_L
    
    _REG_CURRENT_L = 6
    _REG_CURRENT_H = 7
    _REG_CURRENT = _REG_CURRENT_L # battery current, voltage drop over sense resistor
    
    _REG_VOLTAGE_L = 8
    _REG_VOLTAGE_H = 9
    _REG_VOLTAGE = _REG_VOLTAGE_L # battery voltage
    
    _REG_TEMPERATURE = 10 # temperature [C]
    _REG_CC_ADJ_H = 11 # coulomb counter adjustment factor
    _REG_VM_ADJ_H = 12 # voltage mode adjustment factor
    
    _REG_OCV_L = 13
    _REG_OCV_H = 14
    _REG_OCV = _REG_OCV_L # OCV register
    
    _REG_CC_CNF_L = 15
    _REG_CC_CNF_H = 16
    _REG_CC_CNF = _REG_CC_CNF_L # coulomb counter gas gauge configuration
    _CC_CNF_DEFAULT = 395
    
    _REG_VM_CNF_L = 17
    _REG_VM_CNF_H = 18
    _REG_VM_CNF = _REG_VM_CNF_L # voltage gas gause algorithm paramter
    _VM_CNF_DEFAULT = 321
    
    _REG_ALARM_SOC = 19 # SOC alarm level [0.5%]
    _ALARM_SOC_DEFAULT = 2 # 1% [0.5%]
    _REG_ALARM_VOLTAGE = 20 # battery low voltage alarm level [17.6mV]
    _ALARM_VOLTAGE_DEFAULT = 180 # 3.0V
    _REG_CURRENT_THRES = 21 # current threshold for current monitoring
    _CURRENT_THRES_DEFAULT = 10 # +/-470V drop
    _REG_CMONIT_COUNT = 22 # current monitoring counter
    _REG_RELAX_COUNT = _REG_CMONIT_COUNT
    _REG_CMONIT_MAX = 23 # maximum counter value for current monitoring
    _CMONIT_MAX_DEFAULT = 120 # CC-VM: 4 minutes; VM->CC: 1 minute
    _REG_RELAX_MAX = _REG_CMONIT_MAX
    _RELAX_MAX_DEFAULT = _CMONIT_MAX_DEFAULT
    _REG_ID = 24 # part type ID = 16h
    _CHIP_ID = 0x14 # expected chip ID
    _REG_CC_ADJ_L = 25 # coulomb counter adjustment factor
    _REG_VM_ADJ_L = 26 # voltage mode adjustment factor
    _REG_ACC_CC_ADJ_L = 27
    _REG_ACC_CC_ADJ_H = 28
    _REG_ACC_CC_ADJ = _REG_ACC_CC_ADJ_L # coulomb counter correction accumulator
    _REG_ACC_VM_ADJ_L = 29
    _REG_ACC_VM_ADJ_H = 30
    _REG_ACC_VM_ADJ = _REG_ACC_VM_ADJ_L # voltage mode correction accummulator
    
    # RAM registers: Working registers for gas gauge
    _REG_RAM0 = 32
    _REG_RAM1 = 33
    _REG_RAM2 = 34
    _REG_RAM3 = 35
    _REG_RAM4 = 36
    _REG_RAM5 = 37
    _REG_RAM6 = 38
    _REG_RAM7 = 39
    _REG_RAM8 = 40
    _REG_RAM9 = 41
    _REG_RAM10 = 42
    _REG_RAM11 = 43
    _REG_RAM12 = 44
    _REG_RAM13 = 45
    _REG_RAM14 = 46
    _REG_RAM15 = 47
    _REG_RAM_FIRST = _REG_RAM0
    _REG_RAM_LAST = _REG_RAM15
    _RAM_SIZE = _REG_RAM_LAST - _REG_RAM_FIRST + 1
    _IDX_RAM_TEST = 0
    _RAM_TEST = 0xB2 # arbitrary test pattern
    _IDX_RAM_SOC_L = 1
    _IDX_RAM_SOC_H = 2
    _IDX_RAM_SOC = _IDX_RAM_SOC_L
    _IDX_RAM_CC_CNF_L = 3
    _IDX_RAM_CC_CNF_H = 4
    _IDX_RAM_CC_CNF = _IDX_RAM_CC_CNF_L
    _IDX_RAM_VM_CNF_L = 5
    _IDX_RAM_VM_CNF_H = 6
    _IDX_RAM_VM_CNF = _IDX_RAM_VM_CNF_L
    _IDX_RAM_UNUSED_BEGIN = 7
    _IDX_RAM_UNUSED_END = 14
    _IDX_RAM_CRC = 15
    
    # Open Circuit Voltage (OCV) table registers
    # OCV adjustment table [0.55mV]
    _REG_OCV_TAB0 = 48
    _REG_OCV_TAB0 = 49
    _REG_OCV_TAB0 = 58
    _REG_OCV_TAB0 = 50
    _REG_OCV_TAB0 = 51
    _REG_OCV_TAB0 = 52
    _REG_OCV_TAB0 = 53
    _REG_OCV_TAB0 = 54
    _REG_OCV_TAB0 = 55
    _REG_OCV_TAB0 = 56
    _REG_OCV_TAB0 = 57
    _REG_OCV_TAB0 = 58
    _REG_OCV_TAB0 = 59
    _REG_OCV_TAB0 = 60
    _REG_OCV_TAB0 = 61
    _REG_OCV_TAB0 = 62
    _REG_OCV_TAB0 = 63
    _OCV_DEFAULT = 0
    
    # define configuration (defaults)
    
    _RSENSE_DEFAULT = 10 # sense resistor in milli OHm
    # if not defined(CONFIG_GASGAUGE_0_RSENSE) -> what is this?
    # ...
    
    # if defined CONFIG_GASGAUGE_0_BATTERY_IDX -> what is this?
    # ...
    
    # if defined ( CONFIG_GASGAUGE_0_ALARM_SOC ) -> what is this?
    # ...
    
    # other defines
    
    _DEVICE_ADDRESS_I2C = 0x70 # i2C device address is fix
    _POR_DELAY_LOOPS_MAX = 2000 # delay while doing a soft-reset
    
    
    
