"""Display module to support different kinds of visible user interface.

This is a convergence layer to provide unified access to displays,
screens and other visible user interfaces beyond LEDs.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Display", 
           "ColorSpace", "Font", "TextDisplay",
           "Color", "GrayScale1", "GrayScale2", "GrayScale4", "GrayScale8", 
           "Image", "GraphicDisplay", ]

from abc import ABC, abstractmethod

from .module import Module
from .penum import Enum, unique, auto, idiotypic, dataclass
from .systypes import ErrorCode, RunLevel

#
# The order of classes in this module follows the class hierarchy of
# the main classes: Display - TextDisplay - GraphicDisplay
# Helper classes are given near the main classes referencing them.
#


###
#
# Display
#
###
 
class Display(ABC, Module):
    """Generic interface for a visual user interface (display).
    
    This is an abstract base class (ABC), that cannot be instantiated
    directly, but must be derived before making use of it.
     
    The design of this class aims at being agnostic to the display
    technology. Derivatives of this class may be more specific to
    e.g. just symbols displays, text-only displays or graphic displays.
    
    However, a display may tell about its nature, shape and capabilities.
    Moreover, it supports the concept of orientation and may adjust
    back light, contrast and inverse presentation. 
    """

    MODULE_PARAM_PREFIX = "display"

    # Mnemonics to describe the capabilities of the display.
    CAPABILITIES_UNKNOWN     = 0    # Capabilities unknown or not set.
    CAPABILITIES_TEXT_ONLY   = 1    # Text only, character size is likely fixed
    CAPABILITIES_GRAPHIC     = 2    # Full graphic display 

    # Mnemonics to describe intensities as percentages.
    # This is meant for brightness and contrast settings.
    INTENSITY_OFF       = 0
    INTENSITY_LOW       = 25
    INTENSITY_MEDIUM    = 50
    INTENSITY_HIGH      = 75
    INTENSITY_FULL      = 100
    
    # Display orientation. This is meant to compensate e.g. restrictions
    # enforced by the physical assembly. 
    # Note that rotation is applied before flipping!

    # Normal, straight, default; Top-left advancing right
    ORIENTATION_NATURAL = 0x00
    # Vertical flip; Top-right advancing  left
    ORIENTATION_FLIP_V  = 0x01
    # Horizontal flip; Bottom-left advancing  right
    ORIENTATION_FLIP_H = 0x02
    # Twofold flip; Bottom-right advancing left
    ORIENTATION_FLIP_HV = (ORIENTATION_FLIP_H | ORIENTATION_FLIP_V)
    # Clock-wise rotation by 90; Top-right advancing down
    ORIENTATION_ROTATE_CW = 0x04
    # Clock-wise rotation, then V-flip; Top-left advancing down
    ORIENTATION_ROTATE_CW_FLIP_V = (ORIENTATION_ROTATE_CW | ORIENTATION_FLIP_V)
    # Clock-wise rotation, then H-flip; Bottom-right advancing up
    ORIENTATION_ROTATE_CW_FLIP_H = (ORIENTATION_ROTATE_CW | ORIENTATION_FLIP_H)
    # Clock-wise rotation plus twofold flip; Bottom-left advancing up
    ORIENTATION_ROTATE_CW_FLIP_HV= (ORIENTATION_ROTATE_CW | ORIENTATION_FLIP_H | ORIENTATION_FLIP_V)
    # Synonyms
    # Rotation by 180°; Bottom-right advancing left
    ORIENTATION_ROTATE_180 = ORIENTATION_FLIP_HV
    # Counterclock-wise rotation; Bottom-left advancing up
    ORIENTATION_ROTATE_CCW = ORIENTATION_ROTATE_CW_FLIP_HV

    # Mnemonics to describe the shape of the display.
    SHAPE_RECTANGLE   = 0    # Rectangle
    SHAPE_CIRCLE      = 1    # Circle

    def __init__(self):
        # read-only attributes to describe the physical properties and
        # capabilities of this display
        self._capabilities = Display.CAPABILITIES_UNKNOWN    # Type of display
        self._orientation = Display.ORIENTATION_NATURAL
        self._shape = Display.SHAPE_RECTANGLE   # Geometry of the display
        self._brightness = Display.INTENSITY_HIGH
        self._contrast = Display.INTENSITY_HIGH
        
    #############################
    # Module API
    #############################

    #
    # Non-public, internal driver interface
    # Wherever possible, method signatures are oriented on their
    # public counterparts.
    #

    @abstractmethod
    def _drvOpen(self, paramDict):
        """Open the low-level driver and prepare it for use.

        :param dict(str, object) paramDict: Configuration parameters.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        pass
    
    @abstractmethod
    def _drvClose(self):
        """Close this instance and release associated hardware resources.

        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        pass
    
    def _drvSetRunLevel(self, level):
        """Select the power-saving operation mode.

        :param RunLevel level: The level to switch to.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del level
        return ErrorCode.errNotSupported

    #
    # Public API
    #


    @classmethod
    def Params_init( cls, paramDict ):
        """Initialize parameters with default values.
        
        Supported key names and their meanings are:

        ===========================    ===============================================================================================
        Key                            Meaning, Range, Default
        ===========================    ===============================================================================================
        display.brightness             Brightness of screen or backlight as a percentage; 0...100; :attr:`Display.INTENSITY_HIGH`
        display.contrast               Screen contrast setting as a percentage; 0...100; :attr:`Display.INTENSITY_HIGH`
        display.orientation            Orientation of the screen; :attr:`Display.ORIENTATION_NATURAL`
        ===========================    ===============================================================================================
        
        :param dict(str, object) paramDict: Dictionary of configuration settings.
        :return: none
        :rtype: None
        """
        defaults = {
            "brightness":   Display.INTENSITY_HIGH,
            "contrast":     Display.INTENSITY_HIGH,
            "orientation":  Display.ORIENTATION_NATURAL,
        }
        cls._aggregateParams( paramDict, defaults, cls.MODULE_PARAM_PREFIX+"." )
        return None

    def open(self, paramDict):
        self.Params_init(paramDict)
        ret = self._drvOpen(paramDict)
        if ret.isOk():
            ret = self.setRunLevel( RunLevel.active )
            if ret.isLight():
                key = self.MODULE_PARAM_PREFIX + ".orientation"
                ret = self.setOrientation( paramDict[key] )
            if ret.isLight():
                key = self.MODULE_PARAM_PREFIX + ".brightness"
                ret = self.setBrightness( paramDict[key] )
            if ret.isLight():
                key = self.MODULE_PARAM_PREFIX + ".contrast"
                ret = self.setContrast( paramDict[key] )
            if ret.isLight():
                ret = ErrorCode.errOk
        return ret

    def close(self):
        ret = self.setRunLevel( RunLevel.sleep )
        err = self._drvClose()
        if not err.isOk():
            ret = err
        return ret

    def setRunLevel(self, level):
        ret = ErrorCode.errOk

        if level == RunLevel.active:
            intensity = Display.INTENSITY_HIGH
        elif level == RunLevel.idle:
            intensity = Display.INTENSITY_MEDIUM
        elif level < RunLevel.sleep:
            intensity = Display.INTENSITY_LOW
        else:
            intensity = Display.INTENSITY_OFF

        if level < RunLevel.sleep:
            ret = self._drvSetRunLevel(level)
            if ret.isLight():
                ret = self.setBrightness( intensity )
            if ret.isLight():
                ret = self.setContrast( intensity )
        else:
            ret = self.setBrightness( intensity )
            if ret.isLight():
                ret = self.setContrast( intensity )
            if ret.isLight():
                ret = self._drvSetRunLevel(level)
        if ret.isLight():
            ret = ErrorCode.errOk
        return ret

    #############################
    # Specific API
    #############################

    #
    # Non-public, internal driver interface
    # Wherever possible, method signatures are oriented on their
    # public counterparts.
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
    # Public API
    #
    
    @property    
    def capabilities(self):
        """Retrieve the capabilities of the underlying display hardware."""
        return self._capabilities
    
    @property    
    def orientation(self):
        """Retrieve the current display orientation."""
        return self._orientation

    def setOrientation(self, orientation):
        """Set the new display orientation.
        
        This is to maximize mechanical flexibility and to easily
        allow for flipping/rotating the content.

        :param int orientation: The new orientation to set. One of the ``Display.ORIENTATION_*`` values.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = self._drvSetOrientation(orientation)
        if ret.isOk():
            self._orientation = orientation
        return ret

    @property    
    def shape(self):
        """Retrieve the shape of the display."""
        return self._shape

    def setBrightness(self, value):
        """Configure the brightness or back light intensity.
        
        A bright light significantly improves the readability of the
        display content, but, at the same time, drastically increases
        electrical power consumption of the system. The situation-aware
        adjustment of the back light level could provide a chance to
        balance between these two contradicting requirements.
        
        The new brightness value is given as an integer percentage in
        the range of zero (0) to hundred (100), inclusively.
        Setting it to `0[%]` will effectively switch off the light.
        Giving a value of `100[%]` will put the light always on resulting
        in the brightest-possible illumination.
        Dimming the light corresponding to values in between might be
        implemented e.g. through pulse-width modulation (PWM).

        :param int value: The new value to set the brightness to.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if not isinstance( value, int) or \
            (value < self.INTENSITY_OFF) or (value > self.INTENSITY_FULL):
            ret = ErrorCode.errInvalidParameter
        else:
            ret = self._drvSetBrightness(value)
        return ret

    def setContrast(self, value):
        """ Adjusts the contrast intensity.
        
        Contrast is the difference between the brightness levels of
        bright white and full black pixels.
        For LCD due to technical reasons, the brightness of white pixels
        is not affected by this function. Instead, the saturation of
        black pixels can be faded from full black into faint grey. Note
        that low contrast will nominally reduce drawn current and thus,
        marginally save some power. At the same time, it will severely
        degrade reading comfort.
        The caller should deploy this function in conjunction with
        back light adjustment and power saving modes to balance
        readability with power consumption.
        
        The new contrast level is given as an integer percentage in the
        range of zero (0) to hundred (100), inclusively. A value
        of zero will obliterate any contrast and make black and white
        pixels appear the same resulting in nothing can be seen on an
        LCD. The value of `100` will impose the maximum contrast making
        black pixels clearly differ from white pixels.

        :param int value: The new value to set the contrast to.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if not isinstance( value, int) or \
            (value < self.INTENSITY_OFF) or (value > self.INTENSITY_FULL):
            ret = ErrorCode.errInvalidParameter
        else:
            ret = self._drvSetContrast(value)
        return ret
    
    def setInverse(self, inverseOn=True):
        """ Invert the display.
        
        Make white and light pixels appear black and gray, respectivley
        and vice-versa.
        
        :param bool inverseOn: `True` for inverse mode, `False` for normal mode.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = self._drvSetInverse(inverseOn)
        return ret


