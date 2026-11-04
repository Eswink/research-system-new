"""引用充分性的**结构读数**（GOAL-20261103-105 EC-01；`MANUSCRIPT_QUALITY.md` §7 第 4 项）。

**它补哪一格**：`manuscript_quality.NOT_JUDGED` 的第 4 项是
`whether the citation set is sufficient for each claim`。§7 用四条依据（P1 确定性 /
P2 反证可写 / P3 不需外部知识 / P4 不冒充语义）判过：这一项**可机械判（弱口径）**，
但当时**不实现**，理由是「阈值需要先有真实语料标定」。本轮把**读数**做出来，
**阈值仍然不拍** —— 因为仓内**零真实手稿语料**（实测：排除 `.venv` / `node_modules`
后 `manuscript*.md` 0 命中；`data/e2e.db` 的 `artifacts` 表 0 行；所有手稿字节都是
测试夹具，最大 209 词）⇒ 任何「该引 3 篇」类的数字都是**编造**。

**三个读数**（确定性纯函数：零出网、零模型、零时钟、不读文件系统）：

1. **每句的引用数**（`per_sentence`）：在 `CITED_SECTIONS`（introduction / results /
   discussion）里按句切分，逐句数 `[n]` 标记的个数。
2. **每条被引条目被引几次**（`per_reference`）：全手稿范围内每个编号的出现次数。
3. **单支撑节**（`single_support_sections`）：某节的**唯一**引用编号在该节只出现一次、
   且该编号在全稿只被引一次（= 这一节的全部支撑压在同一条文献的一次引用上）。

**本模块不做什么**（射程边界，**这是本模块最重要的一段**）：

* **不判负**。`enforce=False` 是缺省：只返回读数，不抛错。一个「每句零引用」的正文
  在本模块眼里是**一份有读数的正文**，不是一份错的正文。
* **不拍阈值**。三个具名常量 `MIN_MARKS_PER_SENTENCE` / `MIN_CITATIONS_PER_REFERENCE` /
  `MIN_SUPPORT_PER_SECTION` **缺省全部 `None`**。取值条件是**标定语料**：≥3 份真实
  `manuscript.md` 的分布量过之后才有资格填；填了但没写标定来源，`uncalibrated_thresholds()`
  会把名字点出来（判据钉住这一条）。
* **不改 `NOT_JUDGED`**。第 4 项**仍留在**那个常量里：有读数 ≠ 判了「充分」。移出它会让
  `test_nothing_was_implemented_under_the_cover_of_the_argument` 判红，而且那是**冒充** ——
  计数分布不回答「够不够」。
* **不判「那条引用支持了那句话」**（那是第 1 项，需要语义蕴含 ⇒ 只能人评）。

**计数与「充分」的距离**：一份每句都引 3 篇的手稿可能整段引错，一份只有一处引用的
Methods 可能完全恰当。本模块产出的是**可数的形态**，不是判断。反向读它（「读数看起来
正常 ⇒ 引用充分」）正是 §3 明令禁止的那种误读。
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from packages.application.deliverable.manuscript_quality import _CITATION, _SENTENCE_SPLIT

#: 逐句读数的射程：这三节是**主张**所在（abstract / conclusion 是总结面，
#: related_work / methods 的引用密度与主张强度不是同一件事）。
CITED_SECTIONS: tuple[str, ...] = ("introduction", "results", "discussion")

#: 引用标记的语法**不在这里定义**：`_CITATION` 与 `_SENTENCE_SPLIT` 一起从
#: `manuscript_quality` 导入（那一份与 `manuscript.CITATION_PATTERN` 逐字同形）。
#: 本模块**不写第三份正则** —— 由
#: `test_the_citation_grammar_is_the_same_object_not_a_copy` 钉住（它判源码 AST：
#: 本模块里不得出现对引用语法的再一次 `re.compile`）。

#: 每句最少几个引用标记。**`None` = 不判**。
#:
#: **为什么是 None 而不是一个数**：取值需要 ≥3 份**真实**手稿的分布（仓内零真实语料，
#: 见模块 docstring）。填一个数之前必须先有标定语料，并把来源写进 `CALIBRATION_SOURCES`
#: —— 否则 `uncalibrated_thresholds()` 会点名它。
MIN_MARKS_PER_SENTENCE: int | None = None

#: 每条被引条目最少被引几次。`None` = 不判（同上）。
MIN_CITATIONS_PER_REFERENCE: int | None = None

#: 每节最少几条独立支撑。`None` = 不判（同上）。
MIN_SUPPORT_PER_SECTION: int | None = None

#: 三个阈值的**标定语料来源**（常量非 `None` 时这里必须非空且在模块 docstring 里出现）。
#: 键与常量名逐字一致 —— 改常量名要同轮改这里，否则 `uncalibrated_thresholds()` 会当
#: 作「没有标定来源」点名它。
CALIBRATION_SOURCES: Mapping[str, str] = {
    "MIN_MARKS_PER_SENTENCE": "",
    "MIN_CITATIONS_PER_REFERENCE": "",
    "MIN_SUPPORT_PER_SECTION": "",
}

_THRESHOLDS: Mapping[str, int | None] = {
    "MIN_MARKS_PER_SENTENCE": MIN_MARKS_PER_SENTENCE,
    "MIN_CITATIONS_PER_REFERENCE": MIN_CITATIONS_PER_REFERENCE,
    "MIN_SUPPORT_PER_SECTION": MIN_SUPPORT_PER_SECTION,
}


@dataclass(frozen=True, slots=True)
class SentenceMarks:
    """一句的读数（哪一节 / 第几句 / 几个引用标记）。"""

    section: str
    index: int
    marks: int


@dataclass(frozen=True, slots=True)
class CitationSufficiency:
    """三个读数的整体（`measure_citation_sufficiency` 的唯一返回类型）。"""

    per_sentence: tuple[SentenceMarks, ...]
    per_reference: Mapping[int, int]
    single_support_sections: tuple[str, ...]

    @property
    def sentences_without_marks(self) -> tuple[SentenceMarks, ...]:
        """零引用的句子（读数的一部分，**不是判负**）。"""
        return tuple(item for item in self.per_sentence if item.marks == 0)


def _marks(text: str) -> int:
    return len(_CITATION.findall(text))


def _sentences(text: str) -> tuple[str, ...]:
    """按 `manuscript_quality._SENTENCE_SPLIT` 切句（**同一个切分器**，不写第二个）。"""
    return tuple(part for part in _SENTENCE_SPLIT.split(text) if part.strip())


def mark_counts_per_sentence(
    sections: Mapping[str, str], *, section_keys: Sequence[str] = CITED_SECTIONS
) -> tuple[SentenceMarks, ...]:
    """**读数 1**：逐句数 `[n]`（缺节的节不产生读数，不补空句）。"""
    readings: list[SentenceMarks] = []
    for key in section_keys:
        text = str(sections.get(key) or "")
        for index, sentence in enumerate(_sentences(text), start=1):
            readings.append(SentenceMarks(section=key, index=index, marks=_marks(sentence)))
    return tuple(readings)


def citations_per_reference(sections: Mapping[str, str]) -> Mapping[int, int]:
    """**读数 2**：全手稿范围内每个编号的出现次数（键排序 ⇒ 同输入同迭代序）。"""
    counts: dict[int, int] = {}
    for text in sections.values():
        for match in _CITATION.finditer(str(text or "")):
            number = int(match.group(1))
            counts[number] = counts.get(number, 0) + 1
    return {number: counts[number] for number in sorted(counts)}


def single_support_sections(sections: Mapping[str, str]) -> tuple[str, ...]:
    """**读数 3**：唯一支撑压在同一条文献的**一次**引用上的节（节名按传入顺序）。

    条件三条同时成立（缺一不算）：① 该节只引了**一个**编号；② 该编号在该节只出现**一次**；
    ③ 该编号在**全稿**只被引**一次**。
    """
    total = citations_per_reference(sections)
    flagged: list[str] = []
    for key, text in sections.items():
        body = str(text or "")
        numbers = [int(match.group(1)) for match in _CITATION.finditer(body)]
        if len(numbers) != 1:
            continue
        only = numbers[0]
        if total.get(only) == 1:
            flagged.append(key)
    return tuple(flagged)


def measure_citation_sufficiency(
    sections: Mapping[str, str], *, enforce: bool = False
) -> CitationSufficiency:
    """三个读数一次取全。

    `enforce=False`（**缺省**）⇒ 只返回读数、**不抛错**：一份「每句零引用」的正文在这里
    是一份**有读数的**正文。`enforce=True` ⇒ 在读完之后按非 `None` 的阈值判负
    （而三个阈值缺省全 `None` ⇒ 即便 `enforce=True` 也什么都不判，除非调用方显式给值）。
    """
    readings = CitationSufficiency(
        per_sentence=mark_counts_per_sentence(sections),
        per_reference=citations_per_reference(sections),
        single_support_sections=single_support_sections(sections),
    )
    if enforce:
        enforce_sufficiency(readings)
    return readings


class CitationSufficiencyError(ValueError):
    """**只有**在显式 `enforce=True` 且阈值非 `None` 时才可能出现的判负。"""


def uncalibrated_thresholds() -> tuple[str, ...]:
    """填了值但**没有标定语料来源**的阈值名（空元组 = 每个非 `None` 的都有来源）。

    这是「不得拍阈值」这条禁令的机械形态：填一个数不会立刻判红，但**没有来源**的填充
    会被点名。判据 `test_a_threshold_without_a_calibration_source_is_named` 两向按压它。
    """
    docstring = __doc__ or ""
    missing: list[str] = []
    for name, value in _THRESHOLDS.items():
        if value is None:
            continue
        source = CALIBRATION_SOURCES.get(name, "")
        if not source.strip() or source not in docstring:
            missing.append(name)
    return tuple(missing)


def enforce_sufficiency(
    readings: CitationSufficiency,
    *,
    min_marks_per_sentence: int | None = MIN_MARKS_PER_SENTENCE,
    min_citations_per_reference: int | None = MIN_CITATIONS_PER_REFERENCE,
    min_support_per_section: int | None = MIN_SUPPORT_PER_SECTION,
) -> None:
    """**显式**启用时才判负（缺省阈值全 `None` ⇒ 这个函数什么都不做）。

    参数可覆盖模块常量 —— 但**判据不给覆盖开方便之门**：默认值就是从常量读的，
    而常量是 `None`。`enforce=False` 的语义在这里体现为「没有阈值 ⇒ 没有判负」。
    """
    if min_marks_per_sentence is not None:
        thin = [item for item in readings.per_sentence if item.marks < min_marks_per_sentence]
        if thin:
            first = thin[0]
            raise CitationSufficiencyError(
                f"{len(thin)} sentence(s) carry fewer than {min_marks_per_sentence} citation "
                f"mark(s); the first is {first.section} sentence {first.index} "
                f"({first.marks} mark(s))"
            )
    if min_citations_per_reference is not None:
        thin_refs = {
            number: count
            for number, count in readings.per_reference.items()
            if count < min_citations_per_reference
        }
        if thin_refs:
            raise CitationSufficiencyError(
                f"reference(s) {sorted(thin_refs)} are cited fewer than "
                f"{min_citations_per_reference} time(s): {thin_refs}"
            )
    if min_support_per_section is not None and readings.single_support_sections:
        raise CitationSufficiencyError(
            f"section(s) {list(readings.single_support_sections)} rest on a single citation "
            f"(minimum declared: {min_support_per_section} independent support(s))"
        )
