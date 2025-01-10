"""A system convergence layer for smbus, smbus2, periphery or simulative implementation.

The factory class provides implementations for hardware resources like
serial bus or GPIO pins. This unifies the APIs provided by packages
like smbus, smbus2, periphery or gpiozero etc.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["SysProvider", "SysFactory" ]

from philander.penum import Enum, unique, auto, idiotypic
#import warnings

from philander.systypes import ErrorCode

@unique
@idiotypic
class SysProvider(Enum):
    """Menmonic designator for a lower-level lib, package or system\
    environment to rely the implementation on.
    """
    NONE      = auto()
    """No low-level API available.
    """
    AUTO      = auto()
    """Auto-detect best matching lib/package.
    """
    SIM       = auto()
    """Built-in hardware simulation.
    """

    GPIOZERO = auto()
    """GPIO zero implementation for raspberry pi (https://gpiozero.readthedocs.io/en/latest/).
    """
    MICROPYTHON = auto()
    """MicroPython environment (https://docs.micropython.org).
    """
    PERIPHERY = auto()
    """Python periphery lib (https://pypi.org/project/python-periphery/).
    """
    RPIGPIO = auto()
    """RaspberryPi GPIO lib (https://pypi.org/project/RPi.GPIO/).
    """
    SMBUS2    = auto()
    """System Management Bus v2 (SMBUS2) implementation (https://pypi.org/project/smbus2/).
    """

class SysFactory():
    """As a factory, provide implementations for specific hardware resources.
    """

    @staticmethod
    def _autoDetectProvider( providers, fallback=SysProvider.NONE):
        ret = fallback
        # List of supported libs.
        # Each entry is a tuple of SysProvider Mnemonics, module name, class name,
        # such as in (SysProvider.PERIPHERY, "periphery", "I2C")
        for ent in providers:
            try:
                module = __import__( ent[1] )
                if hasattr(module, ent[2]):
                    ret = ent[0]
                    break
                else:
                    # log something
                    pass
            except ImportError:
                pass
        return ret

    @staticmethod
    def _createInstance( provider, implementations ):
        if provider in implementations:
            moduleName, className = implementations.get( provider )
            module = __import__(moduleName, None, None, [className])
            cls = getattr( module, className )
            ret = cls()
        else:
            #raise NotImplementedError('Driver module ' + str(provider) + ' is not supported.')
            # warnings.warn(
            #     "Cannot find GPIO factory lib. Using SIM. Consider installing RPi.GPIO, gpiozero or periphery!"
            # )
            ret = None
        return ret
        
    @staticmethod
    def getSerialBus( provider=SysProvider.AUTO ):
        """Generates a serial bus implementation according to the requested provider.
        
        :param SysProvider provider: The low-level lib to rely on, or AUTO\
        for automatic detection.
        :return: A serial bus implementation object, or None in case of an error.
        :rtype: SerialBus
        """
        provs = [(SysProvider.SMBUS2, "smbus2", "SMBus"),
                (SysProvider.PERIPHERY, "periphery", "I2C"),
                (SysProvider.MICROPYTHON, "machine", "I2C"),
                ]
        impls = {
                  SysProvider.MICROPYTHON:  ("philander.serialbus_micropython", "_SerialBus_Micropython"),
                  SysProvider.PERIPHERY:    ("philander.serialbus_periphery", "_SerialBus_Periphery"),
                  SysProvider.SIM:          ("philander.serialbus_sim", "_SerialBus_Sim"),
                  SysProvider.SMBUS2:       ("philander.serialbus_smbus2", "_SerialBus_SMBus2"),
                }
        if provider == SysProvider.AUTO:
            provider = SysFactory._autoDetectProvider( provs, SysProvider.SIM )
        ret = SysFactory._createInstance( provider, impls )
        return ret

    @staticmethod
    def getGPIO( provider=SysProvider.AUTO ):
        """Generates a GPIO implementation according to the requested provider.
        
        :param SysProvider provider: The low-level lib to rely on, or AUTO\
        for automatic detection.
        :return: A GPIO implementation object, or None in case of an error.
        :rtype: GPIO
        """
        provs = [(SysProvider.RPIGPIO, "RPi.GPIO", "GPIO"),
                (SysProvider.GPIOZERO, "gpiozero", "DigitalOutputDevice"),
                (SysProvider.PERIPHERY, "periphery", "GPIO"),
                (SysProvider.MICROPYTHON, "machine", "Pin"),
                ]
        impls = {
                  SysProvider.GPIOZERO:     ("philander.gpio_zero", "_GPIO_Zero"),
                  SysProvider.MICROPYTHON:  ("philander.gpio_micropython", "_GPIO_Micropython"),
                  SysProvider.PERIPHERY:    ("philander.gpio_periphery", "_GPIO_Periphery"),
                  SysProvider.RPIGPIO:      ("philander.gpio_rpi", "_GPIO_RPi"),
                  SysProvider.SIM:          ("philander.gpio_sim", "_GPIO_Sim"),
                }
        if provider == SysProvider.AUTO:
            provider = SysFactory._autoDetectProvider( provs, SysProvider.SIM )
        ret = SysFactory._createInstance( provider, impls )
        return ret
    