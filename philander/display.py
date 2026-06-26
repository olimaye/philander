"""Basic display module to support different kinds of a visible user interface.

This is a convergence layer to provide unified access to displays,
screens and other visible user interfaces beyond LEDs.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Display", ]

from abc import ABC, abstractmethod

from .module import Module
from .pwm import PWM
from .systypes import ErrorCode, RunLevel

 
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
        # important states to remember
        self._runLevel = RunLevel.shutdown
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
        display.light.pwm.*            PWM configuration for the display light
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

        prefix = cls.MODULE_PARAM_PREFIX + ".light."
        tempDict = cls._extractParams( paramDict, prefix)
        PWM.Params_init(tempDict)
        cls._aggregateParams( paramDict, tempDict, prefix )
        
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
        SetDormant = [RunLevel.sleep, RunLevel.deepSleep, RunLevel.shutdown]
        ret = ErrorCode.errOk

        if level == RunLevel.active:
            intensity = Display.INTENSITY_HIGH
        elif level == RunLevel.idle:
            intensity = Display.INTENSITY_MEDIUM
        elif not level in SetDormant:   # relax, snooze, nap
            intensity = Display.INTENSITY_LOW
        else:
            intensity = Display.INTENSITY_OFF

        if not level in SetDormant: # active ... nap
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
            self._runLevel = level
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
