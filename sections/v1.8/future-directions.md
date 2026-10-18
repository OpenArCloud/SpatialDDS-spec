## **6. Future Directions**

While SpatialDDS establishes a practical baseline for real-time spatial computing, several areas invite further exploration:

* **Reference Implementations**  
  Open-source libraries and bridges to existing ecosystems (e.g., ROS 2, OpenXR, OGC APIs) would make it easier for developers to adopt SpatialDDS in robotics, AR, and twin platforms.  
* **Semantic Enrichment**  
  Extending beyond 2D/3D detections and spatial events, future work could align with ontologies, scene graphs, and complex event processing patterns to enable richer machine-readable semantics for AI world models and analytics.  
* **Neural Integration**  
  Provisional support for neural fields (NeRFs, Gaussian splats) could mature into a stable profile, ensuring consistent ways to stream and query neural representations across devices and services.  
* **Agent Interoperability**  
  The Agent extension's fleet coordination types (AgentStatus, TaskOffer, TaskAssignment, TaskHandoff) provide the typed data layer for multi-agent allocation. Future work could formalize common allocation patterns (auction-based, priority-queue, spatial-nearest) as reference implementations while keeping the protocol algorithm-agnostic.  
* **Collaborative Mapping**  
  The Mapping extension enables multi-agent map discovery, alignment, and lifecycle coordination. Future work could formalize map merge protocols, distributed optimization coordination, and standardized map quality benchmarks for fleet-scale deployments.  
* **Standards Alignment**  
  Ongoing coordination with OGC, Khronos, W3C, and GSMA initiatives will help ensure SpatialDDS complements existing geospatial, XR, and telecom standards rather than duplicating them.
* **On-bus content catalog query**  
  `ContentAnnounce` plus manifests and HTTP search cover content discovery today. Whether an on-bus, area-scoped catalog query/response joins them is an open design question; evidence from federation prototypes will inform it. Deliberately not added in 1.7.
* **Open World Model (`spatial.owm`)**  
  The provisional `spatial.owm/0.1` module (Appendix E) adds an identity-and-lifecycle layer over the discovery catalogue — entities with pose, type, and state that point back at catalogue content. It is independently versioned and exempt from the 1.x additive guarantee precisely so its shape can change while implementers exercise it. It leaves provisional status on two conditions, stated in its preamble: a second independent implementation, and relationship/identity semantics (per-edge basis, confidence, and retraction) landing as a resolved design rather than the reserved gap 0.1 deliberately leaves open.

### Queryable Coverage Response

Discovery today answers *who is here* through `Announce` and the Coverage Model, and `CoverageQuery` lets a consumer ask which providers cover a region. What a working federation prototype adds on top is a direct, area-scoped **coverage answer**: a responder returns per-provider coverage summaries for the queried region, merged with its local announce cache so that providers known only from their earlier announces — not merely those answering the query live — stay discoverable in the same response. A future coverage-response type must meet that requirement: from a single area-scoped query a consumer MUST be able to learn the coverage of every provider the responder knows about, queried and cached alike, with announce-only providers never silently dropped. This is recorded as a problem statement from that prototype; the on-bus message shape is deliberately deferred to a later batch and is explicitly not added as IDL in 1.8.

### Content Withdrawal (Typed Dispose)

Discovery can say a **service** has departed: `Depart` is `{service_id, stamp}`,
the right record for exactly one of the two publishable kinds. Nothing says a
**content** record has been withdrawn. `ContentAnnounce` carries no lifecycle
member, so the §2.14 terminal-sample-then-dispose convention has no typed
message to hang on for content, and a dispose cannot be journalled as a typed
message the way a publish can. A publishing endpoint in the SpatialDDS-web
prototype, needing to record a withdrawal with nothing typed to carry it,
resorts to an out-of-band MCAP metadata record it names `spatialdds-web:dispose`
— a convention of that one endpoint, not of the binding — which is evidence that
implementers are already forced to invent something here. A future revision
could add a withdrawal record that covers content as `Depart` covers services,
or a lifecycle member on the content record itself; the message shape is
deliberately deferred and is explicitly not added as IDL in 1.8. (Recorded from
the SpatialDDS-web publish work; the service-side reading gap it travelled with
— addressing the four-segment `spatialdds/discovery/depart/v1` well-known topic
over the web binding — is already resolved by N.3's short-topic rule and is not
part of this item.)

