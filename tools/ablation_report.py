#!/usr/bin/env python3
"""配对消融的**读数表 + 位移统计 + `MIN_CORPUS=3` 拒绝门**（GOAL-20261111-109 EC-04/05）。

**它补哪一格**：`ablation.py` / `output_readings.py` 是纯函数（收装配、收单份读数）。
要回答「k 次重复 × 两臂之后，X 的存在有没有使输出读数**分布**发生位移」，必须有人把
k×2 份观测汇总成表、算位移、并**拒绝语料不足的认证** —— 那就是本脚本。

**输入契约**（JSON 文件或 stdin；由**跑消融实验的一方**产出——本脚本只汇总，不触网）：

```json
{"slot": "retrieval",
 "pairs": [{"label": "k1",
            "present": {"comparison_digest": "sha256:..", "design_state": "block_present",
                        "arm_count": 2, "parameter_count": 3, "citation_count": 1},
            "absent":  {... 同形 ...}}]}
```

**判什么、不判什么**（措辞边界机械化，EC-05）：判**读数分布的位移**
（design block 产出率 / 臂数 / 参数数 / 引用数四列，两臂各一列 + 位移列）；
**不判**「模型采纳了 X」——报告文本由本模块自己的词表守卫压住
（`forbidden_words()` 闭集；`render_report` 出口自检，命中即抛）。

**门**：`MIN_CORPUS = 3` 对配对（与 `citation_distribution.MIN_CORPUS` 同源同值）；
**k<3 拒绝认证并点名**（缺什么、现有什么）——没有语料支撑的位移结论不是结论，是编造。

**它不做什么**：不写阈值、不改库、不触网、不扫测试夹具。

用法：

    uv run --frozen --no-sync python -B tools/ablation_report.py --input ablation.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]

#: 配对语料下界（与 `citation_distribution.MIN_CORPUS` 同值；**本模块自持一份**，
#: 并由判据断言两者相等——跨模块常量不 import 只比对，避免 tools/ 依赖产品包）。
MIN_CORPUS = 3

#: 观测里**必须**有的四列读数（可数的；缺列即点名，不猜默认值）。
READING_FIELDS: tuple[str, ...] = (
    "design_block",
    "arm_count",
    "parameter_count",
    "citation_count",
)

#: 措辞边界闭集（EC-05）：报告文本里**不得**出现任何一个词。
#: 「采纳/adopt」是**意图归因**词汇；本报告判的是分布位移，词表是这条边界的机械形态。
_FORBIDDEN_WORDS: tuple[str, ...] = (
    "adopt",
    "adopts",
    "adopted",
    "adoption",
    "采纳",
    "采纳了",
    "被采纳",
)

#: 两臂的固定标签（`present` = 有 X；`absent` = 无 X。不收其它标签）。
ARM_LABELS: tuple[str, ...] = ("present", "absent")


class AblationError(ValueError):
    """输入畸形（缺列 / 臂标签非法 / 配对两臂键不等）—— 点名，**不猜**。

    **不**用 dataclass 承载：`slots=True` 的冻结 dataclass 会生成只收声明字段的
    `__init__`，`AblationError("消息")` 直接 TypeError（实测）——异常就要是异常。
    """


@dataclass(frozen=True, slots=True)
class CorpusGate:
    """语料够不够（`MIN_CORPUS`）；不够就**点名缺什么**（形态照 calibration_gate）。"""

    sufficient: bool
    pairs: int
    missing: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ColumnShift:
    """一列读数的两臂分布与位移（均值差；列名 + 两臂均值 + 位移）。"""

    field: str
    present_mean: float
    absent_mean: float

    @property
    def shift(self) -> float:
        return round(self.present_mean - self.absent_mean, 4)

    @property
    def shifted(self) -> bool:
        return self.shift != 0.0


@dataclass(frozen=True, slots=True)
class AblationReport:
    """汇总结果：门 + 位移列 + 是否有任一列位移（**不**给出「采纳」类结论）。"""

    slot: str
    gate: CorpusGate
    shifts: tuple[ColumnShift, ...]
    labels: tuple[str, ...]

    @property
    def shifted_columns(self) -> tuple[str, ...]:
        return tuple(column.field for column in self.shifts if column.shifted)


def forbidden_words() -> tuple[str, ...]:
    """措辞边界闭集（判据读它做正例与反证）。"""
    return _FORBIDDEN_WORDS


def _observation(raw: object, *, arm: str, label: str) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise AblationError(f"pair {label!r} arm {arm!r} must be a mapping")
    digest = raw.get("comparison_digest")
    if not isinstance(digest, str) or not digest:
        raise AblationError(f"pair {label!r} arm {arm!r} missing comparison_digest")
    values: dict[str, Any] = {}
    for field in READING_FIELDS:
        value = raw.get(field)
        if not isinstance(value, int) or isinstance(value, bool):
            raise AblationError(
                f"pair {label!r} arm {arm!r} field {field!r} must be an int, got {value!r}"
            )
        values[field] = value
    values["comparison_digest"] = digest
    return values


def _load(raw: object) -> tuple[str, tuple[tuple[str, dict[str, Any], dict[str, Any]], ...]]:
    """输入 JSON → (slot, [(label, present, absent)])；**畸形逐条点名**。"""
    if not isinstance(raw, Mapping):
        raise AblationError("input must be a JSON object with 'slot' and 'pairs'")
    slot = raw.get("slot")
    if not isinstance(slot, str) or not slot:
        raise AblationError("input 'slot' must be a non-empty string")
    pairs_raw = raw.get("pairs")
    if not isinstance(pairs_raw, list):
        raise AblationError("input 'pairs' must be a list")
    pairs: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for item in pairs_raw:
        if not isinstance(item, Mapping):
            raise AblationError("each pair must be an object with label/present/absent")
        label = str(item.get("label", ""))
        if not label:
            raise AblationError("each pair needs a non-empty 'label'")
        present = _observation(item.get("present"), arm="present", label=label)
        absent = _observation(item.get("absent"), arm="absent", label=label)
        if present["comparison_digest"] != absent["comparison_digest"]:
            raise AblationError(
                f"pair {label!r}: the two arms must share one comparison_digest "
                f"({present['comparison_digest']} != {absent['comparison_digest']})"
            )
        pairs.append((label, present, absent))
    return slot, tuple(pairs)


def corpus_gate(pairs: Sequence[Any]) -> CorpusGate:
    """k 对配对够不够标定；**k<3 拒绝认证并点名**（形态照 `calibration_gate`）。"""
    count = len(pairs)
    if count >= MIN_CORPUS:
        return CorpusGate(sufficient=True, pairs=count, missing=())
    return CorpusGate(
        sufficient=False,
        pairs=count,
        missing=(f"ablation pairs: {count} of {MIN_CORPUS} required",),
    )


def column_shifts(
    pairs: Sequence[tuple[str, dict[str, Any], dict[str, Any]]],
) -> tuple[ColumnShift, ...]:
    """四列读数的两臂均值与位移（确定性；四舍五入到 4 位避免浮点噪声进判词）。"""
    if not pairs:
        return tuple()
    shifts: list[ColumnShift] = []
    for field in READING_FIELDS:
        present = sum(item[1][field] for item in pairs) / len(pairs)
        absent = sum(item[2][field] for item in pairs) / len(pairs)
        shifts.append(
            ColumnShift(
                field=field,
                present_mean=round(present, 4),
                absent_mean=round(absent, 4),
            )
        )
    return tuple(shifts)


def build_report(raw: object) -> AblationReport:
    """输入 JSON → 汇总（门 + 位移列）。**畸形逐条点名**；不做任何意图归因。"""
    slot, pairs = _load(raw)
    return AblationReport(
        slot=slot,
        gate=corpus_gate(pairs),
        shifts=column_shifts(pairs),
        labels=tuple(label for label, _present, _absent in pairs),
    )


def render_report(report: AblationReport) -> str:
    """汇总 → 文本报告（出口自检措辞边界：命中闭集词即抛，fail-closed）。"""
    lines = [
        f"# Ablation report: slot={report.slot}",
        f"pairs: {report.gate.pairs} (MIN_CORPUS={MIN_CORPUS})",
        f"gate: {'sufficient' if report.gate.sufficient else 'INSUFFICIENT'}",
    ]
    if report.gate.missing:
        lines.extend(f"missing: {item}" for item in report.gate.missing)
    lines.append("")
    lines.append("column | present_mean | absent_mean | shift | shifted")
    lines.append("--- | --- | --- | --- | ---")
    for column in report.shifts:
        lines.append(
            f"{column.field} | {column.present_mean} | {column.absent_mean} | "
            f"{column.shift} | {'yes' if column.shifted else 'no'}"
        )
    lines.append("")
    shifted = report.shifted_columns
    if report.gate.sufficient:
        verdict = (
            f"verdict: with {report.gate.pairs} pairs, output readings shifted in "
            f"{len(shifted)} of {len(report.shifts)} columns ({', '.join(shifted) or 'none'})"
            if shifted
            else f"verdict: with {report.gate.pairs} pairs, no column shifted"
        )
    else:
        verdict = "verdict: corpus insufficient; no distributional claim is made"
    lines.append(verdict)
    text = "\n".join(lines) + "\n"
    offenders = [word for word in _FORBIDDEN_WORDS if word in text]
    if offenders:
        raise AblationError(f"report text contains forbidden wording: {offenders}")
    return text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="paired-ablation readings report")
    parser.add_argument("--input", default="-", help="observations JSON ('-' = stdin)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    raw: object
    if args.input == "-":
        raw = json.load(sys.stdin)
    else:
        raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = build_report(raw)
    sys.stdout.write(render_report(report))
    return 0 if report.gate.sufficient else 1


if __name__ == "__main__":
    raise SystemExit(main())