###
#
# TextDisplay
#
###

@unique
@idiotypic
class ColorSpace(Enum):
    """Mnemonics to define color / gray scale resolution.
    """
    # Mnemonics for the color space.
    GRAY_1  = 1      # 1 bit black or white, no nuances in color
    GRAY_2  = 2      # 2 bit gray scale
    GRAY_4  = 3      # 4 bit gray scale
    GRAY_8  = 4      # 8 bit gray scale, one byte per pixel
    PALETTE_4 = 10   # 4 bit color palette
    PALETTE_8 = 11   # 8 bit color palette
    RGB_16  = 20     # 16 bit RGB
    RGB_24  = 21     # 24 bit RGB, true color
    RGB_32  = 22     # 32 bit RGB true color 


@dataclass
class Font():
    """The font data structure.
    
    Font data mainly contain some meta information plus the pixel data
    for each ASCII character. A font can omit non-printable characters
    to save memory. A font could extend to non-ASCII characters, however.
    """
    charWidth   : int = 8       # Horizontal width of a character in pixel
    charHeight  : int = 8       # Vertical height of each character in pixel
    encoding    : str = "ascii" # One of the Python standard encodings
    colorspace  : ColorSpace = ColorSpace.GRAY_1
    firstAscii: int = 32        # Offset into the ASCII-table
    numCharacters: int = 96     # Number of characters
    name    : str = ""          # Name of the font
    idxAdr  : int = 0           # Index or address for built-in/hardware fonts
    letter  : bytes = None      # letter data, device-specific

