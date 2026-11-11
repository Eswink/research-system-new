"""GOAL-20261111-109 EC-01：**run 级可比键**——配对消融的配对依据。

**它守什么**（每条都指向可证伪事实）：

1. 仅 `run_id` / `frozen_at` / `project_id` 不同的两份 manifest ⇒ 键**相等**
   （不然「同一装配、两次 run」配不成对）；
2. **既有 `semantic_digest()` 在同一对上不等** ⇒ 它不能当配对键
   （这正是 EC-01 点名「不能用」的那句话的机械证明——不钉住它，
   有人把它换回去时没有任何判据会红）；
3. **反证**：剔除面之外**任何一个**声明字段换一个字 ⇒ 键不等 ⇒ 判红
   （证明它真在比内容，不是恒等函数——逐字段参数化，不是只挑一个字段）；
4. 剔除面**恰是那三个**：`comparison_fields()` 必须等于「全部字段 − 三者」
   （新增 manifest 字段自动纳入 ⇒ 剔除面不会悄悄扩大）。
"""

from __future__ import annotations

import dataclasses

import pytest

from packages.application.run_orchestration.comparison_digest import (
    EXCLUDED_FIELDS,
    comparable,
    comparison_digest,
    comparison_fields,
)
from packages.domain.manifest import RunManifest

#: 一份**填满**的基线 manifest（空 dict 的 digest 相等是空真；受判面要非空）。
_BASE: dict[str, object] = {
    "run_id": "run-a",
    "project_id": "proj-1",
    "protocol_version": "1.0.0",
    "protocol_digest": "sha256:aa",
    "compiled_plan_digest": "sha256:bb",
    "source_commit": "371b6a8f",
    "role_definitions": {"writer": {"panel_role": "WRITER"}},
    "agent_specs": {"writer": {"model_binding": {"type": "MODEL_PROFILE"}}},
    "resolved_models": {"writer": "hy4free"},
    "model_runtime_fingerprints": {"writer": {"verdict": "REPEATABLE_CONFIGURATION"}},
    "effective_tools": {"literature.search": "europe_pmc"},
    "tool_pack_digests": ["sha256:cc"],
    "task_contracts": {"research_manuscript": {"max_attempts": 2}},
    "policy_version": "policy-1",
    "context_template_hashes": ["sha256:dd"],
    "workspace_backend": "docker",
    "execution_backend": "docker",
    "environment": "linux",
    "input_artifact_digests": ["sha256:ee"],
    "budget_reservation_ref": "res-1",
    "endpoint_config_digest": "sha256:ff",
    "probe_suite_digest": "sha256:11",
    "fallback_audit": {"mode": "none"},
    "image_digest": "sha256:22",
    "skill_versions": {"citation-binding": "1.0.0"},
    "evaluation_dataset_digest": "sha256:33",
    "pricing_version": "unpriced_v1",
    "pricing_digest": "sha256:44",
    "accepted_policy_exceptions": [],
}


def _manifest(**overrides: object) -> RunManifest:
    return RunManifest(**{**_BASE, **overrides})  # type: ignore[arg-type]


def test_identity_fields_alone_do_not_break_pairing() -> None:
    """仅 run_id / frozen_at / project_id 不同 ⇒ 键相等（配对成立）。"""
    left = _manifest()
    right = _manifest(
        run_id="run-b",
        project_id="proj-2",
        frozen_at="2026-11-12T00:00:00Z",
    )
    assert comparable(left, right), "身份字段不应进可比键"
    assert comparison_digest(left).digest == comparison_digest(right).digest


def test_semantic_digest_cannot_be_the_pairing_key() -> None:
    """**同一条对的 `semantic_digest` 不等** ⇒ 它不能当配对键（EC-01 点名的那句话）。

    不钉住这条，就有人「顺手换回 semantic_digest」而没有任何判据会红——
    那会让两轮 run 永远配不成对，配对消融在真实路径上结构性不可达。
    """
    left = _manifest()
    right = _manifest(run_id="run-b")
    assert left.semantic_digest() != right.semantic_digest()
    assert comparable(left, right)


@pytest.mark.parametrize(
    ("field_name", "drift"),
    [
        ("protocol_digest", "sha256:XX"),
        ("resolved_models", {"writer": "hy3"}),
        ("effective_tools", {"literature.search": "ncbi_eutils"}),
        ("task_contracts", {"research_manuscript": {"max_attempts": 1}}),
        ("policy_version", "policy-2"),
        ("image_digest", "sha256:YY"),
        ("skill_versions", {"citation-binding": "1.0.1"}),
        ("pricing_digest", "sha256:ZZ"),
        ("endpoint_config_digest", "sha256:AA"),
        ("fallback_audit", {"mode": "requested"}),
        ("budget_reservation_ref", "res-2"),
        ("execution_backend", "local"),
    ],
)
def test_any_compared_field_drift_breaks_the_key(field_name: str, drift: object) -> None:
    """**反证**：剔除面之外任一声明字段漂移 ⇒ 键不等（逐字段参数化，不是挑一个）。"""
    left = _manifest()
    right = _manifest(**{field_name: drift})
    assert not comparable(left, right), f"{field_name} 漂移后仍可配对 ⇒ 键没有比它"
    # 且漂移必须真的发生了（防「漂移值 == 原值」的空真反证）。
    assert getattr(left, field_name) != getattr(right, field_name)


def test_excluded_fields_are_exactly_the_three_named() -> None:
    """剔除面恰是 `run_id` / `frozen_at` / `project_id`；其余声明字段全在。"""
    all_fields = {field.name for field in dataclasses.fields(RunManifest)}
    assert set(EXCLUDED_FIELDS) == {"run_id", "frozen_at", "project_id"}
    assert set(comparison_fields()) == all_fields - set(EXCLUDED_FIELDS)


def test_the_compared_surface_is_not_empty() -> None:
    """受判面非空（27 个声明字段；空真不算通过）。"""
    assert len(comparison_fields()) >= 20
    key = comparison_digest(_manifest())
    assert key.compared_fields == len(comparison_fields())
    assert len(key.digest) > 16
