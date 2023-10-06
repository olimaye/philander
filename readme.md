# About philander

Philander is a collection of drivers for the components of an embedded
system or wireless sensor node. This includes but is not limited to:
  - sensors
  - battery chargers
  - battery fuel gauges
  - actors, such as motors
  - GUI elements, like LEDs and buttons
  - service modules, e.g. integer mathematics
  
The code is completely written in Python and relies on low-level
communication modules such as smbus, smbus2 or periphery and pymitter.
As with all driver collections, it aims at making application
development easier by providing a unified interface for parts that are
expected to do the same or similar things.

The intended hardware platform is all kind of single-board computers
such as Raspberry Pi, Arduino and Google Coral.
This software is specifically designed for making the features of their
shields, daughter- and add-on boards available to the application.

# Installation

Released builds of this collection can be installed from the
python package index at [https://pypi.org](https://pypi.org) by just
using pip as in:
`pip3 install philander`

# Application development
The main guide line is: Keep your application code as generic as
possible. References to philander objects should only be as specific as
necessary!

The API reference may be generated from the source code, through, e.g.
sphinx.
 
The most relevant philander objects are derived from module. The life
cycle of a module is as follows.

## Instantiation
Instantiation is usually done by a default constructor without any
parameter.

## Params_init
This is a class method to pre-populate an empty dictionary with a
reasonable default configuration.

## Open
Configures an object and prepares it for use.
Configuration is done through Python dictionaries, passed in as the
first parameter. The dictionary can be pre-initialized by Params_init()
or set by the application. Alternatively, parts of it could be read from
config files, for example.

## Operation
Run time operation of a module depends on the actual type and my be
specified by other interfaces, such as sensor, charger or gasgauge.

## Close

Shut down the instance and possibly release any hardware resources
allocated by this object.

# Example code
```
from philander.accelerometer import Accelerometer
from philander.bma456 import BMA456 as sensorDriver
from philander.systypes import ErrorCode

configSensor = {
    "SerialBus.designator": "/dev/i2c-1",
    "SerialBusDevice.address": 0x18,
    "Sensor.dataRange"    : 4000,
    "Sensor.dataRate"     : 100,
}
sensor = sensorDriver()
sensorDriver.Params_init( configSensor )

err = sensor.open( configSensor )
if (err == ErrorCode.errOk):
    print("Success!")
else:
    print("Error: ", err)

mdata, err = sensor.getNextData()
if (err == ErrorCode.errOk):
    print(now, mdata)

sensor.close()
```

# Library development

Python developers are welcome to add own classes and driver
implementations to this collection. Stick to the rules and conventions
of object-oriented Python programming!

The mandatory coding convention for Python code is the Python
Enhancement Proposal #8 ([PEP 8](https://peps.python.org/pep-0008/)).
It also gives advice on the naming convention.

Documentation must follow [PEP 257](https://peps.python.org/pep-0257/).
The Docstring format should be reStructuredText as defined by the
[reStructuredText Markup Specification](https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html).
To generate the HTML documentation output from the source files, tools
like [Sphinx](https://www.sphinx-doc.org) may be used.
Preferrably, the same tool should also be able to generate PDF output.

