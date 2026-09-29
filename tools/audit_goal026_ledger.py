#!/usr/bin/env python3
"""GOAL-20260929-026 CI 台账审计（EC-05）：**空集合 = 未取证**（判红），不是 OK。

背景（GOAL-026 建档时的实测）：上一轮的台账脚本 `scratch/audit_goal025_ledger.sh`
对**空** `jobs` 列表**无条件打 `OK`** —— 空集被读成「没有失败」。本工具把这条口径倒过来：

- `jobs == []` ⇒ **FAIL**，理由里必须出现 `未取证`（**不是** OK）；
- `jobs` 条数低于该作业名的**下界** ⇒ FAIL（M0 八 job / CodeQL 三 job）；
- 任一 job 的 `conclusion != success` ⇒ FAIL（**点名** job）；
- run 对象的 `name` / `status` / `conclusion` / `run_attempt` / `head_sha` **任一为空** ⇒ FAIL；
- 一个 run 文件都没找到 ⇒ FAIL（空输入 = 未取证）。

判词行只有 `PASS` / `FAIL` 开头（可直接喂给 `tools/two_tree_recheck.py` 的「判词纯度」要求）。

**输入不在树内**：Go 的台账原始 JSON 落在 `scratch/`（gitignored）。所以本工具**不进**两树复检的
判词面；它由收口验证器以**合成输入**做行为判据（空集 ⇒ 判红、良集 ⇒ 判绿），
真实台账则由收口复检在本机跑一次、留档到 `scratch/`。

用法：

    python tools/audit_goal026_ledger.py --runs-dir scratch
    python tools/audit_goal026_ledger.py --runs-dir scratch --expect-sha <40 位 sha>
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

#: 每个 workflow 名的 **job 条数下界**（低于它 ⇒ 未取证）。键是 GitHub 上的 workflow 名。
MIN_JOBS: dict[str, int] = {"M0 Quality Gates": 8, "Push on main": 3}

#: 空集合的判词标记：出现即表示「没有证据」，不是「没有失败」。
EMPTY_SET_MARK = "未取证"

#: run 对象里**非空**才算取证的字段。
REQUIRED_RUN_FIELDS: tuple[str, ...] = ("name", "status", "conclusion", "run_attempt", "head_sha")

SUCCESS = "success"


@dataclass(frozen=True, slots=True)
class Verdict:
    """一行判词：`PASS` / `FAIL` + 名字 + 说明。"""

    name: str
    ok: bool
    detail: str = ""

    def line(self) -> str:
        status = "PASS" if self.ok else "FAIL"
        suffix = f" -> {self.detail}" if self.detail else ""
        return f"{status} {self.name}{suffix}"


def load_json(path: Path) -> object | None:
    if not path.is_file():
        return None
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload


def missing_fields(run: object) -> list[str]:
    if not isinstance(run, dict):
        return list(REQUIRED_RUN_FIELDS)
    return [field for field in REQUIRED_RUN_FIELDS if run.get(field) in (None, "")]


def job_list(payload: object) -> list[object] | None:
    """jobs 列表：接受 **API 原样响应**（`{"total_count": n, "jobs": [...]}`）与裸列表两种形态。

    两种都接受是**实测**需要：`/actions/runs/<id>/jobs` 的响应是前者，本机的合成输入用后者。
    既不是列表也不是带 `jobs` 的字典 ⇒ `None`（由调用方判**未取证**，不是判 OK）。
    """
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        inner = payload.get("jobs")
        if isinstance(inner, list):
            return inner
    return None


def failed_jobs(jobs: list[object]) -> list[str]:
    return [
        str(job.get("name"))
        for job in jobs
        if isinstance(job, dict) and job.get("conclusion") != SUCCESS
    ]


def run_problem(run: dict[str, object], expect_sha: str | None) -> str | None:
    """run 对象自身的取证问题（`None` = 无问题）。"""
    absent = missing_fields(run)
    if absent:
        return f"run 字段为空 ⇒ {EMPTY_SET_MARK}：{absent}"
    if run.get("status") != "completed":
        return f"run 未到终态：status={run.get('status')!r}"
    if run.get("conclusion") != SUCCESS:
        return f"run 结论非成功：conclusion={run.get('conclusion')!r}"
    if expect_sha is not None and run.get("head_sha") != expect_sha:
        return f"sha 不符：{run.get('head_sha')!r} != {expect_sha}"
    return None


def jobs_problem(run: dict[str, object], jobs: list[object]) -> str | None:
    """job 集合的取证问题（`None` = 无问题）；**空集 = 未取证**，不是「没有失败」。"""
    if not jobs:
        return f"jobs 为空 ⇒ {EMPTY_SET_MARK}（空集不是「没有失败」）"
    name = str(run.get("name"))
    floor = MIN_JOBS.get(name)
    if floor is None:
        return f"未登记 job 下界的 workflow：{name!r}"
    if len(jobs) < floor:
        return f"job 条数 {len(jobs)} < 下界 {floor} ⇒ {EMPTY_SET_MARK}"
    bad = failed_jobs(jobs)
    return f"这些 job 未成功：{bad}" if bad else None


def audit_pair(run_path: Path, jobs_path: Path, expect_sha: str | None) -> Verdict:
    """审一对 (run 对象, jobs 响应) —— 任一环不成立即判红，理由带原因。"""
    label = run_path.stem
    run = load_json(run_path)
    jobs = job_list(load_json(jobs_path))
    if run is None:
        return Verdict(label, False, f"run 对象缺失或不可解析：{run_path.name}")
    if jobs is None:
        return Verdict(label, False, f"jobs 无法解析成列表 ⇒ {EMPTY_SET_MARK}：{jobs_path.name}")

    assert isinstance(run, dict)  # 上面的 `None` 分支已把非字典形态挡掉
    problem = run_problem(run, expect_sha) or jobs_problem(run, jobs)
    if problem is not None:
        return Verdict(label, False, problem)
    detail = f"name={run.get('name')} jobs={len(jobs)} attempt={run.get('run_attempt')}"
    return Verdict(label, True, detail)


def pairs_in(runs_dir: Path, prefix: str) -> list[tuple[Path, Path]]:
    """`<prefix>*-jobs.json` 与其对应 run 对象（去掉 `-jobs` 后缀）成对返回。

    `scratch/` 里还躺着**别的 GOAL** 的台账文件（`goal015-*` / `goal4-*` / `tmp-*` …）：
    受判面因此必须由 `--prefix` **显式**收窄到本 GOAL，而不是「扫整个目录」
    （否则别的 GOAL 的缺证据会把本轮判红，反之也会把本轮的空缺掩盖在噪声里）。
    """
    pairs: list[tuple[Path, Path]] = []
    for jobs_path in sorted(runs_dir.glob(f"{prefix}*-jobs.json")):
        run_path = jobs_path.with_name(jobs_path.name.replace("-jobs.json", ".json"))
        pairs.append((run_path, jobs_path))
    return pairs


def audit_all(runs_dir: Path, expect_sha: str | None, prefix: str) -> list[Verdict]:
    pairs = pairs_in(runs_dir, prefix)
    if not pairs:
        return [
            Verdict(
                "ledger-input",
                False,
                f"{runs_dir} 下没有任何 {prefix}*-jobs.json ⇒ {EMPTY_SET_MARK}",
            )
        ]
    return [audit_pair(run_path, jobs_path, expect_sha) for run_path, jobs_path in pairs]


def emit(verdicts: Iterable[Verdict]) -> bool:
    collected = list(verdicts)
    for verdict in collected:
        print(verdict.line(), flush=True)
    failed = [verdict for verdict in collected if not verdict.ok]
    head = "PASS" if not failed else "FAIL"
    print(f"{head} ledger-audit runs={len(collected)} failed={len(failed)}", flush=True)
    return not failed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL-026 CI 台账审计（空集 = 未取证）")
    parser.add_argument("--runs-dir", required=True, help="存放 run / jobs JSON 的目录")
    parser.add_argument("--expect-sha", default=None, help="只接受该 head_sha 的 run")
    parser.add_argument(
        "--prefix", default="goal026-", help="只审该前缀的 run（默认本 GOAL 的前缀）"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runs_dir = Path(args.runs_dir)
    if not runs_dir.is_dir():
        print(f"FAIL ledger-input -> 目录不存在：{runs_dir}")
        return 2
    return 0 if emit(audit_all(runs_dir, args.expect_sha, args.prefix)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
