"""**参考文献表**：从本 run 的工具结果字节里读出元数据，渲染成 Vancouver 风格的一条一引。

**它补哪一格**（GOAL-20261028-099 EC-03，建档实测）：报告此前把来源渲染成 Python 的
`dict` 字面量（`research_report.py` 的 `f"- {dict(item)}"` ⇒
`- {'identifier': '39000001', 'evidence_id': 'ev-1', 'title': '...'}`）—— 那是**调试形态**，
不是参考文献。而**元数据早已取到却从未被用**：Europe PMC 解析出
`pmid/doi/title/journal/year/authorString`（`adapters/research_tools/europe_pmc_parsing.py`）、
NCBI 解析出 `pmid/title/abstract/journal/year/authors`（`adapters/research_tools/parsing.py`），
整份 tool-result JSON 已落盘，但 `.get("journal")` / `.get("year")` / `.get("authors")`
在应用层**零命中**，`SourceRecord.authors` 恒空。

**两种作者形态都认**（这是本轮最容易写错的一处，两份真实解析器的形状不同）：

- NCBI efetch：`authors` 是**列表**（`["Hoffmann C", ...]`）；
- Europe PMC search：`authorString` 是**整串**（`"Hoffmann C, Djerroud S, et al."`）。

**缺失 ⇒ 点名，不猜占位符**。缺失分三类，判词各不相同：

1. `journal` / `year` 缺 ⇒ 那一条**不完整**，进 `problems`（不写 `[unknown journal]`
   之类的假占位符 —— 读者会把占位符读成一个真值）；
2. `authors` 缺 ⇒ 同上，`problems` 点名**哪一条缺什么**；
3. 整条记录连标识都没有 ⇒ 它不是一条可引用的来源（上游抽取面已挡，这里再挡一次）。

**零出网 / 零模型 / 零时钟**：输入只有本 run 已落库的 tool-result 字节，输出是纯文本。

**如实边界**：本模块**不判**「这条文献真的支持那句话」（引用相关性），也**不**去外部
补全元数据（那会出网）。它判的是「这段引用的每个字段都来自落盘字节」。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

#: 引用的**编号形态**（`[1]`、`[12]`）——正文里模型只许写这个。
CITATION_MARK_OPEN = "["
CITATION_MARK_CLOSE = "]"

#: 一条参考文献里**必须有**的三个字段（缺任何一个 ⇒ 点名，不猜占位符）。
REQUIRED_FIELDS: tuple[str, ...] = ("authors", "title", "journal", "year")

#: 作者列表超过这个条数就截断成 `et al.`（Vancouver 的常见约定；判据据此可复核）。
MAX_AUTHORS = 6


class ReferenceError(RuntimeError):
    """参考文献表不可用（缺必填字段 / 记录畸形）—— **点名**，不静默填占位符。"""


@dataclass(frozen=True, slots=True)
class ReferenceEntry:
    """一条参考文献（字段全部**逐字**来自落盘的工具结果字节）。"""

    identifier: str
    authors: tuple[str, ...]
    title: str
    journal: str
    year: str
    doi: str = ""
    pmid: str = ""

    def vancouver(self) -> str:
        """Vancouver 风格的一行：`Authors. Title. Journal. Year. doi:… PMID:…`。

        作者形态：`<= MAX_AUTHORS` 全列；更多则前 `MAX_AUTHORS` 位 + `et al.`
        （截断是**渲染约定**，不是把作者「补造」出来 —— 少的那几位以 `et al.` 明示）。
        """
        authors = self._authors_text()
        parts = [f"{authors}.", f"{self.title.rstrip('.')}.", f"{self.journal}."]
        if self.year:
            parts.append(f"{self.year}.")
        ids: list[str] = []
        if self.doi:
            ids.append(f"doi:{self.doi}")
        if self.pmid:
            ids.append(f"PMID:{self.pmid}")
        if ids:
            parts.append(" ".join(ids))
        return " ".join(parts)

    def _authors_text(self) -> str:
        shown = self.authors[:MAX_AUTHORS]
        text = ", ".join(shown)
        if len(self.authors) > MAX_AUTHORS:
            return f"{text}, et al"
        return text


@dataclass(frozen=True, slots=True)
class ReferenceTable:
    """一次装配的结果：逐条文献 + 逐条**点名**的缺失（缺件不是静默）。"""

    entries: tuple[ReferenceEntry, ...]
    #: 逐条缺失说明（`identifier: missing authors, journal`）。空 = 全部完整。
    problems: tuple[str, ...] = ()
    #: 被跳过的记录数（畸形 / 无标识）—— 与 `problems` 分开：那是「读不全」，这是「不是条目」。
    skipped: int = 0

    @property
    def complete(self) -> bool:
        """每一条都字段齐备（判据用它判「完整元数据夹具」那一臂）。"""
        return bool(self.entries) and not self.problems

    def marks(self) -> tuple[str, ...]:
        """正文允许出现的引用标记（`[1]`…`[n]`；n = 条目数）。"""
        return tuple(
            f"{CITATION_MARK_OPEN}{index}{CITATION_MARK_CLOSE}"
            for index in range(1, len(self.entries) + 1)
        )

    def markdown(self) -> str:
        """`## References` 那一节（编号从 1 起，与 `marks()` **同一编号**）。

        空表也写出表头 + 一行说明（**不省略该节**：节的存在本身是契约的一部分）。
        """
        lines = ["## References", ""]
        if not self.entries:
            lines.append(
                "_No citable record: this run's tool results carry no bibliographic entry._"
            )
            return "\n".join(lines)
        lines += [
            f"{index}. {entry.vancouver()}" for index, entry in enumerate(self.entries, start=1)
        ]
        return "\n".join(lines)


def reference_table(artifacts: Any, evidence: tuple[Any, ...]) -> ReferenceTable:
    """本 run 的**工具证据** → 参考文献表（只读 canonical；零出网）。

    读法与 `report_facts.sources_of` **同一处来源**（tool-result 制品的 `articles[]`），
    但抽取的字段不同：那边只需要「标识 + 标题」，这里要作者 / 年 / 刊名。
    两处不合并成一个函数是有意的 —— 那边被既有判据逐字钉住（字形一变它先红），
    这边的字段集是本轮新增的；合并会让「改一处、两个面一起变」。
    """
    entries: list[ReferenceEntry] = []
    problems: list[str] = []
    skipped = 0
    seen: set[str] = set()
    for item in evidence:
        artifact_id = getattr(item, "artifact_id", None)
        if not artifact_id or not str(item.source_ref).startswith("tool:"):
            continue
        for raw in _articles(artifacts, artifact_id):
            identifier = _identifier_of(raw)
            if not identifier:
                skipped += 1
                continue
            if identifier in seen:
                continue
            seen.add(identifier)
            entry, missing = _entry_of(raw, identifier)
            if missing:
                problems.append(f"{identifier}: missing {', '.join(missing)}")
            entries.append(entry)
    return ReferenceTable(entries=tuple(entries), problems=tuple(problems), skipped=skipped)


def _articles(artifacts: Any, artifact_id: str) -> tuple[Mapping[str, Any], ...]:
    """tool-result 制品 → 逐条记录（两种既有形状：`articles[]` 与 `ids[]`）。

    `ids[]`（esearch 的命中列表）**没有元数据** —— 它们不是可引用的条目，返回空、
    由调用方如实处置（`skipped` 不因它们增加：那不是「畸形」，是「这一步只给了 id」）。
    """
    if artifacts.meta(artifact_id) is None:
        return ()
    try:
        parsed: Any = json.loads(artifacts.get(artifact_id).decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return ()
    if not isinstance(parsed, Mapping):
        return ()
    articles = parsed.get("articles")
    if not isinstance(articles, list):
        return ()
    return tuple(item for item in articles if isinstance(item, Mapping))


def _identifier_of(article: Mapping[str, Any]) -> str:
    """单条记录的主标识（PMID 优先、退化到 DOI；都缺 ⇒ 空串）。"""
    for key in ("pmid", "doi"):
        value = article.get(key)
        if value:
            return str(value)
    return ""


def _text(article: Mapping[str, Any], key: str) -> str:
    """标量 → 去空白字符串（None / 非标量 ⇒ 空串；不猜、不编造）。"""
    value = article.get(key)
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    return ""


def _authors(article: Mapping[str, Any]) -> tuple[str, ...]:
    """两种作者形态 → 元组（NCBI 的 `authors` 列表 / Europe PMC 的 `authorString` 整串）。

    **两种都要处理**（本轮建档实测：两份解析器给出的形状不同）。空列表 / 空白串 ⇒ `()`，
    由 `_entry_of` 计入缺失（**不**用 `["Unknown"]` 之类的占位符顶上）。
    """
    listed = article.get("authors")
    if isinstance(listed, list):
        names = tuple(str(item).strip() for item in listed if str(item).strip())
        if names:
            return names
    text = _text(article, "author_string")
    if not text:
        return ()
    return tuple(part.strip() for part in text.split(",") if part.strip())


def _entry_of(
    article: Mapping[str, Any], identifier: str
) -> tuple[ReferenceEntry, tuple[str, ...]]:
    """单条记录 → （条目, 缺失字段名）。**缺失不阻止条目存在** —— 它进 `problems`。

    为什么不直接抛：一份「全部完整」的夹具与一份「缺作者」的夹具都要能渲染出表 ——
    判据的两向臂（完整 / 缺失）判的是**同一条渲染路径**，若缺失即抛，第二臂就只能判
    「抛了」，判不到「表里少了什么、点名说了什么」。
    """
    fields = {
        "authors": _authors(article),
        "title": _text(article, "title"),
        "journal": _text(article, "journal"),
        "year": _text(article, "year"),
    }
    missing = tuple(name for name in REQUIRED_FIELDS if not fields[name])
    entry = ReferenceEntry(
        identifier=identifier,
        authors=fields["authors"] if isinstance(fields["authors"], tuple) else (),
        title=str(fields["title"]),
        journal=str(fields["journal"]),
        year=str(fields["year"]),
        doi=_text(article, "doi"),
        pmid=_text(article, "pmid"),
    )
    return entry, missing


def render_references(table: ReferenceTable) -> str:
    """参考文献表的 markdown（`## References` + 逐条编号）。

    缺失**逐条点名**写在表后（判据据此判「不静默填」）：一条完整表里出现那段
    说明就是 bug，一条缺失表里**没有**那段说明也是 bug。
    """
    text = table.markdown()
    if table.problems:
        text += "\n\n_Records with incomplete metadata (named, not filled in):_\n"
        text += "\n".join(f"- {item}" for item in table.problems)
    if table.skipped:
        text += f"\n\n_{table.skipped} record(s) carried no identifier and are not citable._"
    return text


def citation_mark(index: int) -> str:
    """正文里的引用标记（**唯一**构造点：编号形态只在这里定）。"""
    if index < 1:
        raise ReferenceError(f"citation index must be >= 1, got {index}")
    return f"{CITATION_MARK_OPEN}{index}{CITATION_MARK_CLOSE}"


__all__ = [
    "CITATION_MARK_CLOSE",
    "CITATION_MARK_OPEN",
    "MAX_AUTHORS",
    "REQUIRED_FIELDS",
    "ReferenceEntry",
    "ReferenceError",
    "ReferenceTable",
    "citation_mark",
    "reference_table",
    "render_references",
]