class TextDisplay(Display):
    """Abstract API class for displays capable of showing text.
    
    Implementations of this interface are expected to drive a specific
    hardware, which is assumed to be a text-only display.
    However, this interface may also be implemented for graphical
    displays being able to draw text.
    
    Text displays may support one or more fonts. They may have a hardware
    cursor and adjust its mode and size. Moreover, they offer to define
    a certain screen-full policy which may involve scrolling.
    
    Text displays are not aware of colors.
    Further on, logic operations of character font data with the
    background are not supported. So, there is nothing comparable to the
    ink concept introduced for :class:`GraphicDisplay`. 
    """

    # Mnemonics for the screen (hardware-) cursor appearance.
    CURSOR_MODE_OFF         = 0    # Off, cursor does not show
    CURSOR_MODE_WHITE       = 1    # Static white cursor, hiding content
    CURSOR_MODE_BLACK       = 2    # Static black cursor, hiding content
    CURSOR_MODE_INVERSE     = 3    # Revert content, no blink
    CURSOR_MODE_BLINK_WHITE = 4    # Blinking content<->white
    CURSOR_MODE_BLINK_BLACK = 5    # Blinking content<->black
    CURSOR_MODE_BLINK_INVERSE = 6  # Blinking content normal<->inverse

    # Mnemonics for the cursor size, applicable to both, width and height
    CURSOR_SIZE_SLIM   = 1      # Just one pixel or line
    CURSOR_SIZE_QUARTER= 2      # A quarter of a character width/height
    CURSOR_SIZE_HALF   = 3      # Half a character
    CURSOR_SIZE_FULL   = 4      # Full character
    
    # The screen-full-policy to apply in character output.
    # This policy is applied each time when reaching the lower-right end
    # of the screen.
    SCREEN_POLICY_STOP    = 0    # Simply stop, do nothing
    SCREEN_POLICY_CLEAR   = 1    # Clear screen and start over at upper left
    SCREEN_POLICY_INVERT  = 2    # Start at left top, inverting
    SCREEN_POLICY_SCROLL  = 3    # Scroll up one line or more and go on

    # Scroll direction to indicate, how the display content is to be moved.
    # Note that this refers to, how the content (or paper) moves and not,
    # how the view port/window changes!
    SCROLL_DIR_LEFT    = 1   # Content moves left
    SCROLL_DIR_RIGHT   = 2   # Content moves right
    SCROLL_DIR_UP      = 3   # Content moves up.
    SCROLL_DIR_DOWN    = 4   # Content moves down.

    DEFAULT_TAB_SIZE    = 4  # tab size in characters
    
    def __init__(self):
        super().__init__()
        # Derived attributes
        self._capabilities = Display.CAPABILITIES_TEXT_ONLY
        # Own attributes
        self._cursorWidth = TextDisplay.CURSOR_SIZE_FULL
        self._cursorHeight = TextDisplay.CURSOR_SIZE_QUARTER
        self._cursorX = 0  # hardware cursor position, x component
        self._cursorY = 0  # hardware cursor position, y component
        self._currentX = 0  # internal current position, x component
        self._currentY = 0  # internal current position, y component
        self._screenPolicy = TextDisplay.SCREEN_POLICY_STOP
        self._tabsize = TextDisplay.DEFAULT_TAB_SIZE     # Size of a tab
        self._font = None
        self._widthChar  = 0    # Horizontal screen width in characters
        self._heightChar = 0    # Vertical screen height in characters

        
    #############################
    # Module API
    #############################

    #
    # Non-public, internal driver interface
    # Wherever possible, method signatures are oriented on their
    # public counterparts.
    #

    #
    # Public API
    #

    @classmethod
    def Params_init( cls, paramDict ):
        """Initialize parameters with default values.
        
        Supported key names and their meanings are:

        ===========================    ===============================================================================================
        Key                            Meaning, Range, Default
        ===========================    ===============================================================================================
        display.screenpolicy           Screen-full policy to apply; :attr:`TextDisplay.SCREEN_POLICY_STOP`
        display.tabsize                Number of spaces for a tab; positive integer; 4
        ===========================    ===============================================================================================
        
        :param dict(str, object) paramDict: Dictionary of configuration settings.
        :return: none
        :rtype: None
        """
        super().Params_init(paramDict)
        defaults = {
            "display.screenpolicy": TextDisplay.SCREEN_POLICY_STOP,
            "display.tabsize": TextDisplay.DEFAULT_TAB_SIZE,
        }
        cls._aggregateParams( paramDict, defaults, cls.MODULE_PARAM_PREFIX )
        return None

    def open(self, paramDict):
        ret = super().open( paramDict )
        if ret.isOk():
            ret = self.setCursorMode( TextDisplay.CURSOR_MODE_OFF )
            if ret.isLight():
                ret = self.setCursorSize(TextDisplay.CURSOR_SIZE_FULL, TextDisplay.CURSOR_SIZE_QUARTER)
            if ret.isLight():
                ret = self.moveCursorToChar(0, 0)
            if ret.isLight():
                ret = self.clearScreen()
            if ret.isLight():
                ret = self.goToChar(0, 0)
            if ret.isOk():
                key = self.MODULE_PARAM_PREFIX + ".screenpolicy"
                ret = self.setScreenFullPolicy( paramDict[key] )
            if ret.isOk():
                font, ret = self.getFont()
                if ret.isOk():
                    ret = self.setFont(font)
            if ret.isLight():
                ret = ErrorCode.errOk
        return ret
    
    
    #############################
    # Specific API
    #############################

    #
    # Non-public, internal driver interface
    # Wherever possible, method signatures are oriented on their
    # public counterparts.
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
        ret = self.drawBox(self._widthPixel, self._heightPixel,
                           self._backgroundColor)
        return ret
        
    def _drvScrolLV( self, numLines ):
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
    
    @abstractmethod
    def _drvPrintChar( self, code):
        """Print a character at the internal ``current position``.
        
        :param int code: The ASCII code of the character to print.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del code
        return ErrorCode.errNotImplemented

    #
    # Non-public helper methods
    #

    def _updateLineFeed(self):
        ret = ErrorCode.errOk
    
        # Try line feed
        iTemp = self._currentY + 1
        if (iTemp + 1 <= self._heightChar):
            ret = self.goToChar( 0, iTemp)
            # Possibly clear the line with (inverted?) background color.
        else:
            # reached the end of screen: apply the screen full policy
            if (self._screenPolicy == self.SCREEN_POLICY_CLEAR):
                ret = self.clearScreen()
            if (self._screenPolicy == self.SCREEN_POLICY_INVERT):
                self.goToChar(0, 0)
                # Do something special
            if (self._screenPolicy == self.SCREEN_POLICY_SCROLL):
                ret = self._drvScrolLV(1)
                # Go to the beginning of the row that should be replaced
                self.goToChar(0, self._currentY)
            else:
                ret = ErrorCode.errInadequate
        return ret
    
    def _updateNextChar(self):
        ret = ErrorCode.errOk
        self._currentX += 1
        if( self._currentX + 1 <= self._widthChar ):
            ret = self.goToChar( self._currentX, self._currentY )
        else:
            ret = self._updateLineFeed()
        return ret

    #
    # Public API
    #

    @property    
    def widthChar(self):
        """Retrieve the display width, measured in characters."""
        return self._widthChar
    
    @property    
    def heightChar(self):
        """Retrieve the display height in characters."""
        return self._heightChar
    
    def setCursorMode( self, mode ):
        """Switches the hardware cursor to a specific appearance.
        
        The cursor shape is mostly rectangular and usually it cannot be
        modified. The size and position of the cursor can be manipulated
        by the :meth:`setCursorSize`, :meth:`CursorGoto` and similar
        functions. Like with all the content displayed, the cursor is
        subject to the `inverse` feature controlled by :meth:'setInverse`.

        The given :attr:`mode` parameter defines, how the cursor should
        behave and look like. The specific appearance is detailed in the
        following table.
        
        =============   ====================================================
        Mode            Appearance
        =============   ====================================================
        OFF             Switches the cursor off.
                        The cursor does not show up.
        WHITE           The cursor is static white. This cursor cannot
                        be seen when between spaces.
        BLACK           A constantly black cursor.
        INVERSE         Cursor reverts, but does not blink.
                        This mode gives a steady cursor field inverting
                        the content beneath, that is, black pixels become
                        white and vice-versa. This cursor is always visible.
        BLINK_WHITE     The area under the cursor will blink white.
                        It shows the original content and an all-white area
                        alternating. Note that this cursor is not visible
                        over a white field, such as a space character.
        BLINK_BLACK     The cursor blinks black. The corresponding area
                        shows the original content and an all-black field
                        alternating. This cursor is visible for the
                        majority of meaningful characters.
        BLINK_INVERSE   The cursor blinks reverted. It shows the original
                        content and the reverted content alternating.
                        This cursor is always visible.
        =============   ====================================================

        Also see: :meth:`setCursorSizePosition`
        
        :param mode: The cursor mode to switch to. One of the `CURSOR_MODE_*` values.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = self._drvSetCursorMode(mode)
        return ret

    def setCursorSize( self, width, height ):
        """Sets the size of the cursor.
        
        The cursor shape is always rectangular.
        Depending on the underlying hardware, vertical or horizontal
        bars can be used as cursor by setting the `width` or the
        `height` parameter accordingly.
        
        Remember to set an appropriate cursor mode by calling
        :meth:`setCursorMode` to control thecursor's visibility.
        
        If the given position or size are invalid, nothing happens
        and the function returns an appropriate error code.
        
        :param width: The width of the cursor. One of the `CURSOR_SIZE_*` values.
        :param height: The height of the cursor. One of the `CURSOR_SIZE_*` values.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if (width < TextDisplay.CURSOR_SIZE_SLIM) or    \
            (width > TextDisplay.CURSOR_SIZE_FULL) or   \
            (height < TextDisplay.CURSOR_SIZE_SLIM) or  \
            (height > TextDisplay.CURSOR_SIZE_FULL):
            ret = ErrorCode.errSpecRange
        else:
            ret = self._drvSetCursorSize(width, height)
            if ret.isOk():
                self._cursorWidth = width
                self._cursorHeight = height
        return ret
    
    def moveCursorToChar( self, x, y ):
        """Sets the new absolute position of the hardware cursor.

        Moves the visible hardware cursor to the position given in 
        characters.
        The cursor position is independent of the internal
        ``current position``.
        The latter one defines, where the next characters is drawn
        and is controlled by :meth:`goTo`.
        The cursor position just defines, where the hardware cursor
        appears.
        Also, this function does not make the cursor appear or
        disappear. Instead, this can be controlled by calling the
        :meth:`setCursorMode` function.
        If the given position is out of range, nothing changes and
        an error is returned.
        
        Also see: :meth:`moveCursorByChar`.
        
        :param int x: The horizontal cursor position, given in characters.
        :param int y: The vertical cursor position, given in characters.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if (x < 0) or (x > self._widthChar) or  \
            (y < 0) or (y > self._heightChar):
            ret = ErrorCode.errSpecRange
        else:
            ret = self._drvMoveCursorTo(x, y)
            if ret.isOk():
                self._cursorX = x
                self._cursorY = y
        return ret

    def moveCursorByChar( self, x, y ):
        """Move the hardware cursor *by* the given number of characters.

        Actual movement may depend on the current font selected,
        as this determines the character width and height.
        The cursor's new absolute position will be its current
        position incremented by the arguments given.

        Also see: :meth:`moveCursorToChar`

        :param int x: The number of characters to move horizontally.
        :param int y: The number of character lines to move vertically.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        absX = x + self._cursorX
        absY = y + self._cursorY
        if (absX < 0) or (absX > self._widthChar) or   \
            (absY < 0) or (absY > self._heightChar):
            ret = ErrorCode.errSpecRange
        else:
            ret = self.moveCursorToChar( absX, absY )
        return ret

    def goToChar( self, x, y ):
        """Move the internal ``current position`` to the specified absolute position.
        
        The ``current position`` is, where the next character will
        be printed, independent of where the hardware cursor is.
        If the given position is out of range, nothing changes and
        an error is returned.
        
        Also see: :meth:`moveCursorByChar`.
        
        :param int x: The new horizontal position, given in characters.
        :param int y: The new vertical position, given in characters.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if (x < 0) or (x > self._widthChar) or  \
            (y < 0) or (y > self._heightChar):
            ret = ErrorCode.errSpecRange
        else:
            ret = self._drvGoTo(x, y)
            if ret.isOk():
                self._currentX = x
                self._currentY = y
        return ret

    def goByChar( self, x, y ):
        """Move the internal ``current position`` *by* the given number of characters.
        
        Remember that this internal ``current position`` is not visible.
        It is conceptually different from the hardware cursor, which is
        controlled by the :meth:´moveCursorToChar` and similar functions.
        
        Note that positive arguments will make the current position move
        right/down while negatives will move left/up.
        
        If the movement would exceed the display limits, nothing is
        changed and the function returns an error code.
        
        :param int x: The number of characters to move horizontally. 
        :param int y: The number of characters (lines) to move vertically.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        absX = x + self._currentX
        absY = y + self._currentY
        if (absX < 0) or (absX > self._widthChar) or   \
            (absY < 0) or (absY > self._heightChar):
            ret = ErrorCode.errSpecRange
        else:
            ret = self.goToChar( absX, absY )
        return ret

    def clearScreen(self):
        """Clear the screen, so there is no content visible, anymore.
        
        Reset all character fields and by this, erase the current display
        content.
        Afterwards, place the internal ``current position`` to the upper
        left corner position at ``(0,0)``. So, subsequent printing of
        characters will start there.
        Finally, reset the current background color to white, which is
        only important for the case that the screen-full policy is set to
        ``INVERT``.
        
        Note that the position of the (visible) hardware cursor is not
        affected. If the screen should be blanked without erasing its
        content, consider throttling the contrast or try one of the run
        levels.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        # Reset the displaying mode to normal (without offset)
        # as it could have been modified because of the screen full policy
        # set to SCROLL
        ret = self._drvScrollV( 0 )
        if ret.isLight():
            ret = self.goToChar( 0, 0 )
        if ret.isLight():
            ret = self._drvClearScreen()
        return ret
    
    def getFont(self, name=""):
        """Retrieve a font, given its name.

        If the name parameter is an empty string, the default font is
        retrieved.
        
        :param str name: The name of the font to retrieve.
        :return: The font and an error code indicating either success or the reason of failure.
        :rtype: Tuple( Font, ErrorCode)
        """
        font, ret = self._drvGetBuiltinFont(name)
        return font, ret
        
    def setFont( self, font ):
        """Select a new font as current.
        
        The new font is in effect instantly after returning from this
        function. The current drawing position may change to align with
        the new character size.
        
        :param font: The new character font to set as current.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        if not isinstance( font, Font ):
            ret = ErrorCode.errInvalidParameter
        else:
            ret = self._drvSetFont(font)
        if ret.isOk():
            self._font = font
        return ret
    
    def setScreenFullPolicy( self, policy ):
        """Configure the screen-full policy.
        
        This policy describes, what should happen if, while writing text,
        the internal ``current position`` reaches the end of screen (EOS),
        i.e. the bottom-right corner of the screen, and no more character
        can be placed.
        
        Depending on :attr:`policy` argument, printing characters
        behaves as follows.
        
        ========    =========================================
        Policy      Behavior
        ========    =========================================
        STOP        Simply does nothing. Does not update the internal
                    drawing cursor. So, further attempts of drawing
                    characters will address invalid screen area and thus,
                    return with an error code. The handling of reaching
                    the end of screen is solely put into the
                    responsibility of the application.
                    To support the application in this mode, printing the
                    last character at the bottom right corner returns an
                    :attr:``ErrorCode.ErrSpecRange`` indication,
                    upon which the caller should take appropriate action.
        CLEAR       After reaching the end, the screen is immediately
                    cleared, positioning the internal ``current position``
                    at the upper left corner. So, further text starts
                    from the top-left of the screen.
                    The advantage of this policy is, that it is a
                    light-weight implementation that allows for
                    continuous text output without caller interaction.
                    The disadvantage is, that after text rolls over a
                    screen boundary - even if only by one letter - old
                    text cannot be seen, anymore.
        INVERT      Each time, text placement reaches a new line (!),
                    that line is cleared and by this, colored with a
                    certain background color starting with white.
                    When reaching the bottom right corner, text continues
                    at the top left screen position without clearing the
                    screen. Instead, the background color is flipped from
                    white to black or vice versa, clearly marking the
                    *new* lines. The *current* screen  and the *previous*
                    one appear clearly separated by inverse colors. And
                    even if the screen is full, as much as possible of
                    the old text can be seen.
        SCROLL      This is the most popular policy known from common
                    console applications. When the text reaches the end
                    of the screen, the whole content scrolls up by one
                    line of text. That is, the first line at the top is
                    abandoned, the second line is placed on the first one,
                    the third goes to the second and so on.
                    The last line is placed in the last but one freeing
                    space for a new last line. After blanking the last
                    line, further text goes there until the end of line,
                    and thus, the end of the screen is reached again and
                    the procedure starts anew.
                    This is the policy with the most convenient user
                    experience. If this behavior is not supported by
                    hardware, it requires the most complex software
                    implementation.
        ========    =========================================

        Due to the varying support for different policies or code size
        requirements, the caller should be prepared to get an
        :attr:`ErrorCode.errNotImplemented` return value for one or the
        other policy.
        
        :param int policy: The new policy to apply. One of the ``SCREEN_POLICY_*`` values.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if not isinstance( policy, int) or \
            (policy < self.SCREEN_POLICY_STOP) or (policy > self.SCREEN_POLICY_SCROLL):
            ret = ErrorCode.errInvalidParameter
        else:
            ret = ErrorCode.errOk
            self._screenPolicy = policy
        return ret

    def printChar( self, code):
        """Print a character at the internal ``current position``.
        
        The size of the character is defined by the current font.
        Upon successful return, the current position is moved on by one
        character position. Usually, this means moving right by one 
        character. At the end of a line, the new current position is
        automatically placed at the beginning of the next line.
        At the end of the screen, the screen-full policy applies.
        
        The character handed in should be a genuine ASCII code.
        Codes less than 32 (hex. 0x20) are control codes and thus, are
        not printed. Still, passing those codes to this function may have
        visible effects. As far as these codes concern
        cursor control, the associated movement is emulated with the
        internal ``current position`` as good as possible. Other codes
        in this category may be simply are ignored.
        
        Codes from 32...127, inclusively, are printed according to the
        current font.
        It's up to the implementation, how to handle non-ASCII codes
        beyond 127.

        Also see: :meth:`goToChar`, :meth:`setScreenFullPolicy`
        
        :param int code: The character to print.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
    
        if( self._font is None ):
            ret = ErrorCode.errInadequate
        elif( (self._currentX + 1 > self._widthChar) or \
                (self._currentY + 1 > self._heightChar) ):
            ret = ErrorCode.errSpecRange
        else:
            # Characters with special treatment
            if code == 8:       # backspace
                if self.goByChar( -1, 0 ).isOk():
                    ret = self.printChar( ' ' )
                    self.goByChar( -1, 0 )
            elif code == 9:     # Tab
                iTemp = self._tabsize
                iTemp = self._currentX + iTemp - (self._currentX % iTemp)
                if( iTemp + 1 <= self._widthChar ):
                    ret = self.goToChar( iTemp, self._currentY )
                else:
                    ret = self._updateLineFeed()
            elif (code == 10) or (code == 13):   # Line feed, carriage return
                ret = self._updateLineFeed()
                if ret == ErrorCode.errInadequate:
                    self.goToChar( self._widthChar, self._currentY )
            elif code == 12:    # Form feed
                ret = self.goToChar( 0, 0 )
            else:
                ret = self._drvPrintChar(code)
                # Update virtual cursor position to place next character at
                if ret.isOk():
                    ret = self._updateNextChar()
        return ret

    def printString( self, string ):
        """Print a string.
        
        The first character of the given string is printed at the
        internal ``current position``. Then, the rest of it is printed
        consecutively character by character advancing the internal
        ``current position`` until the screen-full policy must be
        applied.
        
        Also see: :meth:`printChar`
        
        :param str string: The string to be printed.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        data = string.encode()
        for code in data:
            ret = self.printChar(code)
            if not ret.isOk():
                break
        return ret

