# Returning error codes vs. throwing exceptions

## Status

<!-- one of [proposed | rejected | accepted | deprecated | superseded by [linked ADR](adr-link.md)] -->

proposed

## Date <!-- optional -->

<!-- YYYY-MM-DD (no period!) Date when this decision was last updated -->

2024-07-12

## Deciders <!-- optional -->

<!-- List everyone actively involved in the decision! Do not assume any relation between order and importance. -->
* O. Maye
* C. Bellgardt

## Context

<!-- Describe the context and problem statement, e.g., in free form using two to three sentences. You may want to articulate the problem in form of a question or give the technical story. What is the issue that is motivating this decision or change? How is the decision architecturally significant - warranting an ADR? What is the high level design Approach? Leave the details for the options section below! -->

During execution, methods may encounter errorneous conditions that hinder or even prevent from fulfilling their original task. To allow the caller to correctly interprete the result or take counter measures to errors, it's necessary to inform higher layers on such conditions or anomalies. In software theory, several approaches exist. We have to decide for one of them and apply it, consistently.

It would be nice, if the solution does not depend too much on the programming language. Especially, an adaptation to C should be possible.

## Options <!-- optional -->

<!-- Give an austere description of the considered options. Concentrate on technical aspects. Give pros and cons, but do not argue, why this option was finally selected or not.
### [option 1]

[example | description | pointer to more information | …]

* Good, because [argument a]
* Good, because [argument b]
* Bad, because [argument c]
-->

In Python, there are several ways to inform a caller on errors and malfunction of a method.

### A: Throwing Exceptions

The method throws an Exception. It must be well documented, under which condition which Excpetion is thrown. It's the responsibility of the caller to handle the exception appropriately. 

* Good, because this is the pythonic way.
* Good, because the general reason of error could be coded into the Exception type, while a detailed explanation could be provided in the exception message
* Bad, because one must interprete the message in order get the reason. Problematic if the caller does not have access to the user interface or there is no UI to represent text messages.
* Bad, because largely incompatible with plain C.
* Bad, because it needs a lengthy exception handling passage in the calling code.

### B: Returning an Error Code only

The methods return only an error code. Any other method output is passed to the caller as an output parameter. The C equivalent is pass-by-reference.

* Good, because compatible with C programming language
* Good, because it ensures consistent semantics for return values throughout the whole library.
* Bad, because it increases the number of parameters. Output parameters could be mistaken or confused.
* Bad, because the by-reference-handling of parameters is tricky in Python
* Bad, because it feels quite un-pythonic.

### C: Returning an Error Code as part of a tuple

The method returns an error code as part of a tuple, as in:

```` return err, otherVal````

* Good, because the caller just has to evaluate a numeric value.
* Good, because there is no need for string processing, no dependence on the UI, no exception handling for the caller
* Bad, because there is no pendant in C; not really.

## Considerations <!-- optional -->

<!-- Document decision drivers, forces, concerns, ancillary or related issues, questions that arose in debate of the ADR. Indicate if/how they were resolved or mollified.

* [driver 1, e.g., a force, facing concern, …]
* [driver 2, e.g., a force, facing concern, …]
-->
* Error handling shall be leightweight, i.e. cause only a few lines in the caller's code
* Error handling shall be possible, even if there is no text-capable user interface
* The solution shall not prevent from or raise burden for porting the code to C.

## Decision

<!-- What is the change that we're proposing and/or doing? Document any agreed upon important implementation detail, caveats, future considerations, remaining or deferred design issues. Document any part of the requirements not satisfied by the proposed design. 

Chosen option: "[option 1]", because [justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force force | comes out best (see below)].
-->
Chosen option: "C", because this seems to be the best compromise: Prevent the calling-cascade from having to handle exceptions or process text messages, while still communicating the general reason / diagnosis of a problem. Choosing a "more pythonic" way without making a C-port impossible.

## Consequences

<!-- What becomes easier or more difficult to do because of this change?
* [e.g., improvement of quality attribute satisfaction, follow-up decisions required]
* [e.g., compromising quality attribute, follow-up decisions required]
-->

We are aware of the following:
* We must define consistently, the position of the error code within the returned tuple: first or last.

## Related ADRs <!-- optional -->

<!-- List any relevant ADRs - such as a design decision for a sub-component of a feature, a design deprecated as a result of this design, etc..
* [Depends on|Refined by|...] [ADR Title](URL)
--> 

* Refined by [Tuple order](return-values.md)

## References <!-- optional -->

<!-- List additional references.
* \[Title\]\(URL\)
-->

## Change Log <!-- optional -->

<!-- List the changes to the document. Sort by date in descending order.
* YYYY-MM-DD [Author]: [New status, if changed]. [Change]
-->

* 2024-07-12 O. Maye: PROPOSED. ADR created.
