"""Integer mathematics helper functions.

Provide mathematical functions implementing bit-twiddling hacks, such as
ispowtwo, iprevpowtwo and vlbs or ffs.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["ispowtwo", "iprevpowtwo", "vlbs"]


def ispowtwo( x ):
    """Checks if the argument is a power of two, i.e. has exactly one bit set.
    
    Note that one (1) is considered a power of two, while zero (0) is not.
    
    Example: For x=32 the result is True. For x=47 the result is False.
    
    :param int x: The argument to check, interpreted as an unsigned integer.
    :return: True, if the argument is a power of two, False otherwise.
    :rtype: Boolean
    """
    return (x and not(x & (x - 1)))

def iprevpowtwo(n):
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

def vlbs(x):
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
