"""Display driver module for text LCDs driven by the SSD1803A controller.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["SSD1803A"]

import logging

from .display import Display
from .display_text import TextDisplay, ColorSpace, Font
from .serialbus import SerialBusDevice, SerialBusType, SerialBus, SPIMode
from .systypes import ErrorCode, RunLevel

@dataclass
class _Font(Font):
    """A device-specific extension of the base Font data structure.
    
    For fast and memory-efficient handling, it's necessary to add a few
    more attributes, such as the ROM table, double-height- or 6-dot-flag.
    Note that this information may be redundant to the base attributes.
    """
    rom   : int = 8       # Horizontal width of a character in pixel
    bDoubleHeight   : bool = False  # True, if shown in double-height

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
    
    ROM_A       = 0x00
    ROM_B       = 0x04
    ROM_C       = 0x08

    # Font definition    
    FONT_A_5x8 = Font(
        charWidth = 5, charHeight = 8,
        encoding = "ascii",
        colorspace = ColorSpace.GRAY_1,
        firstAscii = 0, numCharacters = 256,
        name = "Western Europe 5x8",
        idxAdr = ROM_A
    )
         
    FONT_B_5x8 = Font(
        charWidth = 5, charHeight = 8,
        encoding = "ascii",
        colorspace = ColorSpace.GRAY_1,
        firstAscii = 0, numCharacters = 256,
        name = "Eastern Europe 5x8",
        idxAdr = ROM_B
    )
         
    FONT_C_5x8 = Font(
        charWidth = 5, charHeight = 8,
        encoding = "ascii",
        colorspace = ColorSpace.GRAY_1,
        firstAscii = 0, numCharacters = 256,
        name = "Extended European 5x8",
        idxAdr = ROM_C
    )
         
    BUILTIN_FONTS = [
        FONT_B_5x8, FONT_A_5x8, FONT_C_5x8
    ]
    
    BUILTIN_FONT_NAMES = [font.name for font in BUILTIN_FONTS]
    
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
    Rev. 2.0, chapter 7.10. SPI ("Serial Interface", 7.10.2).
    Bit-order is interpreted as LSB-first.
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
            logging.error("SSD1803A._writeCmd> Bus type %s unsupported.",
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
            logging.error("SSD1803A._readInfo> Bus type %s unsupported.",
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
            logging.error("SSD1803A._writeRAM> Bus type %s unsupported.",
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
            logging.error("SSD1803A._readRAM> Bus type %s unsupported.",
                          self._serbusdev.serialBus.type)
            ret = ErrorCode.errNotImplemented
        return data, ret


    #
    # Higer level internal helpers
    #    
    def _instrFunctionSet(self, RE=0, IS=0, BE=0, REV=0):
        cmd = 0x30      # DL = 1
        if (self._heightChar==2) or (self._heightChar==4):
            cmd |= 0x08     # N=1 for 2 and 4 rows, 0 otherwise 
        if RE==0:
            if self._font is not None:
                if self._font.charHeight==16:
                    cmd |= 0x04     # DH=1 for double-height font
            # Leave RE=0
            if IS:
                cmd |= 0x01 # Set IS, as requested.
        else:
            if BE:
                cmd |= 0x04 # Set BE, if necessary
            cmd |= 0x02 # RE=1
            if REV:
                cmd |= 0x01 # Set REV, possibly.
        ret = self._writeCmd( cmd )
        return ret
            
    def _instrExtendedFunctionSet(self):
        """ Set FW, B/W and NW.
        """
        cmd = 0x08
        if self._font and (self._font.charWidth==6):
            cmd |= 0x04
        if self._cursorMode==self.CURSOR_MODE_INVERSE:
            cmd |= 0x02
        if self._heightChar > 2:
            cmd |= 0x01     # NW=1 for 3 and 4 rows, 0 otherwise 
        ret = self._writeCmd( cmd )
        return ret
    
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
        SerialBusDevice.Params_init(serDict)
        cls._aggregateParams( paramDict, serDict, prefix )
        
        key = cls.MODULE_PARAM_PREFIX + "." + SerialBus.MODULE_PARAM_PREFIX + ".type"
        if key in paramDict:
            if paramDict[key] == SerialBusType.I2C:
                key = cls.MODULE_PARAM_PREFIX + "." + SerialBusDevice.MODULE_PARAM_PREFIX + ".address"
                if key in paramDict:
                    if not paramDict[key] in cls.ADDRESSES_ALLOWED:
                        paramDict[key] = cls.ADDRESSES_ALLOWED[0]
                else:
                    paramDict[key] = cls.ADDRESSES_ALLOWED[0]
                    
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
                # Fundamental settings
                self._instrFunctionSet(RE=1)    # DL, RE
                self._instrExtendedFunctionSet()    # FW, B/W, NW
                self._drvSetOrientation( Display.ORIENTATION_NATURAL )
                # Recommended ramp-up procedure
                ret = self._drvClearScreen()
                self._instrFunctionSet(RE=1, IS=1)
                self._writeCmd( 0x13 ) # Reset Bias / OSC Frequency
                self._writeCmd( 0x7F ) # Maximum contrast
                self._writeCmd( 0x5C ) # ICON on, Booster reg. on
                self._writeCmd( 0x6E ) # Follower control
                self._instrFunctionSet(RE=0)
                self._writeCmd( 0x0F ) # Display on, Cursor on, Blink on
            else:
                logging.error("SSD1803A._drvOpen> Couldn't open serial bus device, error: %s.", ret)
                self._serbusdev = None
        logging.debug("SSD1803A._drvOpen> Return: %s.", ret)
        return ret
    
    def _drvClose(self):
        """Close this instance and release associated hardware resources.

        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        err = self._drvClearScreen()
        ret =  err if ret == ErrorCode.isOk() else ret
        err = self._drvSetRunLevel( RunLevel.shutdown )
        ret =  err if ret == ErrorCode.isOk() else ret
        if self._serbusdev:
            err = self._serbusdev.close()
            self._serbusdev = None
        ret =  err if ret == ErrorCode.isOk() else ret
        logging.debug("SSD1803A._drvClose> Return: %s.", ret)
        return ret
    
    def _drvSetRunLevel(self, level):
        """Select the power-saving operation mode.

        :param RunLevel level: The level to switch to.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if level <= RunLevel.idle:
            ret = self._instrFunctionSet(RE=1)
            self._writeCmd( 0x02 ) # Power down PD=0
            ret = self._instrFunctionSet(RE=0)
            self._writeCmd( 0x0F ) # Display on, Cursor on, Blink on
        elif level <= RunLevel.nap:
            ret = self._instrFunctionSet(RE=1)
            self._writeCmd( 0x02 ) # Power down PD=0
            ret = self._instrFunctionSet(RE=0)
            self._writeCmd( 0x08 ) # Display off, Cursor off, Blink off
        else:
            ret = self._instrFunctionSet(RE=0)
            self._writeCmd( 0x08 ) # Display off, Cursor off, Blink off
            ret = self._instrFunctionSet(RE=1)
            self._writeCmd( 0x03 ) # Power down PD=1
        return ret


    #
    # Display API
    #

    def _drvSetOrientation(self, orientation):
        """Switch to a new display orientation.
        
        :param int orientation: The new orientation to set. One of the ``Display.ORIENTATION_*`` values.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if orientation == Display.ORIENTATION_NATURAL:
            ret = self._instrFunctionSet(RE=1)
            ret = self._writeCmd( 0x06 ) # Bottom view
        elif orientation == Display.ORIENTATION_ROTATE_180:
            ret = self._instrFunctionSet(RE=1)
            ret = self._writeCmd( 0x05 ) # Top view
        else:
            logging.debug("SSD1803A._drvSetOrientation> Invalid orientation: %s.",
                          orientation)
            ret = ErrorCode.errNotSupported
        return ret
    
    def _drvSetBrightness(self, value):
        """Configure the brightness intensity.
        
        Note that the LED backlight cannot be controlled by the display
        driver chip. As this this external circuitry, the brightness must
        be adjusted by either a potentiometer or PWM.
        
        :param int value: The new value to set the brightness to.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        logging.debug("SSD1803A._drvSetBrightness> Not supported. value=%d",
                      value)
        return ErrorCode.errNotSupported

    def _drvSetContrast(self, value):
        """ Adjusts the contrast intensity.
        
        :param int value: The new value to set the contrast to.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        # Scale percentage 0...100 -> 0...63 6 bit number C5...C0
        contrast = int( value / 101 * 64 ) & 0x3F
        # Upper C5 and C4 go to power control as DB1 and DB0
        ret = self._instrFunctionSet(RE=0, IS=1)
        self._writeCmd( 0x5C | (contrast >> 4)  ) # Ion=1, Bon=1, DB1=C5, DB0=C4
        ret = self._writeCmd( 0x70 | (contrast & 0x0F)  ) # Contrast set, DB3...DB0=C3...C0
        logging.debug("SSD1803A._drvSetContrast> value=%d, return: %s",
                      value, ret)
        return ret
    
    def _drvSetInverse(self, inverseOn=True):
        """ Invert the display.
        
        :param bool inverseOn: `True` for inverse mode, `False` for normal mode.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = self._instrFunctionSet(RE=1, BE=1, REV=inverseOn)
        logging.debug("SSD1803A._drvSetInverse> value=%d, return: %s",
                      inverseOn, ret)
        return ret

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
        # According to the data sheet, chapter 7.2, the range (!)  of the
        # address counter (AC) depends on the number of rows as follows:
        #   1 line : 0x00 - 0x4F
        #   2 lines: 0x00 - 0x27, 0x40 - 0x67
        #   3 lines: 0x00 - 0x13, 0x20 - 0x33, 0x40 - 0x53
        #   4 lines: 0x00 - 0x13, 0x20 - 0x33, 0x40 - 0x53, 0x60 - 0x73
        # Actual addressing also depends on the character width (5/6 dots).
        if y==0:
            ac = 0x00
        elif y==1:
            ac = 0x20
        elif y==2:
            ac = 0x40
        else:
            ac = 0x60
        ac += x
        cmd = 0x80 | ac
        self._instrFunctionSet(RE=0)
        ret = self._writeCmd( cmd )  # set AC
        logging.debug("SSD1803A._drvGoTo> x=%d y=%d, new ac=0x%02x return: %s",
                      x, y, ac, ret)
        return ret

    def _drvClearScreen( self ):
        """Clear all contents from screen.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = self._writeCmd( 0x01 ) # Clear Display
        return ret
        
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
        return SSD1803A.BUILTIN_FONT_NAMES, ErrorCode.errOk

    def _drvGetBuiltinFont(self, name=""):
        """Retrieve the built-in fonts given its name.

        If the name parameter is an empty string, the default font is
        retrieved.
        
        :param str name: The name of the font to retrieve.
        :return: The font and an error code indicating either success or the reason of failure.
        :rtype: Tuple( Font, ErrorCode)
        """
        ret = None
        err = ErrorCode.errOk
        try:
            idx = SSD1803A.BUILTIN_FONT_NAMES.index( name )
            ret = SSD1803A.BUILTIN_FONTS[idx]
            err = ErrorCode.errOk
        except ValueError:
            ret = None
            err = ErrorCode.errInvalidParameter
        return ret, err
        
    def _drvSetFont( self, font ):
        """Select a new font as current.
        
        Implementations will also want to update internal attributes
        like _widthChar, _currentX or _cursorX.
        
        :param font: The new character font to set as current.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        self._instrFunctionSet( RE=1 )
        self._writeCmd( 0x72 ) # ROM selection
        self._writeRAM( font.idxAdr )
        ret = self._instrExtendedFunctionSet()
        return ret
    
    def _drvPrintChar( self, code):
        """Print a character at the internal ``current position``.
        
        :param int code: The ASCII code of the character to print.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = self._writeRAM( code )
        return ret

