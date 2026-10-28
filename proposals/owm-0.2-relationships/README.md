# Proposal: OWM 0.2 relationships and identity

**Status: proposal. Not normative, and not part of any stamped SpatialDDS
version.** Nothing in this folder changes what `spatial.owm/0.1` (SpatialDDS
1.8, Appendix E) says. It is the design under discussion for the reserved
gap that 0.1 leaves open: per-edge basis, confidence and retraction
(`sections/v1.8/02-conventions.md`, `sections/v1.8/future-directions.md`).

| file | what it is |
| --- | --- |
| [`design-options.md`](design-options.md) | The design document: options A–D, prior art, the recommended shape and its consumption semantics. Added verbatim as supplied, then edited only where a ruling directed it (see its history). |
| [`edits.md`](edits.md) | Edits proposed from implementation evidence. The ruled ones are applied to the design document; the rest wait for the working group. |

## Implementation evidence

The SpatialDDS-demo repository carries a prototype of the recommended shape
as a demo-owned extension, `oarc.relationship`, registered through the SDK's
`sd.dds.extend()`, on `spatialdds/<scene>/world/oarc.relationship/v1`. It is
not a spec type. Its record of what it measured is
`docs/owm-02-worked-example.md` in that repository, and its census
`docs/owm-02-census.md`. Every edit in `edits.md` names its origin there.
