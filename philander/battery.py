"""A module to reflect capabilities and properties of re-chargeable batteries.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Level", "Capacity", "Status"]

from enum import Enum, unique, Flag

from .primitives import Percentage


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
        new_lvl = Level.invalid
        for lvl in list(Level):
            if lvl is Level.invalid:
                continue
            elif (percentage >= lvl) and (new_lvl is Level.invalid or lvl > new_lvl):
                # check if percentage is above certain level
                # and if lvl is closer to percentage than previously set new_lvl
                new_lvl = lvl
        return new_lvl


class Capacity(int):
    """Absolute capacity of a battery in mAh
    """
    invalid = 0xFFFF


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
