"""面板判词的**引用面**（GOAL-20261111-111 EC-01）：让判词可被反驳。

**它补哪一格**：`manuscript_panel` 的 `rationale` 是模型写的自由文本。读者拿到
「REFUTED: the Results section overstates what the measurements show」时**无法核对**
它指的是正文哪一句 —— 它可能指着一句不存在的话。判词因此停在「某个模型认为」，
**不可反驳**。

**本轮把它变成什么**：正文切成**编号句子**（`S1…Sn`，确定性、可复算）；
`REFUTED` 的 `rationale` 必须**落在正文的字节上**：

1. 点名 `S<n>` 且 `n` 在 `1..len(sentences)` 内；或
2. 引用一段**正文的真实子串**（长度 ≥ `MIN_QUOTE_CHARS`，避免「the」这种平凡命中）。

**两种「不成立」必须分得开**（GOAL-081 的教训在判词面的应用）：

- `EMPTY_RATIONALE`：模型**没写**理由 —— 「没给判据」；
- `NOT_GROUNDED`：写了理由但**指不到正文**（`S99` 越界 / 片段不在正文）—— 「给了个假的」。

两者都判负，但**点名不同**：前者是模型没做功课，后者是判词不可核验。

**射程（写死，不夸大）**：核验成立只说明「那句话确实在正文里，且判词指着它」——
**不说明**「那个判断是对的」。本轮**不**给引用充分性拍阈值，**不**改 `NOT_JUDGED`。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

#: 句子切分点：句末标点（`.!?`）后跟空白。与 `manuscript_quality._SENTENCE_SPLIT` 同形
#: ——**同一条语言假定只应有一份**；这里不 import 它（那会拖进确定性判据模块的整份依赖），
#: 而由判据断言两处正则**逐字相同**（改一处不改另一处 ⇒ 红）。
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

#: 判词里点名的句子编号（`S3` / `s12`）。
SENTENCE_REF = re.compile(r"\bS(\d{1,3})\b", re.IGNORECASE)

#: 引用片段的最小长度（字符）：短于它就没有区分力（「the」在任何正文里都命中）。
MIN_QUOTE_CHARS = 12

#: 核验结果闭集（**两种「不成立」分开**）。
GROUNDED = "GROUNDED"
NOT_GROUNDED = "NOT_GROUNDED"
EMPTY_RATIONALE = "EMPTY_RATIONALE"
OUTCOMES: frozenset[str] = frozenset({GROUNDED, NOT_GROUNDED, EMPTY_RATIONALE})

#: 判词里显式引用原文的标记（模型按提示词写 `excerpt: "..."` / 双引号原文）。
_QUOTED = re.compile(r"[\"“]([^\"”]{12,})[\"”]")


@dataclass(frozen=True, slots=True)
class NumberedSentence:
    """一条编号句子：`ordinal` 从 1 起，与读面写的 `S<n>` 同一编号。"""

    ordinal: int
    text: str

    @property
    def marker(self) -> str:
        return f"S{self.ordinal}"


@dataclass(frozen=True, slots=True)
class GroundingResult:
    """一条 rationale 的核验结论：结果闭集之一 + **点名**（缺什么 / 指到了哪句）。"""

    outcome: str
    #: 命中的句子编号（`GROUNDED` 时非空；否则空）。
    sentences: tuple[int, ...] = ()
    #: `NOT_GROUNDED` / `EMPTY_RATIONALE` 时逐条点名原因。
    missing: tuple[str, ...] = ()

    @property
    def grounded(self) -> bool:
        return self.outcome == GROUNDED


def number_sentences(text: str) -> tuple[NumberedSentence, ...]:
    """正文 → 编号句子（确定性；空正文 ⇒ 空元组，不猜）。"""
    body = (text or "").strip()
    if not body:
        return ()
    parts = [part.strip() for part in SENTENCE_SPLIT.split(body) if part.strip()]
    return tuple(NumberedSentence(ordinal=index, text=part) for index, part in enumerate(parts, 1))


def grounding_of(rationale: str, sentences: Sequence[NumberedSentence]) -> GroundingResult:
    """一条 `rationale` 是否**落在正文上**（`S<n>` 在范围内，或引用了真实子串）。"""
    body = (rationale or "").strip()
    if not body:
        return GroundingResult(
            outcome=EMPTY_RATIONALE,
            missing=("rationale is empty: a verdict without a reason cites nothing",),
        )
    corpus = " ".join(sentence.text for sentence in sentences)
    hits: list[int] = []
    missing: list[str] = []
    for raw in SENTENCE_REF.findall(body):
        ordinal = int(raw)
        if 1 <= ordinal <= len(sentences):
            hits.append(ordinal)
        else:
            missing.append(f"S{ordinal} is outside the manuscript (1..{len(sentences)})")
    quoted_hits = 0
    for quote in _QUOTED.findall(body):
        if quote.strip() and quote.strip() in corpus:
            quoted_hits += 1
            continue
        missing.append(f"quoted text is not a substring of the manuscript: {quote.strip()[:60]!r}")
    if hits or quoted_hits:
        return GroundingResult(outcome=GROUNDED, sentences=tuple(sorted(set(hits))))
    if missing:
        return GroundingResult(outcome=NOT_GROUNDED, missing=tuple(missing))
    return GroundingResult(
        outcome=NOT_GROUNDED,
        missing=(
            "rationale names no sentence (S<n>) and quotes no manuscript text: "
            "a verdict nobody can check is not a verdict about this manuscript",
        ),
    )


def grounded_in(rationale: str, text: str) -> GroundingResult:
    """便利入口：`rationale` 对**整份正文**核验（切句在本函数内完成）。"""
    return grounding_of(rationale, number_sentences(text))


__all__ = [
    "EMPTY_RATIONALE",
    "GROUNDED",
    "GroundingResult",
    "MIN_QUOTE_CHARS",
    "NOT_GROUNDED",
    "OUTCOMES",
    "NumberedSentence",
    "SENTENCE_REF",
    "SENTENCE_SPLIT",
    "grounded_in",
    "grounding_of",
    "number_sentences",
]
