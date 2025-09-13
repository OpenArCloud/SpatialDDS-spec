# SpatialDDS Specification

**SpatialDDS: A Protocol for Real-World Spatial Computing**  
Version 1.1 (September 2025)

---

## 📖 Overview
SpatialDDS is a lightweight, standards-based protocol for exchanging real-world spatial data over DDS (Data Distribution Service).
It provides a common “data bus” for robotics, AR/XR, IoT, digital twins, and AI-driven world models.

By organizing schemas into modular **IDL profiles**, SpatialDDS allows implementations to adopt only what they need, while remaining interoperable and codec-agnostic.

---

## 📂 Repository Layout
```
/spec
  00-front-matter.md      # Title, version, author, updates
  01-introduction.md      # High-level overview
  02-idl-profiles.md      # Core, Discovery, Anchors, Extensions
  03-example-manifests.md # VPS, Mapping, Content/Experience, etc.
  04-operational-scenarios.md
  05-extensions.md
  06-future-directions.md
  07-references.md
  08-glossary.md

/idl
  core.idl
  anchors.idl
  discovery.idl
  argeo.idl
  slam_frontend.idl
  semantics.idl
  vio.idl
  (optional) neural.idl, agent.idl
```
- **Markdown files (`/spec`)**: Human-readable spec, split by section.
- **IDL files (`/idl`)**: Clean schemas extracted from the text, one per profile/extension.

---

## 🔄 Versioning
- `v1.1`: Baseline import from Google Doc → Markdown + IDL.
- `v1.2`: In progress (adds Anchor Manifests and related scenarios).

Each version will be tagged in Git (`git tag v1.1`).

---

## 🛠️ Contributing
1. Fork the repo and create a branch (`feature/my-change`).
2. Edit the relevant Markdown and/or IDL files.
3. Submit a Pull Request with a clear description.

**Notes:**
- Keep Markdown clean and consistent (`#`, `##`, `###` headings, fenced code blocks).
- Add new profiles/extensions as separate `.idl` files under `/idl`.
- Use Issues for proposals or discussion before major changes.

---

## 📦 Outputs
From this Markdown + IDL source, the spec can be exported to:
- **PDF** via Pandoc or LaTeX
- **Static site** via Pandoc/Docusaurus
- **Reference schemas** from the `.idl` files

---

## 📣 Call to Action
SpatialDDS is an **open invitation** to collaborate on a lightweight, interoperable data bus for real-world spatial computing.
Feedback and contributions are welcome from the communities of **robotics, AR/XR, IoT, smart cities, and AI world models**.


---

## 🧰 Building Artifacts with Pandoc

Ensure you have **pandoc** installed. For PDF, install a LaTeX engine such as **TeX Live** (Linux) or **MacTeX** (macOS).

Build commands:

```bash
# Build PDF (default)
make

# Or explicitly:
make pdf

# Build Word and HTML outputs
make docx
make html

# Clean generated files
make clean
```

If you prefer using a Pandoc defaults file:
```bash
pandoc spec/*.md --defaults pandoc.yaml -o SpatialDDS-1.1.pdf
```
