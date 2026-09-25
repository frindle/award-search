"""Adversarial fixture for: aw-sched-routes-s8-parse-cap

>>> THE ONE THING THE GENERATOR CANNOT WRITE FOR YOU <<<

CASES is empty and the verify FAILS until you fill it in. That is deliberate.
A generator can emit a verify that DISCRIMINATES (fails at baseline, passes on
a fix). It cannot decide whether the verify is RELEVANT -- whether it tests the
property the task actually asked for. A benign case passes broken work.

Pick inputs that separate "did the job" from "made the test go green":
  * the exact boundary the defect is about, and one on each side of it
  * the degenerate inputs (missing key, None, empty, wrong type) that must NOT
    raise
  * at least one case that a plausible WRONG fix would fail
  * the regression half: things that already work and must keep working

Each case: (description, callable_returning_actual, expected)
"""
import sys
import types
import importlib.util
import pathlib


def _load_target():
    """Load src/webui/scheduled_routes.py as a real package module.

    The target uses relative imports (`from ..scheduled_runner import ...`),
    so it cannot be loaded standalone: register stub parent packages and the
    not-yet-landed sibling modules first, then exec the file under its true
    dotted name.
    """
    root = pathlib.Path(__file__).resolve().parent / "src"

    def _pkg(name, path):
        mod = types.ModuleType(name)
        mod.__path__ = [str(path)]
        sys.modules[name] = mod
        return mod

    if "src" not in sys.modules:
        _pkg("src", root)
    if "src.webui" not in sys.modules:
        _pkg("src.webui", root / "webui")

    # Sibling modules the target imports but that are out of scope for this
    # slice -- stub them so the import succeeds without pulling in Playwright.
    runner = types.ModuleType("src.scheduled_runner")
    runner.run_schedule = lambda **kw: {"stub": True}
    sys.modules.setdefault("src.scheduled_runner", runner)

    partners = types.ModuleType("src.transfer_partners")
    partners.list_partners = lambda: []
    sys.modules.setdefault("src.transfer_partners", partners)

    name = "src.webui.scheduled_routes"
    spec = importlib.util.spec_from_file_location(
        name, root / "webui" / "scheduled_routes.py")
    target = importlib.util.module_from_spec(spec)
    # REGISTER BEFORE EXEC so string-annotation resolution finds the module.
    sys.modules[name] = target
    spec.loader.exec_module(target)
    return target


target = _load_target()


def _raises_value_error(fn, *args):
    try:
        fn(*args)
    except ValueError:
        return True
    except Exception as e:  # wrong exception type is a failure
        return "raised {} instead of ValueError".format(type(e).__name__)
    return False


def _cap(value):
    """(value, typename) so int vs float is discriminated (5 == 5.0 in Python)."""
    got = target.parse_cap(value)
    return (got, type(got).__name__)


CASES = [
    # degenerate inputs: no cap requested -> None, and they must NOT raise
    ("None means no cap", lambda: target.parse_cap(None), None),
    ("empty string means no cap", lambda: target.parse_cap(""), None),
    ("whitespace-only string means no cap", lambda: target.parse_cap("   "), None),

    # whole numbers come back as int, not float (5 == 5.0 would hide this)
    ("whole number '5' -> int 5", lambda: _cap("5"), (5, "int")),
    ("zero is a valid cap -> int 0", lambda: target.parse_cap("0"), 0),

    # fractional values come back as float
    ("fractional '2.5' -> float 2.5", lambda: _cap("2.5"), (2.5, "float")),

    # invalid input must raise ValueError, not crash with something else
    ("non-numeric 'abc' raises ValueError", lambda: _raises_value_error(target.parse_cap, "abc"), True),

    # regression half: earlier slices' helpers in the same file keep working
    ("parse_csv still splits and strips", lambda: target.parse_csv(" a , b ,,c "), ["a", "b", "c"]),
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
