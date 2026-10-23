#!/usr/bin/env python3
"""Read SpatialDDS IDL as the single source of type truth.

The dataset conformance harnesses (nuScenes, DeepSense 6G) used to hand-mirror
the IDL — enum value lists and struct field lists typed into Python dicts. That
mirror drifted from the canonical `idl/v<ver>/` tree (the Appendix I audit found
several stale copies), so a harness could report coverage against a type shape
the spec no longer carried.

This module removes the mirror. It parses the canonical `.idl` files directly and
exposes the three shapes the harnesses actually test:

  enum_values(name)   -> ordered enumerator names        (e.g. RadDynProp)
  struct_fields(name) -> ordered member names            (e.g. RadDetection)
  module_consts(name) -> ordered const names in a module (e.g. GnssService)

After the harnesses read from here, a hand-mirror drift is impossible by
construction: there is no second copy to drift from.

Parsing is deliberately small — SpatialDDS IDL is flat structs, plain enums, and
const modules; no unions or nested aggregates in the types the harnesses touch.
Each helper raises KeyError if the type is absent, so a renamed/removed type
surfaces as a crash in the harness rather than a silent miss.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ── comment stripping ────────────────────────────────────────────────
_LINE_COMMENT = re.compile(r"//[^\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
# a leading annotation on a declaration: @name or @name(...)
_ANNOTATION = re.compile(r"@[A-Za-z_][A-Za-z0-9_]*(?:\s*\([^)]*\))?\s*")
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _strip_comments(text):
    text = _BLOCK_COMMENT.sub("", text)
    text = _LINE_COMMENT.sub("", text)
    return text


def _idl_text(ver):
    """Concatenated, comment-stripped text of every .idl file for a version.

    Includes the provisional/ subtree so Appendix E types (e.g. OWM) resolve.
    """
    parts = []
    base = os.path.join(ROOT, "idl", f"v{ver}")
    for dirpath, _dirs, files in os.walk(base):
        for fn in sorted(files):
            if fn.endswith(".idl"):
                with open(os.path.join(dirpath, fn), encoding="utf-8") as fh:
                    parts.append(_strip_comments(fh.read()))
    return "\n".join(parts)


def _balanced_body(text, open_idx):
    """Return the text between the brace at/after open_idx and its match."""
    start = text.index("{", open_idx)
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
    raise ValueError("unbalanced braces")


def _find_block(text, keyword, name):
    """Body text of `keyword name { ... }` (keyword in {enum,struct,module})."""
    pat = re.compile(rf"\b{keyword}\s+{re.escape(name)}\b")
    m = pat.search(text)
    if not m:
        raise KeyError(f"{keyword} {name!r} not found in IDL")
    return _balanced_body(text, m.end())


def _member_name(statement):
    """Last identifier of a struct-member declaration, or None if not a member.

    Handles leading annotations (@key, @id(n), ...), qualified types
    (spatial::common::Vec3), templated types (sequence<T,N>, string<64>), and
    trailing array dims (matrix[3][3]). The member name is the final identifier
    once annotations and array dims are removed.
    """
    s = statement.strip()
    if not s:
        return None
    # drop leading annotations
    while True:
        m = _ANNOTATION.match(s)
        if not m:
            break
        s = s[m.end():]
    # drop any default/assignment and trailing array dimensions
    s = s.split("=", 1)[0]
    s = re.sub(r"\[[^\]]*\]", "", s)
    idents = _IDENT.findall(s)
    if not idents:
        return None
    return idents[-1]


class _Model:
    def __init__(self, ver):
        self.ver = ver
        self.text = _idl_text(ver)

    def enum_values(self, name):
        body = _find_block(self.text, "enum", name)
        out = []
        for raw in body.split(","):
            # strip @value(...) / other annotations, keep the enumerator ident
            frag = _ANNOTATION.sub("", raw).strip()
            if not frag:
                continue
            m = _IDENT.match(frag)
            if m:
                out.append(m.group(0))
        return out

    def struct_fields(self, name):
        body = _find_block(self.text, "struct", name)
        out = []
        for statement in body.split(";"):
            nm = _member_name(statement)
            if nm:
                out.append(nm)
        return out

    def module_consts(self, name):
        body = _find_block(self.text, "module", name)
        out = []
        for statement in body.split(";"):
            s = statement.strip()
            if s.startswith("const"):
                # const <type> <NAME> = <value>
                before_eq = s.split("=", 1)[0]
                idents = _IDENT.findall(before_eq)
                if idents:
                    out.append(idents[-1])
        return out


_CACHE = {}


def model(ver="1.8"):
    if ver not in _CACHE:
        _CACHE[ver] = _Model(ver)
    return _CACHE[ver]


def enum_values(name, ver="1.8"):
    return model(ver).enum_values(name)


def struct_fields(name, ver="1.8"):
    return model(ver).struct_fields(name)


def module_consts(name, ver="1.8"):
    return model(ver).module_consts(name)


if __name__ == "__main__":
    import sys
    v = sys.argv[1] if len(sys.argv) > 1 else "1.8"
    m = model(v)
    print(f"IDL model v{v}: parsed {len(m.text)} chars")
    for kind, nm in (("enum", "RadDynProp"), ("struct", "RadDetection"),
                     ("module", "GnssService")):
        fn = {"enum": m.enum_values, "struct": m.struct_fields,
              "module": m.module_consts}[kind]
        print(f"  {kind} {nm}: {fn(nm)}")
