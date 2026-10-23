# Stats row — derivation of record

The five numbers in the homepage proof band (`site_overlay/index.html`, the
`proof-numbers` block) are derived here. **Each number cites the run or count that
produced it.** This file and the stats row are one unit: a change to any headline
number MUST change this file in the same commit. A stats-row edit that arrives
without a matching derivation edit should look wrong in review — that is the
intended tripwire, not an oversight.

Derived 2026-10-22, at the 1.8 stamp candidate.

---

## 14 — IDL profiles

Count of top-level IDL module files in the pinned tree:

```
$ ls idl/v1.8/*.idl | wc -l
14
```
→ anchors, argeo, common, core, discovery, events, lidar, mapping, rad,
semantics, slam_frontend, types, vio, vision.

Three provisional modules (`idl/v1.8/provisional/`: owm, radio, rf_beam) are
versioned independently (Appendix E) and are **not** counted in the headline;
they are the provisional surface, not the 1.x-stable profile set.

## 220 — conformance checks

Sum of the per-dataset check totals in Appendix I (each the section's own
"Checks Performed (N)" heading, equal to its Results-table **Total** row):

| Dataset   | Checks | Source (Appendix I) |
|-----------|-------:|---------------------|
| nuScenes  |     28 | §I.1 (27 reproduced by the harness; C-06 manual-only) |
| DeepSense 6G | 48  | §I.2 |
| S3E       |     38 | §I.3 |
| ScanNet   |     35 | §I.4 |
| LaMAR     |     71 | §I.5 (69 pass, 2 gaps; 22-check radio subset) |
| **Total** | **220**| |

**Changed from 216 → 220 this stamp.** The old 216 summed LaMAR at 67
(28+48+38+35+67). The Appendix I audit reconciled LaMAR to 71 against the harness
and benchmark as the authority (69 pass + the two named shutter-type gaps, with
the radio checks scoped as a 22-check subset), so the true total is
28+48+38+35+71 = 220. The number moved because the LaMAR count moved; nothing
else in the sum changed.

Not summed into this headline (different subject, recorded here so the reader
sees them and the scope of the headline is explicit):

- **Web-binding conformance suite — 15 checks, 15/15 pass.** Run 2026-10-22
  against the published `spatialdds==0.5.4` package serving `--demo`, suite from
  this repo (`web-binding/conformance/run.py`), advertise-`demo.spatialdds.org` +
  `--connect` loopback: `15 checks: 15 passed, 0 failed, 0 skipped`, §8.2 anchor
  resolve PASS. This certifies an *endpoint* speaks the binding, not a dataset's
  expressiveness, so it is a separate surface from the dataset headline.
- **Spec build gates — 6.** spec-consistency, registry (37 rows), registry-topic
  cross-check, topic-construct (112 types), gen (112 schemas), roundtrip (9 golden
  vectors). These gate the spec's own internal consistency, not dataset coverage.

## 5 — public datasets validated

The five datasets with a validation record in Appendix I: **nuScenes** (§I.1),
**DeepSense 6G** (§I.2), **S3E** (§I.3), **ScanNet** (§I.4), **LaMAR** (§I.5).
Each section opens with a fixed-format validation record (version validated
against, date, method, verbatim totals).

## 4 — protocol bridges

The bridges in the demo repo's Bridges table
(`SpatialDDS-demo/README.md`, "## Bridges"):

| Bridge | What it does |
|--------|--------------|
| Web (HTTP/WebSocket) | the browser's way onto the bus, embedding the web binding |
| MCAP record / replay | recordings whose schemas come from the IDL |
| ROS 2 | ROS 2 sensor messages in, decoded spec samples out |
| MQTT | JSON at the broker, typed samples on the bus |

→ 4.

## 2 — live reference demos

Enumerated — the live reference deployments on the bus:

1. **The venue reference demo** (`SpatialDDS-demo`) — the venue as a live model
   (robots, ducks, declared water, a browser, all on one bus); shown at ISMAR 2026.
2. **OpenVPS** (`openvps`, `spatialdds` branch) — an open visual positioning
   service that announces its coverage and answers localization queries on the
   same bus.

The **SceneScape sidecar** (`spatialdds-scenescape`) is a *perception adapter* —
it publishes a stock SceneScape deployment's analytics as typed samples — not a
standalone demo, so it is not counted here (it appears in the proof band as the
third reference deployment but under the "adapter" kicker, not "demo").
