"""Abstract actuator interface.

Provide an API to abstract from any type of actuators. Only a very basic
set of common types and functions is provided.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Direction", "Actuator"]

from enum import Enum
from .systypes import ErrorCode

class Direction( Enum ):
    """Data class to represent the direction that an actuator can move to.
    """
    positive            =  1
    negative            = -1
    counterclockwise    = positive
    clockwise           = negative
    left                = positive
    right               = negative
    forth               = positive
    back                = negative
    up                  = positive
    down                = negative

    toStr = {
        positive  : 'positive/counterclockwise/left/forth/up',
        negative  : 'negative/clockwise/right/back/down',
    }

class Actuator():
    """Unified interface to parts and subsystems with mechanical capabilities.
    
    This may involve some sort of motor to execute mechanical work, such as in
    gears, drives or stimulators. However, also other physical media like
    electricity (taser) or light (laser) might be the functional basis of an
    actuator.
    
    An actuator is meant to reflect the most atomic component of a mechanical
    device. Several actuators may compose a more complex subsystem,
    such as a steering axis of a rover.
    """

    def startOperation(self, direction=Direction.positive,
                       strengthIntensity=0,
                       onSpeedDuty=0, ctrlInterval=0,
                       durationLengthCycles=0):
        """Start a continuous or lengthy operation of this actuator instance.
        
        Begin an operation, such as running a motor. The operation may
        or may not end automatically. In any case, the operation can be
        stopped intentionally by calling :meth:`stopOperation`.

        The optional ``direction`` parameter may be used to indicate the
        direction of the operation. Interpretation of left/right or
        positive/negative etc. is up to the implementation.
        
        The ``strengthIntensity`` parameter may be used to set the drive
        strength or intensity of a movement.
        The strength should be given in a meaningful physical unit.
        If meant as an intensity, it should be an integer percentage in
        the range [0...100].
        In the context of PWM control, this parameter may be interpreted
        as the voltage amplitude applied, expressed in milli Volt.
        This parameter is optional.
        
        The optional parameter ``onSpeedDuty`` may indicate the speed of
        the movement or the length of the ON phase in a rectangular
        control signal.
        If interpreted as a speed, it should be given either as a value
        in meters per second (m/s) or as an integer percentage related
        to some maximum possible or reference speed.
        When controlling a PWM device, this is the duty cycle expressed
        as a percentage.

        The ``ctrlInterval`` parameter gives the total length of a
        periodic control interval, e.g. for PWM control. It is expressed
        in milliseconds.
        This parameter is optional.
        
        The parameter ``durationLengthCycles`` is optional.
        It  and may be interpreted as a run time duration, preferably
        expressed as a number in milliseconds (ms).
        Alternatively, this parameter may also be interpreted as a way
        length for the actuator to go, preferably expressed as a number
        in millimeters (mm).
        Finally, this can also be the number of cycles to last, e.g.
        when controlling a PWM device. Then, this is a unitless integer
        number. 
        
        See also: :meth:`stopOperation`.
        
        :param Direction direction: The direction to move the actuator in.
        :param int strengthIntensity: The speed or intensity of the movement.
        :param int durationLengthCycles: The duration, length or number of cycles to move.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del direction, strengthIntensity, onSpeedDuty, ctrlInterval, \
            durationLengthCycles
        return ErrorCode.errNotImplemented
    
    def stopOperation(self):
        """Immediately stops the current operation.
        
        See also: :meth:`startOperation`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errNotImplemented
    
    def action(self, pattern=None):
        """Executes a predefined action or movement pattern with this actuator.
        
        Runs an action on this actuator instance. The type of action
        can be specified further using the optional ``pattern`` parameter.
        In most cases, this will be an integer number designating one
        or the other pre-defined / default movement.
        If applicable, the value zero (0) shall encode a
        "move to home/rest/parking position" action. Also "switch off"
        could be a valid interpretation.
        A value of one (1) shall be used for "the standard/default movement".
        The interpretation of other values is at the discretion of the
        implementation.
        
        :param int pattern: The action pattern to execute.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del pattern
        return ErrorCode.errNotImplemented
    