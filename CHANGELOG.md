# Changelog

| Version | Date       | Key Changes |
|---------|------------|-------------|
| 1.8     | Draft      | **Additive only** (no breaking changes; 1.7 samples remain valid): frame metric scale on `FrameRef` (`ScaleStatus` + `has_scale`/`scale_status`/`meters_per_unit`/`display_unit`, §2.13); directional uncertainty `CovMatrix cov` on `GeoAnchor` plus the `anchor.cov` manifest mirror; polygon/prism geometry on `SpatialZone` (`has_polygon`/`polygon`/`z_min`/`z_max`) and a new `Vec2` primitive; normative keyed-instance removal convention (§2.14); clarified that vertical coverage extent rides the 3D `aabb` (§3.3.4); new Appendix L (Resolution Quality Conformance, Normative) and Appendix M (Documented Operational Conventions, Informative); Gaussian-splat content note. Manifest minor floor unchanged at ≥ 7. All modules swept to `/1.8`; gates repointed to 1.8 (1.7 remains buildable, ungated). **Batch 2:** observer pose covariance on `Detection3D`/`FusedTrack` (Intel SceneScape) with a `CovScope` composition-scope guard; `MapAlignment.scale_ratio` similarity member. **Revision 2026-10-15:** optional `manifest_uri` on `GeoAnchor` (a §7.5-resolvable content reference) and optional `durability` on `TopicMeta` (the DDS kind for N.7 manifest entries), both APPENDABLE and wire-compatible. |
| 1.7     | 2026-08-23 | **Breaking** (pre-adoption instability clause, §3.1): `Time.sec` widened to int64; compound `@key` on `Node`/`Edge` and `mapping::Edge`; `GeoPose` orientation fixed to the local ENU tangent frame (removed `frame_kind`/`frame_ref`, `GeoFrameKind`); `TileMeta` uses a single `Aabb3 aabb` (removed `min_xyz`/`max_xyz`/`lod`); removed `BlobChunk.last`; `CoverageResponse` returns compact `ServiceSummary` rows; `caps.features` is now `sequence<string>` (removed `FeatureFlag`); removed `ProfileSupport.preferred`, `CoverageElement.type`, `CoverageQuery.expr` (and Appendix F.X). Policy: single-identifier syntax `spatial.<profile>/MAJOR.MINOR`; all modules unified to `/1.7`; consolidated `/.well-known/spatialdds/{bootstrap,resolver,search}` namespace; bootstrap auth via `auth_hint`; Appendix G promoted to Normative. Findings batch 2 (draft rev): breaking sequence-bound reductions (`BlobChunk.data`, `KeyframeFeatures.descriptors` → 65535); additive fields across discovery/semantics/vision/vio/events/common; new QoS profiles and registry rows. |
| 1.6     | 2026-07-23 | Added PlannedTrajectory and EntityBinding to core; extended CovKind (POSE6_TWIST6, ROT3); coverage_window in CoverageElement; new conventions for enum serialization, time semantics, bbox ordering, schema stability, topic version stability, spatial privacy; expr deprecation sunset for 2.0; DNS authority lifecycle and resolution-failure fallback chain; demoted Neural and Agent to informative examples; reframed Appendix H as a world-model grounding narrative; new Appendix K (IDL package layout); selective per-profile minor bumps. |
| 1.5     | 2026-04-29 | Finalized 1.5: added FramedPose/NodeGeo redesign, Mapping and Spatial Events extensions, geospatial DNS-SD discovery, restored HTTP discovery binding, four-dataset conformance suite (nuScenes/DeepSense 6G/S3E/ScanNet), and provisional rf_beam profile. |
| 1.4     | 2026-02-07 | Finalized 1.4 draft text and examples; regenerated full spec. |
| 1.3     | 2025-10-03 | Documented SpatialDDS URIs and ABNF; added frame transforms (#30) and bounding volumes (#29); new HTTP-capable discovery model; general restructuring. |
| 1.2     | 2025-09-14 | Added anchor manifest example, refined schema, and standardized bounding-box arrays. |
| 1.1     | 2025-07-01 | Initial concept release of the SpatialDDS specification. |

## Version 1.8 Revision 2026-10-15

This is a revision to 1.8, not an erratum. An erratum fixes a contradiction;
these add features. 1.8 was opened for one bounded revision window, and this
entry is its full and final contents: two additive members. After this window
the spec is locked again; everything else goes to 1.9.

### GeoAnchor content reference

`GeoAnchor` gains an optional `manifest_uri`. An anchor MAY name a content
manifest, resolvable per §7.5, so durable world-locked content can be bound to
the anchor that places it. The member mirrors `ContentAnnounce.manifest_uri`
exactly: the same `SpatialUri` type, the same name, and the same
empty-is-absent mechanism with no guard. It is appended under APPENDABLE, so the
change is wire-compatible. An anchor that names no content is byte-identical to a
pre-revision anchor, and existing recordings decode unchanged. The `SpatialUri`
typedef now lives in `spatial::common` so core and discovery share one spelling;
the move does not change the wire.

Prose: Appendix C states the binding semantics, that content reached through the
reference inherits the anchor's frame, precision, method, and covariance as its
claim level. §8.2.1 documents `anchor.manifest_uri` in the anchor manifest. The
Appendix N conformance scenario §8.2 becomes a live anchor-resolve check, which
reports UNEXERCISED where no served anchor carries a reference.

Origin: 1.9 candidates entry 2, raised by the anchor-bearing sample work in
spatialdds-web where an anchor carrying a content reference could not be
expressed in 1.8. The fountain-anchors sample and its publish path are the
evidence.

### TopicMeta durability

`TopicMeta` gains an optional `durability`, carrying the DDS kind `VOLATILE` or
`TRANSIENT_LOCAL`. A gateway bridging a DDS bus can now populate the `durability`
that Appendix N.7 requires on a manifest topic entry from the bus type, instead
of having no source for it. It is appended under APPENDABLE, so a `TopicMeta`
producer that omits it is unchanged in meaning and on the wire, and existing
recordings decode unchanged. This closes finding 17: N.7 required a field the bus
type could not supply.

Census of the cost. `TopicMeta` is embedded in `Announce.topics`, so every
discovery announce carries it. The committed fountain-anchors recording's
announce, and any sidecar or demo producer that publishes an `Announce`, carry
`TopicMeta` without `durability` until they regenerate. On the wire this is
invisible, APPENDABLE keeps it byte-identical. In the web binding, where a served
announce validates against the regenerated schema, it reads as the one-revision
binding lag exactly as an anchor without `manifest_uri` does, and clears on the
same web re-author. The queuing-retail recording carries no announce and is
unaffected.

Origin: 1.9 candidates entry 3, raised while adding a service announce to the
fountain-anchors recording, the bridged shape's first concrete blocker found
before anyone built one.

## Version 1.8 — Finding 31 (`GeoAnchor.checksum`), 2026-10-16

Resolves the finding held for a ruling in the 25–33 editorial batch. Two parts,
answered separately.

- **§7.5.2 integrity signals — erratum.** The resolve-response list counted "a
  checksum field in the body" as a sufficient integrity signal with no condition
  on whether a receiver could check it, so an endpoint could satisfy an integrity
  requirement with a string that integrity-checks nothing. The list now reads: an
  `ETag` or `Digest` header always qualifies; a body checksum qualifies **only
  where its computation is defined and reproducible by the receiver** from what
  was served. A manifest's `assets[].hash` (defined `<algorithm>:<hex>`)
  qualifies; an undefined digest does not. This is a correction, not a feature:
  it removes an over-promise from the list. `web-binding/conformance/run.py`'s
  `_has_integrity` is tightened to match (a bare `checksum` substring no longer
  counts; `ETag`/`Digest` and defined asset hashes still do).
- **What `checksum` digests — deferred to 1.9.** Defining the digest subject and
  form is recorded as a 1.9 problem statement in Future Directions, with the
  proposed semantics named: the `sha256:` of the canonical N.1 JSON of the record
  with `checksum` itself omitted (the record-builder convention, recomputable by
  any receiver; the only non-self-referential, APPENDABLE-stable choice). Not
  landed in 1.8: assigning the required field a meaning it never had would
  retroactively make records computed under any other convention nonconformant,
  which is a feature decision, not an erratum. Evidence it cannot be left as-is:
  two conventions already ship in SpatialDDS-web (authoring-input vs
  record-canonical), both correct and mutually incompatible.

Origin: demo-agent report ad94aea (finding 31); rulings from James.

## Version 1.8 — Finding 39 (conformance runner), 2026-10-16

A reporting fix in the web-binding conformance runner; no normative text and no
IDL change. SpatialDDS-web 0.2.0 made an empty registry the normal starting
state (`python -m spatialdds.serve --authority registry.example --publish` serves
a conformant surface with no data in it, records arriving later). Against that
shape the runner reported five data-dependent checks as **failures** —
`every resource validates against its published schema`, `canonical form on the
wire`, `latched state is GET with ETag, Cache-Control and 304`, `§8.1 hello
spatial in ten lines`, `§8.4 third-party reader` — where its own UNEXERCISED
vocabulary is the right answer, the same it already applies to the resolver,
access classes, the QoS subset, and the §8.2 anchor-resolve flow. A check whose
subject matter is absent is unexercised with the reason stated, not failed.

- `web-binding/conformance/run.py`: the five checks now `raise Skip` (UNEXERCISED)
  on genuine absence — no resource advertised, or every advertised resource gated
  or empty — instead of asserting on an empty count. The **teeth are kept and
  verified**: `schema_validity` and `latched_get` still assert `200` on every
  advertised path, so an endpoint that *advertises* a resource and 404s it still
  fails; the content checks still fail on a served-but-malformed instance. The
  softening applies only to zero observations, never to a false claim.
- `web-binding/conformance/empty_registry_probe.py` (new): drives all 14 checks
  against a mocked endpoint — no DDS, no gateway — in three states and asserts
  the empty registry certifies as 6 passed / 0 failed / 8 skipped, a 404 on an
  advertised resource still fails, and a 200 missing a required field still
  fails. The class is closed, not the instance.
- **Acceptance record for a fresh (empty) deployment**, verbatim:
  `14 checks: 6 passed, 0 failed, 8 skipped (skipped: every resource validates
  against its published schema, canonical form on the wire, latched state is GET
  with ETag, Cache-Control and 304, access classes, both directions, the carried
  QoS subset is observable, the rest absent, §8.1 hello spatial in ten lines, §8.2
  anchor resolve flow, §8.4 third-party reader, published schemas only)`. Both
  populated shapes are unchanged (the new branches never fire when resources are
  served). Origin: SpatialDDS-web 0.2.0 batch, finding 39.

## Version 1.8 — Findings 25–33 (editorial), 2026-10-15

Editorial and documentation fixes closing a queue of findings raised by the
SpatialDDS-web publish work. No IDL changes, no normative prose changes, and the
112 generated JSON Schemas are byte-identical. The example manifest files and the
web-binding contract/gates are the only things touched.

- **Example manifests (findings 27, 28).** All four `manifests/v1.8/*.json`
  declared `"schema_version": "spatial.core/1.7"` — stale by a minor version and
  under a key the prose never uses. Replaced with the `{id, profile, rtype}`
  envelope §8.1 makes REQUIRED and §3.3.0's worked example carries: `profile` is
  `spatial.manifest/1.8`, and each file now states the `spatialdds://` URI it
  answers to so it is resolvable per §7.5.2 (previously none did). The fix
  direction came from the prose, which is the authority; the derived VPS manifest
  in SpatialDDS-web carries no `schema_version` and is not the template. §8.1
  already mandates `id`, so finding 28's suggested extra sentence in §7.5.2 is
  redundant and was not added. Origin: demo-agent report e87758e.
- **Mapping inverse documented (finding 26).** `web-binding/MAPPING.md` gains an
  "Inverse — the lift direction" section: the mapping is bidirectional, a lifter
  applies exactly three rules that differ from the naive inverse
  (`int64`/`uint64` decimal strings, base64 octet runs, `"type"` tag versus the
  discriminator member) and everything else round-trips naively, with one worked
  `int64` example both directions. A publishing client needs this and the
  projection documented only the forward direction. Origin: demo-agent report
  d2e9c50/9252b8c.
- **Octet-run golden vector (finding 33 sweep).** Confirmed `gen.py` decides
  octet-ness on `inner == "types.uint8"` — the spelling idlc renders from
  `sequence<uint8, N>`, the spelling the IDL actually uses — and carries no dead
  `"octet"` branch, so the generator is right for the right reason. Added
  `golden/blobchunk_octet_run.json` so the rule has a spec-side exercise
  independent of the web repo's authored BlobChunk; `gate_roundtrip` now verifies
  9 golden vectors. Origin: demo-agent report 3f00af3.
- **Content withdrawal (finding 25, feature-gap half).** The absence of a typed
  dispose for content (`Depart` covers services only) is recorded as a 1.9
  problem statement in Future Directions, citing the SpatialDDS-web endpoint's
  out-of-band `spatialdds-web:dispose` MCAP record as evidence. The reading-side
  half (addressing the four-segment `spatialdds/discovery/depart/v1` topic over
  the web binding) was already resolved by N.3's short-topic rule in finding 16
  (68cf1f7) and needed no new erratum. Origin: demo-agent report d2e9c50/9252b8c.
- **`GeoAnchor.checksum` (finding 31).** Characterized, no change landed: whether
  to define what `checksum` digests and whether §7.5.2's integrity-signal list
  should require verifiability are held for a ruling, since either would change
  what existing records mean. Origin: demo-agent report ad94aea.

## Version 1.8 (Draft) — Batch 2

Backward compatibility with 1.7 **and** with 1.8 Batch 1 is preserved. Every
change is additive and APPENDABLE-safe: two new enums and trailing fields only;
no field removed, retyped, or reordered, and no required field added. A
1.7-shaped sample of every touched type (`Detection3D`, `FusedTrack`,
`MapAlignment`) remains valid under the 1.8 IDL.

### Additive IDL
- `semantics::Detection3D`: appended observer pose covariance —
  `has_observer`/`observer_position` (sensor origin in `frame_ref`, metres)/
  `observer_cov` (COV_NONE when absent), plus the composition-scope pair
  `has_observer_cov_scope`/`observer_cov_scope`.
- `semantics::FusedTrack`: appended the aggregate `has_observer_cov`/
  `observer_cov` and the same composition-scope pair. Per-source observer
  uncertainty is carried out-of-band via `core::EntityBinding` → `core::Node.cov`.
- `common::CovScope`: new enum `{COV_SCOPE_LOCAL, COV_SCOPE_COMPOSED}` (absent =
  LOCAL) qualifying whether observer uncertainty is already folded into a stated
  covariance.
- `mapping::MapAlignment`: appended `has_scale_ratio`/`scale_ratio` — the
  similarity factor (`from`-length × `scale_ratio` = `to`-length; 1.0 when
  scales match) that the rigid `T_from_to` cannot carry.
- *Observer covariance contributed by the Intel SceneScape engineering team
  (September 2026 spec review).*

### Normative prose
- Appendix D (Semantics / Perception): observer-covariance semantics — units
  m²/m·rad/rad², row-major, observer pose in `frame_ref`; fused-vs-per-source
  guidance; `CovScope` composition rules with the absent-is-LOCAL rationale.
- Appendix D (SLAM Frontend): a `TrackObs`'s observer covariance is the `cov` of
  the `core::Node` named by its `node_id`.
- Appendix D (Mapping): `scale_ratio` consistency with §2.13 `meters_per_unit`,
  `SCALE_UNKNOWN` handling, and the cross-frame conversion cross-reference.
- Appendix A (typed-first rule): covariance — observer covariance included — MUST
  be carried as typed fields, never `MetaKV`/`json`.

### Provisional module (separately gated)
- **`spatial.owm/0.1`** — a provisional Open World Model module (Appendix E):
  `Entity` (basis + lifecycle), the `ModelPose` fast lane, and keyed
  `ModelCommand` with declines. Independently versioned and exempt from the 1.x
  additive guarantee; relationship/identity semantics are reserved, not frozen.
  Shapes imported from SpatialDDS-demo `oarc_model` at commit `e0fd7d2`. Carried
  as a separate commit under its own ratification gate.

## Version 1.8 (Draft) — Batch 1

Backward compatibility with 1.7 **is** preserved. Every change in this batch is
additive and APPENDABLE-safe: no field was removed, retyped, or reordered, and
no required field was added. A 1.7-shaped sample of every touched type remains
valid under the 1.8 IDL. Topic names retain the `/v1` segment. All module
identifiers are swept to `/1.8`; the build and CI gates are repointed to 1.8,
and 1.7 remains buildable but ungated.

### Additive IDL
- `common::FrameRef`: appended frame metric scale — new `enum ScaleStatus`
  (`SCALE_UNKNOWN`/`SCALE_DECLARED`/`SCALE_DERIVED`) and
  `has_scale`/`scale_status`/`meters_per_unit`/`display_unit`. Absence means
  metric (1 unit = 1 m), so every pre-1.8 publisher stays correct; an
  unestablished scale MUST be stated explicitly as `SCALE_UNKNOWN` (§2.13).
  *Credit: G. Sörös, whose map-autoscaling work motivated and prototyped the
  design.*
- `core::GeoAnchor`: appended `CovMatrix cov` (COV_NONE when absent) for
  directional anchor uncertainty, in the anchor's local ENU tangent frame at the
  encoded GeoPose; `confidence` retained as a monotone scalar summary
  (Proposal A). Mirrored in the manifest as optional `anchor.cov` (§8.2.1).
- `common::Vec2`: new 2D primitive, added beside `Vec3`, as an **APPENDABLE struct** `{ double x; double y; }`. Introduced earlier in the 1.8 draft as `typedef double Vec2[2]` and changed before release: an array typedef used as a sequence element is legal IDL that several widely-used consumers decline, and it made `SpatialZone` and `CrossingLine` unreadable in the first third-party viewer to open a 1.8 recording. APPENDABLE, not FINAL, and deliberately so: FINAL would be byte-identical to `double[2]` (68 octets either way on a 3-element sequence) but a widely deployed omgidl deserializer requires a per-element delimiter regardless of declared extensibility, so a FINAL element is unreadable there while an APPENDABLE one is readable by both conformant and non-conformant readers -- strictly dominant at four octets per vertex on once-latched definitions. Two drafting rules recorded beside the type: array typedefs are not to be used as sequence element types, and structs used as sequence elements should be APPENDABLE.
- `events::SpatialZone`: appended polygon/prism geometry
  (`has_polygon`/`polygon` as `sequence<Vec2, 256>`/`z_min`/`z_max`). The polygon
  takes precedence over `bounds` for containment; `bounds` MUST still carry the
  ring's axis-aligned box for box-only consumers.

### Normative prose
- §2.13 **Frame Scale** — the normative rules for the fields above
  (default-is-metric, explicit-unknown, cross-frame conversion, covariance in
  frame units squared).
- §2.14 **Keyed-Instance Removal** — a deliberately removed latched keyed
  instance MUST publish a final terminal sample with a human-readable reason and
  then dispose; liveliness loss is not removal. `EntityBinding` named explicitly.
- §3.3.4 — clarified that vertical/altitude coverage extent is expressed via the
  3D `aabb` (`min_xyz.z`/`max_xyz.z`), not via new fields.
- **Appendix L: Resolution Quality Conformance (Normative)** — mechanism-agnostic
  calibration tests for the existing quality fields (NEES/χ² covariance
  calibration, status honesty, prior-replay non-regression, cross-session anchor
  stability, reporting + `caps.features` citation). Evaluation-set governance is
  flagged as an open question in an editor's note.

### Informative prose
- **Appendix M: Documented Operational Conventions** — two demo-proven patterns
  (keyed commands with explicit declines; shared multi-writer lanes with
  one-writer-per-key for physical-thing entities). Description only, no new IDL.
- §6 Future Directions: a **Queryable Coverage Response** problem statement
  (area-scoped coverage answer merged with the announce cache). Problem statement
  only, not IDL.
- §8 manifests: a Gaussian-splat content note — splat scenes are carried by
  reference like all content, via glTF + `KHR_gaussian_splatting` and SPZ.

## Version 1.7 - 2026-08-23

Backward compatibility with 1.6 is **not** preserved. Per the pre-adoption
instability clause (§3.1), MINOR revisions in the 1.x series MAY include
breaking schema or wire changes. Topic names retain the `/v1` segment.

### Breaking (wire)
- `builtin::Time.sec`: `int32` → `int64` (no year-2038 limit).
- `core::Node` / `core::Edge`: instance key is now compound (`map_id`, id).
- `mapping::Edge`: instance key is now compound (`map_id`, `edge_id`),
  aligning with `core::Node`/`Edge`.
- `core::GeoPose`: removed `frame_kind` and `frame_ref`; the quaternion is
  fixed to the local ENU tangent frame at the encoded position (OGC GeoPose).
  Removed `enum GeoFrameKind`.
- `core::TileMeta`: replaced `min_xyz`/`max_xyz` with a single `Aabb3 aabb`;
  removed `lod` (redundant with `key.level`).
- `core::BlobChunk`: removed `last`.
- `disco::CoverageResponse`: returns `sequence<ServiceSummary>` (new compact
  row type) instead of `sequence<Announce>`.
- `disco::Capabilities.features`: `sequence<FeatureFlag>` → `sequence<string>`;
  removed `struct FeatureFlag`.
- `disco::ProfileSupport`: removed `preferred`; `name` now carries the module
  family (e.g., `"spatial.core"`).
- `disco::CoverageElement`: removed `type` (derivable from `has_bbox`/`has_aabb`).
- `disco::CoverageQuery`: removed `expr`; deleted Appendix F.X (query
  expression grammar). Use `filter` exclusively.

### Policy
- Single identifier syntax: `spatial.<profile>/MAJOR.MINOR` everywhere; the
  dual `name@MAJOR.MINOR` form is retired.
- All modules version together with the spec; every `MODULE_ID` and
  `schema_version` in 1.7 is `spatial.<profile>/1.7`.
- Added the pre-adoption instability clause (§3.1).
- Consolidated the well-known namespace to a single RFC 8615 registration:
  `/.well-known/spatialdds/{bootstrap,resolver,search}`.
- Bootstrap authentication unified with `auth_hint` (removed the `auth.method`
  enum).
- Appendix G (Frame Identifiers) promoted from Informative to Normative.
- Manifest `profile` MUST match `spatial.manifest/1.<minor>` with `<minor>` ≥ 7.

### Findings batch 2 (draft rev)

Implementation findings from the demo repo (`spatialdds-1.7-findings-update-plan.md`).

Breaking (wire):
- `core::BlobChunk.data`: sequence bound `262144` → `65535` (binding-compatible;
  §3.2). Sweep confirms no other sequence bound in Appendices A–D or provisional
  IDL exceeds 65535.
- `slam_frontend::KeyframeFeatures.descriptors`: bound `1048576` → `65535`;
  larger descriptor sets ride blob transfer (`BlobRef` + `BlobChunk`).

Additive (IDL):
- `common::MetaKV`: added `sequence<KV, 64> entries` (typed extension rows) and a
  new `common::KV` struct. Typed-first extension rule added (Appendix A).
- `semantics::Detection3D`: added `has_velocity` + `Vec3 velocity`.
- Finding 5 (2D detections) resolved by *registration*, not addition: the existing
  labelled, scored, image-space `semantics::Detection2DSet` is now registered as
  topic type `detection2d`. No new type was added.
- `disco::ServiceKind`: appended `SENSING`, `INFRASTRUCTURE`, `FUSION`.
- `events::EventType`: appended `PREDICTED_CONFLICT`; `SpatialEvent` added
  `participant_ids`. Prediction semantics normative note added.
- `vio::ImuSample`: added `has_accel_cov`/`accel_cov` + `has_gyro_cov`/`gyro_cov`
  (`core::CovMatrix`).
- `disco::CoverageElement`: added `has_circle` / `circle_center[3]` /
  `circle_radius_m`. Circle coverage semantics added (§3.3.4).
- `disco::Announce`: added `coverage_source_ids` (empty = self-asserted). Derived
  coverage semantics added (§3.3.4).
- `sensing.common::Codec`: appended `PNG`.

Non-IDL:
- §3.3.3 QoS table: renamed "Typical Deadline" → "Deadline"; Deadline now normative
  and specified only on periodic stream profiles (sporadic/latched/request-reply =
  "—"); `RADAR_RT` reliability "Partial" → "Best-effort" (no partial-reliability
  kind in DDS); added normative QoS-surface and request/offered notes; added five
  profiles: `DET_RT`, `LIDAR_RT`, `IMU_RT`, `SENSOR_META`, `ANCHOR_DELTA`.
- §3.3.2 registry: added ten rows (`framed_pose`, `detection3d`, `detection2d`,
  `lidar_frame`, `lidar_meta`, `radar_tensor_meta`, `video_meta`, `rf_beam_meta`,
  `imu_sample`, `anchor_delta`) and a registry-completeness rule; new registry
  gate.
- Provisional IDL relocated: `examples/rf_beam_example.idl` →
  `provisional/rf_beam.idl`; `examples/radio_example.idl` → `provisional/radio.idl`
  (Appendix E, Appendix K, validator globs updated).
- Appendix I: wire-level conformance suite SHOULD verify per-profile endpoint
  matching between two independently configured participants.

### Batch 2 follow-up (draft rev)

Decision resolutions from `spatialdds-1.7-batch2-followup.md`.

- §3.3.3 QoS table completed to the full normative surface: added **Durability**
  and **History** columns, populated for every profile row (no policy is
  specified only in prose). `RADAR_RT` deadline widened to admit 10–20 Hz radar
  (deadline is now normative; values must admit the profile's class):
  20 ms → 100 ms. `RADIO_SCAN_RT` deadline → "—" (scan cycles are seconds-scale;
  sporadic). `EVENT_RT` History is `KeepLast(64)` (existing events prose wins over
  the table default).
- §3.3.2 registry: added `tile_meta` (`core::TileMeta`), `rad_sensor_meta`
  (`sensing::rad::RadSensorMeta`), and `radio_sensor_meta` (provisional
  `sensing::radio::RadioSensorMeta`) — all QoS `SENSOR_META`. Registry gate
  coverage is now **fatal** (underscore/case-insensitive matching; Appendix E
  examples excluded).
- Topic-construction gate added as a CI job (advisory; requires the CycloneDDS
  IDL Python backend to run, otherwise skips).
- Informative fixes: `examples/agent_example.idl` `TaskType.MAP` → `MAPPING`
  (reserved word); `examples/` re-added to IDL validation scope. Appendix I S3E
  `ServiceKind.SLAM` → `MAPPING` (the enum is unchanged).

### Inventory-driven type additions (batch 3, draft rev)

Resolves `spatialdds-1.7-batch3-brief.md` — spec homes for two demo-owned type
families (`OpenArCloud/SpatialDDS-demo`), hardened to spec conventions. All
**Additive** (new structs; no existing declaration touched).

- `spatial.argeo`: added the VPS request/response pair — `VpsRequest`,
  `VpsResponse`, `QualityRequirements`, and enum `VpsStatus`. Query imagery
  travels by `BlobRef` (never inline bytes); request/response correlate by
  `query_id`; the response's pose rides in a `NodeGeo`.
- `spatial.semantics`: added `FusedTrack` / `FusedTrackSet` for cross-source
  fused tracks with per-source provenance (`source_operators`,
  `source_modalities`, `source_count`).
- §3.3.2 registry: `vps_query` now names `argeo::VpsRequest`; added
  `vps_response` (`argeo::VpsResponse`) and `fused_track`
  (`semantics::FusedTrackSet`, QoS `DET_RT`). Every existing registry row was
  annotated with its IDL type, and the registry gate now **fatally** requires
  every row to name a resolvable IDL type (a typeless row is a spec defect).
- §3.3 bootstrap: on-bus bootstrap exchanges noted as deployment-specific, not
  standardized. Future Directions: on-bus content catalog query parked as an
  open design question (deliberately not added in 1.7).

### Batch 3 follow-up (draft rev)

- `argeo::VpsRequest`: `quality_requirements` is now presence-guarded
  (`has_quality_requirements`); absence means the service's default accuracy
  requirements apply (§2.2 — no sentinel-zero requirements).
- §3.3.2 registry: dropped the `tile_meta` row — `core::TileMeta` is registered
  canonically as `geometry_tile`; `tile_meta` existed only within the 1.7 draft
  window. The registry gate now enforces one normative row per IDL type (alias
  rows excepted; `seg_mask` is marked an alias of `video_frame`'s
  `VisionFrame`).
- §3.3.2: agent-family rows (`agent_status`, `task_offer`, `task_assignment`)
  moved out of the normative registry into an "Informative Example
  Registrations" sub-table — they name types defined only in Appendix E
  examples and are outside the conformance surface; the gate checks only that
  they resolve.
- Added `gaps/2.0-considerations.md`: unify covariance representation
  (`CovMatrix` vs `Mat3x3`) — surveyed before 2.0, not patched in 1.7.

## Version 1.6 - 2026-07-23

### Core profile (spatial.core/1.6)
- Added `PlannedTrajectory` and `PlannedWaypoint` for cooperative planning and intent sharing (registered type `planned_trajectory`).
- Added `EntityBinding` and `ComponentRef` for cross-topic entity correlation (registered type `entity_binding`).

### Sensing common (spatial.sensing.common/1.6)
- Extended `CovarianceType` with `COV_ROT3` (orientation-only) and `COV_POSE6_TWIST6` (12×12 pose + velocity) cases.
- Added `Mat12x12` typedef and corresponding `CovMatrix` union cases.

### Discovery (spatial.discovery/1.6)
- Added `CoverageElement.has_coverage_window` / `coverage_window_start` / `coverage_window_end` for time-varying coverage.

### FrameRef axis convention (coord_convention patch)
- Added `CoordConvention` enum (`ENU`, `CV`, `GRAPHICS`, `UNITY_LH`, `NED`, `OTHER`) and extended `FrameRef` with optional `has_coord_convention` / `coord_convention` fields (APPENDABLE — backward compatible).
- New §2.12 Coordinate Axis Convention (Normative): convention table, default-ENU assumption when absent, chaining rule (no cross-convention chains without axis swap), producer guidance for CV / GRAPHICS / Unity / NED / ENU bridges, MetaKV escape hatch for `OTHER`.
- Motivated by the OpenVPS (CV) ↔ spARcl WebXR (GRAPHICS) ↔ GeoPose (ENU) integration debugging episode.
- Appendix I gains C-06 (nuScenes ego-ENU + camera-CV) and LC-06 (LaMAR hloc-CV + HoloLens-GRAPHICS + GT-ENU) coord-convention conformance checks; totals update to nuScenes 28, LaMAR 71, 5-dataset total 216.

### New normative conventions (§2)
- §2.7.6 Spatial Privacy (Normative Guidance) — pose quantization, trajectory truncation, pseudonymization, consent.
- §2.8 Enum Serialization — JSON identifier strings; CDR uses integer `@value`.
- §2.9 Time Semantics — UTC POSIX time; clock-source `MetaKV` keys.
- §2.10 Bounding Box Ordering — GeoJSON `[lon, lat, ...]` for geographic, `Aabb3 {min_xyz, max_xyz}` for local.
- §2.11 Schema Stability Signaling — `provisional` flag in `MetaKV` and `caps.features`.
- §3.3.1 Topic Version Stability — `/v1` follows profile MAJOR, not MINOR.

### Other normative changes
- §2.7.5 DDS Security wording clarified to allow OAuth2/OIDC, SPIFFE/SPIRE, mutual TLS via `auth_hint`.
- §7.5.6 Authority Expiry / Resolution Failure — cache → content-addressed → graceful-degradation fallback chain.
- `CoverageQuery.expr` deprecation now scheduled for **removal in 2.0**; new implementations MUST use `filter` exclusively.
- `NavSatStatus` registered as type `navsat_status` in §3.3.2; producers SHOULD include a `TopicMeta` entry.

### Conformance — Appendix I.5 LaMAR expansion
- Replaced the 22-check radio-only LaMAR section with a 70-check multi-device version covering HoloLens 2 (vision + ToF depth + IR), iPhone/iPad (vision + LiDAR depth), NavVis scanner (multi-camera + lidar mesh), IMU, poses & trajectories, multi-session Anchors alignment (7 checks: GeoAnchor, AnchorSet, scan-to-scan, sequence-to-scan, year-long stability, refinement lifecycle), Discovery in multi-device context (5 checks: heterogeneous announcements, coverage, manifests), Cross-Device Localization (5 checks).
- The original 22 radio checks (Radio Profile Coverage / Discovery + QoS / Interop + Privacy) are retained verbatim with prefix renames (`LD-*` → `LRD-*`, `LP-*` → `LRP-*`) to avoid ID collisions with the new HoloLens-Depth and Phone-Vision sections.
- Reaffirmed that the original LM-1 gap (no first-class radio fingerprint type) is closed by the provisional `sensing.radio` profile in Appendix E.
- Surfaced 6 deferred items (rolling-shutter timing model, per-frame gravity vector, visual-overlap score, CSI/CIR first-class transport, multi-band coexistence metadata, plus rolling-shutter readout direction) in the results scorecard.

### Strategic / informative changes
- Neural extension demoted to **Informative Example** (Appendix E); removed from Profile Matrix.
- Agent extension demoted to **Informative Example** (Appendix E); removed from Profile Matrix.
- Appendix H replaced with **"SpatialDDS as a Grounding Layer for World Models"** — H.1 Grounding Problem, H.2 Integration Patterns (MCAP/Gymnasium/inference bridges), H.3 What SpatialDDS Does Not Do, H.4 Factor Graphs and Scene Graphs.
- §4 Operational Scenarios reframed; long-form examples remain in Appendix D and Appendix I dataset walkthroughs.
- Appendix I gains a Scope and Limitations preface and a Deferred column on every results table.
- New **Appendix K: IDL Package Layout (Informative)**.
- §6 Future Directions adds wire-level interop testing, transport-agnostic semantic layer, factor-graph interchange, and "Bridges to External Ecosystems" (implemented: MCAP, ROS 2, MQTT, WebSocket; planned: Gymnasium). Appendix H.2 mirrors the bridge list with a corresponding IoT/edge MQTT integration pattern.

### Versioning model
- Selective per-profile minor bumps: only profiles whose IDL changed (`core`, `sensing.common`, `discovery`, `manifest`) move to `/1.6`. All others retain `/1.5`. Topic names remain `/v1` per §3.3.1.

## Version 1.5 - 2026-04-29

- Core and IDL: added `FramedPose`, redesigned `NodeGeo`, expanded pose-graph/mapping/event types, and clarified core patterns (covariance, ordering, optionality).
- Discovery/URIs/Manifests: structured CoverageQuery, defined pagination and topic/QoS conventions, added security + resolver rules, and formalized manifest schema and resolution.
- Extensions: major updates across sensing (vision/lidar/radar, including tensor + detection paths), plus new Mapping and Spatial Events extensions; provisional Neural/Agent/rf_beam expanded.
- Conformance and examples: added nuScenes + DeepSense harnesses, refreshed Appendix I, and updated examples/consistency across appendices.
- Documentation polish: new conceptual overview, improved profiles/footnotes/tables, and broad cleanup of formatting and consistency issues.
- Mapping extension updates: added RANGE constraints in `mapping::EdgeType`, RANGE_COARSE alignment method, and S3E conformance coverage in Appendix I.
- Appendix I framing: updated to a four-dataset conformance suite (nuScenes, DeepSense 6G, S3E, ScanNet), moved the reproducing section to follow I.4, and clarified the manual S3E/ScanNet analysis and updated limitations.
- Vision + conformance: added `PixFormat.DEPTH16` with normative depth semantics and introduced ScanNet indoor RGB-D conformance (Spatial Events, mesh, instance segmentation, depth).
- Discovery bootstrap: added geospatial DNS-SD binding with geohash subdomains, updated bootstrap flow diagram, and referenced DNS-SD/SRV RFCs.
- Discovery HTTP binding: restored `/.well-known/spatialdds/search` with CoverageQuery-equivalent semantics, GET geohash convenience, and updated discovery layering and Appendix B preamble.
- Mapping/Events IDLs: added `mapping.idl` and `events.idl` files and isolated mapping/events enums in submodules to avoid IDL literal collisions.

## Version 1.4 - 2026-02-07

- Finalized 1.4 draft text and examples; regenerated full spec.

## Version 1.3 - 2025-10-03

- Created isolated directories for 1.3 documentation, IDL files, and manifests to enable parallel iteration and cleanup legacy content.
- Documented SpatialDDS URIs for stable identification and manifest discovery, including ABNF definitions for parser interoperability.
- Added optional `coverage.frame` metadata, manifest `transforms[]`, and support for both local and global frames to improve mobility scenarios (issue #30).
- Added optional 3D coverage volumes in manifests plus matching Discovery hints/queries for active volumetric filtering (issue #29).
- Introduced a revamped active Discovery model that now supports HTTP in addition to DDS-based transport.

## Version 1.2 - 2025-09-14

- Added anchor manifest example.
- Refined schema: aligned geopose fields, renamed `id` to `anchor_id`, moved timestamps to `stamp`.
- Standardized bounding-box arrays for geometry data.

## Version 1.1 - 2025-07-01

- Initial concept release of the SpatialDDS specification.
