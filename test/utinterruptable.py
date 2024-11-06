"""
"""
import unittest
import time

from philander.interruptable import Event, EventContext, EventContextControl, Interruptable
from philander.systypes import ErrorCode

globSemaphore = None

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


def handlingRoutine( feedback, *args ):
    global globSemaphore
    # print("Handler called. event=", event, "feedback=", feedback)
    # if len(args) > 0:
    #     print("Additional arguments:")
    #     for a in args: print(a)
    globSemaphore = feedback
    del args
    return None

    
class TestInterruptable( unittest.TestCase ):
    
    def test_context(self):
        src = MySource()
        global globSemaphore
        
        fb = "This is some feedback data."
        globSemaphore = None
        err = src.registerInterruptHandler( Event.evtInt1, fb, handlingRoutine )
        self.assertEqual( err, ErrorCode.errOk )
        src._fire( Event.evtInt1 )
        start = time.time()
        while (not globSemaphore) and (time.time()-start < 5): pass
        self.assertIsNotNone( globSemaphore, "Event didn't fire - timeout!")
        if globSemaphore:
            self.assertEqual( globSemaphore, fb )
            context = EventContext()
            self.assertEqual( context.control, EventContextControl.getFirst )
            self.assertEqual( context.remainInt, 0 )
            err = src.getEventContext( Event.evtInt1, context)
            self.assertIn( err, [ErrorCode.errMoreData, ErrorCode.errOk] )
            self.assertEqual( context.control, EventContextControl.getNext )
            while err == ErrorCode.errMoreData:
                err = src.getEventContext( Event.evtInt1, context)
                self.assertIn( err, [ErrorCode.errMoreData, ErrorCode.errOk] )
                self.assertEqual( context.control, EventContextControl.getNext )
            self.assertEqual( err, ErrorCode.errOk )
            
    def test_register(self):
        src = MySource()
        global globSemaphore
        
        fb = "My feedback data"
        globSemaphore = None
        err = src.registerInterruptHandler( Event.evtInt1, fb, handlingRoutine )
        self.assertEqual( err, ErrorCode.errOk )
        src._fire( Event.evtInt1 )
        start = time.time()
        while (not globSemaphore) and (time.time()-start < 2): pass
        self.assertIsNotNone( globSemaphore, "Event didn't fire - timeout!")
        
        globSemaphore = None
        src._fire( Event.evtInt2 )
        start = time.time()
        while (not globSemaphore) and (time.time()-start < 2): pass
        self.assertIsNone( globSemaphore, "Event fired - wrong handler!")

        globSemaphore = None
        err = src.registerInterruptHandler( Event.evtNone, None, handlingRoutine )
        self.assertEqual( err, ErrorCode.errOk )
        src._fire( Event.evtInt1 )
        start = time.time()
        while (not globSemaphore) and (time.time()-start < 2): pass
        self.assertIsNone( globSemaphore, "Event fired on de-registered handler!")

        globSemaphore = None
        err = src.registerInterruptHandler( Event.evtInt1, fb, handlingRoutine )
        self.assertEqual( err, ErrorCode.errOk )
        fbAlt = "Alternative feedback"
        err = src.registerInterruptHandler( Event.evtInt1, fbAlt, handlingRoutine )
        self.assertEqual( err, ErrorCode.errOk )
        src._fire( Event.evtInt1 )
        start = time.time()
        while (not globSemaphore) and (time.time()-start < 2): pass
        self.assertIsNotNone( globSemaphore, "Event didn't fire - timeout!")
        self.assertEqual( globSemaphore, fbAlt )
        
        globSemaphore = None
        err = src.registerInterruptHandler( Event.evtNone, fb, None )
        self.assertEqual( err, ErrorCode.errOk )
        src._fire( Event.evtInt1 )
        start = time.time()
        while (not globSemaphore) and (time.time()-start < 2): pass
        self.assertIsNone( globSemaphore, "Event fired on de-registered handler!")
    
    
if __name__ == '__main__':
    unittest.main()

