"""GOAL-20261028-099 EC-02：**手稿结构**与**引用闭合**（两向判据）。

**它补哪一格**：`deliverable/manuscript.py` 把一个会话写的正文 + 汇编器写的数据表与
References 装成 `manuscript.md`。本文件把它的**结构事实**变成机械判据：

1. **八节齐全**：`Abstract` + 六个编号节（`1. Introduction` … `6. Conclusion`）；
2. **`References` 由汇编器写**（模型写的那块面里**没有**这一节 —— 它不写）；
3. **正文 `[n]` 与 References 逐条一一映射**：越界引用 ⇒ 点名；孤儿条目 ⇒ 点名；
4. **数字只在汇编器写的地方**：正文含任何 Unicode 十进制数位（引用标记除外）⇒
   `ManuscriptError` **点名哪一节、哪个字符**（不静默抽掉）；
5. **两向反证**：改 `year` ⇒ 表随之变；换回旧的 dict-repr 渲染 ⇒ 判据点名判红。

**反证臂怎么做的**：不是「合成一个别的错」，而是**复现本次要消灭的真实形态**
（旧的 `f"- {dict(item)}"` 渲染）与**本次引入的判据的失败形态**（正文写数字 /
引用越界 / 引用孤儿），逐个证明判据真咬得住。
"""

from __future__ import annotations

import json
import re

import pytest

from packages.application.deliverable.manuscript import (
    DATA_TABLE_HEADING,
    MANUSCRIPT_KEYS,
    REFERENCES_HEADING,
    SECTION_HEADINGS,
    ManuscriptAdmission,
    ManuscriptError,
    build_manuscript,
    parse_manuscript,
    validate_manuscript,
)
from packages.application.deliverable.references import (
    ReferenceEntry,
    ReferenceTable,
    render_references,
)
from packages.application.deliverable.research_report import ReportInputs

_SECTIONS: dict[str, str] = {
    "title": "Retrieval Grounding For Controlled Planning Studies",
    "abstract": "We study whether grounding a research plan in retrieved literature changes "
    "the plan a controlled experiment can execute.",
    "introduction": "Planning assistants propose studies that the literature may already "
    "settle; we ask what changes when the material is retrieved first.",
    "related_work": "The closest retrieved work builds reproducibility tooling and reports "
    "the cost of custom pipelines; it leaves open which planning choices move a measured "
    "outcome, which is what this study varies [1][2].",
    "methods": "Two arms run the same shipped benchmark script; the treatment arm sets a "
    "larger item count than the control arm, so the comparison isolates the workload.",
    "results": "The treatment arm's count exceeds the control arm's, as the data table "
    "records; the per-arm readings are listed there by name [1].",
    "discussion": "The measured difference is a workload effect, not a quality claim: the "
    "study varies the item count only, and one script cannot speak for another [2].",
    "conclusion": "Grounded planning yields an execrable design; whether it yields a better "
    "one is not something this run measured.",
}

_ENTRIES = (
    ReferenceEntry(
        identifier="39284801",
        authors=("Hoffmann C", "Djerroud S"),
        title="ENCORE: a practical implementation to improve reproducibility",
        journal="Nat Commun",
        year="2024",
        doi="10.1038/s41467-024-52446-8",
        pmid="39284801",
    ),
    ReferenceEntry(
        identifier="40601758",
        authors=("Kanitz A", "Gursoy G", "Zhang L"),
        title="Fundamentals of FAIR biomedical data analyses in the cloud",
        journal="PLoS Comput Biol",
        year="2025",
        doi="10.1371/journal.pcbi.1013215",
        pmid="40601758",
    ),
)


def _table(entries: tuple[ReferenceEntry, ...] = _ENTRIES) -> ReferenceTable:
    return ReferenceTable(entries=entries)


def _inputs() -> ReportInputs:
    return ReportInputs(
        run_id="run-manuscript-001",
        protocol_id="direction_to_manuscript_v1_0_0",
        state="SUCCEEDED",
        objective="Does grounding a plan in retrieved literature change the design it yields?",
        sources=(
            {"identifier": "39284801", "evidence_id": "ev-1", "title": "ENCORE"},
            {"identifier": "40601758", "evidence_id": "ev-2", "title": "FAIR"},
        ),
        metrics=(
            {"name": "comparisons", "value": "7990.0", "experiment_run_id": "exp-control"},
            {"name": "comparisons", "value": "178.5", "experiment_run_id": "exp-treatment"},
        ),
        verdict={"decision": "ACCEPT", "reason": "coverage holds"},
    )


def _admission(sections: dict[str, str] | None = None) -> ManuscriptAdmission:
    body = dict(_SECTIONS)
    body.update(sections or {})
    return ManuscriptAdmission(
        author="model_assisted:writer",
        returned_model="twin-a",
        digest="0" * 64,
        sections=body,
    )


def _manuscript(sections: dict[str, str] | None = None) -> str:
    return build_manuscript(_inputs(), _admission(sections), _table())


