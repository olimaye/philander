# TODO: all the comments

"""Register definitions for the STC311x family battery gas gauges.
    
Definition of registers and default values for the
above-mentioned chips.
Externalized, just for clarity of the source code.
"""
__author__ = "Carl Bellgardt"
__version__ = "0.1"
__all__ = ["STC3115_Reg", "STC3117_Reg", "_STC311x_Reg", "ChipType"]

from enum import Enum, auto


class ChipType(Enum):
    STC3115 = auto()
    STC3117 = auto()


class _STC311x_Reg:
    def __init__(self, Param_dict):
        # apply config
        self.CONFIG_GASGAUGE_0_RSENSE = Param_dict["Gasgauge.senseResistor"]
        self.CONFIG_GASGAUGE_0_BATTERY_IDX = Param_dict["Gasgauge.battery_idx"]  # TODO: what is this pin used for?
        self.CONFIG_GASGAUGE_0_GPIO_ALARM = Param_dict["Gasgauge.gpio_alarm_idx"]
        self.RELAX_MAX_DEFAULT = Param_dict["Gasgauge.cmonit_max"]
        self.SETUP_0_REG_CC_CNF = Param_dict["Gasgauge.cc_cnf"]
        self.SETUP_0_REG_VM_CNF = Param_dict["Gasgauge.vm_cnf"]
        self.SETUP_0_REG_ALARM_SOC = Param_dict["Gasgauge.alarm_soc"]
        self.SETUP_0_REG_ALARM_VOLTAGE = Param_dict["Gasgauge.alarm_voltage"]
        self.SETUP_0_REG_CURRENT_THRES = Param_dict["Gasgauge.current_thres"]
        self.SETUP_0_REG_CMONIT_MAX = Param_dict["Gasgauge.cmonit_max"]

    # Definition of registers and their content

    REG_MODE = 0  # Mode register
    # possible values of the mode register
    MODE_VMODE = 0x01  # 0: Mixed mode (Coulomb counter active); 1: Power saving voltage mode
    MODE_ALM_ENA = 0x08  # Alarm function enable
    MODE_GG_RUN = 0x10  # Standby / operating mode
    MODE_FORCE_CC = 0x20  # Forces the relaxation timer to switch to the Coulomb counter (CC) state.
    MODE_FORCE_VM = 0x40  # Forces the relaxation timer to switch to voltage mode (VM) state.

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
    # REG 11, 12 set in chip specific implementation
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
    REG_CMONIT_COUNT = 22  # Current monitoring counter
    REG_RELAX_COUNT = REG_CMONIT_COUNT
    REG_CMONIT_MAX = 23  # Maximum counter value for current monitoring
    REG_RELAX_MAX = REG_CMONIT_MAX
    RELAX_MAX_DEFAULT = None  # set in __init__()
    REG_ID = 24  # Part type ID = 16 (hex)
    CHIP_ID = None  # Expected chip ID, depends on specific chip

    # REG 25 - 30 set in chip specific implementation

    # RAM registers: Working registers for gas gauge
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

    # Define configuration (defaults)

    CONFIG_GASGAUGE_0_RSENSE = None  # Sense resistor in milli Ohm; set in __init__()
    CONFIG_RSENSE_DEFAULT = 10  # default value
    CONFIG_GASGAUGE_0_GPIO_ALARM = None  # GPIO pin index for interrupts; set in __init__()

    # TODO: all these configs below should be set via the __init__ and calculated accordingly
    # if defined(Gasgauge.battery_idx):
    # TODO: -> make default in Param_dict None?
    # TODO: how does this function work: #SETUP_0_REG_CC_CNF = ((CONFIG_GASGAUGE_0_RSENSE) * ( CFG_SUBSECTATR(BATTERY, CONFIG_GASGAUGE_0_BATTERY_IDX, CAPACITY) ) * 250 + 6194) / 12389
    # else: default case (if parameter is not given)
    SETUP_0_REG_CC_CNF = None  # set in __init__()

    # TODO: same as above:
    # if defined(Gasgauge.battery_idx):
    # SETUP_0_REG_VM_CNF = ((_CFG_SUBSECTATR(BATTERY, CONFIG_GASGAUGE_0_BATTERY_IDX, IMPEDANCE))  # (CFG_SUBSECTATR(BATTERY, CONFIG_GASGAUGE_0_BATTERY_IDX, CAPACITY)) # 50L + 24444L ) / 48889L
    # else
    SETUP_0_REG_VM_CNF = None  # set in __init__()

    # if defined(CONFIG_GASGAUGE_0_ALARM_SOC):
    # SETUP_0_REG_ALARM_SOC = (CONFIG_GASGAUGE_0_ALARM_SOC << 1)
    # else
    SETUP_0_REG_ALARM_SOC = None  # SOC lower threshold; SOC alarm level [0.5%]; set in __init__
    ALARM_SOC_DEFAULT = 2  # default value

    # if defined(CONFIG_GASGAUGE_0_ALARM_VOLTAGE):
    # SETUP_0_REG_ALARM_VOLTAGE = ((CONFIG_GASGAUGE_0_ALARM_VOLTAGE  # 5 + 44) / 88)
    # else
    SETUP_0_REG_ALARM_VOLTAGE = None  # Voltage lower threshold; 3.0 V; set in __init__()
    ALARM_VOLTAGE_DEFAULT = 170  # default value

    # if defined(CONFIG_GASGAUGE_0_RELAX_CURRENT):
    # SETUP_0_REG_CURRENT_THRES = ((CONFIG_GASGAUGE_0_RELAX_CURRENT  # CFG_SUBSECTATR(BATTERY, CONFIG_GASGAUGE_0_BATTERY_IDX, IMPEDANCE) + 23520L) / 47040L)
    # else
    SETUP_0_REG_CURRENT_THRES = None  # Current monitoring threshold; +/-470 V drop; set in __init__()
    CURRENT_THRES_DEFAULT = 10  # default value

    # if defined(CONFIG_GASGAUGE_0_RELAX_TIMER):
    # SETUP_0_REG_CMONIT_MAX = ((_CONFIG_GASGAUGE_0_RELAX_TIMER + 2) >> 2)
    # else
    SETUP_0_REG_CMONIT_MAX = None  # Monitoring timing threshold; CC-VM: 4 minutes; VM->CC: 1 minute; set in __init__()
    CMONIT_MAX_DEFAULT = 120  # default value

    # Other defines

    DEVICE_ADDRESS_I2C = 0x70  # I2C device address is fix.
    POR_DELAY_LOOPS_MAX = 2000  # Delay while doing a soft-reset.