###
#
# GraphicDisplay
#
###

# Colors and color names

class Color(int):
    """Colors that can be used when drawing to the LCD.
    
    The underlying hardware might support different color spaces, like
    8 bit gray scale or 24 bit true color levels.
    """

@unique
@idiotypic
class GrayScale1(Enum):
    """Mnemonics for the black/white color space.
    
    The underlying color-space is 1-bit b/w scale allowing for just 2
    nuances - black and white.
    """
    BLACK         = 0x00  # 1bit color space, full black
    WHITE         = 0xFF  # 1bit color space, bright white
    
@unique
@idiotypic
class GrayScale2(Enum):
    """Mnemonics for a simple 2-bit mono-chromatic color space.
    
    The underlying color-space is 2-bit gray scale allowing for just 4
    nuances.
    """
    BLACK         = 0x00   # 2bit color space, full black
    DARK_GRAY     = 0x55   # 2bit color space, dark gray
    LIGHT_GRAY    = 0xAA   # 2bit color space, light gray
    WHITE         = 0xFF   # 2bit color space, bright white
    
@unique
@idiotypic
class GrayScale4(Enum):
    """Mnemonics for a 4-bit mono-chromatic color space.
    
    The underlying color-space is 4-bit gray scale allowing for 16
    nuances.
    """
    BLACK         = 0x00  # 4bit color space, full black
    DIRTY_BLACK   = 0x11  # 
    MEDIUM_BLACK  = 0x22  # 
    COAL_GRAY     = 0x33  # 
    LIGHT_BLACK   = 0x44  # 
    DARK_GRAY     = 0x55  # 4bit color space, dark gray
    ZINC_GRAY     = 0x66  # 
    LEAD_GRAY     = 0x77  # 
    MEDIUM_GRAY   = 0x88  # 4bit color space, medium gray
    SPANISH_GRAY  = 0x99  # 
    LIGHT_GRAY    = 0xAA  # 4bit color space, light gray 
    SILVER_GRAY   = 0xBB  # 
    DARK_WHITE    = 0xCC  # 
    MEDIUM_WHITE  = 0xDD  # 
    DIRTY_WHITE   = 0xEE  # 
    WHITE         = 0xFF  # 4bit color space, bright white

