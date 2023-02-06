class Device:
    
    BITS_NONE = 0
    BITS_ALL  = 0xFFFF
    
    #
    # Retrieves a byte register content
    #
    def getReg( self, register ):
        pass
    
    #
    # Writes new content to a byte register
    #
    def setReg( self, register, data ):
        pass
    
    #
    # Modifies the content of a byte register by setting (enabling) and clearing (disabling)
    # the specified bits. All other bits are left untouched.
    # enMask: The bits to set (enable).
    # disMask: The bits to clear (disable).
    # If bits are specified in both masks, the behaviour is undefined for those bits. It's up
    # to the implementation executing one or the other.
    #
    def modReg( self, register, enMask, disMask ):
        if (enMask!=0) or (disMask!=0):
            cnt = self.getReg( register )
            newCnt = (cnt | enMask) & ~disMask
            if newCnt != cnt:
                self.setReg( register, newCnt )
    
    #
    # Enables (sets) the given bits in a byte register.
    #
    def enableReg( self, register, mask ):
        if mask != 0 :
            cnt = self.getReg( register )
            newCnt = cnt | mask
            if newCnt != cnt:
                self.setReg( register, newCnt )
    
    #
    # Disables (resets, clears) the given bits in a byte register.
    #
    def disableReg( self, register, mask ):
        if mask != 0 :
            cnt = self.getReg( register )
            newCnt = cnt & ~mask
            if newCnt != cnt:
                self.setReg( register, newCnt )
    
    #
    # Copies the given bits to a byte register. Bits cleared
    # in the content parameter are reset in the register. And
    # bits set in the content, are also set in the regiser.
    # mask Marks the bits to copy
    # content The content to copy.
    #
    def copyReg( self, register, mask, content ):
        if mask != 0 :
            cnt = self.getReg( register )
            newCnt = (cnt & ~mask) | (content & mask)
            if newCnt != cnt:
                self.setReg( register, newCnt )
    
    #
    # Retrieves a wide register content (word, 16 bit)
    #
    def getWReg( self, register ):
        lo = self.getReg( register )
        hi = self.getReg( register+1 )
        data = (hi << 8) | lo
        return data
    
    #
    # Writes new content to a wide register (word, 16 bit)
    #
    def setWReg( self, register, data ):
        lo = data & 0xFF
        hi = data >> 8
        self.setReg( register, lo )
        self.setReg( register+1, hi )
        pass
    
    #
    # Modifies the content of a wide register by setting (enabling) and clearing (disabling)
    # the specified bits. All other bits are left untouched.
    #
    def modWReg( self, register, enMask, disMask ):
        if (enMask!=0) or (disMask!=0):
            cnt = self.getWReg( register )
            newCnt = (cnt | enMask) & ~disMask
            if newCnt != cnt:
                self.setWReg( register, newCnt )
    
    #
    # Enables (sets) the given bits in a wide register.
    #
    def enableWReg( self, register, mask ):
        if mask != 0 :
            cnt = self.getWReg( register )
            newCnt = cnt | mask
            if newCnt != cnt:
                self.setWReg( register, newCnt )
    
    #
    # Disables (resets, clears) the given bits in a wide register.
    #
    def disableWReg( self, register, mask ):
        if mask != 0 :
            cnt = self.getWReg( register )
            newCnt = cnt & ~mask
            if newCnt != cnt:
                self.setWReg( register, newCnt )

    #
    # Copies the given bits to a word register. Bits cleared
    # in the content parameter are reset in the register. And
    # bits set in the content, are also set in the regiser.
    # mask Marks the bits to copy
    # content The content to copy.
    #
    def copyWReg( self, register, mask, content ):
        if mask != 0 :
            cnt = self.getWReg( register )
            newCnt = (cnt & ~mask) | (content & mask)
            if newCnt != cnt:
                self.setWReg( register, newCnt )
    
