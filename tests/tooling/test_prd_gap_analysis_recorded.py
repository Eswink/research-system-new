"""EC-07：PRD 差距分析**落树且被登记**，每条结论带仓库内 `file:line` 证据。

**它补哪一格**：`docs/product/PRD_GAP_ANALYSIS.md` 是 GOAL-20261119-115 的调研交付物；
没有判据时，把四节删掉、或把 `docs/INDEX.md` 的登记行去掉，全仓不会有任何东西变红。

**判什么**（缺一即红）：

1. 文件在树，且四节齐全（市面对照 / PRD 缺口 / 科研 agent 不足 / 优先级）；
2. 至少 20 条 `path:line` 形态的仓库内引用 —— **去重后**计数（同一行引两次不算两条）；
3. 文末有「来源」节（外部对照的口径必须可追）；
4. `docs/INDEX.md` 登记了该路径；
5. 非 ZDR 的接入事实**写在这一页里**（GOAL 正文的硬要求：`iceman-contributor-free`
   的 prompt 会用于改进模型这件事必须与产品声明一起被读到）。

**反证臂**：把引用计数压到 0 ⇒ 判红；把「来源」节标题改掉 ⇒ 判红。
"""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DOC = "docs/product/PRD_GAP_ANALYSIS.md"
_INDEX = "docs/INDEX.md"

#: 四节各自的语义关键词（标题是 `## <编号>. <标题>`，按**内容**匹配而不是逐字）。
_SECTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("market-comparison", ("定位差异", "市面")),
    ("prd-gap", ("PRD 缺口", "缺口")),
    ("research-agent-gaps", ("不足",)),
    ("priority", ("优先级",)),
)

#: `path/to/file.ext:LINE` 或 `path/to/file.ext:L1-L2`（可选反引号由正则两侧容忍）。
_CITATION = re.compile(r"[A-Za-z0-9_./-]+\.(?:py|ts|tsx|yaml|yml|json|md|toml):\d+(?:-\d+)?")


def _doc() -> str:
    return (_ROOT / _DOC).read_text(encoding="utf-8")


def _index() -> str:
    return (_ROOT / _INDEX).read_text(encoding="utf-8")


def citations(text: str) -> set[str]:
    """仓库内 `file:line` 引用（**去重**：同一处引两次算一条）。"""
    return set(_CITATION.findall(text))


def sections(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith("## ")]


class TestTheDocumentIsInTreeAndRegistered:
    def test_the_document_exists(self) -> None:
        assert (_ROOT / _DOC).is_file(), f"{_DOC} 不在树"

    def test_the_index_registers_it(self) -> None:
        assert _DOC.removeprefix("docs/") in _index() or _DOC in _index(), (
            f"{_INDEX} 没有登记 {_DOC}"
        )

    def test_the_four_sections_are_present(self) -> None:
        headings = sections(_doc())
        missing = [
            label
            for label, keywords in _SECTIONS
            if not any(any(word in heading for word in keywords) for heading in headings)
        ]
        assert not missing, f"缺节：{missing}（现有：{headings}）"

    def test_the_source_section_is_last(self) -> None:
        headings = sections(_doc())
        assert headings, "文档没有任何二级标题"
        assert "来源" in headings[-1], f"最后一节必须是来源，实得 {headings[-1]!r}"


class TestTheEvidenceIsNonVacuous:
    def test_at_least_twenty_distinct_citations(self) -> None:
        found = citations(_doc())
        assert len(found) >= 20, f"只有 {len(found)} 条去重后的 file:line 引用（要求 ≥20）"

    def test_the_non_zdr_fact_is_stated_here(self) -> None:
        """GOAL 正文的硬要求：非 ZDR 的接入事实必须能与产品声明一起读到。"""
        text = _doc()
        assert "iceman-contributor-free" in text, "没有点名非 ZDR 的那个模型"
        assert "ZDR" in text, "没有把「非 ZDR」这条事实写出来"

    def test_the_document_does_not_claim_the_gaps_are_solved(self) -> None:
        """如实边界：这一页写的是**差在哪**，不是"已经补上了"。"""
        assert "声称边界" in _doc(), "缺「声称边界」一节"
        assert "不宣称" in _doc(), "声称边界必须包含「不宣称」类表述"


class TestTheCriterionBitesInBothDirections:
    def test_a_document_without_citations_is_refused(self) -> None:
        stripped = _CITATION.sub("file.py", _doc())
        assert citations(stripped) == set()

    def test_a_doc_with_renamed_source_section_is_refused(self) -> None:
        text = _doc().replace("## 6. 来源", "## 6. 附录")
        assert "来源" not in sections(text)[-1], sections(text)[-1]
