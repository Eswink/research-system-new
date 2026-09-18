"""重建能力分类器：判据矩阵与"点名事实"的确定性（GOAL-005 cycle 6 = EC-06）。

判据形状：`missing` 必须逐字等于期望元组（顺序 = run 行字段声明顺序），`status` 必须
与"能不能尝试重建"一致；拒绝文案（`early_refusal`）必须与 `rebuild_and_resume` 的
两条早退逐字相同，`dependency_prefix` 必须与既有异常前缀逐字相同。
"""

from __future__ import annotations

import uuid

import pytest

from packages.application.run_orchestration.rebuild_readiness import (
    REBUILD_REFUSED,
    REBUILD_SELF_CONTAINED,
    REBUILD_SOURCE_DEPENDENT,
    RebuildReadiness,
    rebuild_readiness,
)
from packages.domain.core import ID, Digest
from packages.domain.protocol_source import ProtocolBody, ProtocolSource
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState

DIGEST = Digest.parse("sha256:" + "a" * 64)
SEMANTIC = Digest.parse("sha256:" + "b" * 64)
SOURCE = ProtocolSource(protocol_path="examples/protocols/console_demo_research_v1.yaml")


def _run(**overrides: object) -> ResearchRun:
    base: dict[str, object] = {
        "id": ID(str(uuid.uuid4())),
        "project_id": "p-1",
        "protocol_id": "console_demo_research_v1",
        "state": ResearchRunState.State.PAUSED,
        "manifest_digest": DIGEST,
        "manifest_semantic_digest": SEMANTIC,
        "protocol_source": SOURCE,
        "protocol_body": None,
    }
    base.update(overrides)
    return ResearchRun(**base)  # type: ignore[arg-type]


def test_a_self_contained_row_needs_no_external_source() -> None:
    """正文 + 两个 digest ⇒ 自足：读面不能把这种行说成缺事实。"""
    body = ProtocolBody.of("version: 0.4.0\n")

    readiness = rebuild_readiness(_run(protocol_body=body))

    assert readiness.status == REBUILD_SELF_CONTAINED
    assert readiness.missing == ()
    assert readiness.body_frozen is True
    assert readiness.dependency_prefix() == "", "自足行不点名缺正文"


def test_a_row_without_a_frozen_body_says_it_depends_on_the_source() -> None:
    """两个 digest 齐、无正文 ⇒ 依赖来源（不是缺事实）：判据是合取，不能过宽。"""
    readiness = rebuild_readiness(_run(protocol_body=None))

    assert readiness.status == REBUILD_SOURCE_DEPENDENT
    assert readiness.missing == (), "只有来源可重建：不得把它算成缺事实"
    assert readiness.dependency_prefix() == "run has no frozen protocol body; "


def test_a_legacy_row_without_body_or_source_names_both_facts() -> None:
    """旧 run 形态（无正文、无来源）⇒ 点名**两条**事实，而不是一个含糊的 None。"""
    readiness = rebuild_readiness(_run(protocol_source=None, protocol_body=None))

    assert readiness.status == REBUILD_REFUSED
    assert readiness.missing == ("protocol_body", "protocol_source")
    assert readiness.early_refusal() == (
        "run has no recorded protocol source (predates source recording)"
    )


def test_a_legacy_event_shape_names_the_missing_semantic_digest() -> None:
    """旧 `manifest.frozen` 事件形态（无 `semantic_digest`）⇒ 点名这一条事实。"""
    readiness = rebuild_readiness(_run(manifest_semantic_digest=None))

    assert readiness.status == REBUILD_REFUSED
    assert readiness.missing == ("manifest_semantic_digest",)
    assert readiness.early_refusal() is None, "这一条由 convergence 守卫拒，不是早退"
    assert readiness.body_frozen is False
    assert readiness.dependency_prefix() == "run has no frozen protocol body; ", (
        "这一行同样没有冻结正文 ⇒ 前缀如实说明重建依赖来源"
    )


def test_a_row_without_a_frozen_digest_names_that_fact() -> None:
    readiness = rebuild_readiness(_run(manifest_digest=None, manifest_semantic_digest=None))

    assert readiness.status == REBUILD_REFUSED
    assert readiness.missing == ("manifest_digest", "manifest_semantic_digest")
    assert readiness.early_refusal() == "run has no frozen manifest digest; cannot verify rebuild"


def test_an_never_frozen_row_names_all_four_facts_in_field_order() -> None:
    """从未冻结的 run：四条事实全缺，顺序 = run 行字段声明顺序（可复核）。"""
    readiness = rebuild_readiness(
        _run(
            manifest_digest=None,
            manifest_semantic_digest=None,
            protocol_source=None,
            protocol_body=None,
        )
    )

    assert readiness.missing == (
        "manifest_digest",
        "manifest_semantic_digest",
        "protocol_body",
        "protocol_source",
    )
    assert readiness.early_refusal() == (
        "run has no recorded protocol source (predates source recording)"
    ), "早退顺序与 rebuild_and_resume 一致（装配输入全缺先拒）"


def test_the_missing_set_is_the_field_names_of_the_row() -> None:
    """结构判据：missing 里的每个名字都必须是 canonical 行的字段名（不是自造词）。"""
    from dataclasses import fields

    field_names = {f.name for f in fields(ResearchRun)}
    readiness = rebuild_readiness(
        _run(manifest_digest=None, manifest_semantic_digest=None, protocol_source=None)
    )

    assert set(readiness.missing) <= field_names, "点名的事实必须能在 run 行上找到"


@pytest.mark.parametrize(
    ("status", "missing"),
    [
        (REBUILD_REFUSED, ()),
        (REBUILD_SELF_CONTAINED, ("protocol_body",)),
        (REBUILD_SOURCE_DEPENDENT, ("manifest_digest",)),
    ],
)
def test_the_value_object_refuses_self_contradicting_states(
    status: str, missing: tuple[str, ...]
) -> None:
    """REFUSED 必须点名 ≥1 条事实；非 REFUSED 不得带 missing（自相矛盾构造不出来）。"""
    with pytest.raises(ValueError):
        RebuildReadiness(status=status, missing=missing)
