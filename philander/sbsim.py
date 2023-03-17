from Module import Module
from enum import unique, Enum, auto
from dataclasses import dataclass
from systypes import ErrorCode

class sbsim( Module ):
    
    def readRegByte( self, aReg ):
        pass

    def writeRegByte( self, aReg, data ):
        pass

    def readRegWord( self, aReg ):
        lo = self.readRegByte(aReg)
        hi = self.readRegByte(aReg+1)
        return ((hi << 8) | lo)

    def writeRegWord( self, aReg, data ):
        bVal = data & 0xFF
        self.writeRegByte(aReg, bVal)
        bVal = (data >> 8) & 0xFF
        self.writeRegByte(aReg+1, bVal)
        return None

    def readRegDWord( self, aReg ):
        L = self.readRegWord( aReg )
        H = self.readRegWord( aReg+2 )
        ret = (H << 16) + L
        return ret

    def writeRegDWord( self, aReg, data ):
        L = data & 0xFFFF
        H = (data & 0xFFFF0000) >> 16
        self.writeRegWord( aReg, L )
        self.writeRegWord( aReg+2, H )
        return None
    
    def readRegBlock( self, aReg, num ):
        data = [0] * num
        for idx in range(num):
            data[idx] = self.readRegByte(aReg+idx)
        return data

    def writeRegBlock( self, aReg, data ):
        for idx in range( len(data) ):
            self.writeRegByte(aReg+idx, data[idx])
        return None


class sbsimNull( sbsim ):
    
    DEFAULT_READING = 0x42
    
    @classmethod
    def Params_init(cls, paramDict):
        paramDict["sbsimNull.reading"] = paramDict.get("sbsimNull.reading", sbsimNull.DEFAULT_READING)
        
    def open( self, paramDict ):
        paramDict["sbsimNull.reading"] = paramDict.get("sbsimNull.reading", sbsimNull.DEFAULT_READING)
        self._reading = paramDict["sbsimNull.reading"]
        return ErrorCode.errOk
            
    def readRegByte( self, aReg ):
        del aReg
        return self._reading

    def writeRegByte( self, aReg, data ):
        pass
    


@unique
class RegType(Enum):
    rtROM   = auto()
    rtRAM   = auto()
    rtNVM   = auto()
    rtVOLATILE  = auto()
    
@dataclass
class Register:
    address:    int
    content:    int
    type:       RegType

    def __init__(self, adr, cont=0, typ=RegType.rtRAM):
        self.address = adr
        self.content = cont
        self.type = typ


    
class sbsimMemory( sbsim ):
    
    def __init__(self, regs):
        self._regs = regs
    
    def _findReg(self, aReg):
        reg = None
        for r in self._regs:
            if r.address==aReg:
                reg = r
                break
        return reg
    
    def open( self, paramDict ):
        del paramDict
        return ErrorCode.errOk
            
    def updateVolatileOnRead(self, reg):
        reg.content = reg.content + 1
        return None
    
    def updateOnWrite(self, reg, newData):
        reg.content = newData
        return None
    
    def readRegByte( self, aReg ):
        reg = self._findReg(aReg)
        if (reg is None):
            result = 0
        else:
            result = reg.content
            if (reg.type == RegType.rtVOLATILE):
                self.updateVolatileOnRead( reg )
        return result

    def writeRegByte( self, aReg, data ):
        reg = self._findReg(aReg)
        if not (reg is None):
            if (reg.type == RegType.rtRAM):
                self.updateOnWrite(reg, data)
        return None
    