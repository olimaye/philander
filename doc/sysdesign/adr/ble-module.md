# The BlueTooth (BLE) API module

## Status

<!-- one of [proposed | rejected | accepted | deprecated | superseded by [linked ADR](adr-link.md)] -->

accepted

## Date <!-- optional -->

<!-- YYYY-MM-DD (no period!) Date when this decision was last updated -->

2025-01-13

## Deciders <!-- optional -->

<!-- List everyone actively involved in the decision! Do not assume any relation between order and importance. -->
* O. Maye

## Context

<!-- Describe the context and problem statement, e.g., in free form using two to three sentences. You may want to articulate the problem in form of a question or give the technical story. What is the issue that is motivating this decision or change? How is the decision architecturally significant - warranting an ADR? What is the high level design Approach? Leave the details for the options section below! -->

For using the bluetooth functionality of a target device, several APIs are established by third parties, already.
[BLEAK](https://github.com/hbldh/bleak) is implemented for PC-class devices and Raspberry Pi. It is also available for Google Coral. Mostly, the implementations concentrate on the GATT client side. The MicroPython-specific
[bluetooth](https://docs.micropython.org/en/latest/library/bluetooth.html) library is quite low-level. Its direct use is discouraged. Instead, it's recommend to rely on the [aioble](https://github.com/micropython/micropython-lib/tree/master/micropython/bluetooth/aioble) wrapper library, for most applications.

The current BLE interface (ble.py) was created with BLEAK in mind with only slight abstractions. Also, it doesn't reflect the BLE terminology, very well. Further, it is not foreseen for async I/O.

As `aioble` is not available on RasPi/Coral platforms and `bleak` is not available on the RaspiPico/MicroPython platform, we need a common, unifying interface or wrapper to really allow for platform-independent application development.


## Options <!-- optional -->

<!-- Give an austere description of the considered options. Concentrate on technical aspects. Give pros and cons, but do not argue, why this option was finally selected or not.
### Option A

[example | description | pointer to more information]

* Good, because [argument a]
* Good, because [argument b]
* Bad, because [argument c]
-->

The following options came into mind, when thinking on a unified BLE interface.

### Option A

Provide an own `philander\ble.py` module showing a self-defined BLE-API to the outside (application). Depending on the environment at runtime, the implementation just wraps either MicroPython's `bluetooth` or `aioble` libraries or the external `bleak` package. So, at least two non-empty implementations must be created.

This approach is similar to the design of the `gpio` and `serialbus` modules.

* Good, because we can define the API ourself.
* Bad, because of the effort it needs to implement and test two BLE modules.
* Bad, because of the performance loss and memory consumption introduced by this additional layer.

### Option B

Define `aioble` to be *the* BLE API. Do not provide any BLE interface as part of `philander`.
This would imply the necessity of providing wrapper/convergence modules on platforms other than MicroPython, such as Raspberry Pi or Google Coral.


* Good, because getting rid of the BLE module cleans out `philander`, a bit
* Good, because there is no effort for the MicroPython environment
* Bad, because a wrapper module is needed for the PC/Pi/Bleak environments.

## Considerations <!-- optional -->

<!-- Document decision drivers, forces, concerns, ancillary or related issues, questions that arose in debate of the ADR. Indicate if/how they were resolved or mollified.

* [driver 1, e.g., a force, facing concern, …]
* [driver 2, e.g., a force, facing concern, …]
-->
With respect to the BLE concept and terminology, `aioble` appears to be the most appropriate realization for Python API.

## Decision

<!-- What is the change that we're proposing and/or doing? Document any agreed upon important implementation detail, caveats, future considerations, remaining or deferred design issues. Document any part of the requirements not satisfied by the proposed design. 

Chosen option: "[option 1]", because [justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force force | … | comes out best (see below)].
-->

Chosen option: "Option B", in favor of streamlining the `philander` project and focusing on drivers for components.

## Consequences

<!-- What becomes easier or more difficult to do because of this change?
* [e.g., improvement of quality attribute satisfaction, follow-up decisions required, …]
* [e.g., compromising quality attribute, follow-up decisions required, …]
* …
-->

We are aware of the following:
* Existing applications must be re-written or adapted to the new BLE API
* The BLE module can be kicked out from the project
* To support RasPi and Google Coral platforms, it needs a bleak-to-aioble wrapper

## Related ADRs <!-- optional -->

<!-- List any relevant ADRs - such as a design decision for a sub-component of a feature, a design deprecated as a result of this design, etc..
* [Depends on|Refined by|...] [ADR Title](URL)
--> 

None.

## References <!-- optional -->

<!-- List additional references.
* \[Title\]\(URL\)
-->

## Change Log <!-- optional -->

<!-- List the changes to the document. Sort by date in descending order.
* YYYY-MM-DD [Author]: [New status, if changed]. [Change]
-->

* 2025-01-13 O. Maye: ACCEPTED. Decided for option B (aioble).
