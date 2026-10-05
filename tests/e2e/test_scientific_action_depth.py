"""GOAL-20261005-030 EC-03 判据：**科研动作的深度**。

（真科研动作 + 结构化产出 + canonical 落盘 + 读面可复核 + 反证点名）

**它补什么**：EC-01 证的是「承接的读能力真的被用上」，但那些读的是**已经存在**的 canonical
状态。本判据加一个**产生新知识**的动作，并对它的结论下一道**可否证**的判据。

**被测对象**：`examples/protocols/scientific_action_depth_v1.yaml`（本轮新增）经
`compile → preflight → freeze → execute_phases` 跑完，三个 phase：

1. `probe`（run-chain 读）—— 三条已放行承接读能力；
2. `experiment`（**真科研动作**，合约声明沙箱实验）—— 在真实容器里跑确定性基准实验
   （精确重复检测：两两比较 vs 哈希索引），产出结构化 `metrics`；
3. `verdict`（run-chain 读，在 experiment **之后**）—— 读本 run 的证据投影，
   返回内容含实验那次工具证据 ⇒ **下游消费**。

**四件事逐条取证**（承 EC-03 的四个要求）：

1. **真科研动作**：实验由**真实容器**执行（`image_digest` 在场 ⇒ 制品来自容器，不是桩），
   且产出的指标是**科学测量**（`pairwise_comparisons` / `indexed_comparisons` /
   `comparison_reduction_ratio` / `agreement`）而非流程计数。
2. **结构化产出**：`metrics` 制品存在且**逐字段**可断言（不是自由文本、不是在字符串里找关键词）；
   字段名与实验脚本**写死的一致**（判据不 import 脚本当预言机）。
3. **canonical 落盘 + 读面可复核**：实验制品经 `GET /runs/{id}/artifacts` 可见、
   `GET /artifacts/{id}/content` 取得到；实验记录经 `GET /runs/{id}/experiments` 可见；
   证据经 `GET /runs/{id}/evidence` 可见。
4. **反证（下游判负并点名）**：把**实验的可否证判据提高**到实验达不到的水平
   （`comparison_reduction_ratio >= 1e6`）⇒ 同一份协议、同一套装配 ⇒ 该 phase
   **判拒并点名那个数**（`comparison_reduction_ratio=... GTE 1000000`），run 收敛 `FAILED`。
   这条同时证明**那道阈值是真的判据**（不是装饰）—— 承 GOAL-027「评审真能判不通过」的形态。

**如实边界**（本文件不声称已解决）：

- 实验**不出网**（纯标准库、语料脚本内生成）；挂 `requires_docker`（实验那段是真容器，
  非 Linux 容器守护进程下如实 skip）。
- 装配走 run-ready 夹具 + 装配方声明的两段执行体缝（运行链读 / 合约声明的沙箱实验），
  与 GOAL-011/027/029 全部离线判据同一条路径：它证的是**链路与判据**。
- **`metrics` 判据落在执行它的那个 phase**（既有语义）：下游 `verdict` 消费的是
  **run 级证据投影**（含实验工具证据），**不**读 `metrics` 字段。两条路径都取证，
  但**不**声称「指标跨 phase 传播」。
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from adapters.canonical import CanonicalReadProvider
from packages.application.ports.tool_provider import ToolProvider
from packages.application.run_orchestration.phase_capabilities import (
    CapabilityDeps,
    RunChainCall,
)
from tests.e2e.live_control_plane_support import with_contract_declared_experiment
from tests.e2e.live_run_support import (
    openhands_deps as _openhands_deps,
)
from tests.e2e.live_run_support import (
    run_chain_store_ledger as _store_ledger,
)
from tests.e2e.live_run_support import (
    start_run as _start,
)

# 读面快照与 mock 端点与既有离线 e2e 同源（同一套装配，避免两处各写一份）。
from tests.e2e.test_ec03_real_runtime_offline_chain import _read_chain, mock_relay

__all__ = ["mock_relay"]

pytestmark = pytest.mark.requires_docker

_PROTOCOL = "scientific_action_depth_v1.yaml"
_PROTOCOL_ID = "scientific_action_depth_v1_0_0"
_EXPERIMENT_SCRIPT = "examples/experiments/exact_match_index_benchmark.py"
_EXPERIMENT_IMAGE = "research-os-sandbox:m9-test"
#: 合约 id（本轮新增；装配方只给脚本与镜像，**不**改目录里的判据）。
_EXPERIMENT_CONTRACT = "scientific_action_experiment"
_METRIC = "comparison_reduction_ratio"
_THRESHOLD = 100
#: 本协议的 run-chain 声明（三条已放行承接读能力，逐条对应 provider 侧 tool id）。
_CAPABILITIES = ("artifact.read", "evidence.read", "workspace.read")
_TOOL_IDS = {
    "artifact.read": "artifact_read",
    "evidence.read": "evidence_read",
    "workspace.read": "workspace_read",
}
_PROVIDER = "m12_artifact"
_BRIEF = "input-brief:real_research_v1"


def _provider(deps: Any) -> tuple[CanonicalReadProvider, Any, Any]:
    store, ledger = _store_ledger(deps)
    return CanonicalReadProvider(store, ledger, spill_threshold_bytes=1), store, ledger


def _calls() -> tuple[RunChainCall, ...]:
    """三条读能力的运行链声明（与 EC-01 同一组、同一取参口径）。"""
    return (
        RunChainCall(
            provider_id=_PROVIDER,
            tool_id=_TOOL_IDS["artifact.read"],
            capability="artifact.read",
            fixed_arguments={"artifact_id": _BRIEF},
        ),
        RunChainCall(
            provider_id=_PROVIDER,
            tool_id=_TOOL_IDS["evidence.read"],
            capability="evidence.read",
            run_id_argument=True,
        ),
        RunChainCall(
            provider_id=_PROVIDER,
            tool_id=_TOOL_IDS["workspace.read"],
            capability="workspace.read",
            run_id_argument=True,
        ),
    )


def _assembled_deps(mock_relay_url: str, *, falsify_threshold: int | None = None) -> Any:
    """run-ready 装配 + 两段执行体缝（运行链读 / 合约声明的沙箱实验）。

    `falsify_threshold` 非空 ⇒ **反证臂**：把实验合约那条 `METRIC_THRESHOLD` 的阈值
    改到实验达不到的水平（只动 `preflight_override` 的目录快照，与既有反证手法同源；
    **不改**仓库里的契约文件）。
    """
    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.assembly import policy_bindings

    deps = _openhands_deps(mock_relay_url, map_tools=False)
    provider, store, ledger = _provider(deps)
    if falsify_threshold is not None:
        _raise_the_threshold(deps, falsify_threshold)

    spec = deps.preflight_override.catalog.tool_providers[_PROVIDER]
    policy = policy_bindings().get("policy_evaluator")
    assert policy is not None, "policy.yaml must be loadable for the run-chain policy check"
    capabilities = CapabilityDeps(
        calls=_calls(),
        providers={str(spec.id): cast("ToolProvider", provider)},
        provider_specs={str(spec.id): spec},
        policy=policy,
        artifacts=store,
        ledger=ledger,
    )
    old = deps.runs
    assert old is not None
    deps.runs = RunOrchestrationService(
        replace(old._deps, runtime=old._deps.runtime, capabilities=capabilities)
    )
    # 合约声明的沙箱实验缝（装配方只给脚本与镜像；判据来自出厂目录）。
    with_contract_declared_experiment(deps, script=_EXPERIMENT_SCRIPT, image=_EXPERIMENT_IMAGE)
    return deps


def _raise_the_threshold(deps: Any, threshold: int) -> None:
    """反证臂：只动 `preflight_override` 的目录快照，把那条指标阈值改到实验达不到的水平。

    **不改**仓库里的契约文件（与既有反证手法同源：改的是本次 run 看到的目录）。
    """
    from decimal import Decimal

    context = deps.preflight_override
    assert context is not None
    contracts = dict(context.catalog.task_contracts)
    contract = contracts[_EXPERIMENT_CONTRACT]
    criteria = [
        replace(item, threshold=Decimal(threshold)) if item.metric == _METRIC else item
        for item in contract.acceptance_criteria
    ]
    assert any(item.metric == _METRIC for item in criteria), (
        "反证臂要找的那条判据不在了 —— 本判据的前提变了",
        [item.metric for item in contract.acceptance_criteria],
    )
    contracts[_EXPERIMENT_CONTRACT] = replace(contract, acceptance_criteria=criteria)
    deps.preflight_override = replace(
        context, catalog=replace(context.catalog, task_contracts=contracts)
    )


def _app(deps: Any) -> Any:
    from services.api.app import create_app

    return create_app(deps)


def _artifact_ids(reads: Any) -> list[str]:
    payload = reads.artifacts
    entries = payload["artifacts"] if isinstance(payload, dict) else payload
    return [str(item.get("id") or "") for item in entries]


def _artifact_content(client: TestClient, artifact_id: str) -> dict[str, Any]:
    response = client.get(f"/artifacts/{artifact_id}/content")
    assert response.status_code == 200, (artifact_id, response.status_code)
    parsed: dict[str, Any] = json.loads(response.content.decode("utf-8"))
    return parsed


def _metrics_artifact(reads: Any) -> str:
    """本 run 的 `metrics` 制品 id（实验制品的既有命名：以 `metrics` 结尾）。"""
    matched = [
        artifact_id
        for artifact_id in _artifact_ids(reads)
        if artifact_id.rsplit(":", 1)[-1] == "metrics"
    ]
    assert matched, ("实验必须产出 metrics 制品", _artifact_ids(reads))
    return matched[0]


def _tool_evidence_for(reads: Any, tool_id: str) -> list[dict[str, Any]]:
    return [
        item
        for item in reads.evidence
        if len(item.get("tool_refs") or []) == 2 and str(item["tool_refs"][1]) == tool_id
    ]


class TestTheScientificActionIsReal:
    """① 真科研动作：真实容器执行 + 科学测量（不是流程计数）。"""

    def test_the_experiment_runs_in_a_real_container(self, mock_relay: str) -> None:
        deps = _assembled_deps(mock_relay)
        with TestClient(_app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))
            experiments = client.get(f"/runs/{reads.run['id']}/experiments").json()

        assert reads.run["state"] == "SUCCEEDED", (reads.run, reads.failures)
        entries = experiments["experiments"]
        assert len(entries) == 1, experiments
        entry = entries[0]
        # 制品来自**容器**（不是桩）：镜像指纹 + metrics 制品在场。
        assert entry["image_digest"], ("制品来自容器，不是桩", entry)
        names = {str(item).rsplit(":", 1)[-1] for item in entry["artifact_ids"]}
        assert "metrics" in names, names

    def test_the_metrics_are_scientific_measurements(self, mock_relay: str) -> None:
        """指标是**科学测量**：两法各自的比较次数 + 一致性 + 比值（逐字段断言）。"""
        deps = _assembled_deps(mock_relay)
        with TestClient(_app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))
            metrics = _artifact_content(client, _metrics_artifact(reads))

        # 字段名与实验脚本**写死的一致**（判据不 import 脚本当预言机）。
        for field in (
            "pairwise_comparisons",
            "indexed_comparisons",
            "comparison_reduction_ratio",
            "agreement",
            "duplicates_found",
            "duplicates_expected",
        ):
            assert field in metrics, (field, sorted(metrics))
        assert metrics["agreement"] is True, metrics
        assert metrics["duplicates_found"] == metrics["duplicates_expected"], metrics
        # 两法**确实**是两种代价：两两比较远多于索引桶内比较。
        assert metrics["pairwise_comparisons"] > metrics["indexed_comparisons"], metrics
        assert float(metrics["comparison_reduction_ratio"]) >= _THRESHOLD, metrics


class TestTheActionOutputIsStructuredAndReviewable:
    """②③ 结构化产出 + canonical 落盘 + 读面可复核。"""

    def test_the_metrics_artifact_is_on_the_run_read_face(self, mock_relay: str) -> None:
        deps = _assembled_deps(mock_relay)
        with TestClient(_app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))
            artifact_id = _metrics_artifact(reads)
            content = _artifact_content(client, artifact_id)

        assert isinstance(content, dict), content
        assert content["pairwise_comparisons"] > 0, content

    def test_the_experiment_and_evidence_are_reviewable(self, mock_relay: str) -> None:
        deps = _assembled_deps(mock_relay)
        with TestClient(_app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))
            experiments = client.get(f"/runs/{reads.run['id']}/experiments").json()

        assert experiments["experiments"], experiments
        # 实验证据在 run 的证据读面上（`experiment_run_id` 是既有字段）。
        assert reads.evidence, reads.evidence


class TestTheDownstreamPhaseConsumesTheExperiment:
    """下游消费：`verdict`（在 experiment 之后）读到的证据投影含实验工具证据。"""

    def test_the_verdict_phase_reads_evidence_after_the_experiment(self, mock_relay: str) -> None:
        deps = _assembled_deps(mock_relay)
        with TestClient(_app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))

            # `evidence.read` 两次（probe 与 verdict 各一次）⇒ 取**后**一次（下游）。
            readings = _tool_evidence_for(reads, _TOOL_IDS["evidence.read"])
            assert len(readings) >= 2, (
                "probe 与 verdict 各应有一次 evidence.read 调用",
                len(readings),
            )
            # 下游那次调用的返回内容：按制品的 task 段区分（两个 phase 各一个 task）。
            probe_artifact = str(readings[0]["artifact_id"])
            downstream = next(
                (item for item in readings if str(item["artifact_id"]) != probe_artifact),
                None,
            )
            assert downstream is not None, [item["artifact_id"] for item in readings]
            payload = _artifact_content(client, str(downstream["artifact_id"]))

            # 实验是否留下了 run 级证据：`GET /runs/{id}/evidence` 里带
            # `experiment_run_id` 的条目（既有字段；实验证据的形态）。
            experiment_evidence = [item for item in reads.evidence if item.get("experiment_run_id")]
            assert experiment_evidence, (
                "实验必须留下带 experiment_run_id 的证据（否则下游读不到它）",
                reads.evidence,
            )
            consumed = {str(item.get("id")) for item in payload.get("evidence", [])}
            missing = sorted({str(item["id"]) for item in experiment_evidence} - consumed)
            assert missing == [], (
                "下游 evidence.read 的返回内容必须含**实验**留下的证据 id（否则『跑完没人看』）",
                missing,
                sorted(consumed),
            )


class TestARaisedThresholdRejectsAndNamesTheNumber:
    """④ 反证：把可否证的判据抬到实验达不到的水平 ⇒ 判拒并**点名那个数**。

    这条同时证明**那道阈值是真的判据**（不是装饰）：同一份协议、同一套装配，
    **只**改那一个阈值 ⇒ 该 phase 判负且判词里出现实测值。
    """

    def test_an_unreachable_threshold_fails_the_run_and_names_the_value(
        self, mock_relay: str
    ) -> None:
        deps = _assembled_deps(mock_relay, falsify_threshold=1_000_000)
        with TestClient(_app(deps)) as client:
            reads = _read_chain(client, _start(client, _PROTOCOL))

        assert reads.run["state"] == "FAILED", (reads.run, reads.failures)
        assert reads.failures, "失败必须带判词"
        joined = " ".join(reads.failures)
        assert _METRIC in joined, (
            "判词必须点名那条指标（否则无法判断是哪条判据拒的）",
            reads.failures,
        )
        assert "GTE" in joined and "1000000" in joined.replace(",", ""), (
            "判词必须给出比较式（实测值 + 算子 + 阈值）",
            reads.failures,
        )


class TestTheRunChainFaceIsTheSameOneAsEc01:
    """受判面自检：本协议的三条读能力与 EC-01 同一组（同一条「已放行」约束）。"""

    def test_the_protocol_declares_the_three_granted_capabilities(self) -> None:
        from pathlib import Path

        import yaml

        raw = yaml.safe_load(Path(f"examples/protocols/{_PROTOCOL}").read_text(encoding="utf-8"))
        phases = {phase["id"]: phase for phase in raw["phases"]}
        assert set(phases) == {"probe", "experiment", "verdict"}, sorted(phases)
        for phase_id in ("probe", "verdict"):
            assert phases[phase_id].get("capability_execution") == "run_chain", phases[phase_id]
            assert set(phases[phase_id]["required_capabilities"]) == set(_CAPABILITIES), (
                phase_id,
                phases[phase_id]["required_capabilities"],
            )
        assert phases["experiment"]["task_contract"] == _EXPERIMENT_CONTRACT, phases["experiment"]


class TestTheFalsifiableCriterionIsPinnedInTheCatalog:
    """**受判面自检（本轮实测抓到的一处判据缺口）**：那条判据必须真的在**出厂目录**里。

    为什么单列一类：反证臂（`TestARaisedThresholdRejectsAndNamesTheNumber`）改的是
    **运行时快照**（`preflight_override`），它证明「阈值被真的判了」；但**出厂目录里那条
    阈值本身**若被改小（实测：把 100 改成 1），反证臂**仍会通过** —— 于是「本协议对科学结论
    下了一道可否证的判据」这句话就**没有受判**（判据被写窄：只判了机制，漏了那个数）。
    本类把**目录里的事实**钉住：判据在场、指标名对、算子对、阈值对，且实验的**实测**返回值
    确实在阈值之上（**非空真**：阈值不是随便写的数）。
    """

    def test_the_catalog_carries_the_metric_threshold(self) -> None:
        from decimal import Decimal

        from adapters.contracts import load_task_contracts
        from packages.domain.enums import AcceptanceCriterionType, ComparisonOperator

        contract = load_task_contracts("examples/contracts/task_contracts.yaml")[
            _EXPERIMENT_CONTRACT
        ]
        matched = [
            item
            for item in contract.acceptance_criteria
            if item.type is AcceptanceCriterionType.METRIC_THRESHOLD
        ]
        assert len(matched) == 1, (
            "本协议必须恰有一条 METRIC_THRESHOLD（可否证的科研判据）",
            [item.type.value for item in contract.acceptance_criteria],
        )
        criterion = matched[0]
        assert criterion.metric == _METRIC, criterion.metric
        assert criterion.operator is ComparisonOperator.GTE, criterion.operator
        assert criterion.threshold == Decimal(_THRESHOLD), (
            "阈值必须是写死的那个数（改小它 = 让这条判据不再可否证）",
            criterion.threshold,
        )

    def test_the_experiment_output_actually_clears_the_threshold(self) -> None:
        """非空真：实验的**实测**值确实在阈值之上 ⇒ 这道判据是**可达**的（不是恒假装饰）。"""
        import json as _json
        import os
        import subprocess
        import sys
        import tempfile
        from pathlib import Path as _Path

        # 仓库绝对路径：子进程的 cwd 是临时目录（脚本自己往 cwd 写 `metrics`）。
        script = _Path(__file__).resolve().parents[2] / _EXPERIMENT_SCRIPT
        assert script.is_file(), script
        with tempfile.TemporaryDirectory() as tmp:
            completed = subprocess.run(  # noqa: S603 - 固定脚本路径，无外部输入
                [sys.executable, str(script)],
                cwd=tmp,
                env=dict(os.environ, EXPERIMENT_RUN_ID="probe-threshold-check"),
                capture_output=True,
                text=True,
                check=False,
            )
            assert completed.returncode == 0, (completed.stdout, completed.stderr)
            metrics = _json.loads((_Path(tmp) / "metrics").read_text(encoding="utf-8"))
        observed = float(metrics[_METRIC])
        assert observed >= _THRESHOLD, (
            "实验实测值必须真的越过阈值（否则那条判据是恒假装饰）",
            observed,
            _THRESHOLD,
        )
