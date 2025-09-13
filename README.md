# SpatialDDS Specification

This repository contains the SpatialDDS spec in Markdown, with IDL schemas and example manifests split into separate folders.

## Layout
```
/spec        # Markdown sections
/idl         # Extracted IDL per profile
/manifests   # Example manifests as JSON
```

## Build (Pandoc)
Requires: `pandoc` (and a LaTeX engine for PDF).

```bash
make          # builds PDF (default)
make pdf
make docx
make html
```

## Notes
- IDL files are extracted automatically from fenced ```idl blocks in the Markdown.
- Manifests are extracted from fenced ```json blocks when present; the Knossos Anchor Manifest is included explicitly.
