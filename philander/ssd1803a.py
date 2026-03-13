"""Display driver module for text LCDs driven by the SSD1803A controller.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["SSD1803A"]

import logging

from .display import TextDisplay
from .serialbus import SerialBusDevice, SerialBusType, SerialBus, SPIMode
from .systypes import ErrorCode


class SSD1803A( TextDisplay ):
    """Driver class for a text LCD driven by SSD1803A.

    Although, this module aims at being generic beyond the controller
    hardware, clearly the DOGM204-A text display by Display Visions was in
    mind when developing this driver. 
    
    The DOGM204 is a 4x20 characters chip-on-glass display module driven by
    the SSD1803A display controller by Solomon Systech. The module can be
    controlled via SPI or I2C. More information on that hardware can be
    found at: https://www.lcd-module.de/fileadmin/pdf/doma/dogm204.pdf

    The SSD1803A supports display sizes of up to 80 characters (max. total).
    Character format may be 5x8 or 6x8.
    Detailed technical information on the controller can be found at:
    https://www.solomon-systech.com/product/SSD1803A
    """

    ADDRESSES_ALLOWED = [0x3C, 0x3D]

    PART_ID     = 0x1A  # Internal part ID, can be used to check communication
    
    REG_CMD     = 0     # Command register, RS=0, D/C#=0
    REG_DATA    = 1     # Data or RAM register, RS=1, D/C#=1
    
    def __init__(self):
        """Initialize the instance with defaults.
        
        Also see: :meth:`.Params_init`, :meth:`.ShiftReg.Params_init`
        """
        super().__init__()
        # Derived attributes
        self._widthChar = 20
        self._heightChar = 4
        # Own attributes
        self._serbusdev = None

    #
    # internal helper
    #

    """Serial communication for the SSD1803A is detailed in the datasheet,
    Rev. 2.0, chapter 7.10. SPI ("Serial Interface", 7.10.2) bit-order
    is interpreted as LSB-first.
    This driver encapsulates serial communication with only a handful
    functions and tries to accommodate both, MSB- and LSB-first
    configurations.
    """
    
    @classmethod
    def _reverseBitOrder(cls, buffer):
        """Reverse bit order for each byte in the given buffer in-place.
        """
        for idx in range( len(buffer) ):
            b = buffer[idx]
            invb = 0
            for _ in range(8):
                invb = (invb << 1) | (b & 0x01)
                b >>= 1
            buffer[idx] = invb
        return None
    
    def _writeCmd(self, data):
        ret = ErrorCode.errOk
        if self._serbusdev.serialBus.type == SerialBusType.SPI:
            # RS=0, R/W=0
            buffer = [0x1F, data & 0x0F, (data & 0xF0)>>4]
            if self._serbusdev.serialBus.spiBitOrder == "MSB":
                self._reverseBitOrder(buffer)
            ret = self._serbusdev.writeBuffer( buffer )
        elif self._serbusdev.serialBus.type == SerialBusType.I2C:
            # D/C#=0, Co=0
            ret = self._serbusdev.writeByteRegister( 0x00, data )
        else:
            logging.debug("SSD1803A._writeCmd: bus type %s unsupported.",
                          self._serbusdev.serialBus.type)
            ret = ErrorCode.errNotImplemented
        return ret

    def _readInfo(self):
        bf, ac, cid, ret = False, 0, 0, ErrorCode.errOk
        if self._serbusdev.serialBus.type == SerialBusType.SPI:
            # RS=0, R/W=1
            # Remember readWordRegister() reads little-endian first.
            if self._serbusdev.serialBus.spiBitOrder == "MSB":
                data, ret = self._serbusdev.readWordRegister( 0xFC )
                data = [ data & 0xFF, (data & 0xFF00)>>4]
                self._reverseBitOrder( data )
                b1 = data[0]
                b2 = data[1]
            else:
                data, ret = self._serbusdev.readWordRegister( 0x3F )
                b1 = data & 0xFF
                b2 = (data & 0xFF00) >> 8
            bf = b1 & 0x80
            ac = b1 & 0x7F
            cid = b2 & 0x7F
        elif self._serbusdev.serialBus.type == SerialBusType.I2C:
            # D/C#=0, Co=0
            data, ret = self._serbusdev.readWordRegister( 0x00 )
            bf = data & 0x80
            ac = data & 0x7F
            cid = (data & 0x7F00) >> 8
        else:
            logging.debug("SSD1803A._readInfo: bus type %s unsupported.",
                          self._serbusdev.serialBus.type)
            ret = ErrorCode.errNotImplemented
        # busy flag, AC = address counter, ID, error
        return bf, ac, cid, ret

    def _writeRAM(self, data):
        ret = ErrorCode.errOk
        if not data:
            ret = ErrorCode.errFewData
        elif self._serbusdev.serialBus.type == SerialBusType.SPI:
            # Start byte, RS=1, R/W=0
            if self._serbusdev.serialBus.spiBitOrder == "MSB":
                ret = self._serbusdev.writeBuffer( [0xFA] )
            else:
                ret = self._serbusdev.writeBuffer( [0x5F] )

            for b in data:
                wbuf = [ (b & 0x0F), (b & 0xF0)>>4 ]
                if self._serbusdev.serialBus.spiBitOrder == "MSB":
                    self._reverseBitOrder( wbuf )
                ret = self._serbusdev.writeBuffer( wbuf )
                if not ret.isOk():
                    break
        elif self._serbusdev.serialBus.type == SerialBusType.I2C:
            # D/C#=1, Co=0
            ret = self._serbusdev.writeBufferRegister( 0x40, data )
        else:
            logging.debug("SSD1803A._writeRAM: bus type %s unsupported.",
                          self._serbusdev.serialBus.type)
            ret = ErrorCode.errNotImplemented
        return ret

    def _readRAM(self, num):
        ret = ErrorCode.errOk
        data = None
        if not isinstance( num, int ) or (num<=0):
            ret = ErrorCode.errInvalidParameter
        elif self._serbusdev.serialBus.type == SerialBusType.SPI:
            # RS=1, R/W=1
            data = [0] * num
            if self._serbusdev.serialBus.spiBitOrder == "MSB":
                ret = self._serbusdev.writeBuffer( [0xFE,] )
            else:
                ret = self._serbusdev.writeBuffer( [0x7F,] )
            for idx in range(num):
                b, ret = self._serbusdev.readBuffer( 1 )
                if ret.isOk():
                    data[idx] = b[0]
                else:
                    break
            if ret.isOk() and (self._serbusdev.serialBus.spiBitOrder == "MSB"):
                self._reverseBitOrder(data)
                
        elif self._serbusdev.serialBus.type == SerialBusType.I2C:
            # D/C#=1, Co
            data, ret = self._serbusdev.readBufferRegister( 0x40, num )
        else:
            logging.debug("SSD1803A._readRAM: bus type %s unsupported.",
                          self._serbusdev.serialBus.type)
            ret = ErrorCode.errNotImplemented
        return data, ret
            
    #
    # Module API
    #

    @classmethod
    def Params_init( cls, paramDict ):
        """Initialize parameters with default values.
        
        Supported key names and their meanings are:

        ===========================    ===============================================================================================
        Key                            Meaning, Range, Default
        ===========================    ===============================================================================================
        display.SerialBusDevice.*      Serial bus device config; See :meth:`.SerialBusDevice.Params_init`.
        display.SerialBus.*            Serial bus configuration; See :meth:`.SerialBus.Params_init`.
        ===========================    ===============================================================================================
        
        :param dict(str, object) paramDict: Dictionary of configuration settings.
        :return: none
        :rtype: None
        """
        prefix = cls.MODULE_PARAM_PREFIX + "."
        serDict = cls._extractParams( paramDict, prefix)
        SerialBus.Params_init(serDict)
        cls._aggregateParams( paramDict, serDict, cls.MODULE_PARAM_PREFIX + "." )
        
        key = cls.MODULE_PARAM_PREFIX + "." + SerialBus.MODULE_PARAM_PREFIX + ".type"
        if key in paramDict:
            if paramDict[key] == SerialBusType.I2C:
                key = cls.MODULE_PARAM_PREFIX + "." + SerialBusDevice.MODULE_PARAM_PREFIX + ".address"
                if key in paramDict:
                    if not paramDict[key] in cls.ADDRESSES_ALLOWED:
                        paramDict[key] = cls.ADDRESSES_ALLOWED[0]
                else:
                    paramDict[key] = cls.ADDRESSES_ALLOWED[0]
                    
        prefix = cls.MODULE_PARAM_PREFIX + "." + SerialBusDevice.MODULE_PARAM_PREFIX
        serDict = cls._extractParams( paramDict, prefix)
        SerialBusDevice.Params_init(serDict)
        cls._aggregateParams( paramDict, serDict, cls.MODULE_PARAM_PREFIX + "." )
        
        super().Params_init(paramDict)
        
        
    def _drvOpen(self, paramDict):
        """Open the low-level driver and prepare it for use.

        :param dict(str, object) paramDict: Configuration parameters.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if self._serbusdev:
            ret = ErrorCode.errResourceConflict
        if ret.isOk():
            prefixMod = self.MODULE_PARAM_PREFIX + "."
            # Extract serial bus parameters
            sparams = self._extractParams( paramDict, prefixMod )
            self._serbusdev = SerialBusDevice()
            ret = self._serbusdev.open(sparams)
            if ret.isOk():
                self._writeCmd( 0x3A ) # DL=8 bit, RE=1; REV=0
                self._writeCmd( 0x09 ) # Display has 4 lines
                self._writeCmd( 0x06 ) # Bottom view
                self._writeCmd( 0x1E ) # Bias
                self._writeCmd( 0x39 ) # RE=0, IS=1
                self._writeCmd( 0x1B ) # Bias
                self._writeCmd( 0x6E ) # Follower control
                self._writeCmd( 0x57 ) # Power control, contrast
                self._writeCmd( 0x72 ) # Contrast low
                self._writeCmd( 0x38 ) # RE=0, IS=0
                self._writeCmd( 0x0F ) # Display on, Cursor on, Blink on
            else:
                logging.debug("SSD1803A couldn't open serial bus device, error: %s.", ret)
                self._serbusdev = None
        logging.debug("SSD1803A.open() returns: %s.", ret)
        return ret
    
    def _drvClose(self):
        """Close this instance and release associated hardware resources.

        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if self._serbusdev:
            ret = self._serbusdev.close()
            self._serbusdev = None
        logging.debug("SSD1803A.close() returns: %s.", ret)
        return ret
    
    def _drvSetRunLevel(self, level):
        """Select the power-saving operation mode.

        :param RunLevel level: The level to switch to.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del level
        return ErrorCode.errNotSupported


    #
    # Display API
    #

    def _drvSetOrientation(self, orientation):
        """Switch to a new display orientation.
        
        :param int orientation: The new orientation to set. One of the ``Display.ORIENTATION_*`` values.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del orientation
        return ErrorCode.errNotSupported
    
    def _drvSetBrightness(self, value):
        """Configure the brightness intensity.
        
        :param int value: The new value to set the brightness to.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del value
        return ErrorCode.errNotSupported

    def _drvSetContrast(self, value):
        """ Adjusts the contrast intensity.
        
        :param int value: The new value to set the contrast to.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del value
        return ErrorCode.errNotSupported
    
    def _drvSetInverse(self, inverseOn=True):
        """ Invert the display.
        
        :param bool inverseOn: `True` for inverse mode, `False` for normal mode.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del inverseOn
        return ErrorCode.errNotSupported

    #
    # TextDisplay API
    #

    def _drvSetCursorMode( self, mode ):
        """Switches the hardware cursor to a specific appearance.
                
        :param mode: The cursor mode to switch to. One of the `CURSOR_MODE_*` values.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del mode
        return ErrorCode.errNotSupported

    def _drvSetCursorSize( self, width, height ):
        """Sets the size of the cursor.
        
        :param width: The width of the cursor. One of the `CURSOR_SIZE_*` values.
        :param height: The height of the cursor. One of the `CURSOR_SIZE_*` values.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del width, height
        return ErrorCode.errNotSupported

    def _drvMoveCursorTo( self, x, y ):
        """Sets the new absolute position of the hardware cursor.

        :param int x: The horizontal cursor position, given in characters.
        :param int y: The vertical cursor position, given in characters.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del x, y
        return ErrorCode.errNotSupported

    def _drvGoTo( self, x, y ):
        """Move the internal ``current position`` to the specified absolute position.
        
        :param int x: The new horizontal position.
        :param int y: The new vertical position.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del x, y
        return ErrorCode.errOk

    def _drvClearScreen( self ):
        """Clear all contents from screen.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errNotImplemented
        
    def _drvScrollV( self, numLines ):
        """Scroll the contents by the given number of lines.
        
        A positive argument makes the content scroll up, so the view port
        moves down, while for a negative argument it's vice versa.
        
        The content scrolled off the screen is not buffered. So, when
        scrolling back, it's the responsibility of the caller to reproduce
        that content, again.
        
        :param int numLines: The number of lines to scroll.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del numLines
        return ErrorCode.errNotSupported

    def _drvGetBuiltinFontNames(self):
        """Retrieve the names of the fonts possibly built-in the display hardware.

        The names of all built-fonts are returned as a list.
        If there is no built-in fonts, an empty list is returned.
        If there is a default font, its name is assumed to be the first
        in the list - at index zero.
        
        :return: The list of font names and an error code indicating either success or the reason of failure.
        :rtype: Tuple( list(str), ErrorCode)
        """
        return [], ErrorCode.errNotSupported

    def _drvGetBuiltinFont(self, name=""):
        """Retrieve the built-in fonts given its name.

        If the name parameter is an empty string, the default font is
        retrieved.
        
        :param str name: The name of the font to retrieve.
        :return: The font and an error code indicating either success or the reason of failure.
        :rtype: Tuple( Font, ErrorCode)
        """
        del name
        return None, ErrorCode.errNotSupported
        
    def _drvSetFont( self, font ):
        """Select a new font as current.
        
        Implementations will also want to update internal attributes
        like _widthChar, _currentX or _cursorX.
        
        :param font: The new character font to set as current.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del font
        return ErrorCode.errNotSupported
    
    def _drvPrintChar( self, code):
        """Print a character at the internal ``current position``.
        
        :param int code: The ASCII code of the character to print.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del code
        return ErrorCode.errNotImplemented

