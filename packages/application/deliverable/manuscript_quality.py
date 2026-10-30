"""**叙述质量与事实一致性**的可机械判口径（GOAL-20261030-101 EC-01）。

**它补哪一格**：`deliverable/manuscript.py` 的 `validate_manuscript` 判四件**结构事实**
（八键齐备 / 正文无数字 / 引用不越界 / 无孤儿引用），而「写得对不对」**一条都不判** ——
这一格连续四轮登记为未覆盖项（GOAL-096 `U-1` → 097 `U-2` → 099 `W-5` → 100 `U-2`），
也是科研能力阶梯「报告」域的 `下一级`。

**本模块判什么**（三条，全部**确定性纯函数**：零出网、零模型、零时钟、不读文件系统）：

1. **引用—主张相关**（`check_citation_alignment`）：`Results` 节至少带一个 `[n]`，且
   **每一个被引条目**的 `title` 与正文（八节合计）**共享至少一个实词**（去停用词后）。
2. **节间不自我重复**（`check_section_distinctness`）：`abstract` 与 `conclusion` 的
   **归一化句子集合**不得重合（一句话在两个总结面里原样出现两次 = 两个面在说同一件事）。
3. **节非空洞**（`check_section_depth`）：每一节（标题除外）的**词数**不得低于阈值。
   阈值**由实测分布定**，不是拍脑袋：三套受控夹具的八节词数实测为
   `abstract 11…32 / introduction 9…24 / related_work 11…33 / methods 13…28 /
   results 12…39 / discussion 12…29 / conclusion 11…24` ⇒ 取**下界之下的保守值 8**
   （比任何一份夹具的最短节都低，只抓「写了几个词应付」这一类，不惩罚简洁）。

**本模块不判什么**（射程边界，**这是本模块最重要的一段**）：

* **不判「`[2]` 支持了那句话」** —— 词重叠只说「引的条目与正文**不是无关**」。一篇讲
  reproducibility 的文献与一段讲 reproducibility 的正文共享该词，但正文那句话可能
  **恰好相反**。判「支持」需要语义蕴含，那是人评或模型评，**本模块不声称做到**。
* **不判论证是否成立** —— 前提是否足够、推断是否有效、结论是否被数据支撑，全部在射程外。
  阶梯「报告」域的 `下一级`（「论证是否成立」）**因此仍未达成**。
* **不判方法学正确性**（臂是否合适、指标是否测到了想测的东西）。
* **不判引用是否充分**（一个主张该引 3 篇而只引 1 篇，本模块看不见）。
* **不判文风 / 可读性 / 语法**。

**为什么这三条值得做（而不是「反正判不全就不判」）**：它们各自封住一个**具体的、
已经发生过**的失败形态 ——
① 引用编号对但引错条目（GOAL-099 `W-1` 的邻居形态）；
② 摘要与结论互相复制（模型偷懒的典型形态）；
③ 某节写成一两个词（模型漏答一节的典型形态）。
三条都是**必要不充分**条件：过不了就是错的，过了不代表对。**这个方向的不对称是本设计
的全部价值**，也是它必须写进 docstring 的原因 —— 反向读它（「过了就是对的」）会把弱判据
当成强结论。

**判据在哪**：`tests/application/test_manuscript_quality.py`（三条各带反证臂）。
**调用点**：`deliverable/manuscript.py` 的 `validate_manuscript`（装配路径必经），
`assembled_by` 由该处传入 `ManuscriptQuality` 上下文（引用条目的 `title` 从
`ReferenceTable` 取 —— canonical，不出网）。
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

#: 手稿品质判据**不判**的面（写进制品脚注与文档，供读者核对射程）。
NOT_JUDGED: tuple[str, ...] = (
    "whether a citation supports the sentence it is attached to (only: not unrelated)",
    "whether the argument holds (premises sufficient / inference valid / conclusion supported)",
    "whether the method is appropriate for the question",
    "whether the citation set is sufficient for each claim",
    "writing style, readability, grammar",
)

#: 英文停用词（去停用词之后剩下的才算「实词」）。**封闭词表**：改它 = 改判据口径，
#: 必须同轮改 `tests/application/test_manuscript_quality.py` 里钉住它的用例。
STOPWORDS: frozenset[str] = frozenset(
    """a an the and or of to in for on with by as at from that this these those it its is are
    was were be been being we our us they their them which what who whom whose not no nor but if
    then than so such can could may might will would should do does did done have has had into
    over under about across after against all also among any because before between both during
    each few more most other some only own same very just too now up down out off again further
    once here there when where why how you he she his her i""".split()
)

#: 一节的最少词数（阈值**实测而来**：三套夹具的八节实测下界是 9 / 11 / 12 / 13 —— 见模块
#: docstring；取 8 只抓「写了几个词应付」，不惩罚简洁）。**标题**不受此判（它天然很短）。
MIN_SECTION_WORDS = 8

#: 「实词」的字符范围：英文词 + 连字符（`single-cell` 算一个词）。
_WORD = re.compile(r"[A-Za-z][A-Za-z-]{2,}")
#: 句子的切分点：句末标点后跟空白（不切 `e.g.` 之外的缩写由「后跟空白」这一条兜住大半）。
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
#: 引用标记（与 `manuscript.CITATION_PATTERN` 同一语法；此处**再写一份**是为了让本模块
#: 不 import 手稿模块 —— 反过来手稿模块 import 本模块，单向依赖避免循环）。
_CITATION = re.compile(r"\[(\d+)\]")


class ManuscriptQualityError(ValueError):
    """一条**点名**的品质判负（哪一节 / 哪条引用 / 哪一句）。"""


def content_words(text: str) -> frozenset[str]:
    """去停用词后的实词集合（小写；长度 ≥ 3 的英文词，连字符算同一个词）。"""
    return frozenset(word.lower() for word in _WORD.findall(text) if word.lower() not in STOPWORDS)


def _numbered(text: str) -> tuple[int, ...]:
    return tuple(int(match.group(1)) for match in _CITATION.finditer(text))


def check_citation_alignment(sections: Mapping[str, str], titles: Sequence[str]) -> None:
    """**引用—主张相关**：`Results` 有引用，且每条被引文献与正文**不是无关**。

    `titles` 按 References 的顺序（`titles[n-1]` = 第 `n` 条）—— 由调用方从
    `ReferenceTable` 取，本函数不读表、不猜顺序。

    **空引用列表是合法状态**（不是豁免，是合约原文）：`research_manuscript` 的任务书写明
    「If no records are listed, this run retrieved nothing citable: write the body without
    citation marks」⇒ `titles` 为空时本判据**没有对象**，直接通过。（此时 `Results` 不引
    任何东西不是缺陷 —— 本 run 确实什么都没检索到。若要求它引用，就会逼模型编造。）

    判负三种（各自点名，不合并成一句「引用不合格」）：
    ① 有可引用条目、但 `results` 节**没有任何** `[n]`（结果段不引 → 读者无法核）；
    ② 被引编号越界（调用方通常已判；本函数**再判一次**是因为它自己也要用 `titles` 索引，
       不能依赖上游顺序）；
    ③ 某条被引文献的 `title` 与正文**零实词重叠** ⇒ 点名条号与标题。

    **射程**：词重叠只说「不是无关」。**不**说「支持」。见模块 `NOT_JUDGED`。
    """
    if not titles:
        return
    results = str(sections.get("results") or "")
    if not _numbered(results):
        raise ManuscriptQualityError(
            "the Results section carries no citation mark: a measured claim that cites nothing "
            "cannot be checked by a reader (this run listed "
            f"{len(titles)} citable record(s))"
        )
    body = content_words(" ".join(str(sections.get(key) or "") for key in sections))
    cited = sorted({index for text in sections.values() for index in _numbered(str(text or ""))})
    for index in cited:
        if index < 1 or index > len(titles):
            raise ManuscriptQualityError(
                f"citation [{index}] resolves to no reference (this run lists {len(titles)})"
            )
        overlap = content_words(titles[index - 1]) & body
        if not overlap:
            raise ManuscriptQualityError(
                f"reference [{index}] ({titles[index - 1][:60]!r}) shares no content word with the "
                "manuscript body: the cited work is not merely unsupportive, it is unrelated to "
                "anything this manuscript says"
            )


def _sentences(text: str) -> frozenset[str]:
    """归一化句子集合（小写、压缩空白、去首尾标点空白）。"""
    normalised: set[str] = set()
    for raw in _SENTENCE_SPLIT.split(text):
        cleaned = " ".join(unicodedata.normalize("NFKC", raw).split()).strip(" .,;:!?").lower()
        if cleaned:
            normalised.add(cleaned)
    return frozenset(normalised)


def check_section_distinctness(sections: Mapping[str, str]) -> None:
    """**节间不自我重复**：`abstract` 与 `conclusion` 的句子集合不得有交集。

    判负即点名**共用的那一句**（不笼统说「两节重复」）—— 一句话在两个总结面里原样出现
    两次，等于两个面在说同一件事而漏掉了另一个面该说的话。

    **射程**：只判**逐字（归一化后）相同**的句子。改写过的重复（同义复述）本判据看不见；
    `abstract` 与正文其他节的重复也**不判**（摘要引正文原句是正当写法）。
    """
    shared = _sentences(str(sections.get("abstract") or "")) & _sentences(
        str(sections.get("conclusion") or "")
    )
    if shared:
        raise ManuscriptQualityError(
            "the Abstract and the Conclusion share the sentence(s) "
            f"{sorted(shared)!r}: the two summary faces must not say the same thing verbatim"
        )


def check_section_depth(sections: Mapping[str, str], *, minimum: int = MIN_SECTION_WORDS) -> None:
    """**节非空洞**：每一节（`title` 除外）的词数 ≥ `minimum`；不足 ⇒ 点名节与词数。

    `title` **不判**：它天然很短，且它的作用是标识而不是论述。空节已由
    `validate_manuscript` 的「八键齐备」判掉；本条抓的是「写了一个词就当写完了」。
    """
    thin: list[str] = []
    for key, text in sections.items():
        if key == "title":
            continue
        count = len(_WORD.findall(str(text or "")))
        if count < minimum:
            thin.append(f"{key}({count}<{minimum})")
    if thin:
        raise ManuscriptQualityError(
            f"these sections are too thin to carry their part of the argument: {', '.join(thin)}"
        )


@dataclass(frozen=True, slots=True)
class ManuscriptQuality:
    """一次品质判据的**输入面**（参考文献的标题，按 References 顺序）。

    传的是 `Sequence[str]` 而不是 `ReferenceTable`：本模块**不依赖**手稿模块（避免循环
    依赖），也不解析元数据 —— 它只要「第 n 条叫什么」。
    """

    titles: tuple[str, ...]

    @classmethod
    def of(cls, entries: Sequence[object]) -> "ManuscriptQuality":
        """从 `ReferenceTable.entries` 取标题（每条一个 `title` 属性；缺失 ⇒ 空串）。"""
        return cls(tuple(str(getattr(entry, "title", "") or "") for entry in entries))


def validate_quality(sections: Mapping[str, str], quality: ManuscriptQuality) -> None:
    """三条判据**依次**跑（每条各自点名；第一条不过就停 —— 后面的结论会被它污染）。"""
    check_citation_alignment(sections, quality.titles)
    check_section_distinctness(sections)
    check_section_depth(sections)


__all__ = [
    "MIN_SECTION_WORDS",
    "NOT_JUDGED",
    "STOPWORDS",
    "ManuscriptQuality",
    "ManuscriptQualityError",
    "check_citation_alignment",
    "check_section_depth",
    "check_section_distinctness",
    "content_words",
    "validate_quality",
]
