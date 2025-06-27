# Changelog for the philander project

This is the summary of relevant changes throughout different releases.

<!---Types of entries:--->
<!---### Added--->
<!---### Changed--->
<!---### Deprecated--->
<!---### Removed--->
<!---### Fixed--->
<!---### Security--->

## [Unreleased]
Nothing, yet.

## [0.5.1] - 2025-06-27

### Fixed
- ST ADC1283 driver's `provider` attribute is now set to `SysProvider.COMPOSITE`
- SerialBus implementation for SMBUS2 fixed `ModuleNotFoundError: No module named 'serialbus'`
- SysFactory.autDetectProvider now works with non-top-level module names.

## [0.5] - 2025-06-05

### Added
- ADC module and implementation for Micropython plus SIM and test
- ADC driver for ST ADC1283 serial ADC chip and unit test
- PWM module and implementation for Micropython, RPi.GPIO and Periphery plus test
- SerialBus: SPI support for periphery and MicroPython environments

### Changed
- SerialBus: renamed readWriteBuffer() into writeReadBuffer() and redefined contract
- SysFactory: generators moved to their modules ADC, GPIO, PWM and SerialBus

## [0.4] - 2024-11-15

### Added
- Support of the Micropython environment
- Micropython and Sim(ulation) implementation for the `gpio` module.
- Micropython implementation for `led`.
- The `penum` module to provide `Enum`, `Flag` and `dataclass` on Micropython
- `primitives`: `Percentage.checkRange()`
- `sysfactory`: Factory class `SysFactory` to create instances of system-dependent classes like serial bus and GPIO.
- `systypes`: Added `ErrorCode.errNotInited`, `.errInitFailed`, `.errLowLevelFail` and `.errStopped` to reflect corresponding error conditions, occurring e.g. during initilization of the BMA456 sensor.
- Module `test.micromenu` to provide a substitute for `simple_term_menu` on Micropython
- Unit tests `utaccel`, `utactuator`, `utbattery`, `utbma456`, `utbutton`, `utdictionary`, `utinterruptable`, `utpenum`, `utpotentiometer`, `utpymitter`, `utthermometer`
- Unit test suite `suiteNoHw` for non-hardware related tests running on any platform

### Changed
- `bma456`:
    - Feature configuration data is outsourced to a corresponding file to save memory.
    - Simulation is not always instantiated, but on demand from module+class name.
    - Initialization returns more indicative error codes, such as `ErrorCode.errLowLevelFail` or `ErrorCode.errStopped`
- `accelerometer`: `AxesSign`, `Tap` and `EventSource` mnemonics are now auto-defined instead of hard-coded fix values. `Orientation` derives `Flag`, while `Tap` is inherited from `Enum`. `Data.data` initializes with `None`.
- `battery`: `fromPercentage` performs type check and has doc.
- `configurable`: Attribute `Configuration.type` renamed into `Configuration.item`.
- `dictionary`: Class name is now upper case `Dictionary`.
- `gpio`:
    - Implementation now spreads into platform-dependent sub-modules
    - `GPIO` is a common, abstract interface class, now. 
    - instances are created by `SysFactory.getGPIO()`.
- `interruptable`: `Event` and `EventContextControl` are not `Enum`, anymore. Renamed `EventContextControl` attributes.
- `mcp40`: Implementation to fit the new `Potentiometer` interface.
- `potentiometer`: Reworked the `Potentiometer` interface into dedicated `[get|set][digital|resistance|percentage]()` methods.
- `sensor`:
    - Renamed `Calibration.type` into `.scheme`.
    - `SelfTest` is now a `Flag`.
    - `Sensor` empty interface methods `getStatus()`, `getLatestData()`, and `getNextData()` return `ErrorCode.errNotImplemented` now.
- `serialbus`:
    - Implementation now spreads into platform-dependent sub-modules
    - `SerialBus` is a common, abstract interface class, now. 
    - instances are created by `SysFactory.getSerialBus()`.
- `thermometer`: `Data.temperature` is now initialized with zero by default.
- Module `test.generalTestSuite` uses `micromenu` when running on Micropython

### Deprecated
- Module `test.generalTestSuite` does not support Enum types, anymore.

### Removed
- SMBUS package is no longer supported. Use SMBUS2, instead!
- BLE module was removed. As per ADR, [aioble](https://github.com/micropython/micropython-lib/tree/master/micropython/bluetooth/aioble) is the preferred BLE API.
- The `fastgait` module should be part of the application.

### Fixed
- `BMA456.getLatestData` and `getNextData` return a `Data` object, instead of a list, as defined by the `Sensor` interface.
- `Dictionary.findKey` really returns a single key, instead of a list.
- `interruptable`: `Event.evt*` mnemonics are now strings, and thus, hashable. Consolidated behaviour of `Interruptable.registerInterruptHandler()` and `_fire()`.
- `simBMA456` and `simDev`: Implementation fixed and adapted to the new `SerialBus` and `Sensor` behaviour.


## [0.3] - 2024-08-08

### Added
- interface for digital potentiometers and implementation for MCP4017/18/19
- ST L6924 battery charger implementation
- STC3115/17 gas gauge implementation, to be completed.
- general test suite helper to ease testing driver implementations.
- convenience function ErrorCode.isOk()
- battery.Level.fromPercentage() to do the conversion

### Fixed
- documented design decisions on error codes vs. exceptions and the order of return values.

## [0.2] - 2024-04-19

### Added
- GPIO configuration option to invert the interpretation of a pin-state (LOW-active)

### Fixed
- Button and LED now strip their configuration key prefixes before passing to GPIO.
- Bugs found, when running on a Google Coral mini board.

## [0.1.1] - 2023-10-10

### Added
- change log file
- project meta data URLs
- API documentation on [readthedocs.io](https://philander.readthedocs.io)

### Changed
- structure of the doc directory
- minor changes in the readme

### Fixed
- Python 3.11 compatibility issues with dataclass default values in module sensor

## [0.1.0] - 2023-09-29
### Added
- Initial revision of the package.
