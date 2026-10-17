#!/usr/bin/env python3
"""Item 7.4 — streamed payloads are validated, and a malformed one still fails.

The volatile-lane finding: `check_schema_validity` saw only latched GET
collections, so a VOLATILE lane — empty collection, all traffic on the N.5
stream — was never validated, and one latched instance elsewhere lifted the
endpoint-wide count to PASS (measured: 87% of a VOLATILE-heavy endpoint's
payloads unvalidated). The fix adds `check_streamed_validity`, which subscribes
per resource and validates every streamed payload, with a per-resource
UNEXERCISED verdict and a bounded read (a floor, not a total, for a live backend
whose stream never goes quiet). Its validation core is `_validate_stream`, a
pure function so the rule is exercisable without a socket.

This probe drives `_validate_stream` directly and asserts:

  VALID STREAM   every `data` payload validates -> the count, no raise.
  MALFORMED      a payload that fails its schema -> raises (the teeth): a
                 streamed payload is held to its schema exactly as a latched one.
  NON-SAMPLES    markers / disposes / liveliness (no `data`) are not counted ->
                 an all-marker stream is zero, which makes the check UNEXERCISED.
  CAP            hitting the sample cap reports the count as a floor (hit_cap).

Run it directly; exit 0 iff every expectation holds.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run import _validate_stream  # noqa: E402

SCHEMA = {"type": "object", "required": ["x"],
          "properties": {"x": {"type": "integer"}}, "additionalProperties": True}


def msg(x):
    return {"event": "sample", "data": {"x": x}}


def main():
    bad = []

    # VALID: three data payloads, plus a marker and a dispose (no `data`).
    stream = [msg(1), msg(2), {"event": "end_of_replay", "replayed": 2},
              msg(3), {"event": "dispose", "key": "k"}]
    n, hit = _validate_stream(stream, SCHEMA, cap=500)
    print(f"VALID STREAM : count={n} hit_cap={hit}")
    if (n, hit) != (3, False):
        bad.append(f"valid: expected count=3 hit_cap=False, got {n}/{hit}")

    # MALFORMED: a payload whose `x` is a string fails the schema -> raises.
    raised = False
    try:
        _validate_stream([msg(1), {"event": "sample", "data": {"x": "nope"}}],
                         SCHEMA, cap=500)
    except Exception as e:
        raised = True
        print(f"MALFORMED    : raised {type(e).__name__} (teeth)")
    if not raised:
        bad.append("malformed: a streamed payload that fails its schema must raise")

    # NON-SAMPLES: only markers/disposes -> zero counted -> check reports UNEXERCISED.
    n2, _ = _validate_stream([{"event": "end_of_replay"}, {"event": "dispose"}],
                             SCHEMA, cap=500)
    print(f"NON-SAMPLES  : count={n2}")
    if n2 != 0:
        bad.append(f"non-samples: expected 0, got {n2}")

    # CAP: three payloads with cap=3 -> hit_cap, so the count is a floor.
    n3, hit3 = _validate_stream([msg(1), msg(2), msg(3)], SCHEMA, cap=3)
    print(f"CAP          : count={n3} hit_cap={hit3}")
    if not hit3:
        bad.append("cap: count == cap must report hit_cap (the count is a floor)")

    print()
    if bad:
        print("stream_validity_probe FAILED:")
        for b in bad:
            print("  - " + b)
        return 1
    print("stream_validity_probe OK — streamed payloads validate per resource, a "
          "malformed one fails, and the cap reports a floor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
