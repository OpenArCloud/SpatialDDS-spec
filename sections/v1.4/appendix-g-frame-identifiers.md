## **Appendix G: Frame Identifiers (Informative Reference)**

SpatialDDS represents reference frames using the `FrameRef` structure:

The normative IDL for `FrameRef` resides in Appendix A (Core profile). This appendix is descriptive/informative and restates the usage guidance for reference frames.

```idl
struct FrameRef {
  string uuid;   // globally unique frame ID
  string fqn;    // normalized fully-qualified name, e.g. "earth-fixed/map/cam_front"
};
```

### UUID Rules
- `uuid` is authoritative for identity.
- `fqn` is an optional human-readable alias.
- Implementations MUST treat `uuid` uniqueness as the identity key.
- Deployments SHOULD establish well-known UUIDs for standard roots (e.g., `earth-fixed`, `map`, `body`) and document them for participants.

### Name and Hierarchy Rules
- `fqn` components are slash-delimited.
- Reserved roots include `earth-fixed`, `map`, `body`, `anchor`, `local`.
- A `FrameRef` DAG MUST be acyclic.

### Manifest References
Manifest entries that refer to frames MUST use a `FrameRef` object rather than raw strings. Each manifest MAY define local frame aliases resolvable by `fqn`.

### Notes
Derived schemas (e.g. GeoPose, Anchors) SHALL refer to the Appendix A definition by reference and MUST NOT re-declare frame semantics. The conventions in §2.1 and the coverage/discovery rules in §3.3 reference this appendix for their frame requirements.
