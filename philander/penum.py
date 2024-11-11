"""A light-weight replication of the Python 3.4 built-in Enum and Flag classes.

For portability, this is to support the MicroPython environments. While
functionality is drastically reduced, this implementation strives for
providing the most basic features of enums, flags and dataclasses.
"""

__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["auto", "dataclass", "Enum", "Flag", "idiotypic", "unique"]

_hasBuiltinEnums = False
try:
    from enum import Enum, Flag, unique, auto
    from dataclasses import dataclass
    (Enum, Flag, unique, auto, dataclass)   # suppress "unused" warning
    _hasBuiltinEnums = True
except ImportError as exc:
    _hasBuiltinEnums = False


if not _hasBuiltinEnums:
    class auto():
        """Automatically assign the *next* value to an enum or flag.

        Note that there is no guarantee on the attribute order,
        meaning that the attributes are not necessarily assigned an
        auto value  in the order of their appearance.
        Thus, mixing explicit and auto assignments may lead to unexpected
        results violating the uniqueness of attribute values.
        """
        pass

if _hasBuiltinEnums:
    def idiotypic(cls):
        return cls

else:
    def idiotypic(cls):
        """Class decorator for idiotypic classes.
        
        Modifies each class attribute to be an instance of that class and to
        have an attribute ``key`` set to the name of that attribute as a
        string value as well as another attribute ``value`` set to the value
        originally given at the class definition. This feature is meant to
        be used with enums and flags.
        
        The technique of a decorator is used, because Micropython does not
        support metaclasses.
        """
        enumerations = {x: y for x, y in cls.__dict__.items() \
                         if not (x.startswith('_') or callable(y) or \
                                 isinstance(y, classmethod) or \
                                 isinstance(y, staticmethod) )}
        cls._idiotypicDone = False
        # handle auto() and auto
        next_value = 0x01
        for k, v in enumerations.items():
            if type(v) is auto or v is auto:
                enumerations[k] = next_value
            elif isinstance(v, int) and not isinstance(v, bool):
                next_value = v
            if issubclass( cls, Flag ):
                next_value = next_value << 1
            else:
                next_value = next_value + 1
        cls._enumerations = enumerations
        # make "static" instances of each enumeration object
        cls._instances = {k: cls(v) for k, v in enumerations.items()}
        # initialize static instances
        for k, instance in cls._instances.items():
            setattr( instance, "key", k )
            setattr( instance, "value", enumerations[k] )
            setattr( cls, k, instance )
        cls._idiotypicDone = True
        return cls


if not _hasBuiltinEnums:
    def unique(cls):
        """Class decorator for unique enums.
        
        Checks the attributes of the decorated class to be assigned to
        unique values. If any two attributes are of equal value,
        raises an exception.
        
        :raise ValueError: If the class has two equal attributes.
        """
        enumerations = {x: y for x, y in cls.__dict__.items() \
                                if not (x.startswith('_') or callable(y) or isinstance(y, classmethod))}
        seen = dict()
        for key, value in enumerations.items():
            if value in seen.keys():
                raise ValueError(f"Uniqueness violated in class {cls.__name__} by duplicate attributes: {key} and {seen[value]} are the same!")
            else:
                seen[value] = key    
        return cls

if not _hasBuiltinEnums:
    def dataclass(cls):
        """Dataclass decorator.
        
        Scan a class for data attributes, i.e. variables, not methods.
        Add a constructor to the class to create and initialize same-named
        instance attributes.
        Note that this constructor does not support positional arguments,
        but just keyword arguments. This is because the order of attributes
        retrieved cannot be guaranteed.
        """
        attribs = dict()
        for currcls in [cls] + list(cls.__bases__):
            currclsattr = {x: y for x, y in currcls.__dict__.items() if not (x.startswith('_') or callable(y) or isinstance(y, classmethod))}
            for name, val in currclsattr.items():
                #if not type(val) in (int, float, complex, bool, str, tuple, range, frozenset, bytes):
                if type(val) in (list, dict, set, bytearray):
                    raise ValueError(f"Mutual defaults are not allowed. {name} is of type {type(val)}!")
            attribs.update( currclsattr )
    
        def _constructor(self, *args, **kwargs):
            # Do not allow positional arguments, as the order of attributes
            # cannot be guaranteed by __dict__
            numArgs = len(args)
            if numArgs > 0:
                raise TypeError(f"Positional arguments are not supported. {numArgs} were given!")
            # Overwrite key word arguments
            for pname in kwargs:
                if pname in attribs:
                    setattr( self, pname, kwargs[pname] )
                else:
                    raise TypeError(f"Unexpected keyword argument {pname}")
    
        def _str(self):
            """Generates a string representation of this instance.
            """
            result = self.__class__.__name__ + ": "
            for aname in attribs:
                result = result + "%s=%s, " % (aname, getattr(self, aname) )
            return result
        
        cls.__init__ = _constructor
        cls.__str__  = _str
        return cls


