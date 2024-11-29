"""Register definitions for the STC311x family battery gas gauges.
    
Definition of registers and default values for the
above-mentioned chips.
Externalized, just for clarity of the source code.
"""
__author__ = "Carl Bellgardt"
__version__ = "0.1"
__all__ = ["STC3117_Reg", ]

from philander.STC311x_Reg import STC311x_Reg

class STC3117_Reg(STC311x_Reg):
    """Definition of the STC3115 exclusive registers and values.
    
    Registers and content interpretation specific to this chip. It
    complements those definitions inherited from the base class.
    """

    # Register REG_MODE
    MODE_BATD_PU = 0x02  # BATD internal pull-up enable
    MODE_FORCE_CD = 0x04  # CD driven by internal logic / forced high
    MODE_OFF = STC311x_Reg.MODE_OFF | MODE_BATD_PU
    MODE_DEFAULT = STC311x_Reg.MODE_DEFAULT | MODE_BATD_PU

    # Register 1: REG_CTRL
    CTRL_UVLOD = 0x80  # UVLO event detection

    # Register 2: REG_SOC_L
    # Register 3: REG_SOC_H
    # Register 4: REG_COUNTER_L
    # Register 5: REG_COUNTER_H
    # Register 6: REG_CURRENT_L
    # Register 7: REG_CURRENT_H
    # Register 8: REG_VOLTAGE_L
    # Register 9: REG_VOLTAGE_H
    # Register 10: REG_TEMPERATURE

    # Register 11/12: REG_AVG_CURRENT_L/H
    REG_AVG_CURRENT_L = 11
    REG_AVG_CURRENT_H = 12
    REG_AVG_CURRENT = REG_AVG_CURRENT_L  # Battery average current or SOC change rate

    # Register 13: REG_OCV_L
    # Register 14: REG_OCV_H
    # Register 15: REG_CC_CNF_L
    # Register 16: REG_CC_CNF_H
    # Register 17: REG_VM_CNF_L
    # Register 18: REG_VM_CNF_H
    # Register 19: REG_ALARM_SOC
    # Register 20: REG_ALARM_VOLTAGE
    # Register 21: REG_CURRENT_THRES
    
    # Register 22: REG_CMONIT_COUNT
    REG_CMONIT_COUNT = 22  # Current monitoring counter

    # Register 23: REG_CMONIT_MAX
    REG_CMONIT_MAX = 23  # Maximum counter value for current monitoring
    CMONIT_MAX_DEFAULT = 0x78
    
    # Register 24: REG_ID
    CHIP_ID = 0x16  # Expected ID found in REG_ID

    # Register 25-26: not used

    # Register 27/28: REG_CC_ADJ_L/H
    REG_CC_ADJ_L = 27
    REG_CC_ADJ_H = 28
    REG_CC_ADJ = REG_CC_ADJ_L  # Coulomb counter adjustment register

    # Register 29/30: REG_VM_ADJ_L/H
    REG_VM_ADJ_L = 29
    REG_VM_ADJ_H = 30
    REG_VM_ADJ = REG_VM_ADJ_L  # Voltage mode adjustment register

    # REG 31: not used
    # REG 32-47: RAM registers, working registers for gas gauge
    # REG 48-79: Open Circuit Voltage (OCV) table registers
    # OCV points, 2 bytes per point [0.55mV]
    REG_OCVTAB0_L = 48
    REG_OCVTAB0_H = 49
    REG_OCVTAB0 = REG_OCVTAB0_L
    REG_OCVTAB1_L = 50
    REG_OCVTAB1_H = 51
    REG_OCVTAB1 = REG_OCVTAB1_L
    REG_OCVTAB2_L = 52
    REG_OCVTAB2_H = 53
    REG_OCVTAB2 = REG_OCVTAB2_L
    REG_OCVTAB3_L = 54
    REG_OCVTAB3_H = 55
    REG_OCVTAB3 = REG_OCVTAB3_L
    REG_OCVTAB4_L = 56
    REG_OCVTAB4_H = 57
    REG_OCVTAB4 = REG_OCVTAB4_L
    REG_OCVTAB5_L = 58
    REG_OCVTAB5_H = 59
    REG_OCVTAB5 = REG_OCVTAB5_L
    REG_OCVTAB6_L = 60
    REG_OCVTAB6_H = 61
    REG_OCVTAB6 = REG_OCVTAB6_L
    REG_OCVTAB7_L = 62
    REG_OCVTAB7_H = 63
    REG_OCVTAB7 = REG_OCVTAB7_L
    REG_OCVTAB8_L = 64
    REG_OCVTAB8_H = 65
    REG_OCVTAB8 = REG_OCVTAB8_L
    REG_OCVTAB9_L = 66
    REG_OCVTAB9_H = 67
    REG_OCVTAB9 = REG_OCVTAB9_L
    REG_OCVTAB10_L = 68
    REG_OCVTAB10_H = 69
    REG_OCVTAB10 = REG_OCVTAB10_L
    REG_OCVTAB11_L = 70
    REG_OCVTAB11_H = 71
    REG_OCVTAB11 = REG_OCVTAB11_L
    REG_OCVTAB12_L = 72
    REG_OCVTAB12_H = 73
    REG_OCVTAB12 = REG_OCVTAB12_L
    REG_OCVTAB13_L = 74
    REG_OCVTAB13_H = 75
    REG_OCVTAB13 = REG_OCVTAB13_L
    REG_OCVTAB14_L = 76
    REG_OCVTAB14_H = 77
    REG_OCVTAB14 = REG_OCVTAB14_L
    REG_OCVTAB15_L = 78
    REG_OCVTAB15_H = 79
    REG_OCVTAB15 = REG_OCVTAB15_L
    OCV0_DEFAULT = 0x1770  # 3300 mV
    OCV1_DEFAULT = 0x1926  # 3541 mV
    OCV2_DEFAULT = 0x19B2  # 3618 mV
    OCV3_DEFAULT = 0x19FB  # 3658 mV
    OCV4_DEFAULT = 0x1A3E  # 3695 mV
    OCV5_DEFAULT = 0x1A6D  # 3721 mV
    OCV6_DEFAULT = 0x1A9D  # 3747 mV
    OCV7_DEFAULT = 0x1AB6  # 3761 mV
    OCV8_DEFAULT = 0x1AD5  # 3778 mV
    OCV9_DEFAULT = 0x1B01  # 3802 mV
    OCV10_DEFAULT = 0x1B70  # 3863 mV
    OCV11_DEFAULT = 0x1BB1  # 3899 mV
    OCV12_DEFAULT = 0x1BE8  # 3929 mV
    OCV13_DEFAULT = 0x1C58  # 3991 mV
    OCV14_DEFAULT = 0x1CF3  # 4076 mV
    OCV15_DEFAULT = 0x1DA9  # 4176 mV

    # REG 80-95: State Of Charge (SOC) SOC points [0.5%]
    REG_SOCTAB0 = 80
    REG_SOCTAB1 = 81
    REG_SOCTAB2 = 82
    REG_SOCTAB3 = 83
    REG_SOCTAB4 = 84
    REG_SOCTAB5 = 85
    REG_SOCTAB6 = 86
    REG_SOCTAB7 = 87
    REG_SOCTAB8 = 88
    REG_SOCTAB9 = 89
    REG_SOCTAB10 = 90
    REG_SOCTAB11 = 91
    REG_SOCTAB12 = 92
    REG_SOCTAB13 = 93
    REG_SOCTAB14 = 94
    REG_SOCTAB15 = 95
    SOC0_DEFAULT = 0x00  # 0 %
    SOC1_DEFAULT = 0x06  # 3 %
    SOC2_DEFAULT = 0x0C  # 6 %
    SOC3_DEFAULT = 0x14  # 10 %
    SOC4_DEFAULT = 0x1E  # 15 %
    SOC5_DEFAULT = 0x28  # 20 %
    SOC6_DEFAULT = 0x32  # 25 %
    SOC7_DEFAULT = 0x3C  # 30 %
    SOC8_DEFAULT = 0x50  # 40 %
    SOC9_DEFAULT = 0x64  # 50 %
    SOC10_DEFAULT = 0x7B  # 60 %
    SOC11_DEFAULT = 0x82  # 65 %
    SOC12_DEFAULT = 0x8C  # 70 %
    SOC13_DEFAULT = 0xA0  # 80 %
    SOC14_DEFAULT = 0xB4  # 90 %
    SOC15_DEFAULT = 0xC8  # 100 %
