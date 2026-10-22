"""Integer mathematics helper functions.

Provide mathematical functions implementing bit-twiddling hacks, such as
ispowtwo, iprevpowtwo and vlbs or ffs.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["bswap16", "bswap32", "wswap32", 
           "ctz", "ffs", "ispowtwo", "iprevpowtwo", "vlbs"]

def bswap16( x: int ):
    """Swap bytes, reverse byte order in least-significant word
    
    The byte series A-B is converted to B-A.
    For example, a value of 0x1234 is transformed to 0x3412.

    :param int x: The argument to operate on.
    :return: The argument in reverse byte order.
    :rtype: int
    """
    return ((x & 0xFF00) >> 8) | ((x & 0xFF) << 8)


def bswap32( x: int ):
    """Swap bytes, reverse byte order in least-significant d-word.
    
    The byte series A-B-C-D is converted to D-C-B-A.
    So, a value of 0x12345678 is transformed to 0x78563412.

    :param int x: The argument to operate on.
    :return: The argument in reverse byte order.
    :rtype: int
    """
    return ( ((x & 0xFF000000) >> 24) | ((x & 0x00FF0000) >> 8) | \
             ((x & 0x0000FF00) << 8)  | ((x & 0x000000FF) << 24))

def wswap32( x: int ):
    """Swap words, while maintaining byte-order.
    
    The byte series A-B-C-D is converted to C-D-A-B.
    So, a value of 0x12345678 is transformed to 0x56781234.

    :param int x: The argument to operate on.
    :return: The argument in reverse byte order.
    :rtype: int
    """
    return ((x & 0xFFFF0000) >> 16) | ((x & 0x0000FFFF) <<16)

def ctz( x: int ):
    """Count trailing zeroes.
    
    Count the number of zero-bits following the least-significant set bit.
    Note that ffs(x) = ctz(x) + 1. To maintain this relation when the
    argument is zero, this function returns -1 in this case.

    Example: For x=24 the result is 3. For x=25 the result is 0.

    :param int x: The input argument, interpreted as an unsigned integer.
    :return: The number of trailing zeroes after the least-significant set bit.
    :rtype: int
    """
    ret = 0
    if x==0:
        ret = -1
    else:
        mask = 1
        while not (x & mask):
            ret = ret + 1
            mask = mask << 1
    return ret

def ffs( x: int ):
    """Find first set.
    
    Finds the first, i.e. least-significant bit set and returns its
    index number, where counting starts from 1.
    For an input of zero, the result is zero, by definition.
    Note that ffs(x) = ctz(x) + 1.

    Example: For x=24 the result is 4. For x=25 the result is 1.

    :param int x: The input argument, interpreted as an unsigned integer.
    :return: The one-based position index of the least-significant set bit.
    :rtype: int
    """
    ret = 0
    if (x == 0):
        ret = 0
    else:
        ret = ctz(x) + 1
    return ret

def ispowtwo( x: int ):
    """Checks if the argument is a power of two, i.e. has exactly one bit set.
    
    Note that one (1) is considered a power of two, while zero (0) is not.
    
    Example: For x=32 the result is True. For x=47 the result is False.
    
    :param int x: The argument to check, interpreted as an unsigned integer.
    :return: True, if the argument is a power of two, False otherwise.
    :rtype: Boolean
    """
    return (x and not(x & (x - 1)))

def iprevpowtwo( n: int ):
    """Gives the previous power of two for the given argument.
    
    Returns the greatest power of two, that is less than or equal to the
    provided argument. For zero, the function returns zero.
    
    Example: For n=32 the result is 32. For n=47 the result is 32, too.
    
    :param int n: The argument, interpreted as an unsigned integer.
    :return: The previous power of two for that argument, or zero if n=0.
    :rtype: int
    """
    if (n > 0 ):
        ndx = 0
        while ( 1 < n ):
            n = ( n >> 1 )
            ndx += 1
        ret = 1 << ndx
    else:
        ret = 0
    return ret

def vlbs( x: int ):
    """For a given integer, find the value of the least bit set.

    If no bit of the argument is set, i.e. for zero (0), the result is
    zero (0). Otherwise, the result is a bit *value* and not a bit
    number! That's why, the return value is  always a power of two - or zero.
    
    Example: For x=32 the result is 32. For x=47 the result is 1.
    
    :param int x: The input argument, interpreted as an unsigned integer.
    :return: The value of the least bit set, or zero.
    :rtype: int
    """
    return (x & (~x + 1))
