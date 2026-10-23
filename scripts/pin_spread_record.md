# Consumer pin-spread — recorded runs

`scripts/check_pin_spread.py` reads each downstream consumer's declared SpatialDDS
spec pin (the spec commit it generated/vendored against) and reports it against
spec `main` HEAD with the commit distance. It is a **reporting instrument**, not a
gate: a lagging pin is a scheduled resync, not a build failure. Each run is a
point-in-time snapshot — distances grow as spec `main` advances past a fixed pin.

## First record — 2026-10-22 (spec `main` at `b4f9a8e`, the 1.8 stamp candidate)

```
consumer               declared pin  distance behind spec main  source (file:line)
---------------------  ------------  -------------------------  ------------------------------------------------------------------
SpatialDDS-demo        9c3e1f2       31                         SpatialDDS-demo/ar_demo/SPEC_COMPLIANCE.md:3
spatialdds-ros         9c3e1f2       31                         spatialdds-ros/spatialdds_idl18/PROVENANCE.md:9
spatialdds-scenescape  424a8b3d8e0c  52                         spatialdds-scenescape/idl/PROVENANCE:12
openvps                5ee5f96       20                         openvps/maplocalizer/server/vendor/spatialdds_idl18/__init__.py:11
spatialdds-web         9c3e1f27c176  31                         spatialdds-web/webjson/PROVENANCE:18
```

Notes for this record:

- demo, ros, and web all pin the same spec commit `9c3e1f2` (web records it as the
  full SHA `9c3e1f27c176…`); scenescape is furthest behind at 52; openvps is the
  most current at 20.
- All five declared pins resolve to ancestors of HEAD (no divergent/unknown pins).
- Resyncs to the `v1.8` tag are tracked as follow-up batches in each consumer repo;
  they are out of scope for the stamp itself.