if not _hasBuiltinEnums:
    class Enum():
        """An enumeration base type.
        
        Provide the most basic properties of an enumeration type. So, enums
        have attributes with speaking names and - in principle - arbitrary
        values. However, most commonly the attributes have integer values.
        A class should be derived from this class to define such attributes.
        
        To make the attributes be of the same type as the class defining them,
        that class should be decorated as `idiotypic`.
        
        In order to ensure the enum attributes are unique, use the `unique`
        decorator.
        """
        
        def __init__(self, value: int = 0):
            """ Constructor to create an enum instance.
            
            For idiotypic classes, a singleton implementation is imitated as
            follows: The ``value`` attribute of the created instance will be
            the same as the matching attribute's value.
            An exception is raised if the given value is different from the
            values defined by the attributes.
            
            :param int value: The value of this enum item. Should be unique.
            :raise ValueError: If the given value does not match any of the enum values.
            """
            if hasattr(self.__class__, "_idiotypicDone") and self.__class__._idiotypicDone:
                # make sure the passed in value is a valid enumeration value
                if value not in self.__class__._enumerations.values():
                    raise ValueError(f'{value} is not a valid {self.__class__.__name__}')
                # save the actual enumeration value
                for k, v in self.__class__._enumerations.items():
                    if v == value:
                        self.key = k
                        self.value = v
            else:
                self.value = value
                if isinstance(value, int) and not isinstance(value, bool):
                    self.key = "item_%d" % (value & 0xFFFF)
                else:
                    self.key = "item_%s" % str(value).strip()[:5]
    
        # @classmethod
        # def __str__(cls):
        #     return f'<enum \'{cls.__name__}\'>'
        
        @classmethod
        def __len__(cls):
            return len(cls._enumerations)
    
        @classmethod
        def __iter__(cls):
            return iter(cls._instances)
    
        @classmethod
        def __getitem__(cls, key):
            values = list( cls._instances.values() )
            item = values[key] 
            return item
    
    #     def __getattribute__(cls, key):
    #         if key.startswith('_'):
    #             return object.__getattribute__(cls, key)
    #         else:
    #             return cls(object.__getattribute__(cls, '_enumerations')[key])
    #
    #     def __contains__(cls, other):
    #         if type(other) == cls:
    #             return True
    #         else:
    #             return False
    
    
        def __lt__(self, other):
            """ The less-than operator. Called for the '<' comparison.
            """
            if isinstance(other, Enum) and \
                ( issubclass( type(self), type(other) ) or
                  issubclass( type(other), type(self) ) ):
                return self.value < other.value
            elif isinstance(other, type(self.value)):
                return self.value < other
            return NotImplemented
    
        def __le__(self, other):
            """ The less-or-equal operator. Called for the '<=' comparison.
            """
            if isinstance(other, Enum) and \
                ( issubclass( type(self), type(other) ) or
                  issubclass( type(other), type(self) ) ):
                return self.value <= other.value
            elif isinstance(other, type(self.value)):
                return self.value <= other
            return NotImplemented
    
        def __eq__(self, other):
            """ The equals operator. Called for the '==' comparison.
            """
            if isinstance(other, Enum) and \
                ( issubclass( type(self), type(other) ) or
                  issubclass( type(other), type(self) ) ):
                return self.value == other.value
            elif isinstance(other, type(self.value)):
                return self.value == other
            return NotImplemented
            
        def __ne__(self, other):
            """ The not-equal operator. Called for the '!=' comparison.
            """
            if isinstance(other, Enum) and \
                ( issubclass( type(self), type(other) ) or
                  issubclass( type(other), type(self) ) ):
                return self.value != other.value
            elif isinstance(other, type(self.value)):
                return self.value != other
            return NotImplemented
    
        def __gt__(self, other):
            """ The greater-than operator. Called for the '>' comparison.
            """
            if isinstance(other, Enum) and \
                ( issubclass( type(self), type(other) ) or
                  issubclass( type(other), type(self) ) ):
                return self.value > other.value
            elif isinstance(other, type(self.value)):
                return self.value > other
            return NotImplemented
    
        def __ge__(self, other):
            """ The greater-or-equal operator. Called for the '>=' comparison.
            """
            if isinstance(other, Enum) and \
                ( issubclass( type(self), type(other) ) or
                  issubclass( type(other), type(self) ) ):
                return self.value >= other.value
            elif isinstance(other, type(self.value)):
                return self.value >= other
            return NotImplemented
    
        def __hash__(self):
            """Hash function to support ``hash()`` and operations with sets, dictionaries etc.
            """
            return hash(self.value)
        
        def __str__(self):
            """Generates a string representation of this instance.
            
            Called e.g. for printing.
    
            :return: A string describing the content of this instance.
            :rtype: str
            """
            return "%s.%s" % (self.__class__.__name__, self.key)
        
        def __and__(self, other):
            """ The bitwise AND operator. Called for the '&' operation.
            
            Note that the result of a binary operation of two Enums is a plain
            integer and not an Enum! Typically, this result is beyond the range
            of the attributes defined.
            This kind of logic is provided just for convenience.
            """
            if isinstance(other, Enum):
                return (self.value & other.value)
            elif isinstance(other, int):
                return (self.value & other)
            return NotImplemented
    
        def __or__(self, other):
            """ The bitwise OR operator. Called for the '|' operation.
            
            Note that the result of a binary operation of two Enums is a plain
            integer and not an Enum! Typically, this result is beyond the range
            of the attributes defined.
            This kind of logic is provided just for convenience.
            """
            if isinstance(other, Enum):
                return (self.value | other.value)
            elif isinstance(other, int):
                return (self.value | other)
            return NotImplemented
    
        def __xor__(self, other):
            """ The bitwise XOR operator. Called for the '^' operation.
            
            Note that the result of a binary operation of two Enums is a plain
            integer and not an Enum! Typically, this result is beyond the range
            of the attributes defined.
            This kind of logic is provided just for convenience.
            """
            if isinstance(other, Enum):
                return (self.value ^ other.value)
            elif isinstance(other, int):
                return (self.value ^ other)
            return NotImplemented
    
        def __invert__(self):
            """ The bitwise NOT operator. Called for the '~' operation.
            
            Note that the result of a binary operation of two Enums is a plain
            integer and not an Enum! Typically, this result is beyond the range
            of the attributes defined.
            This kind of logic is provided just for convenience.
            """
            return (~self.value)


