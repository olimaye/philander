# Return values and tuple order

## Status

<!-- one of [proposed | rejected | accepted | deprecated | superseded by [linked ADR](adr-link.md)] -->

proposed

## Date <!-- optional -->

<!-- YYYY-MM-DD (no period!) Date when this decision was last updated -->

2024-07-11

## Deciders <!-- optional -->

<!-- List everyone actively involved in the decision! Do not assume any relation between order and importance. -->
* O. Maye
* C. Bellgardt

## Context

<!-- Describe the context and problem statement, e.g., in free form using two to three sentences. You may want to articulate the problem in form of a question or give the technical story. What is the issue that is motivating this decision or change? How is the decision architecturally significant - warranting an ADR? What is the high level design Approach? Leave the details for the options section below! -->

Some of the interface methods return values or objects to be processed further by the caller. Further, the success or reason of failure for a method call is indicated by an error code. It would violate good programming practice to let the return value implicitly encode the success-or failure indicator, e.g. by using NULL values or "-1". Further, the specific reason of failure would even be impossible to encode.

For that reason, these methods must return both, the semantic return value or object and an error code.

In Python, returning two values can be achieved by the means of tuples. This decision is to clarify the order of elements in this tuple.

## Options <!-- optional -->

<!-- Give an austere description of the considered options. Concentrate on technical aspects. Give pros and cons, but do not argue, why this option was finally selected or not.
### Option A

[example | description | pointer to more information]

* Good, because [argument a]
* Good, because [argument b]
* Bad, because [argument c]
-->

As far as we can see, there are only two options: Will the error code be the first or the last element in this tuple?

### Option A

The error code is placed first, as in:
````return err, tmp, hum````

* Good, because [argument a]
* Good, because [argument b]
* Bad, because [argument c]

### [option 2]

[example | description | pointer to more information | …]

* Good, because [argument a]
* Good, because [argument b]
* Bad, because [argument c]

### [option 3]

[example | description | pointer to more information | …]

* Good, because [argument a]
* Good, because [argument b]
* Bad, because [argument c]

## Considerations <!-- optional -->

<!-- Document decision drivers, forces, concerns, ancillary or related issues, questions that arose in debate of the ADR. Indicate if/how they were resolved or mollified.

* [driver 1, e.g., a force, facing concern, …]
* [driver 2, e.g., a force, facing concern, …]
-->
* Power consumption argues for option #1
* Price is best for option #2
* Availability is largely unknown for all of them
* Programming experience must be weighted highest and exists only für option #3.


## Decision

<!-- What is the change that we're proposing and/or doing? Document any agreed upon important implementation detail, caveats, future considerations, remaining or deferred design issues. Document any part of the requirements not satisfied by the proposed design. 

Chosen option: "[option 1]", because [justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force force | … | comes out best (see below)].
-->

Chosen option: "[option 1]", because [justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force force | … | comes out best (see below)].

## Consequences

<!-- What becomes easier or more difficult to do because of this change?
* [e.g., improvement of quality attribute satisfaction, follow-up decisions required, …]
* [e.g., compromising quality attribute, follow-up decisions required, …]
* …
-->

We are aware of the following:
* we know, how to program it
* it's expensive and hard to get.

## Related ADRs <!-- optional -->

<!-- List any relevant ADRs - such as a design decision for a sub-component of a feature, a design deprecated as a result of this design, etc..
* [Depends on|Refined by|...] [ADR Title](URL)
--> 

* Depends on [client-server](client-server.md)

## References <!-- optional -->

<!-- List additional references.
* \[Title\]\(URL\)
-->

* \[Title\]\(URL\)

## Change Log <!-- optional -->

<!-- List the changes to the document. Sort by date in descending order.
* YYYY-MM-DD [Author]: [New status, if changed]. [Change]
-->

* 2024-01-20 G.Surname: PROPOSED. ADR created and first two options #1 and #2 outlined.