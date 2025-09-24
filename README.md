# SpatialDDS Specification (Concept)

SpatialDDS is a concept protocol for real-world spatial computing that defines a shared bus for spatial data, AI world models, and digital twins.

It's released to spark discussion—explore the spec, experiment, and join the conversation through issues or pull requests to help shape future iterations.

This repository hosts the published 1.2 specification alongside a work-in-progress 1.3 draft. See the [CHANGELOG](CHANGELOG.md) for version history. The rendered documentation is published at [openarcloud.github.io/SpatialDDS-spec](https://openarcloud.github.io/SpatialDDS-spec/).


## Repository structure

- `SpatialDDS-1.2.md` / `SpatialDDS-1.3.md` – entry points that link to the specification's sections for each release.
- `SpatialDDS-1.2-full.md` / `SpatialDDS-1.3-full.md` – combined specifications generated from all sections.
- `sections/v*/` – markdown files containing each section of the specification, appendices, glossary, and references for a given version.
- `idl/v*/` – Interface Definition Language files for core, discovery, anchors, and other profiles as well as example IDL definitions, versioned with the spec.
- `manifests/v*/` – example JSON manifests illustrating how services, anchors, and content can advertise themselves within SpatialDDS, versioned alongside the spec.
- `scripts/` – helper scripts such as `build-spec.sh` for assembling the specification.

## Building the full specification

All IDL files in `idl/v*/` and manifest examples in `manifests/v*/` are treated as canonical. Markdown sections reference them with `{{include:...}}` placeholders. Regenerate the combined specification after modifying any of those files by running:

```bash
./scripts/build-spec.sh            # defaults to version 1.2
./scripts/build-spec.sh 1.3        # builds the 1.3 draft
```

The script injects the referenced IDL and manifest sources and writes `SpatialDDS-<version>-full.md` to the repository root, providing a convenient reference to the complete spec.

## Documentation site

The documentation site is generated with [MkDocs](https://www.mkdocs.org/). To preview it locally:

```bash
pip install -r requirements.txt
./scripts/build-spec.sh 1.2
./scripts/build-spec.sh 1.3
mkdocs serve
```

The GitHub Actions workflow in `.github/workflows/deploy-docs.yml` rebuilds the site and deploys it to GitHub Pages whenever changes land on `main`.

## Contributing

Issues and pull requests are welcome. Please open an issue to discuss large changes or questions about the specification.

For a practical illustration of the concepts, explore the companion [SpatialDDS demo](https://github.com/OpenArCloud/SpatialDDS-demo).

## License

This work is licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).
See the [LICENSE](LICENSE) file for details.

