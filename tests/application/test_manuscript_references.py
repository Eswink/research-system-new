"""GOAL-20261028-099 EC-03：**真参考文献表**从落盘的工具结果字节里读出来。

**它补哪一格**：报告此前把来源渲染成 Python 的 `dict` 字面量
（`- {'identifier': '39000001', 'evidence_id': 'ev-1', 'title': '…'}`）—— 那不是一条
参考文献。而元数据**早已取到却从未被用**：Europe PMC 解析出
`pmid/doi/title/journal/year/authorString`、NCBI 解析出 `pmid/title/abstract/journal/year/authors`，
整份 tool-result JSON 已落盘。本文件把「每个字段都来自落盘字节」变成机械事实。

**三向判据**（缺一即判红）：

(ii) **完整元数据夹具 ⇒ 每行都有作者 / 年 / 刊名**，且两种作者形态（NCBI 的
     `authors[]` 列表、Europe PMC 的 `authorString` 整串）各自渲染成同一形状；
(ii) **缺 `authors` ⇒ 点名「哪一条缺什么」**，**不静默填占位符**；
(iii) **反证**：换回旧的 dict-repr 渲染 ⇒ 判据判红（那行没有作者/年/刊名，
     也不匹配编号形态）；改制品 `year` ⇒ 表随之变（表真的读字节）。

**两向按压**：`reference_table` 若把 `authorString` 分支删掉 ⇒ 4 条判据判红并点名；
若把缺失分支改成填 `"Unknown"` ⇒ 缺失判据判红。两处都按 raw `sha256` 逐字节复原。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from adapters.fakes.artifact_store import FakeArtifactStore
from packages.application.deliverable.references import (
    MAX_AUTHORS,
    ReferenceEntry,
    ReferenceError,
    ReferenceTable,
    citation_mark,
    reference_table,
    render_references,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from packages.domain.enums import ArtifactState
from packages.domain.evidence import Evidence

_ROOT = Path(__file__).resolve().parents[2]
_REFERENCES = _ROOT / "packages" / "application" / "deliverable" / "references.py"

#: 渲染里**不得出现**的占位符词表（`fix_policy.forbidden`：补造缺失的作者/年份）。
#: 判据落在这一面是**结构判据**：它不依赖「缺失计数」那个量 —— 那个量会被「填一个
#: 占位符」同时改掉（本轮按压实测：填 `Unknown` 会让 missing 变空 ⇒ 判据自己沉默）。
PLACEHOLDER_TOKENS: tuple[str, ...] = ("Unknown", "N/A", "n.d.", "Anonymous", "TBD")

#: NCBI efetch 形态（`authors` 是**列表**）—— 取自 `adapters/research_tools/parsing.py` 的输出形状。
_NCBI_RECORD: dict[str, Any] = {
    "pmid": "39284801",
    "title": "ENCORE: a practical implementation to improve reproducibility",
    "abstract": "…",
    "journal": "Nat Commun",
    "year": "2024",
    "authors": ["Hoffmann C", "Djerroud S"],
}
#: Europe PMC search 形态（`authorString` 是**整串**）—— 取自 `europe_pmc_parsing.py` 的形状。
_EUROPE_PMC_RECORD: dict[str, Any] = {
    "pmid": "40601758",
    "doi": "10.1371/journal.pcbi.1013215",
    "title": "Fundamentals of FAIR biomedical data analyses in the cloud",
    "journal": "PLoS Comput Biol",
    "year": "2025",
    "author_string": "Kanitz A, Gursoy G, et al.",
}


def _store_with(
    payload: dict[str, Any], artifact_id: str = "tool-result:search"
) -> tuple[Any, tuple[Evidence, ...]]:
    """种入一份 tool-result 制品 + 一条工具证据（读面只认 `tool:` 前缀）。"""
    store = FakeArtifactStore()
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
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
    store.put(artifact, content)
    store.mark(artifact_id, ArtifactState.VERIFIED)
    evidence = Evidence(
        id=f"evidence:{artifact_id}",
        source_ref=f"tool:europe_pmc:literature.read:{artifact_id}",
        content_digest=str(artifact.digest),
        extracted_by="system:tool-evidence",
        artifact_id=artifact_id,
        run_id="r1",
    )
    return store, (evidence,)


def _tool_result(*records: dict[str, Any]) -> dict[str, Any]:
    return {"query": "q", "count": len(records), "ids": [], "articles": list(records)}


# --- (i) 完整元数据：每行都有作者 / 年 / 刊名，两种作者形态都认 -----------------


def test_a_complete_record_renders_authors_year_and_journal() -> None:
    """(i) 完整元数据 ⇒ 那一条**三样都有**（不是「字段在 JSON 里但表里没有」）。"""
    store, evidence = _store_with(_tool_result(_NCBI_RECORD))
    table = reference_table(store, evidence)
    assert table.complete, table.problems
    entry = table.entries[0]
    assert entry.authors == ("Hoffmann C", "Djerroud S")
    assert entry.year == "2024"
    assert entry.journal == "Nat Commun"
    line = table.markdown()
    assert "Hoffmann C, Djerroud S." in line
    assert "Nat Commun." in line
    assert "2024." in line


def test_the_europe_pmc_author_string_shape_renders_the_same_way() -> None:
    """(i) Europe PMC 的 `authorString`（**整串**）渲染成与 NCBI 列表同一形状。

    这是本轮最容易写错的一处：**只处理一种形态**会在另一种形态上静默丢掉作者，
    而那条判据在单一形态的夹具里会**假绿**（真实字节里两种都有 —— 见证据文件
    `.cursor/plans/goals/evidence/GOAL-20261028-099-ec03-metadata-census.txt`：
    6 条列表形态、4 条整串形态）。
    """
    store, evidence = _store_with(_tool_result(_EUROPE_PMC_RECORD))
    table = reference_table(store, evidence)
    assert table.complete, table.problems
    entry = table.entries[0]
    assert entry.authors == ("Kanitz A", "Gursoy G", "et al.")
    assert "Kanitz A, Gursoy G, et al.." in table.markdown() or (
        "Kanitz A, Gursoy G, et al." in table.markdown()
    )


def test_both_shapes_in_one_payload_each_render() -> None:
    """(i) 同一份 payload 里两种形态并存 ⇒ **两条都**有作者（不是只认第一条）。"""
    store, evidence = _store_with(_tool_result(_NCBI_RECORD, _EUROPE_PMC_RECORD))
    table = reference_table(store, evidence)
    assert len(table.entries) == 2
    assert all(entry.authors for entry in table.entries), [e.authors for e in table.entries]
    assert table.complete, table.problems


def test_a_long_author_list_is_truncated_visibly() -> None:
    """(i) 作者超过上限 ⇒ 前 N 位 + `et al`（**明示**截断，不是悄悄丢掉）。"""
    many = dict(_NCBI_RECORD)
    many["authors"] = [f"Author{chr(65 + index)} X" for index in range(MAX_AUTHORS + 2)]
    store, evidence = _store_with(_tool_result(many))
    entry = reference_table(store, evidence).entries[0]
    assert len(entry.authors) == MAX_AUTHORS + 2  # 条目保留全部（渲染时才截）
    assert "et al" in entry.vancouver()
    shown = entry.vancouver().split(".")[0]
    assert shown.count(",") <= MAX_AUTHORS


# --- (ii) 缺 authors ⇒ 点名，不静默填 ---------------------------------------


def test_a_record_without_authors_is_named_not_filled() -> None:
    """(ii) 缺 `authors` ⇒ `problems` 点名**哪一条缺什么**；**不**出现占位符。"""
    no_authors = {key: value for key, value in _NCBI_RECORD.items() if key != "authors"}
    store, evidence = _store_with(_tool_result(no_authors))
    table = reference_table(store, evidence)
    assert not table.complete
    assert table.entries, "缺作者不该把整条记录丢掉（它是可定位的一条）"
    assert table.problems == ("39284801: missing authors",), table.problems
    rendered = render_references(table)
    assert "missing authors" in rendered
    assert "Unknown" not in rendered and "unknown" not in rendered
    assert "N/A" not in rendered and "n.d." not in rendered


def test_a_record_without_a_journal_names_the_journal() -> None:
    """(ii) 缺 `journal` ⇒ 点名它（每一条缺失各自点名，不合并成一句「不完整」）。"""
    no_journal = {key: value for key, value in _EUROPE_PMC_RECORD.items() if key != "journal"}
    store, evidence = _store_with(_tool_result(no_journal))
    table = reference_table(store, evidence)
    assert table.problems == ("40601758: missing journal",), table.problems


def test_two_missing_fields_are_both_named() -> None:
    """(ii) 同时缺两个 ⇒ 两个都点名（`missing authors, year`）。"""
    stripped = {key: value for key, value in _NCBI_RECORD.items() if key not in {"authors", "year"}}
    store, evidence = _store_with(_tool_result(stripped))
    table = reference_table(store, evidence)
    assert table.problems == ("39284801: missing authors, year",), table.problems


def test_a_record_without_an_identifier_is_not_citable() -> None:
    """标识都缺 ⇒ 它不是一条可引用的来源（计入 `skipped`，不进表）。"""
    anonymous = {"title": "no identifier", "journal": "J", "year": "2020", "authors": ["X Y"]}
    store, evidence = _store_with(_tool_result(anonymous))
    table = reference_table(store, evidence)
    assert table.entries == ()
    assert table.skipped == 1
    assert "not citable" in render_references(table)


def test_the_ids_only_shape_yields_no_references() -> None:
    """`ids[]` 形态（esearch 命中列表）**没有元数据** ⇒ 不产出条目，也不报缺失。"""
    store, evidence = _store_with({"query": "q", "count": 2, "ids": ["111", "222"]})
    table = reference_table(store, evidence)
    assert table.entries == ()
    assert table.problems == ()
    assert table.skipped == 0


# --- (iii) 两向反证 ---------------------------------------------------------


def test_changing_the_artifact_year_changes_the_reference_line() -> None:
    """(iii) 改**制品字节**的 `year` ⇒ 表随之变（表真的读制品，不是写死的）。"""
    store, evidence = _store_with(_tool_result(_NCBI_RECORD))
    before = reference_table(store, evidence).markdown()
    assert "2024." in before
    changed = dict(_NCBI_RECORD)
    changed["year"] = "1999"
    store2, evidence2 = _store_with(_tool_result(changed))
    after = reference_table(store2, evidence2).markdown()
    assert "1999." in after
    assert "2024." not in after


def test_changing_the_artifact_journal_changes_the_reference_line() -> None:
    """(iii) 改 `journal` ⇒ 表随之变（同一向判据的第二个字段，防「只有 year 是活的」）。"""
    store, evidence = _store_with(_tool_result(_NCBI_RECORD))
    changed = dict(_NCBI_RECORD)
    changed["journal"] = "Some Other Journal"
    store2, evidence2 = _store_with(_tool_result(changed))
    assert "Some Other Journal." in reference_table(store2, evidence2).markdown()
    assert "Some Other Journal." not in reference_table(store, evidence).markdown()


def test_the_legacy_dict_repr_line_is_not_a_reference() -> None:
    """(iii) **反证**：旧的 dict-repr 行不满足本判据的三条事实。

    旧形态（本轮消灭的那一个）：`- {'identifier': '39284801', 'evidence_id': 'ev-1'}`。
    它没有作者、没有刊名、没有年份，也不匹配 References 的编号形态 ⇒ 判据点名判红。
    """
    legacy_line = f"- {dict({'identifier': '39284801', 'evidence_id': 'ev-1'})}"
    assert legacy_line.startswith("- {'identifier'")
    for fact in ("authors", "journal", "year"):
        assert fact not in legacy_line
    # 编号形态（判据用来做「正文 [n] ↔ References 逐条映射」的那一侧）也不成立。
    import re

    assert re.match(r"^\d+\. ", legacy_line) is None
    # 而真正的表行两条都成立。
    store, evidence = _store_with(_tool_result(_NCBI_RECORD))
    real = reference_table(store, evidence).markdown().splitlines()[-1]
    assert re.match(r"^\d+\. ", real) is not None
    assert "Nat Commun." in real and "2024." in real


def test_citation_marks_are_numbered_from_one() -> None:
    """引用标记的唯一构造点：`[1]`…`[n]`，与 References 的编号**同一编号**。"""
    store, evidence = _store_with(_tool_result(_NCBI_RECORD, _EUROPE_PMC_RECORD))
    table = reference_table(store, evidence)
    assert table.marks() == ("[1]", "[2]")
    assert citation_mark(1) == "[1]"
    with pytest.raises(ReferenceError):
        citation_mark(0)


def test_the_table_is_deterministic_and_deduplicated() -> None:
    """同一份字节 ⇒ 同一张表；同一标识出现两次 ⇒ 只有一条（去重按标识）。"""
    store, evidence = _store_with(_tool_result(_NCBI_RECORD, _NCBI_RECORD))
    first = reference_table(store, evidence)
    second = reference_table(store, evidence)
    assert first == second
    assert len(first.entries) == 1


def test_a_non_tool_source_is_not_a_reference() -> None:
    """只认 `tool:` 前缀的工具证据（声明输入 / 自产件都不是检索来源）。"""
    store, evidence = _store_with(_tool_result(_NCBI_RECORD))
    foreign = Evidence(
        id="evidence:declared",
        source_ref="examples/config/roles.yaml",
        content_digest=str(evidence[0].content_digest),
        extracted_by="system:run-input",
        artifact_id="tool-result:search",
        run_id="r1",
    )
    assert reference_table(store, (foreign,)).entries == ()


def test_an_empty_table_still_writes_the_section() -> None:
    """空表也写出 `## References` + 一行说明（**不省略该节**：节的存在是契约的一部分）。"""
    rendered = render_references(ReferenceTable(entries=()))
    assert rendered.startswith("## References")
    assert "No citable record" in rendered


# --- 两向按压（真文件）------------------------------------------------------


def _restore(path: Path, original: bytes, digest: str) -> None:
    path.write_bytes(original)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, "press restore failed"


def test_dropping_the_author_string_branch_turns_the_judges_red() -> None:
    """按压：删掉 `authorString` 分支 ⇒ 整串形态的作者**静默丢失** ⇒ 判据必须咬住。

    「静默丢失」的形态是：`authors == ()` 且**没有** `problems`（因为那是另一种形态，
    不是「缺失」）。这正是最危险的假绿：表看着有作者位，实际空着。
    """
    original = _REFERENCES.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    text = original.decode("utf-8")
    branch = '    text = _text(article, "author_string")\n'
    assert branch in text, "author_string branch not found"
    pressed = text.replace(branch, "    text = ''\n", 1).encode("utf-8")
    assert hashlib.sha256(pressed).hexdigest() != digest
    try:
        _REFERENCES.write_bytes(pressed)
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location("references_pressed", _REFERENCES)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules["references_pressed"] = module
        spec.loader.exec_module(module)
        store, evidence = _store_with(_tool_result(_EUROPE_PMC_RECORD))
        table = module.reference_table(store, evidence)
        assert table.entries[0].authors == (), (
            "the pressed module still read authorString — the press did not take effect"
        )
        assert "missing authors" in " ".join(table.problems), table.problems
    finally:
        _restore(_REFERENCES, original, digest)
    restored = reference_table(*_store_with(_tool_result(_EUROPE_PMC_RECORD))[0:2])
    assert "Kanitz A" in restored.markdown()


def test_no_placeholder_token_ever_reaches_the_rendered_table() -> None:
    """**结构判据**：渲染输出里一个占位符都没有（真实模块 —— 不是按压里的那一份）。

    这一条独立于「缺失计数」那个量：填一个占位符会让缺失计数变空，**不会**让这一条变绿
    —— 它看的是产物里的字面。两种夹具都判（完整 / 缺失），两向都不许出现占位符。
    """
    no_authors = {key: value for key, value in _NCBI_RECORD.items() if key != "authors"}
    for records in (
        (_NCBI_RECORD,),
        (no_authors,),
        (_NCBI_RECORD, _EUROPE_PMC_RECORD),
        (),
    ):
        rendered = render_references(reference_table(*_store_with(_tool_result(*records))[0:2]))
        offenders = [token for token in PLACEHOLDER_TOKENS if token in rendered]
        assert not offenders, (record_ids(records), offenders, rendered)


def record_ids(records: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    """夹具的标识（判词里点名是哪一组夹具失败）。"""
    return tuple(str(item.get("pmid") or item.get("doi") or "?") for item in records)


def test_a_reference_entry_rejects_an_empty_paper() -> None:
    """一条没有作者的条目渲染出来就**不是**一条完整引用（结构事实，不是风格）。"""
    entry = ReferenceEntry(identifier="1", authors=(), title="T", journal="J", year="2020")
    assert entry.vancouver().startswith(".")


def test_filling_a_placeholder_is_visible_in_the_rendered_table() -> None:
    """按压：缺失时填 `"Unknown"` ⇒ 渲染里出现占位符 ⇒ **结构判据**咬住。

    **这一条是本轮最有价值的按压**（第一次写时它**假绿**了，如实记录）：把
    `fields["authors"] = fields["authors"] or ("Unknown",)` 插进 `_entry_of` 之后，
    `missing` 变空 ⇒ **「点名缺失」那条判据自己沉默了** —— 因为判据与被防的动作
    改的是同一个量。这正是 `fix_policy.forbidden` 点名的「补造缺失的作者/年份」：
    它让表看起来完整，同时让判据闭嘴。

    ⇒ 判据因此分成两层：`problems`（点名缺失）**与**「渲染里没有占位符词」
    （`test_no_placeholder_token_ever_reaches_the_rendered_table`）。按压证明后者
    在违规形态下**真的红**；前者在真实模块上点名缺失。
    """
    original = _REFERENCES.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    text = original.decode("utf-8")
    anchor = "    missing = tuple(name for name in REQUIRED_FIELDS if not fields[name])\n"
    assert anchor in text, "missing-field anchor not found"
    pressed = text.replace(
        anchor,
        '    fields["authors"] = fields["authors"] or ("Unknown",)\n'
        "    missing = tuple(name for name in REQUIRED_FIELDS if not fields[name])\n",
        1,
    ).encode("utf-8")
    try:
        _REFERENCES.write_bytes(pressed)
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location("references_filled", _REFERENCES)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules["references_filled"] = module
        spec.loader.exec_module(module)
        no_authors = {key: value for key, value in _NCBI_RECORD.items() if key != "authors"}
        pressed_text = module.render_references(
            module.reference_table(*_store_with(_tool_result(no_authors))[0:2])
        )
        offenders = [token for token in PLACEHOLDER_TOKENS if token in pressed_text]
        assert offenders, (
            "the pressed module filled a placeholder but the rendered text shows none — "
            "the press did not take effect, or the structural judge cannot see it"
        )
        # 而**真实**模块的产物里一个占位符都没有，且缺失逐条点名。
        real_text = render_references(reference_table(*_store_with(_tool_result(no_authors))[0:2]))
        assert not any(token in real_text for token in PLACEHOLDER_TOKENS), real_text
        assert "39284801: missing authors" in real_text
    finally:
        _restore(_REFERENCES, original, digest)