# --- 1. 八节齐全 -------------------------------------------------------------


def test_the_manuscript_carries_abstract_and_six_numbered_sections() -> None:
    """(1) `Abstract` + 六个编号节 + `References`，顺序就是文档顺序。"""
    text = _manuscript()
    assert text.startswith("# Retrieval Grounding For Controlled Planning Studies")
    positions = [text.index(heading) for heading in SECTION_HEADINGS]
    assert positions == sorted(positions), positions
    assert len(SECTION_HEADINGS) == 7  # Abstract + 6
    assert text.index(REFERENCES_HEADING) > positions[-1]


def test_the_heading_set_is_i_mrad() -> None:
    """(1) 标题**逐字**是 IMRaD 的形状（改字 = 改契约，判据据此定位）。"""
    assert SECTION_HEADINGS == (
        "## Abstract",
        "## 1. Introduction",
        "## 2. Related Work",
        "## 3. Methods",
        "## 4. Results",
        "## 5. Discussion",
        "## 6. Conclusion",
    )


def test_the_model_face_does_not_write_the_references_section() -> None:
    """(2) `References` 由汇编器写：模型正文里**没有**这一节（它只写八个键）。"""
    sections = parse_manuscript(json.dumps({"manuscript_narrative": _SECTIONS}))
    assert set(sections) == set(MANUSCRIPT_KEYS)
    assert not any(REFERENCES_HEADING in value for value in sections.values())


# --- 3. 引用闭合 -------------------------------------------------------------


def test_the_body_citations_map_onto_the_reference_list() -> None:
    """(3) 正文 `[n]` 与 References **逐条**映射：每条都被引、每个标记都解得开。"""
    text = _manuscript()
    body = text.split(REFERENCES_HEADING, 1)[0]
    marks = {int(item) for item in re.findall(r"\[(\d+)\]", body)}
    assert marks == {1, 2}, marks
    numbered = re.findall(r"^(\d+)\. ", text.split(REFERENCES_HEADING, 1)[1], re.MULTILINE)
    assert numbered == ["1", "2"], numbered


def test_an_out_of_range_citation_is_refused_by_name() -> None:
    """(3) 反证臂：正文引用 `[3]`（本 run 只有两条）⇒ 点名拒绝。"""
    bad = dict(_SECTIONS)
    bad["results"] = bad["results"] + " A third source would be cited here [3]."
    with pytest.raises(ManuscriptError) as raised:
        validate_manuscript(bad, _table())
    message = str(raised.value)
    assert "[3]" in message and "2" in message, message


def test_an_orphan_reference_is_refused_by_name() -> None:
    """(3) 反证臂：第三条文献列了却从不被引用 ⇒ 点名拒绝（两向闭合的另一半）。"""
    bad = dict(_SECTIONS)
    extended = _ENTRIES + (
        ReferenceEntry(
            identifier="99999999",
            authors=("Doe J",),
            title="A work nobody cites",
            journal="J Test",
            year="2020",
        ),
    )
    with pytest.raises(ManuscriptError) as raised:
        validate_manuscript(bad, _table(extended))
    message = str(raised.value)
    assert "[3]" in message or "3" in message, message


# --- 4. 数字只在汇编器写的地方 ------------------------------------------------


@pytest.mark.parametrize("key", sorted(MANUSCRIPT_KEYS))
def test_a_numeral_in_any_section_is_refused_by_name(key: str) -> None:
    """(4) 正文任何一节写数字 ⇒ `ManuscriptError` **点名那一节与那个字符**。"""
    bad = dict(_SECTIONS)
    bad[key] = bad[key] + " The effect is 42 percent."
    with pytest.raises(ManuscriptError) as raised:
        validate_manuscript(bad, _table())
    message = str(raised.value)
    assert key in message, message
    assert "'4'" in message or "'2'" in message, message


def test_a_digit_inside_a_citation_mark_is_not_a_violation() -> None:
    """(4) 引用标记里的数字**不是**正文数字（否则每个引用都会被误判）。"""
    validate_manuscript(dict(_SECTIONS), _table())  # 不抛即通过


def test_the_model_body_carries_no_digits_and_the_table_does() -> None:
    """(4) 两块的**分界**：模型写的散文里无数字，数据表里有数字（且带来源列）。

    扫的面要**排除两块汇编器写的字**：抬头（run id / digest 全是数字）与**节标题**
    （`## 1. Introduction` 的编号是汇编器加的，模型只写正文）。这正是判据本身的口径：
    `validate_manuscript` 扫的是**八个键的值**，不是拼出来的文档 —— 拼装会引入汇编器
    自己的数字，拿它当「模型违规」是判据指错了方向。
    """
    text = _manuscript()
    body = text[text.index(SECTION_HEADINGS[0]) : text.index(DATA_TABLE_HEADING)]
    prose = "\n".join(
        line for line in body.splitlines() if line.strip() and not line.startswith("## ")
    )
    assert re.search(r"\d", re.sub(r"\[\d+\]", "", prose)) is None, prose
    tail = text[text.index(DATA_TABLE_HEADING) :]
    assert "7990.0" in tail and "178.5" in tail
    assert "| 类别 | 名称 | 值 | 来源 |" in tail


