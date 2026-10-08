"""GOAL-20261008-035 EC-02 判据：**研究循环的 run 路径**上产出可判定的可复现结论。

靶子（EC-02 (c)(d)）：一次真实 run 跑到终态后，读面 `/runs/{run_id}/experiments` 给出
**可复核**的复现结论 —— 复用既有域类型（`ReproducibilityAudit`）与既有 digest 口径
（`build_reproducibility_audit` / `verify_reproducibility_audit` / `verify_audit_outputs`），
**不建第二套**。

判据形态：

- **主干**：审计**在存储里**（不是内存里算一下）⇒ 读面 `reproduction_available=true`、
  `audit_digest` 是封存值、`audit_status` 是域锚点结论、`audit_verified` 是**重算**结果；
  并**独立重算**一次（从存储取回审计对象自行 `compute_audit_digest()`），与读面读数比对 ——
  「判据自报绿」不算证据，两条独立路径一致才算。
- **反证 ①（篡改绑定载荷）**：改掉一个被绑定的字段而**不**重新封存 ⇒ 读面 `audit_verified=false`
  （digest 重算抓得住），而**锚点检查仍可能 PASS** —— 两条是**不同**的事实，判据分开验。
- **反证 ②（换掉一个关键引用）**：把审计绑定的某个输出制品置为墓碑 ⇒ 读面出现 severity
  `FAIL` 的发现，且 `message` **逐字点名**那个制品 id（不是一句含糊的「复现性有问题」）。

**如实边界**：本文件的装配是 run-ready 夹具（`preflight_override`）⇒ 证明的是**链路与判据**，
不是「真实控制面」；实验那一段是真容器（挂 `requires_docker`，非 Linux 可用 daemon 下如实 skip，
由 CI 的 `container-quality` 作业真跑）。跨机器的位级复现**不在**本判据的声明范围内。
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.e2e.live_run_support import start_run
from tests.e2e.test_ec02_experiment_chain_offline import _PROTOCOL, _deps

pytestmark = pytest.mark.requires_docker

_AUDIT_CROSS_CHECK_CODES = frozenset({
    "ARTIFACT_MISSING",
    "ARTIFACT_CORRUPTED",
    "ARTIFACT_DIGEST_DRIFT",
})


def _run_experiment() -> tuple[Any, dict[str, Any], dict[str, Any]]:
    """跑一次声明了沙箱实验的协议，取回 (deps, run, 实验读面条目)。"""
    from services.api.app import create_app

    deps = _deps()
    with TestClient(create_app(deps)) as client:
        run = start_run(client, _PROTOCOL)
        assert run["state"] == "SUCCEEDED", run
        view = client.get(f"/runs/{run['id']}/experiments").json()
    assert len(view["experiments"]) == 1, view
    return deps, run, view["experiments"][0]


def _view_of(deps: Any, run_id: str) -> dict[str, Any]:
    """再读一次实验视图（篡改之后用；每次都经既有读面新取）。"""
    from services.api.app import create_app

    with TestClient(create_app(deps)) as client:
        body = client.get(f"/runs/{run_id}/experiments").json()
    return dict(body["experiments"][0])


def test_the_run_path_records_a_verifiable_reproducibility_conclusion() -> None:
    """主干（EC-02 (c)）：结论**在存储里**、读面可读、且**独立重算**与读面一致。"""
    deps, run, experiment = _run_experiment()

    assert experiment["reproduction_available"] is True, experiment
    assert str(experiment["audit_digest"]).startswith("sha256:"), experiment
    assert experiment["audit_status"] == "PASS", experiment
    assert experiment["audit_verified"] is True, experiment
    # 域口径：`FAIL` 阻断项必须为零；非阻断项是**如实标注**（`code_digest` 未单独 pin 时
    # 域函数给 WARNING，它的 docstring 明说那是「诚实标注而非缺陷」）。读面把 WARNING
    # 也一并呈现 —— 不是把它藏起来凑一个漂亮的空列表。
    blocking = [item for item in experiment["audit_findings"] if item["severity"] == "FAIL"]
    assert blocking == [], experiment
    assert {item["code"] for item in experiment["audit_findings"]} <= {
        "CODE_DIGEST_NOT_PINNED",
        "SEMANTIC_METRICS_DIGEST_MISSING",
    }, experiment

    # 独立路径：从**存储**取回审计对象，自行重算封存 digest 并逐条核对读面读数。
    stored = deps.experiment_store.get_audit(experiment["experiment_run_id"])
    assert str(stored.audit_digest) == experiment["audit_digest"], (stored, experiment)
    assert stored.compute_audit_digest() == stored.audit_digest, stored
    # 锚点逐条在场（域函数的判据，不是本文件自己列的清单）
    assert stored.status == experiment["audit_status"], stored
    assert [item for item in stored.findings() if item.is_blocking] == [], stored


def test_tampering_the_bound_payload_is_caught_by_digest_recomputation() -> None:
    """反证 ①：改坏一个**被绑定**的字段而不重新封存 ⇒ digest 重算判红。

    与锚点检查**分开判**：篡改后锚点仍然齐全（`audit_status` 还是 PASS），红的是
    「载荷与封存 digest 不一致」这条独立事实 —— 两个读数不是同一个东西。
    """
    import dataclasses

    deps, run, experiment = _run_experiment()
    stored = deps.experiment_store.get_audit(experiment["experiment_run_id"])
    tampered = dataclasses.replace(stored, command="tampered-command --not-the-real-one")
    deps.experiment_store.save_audit(tampered)

    after = _view_of(deps, run["id"])
    assert after["audit_verified"] is False, after
    assert after["audit_status"] == "PASS", after
    assert after["audit_digest"] == experiment["audit_digest"], after


def test_swapping_an_output_artifact_is_named_in_the_findings() -> None:
    """反证 ②：审计绑定的输出制品被置墓碑 ⇒ 发现里**逐字点名**它（不是笼统判负）。"""
    deps, run, experiment = _run_experiment()
    victim = experiment["artifact_ids"][0]
    assert deps.artifacts is not None
    deps.artifacts.delete(victim)

    after = _view_of(deps, run["id"])
    failures = [item for item in after["audit_findings"] if item["severity"] == "FAIL"]
    assert failures, after
    named = [item for item in failures if victim in item["message"]]
    assert named, (victim, failures)
    assert named[0]["code"] in _AUDIT_CROSS_CHECK_CODES, named[0]
