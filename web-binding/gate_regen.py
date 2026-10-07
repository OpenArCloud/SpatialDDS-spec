#!/usr/bin/env python3
"""Web Binding — Gate 1: regenerate-and-diff (web-binding brief §6).

Regenerates every JSON Schema + the serializer tables from the IDL and fails if
the committed web-binding/schemas/ or serializer_tables.json differ. A type
change that forgets its JSON form cannot merge.

Thin wrapper over `gen.py --check`. Run under the borrowed environment
(web-binding/README.md); needs `idlc`. If idlc is absent it SKIPS clean, printing
the reason and the remedy (runner-manifest discipline).
"""
import os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    if shutil.which("idlc") is None:
        print("gate_regen: SKIP — `idlc` not on PATH. Remedy: install CycloneDDS "
              "idlc and prepend the interpreter's bin to PATH "
              "(see web-binding/README.md).")
        return 0
    r = subprocess.run([sys.executable, os.path.join(HERE, "gen.py"), "--check"])
    return r.returncode

if __name__ == "__main__":
    sys.exit(main())
