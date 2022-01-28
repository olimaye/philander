from pymitter import EventEmitter
from periphery import GPIO
from threading import Thread
import logging

class SmartButton( EventEmitter ):

    _POLL_TIMEOUT = 1
    _DEBOUNCE_MS  = 2000
    
    def __init__(self, chip='/dev/gpiochip0', pin=None, active_high=True, label='Button' ):
        self.gpio = None
        self.worker = None
        self.done = False
        self.active_high = active_high
        self.gpio = GPIO( chip, pin, 'in', inverted=not active_high, label=label )
        if active_high:
            self.gpio.edge='rising'
        else:
            self.gpio.edge='falling'
        logging.debug('SmartButton <%s> created, chip:%s, pin:%s, actHigh:%s.', label, chip, pin, active_high)
        EventEmitter.__init__( self )
            
            
    def read(self):
        value = self.gpio.read()
        logging.debug('Reading SmartButton <%s> returns %s.', self.gpio.label, value)
        return value
    
    def poll(self, timeout=None):
        value = self.gpio.poll(timeout)
        logging.debug('Polling SmartButton <%s> returns %s.', self.gpio.label, value)
        return value
    
    def close(self):
        self.stop_waiting()
        logging.debug('SmartButton <%s> closed.', self.gpio.label)
        self.gpio.close()

    def setLabel(self, label):
        logging.debug('Renaming SmartButton <%s> into <%s>.', self.gpio.label, label)
        self.gpio.label = label
        
    def asyncWait4Press(self):
        self.stop_waiting()
        self.worker = Thread( target=self._waitingLoop, name='Wait4Button' )
        self.worker.start()
    
    def stop_waiting(self):
        if self.worker:
            if self.worker.is_alive():
                self.done = True
                self.worker.join()
            self.worker = None
        
    def _waitingLoop(self):
        logging.debug('SmartButton <%s> starts waiting thread.', self.gpio.label)
        self.done = False
        lastTime = 0
        while not self.done:
            value = self.gpio.poll( SmartButton._POLL_TIMEOUT )
            if value:
                evt = self.gpio.read_event()
                if (evt.timestamp - lastTime) > SmartButton._DEBOUNCE_MS * 1000000:
                    lastTime = evt.timestamp
                    logging.debug('SmartButton <%s> consumed event %s.', self.gpio.label, evt)
                    self.emit( self.gpio.label )
        logging.debug('SmartButton <%s> terminates waiting thread.', self.gpio.label)
        
