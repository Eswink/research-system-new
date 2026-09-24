"""GOAL-014 EC-02 的**离线**链路判据：出厂配对的「运行链检索 + 沙箱实验」跑到 `SUCCEEDED`。

这条判据守的是 EC-02 的**前半句**（默认门可跑、零出网）：
`examples/protocols/real_experiment_research_v1.yaml`（本轮新增的**配对声明**，`M-2`）
真的能跑完 —— `analysis` 相位由运行链执行真实检索
（本文件里是 `httpx.MockTransport`，链以外的一切都相同），`execution` 相位由**出厂合约**
`experiment_execution` 声明为沙箱实验、交给装配方接的执行体缝，在**真实容器**里跑完，
验收门按合约的**三条既有判据**（`ARTIFACT_EXISTS(metrics)` + `TEST_PASSES` + `POLICY_COMPLIANT`）
裁决 —— 后两条正是 GOAL-014 接通输入面之后才**可真判**的那两条。

**为什么它必须存在**：EC-02 的正向判据（真实 LLM + 真实检索 + 真实实验到 `SUCCEEDED`）挂
`requires_live_llm`，默认门不跑；若只有那一条，这条链路的回归在默认门上就是**不可见**的。
本文件用 mock 端点 + mock NCBI 传输把链路钉住，真实那一次由
`tests/e2e/test_real_control_plane_experiment_live.py` 承担（产品组合根、无 override）。

**如实边界**：本文件的装配是 run-ready 夹具（带 `preflight_override`），因此它证明的是
**链路与判据**，**不是**「真实控制面」——后者由 live 判据证明。挂 `requires_docker`：
主判据要真有 Linux 可用的 Docker daemon（实验那一段是真容器），非 Linux 容器守护进程下
如实 skip，由 `container-quality` 作业真跑。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.e2e.live_control_plane_support import with_contract_declared_experiment
from tests.e2e.live_run_support import (
    ncbi_run_chain_provider as _ncbi_provider,
)
from tests.e2e.live_run_support import (
    offline_ncbi_http,
    openhands_deps,
    start_run,
    with_run_chain_capabilities,
)

# 读面快照与 mock 端点与既有离线 e2e 同源（同一套装配，避免两处各写一份）。
from tests.e2e.test_ec03_real_runtime_offline_chain import _read_chain, mock_relay

__all__ = ["mock_relay"]

pytestmark = pytest.mark.requires_docker

_PROTOCOL = "real_experiment_research_v1.yaml"
_PROTOCOL_ID = "real_experiment_research_v1_0_0"
#: 装配方给出的脚本与镜像（合约 `experiment_execution` 不 pin 这两个量）。
_EXPERIMENT_SCRIPT = "examples/experiments/exact_match_index_benchmark.py"
_EXPERIMENT_IMAGE = "research-os-sandbox:m9-test"


def _deps(mock_relay_url: str, calls: list[str]) -> Any:
    """run-ready 装配 + 两段执行体缝（运行链检索 / 合约声明的沙箱实验），**不**注入判词。"""
    deps = openhands_deps(mock_relay_url, map_tools=False)
    with_run_chain_capabilities(deps, _ncbi_provider(deps, http_client=offline_ncbi_http(calls)))
    with_contract_declared_experiment(deps, script=_EXPERIMENT_SCRIPT, image=_EXPERIMENT_IMAGE)
    return deps


def test_the_paired_protocol_runs_retrieval_and_a_real_experiment_to_success(
    mock_relay: str,
) -> None:
    """主干：真实检索进证据链、真实容器跑完实验、验收门按三条既有判据放行、run `SUCCEEDED`。"""
    from services.api.app import create_app

    http_calls: list[str] = []
    deps = _deps(mock_relay, http_calls)
    with TestClient(create_app(deps)) as client:
        run = start_run(client, _PROTOCOL)
        reads = _read_chain(client, run)
        experiments = client.get(f"/runs/{run['id']}/experiments").json()

    assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
    assert not reads.failures, reads.failures
    assert reads.run["manifest_digest"], "冻结必须真的发生"
    assert reads.run["protocol_id"] == _PROTOCOL_ID, reads.run
    assert http_calls == ["esearch.fcgi", "efetch.fcgi"], http_calls

    # 实验面：合约判的就是它 —— `ARTIFACT_EXISTS(metrics)` 靠这件产物满足。
    entries = experiments["experiments"]
    assert len(entries) == 1, experiments
    entry = entries[0]
    assert entry["experiment_run_id"], entry
    assert entry["image_digest"], ("制品来自容器，不是桩", entry)
    names = {str(item).rsplit(":", 1)[-1] for item in entry["artifact_ids"]}
    assert "metrics" in names, names
    assert {"n_items", "pairwise_comparisons", "indexed_comparisons"} <= set(entry["metrics"]), (
        entry["metrics"]
    )

    # 证据面：检索真的发生（工具来源 + 真标识），且与实验证据并存。
    retrieved = [item for item in reads.evidence if item.get("tool_refs")]
    assert {item["source_trust_label"] for item in retrieved} == {"RETRIEVED"}, reads.evidence


def test_removing_the_experiment_execution_seam_stops_the_run_before_success(
    mock_relay: str,
) -> None:
    """成对反证（离线可复跑）：**不接**实验执行体缝 ⇒ 该任务**点名拒绝**，run 收敛 `FAILED`。

    这一条钉住「声明 ≠ 执行」：合约声明了沙箱实验，而装配方没把执行链接进来时，
    派发方**不得**静默回退到会话（那会让「声明了实验」与「真的跑了实验」分叉），
    而是以 `CONFIGURATION` 失败并以**点名消息**收敛。
    """
    from services.api.app import create_app

    deps = openhands_deps(mock_relay, map_tools=False)
    with_run_chain_capabilities(deps, _ncbi_provider(deps, http_client=offline_ncbi_http([])))
    with TestClient(create_app(deps)) as client:
        run = start_run(client, _PROTOCOL)
        reads = _read_chain(client, run)
        experiments = client.get(f"/runs/{run['id']}/experiments").json()

    assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
    assert any("no experiment runner is wired" in message for message in reads.failures), (
        reads.failures
    )
    assert experiments["experiments"] == [], experiments


def test_removing_the_self_reported_artifact_makes_the_gate_reject_and_name_it(
    mock_relay: str, tmp_path: Path
) -> None:
    """EC-02 的反证 (b)：**去掉实验自报产物**（`metrics` 来源）⇒ 验收门**判拒**且**点名**。

    做法**不是**伪造一个坏实验：脚本还是同一个（同一份字节，只把 `artifact_refs` 里
    那一项去掉），容器照跑、结果契约照样产出 —— 少的只有**实验自报的那件 `metrics` 制品**。
    于是这一条测的是「门的通过**依赖**真实产物，而不是被喂成通过」：
    同一套代码、同一份合约，产物在场 ⇒ `SUCCEEDED`；产物缺席 ⇒ `FAILED`，且失败消息
    **逐字点名** `ARTIFACT_EXISTS` 与 `metrics`。
    """
    from services.api.app import create_app

    real_script = Path(_EXPERIMENT_SCRIPT)
    variant = tmp_path / "no_declared_metrics_experiment.py"
    patched = real_script.read_text(encoding="utf-8").replace(
        '"artifact_refs": ["metrics"]', '"artifact_refs": []'
    )
    assert patched != real_script.read_text(encoding="utf-8"), (
        "脚本契约变了：反证的前提（artifact_refs 里恰有 metrics）不再成立",
    )
    variant.write_text(patched, encoding="utf-8")

    deps = openhands_deps(mock_relay, map_tools=False)
    with_run_chain_capabilities(deps, _ncbi_provider(deps, http_client=offline_ncbi_http([])))
    with_contract_declared_experiment(deps, script=str(variant), image=_EXPERIMENT_IMAGE)
    with TestClient(create_app(deps)) as client:
        run = start_run(client, _PROTOCOL)
        reads = _read_chain(client, run)

    assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
    rejected = "; ".join(reads.failures)
    assert "acceptance gate rejected" in rejected, reads.failures
    assert "ARTIFACT_EXISTS" in rejected and "metrics" in rejected, rejected
