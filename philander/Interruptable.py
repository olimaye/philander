from pymitter import EventEmitter
from enum import Enum, auto, unique
from systypes import ErrorCode


@unique
class EventContextControl(Enum):
    evtCtxtCtrl_clearAll    = auto()
    evtCtxtCtrl_getFirst    = auto()
    evtCtxtCtrl_getNext     = auto()
    evtCtxtCtrl_getLast     = auto()
    evtCtxtCtrl_getPrevious = auto()


class Interruptable:

    def __init__(self):
        self.eventEmitter = EventEmitter()
    

    @classmethod
    def Params_init(cls, paramDict):
        if not ("Interruptable.int1.gpio" in paramDict):
            paramDict["Interruptable.int1.gpio"] = 0
        if not ("Interruptable.int2.gpio" in paramDict):
            paramDict["Interruptable.int2.gpio"] = 0
        if not ("Interruptable.handler" in paramDict):
            paramDict["Interruptable.handler"] = None
        
    #
    # Just closes the object.
    #
    def close(self):
        if not self.eventEmitter is None:
            self.eventEmitter.off_all()


    # Registers for interrupt notification.
    # The mask specifies the interrupts of interest.
    # The given handler will be called upon occurrence
    # of the interrupts specified.
    #
    def registerInterruptHandler(self, handler=None ):
        ret = ErrorCode.errOk
        if (handler is None):
            # Disable; from hardware to app.
            ret = self.disableInterrupt()
            self.eventEmitter.off_all()
        else:
            # Enable; from app (=sink) to hardware (=source)
            self.eventEmitter.on_any( handler )
            ret = self.enableInterrupt()
            if (ret != ErrorCode.errOk):
                self.eventEmitter.off_any( handler )
                self.disableInterrupt()
        return ret;

    #
    #
    #
    def enableInterrupt(self):
        pass
    
    #
    #
    #
    def disableInterrupt(self):
        pass
    
    #
    # Gives the status of each interrupt condition, independently of whether
    # the condition is registered as a source of notification, or not.
    #
    def getEventContext(self, event, context):
        pass
    