@unique
@idiotypic
class GrayScale8(Enum):
    """Mnemonics to short-cut official names for shades of black, white and gray.
    
    The underlying color-space is 8-bit gray scale allowing for a total
    of 256 nuances. Only some of them are named.
    
    Also see:
    https://en.wikipedia.org/wiki/Shades_of_black
    https://en.wikipedia.org/wiki/Shades_of_gray
    https://en.wikipedia.org/wiki/Shades_of_white
    """
     
    BLACK          = 0x00    # Full black, dot always set
    VAMPIRE_BLACK  = 0x08
    ONYX           = 0x0F
    CHINESE_BLACK  = 0x14
    EERIE_BLACK    = 0x1B
    DARK_CHARCOAL  = 0x33
    JET_BLACK      = 0x34
    TUNDORA        = 0x40
    DAVYS_GRAY     = 0x55
    DIM_GRAY       = 0x69
    SONIC_SILVER   = 0x75
    GRAY           = 0x80    # Right between black and white
    SPANISH_GRAY   = 0x98
    DARK_GRAY      = 0xA9
    SILVER_CHALICE = 0xAC
    MEDIUM_GRAY    = 0xBE
    SILVER         = 0xC0
    LIGHT_GRAY     = 0xD3
    GAINSBORO      = 0xDC
    WHITE_SMOKE    = 0xF5
    WHITE          = 0xFF    # Bright white, dot not set

