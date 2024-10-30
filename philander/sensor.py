"""Abstract sensor interface.

Provide an API to abstract from any type of sensors. Only a very basic
set of common types and functions is provided.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Calibration", "CalibrationData", "CalibrationType", \
           "SelfTest", "Sensor"]

from .penum import Enum, Flag, unique, auto, idiotypic, dataclass

from .configurable import Configurable, Configuration, ConfigItem
from .module import Module
from .systypes import ErrorCode, Info


@unique
@idiotypic
class CalibrationType(Enum):
    """Mnemonic type to identify a specific calibration procedure.
    
    This is part of the information to be passed to a sensor when calling
    its :meth:`Sensor.calibrate` method.
    """
    default            = auto()
    """Default calibration procedure. This may be a special
    procedure of the sensor hardware, or simply the use of hard-coded
    default calibration parameters. Depends on the sensor hardware
    and/or driver implementation.
    """
    zero               = auto()
    """Single fix point *zero* calibration. No further calibration data
    is needed. The current sensory exposure should map to exactly zero
    (0) measurement units. May also be interpreted as *nothing detected*
    or 0%.
    """
    one                = auto()
    """Single fix point *one* calibration. No further calibration data
    needed. The current sensory exposure should map to exactly one (1)
    measurement unit. For binary sensors, may also be interpreted as
    *something detected*.
    """
    hundred            = auto()
    """Single fix point *hundred* calibration. No further calibration
    data is needed. The current sensory exposure should map to exactly
    hundred (100) measurement units. For qualitative sensors, may also
    be interpreted as *everything detected* or 100%.
    """
    trueValue          = auto()
    """Single point calibration. The true measurement value of the
    current exposure must be given as part of the calibration data
    structure. The current sensory exposure should map to exactly the
    value given in the calibration data and meant as measurement units.
    """
    expose1            = auto()
    """The first point in a two- or three point calibration, depending
    on what the sensor implementation actually supports. The true
    measurement value at this point is either given implicitly or
    explicitly by further data of the calibration data structure. The
    calibration procedure cannot be finished at this time. Instead, the
    driver's calibration routine should expect to be called again with
    one of the other ``calibExpose`` calibration types.
    """
    expose2            = auto()
    """The second point in a two- or three point calibration, depending
    on what the sensor implementation actually supports. The true
    measurement value at this point is either given implicitly or
    explicitly by further data of the calibration data  structure. A
    two-point calibration finishes at this point, while a 3-point
    calibration should expect to be called once more.
    """
    expose3            = auto()
    """The last point in a three point calibration. The true measurement
    value at this point is either given implicitly or explicitly by
    further data of the calibration data structure.
    """
    offset             = auto()
    """Provides the new, total offset, given in either analogue,
    digitized or measurement units as part of the calibration data
    structure.
    """
    shiftOffset        = auto()
    """The current offset is corrected by the shift given in analogue,
    digitised or measurement units as part of the calibration data
    structure. The shift adds to the current offset.
    """
    linear             = auto()
    """Provides a new pair of total offset and sensitivity/skew for
    translating raw (analogue) values into measurement units. These
    parameters must be given as part of the calibration data structure.
    """
    linearRel          = auto()
    """Gives a pair of relative correctives to the current offset and
    skew/sensitivity. This data must be part of the calibration data
    structure. Note that the offset corrective must be given in either
    analogue, digitised or measurement units and will be added to the
    current offset. The sensitivity corrective is interpreted as a signed
    percentage. It will be added to 100% and then applied to (multiplied
    with) the current sensitivity. This is to allow the current sensitivity
    being, e.g. increased by 3% or 5% and alike.
    """
    param              = auto()
    """Generic calibration type to allow for a transfer of calibration
    parameters. With this, the current parameters are no longer in
    effect, but will be replaced by the data provided in the calibration
    data structure.
    """
    paramRel           = auto()
    """Shift or skew the current calibration parameters by the correctives
    provided in the calibration data structure.
    """
    trueMeasurement    = auto()
    """Provide a pair of ``(m,v)`` measured and true value to calculate
    necessary corrections. This is a calibration with one fix point
    similar to :attr:`trueValue`. The difference is, that the
    measured value is not implicitly given by the current exposure, but
    can be provided explicitly as part of the calibration data structure.
    """
    trueMeasurement2   = auto()
    """Provides two pairs of ``(m,v)`` measured and true values to
    calculate necessary corrections. This is a two-point calibration
    and both points are given in the calibration data structure.
    """
    knownMeasurement   = auto()
    """In contrast to :attr:`trueMeasurement`, calibration uses one
    or more points ``(r,v)`` on the transfer function, where ``r`` is the
    analogue or digitized raw value or voltage equivalent and ``v`` is
    the true, resulting data. This is similar to :attr:`expose3`
    etc. except, the primary measure is not given implicitly by the
    current exposure, but is provided explicitly, instead. All this data
    must be part of the calibration data structure. This is a generic
    mnemonics. The actual number of points is given implicitly / at the
    discretion of the implementation.
    """
    knownMeasurement1  = auto()
    """The same as :attr:`knownMeasurement`. One data point is used.
    """
    knonwMeasurement2  = auto()
    """The same as :attr:`knownMeasurement`. Two data points are
    used.
    """
    knonwMeasurement3  = auto()
    """The same as :attr:`knownMeasurement`. Three data points are
    used.
    """
    temperature        = auto()
    """Re-calibrate the temperature measurement, e.g. for sensors
    involving temperature compensation.
    """

@dataclass
class _CalibrationData_linear:
    """Helper to wrap offset and slope, both given in measurement units.
    """
    
    offset:             object = None
    sensitivity:        object = None
    
@dataclass
class _CalibrationData_iLinear:
    """Helper to wrap offset and slope, both given in (e.g. ADC-) raw
    units.
    """
    
    offset:             int = 0
    sensitivity:        int = 0
    
@dataclass
class _CalibrationData_trueMeasurement:
    """Helper to wrap a pair of an actual measurement result and its
    related true value, both given in measurement units. 
    """
    
    measurement:        object = None
    trueValue:          object = None
    
@dataclass
class _CalibrationData_knownMeasurement:
    """Helper to wrap a list of raw measures given in raw units and a
    list of their corresponding true values, given in measurement units. 
    """
    
    measure:            object = None   
                        # List[int] = field( default_factory=lambda : [0,0,0] )
    trueValue:          object = None
    
@dataclass
class CalibrationData:
    """Container type to encapsulate a calibrations pure data structure.
    """
    
    trueValue:          object = None
    """True measurement value related to the current exposure. Should
    be used with
    :attr:`CalibrationType.trueValue`,
    :attr:`CalibrationType.expose1`,
    :attr:`CalibrationType.expose2` and
    :attr:`CalibrationType.expose3`.
    """
    offset:             object = None
    """Either a new absolute offset, or the shift to correct the current
    offset, given in measurement units. To be used with 
    :attr:`CalibrationType.offset` and
    :attr:`CalibrationType.shiftOffset`.
    """
    iOffset:            int = 0
    """Either a new absolute offset, or the shift to correct the current
    offset, given in analogue, digitised or abstract integer units. To be
    used with :attr:`CalibrationType.offset` and
    :attr:`CalibrationType.shiftOffset`.
    """
    linear:             _CalibrationData_linear = None
    """Either new linear calibration parameters to replace the current
    ones, or corrective numbers to adjust the calibration parameters in
    effect, both given in measurement units. To be used with
    :attr:`CalibrationType.linear` and
    :attr:`CalibrationType.linearRel`.
    """
    iLinear:            _CalibrationData_iLinear= None
    """Either new linear calibration parameters to replace the current
    ones, or corrective numbers to adjust the calibration parameters in
    effect, both given in abstract integer units. To be used with
    :attr:`CalibrationType.linear` and
    :attr:`CalibrationType.linearRel`.
    """
    param:              object = None
    """Generic set of parameters, stored separately. To be used with
    :attr:`CalibrationType.param` and
    :attr:`CalibrationType.paramRel`.
    """
    trueMeasurement:    _CalibrationData_trueMeasurement = None
    """ Pair of measured and true value to support a one-point-calibration.
    Both values are given in measurement units. Note that the values do
    not relate to the current exposure. To be used with
    :attr:`CalibrationType.trueMeasurement`.
    """
    trueMeasurement2:   _CalibrationData_trueMeasurement = None
    """Two pairs of measured and true value to support a two-point-
    calibration. All values are given in measurement units. To be used
    with :attr:`CalibrationType.trueMeasurement2`.
    """
    knownMeasurement:   object = None   
    # List[_CalibrationData_knownMeasurement] = field( default_factory=lambda :
    #                                                    [_CalibrationData_knownMeasurement(),
    #                                                     _CalibrationData_knownMeasurement(),
    #                                                     _CalibrationData_knownMeasurement()] )
    
    """Up to 3 pairs of raw measure and true value to support a
    multi-point-calibration. The source (x)- values *measure* are meant
    as ADC ticks or milli Volts. Up to 3 inputs are supported (x,y,z or
    real/imaginary etc.).
    The target (y)- values *trueValue* are given in measurement units.
    To be used with
    :attr:`CalibrationType.knownMeasurement`,
    :attr:`CalibrationType.knownMeasurement1`,
    :attr:`CalibrationType.calibKnownMeasurement2`,
    :attr:`CalibrationType.calibKnownMeasuremen3`.
    """
    temp:               _CalibrationData_iLinear = None
    """Temperature calibration data. To be used with
    :attr:`CalibrationType.temperature`.
    """

@dataclass
class Calibration:
    """Container to wrap calibration scheme and data at the top level.
    
    This structure is to be passed in calls to :meth:`Sensor.calibrate`.
    The interpretation of the data particles depends on the scheme of the
    calibration as follows.
    
    =================    =========================
    CalibrationType      CalibrationData particle
    =================    =========================
    default              *none* 
    zero                 *none*
    one                  *none*
    hundred              *none*
    trueValue            trueValue
    expose1              trueValue
    expose2              trueValue
    expose3              trueValue
    offset               offset, iOffset
    shiftOffset          offset, iOffset
    linear               linear, iLinear
    linearRel            linear, iLinear
    param                param
    paramRel             param
    trueMeasurement      trueMeasurement
    trueMeasurement2     trueMeasurement2
    knownMeasurement     knownMeasurement
    knownMeasurement1    knownMeasurement
    knonwMeasurement2    knownMeasurement
    knonwMeasurement3    knownMeasurement
    temperature          temp
    =================    =========================    
    """
    scheme:     CalibrationType = CalibrationType.default
    data:       CalibrationData = None
        
@unique
@idiotypic
class SelfTest(Flag):
    """Bit mask type to designate the different types of self tests.
    """
    CONNECTION      = 0x0001
    """Test physical connection, possibly by reading the chip ID
    """
    FUNCTIONAL      = 0x0002
    """Functional test, subject to the implementation.
    """
    SELFTEST_ALL    = 0xFFFF
    """All possible self tests.
    """
    
class Sensor(Module, Configurable):
    """This class is meant to be sub-classed to define interfaces for\
    more-specific categories of sensors.
    """
    
    #
    # Initializes the sensor.
    #
    def __init__( self ):
        paramDict = dict()
        self.Params_init( paramDict )
        # Create instance attributes
        self.dataRange = paramDict["Sensor.dataRange"]
        self.dataRate  = paramDict["Sensor.dataRate"]
 
    @classmethod
    def Params_init( cls, paramDict ):
        """Initializes parameters to their default values.
        Supported key names and their meanings / expected keys are:
        
        * ``Sensor.dataRange``: Upper/lower limit of expected measurements.\
        Defaults to 1.
        * ``Sensor.dataRate``: Measurement frequency, given in Hz.\
        Default is 1.
        
        Also see :meth:`.module.Module.Params_init`.
        
        :param dict(str, object) paramDict: Dictionary mapping option\
        names to their respective values.
        :returns: none
        :rtype: None
        """
        # Fill paramDict with defaults
        if not ("Sensor.dataRange" in paramDict):
            paramDict["Sensor.dataRange"] = 1
        if not ("Sensor.dataRate" in paramDict):
            paramDict["Sensor.dataRate"] = 1
        return None


    def open(self, paramDict):
        """Opens an instance and puts it into a usable state.
        
        Configures the sensor by reading the supported parameters or
        applying default values and calling :meth:`configure`.
        Also see: :meth:`.module.Module.open`.
        
        :param dict(str, object) paramDict: Configuration parameters as\
        obtained from :meth:`.module.Module.Params_init`, possibly.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        defaults = dict()
        self.Params_init( defaults )
        ret = ErrorCode.errOk
        if ("Sensor.dataRange" in paramDict):
            cfg = Configuration( item=ConfigItem.range, value=paramDict["Sensor.dataRange"])
            ret = self.configure( cfg )
        else:
            paramDict["Sensor.dataRange"] = defaults["Sensor.dataRange"]
        if ("Sensor.dataRate" in paramDict):
            cfg = Configuration( item=ConfigItem.rate, value=paramDict["Sensor.dataRate"])
            ret = self.configure( cfg )
        else:
            paramDict["Sensor.dataRate"] = defaults["Sensor.dataRate"]
        return ret

    
    def selfTest(self, tests):
        """Carry out a sensor self test.
        
        The aim of such tests is to verify the integrity and well-functioning
        of the sensor device. The nature of these tests is solely specific
        to the sensor type and implementation. So, a test may be a built-in
        hardware test or some stress test or spot-check implemented in
        software or a combination of both.
        Depending on the underlying sensor type, a test may or may not be
        finished when returning from this function.
        
        If the test finishes upon return, the test result is communicated
        to the application via the return value. In that case, the sensor
        device is assumed to be in the same or similar operating condition
        as before entering this method.
        
        If, in the other case, the test is not finished before returning,
        the sensor is assumed to be put in test mode and further action
        of the application is necessary to elicit the test result. This
        action could, for example, include reading sample data or retrieve
        the information block. How to leave the self-test mode, depends
        on the sensor implementation. Calling this function with the same
        or complementing ``tests`` parameter or invoking
        :meth:`Sensor.reset` or :meth:`Sensor.configure` are just a few
        examples.
        
        :param int tests: A bit mask to select the tests to be executed,\
        in case several tests are available.\
        Interpretation of this parameter is up to the specific sensor\
        type and may include starting and stopping a certain test mode.
        :return: An error code either indicating the test result or that\
        starting/stopping test mode was successful or the reason why it\
        failed.
        :rtype: ErrorCode
        """
        del tests
        return ErrorCode.errNotSupported


    def reset(self):
        """Soft resets the sensor.
        
        Depending on the actual sensor type, configuration may get lost.
        So, the device is in some default state, afterwards and must be
        re-configured according to the application's needs.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        defaults = dict()
        self.Params_init( defaults )
        self.dataRange = defaults["Sensor.dataRange"]
        self.dataRate = defaults["Sensor.dataRate"]
        return ret


    def configure(self, configData):
        """Configures the sensor device as described by the given
        configuration data.
        
        Note that the type of the provided data and its interpretation
        will depend on the sensor implementation.
        Also see: :class:`Configuration`.
        
        :param .sensor.Configuration configData: Specific configuration information.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if (configData.item == ConfigItem.range):
            self.dataRange = configData.value
        elif (configData.item == ConfigItem.rate):
            self.dataRate = configData.value
        else:
            ret = ErrorCode.errNotSupported
        return ret


    def calibrate(self, calib):
        """Calibrates the sensor device according to the given calibration data.
        
        Calibration may, for example, provide static offsets to adjust the
        measurement's zero point or some sort of corrective coefficients
        to account for the sensor's temperature drift.
        The exact type of calibration along with additional data that is
        possibly necessary, is passed in via the ``calib`` parameter.
        Also see: :class:`Calibration`.
        
        :param Calibration calib: The calibration data for that sensor.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del calib
        return ErrorCode.errNotSupported


    def getInfo(self):
        """Retrieves an information block from the sensor device.
        
        Typically, this kind of information is rather static in that,
        it does not change (much) over time. Usually, it further describes
        the sensor origin, manufacturing date, hardware/firmware revision,
        product/model ID, self-identifying numbers and alike. Also, the
        general operating mode or working conditions may be part of the
        info block.
        
        For more dynamic meta-information see :meth:`getStatus`.
        
        The method returns both, an instance of :class:`Info`, carrying
        the information block as well as an error code, indicating
        success or failure. The info block shall be evaluated only, if
        the method returned successfully.
        Even then, the caller should still evaluate the ``validity``
        attribute of the returned info block to find out, which of the
        information is actually valid.
        
        :return: The information object and an error code indicating either success or the reason of failure.
        :rtype: Info, ErrorCode
        """
        info = Info()
        ret = ErrorCode.errOk
        return info, ret


    def getStatus(self, statusID):
        """Retrieves status data from the sensor device.
        
        Typically, this kind of information is more dynamic in that, it
        changes (much) over time. Usually, it further describes the
        sensor's current shape and condition, such as the availability of
        new measurement data, the cause of an interrupt or the status of
        certain hardware functions. Also, secondary measurements such as
        the die temperature could be subject to status data.
        
        For more static meta-information see :meth:`getInfo`.
        
        The given ``statusID`` parameter specifies, exactly which status
        information should be retrieved. Its type and interpretation
        depends on the sensor implementation.
        
        The method returns both, resulting status data and an error code
        indicating success or failure. The status data should be considered
        valid only, if the error code indicates a successful execution
        of this method.
        
        The type and interpretation of the status data depends on the
        specific sensor implementation.

        :param int statusID: Identifies the status information to be retrieved.
        :return: The status object and an error code indicating either success or the reason of failure.
        :rtype: Object, ErrorCode
        """
        del statusID
        return None, ErrorCode.errNotSupported


    def getLatestData(self):
        """Retrieves the most recent data available and returns immediately.
        
        This function will never block, but may read data that has been
        read before, already. More precisely, the data returned was
        valid / taken at a moment in the past, which is as close as
        possible to the current point in time, (including right NOW).
        
        For sensors which deliver measurements continuously in time,
        there is no semantic difference to :meth:`getNextData`.
        
        In contrast, for sensors, which provide measurements discretely
        at certain time intervals, this function is expected to deliver
        the last measurement point - without any waiting. Typically, this
        requires some kind of buffering. at the sensor or driver side.
        
        The method is synchronous in that, it hands out the resulting
        data to the caller upon return. In fact, this method returns both,
        the measurement result and an error code signaling success or
        failure. The measurement data should be considered
        valid only, if the error code indicates a successful execution
        of this method.
        
        The type and interpretation of the returned measurement data is
        specific to the individual sensor and driver implementation. The
        application may rely on values scaled to reasonable units, such
        as temperatures in degree Celsius, distances in meters and
        pressures in Pascal - or multiples and fractions thereof.
        
        Also see: :meth:`getNextData`.
        
        :return: The measurement data object and an error code indicating\
        either success or the reason of failure.
        :rtype: Object, ErrorCode
        """
        return None, ErrorCode.errNotSupported
    

    def getNextData(self):
        """Retrieves the next data, possibly waiting for the current\
        measurement interval to expire.
        
        This function may introduce a blocking wait, but always returns
        with fresh, new data never read before. The measurement is
        taken / valid either immediately or as early as possible in the
        future.
        
        For sensors, that deliver data continuously in time, there is no
        difference to :meth:`getLatestData`.
        
        For sensors that sample data at certain time intervals, this
        function very likely includes some waiting delay until the next
        measurement is due.
        
        In either case, this function blocks until the measurement is
        retrieved and hands out data to the application upon return.
        In that sense, this is a synchronous function.
        
        The return is twofold: the measurement result and an error code
        signaling success or failure. The measurement data should be
        considered valid only, if the error code indicates a successful
        execution of this method.
        
        The type and interpretation of the returned measurement data is
        specific to the individual sensor and driver implementation. The
        application may rely on values scaled to reasonable units or
        multiples and fractions thereof.
        
        Also see: :meth:`getLatestData`.
        
        :return: The measurement data object and an error code indicating\
        either success or the reason of failure.
        :rtype: Object, ErrorCode
        """
        return None, ErrorCode.errNotSupported
