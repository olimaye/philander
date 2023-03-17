

class Module:
    
    # Abstract function to initialize parameters with its defaults.
    # @param[in, out] params The parameter structure to be initialized. Should not be NULL.
    # @return <code>None</code>
    @classmethod
    def Params_init(cls, params):
        pass

    # Opens a specific instance and sets it in a usable state. Allocates necessary
    # hardware resources and configures user-adjustable parameters to meaningful defaults.
    # This function must be called prior to any further usage of the instance.
    # Involving it in the system ramp-up procedure could be a good choice.
    # After usage of this instance is finished, the application should call
    # #module_close.
    # @param[in] paramDicts The parameters to be used for configuration. If NULL, defaults
    # are applied. This is a dictionary containing key-value pairs that
    # configure the instance.
    # @return An <code>#ErrorCode</code> error code either indicating that this
    # call was successful or the reason why it failed.
    def open(self, paramDict):
        pass

    # Closes this instance and releases associated hardware resources. This is the
    # counterpart of #open.
    # Upon return, further usage of this instance is prohibited and may lead to
    # unexpected results. The instance can be re-activated by calling #open,
    # again.
    # @return <code>None</code>
    def close(self):
        pass

    # Switches the instance to one of the power-saving modes or recovers from
    # these modes. Situation-aware deployment of these modes can greatly reduce
    # the system's total power consumption.
    # @param[in] level <code>#RunLevel</code> The level to switch to.
    # @return An <code>#ErrorCode</code> error code either indicating that this
    # call was successful or the reason why it failed.
    def setRunLevel(self, level):
        pass

    # Initializes all modules that support auto-registration and initialization.
    # @return An <code>#ErrorCode</code> error code either indicating that this
    # call was successful or the reason why it failed.
    @classmethod
    def allInit(cls):
        pass

    # Shuts down safely all modules that support auto-registration and shut down.
    # @return <code>None</code>
    @classmethod
    def allShutdown(cls):
        pass

    # Switches all modules supporting auto-registration into the given
    # run level.
    # @param[in] level <code>#RunLevel</code> The level to switch to.
    # @return An <code>#ErrorCode</code> error code either indicating that this
    # call was successful or the reason why it failed.
    @classmethod
    def allSetRunLevel( cls, level ):
        pass
    
    