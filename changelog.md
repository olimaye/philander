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
- nothing yet.

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