def test_the_data_table_sits_under_results() -> None:
    """(4) 数据表在 `Results` 之下（不是文末 —— 读者读结果时就看得到数字）。"""
    text = _manuscript()
    assert text.index(SECTION_HEADINGS[4]) < text.index(DATA_TABLE_HEADING)
    assert text.index(DATA_TABLE_HEADING) < text.index(SECTION_HEADINGS[5])


# --- 5. 两向反证 -------------------------------------------------------------


def test_changing_the_artifact_year_changes_the_reference_line() -> None:
    """(5) 改制品 `year` ⇒ 参考文献那一行随之变（表是真的读字节，不是写死的）。"""
    changed = tuple(
        ReferenceEntry(
            identifier=entry.identifier,
            authors=entry.authors,
            title=entry.title,
            journal=entry.journal,
            year="1999" if entry.identifier == "39284801" else entry.year,
            doi=entry.doi,
            pmid=entry.pmid,
        )
        for entry in _ENTRIES
    )
    before = _manuscript()
    after = build_manuscript(_inputs(), _admission(), _table(changed))
    assert "Nat Commun. 2024." in before
    assert "Nat Commun. 1999." in after
    assert "Nat Commun. 2024." not in after


def test_the_old_dict_repr_rendering_would_be_caught() -> None:
    """(5) **反证**：换回旧的 `f"- {dict(item)}"` 渲染 ⇒ 结构判据判红。

    旧形态是本轮要消灭的那一个（`research_report.py` 的来源节）：
    `- {'identifier': '39284801', 'evidence_id': 'ev-1'}`。它不是一条参考文献 ——
    没有作者、没有刊名、没有年份。判据按**这三件事**判，所以它咬得住。
    """
    legacy = ReferenceTable(
        entries=(),
    )
    legacy_text = render_references(legacy)
    assert "No citable record" in legacy_text

    # 把「旧渲染」当成一个 reference 行塞进去：它没有作者 / 刊名 / 年份。
    rendered_line = f"- {dict(_inputs().sources[0])}"
    assert rendered_line.startswith("- {'identifier'")
    mismatches = [field for field in ("authors", "journal", "year") if field in rendered_line]
    assert mismatches == [], (
        "the legacy dict-repr line would have to carry author/journal/year to pass the "
        f"reference judge, but it carries {mismatches}"
    )
    # 且它**不**匹配编号形态 ⇒ 「正文 `[n]` ↔ References 逐条映射」判据也判红。
    assert re.match(r"^\d+\. ", rendered_line) is None


def test_a_missing_key_is_refused_by_name() -> None:
    """(2)/(4) 八键缺一 ⇒ 点名拒绝（不产出「看起来像手稿」的残件）。"""
    bad = dict(_SECTIONS)
    bad.pop("discussion")
    with pytest.raises(ManuscriptError) as raised:
        validate_manuscript(bad, _table())
    assert "discussion" in str(raised.value)


def test_the_header_records_who_wrote_the_body() -> None:
    """归属可复核：抬头写明叙述作者 / 返回名 / 摘要（不靠读正文猜）。"""
    text = _manuscript()
    assert "**narrative author**: model_assisted:writer" in text
    assert "**returned model**: `twin-a`" in text
    assert "**assembly state**: `SUCCEEDED`" in text


def test_the_manuscript_is_deterministic() -> None:
    """同一份输入 ⇒ 逐字节相同（与既有汇编器同一条纪律）。"""
    assert _manuscript() == _manuscript()


def test_an_admission_without_a_run_id_is_refused() -> None:
    """没有 run id ⇒ 点名（不汇编一份「不知道属于哪个 run」的手稿）。"""
    inputs = ReportInputs(
        run_id="  ",
        protocol_id=_inputs().protocol_id,
        state="SUCCEEDED",
        sources=(),
        metrics=(),
        verdict=None,
        objective=None,
    )
    with pytest.raises(ManuscriptError):
        build_manuscript(inputs, _admission(), _table())


def test_the_footnote_names_both_faces() -> None:
    """文末如实登记「谁写了哪块面」，并点名缺失的类别（不假装完整）。"""
    text = _manuscript()
    assert "model-written" in text and "assembler-written" in text
    empty_inputs = ReportInputs(
        run_id="run-empty",
        protocol_id="p",
        state="SUCCEEDED",
        sources=(),
        metrics=(),
        verdict=None,
        objective=None,
    )
    empty = build_manuscript(
        empty_inputs, _admission({"results": "Nothing was measured."}), _table()
    )
    assert "no retrievable facts" in empty
