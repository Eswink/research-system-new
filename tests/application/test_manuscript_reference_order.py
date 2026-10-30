"""GOAL-20261028-099 EC-03 的**编号顺序**判据（自 `test_manuscript_references.py` 拆出）。

**为什么单列**：那个文件贴着 450 行硬上限（规模门），而「编号 = 提示词里去重后首次出现
位置」这一组判据（含一条 63 行的用例）是**可独立读**的一件事：它判的是**编号与顺序**，
而母文件判的是**字段与渲染**。

**为什么必须有这一组**（本轮实测到的真缝）：检索链有**两步**（`literature.search` 与
`literature.read`），两步各落一份 tool-result 制品、内容重叠 ⇒ 模型看到的
"RETRIEVED SOURCES" 列表里**同一条会出现两次**，而 References 去重。
若编号按「列表位置」数，模型写出的 `[2]` 会越界被拒。⇒ 规则改成「去重后首次出现顺序」。
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from adapters.fakes.artifact_store import FakeArtifactStore
from packages.application.deliverable.references import (
    ReferenceEntry,
    ReferenceTable,
    reference_table,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from packages.domain.enums import ArtifactState
from packages.domain.evidence import Evidence

_NCBI_RECORD: dict[str, Any] = {
    "pmid": "39284801",
    "title": "ENCORE: a practical implementation to improve reproducibility",
    "abstract": "…",
    "journal": "Nat Commun",
    "year": "2024",
    "authors": ["Hoffmann C", "Djerroud S"],
}
_EUROPE_PMC_RECORD: dict[str, Any] = {
    "pmid": "40601758",
    "doi": "10.1371/journal.pcbi.1013215",
    "title": "Fundamentals of FAIR biomedical data analyses in the cloud",
    "journal": "PLoS Comput Biol",
    "year": "2025",
    "author_string": "Kanitz A, Gursoy G, et al.",
}


def _tool_result(*records: dict[str, Any]) -> dict[str, Any]:
    return {"query": "q", "count": len(records), "ids": [], "articles": list(records)}


_THIRD: dict[str, Any] = {
    "pmid": "41111111",
    "title": "A third record",
    "journal": "J Third",
    "year": "2023",
    "authors": ["Third T"],
}
_STORE = FakeArtifactStore()


def _evidence(artifact_id: str, records: tuple[dict[str, Any], ...]) -> Evidence:
    """种一份 tool-result 制品并返回它的工具证据（同一模块内共享一个 store）。"""
    content = json.dumps(_tool_result(*records), ensure_ascii=False, sort_keys=True).encode()
    artifact = Artifact(
        id=artifact_id,
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type="application/json",
        storage_uri=None,
        created_by="system:tool-registry",
        source_refs=["run:r1"],
        classification="tool_result",
    )
    _STORE.put(artifact, content)
    _STORE.mark(artifact_id, ArtifactState.VERIFIED)
    return Evidence(
        id=f"evidence:{artifact_id}",
        source_ref=f"tool:europe_pmc:literature.search:{artifact_id}",
        content_digest=str(artifact.digest),
        extracted_by="system:tool-evidence",
        artifact_id=artifact_id,
        run_id="r1",
    )


def test_the_mark_order_follows_the_prompt_order_with_duplicates_collapsed() -> None:
    """**编号顺序与提示词里模型看到的顺序一致**（重复出现的记录只占一个编号）。

    这是本轮实测到的一处真缝（记在 `## 残余与未覆盖范围`）：检索链有**两步**
    （search + read），两步的 tool-result 制品里都有同一批记录 ⇒ 模型看到的
    "RETRIEVED SOURCES" 列表里**同一条会出现两次**，而 References 去重 ⇒
    若编号按「列表位置」数，模型写的 `[2]` 会越界被拒。

    ⇒ 规则改成「首次出现顺序上的**去重后**位置」，并由本判据钉住：把两条证据
    （模拟 search 与 read 两个制品，内容重叠）喂进去，断言编号顺序 = 首次出现顺序、
    重复记录只占一个编号。
    """
    # 两条证据：第一条是 search（两条记录），第二条是 read（同样的两条 + 一条新的）。
    search = _evidence("tool-result:t1:literature_search", (_NCBI_RECORD, _EUROPE_PMC_RECORD))
    read = _evidence("tool-result:t1:literature_read", (_NCBI_RECORD, _EUROPE_PMC_RECORD, _THIRD))
    table = reference_table(_STORE, (search, read))
    # 去重：三条不同记录（不是五条列表项）。
    assert [entry.identifier for entry in table.entries] == ["39284801", "40601758", "41111111"]
    # 编号顺序 = 首次出现顺序（`[1]` 就是模型在列表里先看到的那条）。
    assert table.marks() == ("[1]", "[2]", "[3]")
    lines = table.markdown().splitlines()
    assert lines[2].startswith("1. ") and "Nat Commun" in lines[2]
    assert lines[3].startswith("2. ") and "PLoS Comput Biol" in lines[3]
    assert lines[4].startswith("3. ") and "J Third" in lines[4]


_BOUNDARY_TABLE = ReferenceTable(
    entries=(
        # 标题**不是占位符**：品质判据（GOAL-20261030-101 EC-01）要求被引条目与正文至少共享
        # 一个实词 ⇒ `T1` 这种两字符假标题会被**正确地**判红。故用真形状的标题，正文也换成
        # 能与它们对上的实词（benchmark / pipeline / workflow）。
        ReferenceEntry(
            identifier="1",
            authors=("A A",),
            title="A benchmark for reproducible pipeline work",
            journal="J1",
            year="2001",
        ),
        ReferenceEntry(
            identifier="2",
            authors=("B B",),
            title="Pipeline provenance in shared pipelines",
            journal="J2",
            year="2002",
        ),
        ReferenceEntry(
            identifier="3",
            authors=("C C",),
            title="Workflow benchmark across institutions",
            journal="J3",
            year="2003",
        ),
    )
)

#: 编号越界用例的正文。**各节互不相同**：摘要与结论若逐字相同，「节间不重复」判据会
#: **正确地**判红 —— 本用例判的是编号越界，故正文按节区分（引用标记三处齐全）。
_BOUNDARY_SECTIONS: dict[str, str] = {
    "title": "A Benchmark Study",
    "abstract": "We measure benchmark pipelines against their published workflows and report "
    "the comparison in a table rather than in this prose [1][2].",
    "introduction": "Prior work documents pipelines in detail but says little about the "
    "measured cost of running them under a shared procedure [3].",
    "related_work": "The closest benchmark pipelines report workflow costs for computational "
    "research and leave the planning choice open [1][2].",
    "methods": "Two arms run one benchmark pipeline under a fixed workflow so the comparison "
    "isolates only the item count [1].",
    "results": "The pipelines differ in measured cost, tabulated below by name so each value "
    "can be checked [1][2][3].",
    "discussion": "The difference is a workload effect and nothing more, because one script "
    "cannot speak for another [3].",
    "conclusion": "Whether the benchmark generalises beyond this run is not something this "
    "study measured, and we do not claim it [1].",
}


def test_a_mark_beyond_the_distinct_record_count_is_refused() -> None:
    """上面那条规则的另一半：编号只到**去重后**的条数 ⇒ 超出即点名拒绝。

    形态就是本轮实测到的那条缝：五条列表项 / 三条不同记录 ⇒ `[4]` 与 `[5]` 都必须被拒，
    否则模型会以为「列表里有第五条」而写出一个解析不到任何条目的标记。
    """
    from packages.application.deliverable.manuscript import (
        ManuscriptError,
        validate_manuscript,
    )

    table = _BOUNDARY_TABLE
    sections = dict(_BOUNDARY_SECTIONS)
    validate_manuscript(sections, table)  # 三条都引 ⇒ 通过
    beyond = dict(sections)
    beyond["results"] = "Benchmark pipelines measured [4]"
    with pytest.raises(ManuscriptError) as raised:
        validate_manuscript(beyond, table)
    assert "[4]" in str(raised.value), str(raised.value)
