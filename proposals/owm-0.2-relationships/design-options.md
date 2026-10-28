# OWM 0.2: Relationships and Identity

Design options for review. Prepared for the OARC / MSF Spatial Computing WG discussion of the Open World Model's next revision.

## Status and context

`spatial.owm/0.1` ships in SpatialDDS 1.8 as a provisional module. Its kernel is proven in production by three independent implementations in three roles: the reference venue demo (publisher and browser consumer), the `spatialdds-ros` library (robots publishing and consuming entities), and the SceneScape sidecar (a perception platform publishing entities it did not invent the schema for).

0.1 deliberately excluded relationship and identity semantics and reserved the slot. The demo's prototype had a working 7-member Relationship type and published a containment hierarchy (venue contains pond, pond contains ducks). It was left out of the module because one implementation and a sketch did not answer the question that matters: who asserts an edge, and on what basis. The prototype's own notes said the same thing: computed containment was left alone "until Relationship can carry a basis."

0.2 answers that question. This document lays out the options and the prior art, and recommends a composite.

## The problem

On today's bus, "the ducks are in the pond" is behavior, not data. The duck mover keeps them there, and any subscriber can infer it from coordinates, but no message says contains. That is the difference between a scene and a world model.

The hard part is not the edge type. It is that an open bus has no definitional authority. SceneScape solves identity and containment completely inside its own walls, and it does so by centralizing: one tracker owns identity, one scene configuration owns the hierarchy, containment is computed by the platform. Nobody can disagree with the tracker because nobody else gets a vote. The moment two publishers share a scene, that move is unavailable. The venue says robot-7; the sidecar says track-42 at the same spot. Whether they are one entity is a question 0.1 cannot even ask.

Two independent efforts converged on the same conclusion. The duck prototype declined to publish containment until edges could carry a basis. The SceneScape integration invented an id-join convention as a stopgap because the module had no way to state identity across publishers. When a closed-world platform and an open-world demo both point at attributable assertions, that is the design.

## Requirements, drawn from the implementations

1. Identity is a claim with a basis and a lifetime, not a primary key. Even SceneScape's centralized track ids churn: occlusion splits a track, re-identification stitches it later. Identity semantics must support making, revising, and retiring a same-as statement.
2. Edges need the same basis taxonomy as nodes. SceneScape's outputs map directly: zones are declared, tracks are observed, occupancy events are derived. The venue's containment is declared by the operator; a fuser's association is derived.
3. Both relationship-as-state and relationship-as-event exist. SceneScape consumers use occupancy (current state) and entered/exited (transitions). 0.2 must pick a primary representation and say how the other is expressed.
4. Nobody renames anyone else's entity. Publishers already mint ids in their own namespaces on the bus; cross-namespace identity must be additive and reversible.
5. Edges retire the way entities do, with reasons, and an edge whose endpoint retires must have defined behavior.

## Options

**A. Edges as claims.** A relationship is never a fact, always a statement: subject, predicate, object, asserter, basis, confidence, validity interval, lifecycle. The bus carries competing claims; consumers filter by asserter and basis rather than receiving one truth. Identity uses the same machinery: same-as is a claim, revisable and retirable, never a merge. The asserter can be grounded in the authenticated DDS publisher rather than invented, and signed later via DDS Security if federation needs it.

