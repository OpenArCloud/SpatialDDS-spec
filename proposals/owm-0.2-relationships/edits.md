# Edits proposed from the prototype

Each edit comes from the SpatialDDS-demo prototype of the recommended shape
(`oarc.relationship`, a demo-owned extension) and names its origin there.
§ references are to the demo's `docs/owm-02-worked-example.md`; "census" is
its `docs/owm-02-census.md`.

**Applied** edits were directed by a ruling and are made in
`design-options.md`. **Open** edits are proposed for the working group and
are not made.

| | edit | status |
| --- | --- | --- |
| E1 | Silence is not a contrary claim | applied: consumption semantics |
| E2 | `derived_from` names evidence records | applied: the shape |
| E3 | Parameterized predicates or identity-bearing qualifiers | applied: open question 6 |
| E4 | Lifecycle members named `state` / `state_reason` | open |
| E5 | Three retirement causes, and their `valid_until` | the causes applied (decision 4); `valid_until` open |
| E6 | A cascade is per asserter | open |
| E7 | The basis of a computed geometric edge | open |
| E8 | Declared as enforced policy | open |
| E9 | A claim against a published extent is about the model | open |
| E10 | Hysteresis | open |
| E11 | A relationship lane carries liveliness | open |

## E1. Silence is not a contrary claim

Two near asserters at 6 m and at 15 m: between 6 and 15 m one asserts and
the other is silent. The silent one has not said "not near", and a consumer
must not read it so. *Origin:* census §1.2, where a second near threshold
was rejected as the coexistence staging for exactly this reason.

## E2. `derived_from` references evidence records

Claims or entities, not claims only, each as (topic, key, stamp): the sample
read, not just the record's name. *Origin:* §1.6. The near fuser reads poses
from the `model_pose` fast lane, and the robot's latched `Entity` is not
restamped on every pose, so an entity id alone does not say which evidence
was read. In the film, 140 of 140 references stamped inside the recording
resolve to a sample in it.

## E3. Parameterized predicates or identity-bearing qualifiers

With a nearness threshold only in `meta`, "near at 15 m" and "near at 6 m"
share one predicate, and proposition identity (subject, predicate, object)
cannot tell them apart. The prototype puts the threshold in the predicate
URI's fragment, `https://demo.spatialdds.org/owm/0.2/predicate/near#15m`,
and also in `meta` for machine reading. *Origin:* census §2. GeoSPARQL 1.1
has no nearness relation, only the `geof:distance` functions, so any near
predicate is someone's own URI.

## E4. Name the lifecycle members as Entity names them

`state` and `state_reason`, not `lifecycle` and `reason`. *Origin:* the
SDK's `Writer.withdraw()` finds a terminal sample's members by those names.
Spelled as drafted, a withdrawal rewrites the edge as it last was, and its
reason survives only in a recording's metadata.

## E5. Three retirement causes, each with its `valid_until` rule

- no longer holds: `valid_until` is the evidence that showed it;
- subject unobserved: the last evidence that showed it true, a lower bound;
- asserter stopped: unset, because the world was not consulted.

A killed asserter withdraws nothing; its edges stand with liveliness lost.
The document should say a consumer reads that as "nobody asserts this now",
not as a retirement. *Origin:* §1.7 and §1.8. In the film, 84 retirements:
79 no longer holds, 4 subject unobserved, 1 asserter stopped; a SIGKILLed
asserter's edge stood with no dispose.

## E6. A cascade is per asserter

Retiring an entity cascades the retiring service's own edges in front of
its tombstone. Other asserters' edges about it dangle until each sees the
withdrawal: a ghost window bounded only by their reading. *Origin:* §1.1,
the model service against duck_mover and the zone watches.

## E7. The basis of a computed geometric edge

The robot within the fountain is computed from an observed pose and an
observed extent. The prototype calls it OBSERVED, as ruled, but it is a
computation over two observations. Does computing make an edge DERIVED?
*Origin:* §1.3.

## E8. Declared as enforced policy

An edge whose truth its asserter maintains, rather than measures, is
DECLARED, and is worth publishing because a snapshot cannot compute it: it
says where a duck will be kept, not where one is. *Origin:* §1.2.

## E9. A claim against a published extent is a claim about the model

The fountain's extent is a coarse locator, not a boundary. An edge computed
against it inherits that gap and makes it visible on the wire. Cross-reference
the module's footprint question. *Origin:* §1.3 and §1.5, and the demo's
`keepout.py`.

## E10. Hysteresis

An edge on a threshold that a behaviour pushes things across churns at that
threshold: 73 near edges in 540 s, because the ducks flee the robot at the
same 15 m. Should a derived predicate carry hysteresis in its definition, or
is churn the honest record of a behaviour that has none? *Origin:* §1.6.

## E11. A relationship lane carries liveliness

A binding that drops writer liveliness makes a killed asserter's edge
indistinguishable from a live one. The web binding's event set already has
`liveliness`; the design should require that a relationship lane carry it.
*Origin:* §1.8, where the demo's pump dropped it until the prototype.
