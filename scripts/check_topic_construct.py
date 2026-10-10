#!/usr/bin/env python3
"""SpatialDDS topic-construction gate (findings batch 2, Part C.2).

Motivated by Finding 2: a sequence bound larger than a binding's limit is not
caught by ``idlc`` alone — it surfaces only when a runtime constructs a DDS
``Topic`` for the type. This gate generates Python bindings for every stable and
provisional IDL type and constructs a CycloneDDS ``Topic`` for each in a
throwaway participant. It is the check that would have caught the 65535 bound
before an implementer did.

Requirements (both optional; the gate SKIPS cleanly when either is absent so it
never breaks a docs-only build):
  * ``idlc`` on PATH with the Python backend (``idlc -l py``).
  * The ``cyclonedds`` Python package importable.

Usage: check_topic_construct.py [version]   (default: 1.7)
Exit status:
  0  all constructed types succeeded, OR the toolchain is unavailable (skip).
  1  at least one type failed to construct a Topic.
"""
import glob
import importlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _have_idlc_py():
    if not shutil.which("idlc"):
        return False
    # The Python backend is NOT advertised in `idlc -h`; it is provided by the
    # cyclonedds Python package the active interpreter exposes (idlc shells out
    # to that interpreter). Sniffing `idlc -h` for "py" therefore reported a
    # false negative and the gate habitually skipped even where `idlc -l py`
    # works. Probe the only reliable way — a trial generation — so the gate runs
    # whenever it is invoked under the documented interpreter that carries
    # cyclonedds (see web-binding/README.md), and still skips cleanly where the
    # backend is genuinely absent.
    d = tempfile.mkdtemp(prefix="idlc_py_probe_")
    try:
        src = os.path.join(d, "_probe.idl")
        with open(src, "w") as fh:
            fh.write("module _probe { struct S { long x; }; };\n")
        r = subprocess.run(["idlc", "-l", "py", src], cwd=d,
                           capture_output=True, text=True)
        return r.returncode == 0 and bool(
            glob.glob(os.path.join(d, "**", "*.py"), recursive=True))
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _have_cyclonedds():
    try:
        importlib.import_module("cyclonedds")
        return True
    except Exception:
        return False


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "1.8"
    idl_dir = os.path.join(ROOT, "idl", f"v{version}")
    if not os.path.isdir(idl_dir):
        print(f"error: missing directory {idl_dir}", file=sys.stderr)
        return 2

    if not _have_idlc_py() or not _have_cyclonedds():
        print("check_topic_construct: SKIP "
              "(requires idlc -l py and the cyclonedds Python package). "
              "IDL bounds are still validated by validate_idl_1_7.sh.")
        return 0

    # Deferred imports — only reached when cyclonedds is present.
    from cyclonedds.domain import DomainParticipant
    from cyclonedds.topic import Topic
    from cyclonedds.idl import IdlStruct

    idl_files = sorted(glob.glob(os.path.join(idl_dir, "*.idl"))) + \
        sorted(glob.glob(os.path.join(idl_dir, "provisional", "*.idl")))

    workdir = tempfile.mkdtemp(prefix="spatialdds_pytopic_")
    sys.path.insert(0, workdir)
    failures = []
    generated_pkgs = set()
    try:
        for f in idl_files:
            # idlc writes its package tree into the working directory and does
            # not honour -o; run it with cwd=workdir so the tree lands where the
            # walk below looks (an -o that was silently ignored is why this gate
            # used to construct zero types once it stopped skipping).
            r = subprocess.run(
                ["idlc", "-l", "py", "-I", idl_dir, f],
                cwd=workdir, capture_output=True, text=True)
            if r.returncode != 0:
                failures.append(f"{os.path.basename(f)}: idlc -l py failed: "
                                f"{r.stderr.strip()[:200]}")
        # idlc emits union discriminators as bare names, so a union-bearing
        # module (e.g. core's CovMatrix on CovarianceType) fails to import until
        # the missing import is added — the same fixup the binding generator
        # applies. Index class -> module, then inject the imports.
        classdef = re.compile(r"^class (\w+)", re.M)
        index = {}
        for p in glob.glob(os.path.join(workdir, "**", "*.py"), recursive=True):
            mod = os.path.relpath(p, workdir)[:-3].replace(os.sep, ".")
            for name in classdef.findall(open(p).read()):
                index.setdefault(name, mod)
        for p in glob.glob(os.path.join(workdir, "**", "*.py"), recursive=True):
            src = open(p).read()
            defined = set(classdef.findall(src))
            missing = [d for d in set(re.findall(r"discriminator=(\w+)", src))
                       if d not in defined and d in index]
            anchor = "import cyclonedds.idl.types as types\n"
            if missing and anchor in src:
                inj = "".join(f"from {index[d]} import {d}\n" for d in sorted(missing))
                open(p, "w").write(src.replace(anchor, anchor + inj, 1))
        # The Python backend emits a top-level 'spatial' (and 'builtin')
        # package tree. Import every generated module and construct a Topic for
        # each IdlStruct subclass.
        for base in ("spatial", "builtin"):
            pkg_root = os.path.join(workdir, base)
            if not os.path.isdir(pkg_root):
                continue
            for dirpath, _, files in os.walk(pkg_root):
                for fn in files:
                    if not fn.endswith(".py") or fn == "__init__.py":
                        continue
                    rel = os.path.relpath(os.path.join(dirpath, fn), workdir)
                    mod = rel[:-3].replace(os.sep, ".")
                    generated_pkgs.add(mod)

        participant = DomainParticipant(0)
        constructed = 0
        for mod in sorted(generated_pkgs):
            try:
                m = importlib.import_module(mod)
            except Exception as e:
                failures.append(f"import {mod}: {e}")
                continue
            for name in dir(m):
                obj = getattr(m, name)
                if isinstance(obj, type) and issubclass(obj, IdlStruct) \
                        and obj is not IdlStruct:
                    try:
                        Topic(participant, f"probe_{mod}_{name}", obj)
                        constructed += 1
                    except Exception as e:
                        failures.append(f"{mod}.{name}: Topic() failed: {e}")
    finally:
        sys.path.remove(workdir)
        shutil.rmtree(workdir, ignore_errors=True)

    if constructed == 0 and not failures:
        failures.append(
            "gate constructed 0 Topics — nothing was exercised (idlc produced no "
            "importable IdlStruct types); a zero-construction run is not a pass")

    if failures:
        print(f"Topic-construction gate FAILED for v{version} "
              f"({len(failures)} issue(s)):\n")
        for x in failures:
            print(f"  - {x}")
        return 1
    print(f"Topic-construction gate OK for v{version} "
          f"({constructed} type(s) constructed a Topic).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
