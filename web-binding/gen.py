#!/usr/bin/env python3
"""SpatialDDS Web Binding — JSON generator (web-binding brief §6, step 4).

Pure function of the IDL: runs `idlc -l py` over idl/v1.8 (+provisional) and
parses idlc's rendered output (its AST, as generated dataclasses) to emit one
JSON Schema per struct type plus serializer tables. There is no independent IDL
parser — the input is idlc's product. Rules per web-binding/MAPPING.md.

Run (borrowed environment — see web-binding/README.md):
    PATH=/Users/fiberhog/miniforge3/bin:$PATH python3 web-binding/gen.py [--check]

--check regenerates to a temp dir and exits non-zero if it differs from the
committed web-binding/schemas/ + serializer_tables.json (gate 1).
"""
import glob, json, keyword, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDLDIR = os.path.join(ROOT, "idl", "v1.8")
OUT_SCHEMAS = os.path.join(ROOT, "web-binding", "schemas")
OUT_TABLES = os.path.join(ROOT, "web-binding", "serializer_tables.json")

# ---- run idlc into a temp cwd (idlc writes packages to CWD) ----------------
def run_idlc():
    work = tempfile.mkdtemp(prefix="webjson_gen_")
    files = sorted(glob.glob(os.path.join(IDLDIR, "*.idl"))) + \
        sorted(glob.glob(os.path.join(IDLDIR, "provisional", "*.idl")))
    for f in files:
        r = subprocess.run(["idlc", "-l", "py", "-I", IDLDIR, f],
                           cwd=work, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"idlc failed on {os.path.basename(f)}:\n{r.stderr}")
    return work

# ---- idlc's Python-keyword renames, undone ---------------------------------
# This generator reads the Python `idlc` rendered rather than an IDL AST, so it
# sees `idlc`'s identifiers, not the specification's. Where an IDL member name
# collides with a Python keyword -- `global` in CoverageElement and ROI, `from`
# in Transform and ValidityWindow -- `idlc` prefixes an underscore, and those
# renames were published: `_global` and `_from` reached eleven schemas and four
# serializer tables, including the discovery types.
#
# MAPPING.md requires members under their verbatim IDL names, and the
# specification's own §3.3.4 coverage and §8.2.3 manifest examples write
# `"global": false`. So the published contract contradicted both the rule and
# the prose, and `additionalProperties: true` made it silent in each direction:
# a conforming producer's `global` was ignored as unknown, while `required`
# reported `_global` missing.
#
# Found by the binding's second implementation (OpenArCloud/spatialdds-web,
# WEB-BINDING-FINDINGS.md finding 10), which parses the IDL directly and so saw
# the two names disagree.
#
# IDL identifiers cannot begin with an underscore, so a leading underscore in
# `idlc`'s output is always a rename. The condition is kept narrow anyway --
# the stripped name must actually be a Python keyword -- so this reverses the
# documented rule and nothing else.
def unmangle(name):
    if name.startswith("_") and keyword.iskeyword(name[1:]):
        return name[1:]
    return name


# ---- parse idlc's rendered .py into a symbol table -------------------------
CLASS_ENUM = re.compile(r'^class (\w+)\(idl\.IdlEnum, typename="([^"]+)"')
CLASS_UNION = re.compile(r'^class (\w+)\(idl\.IdlUnion, discriminator=(\w+).*typename="([^"]+)"')
CLASS_STRUCT = re.compile(r'^class (\w+)\(idl\.IdlStruct, typename="([^"]+)"')
TYPEDEF = re.compile(r"^(\w+) = types\.typedef\['([^']+)',\s*(.+)\]$")
ENUM_MEMBER = re.compile(r'^    (\w+) = \d+')
UNION_CASE = re.compile(r'^    (\w+): types\.case\[\[([^\]]+)\],\s*(.+)\]$')
STRUCT_FIELD = re.compile(r'^    (\w+)\s*:\s*(.+?)\s*$')

