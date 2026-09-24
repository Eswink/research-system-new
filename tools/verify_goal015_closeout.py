"""GOAL-015 EC-04 的独立复检脚本：**只读、标准库、不 import 仓库代码、零出网**。

判据（两棵树同判据同结论）：
1. **产物在册**：四个 EC 的交付物逐个存在（普查表 / 跑法协议 / 归因脚本 / 代管脚本 /
   决策简报 + 四条判据 + 共享守卫）。
2. **判据面逐字节未改**：`tests/egress_guard.py`、`tests/application/test_m2_audit.py`、
   `tests/tooling/test_python_source_limits.py`（规模门禁）、
   `.cursor/skills/system-spec-check/scripts/validate_bundle.py`（检查项）、
   `.cursor/skills/governance-check/scripts/validate.py` —— 全部与 GOAL-015 起点前的基线
   （`BASE = 414f2e5`）**逐字节相同**（`git diff --quiet BASE HEAD -- <path>`）。
3. **没有用 skip/xfail 掩盖**：四条新判据里不得出现 `mark.skip` / `xfail`；共享守卫
   `tests/postgres_guard.py` 按设计会加 skip，因此改判它是否具备 **fail-closed** 出口。
4. **GOAL 记录自洽**：EC-01…EC-03 = `PASS`；EC-04 ∈ {`PASS`, `PENDING`}（`PENDING` 作为
   **时序项**打印：收口记录落盘后再跑应为 `PASS`）；`latest_recheck` 是**仓库相对路径**且存在；
   `child_plans` / `memory_entries` 逐个存在；13 条人工面编号齐全。
5. **决策简报齐备**：条目 ≥ 9、每条六要素非空、对齐表覆盖 13 条编号项（独立实现，不 import
   仓库判据）。
6. **CI 台账**：每行带 run 链接（「台账尾巴」行除外），行数 ≥ 5。

用法：
  uv run --frozen --no-sync python -B tools/verify_goal015_closeout.py            # 主树
  uv run --frozen --no-sync python -B tools/verify_goal015_closeout.py --root <干净 worktree>
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

BASE = "414f2e5"
ELEMENTS = ("要决定什么", "选项", "影响与代价", "证据出处", "不做会怎样", "建议")

ARTIFACTS = (
    "docs/evaluation/CROSS_SUITE_ISOLATION_AUDIT.md",
    "docs/architecture/LOCAL_GATE_PROTOCOL.md",
    "docs/roadmap/OPEN_DECISIONS_BRIEFING.md",
    "tools/classify_local_gate_reds.py",
    "tools/quarantine_and_run_m0.py",
    "tools/verify_goal015_closeout.py",
    "tests/postgres_guard.py",
    "tests/architecture/python/test_default_gate_credential_isolation.py",
    "tests/architecture/python/test_default_gate_isolation_probe.py",
    "tests/architecture/python/test_postgres_skip_is_load_independent.py",
    "tests/tooling/test_pending_decisions_briefing.py",
)

FROZEN = (
    "tests/egress_guard.py",
    "tests/application/test_m2_audit.py",
    "tests/tooling/test_python_source_limits.py",
    ".cursor/skills/system-spec-check/scripts/validate_bundle.py",
    ".cursor/skills/governance-check/scripts/validate.py",
)

JUDGES = (
    "tests/architecture/python/test_default_gate_credential_isolation.py",
    "tests/architecture/python/test_default_gate_isolation_probe.py",
    "tests/architecture/python/test_postgres_skip_is_load_independent.py",
    "tests/tooling/test_pending_decisions_briefing.py",
)

GOAL = ".cursor/plans/goals/GOAL-20260925-015-gate-trustworthiness.md"


class Report:
    def __init__(self) -> None:
        self.checked = 0
        self.failures: list[str] = []
        self.timing: list[str] = []

    def check(self, ok: bool, label: str) -> None:
        self.checked += 1
        if not ok:
            self.failures.append(label)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)


def check_frozen(root: Path, report: Report) -> None:
    for path in FROZEN:
        completed = _git(root, "diff", "--quiet", BASE, "HEAD", "--", path)
        report.check(completed.returncode == 0, f"判据面被改动: {path}")


def check_artifacts(root: Path, report: Report) -> None:
    for path in ARTIFACTS:
        report.check((root / path).is_file(), f"交付物缺失: {path}")


def check_no_masking(root: Path, report: Report) -> None:
    for path in JUDGES:
        text = (root / path).read_text(encoding="utf-8", errors="replace")
        report.check("mark.skip" not in text, f"判据里出现 skip: {path}")
        report.check("xfail" not in text, f"判据里出现 xfail: {path}")
    # 共享守卫**按设计**会加 skip（PG 不可达）；这里判的是它同时具备 **fail-closed** 出口，
    # 否则「跳过」与「通过」在判词上就分不开。
    guard = (root / "tests/postgres_guard.py").read_text(encoding="utf-8", errors="replace")
    report.check("RESEARCHOS_REQUIRE_POSTGRES" in guard, "守卫缺 fail-closed 开关")
    report.check("pytest.exit" in guard, "守卫缺 fail-closed 出口（pytest.exit）")


def check_goal_record(root: Path, report: Report) -> None:
    text = (root / GOAL).read_text(encoding="utf-8")
    for ec in ("EC-01", "EC-02", "EC-03"):
        marker = f"| {ec} |"
        line = next((row for row in text.splitlines() if row.startswith(marker)), "")
        report.check(line.endswith("| **PASS** |"), f"{ec} 状态不是 PASS: {line[-24:]}")
    ec04 = next((row for row in text.splitlines() if row.startswith("| EC-04 |")), "")
    if ec04.endswith("| PENDING |"):
        report.timing.append("EC-04 仍为 PENDING（收口记录尚未落盘）")
    else:
        report.check(ec04.endswith("| **PASS** |"), f"EC-04 既非 PENDING 也非 PASS: {ec04[-24:]}")
    for name in ("latest_recheck", "child_plans", "memory_entries"):
        report.check(name in text, f"GOAL frontmatter 缺 {name}")
    report.check("latest_recheck: .cursor/" in text, "latest_recheck 不是仓库相对路径")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- .cursor/") or stripped.startswith("latest_recheck: .cursor/"):
            target = stripped.removeprefix("latest_recheck:").strip().removeprefix("- ").strip()
            report.check((root / target).is_file(), f"引用不存在: {target}")
    missing = [f"{n}." for n in range(1, 14) if f"\n{n}. **" not in text]
    report.check(not missing, f"GOAL 人工面编号缺失: {missing}")


def _briefing_items(text: str) -> dict[str, str]:
    items: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []
    for line in text.splitlines():
        if line.startswith("## D-") and "｜" in line:
            if current is not None:
                items[current] = "\n".join(buffer)
            current = line.split(" ", 1)[1].split("｜", 1)[0]
            buffer = []
        elif current is not None:
            buffer.append(line)
    if current is not None:
        items[current] = "\n".join(buffer)
    return items


def check_briefing(root: Path, report: Report) -> None:
    path = root / "docs/roadmap/OPEN_DECISIONS_BRIEFING.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    items = _briefing_items(text)
    report.check(len(items) >= 9, f"简报条目不足 9 条（{len(items)}）")
    for item_id, body in items.items():
        for element in ELEMENTS:
            marker = f"- **{element}**："
            row = next((line for line in body.splitlines() if line.startswith(marker)), "")
            report.check(len(row) - len(marker) >= 8, f"{item_id} 的「{element}」缺或空壳")
    rows = [
        line
        for line in text.splitlines()
        if line.startswith("| ") and line.count("|") == 5 and not line.startswith("| ---")
    ]
    numbered = {row.split("|")[1].strip() for row in rows}
    report.check(
        all(str(n) in numbered for n in range(1, 14)), f"对齐表未覆盖 1..13：{sorted(numbered)}"
    )
    report.check("live 判据的开门条件" in text, "简报未覆盖 live 判据开门条件")


def check_ledger(root: Path, report: Report) -> None:
    text = (root / GOAL).read_text(encoding="utf-8")
    ledger = text.split("### CI 台账", 1)[-1].split("## 状态历史", 1)[0]
    rows = [line for line in ledger.splitlines() if line.startswith("| ")]
    report.check(len(rows) >= 5, "CI 台账行数异常")
    for row in rows[2:]:
        if "台账尾巴" in row or row.startswith("| 时间"):
            continue
        report.check("actions/runs/" in row, f"台账行缺 run 链接: {row[:60]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GOAL-015 EC-04 independent recheck")
    parser.add_argument("--root", default="", help="默认主树；可指向干净 worktree")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    report = Report()
    for check in (
        check_artifacts,
        check_frozen,
        check_no_masking,
        check_goal_record,
        check_briefing,
        check_ledger,
    ):
        check(root, report)

    print(f"root={root}")
    print(f"checked={report.checked} failures={len(report.failures)}")
    for note in report.timing:
        print(f"TIMING: {note}")
    for failure in report.failures:
        print(f"FAIL: {failure}")
    return 1 if report.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
