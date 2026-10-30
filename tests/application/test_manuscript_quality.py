"""GOAL-20261030-101 EC-01 判据：**叙述质量与事实一致性**的三条可机械判口径。

**它补哪一格**：`deliverable/manuscript.py` 的 `validate_manuscript` 判四件**结构事实**
（八键齐备 / 正文无数字 / 引用不越界 / 无孤儿引用），「写得对不对」一条都不判 —— 这一格
连续四轮登记为未覆盖项（GOAL-096 `U-1` → 097 `U-2` → 099 `W-5` → 100 `U-2`）。

**判什么**（三条，各一个类，各带反证臂）：
1. `TestCitationAlignment` —— `Results` 有引用，且每条被引文献与正文**不是无关**；
2. `TestSectionDistinctness` —— 摘要与结论的归一化句子集合不重合；
3. `TestSectionDepth` —— 每节（标题除外）词数 ≥ 阈值（阈值**实测而来**，见模块 docstring）。

**反证臂怎么做**（这是本文件的主体，不是附属）：
* **正向**：真夹具（三套）全部通过 —— 判据不是「见谁都红」；
* **反向**：逐个**复现真实失败形态**（引了一条与正文无关的文献 / 摘要抄结论 /
  某节只写两个词）⇒ 判据必须点名判红，且点名**是哪一条/哪一节/哪一句**；
* **边界**：本 run 没检索到任何可引用条目 ⇒ 引用判据**没有对象**，直接通过
  （合约原文允许，见 `research_manuscript` 的 HARD RULE 2 末句）。

**射程边界（如实登记）**：本文件**不判**「引用支持了那句话」、**不判**「论证是否成立」、
**不判**方法学正确性、**不判**文风 —— 详见 `manuscript_quality.NOT_JUDGED` 与
`docs/architecture/MANUSCRIPT_QUALITY.md`。「词重叠」只是「不是无关」，把它读成「支持」
是本判据明令禁止的过度解读（`fix_policy.forbidden` 逐字禁止）。
"""

from __future__ import annotations

import json

import pytest

from packages.application.deliverable.manuscript import (
    MANUSCRIPT_KEYS,
    validate_manuscript,
)
from packages.application.deliverable.manuscript_quality import (
    MIN_SECTION_WORDS,
    NOT_JUDGED,
    STOPWORDS,
    ManuscriptQuality,
    ManuscriptQualityError,
    check_citation_alignment,
    check_section_depth,
    check_section_distinctness,
    content_words,
    validate_quality,
)
from packages.application.deliverable.references import (
    ReferenceEntry,
    ReferenceTable,
)
from packages.application.deliverable.research_report import ReportInputs

#: 一套**真实形状**的正文（每节与下面两条文献的标题共享实词，摘要与结论不重复）。
_SECTIONS: dict[str, str] = {
    "title": "Retrieval Grounding For Controlled Reproducibility Studies",
    "abstract": "We ask whether grounding a plan in the retrieved literature changes the "
    "design a controlled experiment can execute, and we publish the measured comparison in a "
    "separate table rather than in this prose.",
    "introduction": "Planning assistants propose studies that the literature may already "
    "settle; we ask what changes when the material is retrieved before the plan is written.",
    "related_work": "The closest retrieved work builds reproducibility tooling for "
    "computational research and documents the cost of custom pipelines [1][2]; it leaves open "
    "which planning choices actually move a measured outcome.",
    "methods": "Two arms run the same shipped benchmark script. The treatment arm sets a "
    "larger item count than the control arm, so the comparison isolates the workload.",
    "results": "The treatment arm's comparison count differs from the control arm's; the "
    "per-arm readings and their sources are published in the data table below, by name, so "
    "each value can be checked against this run rather than against this sentence [1].",
    "discussion": "The measured difference is a workload effect and nothing more: the study "
    "varies the item count alone, and one script cannot speak for another [2].",
    "conclusion": "Grounded planning yields an executable design here; whether it yields a "
    "better one is not something this run measured, and we do not claim it.",
}

