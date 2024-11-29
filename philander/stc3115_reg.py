"""Register definitions for the STC311x family battery gas gauges.
    
Definition of registers and default values for the
above-mentioned chips.
Externalized, just for clarity of the source code.
"""
__author__ = "Carl Bellgardt"
__version__ = "0.1"
__all__ = ["STC3115_Reg", ]

from philander.STC311x_Reg import STC311x_Reg

class STC3115_Reg(STC311x_Reg):
    """Definition of the STC3115 exclusive registers and values.
    
    Registers and content interpretation specific to this chip. It
    complements those definitions inherited from the base class.
    """
    
    # Register 0: REG_MODE
    MODE_CLR_VM_ADJ = 0x02  # Clear ACC_VM_ADJ and REG_VM_ADJ
    MODE_CLR_CC_ADJ = 0x04  # Clear ACC_CC_ADJ and REG_CC_ADJ

    # Register 1: REG_CTRL
    # Register 2: REG_SOC_L
    # Register 3: REG_SOC_H
    # Register 4: REG_COUNTER_L
    # Register 5: REG_COUNTER_H
    # Register 6: REG_CURRENT_L
    # Register 7: REG_CURRENT_H
    # Register 8: REG_VOLTAGE_L
    # Register 9: REG_VOLTAGE_H
    # Register 10: REG_TEMPERATURE
    
    # Register 11: REG_CC_ADJ_H
    REG_CC_ADJ_H = 11  # Coulomb counter adjustment factor (high)
    
    # Register 12: REG_VM_ADJ_H
    REG_VM_ADJ_H = 12  # Voltage mode adjustment factor (high)
    
    # Register 13: REG_OCV_L
    # Register 14: REG_OCV_H
    # Register 15: REG_CC_CNF_L
    # Register 16: REG_CC_CNF_H
    # Register 17: REG_VM_CNF_L
    # Register 18: REG_VM_CNF_H
    # Register 19: REG_ALARM_SOC
    # Register 20: REG_ALARM_VOLTAGE
    # Register 21: REG_CURRENT_THRES
    
    # Register 22: REG_RELAX_COUNT
    REG_RELAX_COUNT = 22    # Relaxation counter

    # Register 23: REG_RELAX_MAX
    REG_RELAX_MAX = 23  # Relaxation counter max value
    RELAX_MAX_DEFAULT = 0x78

    # Register 24: REG_ID
    CHIP_ID = 0x14  # Expected ID found in REG_ID

    # Register 25: REG_CC_ADJ_L, see Reg#11 for high-part
    REG_CC_ADJ_L = 25  # Coulomb counter adjustment factor (low)

    # Register 26: REG_VM_ADJ_L, see Reg#12 for high-part
    REG_VM_ADJ_L = 26  # Voltage mode adjustment factor (low)
    
    # Register 27/28: REG_ACC_CC_ADJ_L/H
    REG_ACC_CC_ADJ_L = 27
    REG_ACC_CC_ADJ_H = 28
    REG_ACC_CC_ADJ = REG_ACC_CC_ADJ_L  # Coulomb counter correction accumulator

    # Register 29/30: REG_ACC_VM_ADJ_L/H
    REG_ACC_VM_ADJ_L = 29
    REG_ACC_VM_ADJ_H = 30
    REG_ACC_VM_ADJ = REG_ACC_VM_ADJ_L  # Voltage mode correction accumulator

    # REG 31: not used
    # REG 32-47: RAM registers, working registers for gas gauge
    # REG 48-63: OCV adjustment registers
    # OCV adjustment table, LSB=0.55mV
    REG_OCVTAB0 = 48
    REG_OCVTAB1 = 49
    REG_OCVTAB2 = 50
    REG_OCVTAB3 = 51
    REG_OCVTAB4 = 52
    REG_OCVTAB5 = 53
    REG_OCVTAB6 = 54
    REG_OCVTAB7 = 55
    REG_OCVTAB8 = 56
    REG_OCVTAB9 = 57
    REG_OCVTAB10 = 58
    REG_OCVTAB11 = 59
    REG_OCVTAB12 = 60
    REG_OCVTAB13 = 61
    REG_OCVTAB14 = 62
    REG_OCVTAB15 = 63
    OCV_DEFAULT = 0

