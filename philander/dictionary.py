#
# @file
# <p>
# Copyright 2022 IHP, Frankfurt (Oder), Germany
#
# This code is free software. It is licensed under the EUPL, Version 1.1
# or - as soon they will be approved by the European Commission - subsequent
# versions of the EUPL (the "Licence").
# You may redistribute this code and/or modify it under the terms of this
# License.
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
#
# http://joinup.ec.europa.eu/software/page/eupl/licence-eupl
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the Licence is distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the Licence for the specific language governing permissions and
# limitations under the Licence.
# </p>
# <p>
# Declaration of the types and functions making up the dictionary module.
# A dictionary is meant to translate keys to values, both of them being
# integers.
# For example, a certain configuration register content could be
# translated into its physical data domain by means of a dictionary. The BMA456
# acceleration sensor can adjust its measurement range to +/- 2g, 4g, 8g or
# even 16g by setting its ACC_RANGE register to either 0, 1, 2 or 3,
# respectively. Considering the register content to be the key domain, whereas
# the corresponding range limits are the values, a dictionary would translate
# as follows:
# <table>
# <caption>Mapping between register content and range limits.</caption>
# <tr><th>key</th><th>value</th></tr>
# <tr><td>0</td><td>2000</td></tr>
# <tr><td>1</td><td>4000</td></tr>
# <tr><td>2</td><td>8000</td></tr>
# <tr><td>3</td><td>16000</td></tr>
# </table>
# It is also possible to translate vice-versa, i.e. from the value-domain into
# keys bэ finding the nearest matching key. The behavior of this search
# algorithm can be controlled by the dictionary's <em>mode</em> attribute.
# </p>
# <p>
# Note that at the advantage of runtime speed, this implementation assumes the
# dictionary be sorted by values in ascending order.
# </p>
# @author Oliver Maye, IHP microelectronics
# @date 21.12.2022
#

from systypes import ErrorCode

class dictionary():
    
    #
    # Mnemonics of the dictionary mode to control the backward-search algorithm of
    # finding keys for a given value.
    # 
    
    #
    # Bitmask for the mode particle to define the mapping for values below the
    # lowest value (!) in the dictionary, a so-called underrun.
    # 
    DICT_MODE_UNDERRUN              = 0x01
    #
    # Make values below the lowest value be mapped to the key corresponding to that
    # lowest value.
    # 
    DICT_MODE_UNDERRUN_MAP          = 0x00
    #
    # Values below the lowest value in the dictionary are not mapped, but cause an
    # error when trying to find a matching key.
    # 
    DICT_MODE_UNDERRUN_ERROR        = DICT_MODE_UNDERRUN
    #
    # Bitmask for the mode particle to define the mapping for values above the
    # highest value in the dictionary, a so-called overrun.
    # 
    DICT_MODE_OVERRUN               = 0x02
    #
    # Values above the highest value will be mapped to the key corresponding to
    # that highest value.
    # 
    DICT_MODE_OVERRUN_MAP           = 0x00
    #
    # Values larger than the highest value in dictionary will not be mapped, but
    # cause an error when trying to find a matching key.
    # 
    DICT_MODE_OVERRUN_ERROR         = DICT_MODE_OVERRUN
    #
    # Bitmask for the mode particle to define the mapping for values that are
    # in the range defined by the minimum and maximum values in the dictionary.
    # 
    DICT_MODE_MAP                   = 0x0c
    #
    # Strict mapping: Only those values, that are contained in the dictionary will
    # be mapped to their corresponding keys. Other values will produce errors.
    # 
    DICT_MODE_MAP_STRICTLY          = 0x00
    #
    # Map by rounding down: A value is mapped to the key that corresponds to the
    # largest value, that is smaller than (or equal to) it.
    # 
    DICT_MODE_MAP_NEAREST_LOWER     = 0x04
    #
    # Map by rounding up: A value is mapped to the key that corresponds to the
    # smallest value, that is larger than (or equal to) it.
    # 
    DICT_MODE_MAP_NEAREST_HIGHER    = 0x08
    #
    # Map by ordinary rounding: A value is mapped to the key that corresponds to
    # the nearest value in dictionary.
    # 
    DICT_MODE_MAP_NEAREST           = (DICT_MODE_MAP_NEAREST_LOWER | DICT_MODE_MAP_NEAREST_HIGHER)
    
    #
    # Shortcut, just for convenience. Normal mode maps to the nearest possible key,
    # as well as underruns and overruns without errors.
    # 
    DICT_STDMODE_NORMAL             = (DICT_MODE_UNDERRUN_MAP | DICT_MODE_OVERRUN_MAP | DICT_MODE_MAP_NEAREST)
    #
    # Shortcut, just for convenience. Clip mode maps to the nearest possible key,
    # but generates errors for underruns and overruns.
    # 
    DICT_STDMODE_CLIP               = (DICT_MODE_UNDERRUN_ERROR | DICT_MODE_OVERRUN_ERROR | DICT_MODE_MAP_NEAREST)
    #
    # Shortcut, just for convenience. Downward mode rounds down to the nearest key
    # and maps underruns and overruns without errors.
    # 
    DICT_STDMODE_DOWN               = (DICT_MODE_UNDERRUN_MAP | DICT_MODE_OVERRUN_MAP | DICT_MODE_MAP_NEAREST_LOWER)
    #
    # Shortcut, just for convenience. Upward mode rounds up to the nearest key
    # and maps underruns and overruns without errors.
    # 
    DICT_STDMODE_UP                 = (DICT_MODE_UNDERRUN_MAP | DICT_MODE_OVERRUN_MAP | DICT_MODE_MAP_NEAREST_HIGHER)
    #
    # Shortcut, just for convenience. Strict mode just maps to the matching key
    # and generates errors for all values that are not in the dictionary.
    # 
    DICT_STDMODE_STRICT             = (DICT_MODE_UNDERRUN_ERROR | DICT_MODE_OVERRUN_ERROR | DICT_MODE_MAP_STRICTLY)

    #
    #
    #        
    def __init__(self, myMap = {}, mode = DICT_STDMODE_NORMAL):
        self.mode = mode
        self.entry = myMap
        val = sorted( self.entry.values() )
        self.minValue = val[0]
        self.maxValue = val[-1]
        
    def getValue(self, inKey):
        value = None
        result = ErrorCode.errOk
        try:
            value = self.entry[inKey]
        except LookupError:
            result = ErrorCode.errSpecRange
        return value, result
    
    def findKey(self, value):
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
    