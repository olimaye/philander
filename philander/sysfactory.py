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
    """Mnemonic designator for a lower-level lib, package or system\
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

    COMPOSITE = auto()
    """Supported by a matching upper-level driver API, such as ADC via SPI. 
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
    def autoDetectProvider( dependencies, fallback=SysProvider.NONE):
        """Automatically detect a eligible provider.
        
        Test the given dependencies and for the first available, return
        the associated provider mnemonic.
        
        The dependencies are given as a list of constellations to check.
        Each entry of that list is a tuple of (SysProvider Mnemonics, module name, class name)
        such as in (SysProvider.PERIPHERY, "periphery", "I2C").
        
        The fallback parameter is to override SysProvider.NONE in case
        none of the dependencies is fulfilled.

        :param list dependencies: List of tuples describing the supported libs.
        :param SysProvider fallback: Value to be returned, if none of
            the dependencies is fulfilled.
        :return: Mnemonic to identify the first dependency fulfilled.
            SysProvider.NONE or the given fallback, if no matching dependency
            could be found.
        :rtype: SysProvider
        """
        ret = fallback
        for entry in dependencies:
            try:
                #                    name,  globals, locals, fromlist
                module = __import__( entry[1], None, None, [entry[2],] )
                if hasattr(module, entry[2]):       # class name
                    ret = entry[0]                  # Mnemonics
                    break
                else:
                    # log something
                    pass
            except ImportError:
                pass
        return ret

    @staticmethod
    def createInstance( provider, implementations ):
        """Instantiate a certain implementation.
        
        Create an instance of an implementation identified by a provider
        mnemonics.
        
        The given provider parameter is the key argument into the
        dictionary of the implementations. It could be the result of
        calling :meth:`autoDetectProvider`.
        
        The implementations are given as a dictionary translating a
        SysProvider type key into a tuple (pair) -value comprised of
        module name and class name. For example:
        
        SysProvider.PERIPHERY:    ("philander.serialbus_periphery", "_SerialBus_Periphery")
        
        Instantiation is done by calling the empty constructor of the
        identified class.
        
        :param SysProvider provider: The provider mnemonics identifying
            the implementation to be instantiated.
        :param dict implementations: The dictionary describing where to
            find the specific class that must be instantiated, for a given
            provider key.
        :return: An object, which is an instance of the specific
            implementation or None in case of an error.
        :rtype: object
        """
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
    def getGPIO( provider=SysProvider.AUTO ):
        """Generates a GPIO implementation according to the requested provider.
        
        :param SysProvider provider: The low-level lib to rely on, or AUTO\
        for automatic detection.
        :return: A GPIO implementation object, or None in case of an error.
        :rtype: GPIO
        """
        deps = [(SysProvider.RPIGPIO, "RPi.GPIO", "GPIO"),
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
            provider = SysFactory.autoDetectProvider( deps, SysProvider.SIM )
        ret = SysFactory.createInstance( provider, impls )
        return ret
