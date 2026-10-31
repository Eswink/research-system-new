"""GOAL-20261031-102 EC-04：期刊选择面的判据（闭集声明 + 依据引用 + 镜像核对）。

**它补哪一格**：`editorial` 相可以多带两个选择字段（`target_journal` +
`selection_rationale`），取值被**闭集**约束（`examples/config/journals.yaml`）。本文件
两向按压：

- 反证 (a)：选了闭集之外的期刊 ⇒ 点名（集里有什么逐字给出）；
- 反证 (b)：依据一个 scope 关键词都不引 ⇒ 点名；
- 反证 (c)：只给两个字段之一 ⇒ 点名（半个选择没法核）；
- 反证 (d)：闭集声明自身畸形（重名 / 缺关键词 / 空集）⇒ 点名；
- 镜像：闭集里每个名字都必须出现在合约 `editorial_decision` 的 purpose 里
  （两处声明漂移 ⇒ 点名 —— 模型看见的集合与判据用的集合必须是同一个）。

**闭集不是评分**：本文件同时钉住 `journals.yaml` 里**没有**影响因子 / 排名字段
（有 ⇒ 判红 —— 声明面不许偷偷长出评价面）。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from packages.application.deliverable.journal_selection import (
    JOURNALS_CONFIG,
    JournalRecord,
    JournalSelectionError,
    contract_mirror_verdict,
    load_journals,
    parse_selection,
    selection_from_artifact,
    validate_selection,
)

_ROOT = Path(__file__).resolve().parents[2]
_CONTRACTS = _ROOT / "examples" / "contracts" / "task_contracts.yaml"


def _journals() -> tuple[JournalRecord, ...]:
    return load_journals(_ROOT / JOURNALS_CONFIG)


def test_the_closed_set_loads_and_carries_no_ranking() -> None:
    """正臂：闭集可读、每条带 scope 关键词；且**没有**任何评分/排名字段。"""
    records = _journals()
    assert len(records) >= 2, "闭集少于两条就不是闭集，是单选"
    for record in records:
        assert record.scope_keywords, record
        assert record.issn, record
    text = (_ROOT / JOURNALS_CONFIG).read_text(encoding="utf-8")
    for banned in ("impact factor", "impact_factor", "rank", "quartile", "h-index"):
        assert banned not in text.lower(), (
            f"journals.yaml 出现 {banned!r} ⇒ 声明面长出了评价面（闭集不是评分）"
        )


def test_a_selection_outside_the_closed_set_is_refused_by_name() -> None:
    """反证 (a)：闭集之外的期刊 ⇒ 点名（并逐字给出集里有什么）。"""
    with pytest.raises(JournalSelectionError, match="not in the declared closed set") as info:
        validate_selection(("Nature", "fits"), _journals())
    assert "Journal of Reproducible Research Tooling" in str(info.value)


def test_a_rationale_without_scope_keywords_is_refused() -> None:
    """反证 (b)：依据不引用该刊任何 scope 关键词 ⇒ 点名。"""
    with pytest.raises(JournalSelectionError, match="cites none of its scope keywords"):
        validate_selection(
            ("Applied AI Evaluation", "the study is important and timely"), _journals()
        )


def test_a_rationale_citing_a_keyword_passes() -> None:
    """正臂：依据引用该刊 scope 关键词 ⇒ 通过（返回命中的那条记录）。"""
    record = validate_selection(
        ("Applied AI Evaluation", "a controlled benchmark with a model comparison"),
        _journals(),
    )
    assert record.issn, record


def test_half_a_selection_is_refused() -> None:
    """反证 (c)：只给 `target_journal` 不给依据（或反过来）⇒ 点名。"""
    with pytest.raises(JournalSelectionError, match="stand or fall together"):
        parse_selection({"target_journal": "Open Science Methods"})
    with pytest.raises(JournalSelectionError, match="stand or fall together"):
        parse_selection({"selection_rationale": "it fits"})


def test_absence_of_both_fields_is_none() -> None:
    """两字段都没给 ⇒ `None`（不选期刊是合法形态，不是失败）。"""
    assert parse_selection({"decision": "accept"}) is None


def test_a_malformed_closed_set_is_refused() -> None:
    """反证 (d)：重名 / 缺关键词 / 空集的闭集声明 ⇒ 各自点名。"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "dup.yaml").write_text(
            "journals:\n"
            "  - {name: A, issn: '1', scope_keywords: [x]}\n"
            "  - {name: A, issn: '2', scope_keywords: [x]}\n",
            encoding="utf-8",
        )
        with pytest.raises(JournalSelectionError, match="duplicate journal name"):
            load_journals(base / "dup.yaml")
        (base / "empty.yaml").write_text("journals: []\n", encoding="utf-8")
        with pytest.raises(JournalSelectionError, match="declares no journals"):
            load_journals(base / "empty.yaml")
        (base / "bare.yaml").write_text("journals:\n  - {name: A, issn: '1'}\n", encoding="utf-8")
        with pytest.raises(JournalSelectionError, match="scope_keywords"):
            load_journals(base / "bare.yaml")


def test_the_closed_set_mirrors_the_contract_purpose() -> None:
    """镜像判据：闭集里每个名字都必须在合约 `editorial_decision` 的 purpose 里。"""
    purpose = _CONTRACTS.read_text(encoding="utf-8")
    contract = purpose.split("editorial_decision:", 1)[1].split("\n  author_response:", 1)[0]
    contract_mirror_verdict(_journals(), contract)


def test_the_selection_is_readable_from_the_artifact_envelope() -> None:
    """制品字节 → 选择（信封形态：先解信封再读决定块）。"""
    artifact = (
        '{"content": "text\\n```json\\n{\\"editorial_decision\\": {\\"decision\\": '
        '\\"accept\\", \\"rationale\\": \\"ok\\", \\"target_journal\\": \\"Open Science '
        'Methods\\", \\"selection_rationale\\": \\"the methodology is open science\\"}}\\n'
        '```\\n", "declared_artifact": "editorial_decision"}'
    )
    selection = selection_from_artifact(artifact)
    assert selection is not None
    name, rationale = selection
    assert name == "Open Science Methods" and "open science" in rationale.lower()
    validate_selection(selection, _journals())
