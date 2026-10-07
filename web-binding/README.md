# SpatialDDS Web Binding — generator, gates, and contract

Home of the web-binding JSON generator and its two gates (web-binding brief
§6, step 4). The generator is a pure function of the IDL: it walks the AST
`idlc` produces and emits one JSON Schema per type plus serializer tables. No
JSON mapping is ever hand-written; the only hand-authored artifacts here are the
mapping *contract* (`MAPPING.md`) and the *independently-computed* golden
vectors (`golden/`), whose independence from the generator is the point of
gate 2.

## Status

- `MAPPING.md` — the §5 canonical-JSON rule table, ratified (brief v1.1 step 3). **Authored.**
- `golden/` — independently-computed expected-JSON vectors incl. an adversarial double. **Authored.**
- `gen.py` — the generator (IDL AST → JSON Schema + serializer tables). *Pending (next step; builds against the environment below).*
- `gate_regen.py` — gate 1, regenerate-and-diff. *Pending.*
- `gate_roundtrip.py` — gate 2, CDR↔JSON round-trip against `golden/`. *Pending.*
- `gate_names.py` — gate 3, published member names are the IDL's and not the
  code generator's. **Authored**, after the binding's second implementation
  found `_global` and `_from` in eleven published schemas. The assertion is
  necessary because `additionalProperties: true` makes a renamed field silent
  in both directions, so a tolerant reader cannot detect it.
- `schemas/` — generated JSON Schemas (committed; gate 1 diffs against them). *Pending.*

## Build/validate environment (recorded per brief ruling — for CI and the next machine)

The generator and gate 2 need `idlc` with its Python backend and the
`cyclonedds` Python runtime (native core included). On this machine that
environment already exists; it is **borrowed, not replicated**:

- **Interpreter:** `/Users/fiberhog/miniforge3/bin/python3` — has `cyclonedds`
  importable with its bundled native dylibs (`libddsc`, `libcycloneddsidl`).
- **PATH:** prepend `/Users/fiberhog/miniforge3/bin` so that (a) `import
  cyclonedds` resolves and (b) `idlc -l py`'s backend shells out to *that*
  `python3`, not a bare system one. This is the one configuration step; without
  it `idlc -l py` picks the wrong interpreter and `import cyclonedds` fails.
- **idlc:** system `idlc` at `/usr/local/bin/idlc` (native CycloneDDS at
  `/usr/local/lib`). No `CYCLONEDDS_HOME` needed — the pip `cyclonedds` bundles
  its native libs and the system `idlc` carries its own.

Confirmed working: `PATH=/Users/fiberhog/miniforge3/bin:$PATH idlc -l py …`
generates; the `cyclonedds` codec serializes and round-trips CDR under the
miniforge interpreter.

Invoke the generator and gates as:

```sh
PATH=/Users/fiberhog/miniforge3/bin:$PATH /Users/fiberhog/miniforge3/bin/python3 web-binding/gen.py
PATH=/Users/fiberhog/miniforge3/bin:$PATH /Users/fiberhog/miniforge3/bin/python3 web-binding/gate_roundtrip.py
```

**CI:** the runner `pip install cyclonedds` as the existing topic-construct job
does; gate 2 skips-clean only where the environment is genuinely absent, and
prints its reason *and* this remedy when it does (runner-manifest discipline).
After this machine is set up per the above, the gate should not skip here.

## Generator architecture (no second parser)

`gen.py` runs `idlc -l py` over `idl/v1.8/` (and `provisional/`), imports the
generated `IdlStruct` classes, and reflects over their `cyclonedds.idl` type
metadata to emit JSON Schema + serializer tables. It therefore walks the same
AST `idlc` produces — there is no independent IDL parser, by design (brief §6,
principle 3). The post-processing the demo/sidecar generators apply (union
discriminator imports, python-keyword field fixups, package nesting) is reused,
not reinvented.