_ENTRIES: tuple[ReferenceEntry, ...] = (
    ReferenceEntry(
        identifier="39284801",
        authors=("Hoffmann C",),
        title=(
            "ENCORE: a practical implementation to improve reproducibility of "
            "computational research"
        ),
        journal="Nat Commun",
        year="2024",
        pmid="39284801",
    ),
    ReferenceEntry(
        identifier="40601758",
        authors=("Kanitz A",),
        title="Fundamentals of FAIR biomedical data analyses in the cloud using custom pipelines",
        journal="PLoS Comput Biol",
        year="2025",
        pmid="40601758",
    ),
)

_TITLES: tuple[str, ...] = tuple(entry.title for entry in _ENTRIES)


def _quality(titles: tuple[str, ...] = _TITLES) -> ManuscriptQuality:
    return ManuscriptQuality(titles=titles)


def _mutate(**overrides: str) -> dict[str, str]:
    body = dict(_SECTIONS)
    body.update(overrides)
    return body


class TestCitationAlignment:
    """① 引用—主张**相关**（不是「支持」）。"""

    def test_the_real_shape_fixture_is_accepted(self) -> None:
        """正向：真形状的正文 + 真标题 ⇒ 通过（判据不是见谁都红）。"""
        check_citation_alignment(_SECTIONS, _TITLES)

    def test_an_unrelated_cited_work_is_named_red(self) -> None:
        """**反证**：引一条与正文毫无实词重叠的文献 ⇒ 点名条号与标题。

        这是本判据**唯一**能抓的引用错误形态：编号对、条目在表里、但那是**另一篇**。
        实测过的邻居形态见 GOAL-099 `W-1`（模型自己数编号 ⇒ 系统性错位）。
        """
        unrelated = ("Fundamentals of marine sediment core analysis", *_TITLES[1:])
        with pytest.raises(ManuscriptQualityError) as raised:
            check_citation_alignment(_SECTIONS, unrelated)
        message = str(raised.value)
        assert "[1]" in message, message
        assert "marine sediment" in message, message
        assert "unrelated" in message, message

    def test_results_without_any_citation_is_named_red(self) -> None:
        """**反证**：可引用条目在场，而 `Results` 一个标记都没有 ⇒ 点名判红。"""
        with pytest.raises(ManuscriptQualityError) as raised:
            check_citation_alignment(
                _mutate(results="The readings are published in the table below."), _TITLES
            )
        assert "Results section carries no citation mark" in str(raised.value)

    def test_an_empty_reference_list_is_not_an_object(self) -> None:
        """**边界**：本 run 什么都没检索到 ⇒ 引用判据**没有对象**，直接通过。

        合约 `research_manuscript` 的 HARD RULE 2 末句逐字允许这种形态（「If no records
        are listed … write the body without citation marks」）—— 若这里判红，就等于
        逼模型编造一条文献。
        """
        check_citation_alignment(_mutate(results="Nothing was retrieved in this run."), ())

    def test_an_out_of_range_mark_is_named_red_even_without_the_upstream_check(self) -> None:
        """**反证**：编号越界 ⇒ 本函数自己也要判（不依赖上游顺序）。"""
        with pytest.raises(ManuscriptQualityError) as raised:
            check_citation_alignment(
                _mutate(results="The readings are tabulated below [9]."), _TITLES
            )
        assert "[9]" in str(raised.value)


