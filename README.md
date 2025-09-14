# SpatialDDS Specification

SpatialDDS is a protocol for real-world spatial computing that defines a shared bus for spatial data, AI world models, and digital twins. This repository hosts version 1.2 of the specification along with related assets.

## Repository structure

- `SpatialDDS-1.2.md` – entry point that links to the specification's sections.
- `SpatialDDS-1.2-full.md` – combined specification generated from all sections.
- `sections/` – markdown files containing each section of the specification, appendices, glossary, and references.
- `idl/` – Interface Definition Language files for core, discovery, anchors, and other profiles as well as example IDL definitions.
- `manifests/` – example JSON manifests illustrating how services, anchors, and content can advertise themselves within SpatialDDS.
- `scripts/` – helper scripts such as `build-spec.sh` for assembling the specification.

## Building the full specification

Generate a single-file version of the specification by running:

```bash
./scripts/build-spec.sh
```

This writes `SpatialDDS-1.2-full.md` to the repository root, providing a convenient reference to the complete spec.

## Contributing

Issues and pull requests are welcome. Please open an issue to discuss large changes or questions about the specification.

## License

No license has been specified for this repository.

