# Golden vectors — independent ground truth for gate 2

Each file pins the **expected JSON** for one sample of one type, computed **by
hand, independently of the generator**. That independence is the gate's value:
if the generator's serializer and these vectors agree, agreement is evidence;
if the generator produced both, it would only be consistent with itself.

Gate 2 (`gate_roundtrip.py`, run under the borrowed environment — see
`../README.md`) does, per vector:

1. Construct the sample of `type` from `sample` (the logical field values).
2. Serialize to CDR via `cyclonedds`, then CDR → the binding's JSON; assert it
   equals `expected_json`.
3. JSON → sample → CDR; assert the CDR is **byte-identical** to step 2's CDR.

`expected_json` is authored here; the CDR bytes are produced and checked by the
gate (they need the codec). Vectors are **fault-injected before trusted**: flip
one byte/field and confirm the gate fails (brief §6).

## Vector file shape

```json
{
  "type": "spatial::core::PoseSE3",
  "description": "...",
  "sample": { ...logical field values, guards included as booleans... },
  "expected_json": { ...the binding JSON the generator must produce... },
  "exercises": ["which MAPPING.md rules this vector pins"]
}
```

`sample` carries guard booleans (`has_*`) and all members as the type really
holds them; `expected_json` is the MAPPING.md projection (guards dropped, guarded
members present/absent accordingly, int64 as string, enums by name, union tagged,
doubles by the ECMA-262 rule). The gate maps `sample` onto the generated
`IdlStruct`.

## The vectors

- `builtin_time.json` — `int64` past 2⁵³ → unconditional decimal **string**; `uint32` stays a number.
- `pose_adversarial_double.json` — the ECMA-262 double rule on `0.1`, `0.1+0.2`, `1e21`, and integer-valued doubles (`0`, `1`).
- `covmatrix_cov_pos3.json` — **union** as a tagged object, discriminator key `"type"`.
- `frameref_guards.json` — `has_*` guard → presence (one guard false → member absent; one guard true → its run present), enum by name, guard booleans dropped.
