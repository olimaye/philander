"""Module to control a shift register.

A shift register is a micro-electronic device providing a series of
flip-flops, where the output of one flip-flop is connected to the input
of the next one. 
Although there are different types of shifts registers, those which are
addressed by this module, are configured as serial-in, parallel-out (SIPO).

Data is shifted in serially through DIN by each cycle of the
clock DCLK and can be read in parallel from all outputs Q0, Q1, Q2, ...
simultaneously.
The highest significant bit (Q7') shifted out may be available as QOVR.
The content of the flip-flops may be cleared by DCLR.
Further, there are implementations with buffered outputs (latches).
Those may involve additional lines to copy (latch) the current content
of the flip-flops into the buffer by RCLK and to clear the buffer by
cycling RCLR.
Finally, there may be an enabling line ENA. In some devices, this enables
or disables the whole chip. This is useful e.g. for putting the device
into a deep sleep mode in power-critical applications. Upon recovery
from sleep, the content of the flip-flops may get lost.
Other implementations interpret ENA to just mute or un-mute the outputs
Q while still allowing to alter the register contents.
Finally, ENA might de-couple the serial communication DIN/DCLK. These
implementations preserve the content but pause further feeding of the
shift register while ENA is inactive.

A symbolic visualization of a shift register could look like this::

             Q0 Q1 Q2 Q3 Q4 Q5 Q6 Q7
              ^  ^  ^  ^  ^  ^  ^  ^
              |  |  |  |  |  |  |  |
            +-----------------------+
    DIN  -->|                       |--> QOVR
    DCLK -->|                       |<-- RCLK
    DCLR -->|                       |<-- RCLR
    ENA  -->|                       |
            +-----------------------+

             
Typical implementations of such devices are the
`TI SN74HC594 <https://www.ti.com/product/de-de/SN74HC594>`_,
`ST M74HC595 <https://www.st.com/en/automotive-logic-ics/m74hc595.html>`_, and
`ST HCF4094 <https://www.st.com/en/automotive-logic-ics/hcf4094.html>`_.

Note that handling the output Q0, Q1, ..., QOVR is beyond the scope of
this module.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["ShiftReg"]

import logging

from .gpio import GPIO
from .module import Module
from .systypes import ErrorCode


class ShiftReg( Module ):
    """Driver class for a shift register device.
    
    The implementation provided here, does not assume a
    specific size of the shift register, i.e. number of flip-flops.
    Although it provides an implementation for controlling the DIN and
    DCLK lines, i.e. the process of shifting bits into the register,
    it is meant to be derived for more sophisticated / efficient
    implementations. 
    
    Note that for all GPIO lines configured, the actual physical effect
    may be inverted by using the GPIO's `inverted` configuratio parameter.
    This may be necessary to semantically match the chip's implementation
    and behavior.
    """
        
    PIN_IDX_DCLR    = 0
    PIN_IDX_ENA     = 1
    PIN_IDX_RCLK    = 2
    PIN_IDX_RCLR    = 3
    PIN_IDX_DIN     = 4
    PIN_IDX_DCLK    = 5
    PIN_MAXNUM      = 6
    
    MODULE_PARAM_PREFIX = "shiftreg"
    ITEM_PARAM_PREFIX   = ("dclr", "enable", "rclk", "rclr", "din", "dclk")
    
    def __init__(self):
        """Initialize the instance with defaults.
        
        Also see: :meth:`.Params_init`
        """
        self.pin = [None] * ShiftReg.PIN_MAXNUM

    #
    # Module API
    #

    @classmethod
    def Params_init(cls, paramDict):
        """Initializes configuration parameters with defaults.
        
        General or global GPIO adjustments or defaults can be set using
        the `shiftreg.gpio.*` keys. They can be pin-wise overridden by
        specific e.g. `shiftreg.ena.gpio.*` settings.
        
        The following settings are supported:
        
        ==================================   ================================================================
        Key name                             Value type, meaning and default
        ==================================   ================================================================
        shiftreg.gpio.pinNumbering           Global setting: numbering scheme
        shiftreg.gpio.inverted               Global setting: True if low-active
        shiftreg.gpio.level                  Global setting: initial logic level
        shiftreg.din.gpio.pinNumbering       DIN pin: Numbering scheme
        shiftreg.din.gpio.pinDesignator      DIN pin: Name or number of the pin
        shiftreg.din.gpio.inverted           DIN pin: True, if pin is low-active
        shiftreg.din.gpio.level              DIN pin: Initial logic level
        shiftreg.dclk.gpio.pinNumbering      DCLK pin: Numbering scheme
        shiftreg.dclk.gpio.pinDesignator     DCLK pin: Name or number of the pin
        shiftreg.dclk.gpio.inverted          DCLK pin: True, if pin is low-active
        shiftreg.dclk.gpio.level             DCLK pin: Initial logic level
        shiftreg.dclr.gpio.pinNumbering      DCLR pin: Numbering scheme
        shiftreg.dclr.gpio.pinDesignator     DCLR pin: Name or number of the pin
        shiftreg.dclr.gpio.inverted          DCLR pin: True, if pin is low-active
        shiftreg.dclr.gpio.level             DCLR pin: Initial logic level
        shiftreg.rclk.gpio.pinNumbering      RCLK pin: Numbering scheme
        shiftreg.rclk.gpio.pinDesignator     RCLK pin: Name or number of the pin
        shiftreg.rclk.gpio.inverted          RCLK pin: True, if pin is low-active
        shiftreg.rclk.gpio.level             RCLK pin: Initial logic level
        shiftreg.rclr.gpio.pinNumbering      RCLR pin: Numbering scheme
        shiftreg.rclr.gpio.pinDesignator     RCLR pin: Name or number of the pin
        shiftreg.rclr.gpio.inverted          RCLR pin: True, if pin is low-active
        shiftreg.rclr.gpio.level             RCLR pin: Initial logic level
        shiftreg.enable.gpio.pinNumbering    ENA pin: Numbering scheme
        shiftreg.enable.gpio.pinDesignator   ENA pin: Name or number of the pin
        shiftreg.enable.gpio.inverted        ENA pin: True, if pin is low-active
        shiftreg.enable.gpio.level           ENA pin: Initial logic level
        =====================================================================================================
        
        If the `shiftreg.*.pinDesignator` is not given, the driver
        assumes, the corresponding line is not present or implemented.
        
        Also see: :meth:`.Module.Params_init`, :meth:`.GPIO.Params_init`.
        """
        # Driver defaults
        gpioDefaults = {}
        gpioDefaults["gpio.direction"] = GPIO.DIRECTION_OUT
        GPIO.Params_init( gpioDefaults )
        # global defaults
        for key, value in gpioDefaults.items():
            itemKey = ShiftReg.MODULE_PARAM_PREFIX + "." + key
            if not( itemKey in paramDict):
                paramDict[itemKey] = value
        # specific line configuration
        for idx in range(ShiftReg.PIN_MAXNUM):
            prefix = ShiftReg.MODULE_PARAM_PREFIX + "." + \
                     ShiftReg.ITEM_PARAM_PREFIX[idx] + "."
            if( (prefix + "gpio.pinDesignator") in paramDict ):
                paramDict[prefix+"gpio.direction"] = GPIO.DIRECTION_OUT
                for key in gpioDefaults.keys():
                    itemKey = prefix + key
                    if not( itemKey in paramDict):
                        paramDict[itemKey] = paramDict[ShiftReg.MODULE_PARAM_PREFIX + "." + key]
        return None


    def open(self, paramDict):
        ret = ErrorCode.errOk
        if not [p for p in self.pin if not p]:
            ret = ErrorCode.errResourceConflict
        if ret.isOk():
            self.Params_init( paramDict )
            for idx in range(ShiftReg.PIN_MAXNUM):
                prefix = ShiftReg.MODULE_PARAM_PREFIX + "." + \
                         ShiftReg.ITEM_PARAM_PREFIX[idx] + "."
                itemKey = prefix + "gpio.pinDesignator"
                if( itemKey in paramDict ):
                    # Extract GPIO parameters
                    gpioParams = dict( [(k.replace(prefix, ""),v) for k,v in paramDict.items() if k.startswith(prefix)] )
                    self.pin[idx] = GPIO.getGPIO()
                    ret = self.pin[idx].open(gpioParams)
                    if not ret.isOk():
                        logging.debug("ShiftReg couldn't open pin #%s (%s), error: %s.", \
                                      ShiftReg.ITEM_PARAM_PREFIX[idx], \
                                      gpioParams["gpio.pinDesignator"], \
                                      ret)
                        break
            if not ret.isOk():
                # Roll-back
                for idx in range(ShiftReg.PIN_MAXNUM):
                    if self.pin[idx]:
                        self.pin[idx].close()
                        self.pin[idx] = None
        if ret.isOk():
            for idx in (ShiftReg.PIN_IDX_DCLR, ShiftReg.PIN_IDX_RCLK, ShiftReg.PIN_IDX_RCLR):
                if self.pin[idx]:
                    self.pin[idx].set( GPIO.LEVEL_LOW )
            self.clearData()
            self.clearLatch()
            self.enable()
        logging.debug('ShiftReg.open() returns: %s.', ret)
        return ret
    
    def close(self):
        ret = ErrorCode.errOk
        self.disable()
        for idx in range(ShiftReg.PIN_MAXNUM):
            if self.pin[idx]:
                err = self.pin[idx].close()
                self.pin[idx] = None
                if( ret.isOk() and not err.isOk() ):
                    ret = err
        logging.debug('ShiftReg closed, return: %s.', ret)
        return ret
    
    #
    # Module specific API
    #
    
    def write(self, data, numBits=1, autoLatch=True):
        """Feed data into the first stage of the shift register.
        
        The lowest significant number of bits as given by the `numBits`
        parameter is written to DIN sequentially, starting with the
        highest-significant bit, first. If, for example,
        `data = 141 = 0x8d = 10001101b` and `numBits=4`, the sequence
        `1-1-0-1´ is written in that order.
        For each bit written, DIN is set correspondingly and DCLK is
        cycled once to logic `high`and back to logic `low`.
        
        This implementation is GPIO based and accepts single bits to be
        shifted in - at the price of dedicated GPIO lines for DIN and
        DCLK. Implementations in derived classes may depend on SPI or
        other mechanisms and, hence, put restrictions on what `numBits`
        can be. 
        
        If `autoLatch` is `True` and depending on the underlying
        hardware, the resulting content of the shift register is
        latched into the buffer.
        
        :param int data: The data to send to the shift register.
        :param int numBits: Non-negative number of least-significant \
        bits in 'data' to shift-in. Usually 1, 4 or multiple of 8. 
        :param bool autoLatch: Whether to automatically latch the result into the buffer.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if not self.pin[ShiftReg.PIN_IDX_DIN] or not self.pin[ShiftReg.PIN_IDX_DCLK]:
            ret = ErrorCode.errNotSupported
        elif not isinstance( data, int ) or \
             not isinstance( numBits, int ) or (numBits<0):
            ret = ErrorCode.errInvalidParameter
        elif numBits == 0:
            # Do nothing
            ret = ErrorCode.errOk
        else:
            mask = 1 << (numBits-1)
            for _ in range(numBits):
                level = GPIO.LEVEL_HIGH if (data & mask) else GPIO.LEVEL_LOW
                ret = self.pin[ShiftReg.PIN_IDX_DIN].set( level )
                ret = self.pin[ShiftReg.PIN_IDX_DCLK].set( GPIO.LEVEL_HIGH )
                # wait for ~12 ns
                ret = self.pin[ShiftReg.PIN_IDX_DCLK].set( GPIO.LEVEL_LOW )
                if not ret.isOk():
                    break
                mask >>= 1
            if( ret.isOk() and autoLatch ):
                # Intentionally ignore the return as operation might not be supprted
                self.latch()
        logging.debug('ShiftReg write(data=%02x, numBits=%d), return: %s.',
                      data, numBits, ret)
        return ret
    
    def enable(self, activate=True):
        """Set the ENA line to activate the device as given.
        
        If supported by the driven chip, enables or disables the devices,
        as given by the `activate` parameter.
        If `activate`is `True`, the ENA line is set to the logic `high`
        level. Otherwise, it is set to logic `low`.
        Remember that the physical effect may be inverted by using the
        GPIO's `inverted` configuration parameter. 
        
        The actual semantic effect or meaning depends on the underlying
        device. In some rare implementations, disabling puts the chip
        into a deep sleep mode, which may be advantageous in power-
        critical applications. However, upon recovery from sleep, the
        content of the flip-flops may be lost.
        More frequently, de-activating ENA just de-couples the serial
        communication DIN/DCLK. These implementations preserve the
        content but pause further feeding of the shift register while
        ENA is inactive. This behavior is similar to the chip-select (CS)
        line in SPI communication. 
        
        :param bool activate: Whether to activate (default) or deactivate the device.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if self.pin[ShiftReg.PIN_IDX_ENA]:
            level = GPIO.LEVEL_HIGH if activate else GPIO.LEVEL_LOW
            ret = self.pin[ShiftReg.PIN_IDX_ENA].set( level )
        else:
            ret = ErrorCode.errNotSupported
        logging.debug('ShiftReg ENA set to %s, return: %s.', activate, ret)
        return ret
    
    def disable(self):
        """Disable the device, if supported by the underlying chip.
        
        Also see: :meth:`.enable`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return self.enable(False)

    def clearData(self):
        """Use DCLR to reset the register content.
        
        If supported by the driven chip, clears the contents of the
        flip-flops by cycling DCLR.
        That is, the line is set to logic `high` and reset back to
        logic `low`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if self.pin[ShiftReg.PIN_IDX_DCLR]:
            ret = self.pin[ShiftReg.PIN_IDX_DCLR].set( GPIO.LEVEL_HIGH )
            # wait for ~12 ns
            ret = self.pin[ShiftReg.PIN_IDX_DCLR].set( GPIO.LEVEL_LOW )
        else:
            ret = ErrorCode.errNotSupported
        logging.debug('ShiftReg clearData, return: %s.', ret)
        return ret
    
    def clearLatch(self):
        """Use RCLR to reset the buffer (latch) content.
        
        If supported by the driven chip, clears the contents of the
        buffer by cycling RCLR.
        That is, the line is set to logic `high` and reset back to
        logic `low`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if self.pin[ShiftReg.PIN_IDX_RCLR]:
            ret = self.pin[ShiftReg.PIN_IDX_RCLR].set( GPIO.LEVEL_HIGH )
            # wait for ~12 ns
            ret = self.pin[ShiftReg.PIN_IDX_RCLR].set( GPIO.LEVEL_LOW )
        else:
            ret = ErrorCode.errNotSupported
        logging.debug('ShiftReg clearLatch, return: %s.', ret)
        return ret
    
    def latch(self):
        """Use RCLK to copy the register flip-flop content to the buffer.
        
        If supported by the driven chip, copies the contents of the
        shift register to the buffer by cycling RCLK. 
        That is, the line is set to logic `high` and reset back to
        logic `low`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if self.pin[ShiftReg.PIN_IDX_RCLK]:
            ret = self.pin[ShiftReg.PIN_IDX_RCLK].set( GPIO.LEVEL_HIGH )
            # wait for ~12 ns
            ret = self.pin[ShiftReg.PIN_IDX_RCLK].set( GPIO.LEVEL_LOW )
        else:
            ret = ErrorCode.errNotSupported
        logging.debug('ShiftReg latch, return: %s.', ret)
        return ret
    
    def clear(self):
        """Clear the register and buffer content.
        
        If supported by the underlying hardware, use DCLR and
        RCLR to reset. Otherwise, the implementation may
        write a number of zeroes to the register to
        approximate a similar result.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        flagWrite = False
        # clear register data (flip-flops)
        ret = self.clearData()
        if ret.isOk():
            ret = self.clearLatch()
            if( ret == ErrorCode.errNotSupported ):
                ret = self.latch()
                if( ret == ErrorCode.errNotSupported ):
                    flagWrite = True
                
        elif( ret == ErrorCode.errNotSupported ):
            flagWrite = True
    
        if flagWrite:
            ret = self.write( 0, 32 )	# autoLatch clears the buffer
        return ret
    