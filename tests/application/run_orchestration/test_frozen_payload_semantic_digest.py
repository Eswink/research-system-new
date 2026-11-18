"""冻结事件的 payload 与 RunManifest 同源（GOAL-004 cycle 4 = EC-04）。

`manifest.frozen` 是执行期失败收敛路径唯一能读到的冻结事实来源：那条路径没有
`RunOutcome`（`start_run` 抛 `ValueError`），run 行的四项冻结引用只能从事件 payload
补回来。所以 payload 必须带**语义 digest**（排除 `frozen_at`），而且必须与
`RunManifest.semantic_digest()` 逐字相同——本用例钉住这条同源关系（判据只增强）。
"""

from __future__ import annotations

from packages.application.run_orchestration.eventing import frozen_payload
from packages.domain.core import ID, Version
from packages.domain.manifest import RunManifest
from packages.domain.run import ResearchRun

_RUN_ID = ID.generate()


def _run() -> ResearchRun:
    return ResearchRun(id=_RUN_ID, project_id="project-1", protocol_id="protocol-1")


def _manifest(**overrides: object) -> RunManifest:
    kwargs: dict[str, object] = {
        "run_id": _RUN_ID.value,
        "project_id": "project-1",
        "protocol_version": Version("0.4.0"),
        "pricing_version": "pricing-v1",
        "pricing_digest": "sha256:" + "c" * 64,
    }
    kwargs.update(overrides)
    return RunManifest(**kwargs)  # type: ignore[arg-type]


def test_the_frozen_payload_carries_the_manifest_semantic_digest() -> None:
    manifest = _manifest()

    payload = frozen_payload(_run(), manifest)

    assert payload["digest"] == str(manifest.digest())
    assert payload["semantic_digest"] == str(manifest.semantic_digest())
    assert payload["pricing_version"] == "pricing-v1"
    assert payload["pricing_digest"] == "sha256:" + "c" * 64


def test_the_semantic_digest_excludes_the_freeze_moment_like_the_run_row() -> None:
    """语义 digest ≠ 快照 digest：冻结时刻不参与语义比对（与 run 行同一判据）。"""
    payload = frozen_payload(_run(), _manifest())

    assert payload["semantic_digest"] != payload["digest"]
    assert str(payload["semantic_digest"]).startswith("sha256:")


def test_a_field_drift_moves_the_payload_semantic_digest() -> None:
    """payload 里的语义 digest 真的覆盖 manifest 字段（不是常量、不是快照 digest 的别名）。"""
    base = frozen_payload(_run(), _manifest())
    drifted = frozen_payload(_run(), _manifest(policy_version="policy-v2"))

    assert drifted["semantic_digest"] != base["semantic_digest"]


# ---------------------------------------------------------------------------
# GOAL-20261117-114 EC-03：**可比键进冻结快照**（配对消融的事后审计面）。
#
# 完整 `RunManifest` 不落库 ⇒ 想判「两次 run 是不是同一份装配」必须有一个**落库的**
# 可比键。它不能复用 `digest` / `semantic_digest`：前者含 `frozen_at`、后者含 `run_id`，
# 两者在真实的两臂对上都不等（那是 `semantic_digest_cannot_be_the_pairing_key` 那条
# 判据的同一事实）。所以 payload 里第三个 digest 是**另一件事**，这三条钉住它不是别名。
# ---------------------------------------------------------------------------


def test_the_frozen_payload_carries_the_comparison_digest() -> None:
    """payload 的可比键 == 现算的可比键（同源，不是另存一份可能漂移的副本）。"""
    from packages.application.run_orchestration.comparison_digest import comparison_digest

    manifest = _manifest()
    payload = frozen_payload(_run(), manifest)

    assert payload["comparison_digest"] == str(comparison_digest(manifest).digest)
    assert str(payload["comparison_digest"]).startswith("sha256:")


def test_the_comparison_digest_pairs_two_runs_the_other_two_cannot_pair() -> None:
    """**这条是 EC-03 的全部意义**：两个身份字段不同的 run，只有可比键相等。"""
    left = frozen_payload(_run(), _manifest())
    right = frozen_payload(
        _run(), _manifest(run_id=ID.generate().value, frozen_at="2026-11-17T00:00:00Z")
    )

    assert left["comparison_digest"] == right["comparison_digest"]
    assert left["digest"] != right["digest"]
    assert left["semantic_digest"] != right["semantic_digest"]


def test_a_semantic_drift_moves_the_comparison_digest() -> None:
    """反证：装配内容变了 ⇒ 可比键也必须变（它不是恒等函数）。"""
    base = frozen_payload(_run(), _manifest())
    drifted = frozen_payload(_run(), _manifest(policy_version="policy-v2"))

    assert drifted["comparison_digest"] != base["comparison_digest"]
