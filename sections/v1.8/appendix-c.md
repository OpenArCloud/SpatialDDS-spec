## **Appendix C: Anchor Registry Profile**

*The Anchors profile defines durable GeoAnchors and the Anchor Registry. Anchors act as persistent world-locked reference points, while the registry makes them discoverable and maintainable across sessions, devices, and services.*

```idl
{{include:idl/v1.8/anchors.idl}}
```

**Anchor content references (Normative).** A `GeoAnchor` MAY carry a
`manifest_uri` (added in the 1.8 revision) naming a content manifest, resolvable
per §7.5. The reference binds that content to the anchor's frame and precision:
content reached through it is positioned by the anchor's `geopose` in its
`frame_ref`, and the anchor's `method` and `cov` are the claim level the binding
inherits — content is no better localized than the anchor that places it. An
empty `manifest_uri` means the anchor references no content, and such an anchor
is unchanged in meaning and on the wire from a pre-revision one.
