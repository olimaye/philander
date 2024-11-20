"""Module to provide access to and control over LEDs.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["LED"]

import time, logging

from .gpio import GPIO
from .module import Module
from .sysfactory import SysFactory
from .systypes import ErrorCode


class LED( Module ):
    """Generic LED driver class.
    """
    
    CURVE_HARTBEAT = [1, 0, 1, 0.7, 0.4, 0.2, 0, 0, 0, 0]
    CURVE_BLINK_CLASSIC = [1, 0]
    
    CYCLEN_SLOW   = 2
    CYCLEN_NORMAL = 1
    CYCLEN_FAST   = 0.4

    LABEL_DEFAULT = "LED"

    def __init__(self):
        """Initialize the instance with defaults.
        """
        self.gpio = None
        self.worker = None
        self.workerDone = False
        self.label = LED.LABEL_DEFAULT
        self._timer = None
        self._cyclesLeft = None
        self._curve = None
        self._curveItem = 0

    #
    # Module API
    #

    @classmethod
    def Params_init(cls, paramDict):
        """Initializes configuration parameters with defaults.
        
        The following settings are supported:
        
        =============================    =====================================================================================================
        Key name                         Value type, meaning and default
        =============================    =====================================================================================================
        LED.label                        ``str``; A descriptive string label; :attr:`LABEL_DEFAULT`.
        All LED.gpio.* settings as documented at :meth:`.GPIO.Params_init`.
        ======================================================================================================================================
        
        Also see: :meth:`.Module.Params_init`, :meth:`.GPIO.Params_init`.
        """

        if not ("LED.label" in paramDict):
            paramDict["LED.label"] = LED.LABEL_DEFAULT
        paramDict["LED.gpio.direction"] = GPIO.DIRECTION_OUT
        gpioParams = {}
        GPIO.Params_init( gpioParams )
        for key, value in gpioParams.items():
            bkey = "LED." + key
            if not( bkey in paramDict):
                paramDict[bkey] = value
        return None

    def open(self, paramDict):
        ret = ErrorCode.errOk
        if not (self.gpio is None):
            ret = ErrorCode.errResourceConflict
        else:
            defaults = {}
            LED.Params_init(defaults)
            self.label = paramDict.get( "LED.label", defaults["LED.label"] )
            # Overwrite the direction parameter
            paramDict["LED.gpio.direction"] = defaults["LED.gpio.direction"]
            # Extract GPIO parameters
            gpioParams = dict( [(k.replace("LED.", ""),v) for k,v in paramDict.items() if k.startswith("LED.")] )
            self.gpio = SysFactory.getGPIO()
            ret = self.gpio.open(gpioParams)
            if( ret != ErrorCode.errOk ):
                self.gpio = None
            #else:
                # self.pwm = PWM( chip, channel )
                # self.pwm.frequency = frequency
                # self.pwm.enable()
        logging.debug('LED <%s> opened, returns: %s.', self.label, ret)
        return ret
    
    def close(self):
        ret = ErrorCode.errOk
        self.off()
        if self.gpio:
            ret = self.gpio.close()
            self.gpio = None
        logging.debug('LED <%s> closed.', self.label)
        return ret
    
    #
    # LED specific API
    #
    
    def set(self, brightness):
        if self.gpio:
            if (brightness < 0.5):
                self.gpio.set( GPIO.LEVEL_LOW )
            else:
                self.gpio.set( GPIO.LEVEL_HIGH )
        # elif self.pwm:
        #     self.pwm.duty_cycle = brightness
        logging.debug('LED <%s> set to %s.', self.label, brightness)
            
    def on(self):
        self.stop_blinking()
        self.set(1)
        logging.debug('LED <%s> switched ON.', self.label)
        
    def off(self):
        self.stop_blinking()
        self.set(0)
        logging.debug('LED <%s> switched OFF.', self.label)

    def blink(self, curve=CURVE_BLINK_CLASSIC, cycle_length=CYCLEN_NORMAL, num_cycles=None):
        if( not(curve is None) and (len(curve)>0) and
            (cycle_length>0) and
            ((num_cycles is None) or (num_cycles > 0)) ):
            self.stop_blinking()
            # On MicroPython, use its distinct timer features
            if self.gpio._implpak == GPIO._IMPLPAK_MICROPYTHON:
                from machine import Timer
                self._timer = Timer()
                self._cyclesLeft = num_cycles
                self._curve = curve
                self._curveItem = 0
                self.workerDone = False
                self._timer.init( period= (cycle_length*1000 + len(curve)//2) // len( curve ),
                                  mode= Timer.PERIODIC,
                                  callback= self._mpBlinkingLoop )
                logging.debug('LED <%s> starts blinking timer, cycle_length=%s.', self.label, cycle_length)
            else:   # Full Python on SBC and alike
                from threading import Thread
                self.worker = Thread( target=self._blinkingLoop, name='Blinker',
                                      args=(curve, cycle_length, num_cycles) )
                self.worker.start()
    
    def stop_blinking(self):
        if self.gpio._implpak == GPIO._IMPLPAK_MICROPYTHON:
            if not (self._timer is None):
                self._timer.deinit()
                self._timer = None
            self.workerDone = True
            logging.debug('LED <%s> stops blinking.', self.label)
        else:   # Full Python on SBC and alike
            if self.worker:
                if self.worker.is_alive():
                    self.workerDone = True
                    self.worker.join()
            self.worker = None
            
            
    def _blinkingLoop(self, curve, cycle_length, num_cycles):
        logging.debug('LED <%s> starts blinking thread, cycle_length=%s.', self.label, cycle_length)
        self.workerDone = False
        delay = cycle_length / len( curve )
        if num_cycles:
            for _ in range( num_cycles ):
                for value in curve:
                    if self.workerDone:
                        break
                    self.set( value )
                    time.sleep( delay ) 
                if self.workerDone:
                    break
        else:
            while not self.workerDone:
                for value in curve:
                    if self.workerDone:
                        break
                    self.set( value )
                    time.sleep( delay ) 
        logging.debug('LED <%s> terminates blinking thread.', self.label)
        
    def _mpBlinkingLoop(self, timer):
        self.set( self._curve[self._curveItem] )
        self._curveItem += 1
        if( self._curveItem >= len(self._curve )) :
            self._curveItem = 0
            if not( self._cyclesLeft is None ) :
                self._cyclesLeft -= 1
                if( self._cyclesLeft < 1 ):
                    self.workerDone = True
        if self.workerDone:
            timer.deinit()
            logging.debug('LED <%s> terminates blinking timer.', self.label)
        
        