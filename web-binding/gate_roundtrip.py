#!/usr/bin/env python3
"""Web Binding — Gate 2: CDR <-> JSON round-trip over golden vectors (brief §6).

Per vector in web-binding/golden/*.json:
  1. construct the type from `sample`, serialize to CDR;
  2. encode the instance to canonical JSON via the serializer tables; assert it
     equals the canonicalized `expected_json` (the hand-authored, generator-
     independent ground truth);
  3. construct from `expected_json` too, serialize to CDR; assert byte-identical
     to (1) — JSON -> CDR and sample -> CDR reconcile.

Needs `idlc -l py` + `cyclonedds`. SKIPS clean (reason + remedy) if absent.
Run under the borrowed environment (web-binding/README.md).

Canonical double formatting is ECMA-262 Number::toString (MAPPING.md), so the
digest form is reproducible across a Python producer and a browser consumer.
"""
import base64, glob, json, os, re, shutil, subprocess, sys, tempfile, importlib
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IDLDIR = os.path.join(ROOT, "idl", "v1.8")


# ---- ECMA-262 7.1.12.1 Number::toString (finite; NaN/Inf rejected per §2.3) --
def ecma262(x: float) -> str:
    if x != x or x in (float("inf"), float("-inf")):
        raise ValueError("non-finite double is not representable (NaN deprecated, §2.3)")
    if x == 0:
        return "0"
    sign = "-" if x < 0 else ""
    _, digits, exp = Decimal(repr(abs(x))).as_tuple()
    s = "".join(map(str, digits))
    while len(s) > 1 and s.endswith("0"):   # shortest significant digits
        s = s[:-1]; exp += 1
    k = len(s); n = exp + k
    if k <= n <= 21:
        return sign + s + "0" * (n - k)
    if 0 < n <= 21:
        return sign + s[:n] + "." + s[n:]
    if -6 < n <= 0:
        return sign + "0." + "0" * (-n) + s
    e = n - 1
    mant = s[0] + ("." + s[1:] if k > 1 else "")
    return sign + mant + "e" + ("+" if e >= 0 else "-") + str(abs(e))