class Image():
    """Helper class to represent an image.
    """
    
    def __init__(self):
        self._colorspace = ColorSpace.GRAY_1
        self._width = 0
        self._height = 0
        self._data = None
        
    @property
    def width(self):
        return self._width
    
    @property
    def height(self):
        return self._height

    @property
    def colorspace(self):
        return self._colorspace
    
    
class GraphicDisplay(TextDisplay):
    """Abstract API class for displays capable of showing graphics.
    
    Implementations of this interface are expected to drive a specific
    hardware, which is usually an LCD or OLED.
    
    Beyond everything that is inherited from TextDisplay, graphic displays
    know of different colors and inks.
    
    The concept of ink is a short cut for logic operations executed when
    drawing a possibly colored pixel on the background. Pixel data may
    originate from drawing (and anti-aliasing) a line or from the font
    when printing a character. Logic is computed bit-wise of the pixel
    and background color values as follows:
    
    ===========    ==============================================================
    Ink            Effect
    ===========    ==============================================================
    REPLACE        Old content is simply replaced. No logic applies.
    OVERLAY        New content is logically ORed with the old one.
                   Usually that leads to the screen area becoming darker
                   as more pixels are set or gray scales sum up.
    MASK           New content is logically ANDed with the old one
                   resulting in lighter screen area. Only those pixels
                   keep set, that were set before and would be set by
                   the new content.
    INVERT         New content is logically XORed with the old one.
                   Original content is preserved were the new content has
                   white pixels, while the original content is negated
                   were the new content has black pixels.
    ===========    ==============================================================
    
    """


    # Mnemonics for the ink style.
    # The ink style defines the logical operation to be performed when
    # drawing to the display.
    INK_STYLE_REPLACE = 0    # Simply substitute the background, no logic at all
    INK_STYLE_OVERLAY = 1    # Overlay, add, logic OR
    INK_STYLE_MASK    = 2    # Mask, wipe out, logic AND
    INK_STYLE_INVERT  = 3    # Invert, logic  XOR


    def __init__(self):
        # Derived attributes
        super().__init__()
        # Own attributes
        self._widthPixel = 0
        self._heightPixel = 0
        self._colorspace= ColorSpace.GRAY_1 # Color space.
        self._backgroundColor = GrayScale1.BLACK
        self._ink = GraphicDisplay.INK_STYLE_REPLACE
        
    #############################
    # Module API
    #############################

    def open(self, paramDict):
        ret = super().open(paramDict)
        if ret.isOk():
            ret = self.goToPixel(0, 0)
        return ret

    #############################
    # Inherited API
    #############################

    #
    # Non-public, internal driver interface
    # Wherever possible, method signatures are oriented on their
    # public counterparts.
    #

    #
    # Non-public helper methods
    #

    def _invertColor(self, space, value):
        ret = 0
        if space <= ColorSpace.GRAY_8:
            ret = 0xFF - value
        elif space == ColorSpace.PALETTE4:
            ret = 0x0F - value
        elif space == ColorSpace.PALETTE8:
            ret = 0xFF - value
        elif space == ColorSpace.RGB_16:
            ret = 0xFFFF - value
        elif space == ColorSpace.RGB_24:
            ret = 0xFFFFFF - value
        elif space == ColorSpace.RGB_32:
            ret = 0xFFFFFFFF - value
        else:
            ret = 0
        return ret
        
    def _updateLineFeed(self):
        ret = ErrorCode.errOk
    
        # Try line feed
        iTemp = self._currentY + self.font.charHeight
        if (iTemp + self.font.charHeight <= self._heightPixel):
            ret = self.goToChar( 0, iTemp)
            if self._screenPolicy == TextDisplay.SCREEN_POLICY_INVERT:
                ret = self.drawBox( self._widthPixel, self.font.charHeight,
                                    self._backgroundColor, self.INK_STYLE_REPLACE)
        else:
            # reached the end of screen: apply the screen full policy
            if (self._screenPolicy == self.SCREEN_POLICY_CLEAR):
                ret = self.clearScreen()
            if (self._screenPolicy == self.SCREEN_POLICY_INVERT):
                self.goToChar(0, 0)
                self._backgroundColor = self._invertColor(self._colorspace, self._backgroundColor)
                ret = self.drawBox( self._widthPixel, self._font.charHeight,
                                    self._backgroundColor, self.INK_STYLE_REPLACE)
            if (self._screenPolicy == self.SCREEN_POLICY_SCROLL):
                # Number of rows ( pixels ) that should be scrolled
                ret = self._drvScrolLV( self._font.charHeight )
                # Go to the beginning of the row that should be replaced
                ret = self._goToPixel(0, self._currentY)
            else:
                ret = ErrorCode.errInadequate
        return ret
    
    def _updateNextChar(self):
        ret = ErrorCode.errOk
        self._currentX += self._font.charWidth
        if( self._currentX + self._font.charWidth <= self._widthPixel ):
            ret = self.goToPixel( self._currentX, self._currentY )
        else:
            ret = self._updateLineFeed()
        return ret

    #
    # Public API
    #

    def moveCursorToChar( self, x, y ):
        ret = ErrorCode.errOk
        if not self._font:
            ret = ErrorCode.errInadequate
        else:
            xp = x * self._font.charWidth
            yp = y * self._font.charHeight
            if (xp < 0) or (xp > self._widthPixel) or  \
                (yp < 0) or (yp > self._heightPixel):
                ret = ErrorCode.errSpecRange
            else:
                ret = self._drvMoveCursorTo(xp, yp)
                if ret.isOk():
                    self._cursorX = xp
                    self._cursorY = yp
        return ret

    def moveCursorByChar( self, x, y ):
        ret = ErrorCode.errOk
        if not self._font:
            ret = ErrorCode.errInadequate
        else:
            absX = self._cursorX + x*self._font.charWidth
            absY = self._cursorY + y*self._font.charHeight
            if (absX < 0) or (absX > self._widthPixel) or   \
                (absY < 0) or (absY > self._heightPixel):
                ret = ErrorCode.errSpecRange
            else:
                ret = self._drvMoveCursorTo( absX, absY )
                if ret.isOk():
                    self._cursorX = absX
                    self._cursorY = absY
        return ret

    def goToChar( self, x, y ):
        ret = ErrorCode.errOk
        if not self._font:
            ret = ErrorCode.errInadequate
        else:
            xp = x * self._font.charWidth
            yp = y * self._font.charHeight
            ret = self.goToPixel(xp, yp)
        return ret

    def goByChar( self, x, y ):
        ret = ErrorCode.errOk
        if not self._font:
            ret = ErrorCode.errInadequate
        else:
            absX = self._currentX + x*self._font.charWidth
            absY = self._currentY + y*self._font.charHeight
            ret = self.goToPixel(absX, absY)
        return ret

    def clearScreen(self):
        ret = self._drvScrollV( 0 )
        if ret.isLight():
            ret = self.goToPixel( 0, 0 )
        if ret.isOk():
            ret = self._drvClearScreen()
        return ret

    def setFont( self, font ):
        ret = super().setFont(font)
        if ret.isOk():
            self._widthChar = self._widthPixel / self._font.charWidth
            self._heightChar= self._heightPixel/ self._font.charHeight
        return ret
    
    def printChar( self, code ):
        """Print a character at the current position of the virtual drawing cursor.
        
        This current position defines the upper left corner of the
        character bitmap to draw. The size of that bitmap is defined by
        the current font. The content of the bitmap is defined
        by the given character code and the corresponding font entry.
        The color is also defined by that font entry.
        
        Depending on the current ink set, logic operation between the
        character color and the background may be applied. 
        
        Upon successful return, the virtual drawing cursor is moved by
        one character position. Usually, this means moving right by the
        character's width. At the end of a line, the virtual drawing
        cursor is automatically placed at the beginning of the next line.
        At the end of the screen, the screen-full policy applies.
        
        Also see: :meth:`TextDisplay.printChar`
        
        :param int code: The character to print, given as an ASCII code.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
    
        if( self._font is None ):
            ret = ErrorCode.errInadequate
        elif( (self._currentX + self._font.charWidth > self._widthPixel) or \
              (self._currentY + self._font.charHeight > self._heightPixel) ):
            ret = ErrorCode.errSpecRange
        else:
            # Characters with special treatment
            if code == 8:       # backspace
                if self.goByChar( -1, 0 ).isOk():
                    ret = self.printChar( ' ' )
                    self.goByChar( -1, 0 )
            elif code == 9:     # Tab
                iTemp = self._tabsize * self._font.charWidth
                iTemp = self._currentX + iTemp - (self._currentX % iTemp)
                if( iTemp + self._font.charWidth <= self._widthPixel ):
                    ret = self.goToPixel( iTemp, self._currentY )
                else:
                    ret = self._updateLineFeed()
            elif (code == 10) or (code == 13):   # Line feed, carriage return
                ret = self._updateLineFeed()
                if ret == ErrorCode.errInadequate:
                    self.goToPixel( self._widthPixel - 1, self._currentY )
            elif code == 12:    # Form feed
                ret = self.goToChar( 0, 0 )
            else:
                ret = self._drvPrintChar(code)
                # Update virtual cursor position to place next character at
                if ret.isOk():
                    ret = self._updateNextChar()
        return ret

    #############################
    # Specific API
    #############################

    #
    # Non-public, internal driver interface
    # Wherever possible, method signatures are oriented on their
    # public counterparts.
    #

    def _drvDrawPixel( self, x, y, color ):
        """Draw a single pixel with the given color and ink logic.

        The implemantation can rely on :meth:`goToPixel` has been
        executed, before.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del x, y
        ret = self.drawBox( 1, 1, color )
        return ret
        
    @abstractmethod
    def _drvDrawBox( self, width, height, color ):
        """Draw a box with the given color and ink logic.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del width, height, color
        return ErrorCode.errNotSupported
        
    def _drvDrawImage( self, image ):
        """Draw an image at the current position with the given ink logic.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del image
        return ErrorCode.errNotSupported
        
    def _drvScrollHstart( self, direction, start_row, end_row,
                          start_col, end_col, scroll_step ):
        """Execute a horizontal scroll of the content displayed.
        
        :param int direction: The direction of scrolling. One of :attr:`TextDisplay.SCROLL_DIR_LEFT` or :attr:`TextDisplay.SCROLL_DIR_RIGHT`. 
        :param int start_row: Starting row number.
        :param int end_row: End row number.
        :param int start_col: Start column number.
        :param int end_col: End column number.
        :param int scroll_step: The time interval in frames per scroll step
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del direction, start_row, end_row, start_col, end_col, scroll_step
        return ErrorCode.errNotImplemented
 
    def _drvScrollHstop( self ):
        """Deactivate (stop) the horizontal scrolling.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errNotImplemented


    #
    # Public API
    #

    @property    
    def widthPixel(self):
        """Retrieve the display width, measured in characters."""
        return self._widthPixel
    
    @property    
    def heightPixel(self):
        """Retrieve the display height in characters."""
        return self._heightPixel

    @property    
    def colorspace(self):
        """Retrieve the display color space."""
        return self._colorspace
    
    @property    
    def backgroundColor(self):
        """Retrieve the current background color."""
        return self._backgroundColor
    
    @property    
    def ink(self):
        """Retrieve the ink logic."""
        return self._ink
    
    @ink.setter
    def ink(self, value ):
        self._ink = value
    
    def goToPixel( self, x, y ):
        """Move the internal drawing cursor or ``current position`` to the given absolute position.
        
        The internal cursor is the starting point when drawing lines,
        characters etc. and is not visible to the user. Instead, it is
        a virtual cursor.
        It should not be mixed up with the hardware cursor that can be
        controlled by :meth:`TextDisplay.moveCursorToChar`.
        The same cursor is also manipulated by the :meth:`TextDisplay.goToChar`
        method.

        Also see: :meth:`goByPixel`
        
        :param int x: The new horizontal position given in pixels.
        :param int y: The new vertical position given in pixels.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if (x < 0) or (x > self._widthPixel) or  \
            (y < 0) or (y > self._heightPixel):
            ret = ErrorCode.errSpecRange
        else:
            ret = self._drvGoTo(x, y)
            if ret.isOk():
                self._currentX = x
                self._currentY = y
        return ret


    def goByPixel( self, x, y ):
        """Move the virtual drawing cursor by a relative distance, expressed in pixels.
        
        Actually, the new position calculates as the arithmetic sum of
        the internal ``current position`` and the arguments.
        If the movement would exceed the screen limits, nothing is moved and the
        function returns an error code.
        
        Positive values will move the virtual cursor to the right or
        downwards, while negative values will move it to the left or
        upwards, respectively.
        
        Also see: :meth:`goToPixel`, :meth:`TextDisplay.goByChar`
        
        :param int x: The horizontal displacement in pixels.
        :param int y: The vertical distance to move, given in pixels.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return self.goToPixel(x+self._currentX, y+self._currentY)

    def drawBox( self, width, height, color ):
        """Draw a filled rectangle.
        
        The upper left corner of the rectangle is defined by the virtual
        drawing cursor. The size is given by the parameters, as well
        as the color and ink type to draw with.
        A width of 1 will produce a vertical line, a height of 1 will
        result in a horizontal line. If both, width and height are 1,
        the box will be a single pixel.
        
        Note that the rectangle's border color is the same as the fill
        color.
        Depending on the current ink set, logic operation between the
        given (foreground-)color and the background may be applied. 
        
        On return, the virtual drawing cursor is not changed.
        
        :param int width: The horizontal width of the box, given in pixels.
        :param int height: The vertical size of the box to draw, given in pixels.
        :param int color: The color or shade of grey, that the box shall be of.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return self._drvDrawBox(width, height, color)
        
    def drawPixel( self, x, y, color ):
        """Set a pixel at the given position with the given color and ink.
        
        Moves the virtual drawing cursor to the given position and draws
        a 1x1 box with the given color.
        Depending on the current ink set, logic operation between the
        given (foreground-)color and the background may be applied. 

        Also see: :meth:`drawBox`
        
        :param int x: The x coordinate of the pixel to draw.
        :param int y: The y coordinate of the pixel to draw.
        :param int color: The color to draw with.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = self.goToPixel(x, y)
        if ret.isOk():
            ret = self._drvDrawPixel(x, y, color)
        return ret
    
    def drawHLine( self, width, color ):
        """Draw a horizontal line.
        
        Drawing starts from the virtual drawing cursor's current
        position and extends over the specified width.
        Upon return, the position of the virtual drawing cursor is left
        unchanged.
        In terms of speed, this function is preferable over the more general
        function :meth:`drawLine`.

        Depending on the current ink set, logic operation between the
        given (foreground-)color and the background may be applied. 

        Also see: :meth:`drawVLine`, :meth:`drawLine`
         
        :param int width: The length of the line, given in pixels.
        :param int color: The color of the line.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return self.drawBox(width, 1, color)

    def drawVLine( self, height, color ):
        """Draw a vertical line.
        
        Drawing starts at the current position of the virtual drawing
        cursor. The length of the line is specified as a parameter.
        On return, the virtual drawing cursor is still at the same
        position.
        In terms of speed, this function is preferable over the more
        general function :meth:`drawLine`.

        Depending on the current ink set, logic operation between the
        given (foreground-)color and the background may be applied. 

        Also see: :meth:`drawHLine`, :meth:`drawLine`
        
        :param int height: The vertical length of the line, given in pixels.
        :param int color: The color of the line.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return self.drawBox(1, height, color)

    def drawLine( self, xEnd, yEnd, color ):
        """Draw a line in an arbitrary direction.
        
        Drawing starts from the current position of the virtual drawing
        cursor. The end point is given by the parameters.
        Upon return, the virtual drawing cursor is at the end point
        position.
        
        If the caller knows, that the line is simply vertical or
        horizontal, :meth:`drawVLine` or :meth:`drawHLine` should be
        called, instead. Otherwise, this function will find out and
        optimize performance that way.
        
        For all other, non-trivial lines, implementation uses the
        Bresenham algorithm to construct the line pixel by pixel.

        Depending on the current ink set, logic operation between the
        given (foreground-)color and the background may be applied. 
        
        :param int xEnd: The x coordinate of the end point, given in pixels.
        :param int yEnd: The vertical component of the end point, given in pixels.
        :param int color: The color of the line.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        x0 = self._currentX
        y0 = self._currentY

        if x0==xEnd:
            ret = self.drawVLine( yEnd-y0, color )
        elif y0==yEnd:
            ret = self.drawHLine( xEnd-x0, color )
        else:
            if( x0 < xEnd ):
                dx = xEnd - x0
                sx = 1
            else:
                dx = x0 - xEnd
                sx = -1

            if y0 < yEnd:
                dy = y0 - yEnd
                sy = 1
            else:
                dy = yEnd - y0
                sy = -1

            err = dx + dy
            while True: # loop
                self.drawPixel(x0, y0, color)
                if (x0 == xEnd) and (y0 == yEnd):
                    break
                e2 = 2 * err
                if e2 > dy:     # e_xy+e_x > 0
                    err += dy
                    x0 += sx
                if (e2 < dx):   # e_xy+e_y < 0
                    err += dx
                    y0 += sy
            ret = self.goToPixel( xEnd, yEnd )
        return ret

    def drawRectangle( self, width, height, color ):
        """Draw an empty rectangle.
        
        The upper left corner of the rectangle is defined by the virtual
        drawing cursor. The size is given by the parameters as well
        as the color and ink type to draw with.
        
        A width of 1 will produce a vertical line, a height of 1 will
        result in a horizontal line. If both, width and height are 1,
        the result will be a single pixel.
        
        Note that the rectangle's border width is always one pixel.
        Depending on the current ink set, logic operation between the
        given (foreground-)color and the background may be applied. 
        
        On return, the virtual drawing cursor is not changed.

        Also see: :meth:`drawBox`
        
        :param int width: The horizontal width of the rectangle, given in pixels.
        :param int height: The vertical size of the rectangle to draw, given in pixels.
        :param int color: The color or shade of grey, that the box line shall be of.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
    
        if (width > 0) and (height > 0):
            xOrg = self._currentX
            yOrg = self._currentY
    
            ret = self.drawHLine( width, color )
            ret = self.drawVLine( height, color )
            self.goToPixel( xOrg, yOrg + height - 1 )
            ret = self.drawHLine( width, color )
            self.goToPixel( xOrg + width - 1, yOrg )
            ret = self.drawVLine( height, color )
            self.goToPixel( xOrg, yOrg )
        return ret

    def drawCircle( self, radius, color ):
        """Draw a circle.
        
        The center of the circle is defined by the current position
        of the virtual drawing cursor. This position is not changed on
        return.
        The radius of the circle is provided as a parameter.

        Depending on the current ink set, logic operation between the
        given (foreground-)color and the background may be applied. 
        
        The implementation uses a variant of the Bresenham algorithm.
        
        :param int radius: The radius of the circle, given in pixels. Should be positive.
        :param int color: The color of the circle.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        # The current position is the center (x0, y0) of the circle.
        x0 = self._currentX
        y0 = self._currentY
        f = 1 - radius
        ddF_x = 0
        ddF_y = -2 * radius
        x = 0
        y = radius

        self.drawPixel( x0, y0 + radius, color )
        self.drawPixel( x0, y0 - radius, color )
        self.drawPixel( x0 + radius, y0, color )
        self.drawPixel( x0 - radius, y0, color )

        while (x < y):
            if (f >= 0):
                y -= 1
                ddF_y += 2
                f += ddF_y
            x += 1
            ddF_x += 2
            f += ddF_x + 1

            self.drawPixel( x0 + x, y0 + y, color )
            self.drawPixel( x0 - x, y0 + y, color )
            self.drawPixel( x0 + x, y0 - y, color )
            self.drawPixel( x0 - x, y0 - y, color )
            self.drawPixel( x0 + y, y0 + x, color )
            self.drawPixel( x0 - y, y0 + x, color )
            self.drawPixel( x0 + y, y0 - x, color )
            self.drawPixel( x0 - y, y0 - x, color )
        ret = self.goToPixel( x0, y0 )
        return ret

    def drawImage( self, image ):
        """Draw an image at the current position of the virtual drawing cursor.
        
        The size and data of the image are encapsulated in the
        ``image```parameter.
        Depending on the current ink set, logic operation between the
        image data/color and the background may be applied. 
        
        On return, the position of the virtual drawing cursor is left
        unchanged.
        
        :param int image: The image including meta data like width and height. 
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return self._drvDrawImage( image )

    def scrollHstart( self, direction, start_row, end_row,
                      start_col, end_col, scroll_step ):
        """Execute a horizontal scroll of the content displayed.
        
        :param int direction: The direction of scrolling. One of :attr:`TextDisplay.SCROLL_DIR_LEFT` or :attr:`TextDisplay.SCROLL_DIR_RIGHT`. 
        :param int start_row: Starting row number.
        :param int end_row: End row number.
        :param int start_col: Start column number.
        :param int end_col: End column number.
        :param int scroll_step: The time interval in frames per scroll step
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return self._drvScrollHstart( direction, start_row, end_row,
                                      start_col, end_col, scroll_step )
 
    def scrollHstop( self ):
        """Deactivate (stop) the horizontal scrolling.
        
        After calling this function the display data may need to be
        rewritten
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return self._drvScrollHstop()

