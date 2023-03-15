

def ispowtwo( x ):
    return (x and not(x & (x - 1)))


def iprevpowtwo(n):
    if (n > 0 ):
        ndx = 0
        while ( 1 < n ):
            n = ( n >> 1 )
            ndx += 1
        ret = 1 << ndx
    else:
        ret = 0
    return ret

#
# For a given integer, find the value of the least bit set.
#
def vlbs(x):
    return (x & (~x + 1))