The evidence has since grown to show what the 1.9 record must be. Three
*independent* removal mechanisms now ship across two repositories for this one
absent type — a recording loader that infers removal from a `RETIRED` terminal
tombstone; a journal that reads its own `spatialdds-web:dispose` metadata
records; and a web bridge that emits an `oarc.model_entity_disposed` WebSocket
message — each locally correct, mutually unintelligible, and blind to the
others. A tombstone-less removal of a non-publishable type is learnable by
*none* of them. Two forces decide the shape of the fix. First, blessing any one
convention makes the other two retroactively wrong, where **a typed removal
record makes all three unnecessary** — so the answer is a type, not an official
favourite. Second, the record MUST carry **intent and reason**, because the
transport cannot: DDS autodispose means a dispose on the wire is
indistinguishable between a deliberate removal and a writer merely exiting, so
no convention over raw disposes can ever recover what was meant. The 1.9
direction is therefore a typed removal record carrying intent and reason, not a
blessed convention. (Evidence: the SpatialDDS-demo OWM migration, `removal-two-doors-finding.md`.)

### Anchor Integrity Digest (`GeoAnchor.checksum`)

`GeoAnchor.checksum` is REQUIRED on the wire and its comment reads
`integrity/versioning`, but 1.8 defines **what it digests or in what form**
nowhere — not the IDL, not Appendix C, not the conformance suite. So no receiver
can verify it and no two publishers agree: a digest over the canonical JSON or
the XCDR2 bytes, including the checksum member or excluding it, before or after
the revision's appended members, are all equally "the checksum of the anchor
data". Two conventions already exist in deployed code — SpatialDDS-web's
authoring tool digests its input entry (recorded anchors), its record builders
digest the record's own canonical form with `checksum` emptied (published
anchors) — both correct, mutually incompatible, which is the evidence that the
field as specified cannot interoperate. The §7.5.2 erratum (this revision) stops
an undefined `checksum` from counting as an integrity signal until a digest is
defined.

A future revision should define the digest. The **proposed semantics**: the
`sha256:` digest of the **canonical N.1 JSON form of the record with the
`checksum` member itself omitted** — the record-builder convention above. It is
recomputable by any receiver from exactly what was served, and it is the only
non-self-referential, APPENDABLE-stable choice: a digest over XCDR2 bytes shifts
when the type appends a member, and one that includes `checksum` cannot be
checked without already knowing it. This is not landed in 1.8 — assigning the
field a meaning it never had would retroactively make every record computed
under any other convention nonconformant, which is a feature decision, not an
erratum.

### OWM `ModelPose` Frame Reference

`spatial.owm/0.1`'s `ModelPose` (`@key entity_id`, `pose`, `source_id`, `stamp`)
carries no frame. On DDS the frame is learned by joining a pose to the latched
`Entity` of the same `entity_id`, which carries `frame_ref`; the join is free
because the middleware hands a pose subscriber the latched entity set whether it
asked or not, which is why the fast lane was allowed to be lean. Under Appendix N
the two lanes become independent HTTP resources with independent URLs and access
classes — a client may subscribe to the pose lane and never fetch the entity
lane, receiving a stream of positions in an unnamed frame with no error
anywhere. The DDS shape made the join free, so the type never had to state the
dependency; the web shape makes the join a request a client can skip, and the
dependency is now stated nowhere a machine can read.

Recommended fix (the OWM module is provisional, which is the window for this): a
normative statement that a `ModelPose` consumer MUST resolve `frame_ref` through
the `Entity` of the same key, and that a binding serving the pose lane MUST make
the entity lane reachable — so the entity lane's access class cannot be stricter
than the pose lane's. This looks right over a `frame_ref` member on `ModelPose`,
which would cost bytes on the busiest lane and add a second place for the frame
to be wrong: the dependency is real and it is the *statement* of it that is
missing, not the data. A member remains the 1.9 fallback if the statement proves
insufficient. Held for a ruling (it adds a normative MUST). Origin:
SpatialDDS-demo OWM migration, `owm-1.8-spec-queue.md` item 1.

