# SpatialDDS Specification Portal

Welcome to the SpatialDDS specification site. SpatialDDS defines an open protocol
for exchanging spatial data, digital twins, and AI-generated world models.

Use the navigation to explore the latest specification, learn about the
underlying profiles, and review supporting appendices. Each release of the
specification is published in full so that you can search, link, and reference it
like a traditional research document.

## Getting started

- Read the [SpatialDDS v1.3 Specification](specification-v1-3.md) for the latest
  draft, including appendices and glossary material.
- Consult the [SpatialDDS v1.2 Specification](specification-v1-2.md) for the
  previous release.
- Visit the SpatialDDS [IDL](../idl/) and [manifest](../manifests/) directories
  in this repository for additional example assets.

## Local development

You can preview the site locally by installing the MkDocs dependencies and
running the development server:

```bash
pip install -r requirements.txt
./scripts/build-spec.sh 1.2
./scripts/build-spec.sh 1.3
mkdocs serve
```

MkDocs will rebuild automatically as you edit the Markdown sources.
