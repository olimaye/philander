from pymitter import EventEmitter

class EventPublisher:

    eventEmitter = None
    
    #
    # Initializes the object.
    #
    def init(self):
        self.eventEmitter = EventEmitter()

    #
    # Just closes the object.
    #
    def close(self):
        if not self.eventEmitter is None:
            self.eventEmitter.off_all()

    #    
    #
    # Gives the status of each interruptp condition, independently of whether
    # the condition is registered as a source of notification, or not.
    #
    def getIntStatus(self):
        pass