### OWM `ModelCommand.subject_id` Kind Encoding

`ModelCommand.subject_id` is one `string` whose prefix (`"ent:"`) carries the
subject's *kind*, with the grammar living in a module comment. A kind is a
contract; an id is author-supplied data. A publisher that mints
`entity:duck:east` instead of `ent:duck:east` produces a well-formed
`ModelCommand` that validates against its schema, names a real subject, and
carries a defined verb — and is silently ignored by every consumer that branches
on the prefix, with nothing for a conformance check to catch because nothing is
violated. It reads as working until two implementations prefix differently.

1.9 material. When a second subject kind lands (relationships), the fix is an
explicit discriminator — an enum `subject_kind`, or a keyed union — rather than a
widened prefix vocabulary. Until then the asking price is one sentence of
normative text: either the prefix grammar is normative and conformance can check
it, or the field is opaque and consumers MUST NOT branch on its shape. Right now
it is a convention doing a type's job. Origin: SpatialDDS-demo OWM migration,
`owm-1.8-spec-queue.md` item 2.

### Making the Binding Usable from a Browser (1.9)

Two halves of one claim — *a browser can actually use the binding* — kept in one
entry because splitting them loses the second, which already read as a footnote
once. Both are **ruled 1.9** (not errata): the normative text lands in 1.9, and
nothing changes in 1.8. From the SpatialDDS-demo web bridge's browser lane
(`browser-credential-finding.md`); the gateway-side CORS *fix* is the reference
implementation's and is queued in SpatialDDS-web.

**Credential carriage for the WebSocket handshake (blocker A).** N.4 requires the
bearer in the `Authorization` header for both the GET and the WebSocket handshake
and forbids a URL query parameter (which writes the credential into proxy logs
and `Referer` headers). The reasoning is sound, but the browser WebSocket API can
set no request header — a platform constraint — so an operator-scoped N.5
subscription is reachable by every client except the browser, the client Appendix
N most obviously exists for (measured: a header GET 200, a header WebSocket
connects, a subprotocol-only WebSocket 401). Not an erratum — N.4 is not
self-contradictory, it is browser-hostile. The likely answer is **subprotocol
carriage**: blessing `Sec-WebSocket-Protocol: bearer.<token>`, the one credential
channel the WebSocket API exposes — a header that appears in no URL, proxy log,
or `Referer`, so it breaches neither N.4's letter nor its reasoning. A
**single-use ticket** (GET a short-lived ticket, present it in the subscription
URL) is named and argued against: it puts a secret-shaped string in a URL for
exactly the duration the rule exists to prevent. Reclassifying an over-gated lane
to `public-cacheable` helps only where the data is genuinely public (N.4's
guidance: configured geometry is ordinarily public, observations of people are
not) and cannot help a lane that must stay gated.

**A browser-facing endpoint must state its preflight behavior.** Even with a
credential the browser can carry, a conforming gateway can omit every part of the
CORS/preflight behavior a browser needs and still pass every check — making
browser reachability implementation luck. An `Authorization` header is not
CORS-safelisted, so a cross-origin `fetch` carrying one preflights with `OPTIONS`;
a gateway that routes no `OPTIONS` refuses the preflight (405) before the request,
and a response carrying no `Access-Control-Allow-Origin` is unreadable even when
authorized. Measured from a page on another origin: N.6 commands are unreachable
for *every* access class (a command always carries a credential, so it always
preflights), and a `public-cacheable` GET fails outright if the client volunteers
a credential it does not need. The lesson is not "permit this" (nothing forbids
it) but **require it to be stated**, most naturally as an implementation-
requirements note: a browser-facing endpoint answers `OPTIONS` for every resource
and allows `Authorization`/`Content-Type` where accepted; carries
`Access-Control-Allow-Origin` on an authorized response, echoing the requesting
`Origin` with `Vary: Origin` when the response is not cacheable (else a credential
N.4 requires buys a response the client cannot read); and a client SHOULD NOT send
a credential to a resource whose access class does not require one. It is a gap,
not a contradiction, and the substance is new conformance requirements — a
tightening — so 1.9, not an erratum.

