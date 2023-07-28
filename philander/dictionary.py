"""Types and functions making up the dictionary module.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["dictionary", ]

from .systypes import ErrorCode

class dictionary():
    """A dictionary is meant to translate keys to values, both of them being integers.
    
    For example, a certain configuration register content could be
    translated into its physical data domain by means of a dictionary. The BMA456
    acceleration sensor can adjust its measurement range to +/- 2g, 4g, 8g or
    even 16g by setting its ACC_RANGE register to either 0, 1, 2 or 3,
    respectively. Considering the register content to be the key domain, whereas
    the corresponding range limits are the values, a dictionary would translate
    as follows:
    
    ====    ========
    Key     Value
    ====    ========
    0       2000
    1       4000
    2       8000
    3       16000
    ====    ========
    
    It is also possible to translate vice-versa, i.e. from the value-domain into
    keys by finding the nearest matching key. The behavior of this search
    algorithm can be controlled by the dictionary's ``mode`` attribute.
    
    Note that at the advantage of runtime speed, this implementation assumes the
    dictionary be sorted by values in ascending order.
    """
    
    #
    # Mnemonics of the dictionary mode to control the backward-search algorithm of
    # finding keys for a given value.
    # 
    
    DICT_MODE_UNDERRUN              = 0x01
    """Bitmask for the mode particle to define the mapping for values below the
    lowest value (!) in the dictionary, a so-called underrun.
    """
    
    DICT_MODE_UNDERRUN_MAP          = 0x00
    """Make values below the lowest value be mapped to the key corresponding to that
    lowest value.
    """
    
    DICT_MODE_UNDERRUN_ERROR        = DICT_MODE_UNDERRUN
    """Values below the lowest value in the dictionary are not mapped, but cause an
    error when trying to find a matching key.
    """
    
    DICT_MODE_OVERRUN               = 0x02
    """Bitmask for the mode particle to define the mapping for values above the
    highest value in the dictionary, a so-called overrun.
    """
    
    DICT_MODE_OVERRUN_MAP           = 0x00
    """Values above the highest value will be mapped to the key corresponding to
    that highest value.
    """
    
    DICT_MODE_OVERRUN_ERROR         = DICT_MODE_OVERRUN
    """Values larger than the highest value in dictionary will not be mapped, but
    cause an error when trying to find a matching key.
    """
    
    DICT_MODE_MAP                   = 0x0c
    """Bitmask for the mode particle to define the mapping for values that are
    in the range defined by the minimum and maximum values in the dictionary.
    """
    
    DICT_MODE_MAP_STRICTLY          = 0x00
    """Strict mapping: Only those values, that are contained in the dictionary will
    be mapped to their corresponding keys. Other values will produce errors.
    """
    
    DICT_MODE_MAP_NEAREST_LOWER     = 0x04
    """Map by rounding down: A value is mapped to the key that corresponds to the
    largest value, that is smaller than (or equal to) it.
    """
    
    DICT_MODE_MAP_NEAREST_HIGHER    = 0x08
    """Map by rounding up: A value is mapped to the key that corresponds to the
    smallest value, that is larger than (or equal to) it.
    """
    
    DICT_MODE_MAP_NEAREST           = (DICT_MODE_MAP_NEAREST_LOWER | DICT_MODE_MAP_NEAREST_HIGHER)
    """Map by ordinary rounding: A value is mapped to the key that corresponds to
    the nearest value in dictionary.
    """
    
    DICT_STDMODE_NORMAL             = (DICT_MODE_UNDERRUN_MAP | DICT_MODE_OVERRUN_MAP | DICT_MODE_MAP_NEAREST)
    """Shortcut, just for convenience. Normal mode maps to the nearest possible key,
    as well as underruns and overruns without errors.
    """
    
    DICT_STDMODE_CLIP               = (DICT_MODE_UNDERRUN_ERROR | DICT_MODE_OVERRUN_ERROR | DICT_MODE_MAP_NEAREST)
    """Shortcut, just for convenience. Clip mode maps to the nearest possible key,
    but generates errors for underruns and overruns.
    """
    
    DICT_STDMODE_DOWN               = (DICT_MODE_UNDERRUN_MAP | DICT_MODE_OVERRUN_MAP | DICT_MODE_MAP_NEAREST_LOWER)
    """Shortcut, just for convenience. Downward mode rounds down to the nearest key
    and maps underruns and overruns without errors.
    """
    
    DICT_STDMODE_UP                 = (DICT_MODE_UNDERRUN_MAP | DICT_MODE_OVERRUN_MAP | DICT_MODE_MAP_NEAREST_HIGHER)
    """Shortcut, just for convenience. Upward mode rounds up to the nearest key
    and maps underruns and overruns without errors.
    """
    
    DICT_STDMODE_STRICT             = (DICT_MODE_UNDERRUN_ERROR | DICT_MODE_OVERRUN_ERROR | DICT_MODE_MAP_STRICTLY)
    """Shortcut, just for convenience. Strict mode just maps to the matching key
    and generates errors for all values that are not in the dictionary.
    """
    
    def __init__(self, myMap = {}, mode = DICT_STDMODE_NORMAL):
        self.mode = mode
        self.entry = myMap
        val = sorted( self.entry.values() )
        self.minValue = val[0]
        self.maxValue = val[-1]
        
    def getValue(self, inKey):
        """Given a key, retrieves the corresponding value.
        
        The first key in the dictiionary exactly matching the given
        argument, delivers the value returned by this function. If no
        matching key is found, an error is returned.
        
        :param int inKey: Key value for which to find the corresponding value.
        :return: The key's value and an error code indicating either success or the reason of failure.
        :rtype: int, ErrorCode
        """
        value = None
        result = ErrorCode.errOk
        try:
            value = self.entry[inKey]
        except LookupError:
            result = ErrorCode.errSpecRange
        return value, result
    
    def findKey(self, value):
        """Given a value, finds the (nearest) key according to the dictionary's mode.
        
        The value-to-key mapping behavior can be controlled by the
        dictionary mode as defined during object construction.
        
        :param int value: The value for which to find the corresponding key.
        :return: The key and an error code indicating either success or the reason of failure.
        :rtype: int, ErrorCode
        """
        result = ErrorCode.errOk
        key = None
        if ( value < self.minValue ):
            if ((self.mode & dictionary.DICT_MODE_UNDERRUN) == dictionary.DICT_MODE_UNDERRUN_ERROR):
                result = ErrorCode.errSpecRange
            else:
                key = [k for k, v in self.entry.items() if v == self.minValue]
        elif (value > self.maxValue):
            if ((self.mode & dictionary.DICT_MODE_OVERRUN) == dictionary.DICT_MODE_OVERRUN_ERROR):
                result = ErrorCode.errSpecRange
            else:
                key = [k for k, v in self.entry.items() if v == self.maxValue]
        elif (len(self.entry) == 1):
            key = self.entry.keys()[0]
        else:
            if ((self.mode & dictionary.DICT_MODE_MAP) == dictionary.DICT_MODE_MAP_STRICTLY):
                key = [k for k, v in self.entry.items() if v == value]
            elif ((self.mode & dictionary.DICT_MODE_MAP) == dictionary.DICT_MODE_MAP_NEAREST_LOWER):
                for k, v in self.entry.items():
                    if (v <= value) and ((key is None) or (v > self.entry[key])):
                        key = k
            elif ((self.mode & dictionary.DICT_MODE_MAP) == dictionary.DICT_MODE_MAP_NEAREST_HIGHER):
                for k, v in self.entry.items():
                    if (v >= value) and ((key is None) or (v < self.entry[key])):
                        key = k
            elif ((self.mode & dictionary.DICT_MODE_MAP) == dictionary.DICT_MODE_MAP_NEAREST):
                for k, v in self.entry.items():
                    if ((key is None) or (abs(v-value) < abs(self.entry[key]-value))):
                        key = k
            if key is None:
                result = ErrorCode.errSpecRange
        return key, result
    