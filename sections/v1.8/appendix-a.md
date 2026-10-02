## **Appendix A: Core Profile**

*The Core profile defines the fundamental data structures for SpatialDDS. It includes pose graphs, 3D geometry tiles, anchors, transforms, and generic blob transport. This is the minimal interoperable baseline for exchanging world models across devices and services.*

### **Common Type Aliases (Normative)**

```idl
{{include:idl/v1.8/types.idl}}
```

> **Typed-first extension rule (Normative).** Producers SHOULD carry scalar and string-valued extensions in `MetaKV.entries` (typed key/value rows) and reserve `MetaKV.json` for genuinely free-form payloads. Consumers MUST accept either. Keys SHOULD be namespaced (`org.key`). This keeps extension data on the typed wire and inspectable without JSON parsing. **Uncertainty is never free-form:** covariance — including the observer covariance added in 1.8 (`Detection3D.observer_cov`, `FusedTrack.observer_cov`) — MUST be carried in the typed `CovMatrix` / matrix fields the profiles define, never relegated to `MetaKV` or `json`.

### **Core Module**

```idl
{{include:idl/v1.8/core.idl}}
```