if not _hasBuiltinEnums:
    class Flag(Enum):
        """A base class for flag types.
    
        As with enums, flag attributes have speaking names while their values
        are assumed to be integer bit masks.
        A class should be derived from this class to define such attributes.
        
        To make the attributes be of the same type as the class defining them,
        that class should be decorated as `idiotypic`.
        
        In order to ensure the attributes are unique, use the `unique`
        decorator.
        """
    
        def __init__(self, value: int = 0):
            """ Construct a flag instance.
            
            For idiotypic classes, a singleton implementation is imitated as
            follows: The ``value`` attribute of the created instance will be
            the same as the matching attribute's value. The ``key`` attribute
            is copied from that attribute.
            
            :param int value: The value of this flag item, interpreted as a bit mask.
            """
            if hasattr(self.__class__, "_idiotypicDone") and \
                self.__class__._idiotypicDone and \
                value in self.__class__._enumerations.values():
                for k, v in self.__class__._enumerations.items():
                    if v == value:
                        self.key = k
                        self.value = v
            else:
                self.value = value
                if isinstance(value, int) and not isinstance(value, bool):
                    self.key = "item_%04x" % (value & 0xFFFF)
                else:
                    self.key = "item_%s" % str(value).strip()[:5]
    
        def __and__(self, other):
            """ The bitwise AND operator. Called for the '&' operation.
    
            :returns: A same-type object representing the conjunction of this and the given object.
            :rtype: Subclass of Flag
            """
            if isinstance(other, Flag):
                return type(self)(self.value & other.value)
            elif isinstance(other, int):
                return type(self)(self.value & other)
            return NotImplemented
    
        def __or__(self, other):
            """ The bitwise OR operator. Called for the '|' operation.
    
            :returns: A same-type object representing the disjunction of this and the given object.
            :rtype: Subclass of Flag
            """
            if isinstance(other, Flag):
                return type(self)(self.value | other.value)
            elif isinstance(other, int):
                return type(self)(self.value | other)
            return NotImplemented
    
        def __xor__(self, other):
            """ The bitwise XOR operator. Called for the '^' operation.
    
            :returns: A same-type object representing the exclusive-or of this and the given object.
            :rtype: Subclass of Flag
            """
            if isinstance(other, Flag):
                return type(self)(self.value ^ other.value)
            elif isinstance(other, int):
                return type(self)(self.value ^ other)
            return NotImplemented
    
        def __invert__(self):
            """ The bitwise NOT operator. Called for the '~' operation.
    
            :returns: A same-type object representing the negation this object's value.
            :rtype: Subclass of Flag
            """
            return type(self)(~self.value)

        def __bool__(self):
            """Determine the truth value of this instance.
    
            :returns: True, if the value field has no bit flag set, False otherwise.
            :rtype: bool
            """
            return (self.value != 0)
    
