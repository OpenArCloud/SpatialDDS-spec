## **Appendix G: Frame Identifiers (Normative)**

SpatialDDS represents reference frames using the `FrameRef` structure:

```idl
struct FrameRef {
  uuid uuid;           // globally unique frame ID
  string fqn;          // optional fully-qualified name, e.g. "earth-fixed/map/cam_front"
};
```

### UUID Rules
- `uuid` is authoritative for identity.
- `fqn` is an optional human-readable alias.
- Implementations MUST treat `uuid` uniqueness as the identity key.

### Name and Hierarchy Rules
- `fqn` components are slash-delimited.
- Reserved roots include `earth-fixed`, `map`, `body`, `anchor`, `local`.
- A `FrameRef` DAG MUST be acyclic.

### Manifest References
Manifest entries that refer to frames MUST use a `FrameRef` object rather than raw strings. Each manifest MAY define local frame aliases resolvable by `fqn`.

### Notes
This appendix defines the authoritative encoding for `FrameRef`. Additional derived schemas (e.g. GeoPose, Anchors) SHALL refer to this definition by reference and MUST NOT re-declare frame semantics.
