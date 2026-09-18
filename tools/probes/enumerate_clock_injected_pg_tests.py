"""Enumerate the clock-injected PostgreSQL test files and print their clock facts.

GOAL-005 cycle 4 = EC-04 needs a *script* as the enumeration basis ("不靠记忆"):
which files under `tests/postgres/` inject a deterministic clock, and what each
of them does that could make an assertion wall-clock dependent.

For every file that injects a clock this probe prints, from the source text:

- `clock_injection`: the lines that inject a clock (engine/store constructor
  `now=` kwargs, `class _Clock` definitions, `# noqa`-tagged clock lambdas) —
  the "fixture really injects" evidence;
- `wall_clock`: lines reading the wall clock (`datetime.now`, `utcnow`,
  `time.time`, `Timestamp.now`, `perf_counter`, `monotonic`, `sleep`,
  `CURRENT_TIMESTAMP`) — must be empty for an "injected clock" file to be
  judged safe on the read side;
- `clockless_engines`: constructor calls that do NOT pass `now=`, i.e. code
  paths that fall back to the PostgreSQL clock — each of those needs its own
  adjudication (the assertions in that test must not depend on time);
- `time_assertions`: assertion lines mentioning a time-derived column so a
  reviewer can trace the expected value back to its clock source.

Read-only: nothing is written, nothing is executed from the repo, no network.
Usage:

    uv run --frozen --no-sync python -B tools/probes/enumerate_clock_injected_pg_tests.py [--root .]
"""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path

WALL_CLOCK_PATTERNS = (
    "datetime.now(",
    "datetime.utcnow(",
    "time.time(",
    "Timestamp.now(",
    "perf_counter(",
    "monotonic(",
    "sleep(",
    "CURRENT_TIMESTAMP",
)

CLOCK_INJECTION_PATTERNS = (
    "now=",
    "class _Clock",
    "class Clock",
    "def now(",
    "clock[",
)

TIME_ASSERTION_PATTERN = re.compile(
    r"(expires_at|claimed_at|retry_at|not_before|next_retry_at|heartbeat_at|retry_schedule)"
)

ENGINE_CONSTRUCTORS = (
    "PostgresWorkflowEngine(",
    "SqliteWorkflowEngine(",
    "PostgresExperimentStore(",
    "PostgresWorkerRegistry(",
)


def _lines_with(text: str, patterns: tuple[str, ...]) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if any(pattern in line for pattern in patterns):
            hits.append((number, line.strip()))
    return hits


def _constructor_calls(text: str) -> list[tuple[int, str]]:
    """Constructor calls (possibly multi-line) with their full source text."""
    hits: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name is None:
                continue
            spelled = f"{name}("
            if spelled in ENGINE_CONSTRUCTORS:
                segment = ast.get_source_segment(text, node) or spelled
                hits.append((node.lineno, " ".join(segment.split())))
    return sorted(hits)


def report_file(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    clock_injection = _lines_with(text, CLOCK_INJECTION_PATTERNS)
    wall_clock = _lines_with(text, WALL_CLOCK_PATTERNS)
    constructors = _constructor_calls(text)
    clockless = [(n, s) for n, s in constructors if "now=" not in s]
    time_assertions = [
        (n, line.strip())
        for n, line in enumerate(text.splitlines(), start=1)
        if line.strip().startswith("assert") and TIME_ASSERTION_PATTERN.search(line)
    ]
    return {
        "path": path.as_posix(),
        "injects_clock": bool(clock_injection),
        "clock_injection": clock_injection,
        "wall_clock": wall_clock,
        "constructors": constructors,
        "clockless_engines": clockless,
        "time_assertions": time_assertions,
    }


def render(entry: dict[str, object]) -> str:
    path = entry["path"]
    out = [f"=== {path}"]
    out.append(f"    injects_clock: {entry['injects_clock']}")
    for label, key in (
        ("clock_injection", "clock_injection"),
        ("wall_clock", "wall_clock"),
        ("clockless_engines", "clockless_engines"),
        ("time_assertions", "time_assertions"),
    ):
        rows = entry[key]
        assert isinstance(rows, list)
        out.append(f"    {label}: {len(rows)}")
        out.extend(f"        L{n}: {text}" for n, text in rows)  # type: ignore[misc]
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root (default: cwd)")
    args = parser.parse_args()
    target = Path(args.root) / "tests" / "postgres"
    files = sorted(target.glob("*.py"))
    entries = [report_file(path) for path in files]
    injected = [entry for entry in entries if entry["injects_clock"]]
    for entry in injected:
        print(render(entry))
    print()
    print(f"postgres test files: {len(files)}")
    print(f"clock-injected files: {len(injected)}")
    dirty = [
        entry["path"] for entry in injected if entry["wall_clock"] or entry["clockless_engines"]
    ]
    print(f"files with wall-clock reads: {sum(1 for e in injected if e['wall_clock'])}")
    print(f"files with clockless constructors (need per-test adjudication): {len(dirty)}")
    for path in dirty:
        print(f"    - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
