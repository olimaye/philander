"""Generic interface to describe the capabilities of a module.

This is an abstract base class to define methods for ramp-up, shut-down
or switch into certain run level, that are common to each class on
module-level.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Module"]

class Module:
    
    @classmethod
    def Params_init(cls, paramDict):
        """Initialize parameters with their defaults.

        The given dictionary should not be None, on entry.
        Options not present in the dictionary will be added and set to
        their defaults on return.
        
        :param dict(str, object) paramDict: Dictionary mapping option names to their respective values.
        :returns: none
        :rtype: None
        """
        pass

    def open(self, paramDict):
        """Opens the instance and sets it in a usable state.

        Allocate necessary hardware resources and configure
        user-adjustable parameters to meaningful defaults.
        This function must be called prior to any further usage of the
        instance. Involving it in the system ramp-up procedure could be
        a good choice. After usage of this instance is finished, the
        application should call :meth:`close`.
        
        :param dict(str, object) paramDict: Configuration parameters as obtained from :meth:`Params_init`, possibly.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        pass

    def close(self):
        """Closes this instance and releases associated hardware resources.

        This is the counterpart of :meth:`open`. Upon return, further
        usage of this instance is prohibited and may lead to unexpected
        results. The instance can be re-activated by calling :meth:`open`,
        again.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        pass

    def setRunLevel(self, level):
        """Select the power-saving operation mode.

        Switches the instance to one of the power-saving modes or
        recovers from these modes. Situation-aware deployment of these
        modes can greatly reduce the system's total power consumption.
        
        :param RunLevel level: The level to switch to.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del level
        pass
    