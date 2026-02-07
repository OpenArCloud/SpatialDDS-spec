# SpatialDDS Specification (Concept)

SpatialDDS is a concept protocol for real-world spatial computing that defines a shared bus for spatial data, AI world models, and digital twins. You can browse the live specification at [spatialdds.org](https://spatialdds.org).

It's released to spark discussion—explore the spec, experiment, and join the conversation through issues or pull requests to help shape future iterations.

This repository hosts the published 1.3 and 1.4 specifications alongside a work-in-progress 1.5 draft. See the [CHANGELOG](CHANGELOG.md) for version history.


## Repository structure

- `SpatialDDS-1.2.md` / `SpatialDDS-1.3.md` / `SpatialDDS-1.4.md` / `SpatialDDS-1.5.md` – entry points that link to the specification's sections for each release.
- `SpatialDDS-1.2-full.md` / `SpatialDDS-1.3-full.md` / `SpatialDDS-1.4-full.md` / `SpatialDDS-1.5-full.md` – combined specifications generated from all sections.
- `sections/v*/` – markdown files containing each section of the specification, appendices, glossary, and references for a given version.
- `idl/v*/` – Interface Definition Language files for core, discovery, anchors, and other profiles as well as example IDL definitions, versioned with the spec.
- `manifests/v*/` – example JSON manifests illustrating how services, anchors, and content can advertise themselves within SpatialDDS, versioned alongside the spec.
- `scripts/` – helper scripts such as `build-spec.sh` for assembling the specification.

## Building the full specification

All IDL files in `idl/v*/` and manifest examples in `manifests/v*/` are treated as canonical. Markdown sections reference them with `{{include:...}}` placeholders. Regenerate the combined specification after modifying any of those files by running:

```bash
./scripts/build-spec.sh            # defaults to version 1.3
./scripts/build-spec.sh 1.4        # builds the 1.4 draft
```

The script injects the referenced IDL and manifest sources and writes `SpatialDDS-<version>-full.md` to the repository root, providing a convenient reference to the complete spec.

## Browsing the spec locally

The repository includes a lightweight [MkDocs](https://www.mkdocs.org/) configuration so you can explore the spec with built-in navigation and search:

1. Install MkDocs and the required extensions (e.g. `pip install mkdocs mkdocs-mermaid2-plugin pymdown-extensions`).
2. Generate the MkDocs sources with `./scripts/prepare_mkdocs.py` (also invoked by `build-spec.sh`). This expands all `{{include:...}}` blocks and writes the result to `mkdocs_docs/`.
3. Launch a local preview with `mkdocs serve` or render static files with `mkdocs build` (output goes to `site/`).

MkDocs reads from the generated `mkdocs_docs/` tree, so updating any section and re-running the helper script keeps the browsing experience current.

### Automatic publishing

Changes pushed to `main` automatically rebuild and publish the MkDocs site via `.github/workflows/docs.yml`. After the initial deploy, configure GitHub Pages to serve from the `gh-pages` branch to make updates live.

## Contributing

Issues and pull requests are welcome. Please open an issue to discuss large changes or questions about the specification. See the [CONTRIBUTING.md](CONTRIBUTING.md) file for more details.

For a practical illustration of the concepts, explore the companion [SpatialDDS demo](https://github.com/OpenArCloud/SpatialDDS-demo).

## License

This work is licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).
See the [LICENSE](LICENSE) file for details.
