"""Register definitions for the STC311x family battery gas gauges.
    
Definition of registers and default values for the
above-mentioned chips.
Externalized, just for clarity of the source code.
"""
__author__ = "Carl Bellgardt"
__version__ = "0.1"
__all__ = ["STC311x_Reg", ]


class STC311x_Reg:
    """Definition of common registers and values.
    
    Base class to define register addresses and content values
    common to all members of the chip family.
    """

    REG_MODE = 0  # Mode register
    # possible values of the mode register
    MODE_VMODE = 0x01  # 0: Mixed mode (Coulomb counter active); 1: Power saving voltage mode
    MODE_ALM_ENA = 0x08  # Alarm function enable
    MODE_GG_RUN = 0x10  # Standby / operating mode
    MODE_FORCE_CC = 0x20  # Forces the relaxation timer to switch to the Coulomb counter (CC) state.
    MODE_FORCE_VM = 0x40  # Forces the relaxation timer to switch to voltage mode (VM) state.
    MODE_OFF = 0
    MODE_DEFAULT = (MODE_VMODE | MODE_ALM_ENA)

    REG_CTRL = 1  # Control and status register
    # possible values of the control register
    CTRL_IO0DATA = 0x01  # ALM pin status / ALM pin output drive
    CTRL_GG_RST = 0x02  # resets the conversion counter GG_RST is a self-clearing bit
    CTRL_GG_VM = 0x04  # Coulomb counter mode / Voltage mode active
    CTRL_BATFAIL = 0x08  # Battery removal (BATD high).
    CTRL_PORDET = 0x10  # Power on reset (POR) detection / Soft reset
    CTRL_ALM_SOC = 0x20  # Set with a low-SOC condition
    CTRL_ALM_VOLT = 0x40  # Set with a low-voltage condition
    CTRL_DEFAULT = CTRL_IO0DATA

    REG_SOC_L = 2
    REG_SOC_H = 3
    REG_SOC = REG_SOC_L  # Battery state of charge (SOC)
    
    REG_COUNTER_L = 4
    REG_COUNTER_H = 5
    REG_COUNTER = REG_COUNTER_L  # Number of conversions
    
    REG_CURRENT_L = 6
    REG_CURRENT_H = 7
    REG_CURRENT = REG_CURRENT_L  # Battery current, voltage drop over sense resistor
    
    REG_VOLTAGE_L = 8
    REG_VOLTAGE_H = 9
    REG_VOLTAGE = REG_VOLTAGE_L  # Battery voltage
    
    REG_TEMPERATURE = 10  # Temperature [C]
    
    # REG 11, 12 chip specific implementation
    
    REG_OCV_L = 13
    REG_OCV_H = 14
    REG_OCV = REG_OCV_L  # OCV register
    
    REG_CC_CNF_L = 15
    REG_CC_CNF_H = 16
    REG_CC_CNF = REG_CC_CNF_L  # Coulomb counter gas gauge configuration
    CC_CNF_DEFAULT = 395  # Coulomb-counter mode configuration default value
    
    REG_VM_CNF_L = 17
    REG_VM_CNF_H = 18
    REG_VM_CNF = REG_VM_CNF_L  # Voltage gas gauge algorithm parameter
    VM_CNF_DEFAULT = 321  # Voltage mode configuration default value
    
    REG_ALARM_SOC = 19  # SOC alarm level [0.5%]
    
    REG_ALARM_VOLTAGE = 20  # Battery low voltage alarm level [17.6mV]
    
    REG_CURRENT_THRES = 21  # Current threshold for current monitoring
    
    # REG 22, 23 chip specific implementation
    
    REG_ID = 24  # Part type ID = 16 (hex)
    CHIP_ID = None  # Expected chip ID, depends on specific chip

    # REG 25 - 30 chip specific implementation

    # REG 31: not used
    
    # REG 32-47: RAM registers, working registers for gas gauge
    REG_RAM0 = 32
    REG_RAM1 = 33
    REG_RAM2 = 34
    REG_RAM3 = 35
    REG_RAM4 = 36
    REG_RAM5 = 37
    REG_RAM6 = 38
    REG_RAM7 = 39
    REG_RAM8 = 40
    REG_RAM9 = 41
    REG_RAM10 = 42
    REG_RAM11 = 43
    REG_RAM12 = 44
    REG_RAM13 = 45
    REG_RAM14 = 46
    REG_RAM15 = 47
    REG_RAM_FIRST = REG_RAM0
    REG_RAM_LAST = REG_RAM15
    RAM_SIZE = (REG_RAM_LAST - REG_RAM_FIRST + 1)
    IDX_RAM_TEST = 0
    RAM_TEST = 0xB2  # Arbitrary test pattern
    IDX_RAM_SOC_L = 1
    IDX_RAM_SOC_H = 2
    IDX_RAM_SOC = IDX_RAM_SOC_L
    IDX_RAM_CC_CNF_L = 3
    IDX_RAM_CC_CNF_H = 4
    IDX_RAM_CC_CNF = IDX_RAM_CC_CNF_L
    IDX_RAM_VM_CNF_L = 5
    IDX_RAM_VM_CNF_H = 6
    IDX_RAM_VM_CNF = IDX_RAM_VM_CNF_L
    IDX_RAM_UNUSED_BEGIN = 7
    IDX_RAM_UNUSED_END = 14
    IDX_RAM_CRC = 15

    # REG 48-...: OCV adjustment registers