class STC3115_Reg(_STC311x_Reg):
    CHIP_TYPE = ChipType.STC3115

    # STC3115 exclusive mode values (in addition to inherited values _STC311x_Reg._MODE_*)
    # possible values of the mode register REG_MODE
    MODE_CLR_VM_ADJ = 0x02  # Clear ACC_VM_ADJ and REG_VM_ADJ
    MODE_CLR_CC_ADJ = 0x04  # Clear ACC_CC_ADJ and REG_CC_ADJ
    MODE_DEFAULT = (_STC311x_Reg.MODE_VMODE | _STC311x_Reg.MODE_ALM_ENA)
    MODE_OFF = 0

    # STC3115 exclusive control values (in addition to inherited values _STC311x_Reg._CTRL_*)
    # possible values of the control register REG_CTRL
    # there are None.

    # Definition of registers and their content

    CHIP_ID = 0x14  # Expected ID found in REG_ID

    REG_CC_ADJ_H = 11  # Coulomb counter adjustment factor
    REG_VM_ADJ_H = 12  # Voltage mode adjustment factor

    REG_CC_ADJ_L = 25  # Coulomb counter adjustment factor
    REG_VM_ADJ_L = 26  # Voltage mode adjustment factor
    REG_ACC_CC_ADJ_L = 27
    REG_ACC_CC_ADJ_H = 28
    REG_ACC_CC_ADJ = REG_ACC_CC_ADJ_L  # Coulomb counter correction accumulator
    REG_ACC_VM_ADJ_L = 29
    REG_ACC_VM_ADJ_H = 30
    REG_ACC_VM_ADJ = REG_ACC_VM_ADJ_L  # Voltage mode correction accumulator

    # OCV adjustment table [0.55mV]
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


class STC3117_Reg(_STC311x_Reg):
    CHIP_TYPE = ChipType.STC3117

    # STC3117 exclusive mode values (in addition to inherited values _STC311x_Reg._MODE_*)
    # possible values of the mode register REG_MODE
    MODE_BATD_PU = 0x02  # BATD internal pull-up enable
    MODE_FORCE_CD = 0x04  # CD driven by internal logic / forced high
    MODE_DEFAULT = (_STC311x_Reg.MODE_VMODE | MODE_BATD_PU | _STC311x_Reg.MODE_ALM_ENA)
    MODE_OFF = MODE_BATD_PU

    # STC3117 exclusive control values (in addition to inherited values _STC311x_Reg._CTRL_*)
    # possible values of the control register REG_CTRL
    CTRL_UVLOD = 0x80  # UVLO event detection

    # Definition of registers and their content

    CHIP_ID = 0x16  # Expected ID found in REG_ID

    REG_AVG_CURRENT_L = 11
    REG_AVG_CURRENT_H = 12
    REG_AVG_CURRENT = REG_AVG_CURRENT_L  # Battery average current or SOC change rate

    REG_CC_ADJ_L = 27
    REG_CC_ADJ_H = 28
    REG_CC_ADJ = REG_CC_ADJ_L  # Coulomb counter adjustment register
    REG_VM_ADJ_L = 29
    REG_VM_ADJ_H = 30
    REG_VM_ADJ = REG_VM_ADJ_L  # Voltage mode adjustment register

    # Open Circuit Voltage (OCV) table registers
    # OCV points, 2 bytes per point [0.55mV]
    REG_OCVTAB0_L = 48
    REG_OCVTAB0_H = 49
    REG_OCVTAB0 = REG_OCVTAB0_L
    REG_OCVTAB1_L = 50
    REG_OCVTAB1_H = 51
    REG_OCVTAB1 = REG_OCVTAB1_L
    REG_OCVTAB2_L = 52
    REG_OCVTAB2_H = 453
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

    # State Of Charge (SOC) SOC points [0.5%]
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
