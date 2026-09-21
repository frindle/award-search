"""Adversarial fixture for: aw-transfer-partners-s4-capital-one-capital-one

The target is a pure data module (no HTTP surface), so "integration" here means
importing the REAL src/transfer_partners.py file and asserting on its actual
contents -- not re-declaring expected values. The cases below fail at the stub
baseline (capital_one absent) and also catch plausible-but-wrong fixes: a wrong
name, a reordered/truncated partner list, an extra key in the entry, or a fix
that clobbers the citi_typ entry landed by s3.

Each case: (description, callable_returning_actual, expected)
"""
import sys
import importlib.util

spec = importlib.util.spec_from_file_location("target", 'src/transfer_partners.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["target"] = target
spec.loader.exec_module(target)


def _entry(slug):
    return target.PROGRAMS[slug]


CASES = [
    # --- the new entry: exact contract -------------------------------------
    ("capital_one slug exists in PROGRAMS",
     lambda: "capital_one" in target.PROGRAMS, True),

    ("capital_one name is exactly 'Capital One Miles'",
     lambda: _entry("capital_one")["name"], "Capital One Miles"),

    ("capital_one transfers_to has the exact 10 partners in order",
     lambda: _entry("capital_one")["transfers_to"],
     ["air_canada", "emirates", "etihad", "finnair", "flying_blue",
      "qantas", "singapore", "turkish", "virgin_atlantic", "qatar"]),

    ("capital_one entry has exactly the keys name + transfers_to (no extras)",
     lambda: sorted(_entry("capital_one").keys()), ["name", "transfers_to"]),

    # --- regression half: s3's citi_typ entry must survive untouched --------
    ("citi_typ slug still present after adding capital_one",
     lambda: "citi_typ" in target.PROGRAMS, True),

    ("citi_typ name unchanged ('Citi ThankYou Points')",
     lambda: _entry("citi_typ")["name"], "Citi ThankYou Points"),

    ("citi_typ transfers_to unchanged (9 partners, original order)",
     lambda: _entry("citi_typ")["transfers_to"],
     ["flying_blue", "jetblue", "qantas", "qatar", "singapore",
      "turkish", "virgin_atlantic", "etihad", "emirates"]),

    ("PROGRAMS holds exactly the two known slugs (no stray entries)",
     lambda: sorted(target.PROGRAMS.keys()), ["capital_one", "citi_typ"]),
]


def main():
    if len(CASES) < 3:
        print("  SCAFFOLD_INCOMPLETE: {} adversarial case(s) authored, need >= 3."
              .format(len(CASES)))
        print("  A generated scaffold is not a verify. Author the cases in "
              "test_fixture.py.")
        return 1
    fails = 0
    for desc, thunk, want in CASES:
        try:
            got = thunk()
        except Exception as e:
            print("  FAIL {} -- raised {}: {}".format(desc, type(e).__name__, e))
            fails += 1
            continue
        if got != want:
            print("  FAIL {} -- got {!r}, want {!r}".format(desc, got, want))
            fails += 1
    print("  {}/{} case(s) passed".format(len(CASES) - fails, len(CASES)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