class TestSectionDistinctness:
    """② 摘要与结论的句子集合不重合。"""

    def test_the_real_shape_fixture_is_accepted(self) -> None:
        check_section_distinctness(_SECTIONS)

    def test_an_abstract_copied_into_the_conclusion_is_named_red(self) -> None:
        """**反证**：把摘要那一句原样放进结论 ⇒ 点名**那一句**（不笼统说「两节重复」）。"""
        shared = "Grounded planning yields an executable design here and we report the comparison."
        body = _mutate(abstract=f"{shared} We also ask about reproducibility.", conclusion=shared)
        with pytest.raises(ManuscriptQualityError) as raised:
            check_section_distinctness(body)
        message = str(raised.value)
        assert "Abstract and the Conclusion" in message, message
        assert "grounded planning yields an executable design here" in message.lower(), message

    def test_a_rephrased_repetition_is_out_of_scope(self) -> None:
        """**射程**：改写过的重复（同义复述）**不判** —— 逐字相同才是本判据的对象。

        这条用例是**如实登记的射程边界**：把它写成「必须红」会让判据变成一条它做不到的
        承诺（语义等价需要模型/人评）。此处刻意断言「不红」，让读者看见缺口在哪。
        """
        check_section_distinctness(
            _mutate(
                abstract="Grounding a plan in the retrieved literature changes what the "
                "experiment can execute.",
                conclusion="Reading the literature first alters the design an experiment may run.",
            )
        )

    def test_normalisation_folds_case_and_whitespace(self) -> None:
        """归一化：大小写 / 多余空白 / 首尾标点都折掉（否则逐字重复会被漏掉）。"""
        shared = "the two faces must not say the same thing"
        with pytest.raises(ManuscriptQualityError):
            check_section_distinctness(
                _mutate(abstract=f"  {shared.upper()}.  ", conclusion=f"{shared}!")
            )


class TestSectionDepth:
    """③ 每节非空洞（阈值**实测而来**）。"""

    def test_the_threshold_is_the_measured_floor(self) -> None:
        """阈值必须**低于**三套受控夹具的最短节（实测下界 9 词）⇒ 取 8。

        这条钉住「阈值不是拍脑袋的」：它把实测下界（9）与所用阈值（8）都写进断言 ——
        若有人把阈值抬高到 9 以上，三套真夹具会**一起**判红（那是阈值失控，不是稿件变差）。
        """
        assert MIN_SECTION_WORDS == 8, MIN_SECTION_WORDS
        assert MIN_SECTION_WORDS < 9, "阈值必须低于实测下界（9 词）"

    def test_the_real_shape_fixture_is_accepted(self) -> None:
        check_section_depth(_SECTIONS)

    def test_a_thin_section_is_named_with_its_word_count(self) -> None:
        """**反证**：某节只写两个词 ⇒ 点名节名与词数。"""
        with pytest.raises(ManuscriptQualityError) as raised:
            check_section_depth(_mutate(methods="Two arms."))
        message = str(raised.value)
        assert "methods(2<8)" in message, message

    def test_the_title_is_not_judged(self) -> None:
        """`title` 不受本条判（它天然很短，作用是指识而不是论述）。"""
        check_section_depth(_mutate(title="Short"))

    def test_stopwords_are_the_closed_list(self) -> None:
        """停用词是**封闭词表**：改它 = 改口径，必须同轮改这条断言。"""
        assert "the" in STOPWORDS and "and" in STOPWORDS
        assert "reproducibility" not in STOPWORDS
        assert content_words("The cost of a pipeline") == {"cost", "pipeline"}