The 1.9 work lands both together: N.4's subprotocol-carriage sentence and the
implementation-requirements preflight note. Origin: SpatialDDS-demo
`browser-credential-finding.md` (blocker A and the third routing; blocker B, the
gateway's CORS fix, is SpatialDDS-web's).

### Short-Topic Lanes: Which Deserve a Resource

§3.3.2 registers four-segment topic names — `spatialdds/<stream>/<type>/<version>`
with no `<domain>` (the discovery announce/depart lanes, and the VPS and blob
lanes). N.3 maps such a sub-five-segment topic into the well-known namespace and,
as of the short-topic erratum, specifies that the resource served there behaves
as the §N.3 latched collection rooted at the well-known path — `GET`/`ETag`/`304`,
instance keys, access class, and the N.5 stream. That settles *where* a short
topic maps and *how* its resource behaves.

What remains open is *which* short topics are latched state a GET resource suits.
The announce lane is latched, keyed, and public. A VPS request/reply lane
(`vps_query` → `vps_response`) and a blob lane (`blob/chunk`) are not latched
state and do not fit the latched-collection model: a request/reply localization
lane belongs to the **1.9 GeoPose-Protocol-successor service profile** — a
localization service *over* the binding, with a single-shot `POST` and a
continuous-session WebSocket — not to the latched resource model in it. A
pointer, not a new design. (The backend-blind suite is already segment-count
agnostic: it follows the advertised `url` and never splits a topic name, so a
short topic served at its well-known path is exercised exactly as a
domain-scoped one — guarded by `web-binding/conformance/four_segment_probe.py`.)
Origin: the OpenVPS 1.8 migration, `openvps-18-spec-queue.md` item 2.

### Wire-Level Interop Testing

Appendix I validates schema expressiveness through static conformance checks. Future revisions will add wire-level interoperability tests across at least two DDS implementations (CycloneDDS and Fast DDS minimum) to validate end-to-end publish/subscribe fidelity, QoS enforcement, and CDR encoding compatibility.

### Transport-Agnostic Semantic Layer

The spatial semantics defined by SpatialDDS — `FrameRef`-by-UUID, the Coverage Model, manifests, the URI scheme, and the dataset conformance methodology — are conceptually separable from the DDS transport binding. Future work will explore canonical bindings to additional transports (gRPC, MCAP files, Arrow Flight) while preserving the semantic layer unchanged. This would position SpatialDDS as an open semantic standard for spatial data, with DDS as the primary real-time binding and additional bindings for offline recording, cloud integration, and ML pipeline ingestion.

### Factor Graph Interchange

SpatialDDS's pose-graph types (`Node`, `Edge`, `MapMeta`) carry SLAM factor graph results. A dedicated factor graph interchange format — analogous to ONNX for neural networks — would enable portable exchange of arbitrary factor graph structures between solvers. SpatialDDS would reference such graphs via `BlobRef`, with `MapMeta` carrying optimization state metadata. This is a complementary effort, not a SpatialDDS extension.

### Bridges to External Ecosystems

Priority bridges for connecting SpatialDDS to robotics, IoT, ML, and visualization ecosystems. These are implementation artifacts maintained in the SpatialDDS-demo repository, not spec extensions.

Implemented:

- SpatialDDS ↔ MCAP recorder/replayer (offline recording, Foxglove visualization, ML pipeline ingestion).
- SpatialDDS ↔ ROS 2 bridge (`sensor_msgs`, `geometry_msgs`, `vision_msgs` translation with tf2 frame mapping).
- SpatialDDS ↔ MQTT bridge (edge-to-cloud via Mosquitto or AWS IoT Core, with QoS mapping and per-operator topic policies).
- SpatialDDS ↔ WebSocket bridge (browser dashboards, digital twin UIs, topic discovery, client-side subscriptions).

Planned:

- SpatialDDS ↔ Gymnasium observation space adapter (RL agent training on live spatial streams).

Together, these directions point toward a future where SpatialDDS is not just a protocol but a foundation for an open, interoperable ecosystem of real-time world models.

We invite implementers, researchers, and standards bodies to explore SpatialDDS, contribute extensions, and help shape it into a shared backbone for real-time spatial computing and AI world models.
