"""手稿脚注里的**引用分布读数**（GOAL-20261103-105 EC-02）。

**它补哪一格**：EC-01 把三个结构读数做成了函数，但函数只有判据在用 —— 读手稿的人看不到
它。EC-02 把读数写进 `manuscript.md` 的脚注（与 `**Who wrote which face (recorded, not
asserted)**` 同一段）。这一格的判据必须回答一个问题：**脚注里的数字是不是函数真的算出
来的**，而不是「脚注里有几个数字」。

**判据的形状**（这决定它是否真的咬得住）：从 `build_manuscript` 产出的 markdown 里
**解析出**那三个数，再**直接调用** `measure_citation_sufficiency` 拿期望值，逐项断言相等。
两处算的是同一份语义，但走的是**两条路径**（一条经装配、一条直调）—— 任何一侧漂移都会红。

**另一条判据判的是「没拍阈值」**：脚注里必须出现「readings, not a judgement」这类限定语，
且**不得**出现「sufficient」的肯定式断言 —— 读数不是判决（§7 的反向误读禁令在制品面也
有效）。
"""

from __future__ import annotations

import re

from packages.application.deliverable.citation_sufficiency import (
    measure_citation_sufficiency,
)
from packages.application.deliverable.manuscript import (
    ManuscriptAdmission,
    build_manuscript,
)
from packages.application.deliverable.references import ReferenceEntry, ReferenceTable
from packages.application.deliverable.research_report import ReportInputs

_SECTIONS: dict[str, str] = {
    "title": "Retrieval Grounding For Controlled Planning Studies",
    "abstract": "We study whether grounding a research plan in retrieved literature changes "
    "the plan a controlled experiment can execute.",
    "introduction": "Planning assistants propose studies that the literature may already "
    "settle; we ask what changes when the material is retrieved first [1].",
    "related_work": "The closest retrieved work builds reproducibility tooling and reports "
    "the cost of custom pipelines [2].",
    "methods": "Two arms run the same shipped benchmark script; the treatment arm sets a "
    "larger item count than the control arm.",
    "results": "The treatment arm's count exceeds the control arm's, as the data table "
    "records [1]. The second reading is reported there as well [2].",
    "discussion": "The measured difference is a workload effect, not a quality claim [1].",
    "conclusion": "Grounded planning yields an executable design here; whether it yields a "
    "better one is not something this run measured.",
}

_ENTRIES = (
    ReferenceEntry(
        identifier="39284801",
        authors=("Hoffmann C",),
        title="ENCORE: reproducibility tooling for computational research",
        journal="Nat Commun",
        year="2024",
        doi="10.1038/s41467-024-52446-8",
        pmid="39284801",
    ),
    ReferenceEntry(
        identifier="40601758",
        authors=("Kanitz A",),
        title="FAIR data analyses: planning choices that move measured outcomes",
        journal="PLoS Comput Biol",
        year="2025",
        doi="10.1371/journal.pcbi.1013215",
        pmid="40601758",
    ),
)

#: 脚注那一行的固定格式（**判据按它取数**；改格式要同轮改 `manuscript._citation_readings_line`）。
_READINGS = re.compile(
    r"(\d+) sentence\(s\) scored / (\d+) mark\(s\) / (\d+) cited reference\(s\) / "
    r"single-support section\(s\): ([^.]*)\."
)


def _markdown(sections: dict[str, str] | None = None) -> str:
    body = dict(_SECTIONS)
    body.update(sections or {})
    inputs = ReportInputs(
        run_id="run-citation-readings",
        protocol_id="direction_to_manuscript_v1_0_0",
        state="SUCCEEDED",
        objective="Does grounding a plan in retrieved literature change the design it yields?",
        sources=(
            {"identifier": "39284801", "evidence_id": "ev-1", "title": "ENCORE"},
            {"identifier": "40601758", "evidence_id": "ev-2", "title": "FAIR"},
        ),
        metrics=(),
        verdict=None,
    )
    return build_manuscript(
        inputs,
        ManuscriptAdmission(
            author="model_assisted:writer",
            returned_model="twin-a",
            digest="0" * 64,
            sections=body,
        ),
        ReferenceTable(entries=_ENTRIES),
    )


def _footnote_line(markdown: str) -> str:
    for line in markdown.splitlines():
        if "sentence(s) scored" in line:
            return line
    raise AssertionError("the footnote carries no citation-distribution line")


