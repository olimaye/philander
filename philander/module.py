"""Module to provide the ``Module`` base class."""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Module"]

from .systypes import ErrorCode


class Module:
    """Generic interface to describe the capabilities of a module.
    
    This is an abstract base class to define methods for ramp-up, shut-down
    or switch into certain run level, that are common to each class on
    module-level.
    """

    @classmethod
    def _aggregateParams(cls, baseDict, fillerDict, prefix=""):
        """Add entries in `fillerDict` to `baseDict` if not already present.
        
        This is a utility function to enrich the `baseDict` by those
        entries of the `fillerDict` whose key - after prepending the given
        `prefix` - is not already present in the `baseDict`.
        Disregarding the prefix feautre, this function still differs
        from a call like `baseDict.update(fillerDict)` in that, it does
        not overwrite entries in the `baseDict`.
        Let the the `prefix` be "p.", then if `baseDict` contains:
        * "p.A" -> valueA
        * "p.B" -> valueB
        and 'fillerDict' is:
        * "B" -> valueBDifferent
        * "C" -> valueC
        then on return, the `baseDict` will be:
        * "p.A" -> valueA
        * "p.B" -> valueB
        * "p.C" -> valueC
        
        So, the result is more similar to `fillerDict.update(baseDict)`
        except where the aggregated result is stored - and the prefix
        handling.
        This may be important when it comes to manipulating variables
        that are method parameters, such as the `paramDict`
        in :meth:`Params_init`. 

        :param dict(str, object) baseDict: The base dictionary to be aggregated.
        :param dict(str, object) fillerDict: Entries to possibly aggregate with.
        :param str prefix: An optional prefix to be prepended to the keys in `fillerDict`.
        :returns: The resulting :attr:`baseDict` base dictionary.
        :rtype: dict(str, object)
        """
        if (baseDict is not None) and (fillerDict is not None):
            for key, value in fillerDict.items():
                baseKey = prefix + key
                if not baseKey in baseDict:
                    baseDict[baseKey] = value
        return baseDict
    
    @classmethod
    def _extractParams(cls, baseDict, prefix):
        """Retrieve a sub-dictionary whose keys begin with the given prefix.
        
        This utility function looks through `baseDict` and retrieves all
        key-value pairs where the key starts with the given `prefix`.
        The result is given as a separate, independent dictionary. It
        may be empty.

        :param dict(str, object) baseDict: The base dictionary to be searched through.
        :param str prefix: The prefix to look for in the keys.
        :returns: A new dictionary containing only keys starting with `prefix`along with their associated values.
        :rtype: dict(str, object)
        """
        return dict( [(k.replace(prefix, ""),v) for k,v in baseDict.items() if k.startswith(prefix)] )
        
        
    @classmethod
    def Params_init(cls, paramDict):
        """Initialize parameters with their defaults.

        The given dictionary should not be None, on entry.
        Options not present in the dictionary will be added and set to
        their defaults on return.
        
        :param dict(str, object) paramDict: Dictionary mapping option\
        names to their respective values.
        :returns: none
        :rtype: None
        """
        pass

    def open(self, paramDict):
        """Open the instance and set it in a usable state.

        Allocate necessary hardware resources and configure
        user-adjustable parameters to meaningful defaults.
        This function must be called prior to any further usage of the
        instance. Involving it in the system ramp-up procedure could be
        a good choice. After usage of this instance is finished, the
        application should call :meth:`close`.
        
        :param dict(str, object) paramDict: Configuration parameters as\
        obtained from :meth:`.module.Module.Params_init`, possibly.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del paramDict
        return ErrorCode.errOk
        

    def close(self):
        """Close this instance and release associated hardware resources.

        This is the counterpart of :meth:`open`. Upon return, further
        usage of this instance is prohibited and may lead to unexpected
        results. The instance can be re-activated by calling :meth:`open`,
        again.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errOk

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
        return ErrorCode.errNotImplemented
    