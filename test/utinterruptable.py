"""
"""
import unittest
import time

from philander.interruptable import Event, EventContext, EventContextControl, Interruptable
from philander.sysfactory import SysFactory, SysProvider
from philander.systypes import ErrorCode

globEvent = None

class MySource( Interruptable ):

    def __init__(self):
        super().__init__()
        self.isEnabled = False
        
    def enableInterrupt(self):
        self.isEnabled = True
        return ErrorCode.errOk
    
    def disableInterrupt(self):
        self.isEnabled = False
        return ErrorCode.errOk
    
    def getEventContext(self, event, context):
        ret = ErrorCode.errOk
        if event in [Event.evtInt1, Event.evtInt2, Event.evtAny]:
            if context.control == EventContextControl.getFirst:
                context.control = EventContextControl.getNext
                context.remainInt = 0x0F
                ret = ErrorCode.errMoreData
            elif context.control == EventContextControl.getLast:
                context.control = EventContextControl.getPrevious
                context.remainInt = 0x0F
                ret = ErrorCode.errMoreData
            elif context.control in [EventContextControl.getNext, EventContextControl.getPrevious]:
                if context.remainInt > 1:
                    context.remainInt = context.remainInt >> 1
                    ret = ErrorCode.errMoreData
                elif context.remainInt > 0:
                    context.remainInt = 0
                    ret = ErrorCode.errOk
                else:
                    ret = ErrorCode.errFewData
            elif context.control == EventContextControl.clearAll:
                    context.remainInt = 0
                    ret = ErrorCode.errOk
        else:
            ret = ErrorCode.errInvalidParameter
        return ret


def handlingRoutine( event, feedback, *args ):
    global globEvent
    # print("Handler called. event=", event, "feedback=", feedback)
    # if len(args) > 0:
    #     print("Additional arguments:")
    #     for a in args: print(a)
    globEvent = event
    del feedback, args
    return None

    
class TestInterruptable( unittest.TestCase ):
    
    def test_events(self):
        src = MySource()
        global globEvent
        
        fb = "This is some feedback data."
        globEvent = None
        err = src.registerInterruptHandler( Event.evtInt1, fb, handlingRoutine )
        self.assertEqual( err, ErrorCode.errOk )
        src._fire( Event.evtInt1 )
        start = time.time()
        while (not globEvent) and (time.time()-start < 5): pass
        self.assertIsNotNone( globEvent, "Event didn't fire - timeout!")
        if globEvent:
            context = EventContext()
            self.assertEqual( context.control, EventContextControl.getFirst )
            self.assertEqual( context.remainInt, 0 )
            err = src.getEventContext( globEvent, context)
            self.assertIn( err, [ErrorCode.errMoreData, ErrorCode.errOk] )
            self.assertEqual( context.control, EventContextControl.getNext )
            while err == ErrorCode.errMoreData:
                err = src.getEventContext( globEvent, context)
                self.assertIn( err, [ErrorCode.errMoreData, ErrorCode.errOk] )
                self.assertEqual( context.control, EventContextControl.getNext )
            self.assertEqual( err, ErrorCode.errOk )
            
        
if __name__ == '__main__':
    unittest.main()

