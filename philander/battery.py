"""A module to reflect capabilities and properties of re-chargeable batteries.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Level", "Capacity", "Status"]

from .penum import Enum, Flag, idiotypic

from .primitives import Percentage


@idiotypic
class Level(Enum):
    """Level of a battery in [0...100]%
    """
    min       = 0
    empty     = 5
    low       = 20
    medium    = 40
    good      = 70
    full      = 90
    max       = 100
    deepDischarge   = min
    invalid         = Percentage.invalid

    @staticmethod
    def fromPercentage(percentage):
        """Convert a given percentage into the corresponding level predicate.
        
        Returns the largest level, that is less than or equal to the given
        percentage. So, the returned level is an underestimation.
        Or, to put it differently, the real capacity remaining is *at least*
        the level returned.
        
        If the given percentage is ``Percentage.invalid`` or does not compare
        to a number, ``Level.invalid`` is returned.Values below zero are
        mapped to ``Level.min``, while values beyond 100 are mapped to
        ``Level.max``.
        
        :param Percentage percentage: The percentage value to be converted.
        :return: The largest level just under-estimating the given percentage.
        :rtype: Level
        """
        new_lvl = Level.invalid
        try:
            # Check if percentage compares to int
            if percentage < 5: pass
            new_lvl = Level.min
            lst = list(Level)
            lst.remove(Level.invalid)
            for lvl in lst:
                if (lvl.value <= percentage) and \
                     ((new_lvl is Level.invalid) or \
                      (lvl.value > new_lvl.value) ):
                    # check if percentage is above certain level
                    # and if lvl is closer to percentage than previously set new_lvl
                    new_lvl = lvl
        except TypeError:
            # Percentage is something, that does not compare to int:
            new_lvl = Level.invalid
        return new_lvl


class Capacity(int):
    """Absolute capacity of a battery in mAh
    """
    invalid = 0xFFFF


@idiotypic
class Status( Flag ):
    """Container class to reflect the battery status
    """
    normal               = 0x0000
    """Battery ok"""
    
    removed              = 0x0001
    """Battery removed"""
    broken               = 0x0002
    """Charging takes (too) long; old/damaged battery"""
    problemPhysical      = 0x000F
    """Any physical problem"""
    
    empty                = 0x0010
    """Battery empty, deep discharge"""
    low                  = 0x0020
    """Battery voltage low"""
    overvoltage          = 0x0040
    """Battery voltage greater than threshold"""
    overcurrent          = 0x0080
    """Battery current to high"""
    problemElectrical    = 0x00F0
    """Any electrical problem"""
    
    cold                 = 0x0100
    """Battery is too cold"""
    hot                  = 0x0200
    """Battery is too hot"""
    coldOrHot            = (cold | hot)
    """Battery temperature is outside its operating conditions"""
    problemThermal       = 0x0F00
    """Any thermal problem"""
    
    unknown              = 0xFFFF
    """Battery status information is unavailable"""
