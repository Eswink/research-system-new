"""把一份本地门日志里的红项**机械**归入三类（GOAL-015 EC-02）。

三类与判定条件见 `docs/architecture/LOCAL_GATE_PROTOCOL.md` 第 2 节：
(i) 真实缺陷 ⇒ 修代码；(ii) 环境专属 ⇒ 登记 + 归因命令，**不改判据**；
(iii) 门禁 scoping ⇒ 只登记（进决策简报），**不改门禁**。

分类口径：**只看 FAILED 的检查项**（不匹配 `RUN` 行——通过的检查也会有 RUN 行），
再对其内部已知的失败签名做**子归因**。落到表外的红打印 `UNCLASSIFIED`——**不允许**读成
「已忽略」，必须按协议第 2 节当场分类并补进 `LOCAL_GATE_PROTOCOL.md` 第 3 节的分类表。

本工具只做分类与点名：读日志、打印类别与**可复跑的归因命令**；不跑门、不改文件、零出网。

用法：
  python -B tools/classify_local_gate_reds.py --log scratch/goal015-c1-m0-final.log
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

#: 失败检查项 → (类别, 归因命令, 终态)。键是 `FAILED [<name>]` 里的 name。
BY_CHECK: dict[str, tuple[str, str, str]] = {
    "python/tests": (
        "(i) 真实缺陷 —— 但先看子签名（见下）",
        "pytest --ignore=tests/architecture/python/test_dependency_boundaries.py -q",
        "按子签名逐条处置；挂死/超时类走 postgres 守卫判据",
    ),
    "python/typecheck": ("(i) 真实缺陷", "python -m mypy", "改类型，不改配置"),
    "python/product-lint": ("(i) 真实缺陷", "python -m ruff check <roots>", "改代码"),
    "python/format-check": ("(i) 真实缺陷", "python -m ruff format --check", "跑 ruff format"),
    "python/dependency-boundaries": (
        "(i) 真实缺陷",
        "pytest tests/architecture/python/test_dependency_boundaries.py -q",
        "改 import 方向",
    ),
    "framework/validate": (
        "(i) 真实缺陷（记录面）",
        "python .cursor/skills/governance-check/scripts/validate.py",
        "补齐 PLAN / RECHECK / MEM / ALL_PLAN / INDEX（记录未写完即是真红）",
    ),
    "framework/validate_bundle": (
        "(iii) 门禁 scoping",
        "python -B .cursor/skills/system-spec-check/scripts/validate_bundle.py",
        "只登记：进 EC-03 决策简报（不改门禁、不动仓库外在制品）",
    ),
    "framework/docs_consistency_check": (
        "(i) 真实缺陷（文档面）",
        "python -B tools/docs_consistency_check.py",
        "修文档（backtick 引用 / 索引），不改检查项",
    ),
}

#: `python/tests` 内部的已知失败签名 → (类别, 归因命令, 终态)。
#: 一条 check 可以有**多个独立**子签名（本 GOAL 实测：同一轮 `python/tests` 由两类叠加而成）。
SUB_SIGNATURES: tuple[tuple[str, str, str, str], ...] = (
    (
        r"test_list_orders_by_recency_and_filters_project",
        "(i) 真实缺陷（全序语义）",
        "pytest tests/contracts/test_protocol_draft_store_order_tie.py -q",
        "已修：三实现 tie-break 与新近一致（修前 3 failed）",
    ),
    (
        r"egress guard: FAIL",
        "(i) 真实缺陷（测试隔离）",
        "LLM_MAIN_KEY=<任意值> pytest tests/api/test_runs_api.py -q",
        "已修：默认门凭据隔离（修前 blocked 2 / 修后 blocked 0）",
    ),
    (
        r"挂死|TimeoutExpired|\bhang\b",
        "(i) 真实缺陷（跳过守卫依赖收集面）",
        "pytest tests/architecture/python/test_postgres_skip_is_load_independent.py -q",
        "已修：postgres 守卫提为加载无关（含 fail-closed 方向）",
    ),
)

_FAILED_CHECK = re.compile(r"^FAILED \[(?P<name>[^\]]+)\]", re.M)
_SUMMARY = re.compile(r"^FAILED: .*$", re.M)
_GREEN = re.compile(r"^PASS: profile=m0; 23 deterministic checks$", re.M)


def _report_check(name: str, text: str, unexplained: list[str]) -> None:
    known = BY_CHECK.get(name)
    if known is None:
        unexplained.append(name)
        return
    klass, command, terminal = known
    print(f"- `{name}` ⇒ {klass}")
    print(f"    归因命令：{command}")
    print(f"    终态：{terminal}")
    if name != "python/tests":
        return
    for token, sub_klass, sub_command, sub_terminal in SUB_SIGNATURES:
        if re.search(token, text):
            print(f"    子签名 `{token}` ⇒ {sub_klass}")
            print(f"        归因命令：{sub_command}")
            print(f"        终态：{sub_terminal}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify local gate reds into the three classes.")
    parser.add_argument("--log", required=True, help="run_all_checks / pytest 的日志路径")
    args = parser.parse_args(argv)

    path = Path(args.log)
    if not path.is_file():
        print(f"日志不存在：{path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8", errors="replace")

    failed = _FAILED_CHECK.findall(text)
    summary = _SUMMARY.search(text)
    print(f"日志：{path}")
    print(f"FAILED 检查项：{failed or '<none>'}")
    print(f"汇总行：{summary.group(0) if summary else '<none>'}")
    if _GREEN.search(text):
        print("终态：命中全绿行 `PASS: profile=m0; 23 deterministic checks`")
        return 0
    if not failed:
        print("终态：无 FAILED 检查项，但也没有全绿行——请核对是否用了 --keep-going、门是否跑完")
        return 1

    unexplained: list[str] = []
    print("\n分类（只按 FAILED 检查项；先命中者胜）：")
    for name in failed:
        _report_check(name, text, unexplained)

    if unexplained:
        print("\nUNCLASSIFIED（按协议第 2 节三条判定条件当场分类，并补进第 3 节分类表）：")
        for name in unexplained:
            print(f"- {name}")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
