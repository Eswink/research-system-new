"""记忆的**内容级冲突判定**（GOAL-20261018-083 EC-01；阶梯「证据」域的 `下一级`）。

**它补哪一格**：门链的 `contradiction` 阶段（`memory/gate._contradiction_check`）只查
**引用完整性** —— 被引 id 存在 + 不得自指；**正文一个字都不看**。读面的 `CONFLICTED` 处置
也**只来自声明**（`contradictions` 列表由提案方填写，经 `conflicted_by_index` 反向投影）。
⇒ 两条记忆**说法真的相反**、但没人声明时，读面照旧报 `USE`（「照用」）：一份自相矛盾的知识库
与一份一致的知识库在处置面上**不可区分**。

**判定必须是确定性纯函数**（本 GOAL 的 `forbidden`）：**零出网、零模型调用、零时钟、零随机**。
理由：门链是可复现、可离线判的东西；引入 LLM 判「说法是否相反」会让它变成不可复现的门。

**射程（逐条明写，`W-2`）** —— 本模块**只判可机械判的三种形态**：

1. **否定极性**：同一 `(主语, 断言核)`，一侧带否定标记、另一侧不带
   （`X supports Y` vs `X does not support Y`）；
2. **数值方向**：同一 `(主语, 谓词)` 的数值，一侧更大且另一侧更小
   （`the ratio is 2.0` vs `the ratio is 0.5` —— 只有**排序明确相反**时才算，见下）；
3. **极性词对**：同一 `(主语, 谓词)` 的一对**反义谓词**（`increase` vs `decrease`）。

**不判**（`W-2` 的边界，判据里逐条钉住）：需要**世界知识**的矛盾
（`the drug is effective` vs `the drug is ineffective` 在词面上可以判；
但 `it works` vs `it fails` 之外的同义改写、以及「A 比 B 好」vs「B 更差」这类需要推演的形态
**不在**射程）。

**为什么不做全库扫描**（`W-3`）：判定发生在**写入时**（提案 vs 既有记录），不给存量记忆
批量补判 —— 那属迁移，需单独设计。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

#: 否定标记（**词边界**匹配；`not` / `no` / `never` / `without` / 中文「不」「并非」「没有」）。
_NEGATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:not|never|no longer|without)\b", re.IGNORECASE),
    re.compile(r"(?:不|并非|没有|从未)"),
)

#: 反义谓词对（同一 (主语, 谓词位置) 上出现相反的两个词 ⇒ 冲突）。
_ANTONYM_PAIRS: tuple[tuple[str, str], ...] = (
    ("increase", "decrease"),
    ("increases", "decreases"),
    ("increase", "reduce"),
    ("improve", "degrade"),
    ("improves", "degrades"),
    ("higher", "lower"),
    ("supports", "refutes"),
    ("有效", "无效"),
    ("提高", "降低"),
)

#: 判定形态（判词的稳定标签；读面与判据都按它对齐）。
FORM_NEGATION = "NEGATION_POLARITY"
FORM_NUMERIC = "NUMERIC_DIRECTION"
FORM_ANTONYM = "ANTONYM_PREDICATE"

#: **带单位**的度量值（只有这一形态参与数值比较；见 `_numbers` 的理由）。
#: 单位词表是**闭集**且**短**（只收本仓语料里真出现过的单位）—— 不猜未知单位。
_UNITS = (
    "ms",
    "s",
    "sec",
    "secs",
    "seconds",
    "min",
    "mins",
    "minutes",
    "h",
    "hours",
    "kb",
    "mb",
    "gb",
    "bytes",
    "items",
    "records",
    "sources",
    "runs",
    "arms",
    "percent",
    "%",
    "ratio",
    "分",
    "秒",
    "次",
    "条",
)
#: 数字形态（骨架比较用：把每个数字换成占位符后逐字比）。
_NUMBER_SHAPED = re.compile(r"-?\d+(?:\.\d+)?")

_NUMERIC_WITH_UNIT = re.compile(
    r"(?<![\w-])(-?\d+(?:\.\d+)?)\s*(?:" + "|".join(re.escape(unit) for unit in _UNITS) + r")\b"
)


@dataclass(frozen=True, slots=True)
class ContentConflict:
    """一次**内容级**冲突判定的结果（`form` 是判词形态，`shared` 是共享的断言核）。"""

    form: str
    shared: str


def _normalize(text: str) -> str:
    """空白归一 + 小写（**不**做词干化 / 不做同义词替换：那会引入不可复核的推断）。"""
    return " ".join(text.lower().split())


def _negated(text: str) -> bool:
    return any(pattern.search(text) for pattern in _NEGATION_PATTERNS)


def _strip_negation(text: str) -> str:
    """去掉否定标记后的**断言核**（用于判断两侧是否在说同一件事）。

    英语的否定常带助动词（`does not` / `do not` / `did not` / `is not`）—— 只去 `not` 会留下
    一个多出来的 `does`，两侧词形就对不上了（实测：`X supports Y` vs `X does not support Y`
    因此漏判）。⇒ 否定标记连同**紧邻的助动词**一起去掉。
    """
    stripped = text
    for pattern in _NEGATION_PATTERNS:
        stripped = pattern.sub(" ", stripped)
    # 去掉被留在原地的助动词（只在**紧邻**否定位置时才有；这里按词边界整体去，
    # 因为它们不携带断言内容）。
    stripped = re.sub(r"\b(?:does|do|did|is|are|was|were|has|have|had)\b", " ", stripped)
    return " ".join(stripped.split())


def _numbers(text: str) -> tuple[float, ...]:
    """正文里的**度量值**（只收**带单位**的数字 —— 见 `_NUMERIC_WITH_UNIT`）。

    **为什么只收带单位的**：`mem-1` / `内容 1` / `pipeline A ... 3` 里的数字是**标识或编号**，
    不是可比较的量。把它们当量值会让「两条不同的记录」被判成「数值相反」（实测三条误报）。
    ⇒ 只认「数字 + 紧邻的单位词」这一形态；量纲不明确时**不判**（`W-2` 的边界）。
    """
    return tuple(float(match.group(1)) for match in _NUMERIC_WITH_UNIT.finditer(text))


def _shared_core(first: str, second: str) -> str | None:
    """两条正文的**共享断言核**（去掉否定与数字之后的公共部分）。

    只认「除了否定/数字/**第三人称单数后缀**之外完全一致」的形态 —— 这是**形态级**判定的
    边界：任何需要推断的相似性都不算共享（否则会误报，见 `EC-04`）。

    **为什么允许剥第三人称单数**：`X supports Y` vs `X does not support Y` 是同一断言的正反，
    只差一个 `-s`。这不是词干化 —— 只在**两侧词数相同**且**只有动词位不同**时剥（见
    `_strip_third_person`），不做任何语义推断。
    """
    left_words = _word_core(first)
    right_words = _word_core(second)
    if not left_words or not right_words:
        return None
    if len(left_words) != len(right_words):
        return None
    candidates = (
        (" ".join(left_words), left_words, right_words),
        (" ".join(right_words), left_words, _strip_third_person(right_words)),
        (" ".join(left_words), _strip_third_person(left_words), right_words),
        (
            " ".join(_strip_third_person(left_words)),
            _strip_third_person(left_words),
            _strip_third_person(right_words),
        ),
    )
    for label, a, b in candidates:
        if a == b:
            return label
    return None


def _word_core(text: str) -> list[str]:
    """正文 → 词序列（去否定标记 / 助动词 / 数字）。"""
    words = " ".join(re.findall(r"[a-z\u4e00-\u9fff]+", _strip_negation(text))).split()
    return [
        re.sub(r"\d+(?:\.\d+)?", "", word) for word in words if re.sub(r"\d+(?:\.\d+)?", "", word)
    ]


def _strip_third_person(words: list[str]) -> list[str]:
    """剥掉**一个**词的第三人称单数后缀（`supports` → `support`；`is` → `i` 这类不动）。

    只在**长度 ≥ 4** 的纯小写词上剥（`-es` / `-s`），避免把 `is` / `as` 这类短词弄坏。
    """
    out: list[str] = []
    for word in words:
        if len(word) >= 5 and word.endswith("ies"):
            out.append(word[:-3] + "y")
        elif len(word) >= 5 and word.endswith("es"):
            out.append(word[:-2])
        elif len(word) >= 4 and word.endswith("s") and not word.endswith("ss"):
            out.append(word[:-1])
        else:
            out.append(word)
    return out


def detect_content_conflict(first: str, second: str) -> ContentConflict | None:
    """两条正文**是否真的相反**（确定性纯函数；`None` = 判不出或不相反）。

    三种形态按**固定顺序**尝试（判词因此稳定）：否定极性 → 数值方向 → 反义谓词。

    **数值形态的额外前置**（`EC-04` 实测三条误报之后加的）：
    两侧的**字面骨架**必须**逐字相同**（把数字替换成占位符后比较）—— 这一条同时排掉
    `mem-1` vs `mem-2`（编号）、`内容 1` vs `内容 2`（编号）、以及
    `pipeline A ... 3 minutes` vs `pipeline B ... 40 minutes`（**不同主语**：A/B 不同 ⇒
    不是同一断言）。再要求至少一侧的数字**带单位**（见 `_numbers`）。
    """
    left = _normalize(first)
    right = _normalize(second)
    if not left or not right or left == right:
        return None

    shared = _shared_core(first, second)
    if shared is not None and _negated(left) != _negated(right):
        return ContentConflict(form=FORM_NEGATION, shared=shared)

    numeric = _numeric_direction(first, second)
    if numeric is not None:
        return numeric

    antonym = _antonym_pair(left, right)
    if antonym is not None:
        return ContentConflict(form=FORM_ANTONYM, shared=antonym)
    return None


def _numeric_direction(first: str, second: str) -> ContentConflict | None:
    """数值**排序明确相反** + **字面骨架相同**（唯一严格的数值形态）。

    骨架比较：把每个数字替换成 `<n>` 后**逐字比较** —— A/B 这类**不同主语**因此不会被
    当成同一断言（`EC-04` 实测：那是最容易误报的形态）。
    """
    left_shape = _NUMBER_SHAPED.sub("<n>", _normalize(first))
    right_shape = _NUMBER_SHAPED.sub("<n>", _normalize(second))
    if left_shape != right_shape:
        return None
    left_numbers = _numbers(first)
    right_numbers = _numbers(second)
    if not left_numbers or not right_numbers or len(left_numbers) != len(right_numbers):
        return None
    if not _numerically_opposed(left_numbers, right_numbers):
        return None
    return ContentConflict(form=FORM_NUMERIC, shared=left_shape.replace("<n>", "").strip())


def _word_core_shared(first: str, second: str) -> str | None:
    """**去数字后**词序列相同 ⇒ 返回该核（保留：判据/调用方按需使用）。"""
    left_words = _word_core(first)
    right_words = _word_core(second)
    if not left_words or not right_words or left_words != right_words:
        return None
    return " ".join(left_words)


def _numerically_opposed(left: tuple[float, ...], right: tuple[float, ...]) -> bool:
    """数值**排序明确相反**（不是「不相等」—— 那会把任何两次不同测量当成冲突）。

    判据：同一位次上，一侧**全部**更大且另一侧**全部**更小（至少一个位次）。
    等值位次允许（那是同一个量）。
    """
    if len(left) != len(right):
        return False
    greater = any(a > b for a, b in zip(left, right))
    smaller = any(a < b for a, b in zip(left, right))
    if greater and smaller:
        # 同一对数字里既有更大又有更小 ⇒ 量纲不一致，不判（避免误报）。
        return False
    return greater or smaller


def _antonym_pair(left: str, right: str) -> str | None:
    """两侧是否落在同一对反义谓词上（且**只有一个**词位相反）。"""
    for forward, backward in _ANTONYM_PAIRS:
        if (forward in left and backward in right) or (backward in left and forward in right):
            # 断言核 = 去掉那一对词之后的剩余部分；只有剩余部分**一致**才算同一断言。
            a = left.replace(forward, " ").replace(backward, " ")
            b = right.replace(forward, " ").replace(backward, " ")
            a = " ".join(a.split())
            b = " ".join(b.split())
            if a == b and a:
                return a
    return None


def declarations_of(record: Any) -> tuple[str, ...]:
    """该记录**声明**的冲突对象（读面「声明 vs 内容判定」两来源的声明侧）。"""
    return tuple(str(item) for item in (getattr(record, "contradictions", ()) or ()))


__all__ = [
    "FORM_ANTONYM",
    "FORM_NEGATION",
    "FORM_NUMERIC",
    "ContentConflict",
    "declarations_of",
    "detect_content_conflict",
]