def test_the_footnote_numbers_equal_the_function_return_values() -> None:
    """**脚注里的三个数**逐项等于 `measure_citation_sufficiency` 的返回值。

    不是「脚注里有数字」：三个数各有独立的期望值，且都从**函数**拿（不从夹具常量拿）。
    """
    markdown = _markdown()
    line = _footnote_line(markdown)
    matched = _READINGS.search(line)
    assert matched is not None, line
    sentences, marks, references, single = matched.groups()

    readings = measure_citation_sufficiency(_SECTIONS)
    assert int(sentences) == len(readings.per_sentence)
    assert int(marks) == sum(item.marks for item in readings.per_sentence)
    assert int(references) == len(readings.per_reference)
    expected_single = ", ".join(readings.single_support_sections) or "none"
    assert single.strip() == expected_single, (single, expected_single)


def test_changing_the_body_moves_the_footnote_numbers() -> None:
    """**反证**：改正文的引用 ⇒ 脚注里的读数**随之变**（不是写死的常量）。

    这条同时证明两件事：脚注读数取自**本份正文**（不是别的 run 的缓存），且它真的
    重算而不是复用上一次的结果。
    """
    before = _READINGS.search(_footnote_line(_markdown()))
    assert before is not None
    mutated = {"discussion": "The measured difference is a workload effect [1][2]."}
    after = _READINGS.search(_footnote_line(_markdown(mutated)))
    assert after is not None
    assert before.group(2) != after.group(2), (
        f"加一条引用标记后『mark(s)』读数必须变：{before.group(2)} == {after.group(2)}"
    )


def test_the_footnote_says_it_is_a_reading_not_a_judgement() -> None:
    """**制品面也守 §7 的反向误读禁令**：脚注必须自陈「这是读数」。

    读数写进对外制品后，读它的人只会看到数字 —— 因此限定语必须**在同一行里**，
    否则「N 个标记」会被读成「引用充分」。
    """
    line = _footnote_line(_markdown())
    assert "readings, not a judgement" in line, line
    assert "sufficient" in line and "not decided here" in line, line
    # 不得出现肯定式的充分性断言。
    assert not re.search(r"\bsufficient(ly)?\b(?![\s\S]*not decided)", line), line


def test_an_empty_body_still_reports_zero_readings() -> None:
    """没有引用标记的正文 ⇒ 读数是 `0`（**读数不是缺失**，不省略那一行）。

    这里用**空参考文献表**：有表却零引用会被 `validate_manuscript` 的「孤儿条目」判据
    拒绝（那是既有的、正确的规则 —— 列了文献就必须引它）。空表是「本 run 什么都没检索到」
    的真实形态，此时零引用是**合法**的，读数照写。
    """
    markdown = _build_zero_cited_body()
    matched = _READINGS.search(_footnote_line(markdown))
    assert matched is not None
    assert matched.group(2) == "0", "零标记是读数 0，不是缺行"
    assert matched.group(3) == "0"
    assert matched.group(4).strip() == "none"
    assert "retrieved no citable record" in markdown, "空表必须同时如实登记（既有脚注那一条）"


def _build_zero_cited_body() -> str:
    """零引用正文 + **空**参考文献表（唯一合法的零引用形态）。"""
    inputs = ReportInputs(
        run_id="run-zero-citations",
        protocol_id="direction_to_manuscript_v1_0_0",
        state="SUCCEEDED",
        objective=None,
        sources=(),
        metrics=(),
        verdict=None,
    )
    sections = {
        "title": "A Study With No Retrieved Literature",
        "abstract": "We report the design of a study that this run could not ground in a "
        "retrieved record.",
        "introduction": "No marks in this section at all.",
        "related_work": "Prior work exists but this run retrieved nothing citable.",
        "methods": "Two arms run the same shipped benchmark script under a fixed procedure.",
        "results": "Nothing was measured in this run, and the data table has no rows.",
        "discussion": "Nothing follows from a measurement that did not happen here.",
        "conclusion": "The design is executable, but nothing about its outcomes is claimed.",
    }
    return build_manuscript(
        inputs,
        ManuscriptAdmission(
            author="model_assisted:writer",
            returned_model="twin-a",
            digest="0" * 64,
            sections=sections,
        ),
        ReferenceTable(entries=()),
    )