def parse(work):
    syms = {}  # fqn -> dict
    for path in sorted(glob.glob(os.path.join(work, "**", "*.py"), recursive=True)):
        lines = open(path).read().splitlines()
        i = 0
        while i < len(lines):
            ln = lines[i]
            mt = TYPEDEF.match(ln)
            if mt:
                syms[mt.group(2)] = {"kind": "typedef", "under": mt.group(3).strip()}
                i += 1; continue
            me = CLASS_ENUM.match(ln)
            if me:
                members = []
                j = i + 1
                while j < len(lines) and (lines[j].startswith("    ") or not lines[j].strip()):
                    mm = ENUM_MEMBER.match(lines[j])
                    if mm: members.append(mm.group(1))
                    j += 1
                syms[me.group(2)] = {"kind": "enum", "members": members}
                i = j; continue
            mu = CLASS_UNION.match(ln)
            if mu:
                cases = []
                j = i + 1
                while j < len(lines) and (lines[j].startswith("    ") or not lines[j].strip()):
                    mc = UNION_CASE.match(lines[j])
                    if mc:
                        labels = [x.strip().split(".")[-1] for x in mc.group(2).split(",")]
                        cases.append({"member": unmangle(mc.group(1)),
                                      "labels": labels,
                                      "type": mc.group(3).strip()})
                    j += 1
                syms[mu.group(3)] = {"kind": "union", "disc": mu.group(2), "cases": cases}
                i = j; continue
            ms = CLASS_STRUCT.match(ln)
            if ms:
                fields = []
                j = i + 1
                while j < len(lines) and (lines[j].startswith("    ") or not lines[j].strip()):
                    s = lines[j]
                    if s.strip().startswith(("annotate.", "@", "#", '"', "'")):
                        j += 1; continue
                    mf = STRUCT_FIELD.match(s)
                    if mf and "types.case[" not in s:
                        fields.append((unmangle(mf.group(1)), mf.group(2)))
                    j += 1
                syms[ms.group(2)] = {"kind": "struct", "fields": fields}
                i = j; continue
            i += 1
    return syms

# ---- resolve an idlc type expression to (rule, schema) ---------------------
PRIM = {
    "bool": ({"t": "bool"}, {"type": "boolean"}),
    "str": ({"t": "str"}, {"type": "string"}),
    "types.int8":  ({"t": "int"}, {"type": "integer", "minimum": -128, "maximum": 127}),
    "types.int16": ({"t": "int"}, {"type": "integer", "minimum": -32768, "maximum": 32767}),
    "types.int32": ({"t": "int"}, {"type": "integer", "minimum": -2147483648, "maximum": 2147483647}),
    "types.uint8":  ({"t": "int"}, {"type": "integer", "minimum": 0, "maximum": 255}),
    "types.uint16": ({"t": "int"}, {"type": "integer", "minimum": 0, "maximum": 65535}),
    "types.uint32": ({"t": "int"}, {"type": "integer", "minimum": 0, "maximum": 4294967295}),
    "types.int64":  ({"t": "int64"}, {"type": "string", "pattern": r"^-?\d+$"}),
    "types.uint64": ({"t": "uint64"}, {"type": "string", "pattern": r"^\d+$"}),
    "types.float32": ({"t": "double"}, {"type": "number"}),
    "types.float64": ({"t": "double"}, {"type": "number"}),
}
SEQ = re.compile(r'^types\.sequence\[(.+),\s*(\d+)\]$')
ARR = re.compile(r'^types\.array\[(.+),\s*(\d+)\]$')

def resolve(expr, syms, defs, seen):
    expr = expr.strip()
    if expr in PRIM:
        return PRIM[expr]
    # A fixed array and a bounded sequence both map to a JSON array, and the
    # schemas have always distinguished them by minItems. The serializer tables
    # did not: both were `{"t": "array"}`, which is unusable to anything that
    # has to read CDR, because a sequence is length-prefixed and a fixed array
    # is not. The distinction is known here -- `types.array` against
    # `types.sequence` -- and was simply not recorded.
    #
    # So it is recorded: `length` for a fixed array, whose elements sit inline,
    # and `bound` for a bounded sequence, whose count precedes them. A consumer
    # can now tell which from the table alone. Same for an octet payload, where
    # the ambiguity was identical and the consequence worse, because base64
    # hides it: `octet[N]` is N raw bytes, `sequence<octet,N>` is a count and
    # then bytes.
    #
    # Found by the binding's second implementation (OpenArCloud/spatialdds-web,
    # WEB-BINDING-FINDINGS.md finding 8), which could not build a decoder from
    # the published tables and had to parse the IDL instead.
    for rx, fixed in ((SEQ, False), (ARR, True)):
        m = rx.match(expr)
        if m:
            inner, n = m.group(1).strip(), int(m.group(2))
            extent = {"length": n} if fixed else {"bound": n}
            if inner == "types.uint8":  # octet payload -> base64
                return ({"t": "base64", **extent},
                        {"type": "string", "contentEncoding": "base64"})
            r, s = resolve(inner, syms, defs, seen)
            sch = {"type": "array", "items": s, "maxItems": n}
            if fixed: sch["minItems"] = n
            return ({"t": "array", "item": r, **extent}, sch)
    if expr.startswith("'") and expr.endswith("'"):
        fqn = expr[1:-1]
        return resolve_fqn(fqn, syms, defs, seen)
    raise SystemExit(f"gen.py: unresolved type expression: {expr!r}")

def resolve_fqn(fqn, syms, defs, seen):
    sym = syms.get(fqn)
    if sym is None:
        raise SystemExit(f"gen.py: unknown type FQN {fqn!r}")
    if sym["kind"] == "typedef":
        return resolve(sym["under"], syms, defs, seen)
    if sym["kind"] == "enum":
        return ({"t": "enum", "fqn": fqn}, {"type": "string", "enum": list(sym["members"])})
    if sym["kind"] == "union":
        _ensure_def(fqn, syms, defs, seen)
        return ({"t": "union", "fqn": fqn}, {"$ref": f"#/$defs/{_defname(fqn)}"})
    if sym["kind"] == "struct":
        _ensure_def(fqn, syms, defs, seen)
        return ({"t": "ref", "fqn": fqn}, {"$ref": f"#/$defs/{_defname(fqn)}"})
    raise SystemExit(f"gen.py: unhandled symbol {fqn}")

