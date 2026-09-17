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
