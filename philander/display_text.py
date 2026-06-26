"""Module to support character-based text displays.

This is a convergence layer to provide unified access to text-only
displays. Usually, characters are displayed one by one in a row.
A specific display may support multiple rows.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["ColorSpace", "Font", "TextDisplay", ]

from abc import abstractmethod

from .display import Display
from .penum import Enum, unique, idiotypic, dataclass
from .systypes import ErrorCode, RunLevel


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
        self._cursorMode = TextDisplay.CURSOR_MODE_BLACK
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
            "screenpolicy": TextDisplay.SCREEN_POLICY_STOP,
            "tabsize": TextDisplay.DEFAULT_TAB_SIZE,
        }
        cls._aggregateParams( paramDict, defaults, cls.MODULE_PARAM_PREFIX + "." )
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

    @abstractmethod
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
        if ret.isOk():
            self._cursorMode = mode
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

