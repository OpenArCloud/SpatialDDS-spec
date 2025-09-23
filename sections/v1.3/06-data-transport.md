## **6. Data Transport (Normative)**

SpatialDDS separates logical schemas from transport bindings. Implementations SHALL observe the transport requirements in this
section when exchanging data referenced by discovery manifests.

### **6.1 Baseline transports**

* **DDS/RTPS.** All Core profile data SHALL be available via DDS using the Real-Time Publish-Subscribe (RTPS) protocol. Vendors
  MAY use proprietary DDS implementations provided they interoperate on the wire.
* **HTTP/2 or HTTP/3.** Manifests, large geometry blobs, and asset downloads SHALL be retrievable over HTTPS. Providers SHOULD
  offer HTTP/3/QUIC where available to reduce latency and improve congestion control.
* **gRPC/Web services.** Service manifests MAY expose RPC interfaces. When doing so they SHALL specify the protocol (`grpc`,
  `https`, `webrtc`) and version in the manifest `transports` array.

### **6.2 Optional transports**

The following transports MAY be offered in addition to the baseline:

* **DDS over QUIC or TCP.** Providers MAY expose DDS participants over QUIC or TCP tunnels for constrained networks. Such
  transports SHALL be documented in the manifest `transports` array with connection parameters.
* **WebRTC data channels.** Real-time client applications MAY negotiate WebRTC for low-latency streams. WebRTC endpoints SHALL be
  described with ICE server configuration and STUN/TURN requirements.
* **Content-addressed networks (e.g., IPFS).** Large static assets MAY be replicated via content-addressed URIs advertised in the
  manifest.

### **6.3 QoS classes**

SpatialDDS defines QoS recommendations per topic class. Providers SHALL document the QoS policy in manifests and configure DDS
publishers/subscribers accordingly.

| Topic class | Reliability | Durability | Liveliness | Deadline | Notes |
| --- | --- | --- | --- | --- | --- |
| Pose updates (`pg.node`, `geo.fix`) | Best-effort, KEEP_LAST(5) | VOLATILE | AUTOMATIC | ≤ 33 ms | Prioritize latency. |
| Anchor updates (`anchors.delta`) | RELIABLE, KEEP_ALL | TRANSIENT_LOCAL | AUTOMATIC | 1 s | Ensure eventual consistency. |
| Geometry tiles (`geom.tile.*`) | RELIABLE, KEEP_LAST(1) | TRANSIENT_LOCAL | AUTOMATIC | Provider-defined | Tiles may be large; use flow control. |
| Semantics detections (`semantics.det.*`) | RELIABLE, KEEP_LAST(10) | VOLATILE | AUTOMATIC | 100 ms | Maintain recent context. |
| Discovery topics | RELIABLE, KEEP_LAST(1) | VOLATILE | MANUAL_BY_PARTICIPANT | 5 s | Match announce repetition interval. |

Implementations MAY deviate from these defaults when justified by environment constraints but SHALL document deviations in the
manifest `capabilities` or `transports` metadata.

### **6.4 Error handling and health**

* Publishers SHALL set the `ttl_ms` field on discovery messages and SHALL refresh announcements before expiry.
* Subscribers SHALL monitor liveliness. Missing heartbeats for more than 3× the advertised deadline SHOULD trigger reconnection
  or service reselection.
* Providers SHOULD expose health endpoints (HTTP `GET /healthz`) or DDS heartbeat topics so that clients can detect partial
  failures.
* TTL and heartbeat policies SHALL be documented in manifests so that clients can adapt reconnection behavior.
