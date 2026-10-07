# SpatialDDS Specification

SpatialDDS is an open protocol for real-world spatial computing: a shared, typed bus for spatial data, world models, and digital twins across devices and operators. It builds on standard DDS concepts and carries uncertainty, frames, and attribution as first-class citizens. Browse the live specification at [spatialdds.org](https://spatialdds.org).

The current version is **1.8 (Draft)**. It is validated the way prior releases were and then some: conformance gates run in CI, the type system has been exercised by a working adapter that translated more than 50,000 messages from an unmodified production vision system into typed 1.8 samples, and recordings decode in third-party readers from the embedded schemas alone. As a draft under the pre-adoption policy (§3.1), the 1.x series may still change before formal adoption, and amendments remain welcome as review lands. The most recent stamped release is 1.7; earlier versions back to 1.2 are kept in the tree. See the [CHANGELOG](CHANGELOG.md) for history.

## Repository structure

- `sections/v*/` – the specification sections, appendices, glossary, and references for each version.
- `idl/v*/` – the canonical IDL for each version: core, discovery, anchors, events, semantics, sensing, and the provisional modules.
- `manifests/v*/` – example JSON manifests for services, anchors, and content.
- `web-binding/` – the web binding toolchain: the canonical JSON mapping contract, the generator that derives JSON Schemas from the IDL, golden vectors, and the conformance definition.
- `SpatialDDS-<version>.md` / `SpatialDDS-<version>-full.md` – per-version entry points and the combined documents built from the sections.
- `scripts/` – build helpers, including `build-spec.sh`.

## Building and browsing

IDL and manifest files are canonical; markdown sections reference them with `{{include:...}}` placeholders. Rebuild the combined specification after changing any of them:

```bash
./scripts/build-spec.sh 1.8
```

For local browsing with navigation and search, the repository carries an MkDocs setup: install MkDocs with the listed extensions, run `./scripts/prepare_mkdocs.py`, then `mkdocs serve`. Pushes to `main` rebuild and publish the site automatically.

## Implementations

[spatialdds-scenescape](https://github.com/OpenArCloud/spatialdds-scenescape) is the first adapter for a third-party production system: it publishes an unmodified Intel SceneScape deployment's scene analytics as typed SpatialDDS 1.8 samples, was exercised against more than 50,000 real messages from a running deployment, and ships recordings that decode without any of its own code.

The companion [SpatialDDS demo](https://github.com/OpenArCloud/SpatialDDS-demo) is the running reference deployment: live publishers, the Open World Model surface, and bridges you can stand up yourself.

## Contributing

Issues and pull requests are welcome. Open an issue to discuss large changes. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

Licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/). See [LICENSE](LICENSE).
