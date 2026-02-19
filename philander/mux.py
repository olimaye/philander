"""Module to control multiplexer chips.

Usually, multiplexer / de-multiplexer connect one *common* line `X` to
one of four or one of eight other lines `Y0, Y1, ...`.
As this connection can be used both ways, those Y-lines are often called
input / output or I/O channels.

The selection is made by two (1:4) or three (1:8) control lines
`A, B, ...`, which can be interpreted as a bit pattern.
Moreover, there may be an enable or disable line to have no connection
at all. A general pin/logic scheme of a 3:8 de-/multiplexer could look
like this::

         Y0 Y1 Y2 Y3 Y4 Y5 Y6 Y7
          |  |  |  |  |  |  |  |
        +-----------------------+
    A --|                       |
    B --|          *            |-- ENA
    C --|                       |
        +-----------------------+
                   |
                   X             
             
Typical implementations of such devices are the
`TI SN74HCS237 <https://www.ti.com/product/de-de/SN74HCS237>`_,
`ST M74HC4851 <https://www.st.com/en/switches-and-multiplexers/m74hc4851.html>`_, and
`ST HCF4051 <https://www.st.com/en/switches-and-multiplexers/hcf4051.html>`_.

Variants of this chip family work as de-multiplexer or decoder, only:
Lacking a *common* line, the I/O lines are operated in *output* only.
This can be used to drive exactly one out of four or eight lines high or
low. An example of this sort of device is the
`TI SN74LVC138 <https://www.ti.com/product/de-de/SN74LVC138A>`_,

Note that the core intention of this module is to control the `A, B, C`
selector bits and the `ENA` enabling/disabling/inhibiting line, if
present.
However, manipulating the common `X` and I/O `Y` lines is beyond the
scope of this driver.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Mux"]

import logging

from .gpio import GPIO
from .module import Module
from .systypes import ErrorCode


class Mux( Module ):
    """Generic driver class for a de-/multiplexer device.
    """
    
    MAXNUM_BITS = 4
    MODULE_PARAM_PREFIX = "mux."
    
    def __init__(self):
        """Initialize the instance with defaults.
        
        The size of the multiplexer, i.e. the number of control bits
        `A, B, C, ...` is implicitly defined by the number of GPIO
        configurations passed to :meth:`.open`. 
        
        Also see: :meth:`.Params_init`
        """
        self.bit = list()
        self.ena = None
        self.maxValue = 0

    #
    # Module API
    #

    @classmethod
    def Params_init(cls, paramDict):
        """Initializes configuration parameters with defaults.
        
        Note that general or global GPIO adjustments or defaults can be
        set using the `mux.gpio.*` keys.
        They apply to both, the bit control lines as well as the
        enable line.
        They can be pin-wise overridden by specific e.g.
        `mux.bit0.gpio.*` settings.
        
        The following settings are supported:
        
        ==================================   ================================================================
        Key name                             Value type, meaning and default
        ==================================   ================================================================
        mux.gpio.pinNumbering                Global setting: numbering scheme
        mux.gpio.inverted                    Global setting: True if low-active
        mux.gpio.level                       Global setting: initial logic level
        mux.bit[0...3].gpio.pinNumbering     Bit pin: Numbering scheme
        mux.bit[0...3].gpio.pinDesignator    Bit pin: Name or number of the pin
        mux.bit[0...3].gpio.inverted         Bit pin: True, if pin is low-active
        mux.bit[0...3].gpio.level            Bit pin: Initial logic level
        mux.enable.gpio.pinNumbering         ENA pin: Numbering scheme
        mux.enable.gpio.pinDesignator        ENA pin: Name or number of the pin
        mux.enable.gpio.inverted             ENA pin: True, if pin is low-active
        mux.enable.gpio.level                ENA pin: Initial logic level
        =====================================================================================================
        
        The number of `mux.bit0.pinDesignator`, `mux.bit1.pinDesignator`
        etc. settings implicitly defines the size of the multiplexer,
        i.e. the number of control bits. For safety reasons, a 4 bit
        multiplexer (1:16) is supported, at maximum.
        
        If the `mux.enable.pinDesignator` is not given, the driver
        assumes, there is no enable/disable line.
        
        Also see: :meth:`.Module.Params_init`, :meth:`.GPIO.Params_init`.
        """
        # Driver defaults
        gpioDefaults = {}
        gpioDefaults["gpio.direction"] = GPIO.DIRECTION_OUT
        GPIO.Params_init( gpioDefaults )
        # Mux global defaults
        for key, value in gpioDefaults.items():
            tempKey = Mux.MODULE_PARAM_PREFIX + key
            if not( tempKey in paramDict):
                paramDict[tempKey] = value
        # Specific bit configurations
        prefixDefault = Mux.MODULE_PARAM_PREFIX
        for idx in range(Mux.MAXNUM_BITS):
            prefix = Mux.MODULE_PARAM_PREFIX + "bit" + str(idx) + "."
            tempKey = prefix + "gpio.pinDesignator"
            if( tempKey in paramDict ):
                paramDict[prefix+"gpio.direction"] = GPIO.DIRECTION_OUT
                for key in gpioDefaults.keys():
                    tempKey = prefix + key
                    if not( tempKey in paramDict):
                        paramDict[tempKey] = paramDict[prefixDefault+key]
            else:
                break
        # ENA line configuration
        prefix = Mux.MODULE_PARAM_PREFIX + "enable."
        tempKey = prefix + "gpio.pinDesignator"
        if( tempKey in paramDict ):
            paramDict[prefix+"gpio.direction"] = GPIO.DIRECTION_OUT
            for key in gpioDefaults.keys():
                tempKey = prefix + key
                if not( tempKey in paramDict):
                    paramDict[tempKey] = paramDict[prefixDefault+key]
        # This class defaults
        # defaults = {
        #     Mux.PARAM_PREFIX + "key"   : False,
        #     }
        # for key, value in defaults.items():
        #     if not key in paramDict:
        #         paramDict[key] = value
        return None


    def open(self, paramDict):
        ret = ErrorCode.errOk
        if self.bit or self.ena:
            ret = ErrorCode.errResourceConflict
        else:
            Mux.Params_init( paramDict )
            for idx in range(Mux.MAXNUM_BITS):
                prefix = Mux.MODULE_PARAM_PREFIX + "bit" + str(idx) + "."
                tempKey = prefix + "gpio.pinDesignator"
                if( tempKey in paramDict ):
                    # Extract GPIO parameters
                    gpioParams = dict( [(k.replace(prefix, ""),v) for k,v in paramDict.items() if k.startswith(prefix)] )
                    pin = GPIO.getGPIO()
                    ret = pin.open(gpioParams)
                    if( ret == ErrorCode.errOk ):
                        self.bit.append(pin)
                    else:
                        logging.debug("Mux couldn't open pin #%d (%s), error: %s.", \
                                      idx, gpioParams["gpio.pinDesignator"], ret)
                        for  pin in self.bit: pin.close()
                        self.bit.clear()
                        break
                else:
                    break
        if( (ret == ErrorCode.errOk) and not self.bit ):
            ret = ErrorCode.errFewData
        if( ret == ErrorCode.errOk ):
            prefix = Mux.MODULE_PARAM_PREFIX + "enable."
            tempKey = prefix + "gpio.pinDesignator"
            if( tempKey in paramDict ):
                # Extract GPIO parameters
                gpioParams = dict( [(k.replace(prefix, ""),v) for k,v in paramDict.items() if k.startswith(prefix)] )
                self.ena = GPIO.getGPIO()
                ret = self.ena.open(gpioParams)
                if( ret != ErrorCode.errOk ):
                    logging.debug("Mux couldn't open enable line (%s), error: %s.", \
                                  gpioParams["gpio.pinDesignator"], ret)
                    self.ena = None
                    for  pin in self.bit: pin.close()
                    self.bit.clear()
        if( ret == ErrorCode.errOk ):
            self.maxValue = (1 << len(self.bit)) - 1
        
        logging.debug('Mux.open() returns: %s.', ret)
        return ret
    
    def close(self):
        ret = ErrorCode.errOk
        self.disable()
        for  pin in self.bit:
            err = pin.close()
            if( (ret==ErrorCode.errOk) and (err!=ErrorCode.errOk)):
                ret = err
        self.bit.clear()
        if self.ena:
            err = self.ena.close()
            if( (ret==ErrorCode.errOk) and (err!=ErrorCode.errOk)):
                ret = err
            self.ena = None
        self.maxValue = 0
        logging.debug('Mux closed, return: %s.', ret)
        return ret
    
    #
    # Mux specific API
    #
    
    def select(self, number, automute=False):
        """Switch to the channel with the given, zero-based number.
        
        Depending on the size of the multiplexer, the least-significant
        bits of the given number are used to set the control lines
        `A`, `B`, `C` etc. That directly determines, which of the I/O
        channels `Y0`, `Y1`, etc. is connected to the common line `X`.
        
        If the `automute` flag is set, the device is first disabled.
        Then, the channel is selected and finally, the device is enabled,
        again. Note that this will always leave the device in an enabled
        state!
        
        :param int number: Zero-based index number of the channel to select.
        :param bool automute: Flag, if the device should be disabled for switching.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if self.bit:
            if automute:
                self.enable(False)
            acc = int(number)
            for pin in self.bit:
                level = GPIO.LEVEL_HIGH if (acc & 1) else GPIO.LEVEL_LOW
                err = pin.set( level )
                if( (ret==ErrorCode.errOk) and (err!=ErrorCode.errOk)):
                    ret = err
                acc = acc >> 1
            if automute:
                self.enable(True)
        else:
            ret = ErrorCode.errNotInited
        logging.debug('Mux selected %d, return: %s.', number, ret)
        return ret
       
    def enable(self, activate=True):
        """Set the ENA line to activate the device as given.
        
        If supported by the driven chip, enables or disables the devices,
        as given by the `activate` parameter. Note that the actual
        effect on the physical line may be inverted by using the GPIO's
        `inverted` option. This may be necessary to semantically match
        the chip's `ENA` line meaning and behavior.
        
        :param bool activate: Whether to activate (default) or deactivate the multiplexer.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if self.ena:
            level = GPIO.LEVEL_HIGH if activate else GPIO.LEVEL_LOW
            ret = self.ena.set( level )
        else:
            ret = ErrorCode.errNotSupported
        logging.debug('Mux ENA set to %s, return: %s.', activate, ret)
        return ret
    
    def disable(self):
        """Disable the multiplexer, if supported by the underlying chip.
        
        Also see: :meth:`.enable`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return self.enable(False)
