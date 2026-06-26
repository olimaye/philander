"""Module to support graphic display.

This is a convergence layer to provide unified access to graphic
displays. Typically, the smallest item that can be displayed by those
devices, is a single pixel. Possibly, colors beyond the gray-spectrum
are supported. 
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Color",
           "GrayScale1", "GrayScale2", "GrayScale4", "GrayScale8", 
           "Image",
           "GraphicDisplay", ]

from abc import abstractmethod

from .display_text import TextDisplay
from .penum import Enum, unique, idiotypic
from .systypes import ErrorCode



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

    def _drvClearScreen( self ):
        """Clear all contents from screen.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = self.drawBox(self._widthPixel, self._heightPixel,
                           self._backgroundColor)
        return ret
        

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

