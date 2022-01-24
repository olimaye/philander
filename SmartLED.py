from periphery import GPIO, PWM
from threading import Thread
import time

class SmartLED():
    
    CURVE_HARTBEAT = [1, 0, 1, 0.7, 0.4, 0.2, 0, 0, 0, 0]
    CURVE_BLINK_CLASSIC = [True, False]
    
    CYCLEN_SLOW   = 2
    CYCLEN_NORMAL = 1
    CYCLEN_FAST   = 0.4

    def __init__(self, chip='/dev/gpiochip0', pin=None, channel=None,
                active_high=True, initial_value=False, frequency=100):
        self.gpio = None
        self.pwm = None
        self.worker = None
        self.done = False
        self.active_high = active_high
        if pin:
            self.gpio = GPIO( chip, pin, 'out', inverted=not active_high )
            self.gpio.write( initial_value )
        else:
            self.pwm = PWM( chip, channel )
            #if not active_high:
            #    self.pwm.polarity = 'inversed'
            self.pwm.frequency = frequency
            self.pwm.enable()
            self.write( initial_value )
            
    def write(self, brightness):
        if self.gpio:
            self.gpio.write( brightness!=0 )
        elif self.pwm:
            if self.active_high:
                self.pwm.duty_cycle = brightness
            else:
                self.pwm.duty_cycle = 1-brightness
            
    def on(self):
        self.stop_blinking()
        self.write(1)
        
    def off(self):
        self.stop_blinking()
        self.write(0)

    def close(self):
        self.off()
        if self.gpio:
            self.gpio.close()
        elif self.pwm:
            self.pwm.close()
        self.gpio = None
        self.pwm = None

    def blink(self, curve=CURVE_BLINK_CLASSIC, cycle_length=CYCLEN_NORMAL, num_cycles=None):
        self.stop_blinking()
        self.worker = Thread( target=self._blinkingLoop, name='Blinker',
                              args=(curve, cycle_length, num_cycles) )
        self.worker.start()
    
    def stop_blinking(self):
        if self.worker:
            if self.worker.is_alive():
                self.done = True
                self.worker.join()
            self.worker = None
            
            
    def _blinkingLoop(self, curve, cycle_length, num_cycles):
        self.done = False
        delay = cycle_length / len( curve )
        if num_cycles:
            for _ in range( num_cycles ):
                for value in curve:
                    self.write( value )
                    time.sleep( delay ) 
                if self.done:
                    break
        else:
            while not self.done:
                for value in curve:
                    self.write( value )
                    time.sleep( delay ) 
        
        