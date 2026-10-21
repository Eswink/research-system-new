#!/usr/bin/env python3
"""下一轮 charter 骨架的**确定性读取器**（GOAL-20261021-092 EC-01…EC-04）。

**它补哪一格**：「上一轮的输出 → 下一轮的 charter」此前**靠人**：驱动方读完 GOAL 报告，
把「残余与未覆盖范围」抄进下一轮提示词，再翻宪章阶梯的「下一级是什么」。这一步漏一条
残余就丢了，而**没有任何东西**会发现少一条 —— 散文没有失效机制，人的注意力有。

本读取器把它变成机器：输入是**已收口**的一个 GOAL + 它的 RECHECK + 宪章，输出是下一个
GOAL 的 charter 骨架，含三块**可提取**的事实：

1. 「残余与未覆盖范围」的 `W-NN` 列表 —— **逐条原文，不摘要**；
2. 宪章阶梯里**收录本 GOAL** 的那些域的「下一级是什么」（原文）；
3. 「CI 台账」的结论（全绿 / 有判红 / 未能判定）与逐类行数。

**确定性**：零出网、零模型、零时钟、零环境依赖。所有输入都在命令行上显式给出（含
`--next-goal-id`：下一个编号是**判断**，不是提取 ⇒ 不从文件名猜、不看时钟）。同输入 ⇒
逐字节相同（落盘用二进制写，LF 不受平台影响）。

**失败即点名，不生成半成品**：GOAL 非终态 / 缺 RECHECK / RECHECK 不存在 / 不属于本 GOAL /
结果不是通过取值 / 阶梯未收录 / `W` 编号不连续 / 缺残余节 / 缺 CI 台账 ⇒ 打印
`REFUSED <code> <detail>` 并返回 2，**不写** `--out`（写了一半的骨架比不写更有害：它会被当成
完整输入）。

**它不做什么（如实登记）**：

- 它**不**判断下一轮该做什么 —— objective / exit_criteria 是判断，产出的末节把它们显式留空
  （`<待填：判断>`），而不是猜一个值；
- 它**不**校验 RECHECK 正文的结论对不对，只读 frontmatter 的 `result`；
- CI 台账的「全绿」是**按行分类**的机械读数，不是对 CI 本身的独立取证 —— 台账写错，这里
  就跟着错。

用法::

    uv run --frozen --no-sync python -B tools/next_round_charter.py \\
        --root . \\
        --goal .cursor/plans/goals/GOAL-20261020-091-two-models-judge-the-same-artifact.md \\
        --next-goal-id GOAL-20261021-092 \\
        --out .cursor/plans/goals/evidence/GOAL-20261021-092-next-round-charter.md
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

#: 树内固定落点（相对 `--root`）。
CHARTER = ".cursor/plans/goals/MAINLINE.md"
REQUIRED_RECHECK_FIELD = "latest_recheck"

_GOAL_ID = re.compile(r"^GOAL-\d{8}-\d{3}$")

EXIT_OK = 0
EXIT_REFUSED = 2


def _load_parser() -> ModuleType:
    """按**路径**加载同目录的解析原语（`tools/` 不是包 ⇒ 静态 import 会让 mypy 报
    「Source file found twice」；且**必须先写 `sys.modules` 再 `exec_module`**）。"""
    path = Path(__file__).resolve().parent / "charter_parse.py"
    spec = importlib.util.spec_from_file_location("charter_parse", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["charter_parse"] = module
    spec.loader.exec_module(module)
    return module


PARSE = _load_parser()
#: 重新导出（判据与调用方按名字取用；单一来源仍是 `charter_parse.py`）。
Refusal: Any = PARSE.Refusal
CiSummary: Any = PARSE.CiSummary
LadderMatch: Any = PARSE.LadderMatch
Residual: Any = PARSE.Residual


@dataclass(frozen=True, slots=True)
class Inputs:
    """一次读取的全部输入（内容 + 各自摘要）—— 产出的「输入」节就是它。"""

    goal: str
    recheck: str
    goal_text: str
    recheck_text: str
    charter_text: str
    goal_id: str
    next_id: str
    status: str
    result: str


def _require_terminal(metadata: dict[str, Any]) -> str:
    status = str(metadata.get("status") or "").strip()
    if status not in PARSE.TERMINAL:
        raise PARSE.Refusal(
            "GOAL_NOT_TERMINAL",
            f"GOAL 的 frontmatter `status` 是 {status or '（缺失）'!r}，"
            f"只有 {sorted(PARSE.TERMINAL)} 才允许生成下一轮骨架（未收口的一轮没有确定的残余面）",
        )
    return status


def _resolve_recheck(root: Path, metadata: dict[str, Any]) -> Path:
    """按 `latest_recheck` 定位并**逐条**校验它（缺失 / 不存在 / 不属于本 GOAL / 不通过）。"""
    raw = metadata.get(REQUIRED_RECHECK_FIELD)
    if not isinstance(raw, str) or "/" not in raw:
        raise PARSE.Refusal(
            "RECHECK_MISSING",
            f"frontmatter `{REQUIRED_RECHECK_FIELD}` 不是仓库相对路径（{raw!r}）",
        )
    target = root.joinpath(*raw.split("/"))
    if not target.is_file():
        raise PARSE.Refusal(
            "RECHECK_MISSING", f"`{REQUIRED_RECHECK_FIELD}` 指向的复检不存在：{raw}"
        )
    recheck = PARSE.frontmatter(target.read_text(encoding="utf-8", errors="replace"))
    goal_id = str(metadata.get("id") or "")
    parent = str(recheck.get("parent_goal") or "")
    if parent and parent != goal_id:
        raise PARSE.Refusal(
            "RECHECK_NOT_THIS_GOAL",
            f"复检 {raw} 的 `parent_goal` 是 {parent!r}，本 GOAL 是 {goal_id!r}",
        )
    result = str(recheck.get("result") or "")
    if result not in PARSE.PASSING:
        raise PARSE.Refusal(
            "RECHECK_NOT_PASSING",
            f"复检 {raw} 的 `result` 是 {result or '（缺失）'!r}，"
            f"只有 {sorted(PARSE.PASSING)} 允许进入下一轮",
        )
    return target


def _relative(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:  # pragma: no cover - 调用方保证在树内
        return path.as_posix()


def _read_inputs(root: Path, goal: str, next_id: str) -> tuple[Inputs, tuple[Any, ...], Any]:
    """读全部输入并**逐条**校验（任何一条不合格 ⇒ 抛 `Refusal`）。"""
    if not _GOAL_ID.match(next_id):
        raise PARSE.Refusal("NEXT_ID_INVALID", f"`--next-goal-id` 形态非法：{next_id!r}")
    relative = Path(goal)
    absolute = (
        relative if relative.is_absolute() else root.joinpath(*relative.as_posix().split("/"))
    )
    if not absolute.is_file():
        raise PARSE.Refusal("GOAL_MISSING", f"GOAL 不在树：{goal}")
    goal_text = absolute.read_text(encoding="utf-8", errors="replace")
    metadata = PARSE.frontmatter(goal_text)
    goal_id = str(metadata.get("id") or "")
    if not _GOAL_ID.match(goal_id):
        raise PARSE.Refusal("GOAL_UNREADABLE", f"GOAL frontmatter 的 `id` 非法：{goal_id!r}")
    status = _require_terminal(metadata)
    recheck = _resolve_recheck(root, metadata)
    recheck_text = recheck.read_text(encoding="utf-8", errors="replace")
    result = str(PARSE.frontmatter(recheck_text).get("result") or "")
    charter_path = root.joinpath(*CHARTER.split("/"))
    if not charter_path.is_file():
        raise PARSE.Refusal("LADDER_SECTION_MISSING", f"宪章不在树：{CHARTER}")
    charter_text = charter_path.read_text(encoding="utf-8", errors="replace")
    matches = PARSE.ladder_matches(charter_text, goal_id)
    inputs = Inputs(
        goal=relative.as_posix(),
        recheck=_relative(root, recheck),
        goal_text=goal_text,
        recheck_text=recheck_text,
        charter_text=charter_text,
        goal_id=goal_id,
        next_id=next_id,
        status=status,
        result=result,
    )
    return inputs, matches, PARSE.ci_summary(goal_text)


def _header_lines(inputs: Inputs) -> list[str]:
    digest = PARSE.sha256_text
    return [
        f"# 下一轮 charter 骨架（{inputs.goal_id} → {inputs.next_id}）",
        "",
        "> 本文件由 `tools/next_round_charter.py` **确定性**产出：零出网、零模型、零时钟。",
        "> 同输入 ⇒ 逐字节相同。**判断面**（objective / EC 的内容）不在这里 —— 见末节，",
        "> 那些位置显式留空（`<待填：判断>`），不由本工具猜。",
        "",
        "## 一、输入（内容寻址）",
        "",
        f"- 上一个 GOAL：`{inputs.goal}`（`status: {inputs.status}`）",
        f"- 上一个复检：`{inputs.recheck}`（`result: {inputs.result}`）",
        f"- 宪章：`{CHARTER}`",
        f"- 摘要：goal `sha256:{digest(inputs.goal_text)[:16]}`；"
        f"recheck `sha256:{digest(inputs.recheck_text)[:16]}`；"
        f"charter `sha256:{digest(inputs.charter_text)[:16]}`",
        "",
    ]


def _residual_lines(items: Sequence[Any]) -> list[str]:
    span = f"`W-{items[0].number}`…`W-{items[-1].number}`" if items else "（空）"
    return [
        "## 二、上一轮的残余与未覆盖范围（逐条原文，**不摘要**）",
        "",
        f"共 {len(items)} 条（{span}）。搬运时**不得删、不得改写**；每一条都要在下一轮里被处置",
        "（做掉 / 明确承接 / 登记为不做并给理由）—— 处置**不是**本工具的事。",
        "",
        *[item.raw for item in items],
        "",
    ]


def _ladder_lines(matches: Sequence[Any]) -> list[str]:
    escaped = chr(92) + "|"
    lines = [
        "## 三、阶梯：收录本 GOAL 的域，以及那些域的「下一级是什么」",
        "",
        "| 域 | 下一级是什么（原文） |",
        "| --- | --- |",
    ]
    for match in matches:
        lines.append(f"| {match.domain} | {match.next_level.replace('|', escaped)} |")
    lines.extend([
        "",
        f"- 收录本 GOAL 的域：{'、'.join(match.domain for match in matches)}",
        "- 这些「下一级」是本轮的**候选靶子**；做哪一个、做几个，**是判断**，不是提取。",
        "- 若某域的「下一级」为空串 ⇒ 该域已到头（宪章口径），不要凭空造下一格。",
        "",
    ])
    return lines


def _ci_lines(summary: Any) -> list[str]:
    total = summary.green + summary.no_run + summary.red + len(summary.unknown)
    lines = [
        "## 四、CI 台账结论（机械读数，不是独立取证）",
        "",
        f"- 结论：**{summary.verdict}**",
        f"- 行数：{total}（全 success {summary.green} / 无 run {summary.no_run} / "
        f"判红 {summary.red}）",
        f"- 最后一条：{summary.last}",
    ]
    lines.extend(f"- 未识别行：{item}" for item in summary.unknown)
    lines.append("")
    return lines


def _skeleton_lines(next_id: str) -> list[str]:
    created = f"{next_id[5:9]}-{next_id[9:11]}-{next_id[11:13]}"
    return [
        "## 五、下一轮 GOAL 的骨架（可由提取得到的那部分）",
        "",
        "```yaml",
        f"id: {next_id}",
        "status: DRAFT",
        f"created_at: {created}",
        f"updated_at: {created}",
        "objective: <待填：判断>",
        "exit_criteria: <待填：判断（每条自带 verify 与反证臂）>",
        "budget:",
        "  max_cycles: <待填：判断>",
        "  per_cycle_minutes: <待填：判断>",
        "  no_progress_stop_cycles: <待填：判断>",
        "authorization:",
        "  source: user-request",
        "  ref: <待填：本轮授权的原文要点>",
        "latest_recheck: null",
        "```",
        "",
        "## 六、不可自动推导的部分（**判断**，本工具不猜）",
        "",
        "- `objective`：本轮要达成的**一句话目标**；",
        "- `exit_criteria`：每条可机检（命令 + 期望值），且**自带反证臂**（改事实 ⇒ 判据翻向）；",
        "- 靶子选择：第三节里挑哪一个「下一级」，为什么是它而不是别的（写清依赖与代价）；",
        "- 预算与授权：`max_cycles` / 授权要点 / 是否需要停下登记。",
        "",
    ]


def build_skeleton(root: Path, goal: str, next_id: str) -> str:
    """产出一份骨架文本；任何一步不合格 ⇒ 抛 `Refusal`（**不产出半成品**）。"""
    inputs, matches, summary = _read_inputs(root, goal, next_id)
    items = PARSE.residual_section(inputs.goal_text)
    lines = [
        *_header_lines(inputs),
        *_residual_lines(items),
        *_ladder_lines(matches),
        *_ci_lines(summary),
        *_skeleton_lines(next_id),
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成下一轮 GOAL 的 charter 骨架（确定性）")
    parser.add_argument("--root", required=True, help="树根（不硬编码仓库根）")
    parser.add_argument("--goal", required=True, help="已收口 GOAL 的仓库相对路径")
    parser.add_argument(
        "--next-goal-id", required=True, help="下一个 GOAL 的 id（判断，不由本工具猜）"
    )
    parser.add_argument("--out", help="落盘路径（仅在成功时写；二进制写，LF）")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    try:
        text = build_skeleton(root, str(args.goal), str(args.next_goal_id))
    except PARSE.Refusal as refusal:
        print(f"REFUSED {refusal.code} {refusal.detail}", flush=True)
        return EXIT_REFUSED
    if args.out:
        target = Path(str(args.out))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode("utf-8"))
        print(f"wrote {target.as_posix()} (sha256:{PARSE.sha256_text(text)})", flush=True)
    else:
        sys.stdout.write(text)
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
