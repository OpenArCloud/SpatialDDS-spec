## **Appendix L: Resolution Quality Conformance (Normative)**

§6 Future Directions calls for wire-level interop testing. The gap is broader than wire format: a `VpsResponse` may claim `status = VPS_SUCCESS` with `rmse_m = 1.0`, or an anchor may advertise `confidence = 0.95`, and nothing else in this specification tests whether those claims are true. For an open commons where participants trust one another's anchors and fixes, an unverified quality claim is worse than no claim — it composes into confidently-wrong alignment. Interoperability requires not just that messages parse, but that *quality assertions mean what they say*.

This appendix defines conformance tests that any anchor-publishing or VPS-providing implementation MAY be certified against. It is deliberately **not** a test of localization accuracy in the abstract — that depends on scene, sensors, and method, all out of scope and rightly mechanism-agnostic. It is a test of **claim calibration**: does a fix that asserts a quality bar actually satisfy it, at the stated rate? Every test is mechanism-agnostic and consumes only this specification's own quality fields (`confidence`, `rmse_m`, `VpsStatus`, `CovMatrix`). An hloc-based, a bearing-based, a GNSS-only, and a neural resolver all take the same tests and pass or fail on calibration alone, never on method. The word "VPS" in existing type names is retained for continuity; the tests apply to any resolver of the AR+Geo request/response and to any anchor publisher.

Each test is defined over a **labelled evaluation set**: fixes or anchors accompanied by independent ground-truth poses.

### **L.1 Covariance calibration**

Over the evaluation set, the actual error distribution MUST be consistent with the reported `CovMatrix` at a stated significance level: the normalized estimation error squared (NEES) MUST fall within the χ² bounds for the covariance's degrees of freedom at the p-level the implementation claims.

*Plain statement:* if you report ±1 m at 1 σ, about 68 % of your fixes MUST actually land within 1 σ, and the ellipse shape MUST match the error shape. An implementation that reports round (isotropic) covariance on directional error fails this test even if its scalar magnitude is right.

### **L.2 Status honesty**

For requests carrying `QualityRequirements`:

- `VPS_SUCCESS` MUST NOT be returned when measured error exceeds `max_rmse_m` more often than the claimed confidence permits.
- `VPS_DEGRADED` MUST be returned, not `VPS_SUCCESS`, when a fix is produced but falls below the requested bar.
- `VPS_FAILED` MUST be returned, rather than a fabricated in-tolerance fix, when the resolver cannot meet the bar.

*A resolver that never returns `VPS_DEGRADED` or `VPS_FAILED` on hard inputs fails this test. Refusal is a conformance requirement, not an implementation choice.*

### **L.3 Prior-replay non-regression**

When a `VpsRequest` supplies `has_prior_geopose`, the returned fix's error MUST NOT be statistically worse than the supplied prior's error on the evaluation set.

*An anchor resolver that degrades a good GNSS-plus-heading prior is worse than useless; this test forbids advertising a fix that adds nothing while claiming improvement. A resolver MAY return the prior unchanged — reporting so via covariance and confidence — but it MUST NOT move the pose away from truth and claim success.*

### **L.4 Cross-session / cross-device stability**

An anchor advertised as durable MUST resolve, across independent sessions and — where applicable — devices, to poses mutually consistent within the union of their reported covariances.

*A "durable" anchor that lands in different places on different visits, beyond its own stated uncertainty, is mislabelled.*

### **L.5 Reporting**

A conformance run MUST publish, per test, the evaluation-set size, the measured rate versus the claimed rate, and a pass/fail result. An implementation that has passed a profile cites it in `caps.features` (and, for durable providers, its service manifest) so that consumers can filter by *verified* quality, not merely advertised quality. A citation naming a profile the implementation has not passed is itself a conformance violation.

> **Editor's note (open question — comment invited).** Governance of the evaluation set — who curates it, how ground truth is established and audited, how a set is versioned, and how a passing result is attested and revoked — is unresolved and intentionally left outside the normative text above. The tests specify *what* must hold over *a* labelled evaluation set; they do not yet specify *whose* set or *how certified*. Reviewers are invited to comment on whether this specification should define that governance, defer to an external conformance authority, or standardize only a reporting format and leave curation to deployments.

### Why this belongs in the standard

This appendix converts SpatialDDS's honest-quality fields from *hope* into *contract*. The fields already exist; these tests give them teeth, so that "open" also means "verifiably honest" — the differentiator an open commons has over a closed VPS that markets unfalsifiable precision. It pairs naturally with the §6 Wire-Level Interop Testing item as its quality-layer counterpart.

### 3GPP ISAC KPI bridge (Informative)

For readers coming from 3GPP integrated-sensing work, the tests above restate, in SpatialDDS's own vocabulary, quantities the ISAC sensing KPIs (TS 22.137 service requirements; TR 38.765 scope) already name. This is a terminology bridge only; it changes no conformance requirement and introduces no KPI target — SpatialDDS tests *claim calibration*, not an absolute accuracy figure.

| 3GPP ISAC KPI | SpatialDDS conformance analogue |
|---|---|
| Positioning / sensing **accuracy** KPI (e.g. position error at a stated percentile) | L.1 covariance calibration — the reported `CovMatrix` must be consistent with the observed error distribution (NEES within χ² bounds), i.e. the stated accuracy must be the *true* accuracy, not an advertised one. |
| **Detection probability** (P_d) | L.2 status honesty — `VPS_SUCCESS` returned no more often than the claimed confidence actually holds; a fix below the requested bar must downgrade to `VPS_DEGRADED`. |
| **False-alarm rate** (P_fa) | L.2 status honesty, read the other way — a resolver that returns a fabricated in-tolerance fix rather than `VPS_FAILED` on an unresolvable input is manufacturing false alarms; refusal is the conformance requirement. |
| **Sensing latency / refresh** KPIs | Out of scope here — carried by QoS and the per-type timing fields, not by this appendix. |

The mapping is deliberately loose: a 3GPP KPI is a numeric target a deployment sets, whereas an L-test asks only that whatever a producer claims is kept. A producer can cite both — the KPI it targets and the L-profile it has passed — and a consumer filters on the latter for *verified* quality.
