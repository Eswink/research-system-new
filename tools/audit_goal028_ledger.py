#!/usr/bin/env python3
"""GOAL-20260929-028 EC-04 CI 台账**逐提交**审计：批量推送的每一个提交都要有 run 行。

背景（GOAL-028 建档时用原始 REST API 复核的实测缺口）：GOAL-027 的台账把
`6e27a14 + edd4de8 + a603267 + 93fa7f7` 四个提交**合并成一行**，只记 `93fa7f7` 的 run，
并写「无 cancelled」；而实测 `a603267` 的 M0 `36685047472` 是 **cancelled**
（`6e27a14` / `edd4de8` 则 `total_count=0`）。「合并行」让前三个提交的结论**不可见**。

本工具把口径机械化（与 `tools/audit_goal026_ledger.py` 同一形态，但判的是**另一件事**：
那个工具判「单个 run 的 job 集合不空 / 齐 / 全绿」，本工具判「**每个提交都有行**」）：

- 输入是一份**结构化台账**（JSON），由收集脚本从 REST API 原始响应产出：
  `{ "commits": [ {sha, runs: [{run_id, name, status, conclusion, run_attempt, jobs}]} ] }`；
- **每一个提交**必须满足其一（否则 FAIL，并**点名 sha**）：
  ① 自带 run（`runs` 非空）且每个 run 的 `status=completed` / `conclusion` 非空；
  ② 或**显式覆盖声明** `covered_by`（40 位 sha）+ `coverage_note`（非空，写明「被谁的绿承担」）
     —— 即「其 run 被合并行覆盖 + 由谁承担绿」必须**写在结构化字段里**，不接受散文；
- `cancelled` **如实登记**：run 的 `conclusion == "cancelled"` ⇒ 该 run 必须带非空
  `cancellation_note`（否则 FAIL）——「记了 cancelled」与「解释了为什么」是两件事；
- **空集合 / 空字段 = 未取证**（判红，不是 OK）：`commits == []` ⇒ FAIL；提交的
  `runs` 为空**且**无覆盖声明 ⇒ FAIL；run 的 `run_id` / `name` / `conclusion` 任一为空 ⇒ FAIL；
- 判词行只有 `PASS` / `FAIL` 开头（可直接喂给 `tools/two_tree_recheck.py` 的纯度要求）。

用法：

    python tools/audit_goal028_ledger.py --ledger scratch/goal028-ledger.json
    python tools/audit_goal028_ledger.py --ledger <f> --expect-sha <40 位 sha>
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

#: 空集合的判词标记：出现即表示「没有证据」，不是「没有失败」。
EMPTY_SET_MARK = "未取证"
#: 覆盖声明：被同批 head 覆盖时，必须写明的两个结构化字段。
COVERAGE_FIELDS = ("covered_by", "coverage_note")
#: run 对象里**非空**才算取证的字段。
REQUIRED_RUN_FIELDS = ("run_id", "name", "conclusion")
#: 终态 run 的 `status`。
TERMINAL_STATUS = "completed"
#: 需要解释的结论（如实登记的代价：必须写为什么）。
NEEDS_NOTE = {"cancelled"}
FULL_SHA_LENGTH = 40


@dataclass(frozen=True, slots=True)
class Verdict:
    """一行判词：`PASS` / `FAIL` + 名字 + 说明。"""

    name: str
    ok: bool
    detail: str

    def line(self) -> str:
        head = "PASS" if self.ok else "FAIL"
        return f"{head} [{self.name}] {self.detail}"


def _shape_verdicts(commits: object) -> list[Verdict]:
    """输入形状与**空集合**（`commits == []` ⇒ 未取证）。"""
    if not isinstance(commits, list):
        return [Verdict("ledger-shape", False, f"commits must be a list, got {type(commits)}")]
    if not commits:
        return [Verdict("ledger-non-empty", False, f"台账里一个提交都没有：{EMPTY_SET_MARK}")]
    return [Verdict("ledger-non-empty", True, f"{len(commits)} 个提交在台账里")]


def _run_verdicts(sha: str, runs: object) -> list[Verdict]:
    """单个提交的 run 行：要么自带 run 且齐、终态、非空；要么显式覆盖声明。"""
    if not isinstance(runs, list):
        return [
            Verdict(f"commit-runs[{sha[:12]}]", False, f"runs must be a list, got {type(runs)}")
        ]
    out: list[Verdict] = []
    for index, run in enumerate(runs):
        if not isinstance(run, dict):
            out.append(Verdict(f"run[{sha[:12]}#{index}]", False, f"run 不是对象：{run!r}"))
            continue
        name = f"run[{sha[:12]}#{run.get('run_id') or index}]"
        missing = [field for field in REQUIRED_RUN_FIELDS if not run.get(field)]
        if missing:
            out.append(Verdict(name, False, f"字段为空（{', '.join(missing)}）：{EMPTY_SET_MARK}"))
            continue
        if run.get("status") != TERMINAL_STATUS:
            out.append(Verdict(name, False, f"未到终态：status={run.get('status')!r}"))
            continue
        conclusion = str(run.get("conclusion"))
        if conclusion in NEEDS_NOTE and not str(run.get("cancellation_note") or "").strip():
            out.append(Verdict(name, False, f"{conclusion} 未登记原因（cancellation_note 为空）"))
            continue
        if run.get("run_attempt") in (None, ""):
            out.append(Verdict(name, False, f"run_attempt 为空：{EMPTY_SET_MARK}"))
            continue
        out.append(
            Verdict(name, True, f"{run.get('name')} = {conclusion}（attempt={run['run_attempt']}）")
        )
    return out


def _coverage_verdict(sha: str, entry: dict[str, object]) -> Verdict:
    """无自带 run 时的替代路径：**结构化**覆盖声明（40 位 sha + 非空说明）。"""
    name = f"commit[{sha[:12]}]"
    missing = [field for field in COVERAGE_FIELDS if not entry.get(field)]
    covered_by = str(entry.get("covered_by") or "")
    if missing:
        return Verdict(
            name,
            False,
            f"无自带 run 且覆盖声明不全（缺 {', '.join(missing)}）：{EMPTY_SET_MARK}",
        )
    if len(covered_by) != FULL_SHA_LENGTH or not all(c in "0123456789abcdef" for c in covered_by):
        return Verdict(name, False, f"covered_by 不是 40 位小写 hex：{covered_by!r}")
    return Verdict(name, True, f"由其覆盖声明的 {covered_by[:12]} 承担绿")


def audit(ledger: object, expect_sha: str | None = None) -> list[Verdict]:
    """对结构化台账产出逐条判词（纯函数；输入形状错即判红，不抛）。"""
    if not isinstance(ledger, dict):
        return [Verdict("ledger-shape", False, f"台账不是对象：{type(ledger)}")]
    commits = ledger.get("commits")
    verdicts = _shape_verdicts(commits)
    if not verdicts[-1].ok:
        return verdicts
    assert isinstance(commits, list)
    covered: set[str] = set()
    for entry in commits:
        if not isinstance(entry, dict):
            verdicts.append(Verdict("commit-shape", False, f"提交条目不是对象：{entry!r}"))
            continue
        sha = str(entry.get("sha") or "")
        if len(sha) != FULL_SHA_LENGTH:
            verdicts.append(
                Verdict("commit-sha", False, f"sha 不是 40 位：{sha!r}（{EMPTY_SET_MARK}）")
            )
            continue
        runs = entry.get("runs") or []
        if isinstance(runs, list) and runs:
            verdicts.extend(_run_verdicts(sha, runs))
            continue
        coverage = _coverage_verdict(sha, entry)
        verdicts.append(coverage)
        if coverage.ok:
            covered.add(sha)
    verdicts.append(_expect_sha_verdict(covered, expect_sha))
    return verdicts


def _expect_sha_verdict(covered: set[str], expect_sha: str | None) -> Verdict:
    if expect_sha is None:
        return Verdict("expected-sha", True, "未指定 --expect-sha（跳过）")
    if expect_sha in covered:
        return Verdict("expected-sha", False, f"{expect_sha[:12]} 没有自带 run（只有覆盖声明）")
    return Verdict("expected-sha", True, f"{expect_sha[:12]} 自带 run")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GOAL-028 CI 台账逐提交审计")
    parser.add_argument("--ledger", required=True, help="结构化台账 JSON 路径")
    parser.add_argument("--expect-sha", default=None, help="可选：要求该 sha 自带 run")
    args = parser.parse_args(argv)
    path = Path(args.ledger)
    if not path.is_file():
        print(f"FAIL [ledger-file] 台账文件不存在：{path}（{EMPTY_SET_MARK}）")
        return 1
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL [ledger-parse] 台账无法解析：{exc}（{EMPTY_SET_MARK}）")
        return 1
    verdicts = audit(ledger, args.expect_sha)
    for verdict in verdicts:
        print(verdict.line())
    failed = [verdict for verdict in verdicts if not verdict.ok]
    print(f"SUMMARY checks={len(verdicts)} failed={len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
