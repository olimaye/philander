"""Generic interface to describe the capabilities of an event or interrupt source..

This is an abstract base class to define common methods for enabling and
disabling events as well as for managing event information. Further,
helper classes useful for constructing and interpreting event context
information are part of this module.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Event, EventContextControl, EventContext, Interruptable"]

from dataclasses import dataclass
from enum import Enum, auto, unique
from pymitter import EventEmitter
from systypes import ErrorCode

@unique
class Event(Enum):
    evtNone   = auto()
    evtAny	  = auto()
    evtInt1   = auto()
    evtInt2   = auto()


@unique
class EventContextControl(Enum):
    evtCtxtCtrl_clearAll    = auto()
    evtCtxtCtrl_getFirst    = auto()
    evtCtxtCtrl_getNext     = auto()
    evtCtxtCtrl_getLast     = auto()
    evtCtxtCtrl_getPrevious = auto()

@dataclass
class EventContext:
    control:    EventContextControl = EventContextControl.evtCtxtCtrl_getFirst
    remainInt:  int = 0

    def __init__(self):
        pass


class Interruptable:

    def __init__(self):
        self.eventEmitter = EventEmitter()
        self.dictFeedbacks = dict()
            
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
    def registerInterruptHandler(self, onEvent=None, callerFeedBack=None, handler=None ):
        ret = ErrorCode.errOk
        if (handler is None):
            if (onEvent is None) or (onEvent == Event.evtNone):
                # Disable; from hardware to app.
                ret = self.disableInterrupt()
                self.eventEmitter.off_all()
            else:
                self.dictFeedbacks[onEvent] = callerFeedBack
        elif (onEvent is None) or (onEvent == Event.evtNone):
            self.eventEmitter.off_any( handler )
            if (len(self.eventEmitter.listeners_all()) < 1):
                self.disableInterrupt()
        else:
            # Enable; from app (=sink) to hardware (=source)
            if (onEvent == Event.evtAny):
                self.eventEmitter.on_any( handler )
                ret = self.enableInterrupt()
                if (ret == ErrorCode.errOk):
                    self.dictFeedbacks[onEvent] = callerFeedBack
                else:
                    self.disableInterrupt()
                    self.eventEmitter.off_any( handler )
            else:
                self.eventEmitter.on( onEvent, handler )
                ret = self.enableInterrupt()
                if (ret == ErrorCode.errOk):
                    self.dictFeedbacks[onEvent] = callerFeedBack
                else:
                    self.disableInterrupt()
                    self.eventEmitter.off( onEvent, handler )
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
    
    #
    #
    #
    def fire(self, event, *args):
        if (event in self.dictFeedbacks):
            fb = self.dictFeedbacks[event]
        elif (not(event is None)) and (event != Event.evtNone) and (Event.evtAny in self.dictFeedbacks):
            fb = self.dictFeedbacks[Event.evtAny]
        else:
            fb = None
        self.eventEmitter.emit( event, fb, args )
        return None