def canon(v) -> str:
    """Canonical JSON text: sorted keys, ECMA-262 numbers, no insignificant ws."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return ecma262(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return json.dumps(v)
    if isinstance(v, list):
        return "[" + ",".join(canon(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ",".join(json.dumps(k) + ":" + canon(v[k])
                              for k in sorted(v)) + "}"
    if v is None:
        return "null"
    raise TypeError(f"uncanonicalizable: {type(v)}")


# ---- build importable bindings (reuse the sidecar pipeline, trimmed) --------
def build_bindings(work, package):
    files = sorted(glob.glob(os.path.join(IDLDIR, "*.idl"))) + \
        sorted(glob.glob(os.path.join(IDLDIR, "provisional", "*.idl")))
    staging = os.path.join(work, "_staging")
    os.makedirs(staging, exist_ok=True)
    for f in files:
        r = subprocess.run(["idlc", "-l", "py", "-I", IDLDIR, f],
                           cwd=staging, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"idlc failed on {os.path.basename(f)}:\n{r.stderr}")
    out = os.path.join(work, package)
    roots = sorted(d for d in os.listdir(staging)
                   if os.path.isdir(os.path.join(staging, d)))
    os.makedirs(out, exist_ok=True)
    for r in roots:
        shutil.move(os.path.join(staging, r), os.path.join(out, r))
    import_re = re.compile(r"^import (%s)$" % "|".join(roots), re.M)
    ref_re = re.compile(r"'(%s)\." % "|".join(roots))
    # index class name -> module for discriminator import fixups
    index = {}
    for p in glob.glob(os.path.join(out, "**", "*.py"), recursive=True):
        mod = ".".join([package] + os.path.relpath(p, out)[:-3].split(os.sep))
        for name in re.findall(r"^class (\w+)", open(p).read(), re.M):
            index.setdefault(name, mod)
    for p in glob.glob(os.path.join(out, "**", "*.py"), recursive=True):
        src = open(p).read()
        src = import_re.sub(rf"from {package} import \1", src)
        src = ref_re.sub(rf"'{package}.\1.", src)
        discs = set(re.findall(r"discriminator=(\w+)", src))
        missing = [d for d in discs if d not in re.findall(r"^class (\w+)", src, re.M)]
        if missing:
            anchor = "import cyclonedds.idl.types as types\n"
            inj = "".join(f"from {index[d]} import {d}\n" for d in sorted(missing))
            src = src.replace(anchor, anchor + inj, 1)
        open(p, "w").write(src)
    open(os.path.join(out, "__init__.py"), "w").write(
        "".join(f"from . import {r}\n" for r in roots))
    # map typename FQN -> (module, classname)
    fqn_index = {}
    for p in glob.glob(os.path.join(out, "**", "*.py"), recursive=True):
        mod = ".".join([package] + os.path.relpath(p, out)[:-3].split(os.sep))
        for cls, fqn in re.findall(r'^class (\w+)\(.*typename="([^"]+)"', open(p).read(), re.M):
            fqn_index[fqn] = (mod, cls)
    return fqn_index


# ---- construct instance from a logical value, using the serializer tables ---
class RT:
    def __init__(self, tables, fqn_index):
        self.t = tables; self.fx = fqn_index

    def cls(self, fqn):
        mod, name = self.fx[fqn]
        return getattr(importlib.import_module(mod), name)

    def build(self, rule, val):
        k = rule["t"]
        if k in ("bool", "str", "int"): return val
        if k in ("int64", "uint64"): return int(val)
        if k == "double": return float(val)
        if k == "base64": return base64.b64decode(val)
        if k == "enum": return getattr(self.cls(rule["fqn"]), val)
        if k == "array": return [self.build(rule["item"], x) for x in val]
        if k == "ref": return self.build_struct(rule["fqn"], val)
        if k == "union": return self.build_union(rule["fqn"], val)
        raise TypeError(k)

    def build_struct(self, fqn, d):
        kwargs = {}
        for fname, rule in self.t[fqn]["fields"]:
            kwargs[fname] = self.build(rule, d[fname])
        return self.cls(fqn)(**kwargs)

    def build_union(self, fqn, d):
        for label, member, rule in self.t[fqn]["cases"]:
            if label in d.get("type", "") or member in d:
                if member in d and rule is not None:
                    return self.cls(fqn)(**{member: self.build(rule, d[member])})
                return self.cls(fqn)()
        raise ValueError(f"no union case for {d}")

    def encode(self, rule, val):
        k = rule["t"]
        if k in ("bool", "str", "int"): return val
        if k in ("int64", "uint64"): return str(int(val))
        if k == "double": return float(val)
        if k == "base64": return base64.b64encode(bytes(val)).decode()
        if k == "enum": return val.name
        if k == "array": return [self.encode(rule["item"], x) for x in val]
        if k == "ref": return self.encode_struct(rule["fqn"], val)
        if k == "union": return self.encode_union(rule["fqn"], val)
        raise TypeError(k)

    def encode_struct(self, fqn, inst):
        out = {}
        for fname, rule in self.t[fqn]["fields"]:
            out[fname] = self.encode(rule, getattr(inst, fname))
        return out

    def encode_union(self, fqn, inst):
        disc = inst.discriminator
        dname = disc.name if hasattr(disc, "name") else str(disc)
        for label, member, rule in self.t[fqn]["cases"]:
            if label == dname:
                out = {"type": label}
                if rule is not None:
                    out[member] = self.encode(rule, getattr(inst, member))
                return out
        raise ValueError(f"union discriminator {dname} unmatched")


def main():
    if shutil.which("idlc") is None:
        print("gate_roundtrip: SKIP — `idlc` not on PATH. Remedy: install CycloneDDS "
              "idlc + the cyclonedds Python runtime and prepend the interpreter's "
              "bin to PATH (see web-binding/README.md)."); return 0
    try:
        import cyclonedds  # noqa
    except Exception:
        print("gate_roundtrip: SKIP — `cyclonedds` not importable. Remedy: run under "
              "the interpreter that has it (web-binding/README.md)."); return 0

    tables = json.load(open(os.path.join(HERE, "serializer_tables.json")))
    work = tempfile.mkdtemp(prefix="webjson_rt_")
    pkg = "webjson_rt_pkg"
    sys.path.insert(0, work)
    failures = []
    try:
        fqn_index = build_bindings(work, pkg)
        rt = RT(tables, fqn_index)
        vectors = sorted(glob.glob(os.path.join(HERE, "golden", "*.json")))
        checked = 0
        for vf in vectors:
            v = json.load(open(vf))
            fqn = v["type"].replace("::", ".")
            name = os.path.basename(vf)
            is_union = tables.get(fqn, {}).get("kind") == "union"
            bld = (lambda d: rt.build_union(fqn, d)) if is_union else (lambda d: rt.build_struct(fqn, d))
            enc = (lambda i: rt.encode_union(fqn, i)) if is_union else (lambda i: rt.encode_struct(fqn, i))
            try:
                inst_s = bld(v["sample"])
                inst_e = bld(v["expected_json"])
                cdr_s = inst_s.serialize(); cdr_e = inst_e.serialize()
                if cdr_s != cdr_e:
                    failures.append(f"{name}: CDR(sample) != CDR(expected_json)")
                got = enc(inst_s)
                if canon(got) != canon(v["expected_json"]):
                    failures.append(f"{name}: JSON mismatch\n    got:      {canon(got)}\n"
                                    f"    expected: {canon(v['expected_json'])}")
                inst_rt = type(inst_e).deserialize(cdr_e)
                if canon(enc(inst_rt)) != canon(v["expected_json"]):
                    failures.append(f"{name}: CDR->JSON round-trip mismatch")
                checked += 1
            except Exception as e:
                import traceback
                failures.append(f"{name}: {e}\n{traceback.format_exc()}")
    finally:
        sys.path.remove(work); shutil.rmtree(work, ignore_errors=True)
    if failures:
        print(f"gate_roundtrip FAILED ({len(failures)}):")
        for f in failures: print("  - " + f)
        return 1
    print(f"gate_roundtrip OK ({checked} golden vectors: CDR<->JSON round-trip, "
          f"canonical JSON matches ground truth).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
