"""A module t reflect capabilities and properties of re-chargeable batteries.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Level", "Capacity", "Status"]

from dataclasses import dataclass

from .primitives import Percentage


@dataclass
class Level():
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

    toStr = {
        min     : 'minimum',
        empty   : 'empty',
        low     : 'low',
        medium  : 'medium',
        good    : 'good',
        full    : 'full',
        max     : 'maximum',
        invalid : 'invalid',
    }
    
class Capacity(int):
    """Absolute capacity of a battery in mAh
    """
    invalid = 0xFFFF

@dataclass
class Status:
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

    toStr = {
        normal        : 'normal',
        removed       : 'removed',
        broken        : 'broken',
        empty         : 'empty',
        low           : 'low',
        overvoltage   : 'overvoltage',
        overcurrent   : 'overcurrent',
        cold          : 'cold',
        hot           : 'hot',
        coldOrHot   : 'cold or hot',
        unknown       : 'unknown',
    }
