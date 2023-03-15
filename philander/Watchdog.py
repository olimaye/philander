from Interruptable import Interruptable
from Configurable import Configurable

class Watchdog( Interruptable, Configurable ):

    # Interrupts
    INT_WATCHDOG      = 0x0101 # Watchdog elapsed.

    #
    # Configurable API
    #
    
    def _scanParameters( self, paramDict ):
        # Scan parameters
        if "Watchdog.Interval" in paramDict:
            self.interval = self._detectDriverModule( paramDict["Watchdog.Interval"] )
                                

    #
    # Initializes the object.
    # The only input parameter is a dictionary containing key-value pairs that
    # configure the instance. 
    # 
    def __init__( self, paramDict ):
        # This class parameter

        # initialize local attributes
        self.interval = 0;
        Configurable.__init__( self, paramDict )

    #
    # Initializes the WATCHDOG module. Must be called once, before the features of
    # this module can be used.
    #
    def init(self):
        Interruptable.init(self)
        Configurable.init(self)

    # 
    # Shuts down the WATCHDOG module safely.
    #
    def close(self):
        Interruptable.close(self)
        #Configurable.close(self)

    #
    # Enables and restarts the watchdog.
    #
    def enable(self):
        pass
    
    #
    # Disables the watchdog and stops it from runninng, immediately.
    #
    def disable(self):
        pass
    
    #
    # Checks, whether the watchdog is currently running or not.
    # @return TRUE, if the watchdog is running, FALSE otherwise.
    #
    def isRunning(self):
        pass

    # 
    # Clears the watchdog. This is the implementation of the acknowledge mechanism.
    # Calling this function is necessary for an application to prevent from watchdog event.
    # Note that it does not start the timer, e.g. when disabled.
    #
    def clear(self):
        pass

    #
    # Checks, whether the configured time interval has expired, or not. By calling
    # this function, an application may observe the expiration without using the
    # interrupt mechanism.
    # For the time interval to elapse, the counter must be enabled!
    # Note, that without interrupts, this flag is not cleared automatically. The
    # caller would have to use #watchdogClearElapsed for this purpose.
    # @return FASLE, if the time is not yet elapsed. TRUE, if the configured time
    # is over.
    # @see #clearElapsed
    #
    def isElapsed(self):
        pass

    #
    # Clears the elapsed flag. The application should call this function after it
    # observed that the configured time expired. When using interrupts, this flag
    # is reset automatically.
    # @see #isElapsed
    #
    def clearElapsed(self):
        pass
    
