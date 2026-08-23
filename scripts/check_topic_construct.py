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
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _have_idlc_py():
    if not shutil.which("idlc"):
        return False
    out = subprocess.run(["idlc", "-h"], capture_output=True, text=True)
    return "py" in (out.stdout + out.stderr)


def _have_cyclonedds():
    try:
        importlib.import_module("cyclonedds")
        return True
    except Exception:
        return False


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "1.7"
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
            r = subprocess.run(
                ["idlc", "-l", "py", "-I", idl_dir, "-o", workdir, f],
                capture_output=True, text=True)
            if r.returncode != 0:
                failures.append(f"{os.path.basename(f)}: idlc -l py failed: "
                                f"{r.stderr.strip()[:200]}")
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