class TestWiredIntoTheAssemblyPath:
    """**真的被装配路径调用**（不能是死代码）。

    挂点是**装配面**（`manuscript_assembly.assemble_manuscript`）而不是
    `validate_manuscript`：后者判结构事实（八键 / 数字 / 编号闭合），把品质判据塞进去会让
    「编号越界」这类结构用例因为夹具正文写得短而红 —— 本 GOAL 实测到 5 处这样的连带红，
    判词指向了错误的面。分开之后两类判负各自点名，互不掩蔽。
    """

    def test_the_assembly_function_calls_the_quality_gate(self) -> None:
        """**产品路径真的调用了它**：源码级钉住 `assemble_manuscript` 里的那一行。

        与「直接调 `validate_quality`」不同：这条证明**装配面接上了**。只判后者的话，
        判据可以通过而产品路径从不调用它 —— 那正是「声明了但从未构造」的死缝形态
        （MEM「declared but never constructed is a dead seam」）。
        """
        from pathlib import Path

        source = (
            Path(__file__).resolve().parents[2]
            / "packages"
            / "application"
            / "run_orchestration"
            / "manuscript_assembly.py"
        ).read_text(encoding="utf-8")
        assert "validate_manuscript_quality(sections, facts.references)" in source, (
            "装配面没有调用品质判据 ⇒ 它是死代码"
        )
        # 反向：结构入口**不得**自己带品质判据（两类判负必须分开点名）。
        structural = (
            Path(__file__).resolve().parents[2]
            / "packages"
            / "application"
            / "deliverable"
            / "manuscript.py"
        ).read_text(encoding="utf-8")
        body = structural.split("def validate_manuscript(", 1)[1].split("\ndef ", 1)[0]
        assert "validate_quality(" not in body, (
            "`validate_manuscript` 又带回了品质判据 ⇒ 结构用例会因正文短而红"
        )

    def test_the_quality_entry_point_refuses_a_thin_section(self) -> None:
        """`validate_manuscript_quality` 是装配面调的入口；它必须真的判负。"""
        from packages.application.deliverable.manuscript import validate_manuscript_quality

        with pytest.raises(ManuscriptQualityError):
            validate_manuscript_quality(_mutate(methods="Arms."), _table())
        validate_manuscript_quality(_SECTIONS, _table())  # 正例：真夹具通过

    def test_the_structural_validator_still_accepts_a_thin_body(self) -> None:
        """**分层成立**：结构面**不**因正文短而红（这是 GOAL-101 分开两个入口的理由）。

        同一条正文：结构入口通过、品质入口判红 —— 两侧各自点名各自的面。
        """
        from packages.application.deliverable.manuscript import validate_manuscript_quality

        thin = _mutate(methods="Two arms.", discussion="A workload effect.")
        validate_manuscript(thin, _table())  # 结构面：八键齐、无数字、引用闭合 ⇒ 通过
        with pytest.raises(ManuscriptQualityError):
            validate_manuscript_quality(thin, _table())

    def test_the_quality_module_declares_what_it_does_not_judge(self) -> None:
        """**射程自带**：`NOT_JUDGED` 必须逐条在场（读者要能核对「它不判什么」）。"""
        joined = " ".join(NOT_JUDGED).lower()
        assert "supports the sentence" in joined
        assert "argument holds" in joined
        assert "style" in joined or "readability" in joined


def _table() -> ReferenceTable:
    return ReferenceTable(entries=_ENTRIES)


def _inputs() -> ReportInputs:
    return ReportInputs(
        run_id="run-manuscript-quality-001",
        protocol_id="direction_to_manuscript_v1_0_0",
        state="SUCCEEDED",
        objective="does retrieval grounding change the design an experiment can execute",
        sources=(),
        metrics=(),
        verdict=None,
    )


def test_the_default_example_body_is_accepted_by_all_three() -> None:
    """三条一起跑（`validate_quality` 的顺序：引用 → 节间 → 深度）⇒ 真夹具全过。"""
    validate_quality(_SECTIONS, _quality())
    # 反向：任何一条不过时，`validate_quality` 都要把它抛出来（不吞）。
    for broken in (
        _mutate(results="No marks here."),
        _mutate(abstract=_SECTIONS["conclusion"]),
        _mutate(discussion="Short."),
    ):
        with pytest.raises(ManuscriptQualityError):
            validate_quality(broken, _quality())


def test_the_module_is_offline_and_clock_free() -> None:
    """确定性：零出网、零时钟、零文件系统（源码级钉住；与全仓同类判据同一手法）。"""
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[2]
        / "packages"
        / "application"
        / "deliverable"
        / "manuscript_quality.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "datetime.now",
        "time.time",
        "date.today",
        "socket",
        "urllib",
        "httpx",
        "requests.get",
    ):
        assert forbidden not in source, f"manuscript_quality.py 出现了 {forbidden}"


def test_the_json_round_trip_of_the_fixture_is_stable() -> None:
    """夹具本身是 JSON 可往返的（与合约让模型回复的那份形状一致）。"""
    dumped = json.dumps({key: _SECTIONS[key] for key in MANUSCRIPT_KEYS}, ensure_ascii=False)
    assert json.loads(dumped)["results"] == _SECTIONS["results"]