**B. Scoped fusion authorities.** Any participant may publish a derived view: fused entities and edges that reference the member claims they were computed from. A scene may bless one such fuser by convention. This centralizes within a scene where an operator wants it while staying decentralized across scenes. The multi-operator fusion demo already runs this pattern (FusedTrack referencing three operators' detections); 0.2 gives its output a spec home.

**C. Namespaced identity plus join claims.** Publisher-scoped ids stay as they are. Cross-namespace identity happens only through same-as claims from A. Conflation is always attributable and reversible.

**D. Attribute merge semantics.** For two publishers updating one entity's attributes, publisher-scoped fields with explicit merge rules (CRDT-style). This solves convergence, not identity: it says how to merge once two things are one, never whether they are. Deferred until multi-writer entities occur in practice.

## Prior art

- **Wikidata.** Statements with qualifiers, references, and ranks; contradictory claims coexist with provenance and consumers choose by rank. The claims model at planetary scale, and the closest existing system to what OWM needs.
- **W3C PROV-O.** The basis taxonomy (observed / declared / authored / derived) maps nearly one-to-one onto PROV agents, activities, and derivations. Borrowing its vocabulary as type URIs follows the module's existing "borrow vocabularies" rule.
- **owl:sameAs, as a cautionary tale.** Transitive logical identity propagates every mistake globally; the linked-data community documented this failure at length. The lesson is option C: same-as as a scoped, revisable claim, not an axiom.
- **OGC DE-9IM / GeoSPARQL.** Formal topological predicates (contains, within, touches, overlaps). The predicate vocabulary for spatial edges should be cited, not invented.
- **USD composition.** Many layers holding opinions about one scene, composed non-destructively by explicit strength ordering. The strongest prior art for multiple parties asserting over one world. It was built for authored content, which is why OWM's observed and derived side, with confidence and time, complements it rather than duplicating it.
- **Track fusion (JDL, ATC system tracks, STANAG 4676).** Decades of practice on identity for moving observed objects: local tracks, track-to-track association, system tracks referencing members. Option B is this pattern with a spec home.
- **W3C DID / Verifiable Credentials.** Signed claims by decentralized identifiers, if asserters must be verifiable beyond one venue. Overkill inside a venue; right-sized for the federation horizon.
- **RDF-star / named graphs.** Mechanics for statements about statements, if edges themselves ever need to be disputed on the bus.

The pattern across all of it: every mature system either centralized (SceneScape, ATC inside one facility) or moved to attributable, revisable claims (Wikidata, PROV, cross-facility fusion). There is no third answer in the prior art. The module's basis field means OWM chose the second some time ago; 0.2 finishes the choice.

## Recommendation

A as the wire model, B as a convention on top, C as the identity rule, D deferred.

In prior art terms the shape is a reified statement: its nearest relative is the Wikidata statement model (claim, references, rank), flattened into a property-graph edge and carried as a keyed instance on the bus, with the derivation field taken from PROV and from track fusion's system-track lineage.

Illustrative shape, not normative:

```
Relationship {
  id            // the edge's own identity, publisher-namespaced
  subject_ref   // entity ref, any namespace
  predicate     // type URI; spatial predicates cite DE-9IM/GeoSPARQL
  object_ref    // entity ref, any namespace
  basis         // observed | declared | authored | derived
  asserter      // grounded in the authenticated publisher
  confidence    // optional; in [0,1], comparable only within one asserter
  derived_from  // optional refs to member claims, for fused views
  stamp         // assertion time
  valid_from    // optional: the world time the claim is about
  valid_until   // optional; unset means "while asserted"
  meta          // namespaced qualifiers: roles, quantities, units
  lifecycle     // created / revised / retired, with a reason field
}
```

Four decisions are built into that shape rather than left to readers:

1. **Two clocks, kept apart.** `stamp` and `lifecycle` record when the assertion was made, revised, or withdrawn; `valid_from` and `valid_until` record the world time the claim is about. Without the second clock, a retirement cannot distinguish "the relationship ended" from "I no longer stand behind this claim", and consumers of occupancy or containment need that distinction daily. Transitions (entered, exited) derive from validity intervals and lifecycle together, so no second mechanism is needed for events.
2. **Qualifiers have a home.** The namespaced `meta` slot carries what bare triples cannot: a role on a membership, a quantity on an occupancy, units. Same escape-hatch pattern the module already uses on assets; it keeps the predicate vocabulary small instead of letting enrichment multiply predicates.
3. **Confidence is scoped honestly.** A scalar in [0,1], comparable only within a single asserter. Cross-asserter weighting is a consumer's model, never wire semantics; decades of fusion literature say calibrated cross-source confidence does not come for free, so the wire does not pretend it does.
4. **Retirement carries its reason in the type.** The claims type is exactly where a reason field must exist rather than ride an envelope.

**Proposition identity, the one convention publishers must follow:** one asserter holding one opinion about one (subject, predicate, object) revises the same edge id; it does not mint a new edge per update. A different asserter's opinion is always a new edge. Agreement between parties is then countable, and an asserter changing its mind is visible as history on one key.

Same-as is one predicate among others, carried by the same type.

## Consumption semantics

The wire shape is a third of the design; what consumers do with claims is the rest, and same-as is where it matters most:

- Claims coexist. A consumer filters by asserter, basis, validity, and confidence; nothing on the bus resolves disagreement for it.
- **Same-as is non-transitive by default.** No consumer implicitly computes global closure; the linked-data experience with transitive identity is the cautionary tale, since closure propagates every mistake to everything it touches.
- Closure, where wanted, is a **derived view**: a fuser publishes derived claims (basis derived, `derived_from` naming the member claims) asserting the merged identity or the fused edge. The dangerous computation is then itself an attributable, revisable, retractable claim, and consumers choose whose fusion to trust exactly as they choose any other asserter.
- Dangling endpoints: an edge whose subject or object has retired stays readable as history; whether it stays drawn is a consumer policy, with the edge's own validity interval as the default guide.

## What 0.2 does not attempt

Federation across venues and vocabulary governance remain named horizons, as in the original proposal. Both become easier once edges are claims: a venue's model is then a set of attributable statements that can be re-asserted, filtered, or disputed elsewhere.

## Open questions for the working group

1. Predicate set: adopt the DE-9IM core plus same-as and attached-to, or start narrower (contains, same-as) and grow by evidence.
2. Whether a scene's blessed fuser (option B) is spec text or deployment convention.
3. Topic shape: one relationship topic per scene, mirroring the entity topic's durability split.
4. Whether validity intervals are required on observed-basis claims or stay optional everywhere.
5. N-ary relations: the shape above is deliberately binary; cases needing three or more participants (between, handoffs, role-bearing membership) use an intermediate entity or wait for evidence that they deserve more.

## Sequencing

SpatialDDS 1.8 stamps with `spatial.owm/0.1` unchanged. 0.2 lands in the next vehicle (1.9, or a point release if ready sooner); the provisional label exists exactly so the module can rev on its own clock. Implementation evidence is lined up in advance: the venue demo restores declared containment, the SceneScape sidecar publishes derived occupancy edges, and the robot library consumes same-as to fuse a peer seen on the bus with one seen by its own sensors.