def _defname(fqn): return fqn.replace(".", "_")

def _ensure_def(fqn, syms, defs, seen):
    if fqn in seen: return
    seen.add(fqn)
    sym = syms[fqn]
    if sym["kind"] == "struct":
        props, req = {}, []
        for fname, fexpr in sym["fields"]:
            _, s = resolve(fexpr, syms, defs, seen)
            props[fname] = s; req.append(fname)
        defs[_defname(fqn)] = {"type": "object", "properties": props,
                               "required": req, "additionalProperties": True}
    elif sym["kind"] == "union":
        branches = []
        for c in sym["cases"]:
            label = c["labels"][0]
            b = {"type": "object", "required": ["type"],
                 "properties": {"type": {"const": label}}, "additionalProperties": True}
            if not (c["member"] == "none" and c["type"] == "types.uint8"):
                _, s = resolve(c["type"], syms, defs, seen)
                b["properties"][c["member"]] = s
            branches.append(b)
        defs[_defname(fqn)] = {"oneOf": branches}

# ---- serializer tables -----------------------------------------------------
def build_tables(syms):
    tables = {}
    for fqn, sym in syms.items():
        if sym["kind"] == "struct":
            fields = []
            for fname, fexpr in sym["fields"]:
                r, _ = resolve(fexpr, syms, {}, set())
                fields.append([fname, r])
            tables[fqn] = {"kind": "struct", "fields": fields}
        elif sym["kind"] == "union":
            cases = []
            for c in sym["cases"]:
                if c["member"] == "none" and c["type"] == "types.uint8":
                    r = None
                else:
                    r, _ = resolve(c["type"], syms, {}, set())
                cases.append([c["labels"][0], c["member"], r])
            tables[fqn] = {"kind": "union", "disc": sym["disc"], "cases": cases}
        elif sym["kind"] == "enum":
            tables[fqn] = {"kind": "enum", "members": list(sym["members"])}
    return tables

# ---- emit ------------------------------------------------------------------
def emit(syms, schemas_dir, tables_path):
    structs = [fqn for fqn, s in syms.items() if s["kind"] == "struct"]
    os.makedirs(schemas_dir, exist_ok=True)
    for fqn in sorted(structs):
        defs, seen = {}, set()
        _ensure_def(fqn, syms, defs, seen)
        top = defs.pop(_defname(fqn))
        doc = {"$schema": "https://json-schema.org/draft/2020-12/schema",
               "$id": f"spatialdds:webjson:{fqn}", "title": fqn}
        doc.update(top)
        if defs: doc["$defs"] = dict(sorted(defs.items()))
        with open(os.path.join(schemas_dir, _defname(fqn) + ".json"), "w") as fh:
            json.dump(doc, fh, indent=2, sort_keys=True); fh.write("\n")
    with open(tables_path, "w") as fh:
        json.dump(build_tables(syms), fh, indent=2, sort_keys=True); fh.write("\n")
    return len(structs)

def generate(schemas_dir, tables_path):
    work = run_idlc()
    try:
        syms = parse(work)
        return emit(syms, schemas_dir, tables_path)
    finally:
        shutil.rmtree(work, ignore_errors=True)
        for leak in ("spatial", "builtin"):
            shutil.rmtree(os.path.join(os.getcwd(), leak), ignore_errors=True)

def main():
    if "--check" in sys.argv:
        tmp = tempfile.mkdtemp(prefix="webjson_check_")
        try:
            generate(os.path.join(tmp, "schemas"), os.path.join(tmp, "tables.json"))
            diffs = []
            a = {os.path.basename(p): open(p).read()
                 for p in glob.glob(os.path.join(tmp, "schemas", "*.json"))}
            b = {os.path.basename(p): open(p).read()
                 for p in glob.glob(os.path.join(OUT_SCHEMAS, "*.json"))}
            for k in sorted(set(a) | set(b)):
                if a.get(k) != b.get(k): diffs.append(k)
            if open(os.path.join(tmp, "tables.json")).read() != \
               (open(OUT_TABLES).read() if os.path.exists(OUT_TABLES) else ""):
                diffs.append("serializer_tables.json")
            if diffs:
                print("gen.py --check FAILED: committed output is stale:\n  " +
                      "\n  ".join(diffs)); return 1
            print(f"gen.py --check OK ({len(b)} schemas match)."); return 0
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    n = generate(OUT_SCHEMAS, OUT_TABLES)
    print(f"gen.py: wrote {n} schemas to web-binding/schemas/ + serializer_tables.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())
