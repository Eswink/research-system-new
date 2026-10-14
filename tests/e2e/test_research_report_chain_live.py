"""GOAL-20261014-077 **EC-04** live 判据：新站真实 run 跑完整研究链并留下报告。

**判什么**（一次真实 run，点名 `research_report_chain_v1.yaml`，**产品组合根**
+ `preflight_override is None` + 真实执行体）：

1. **终态恰为 `SUCCEEDED`**（`FAILED` 也是终态，但不在这里算通过）；
2. **报告制品在位**：`{run_id}:research_report.md` 在 `GET /runs/{id}/artifacts` 上，
   `GET /artifacts/{id}/content` 内联 `text/markdown`；
3. **四节齐全**且**每数字可溯源**：报告里的来源标识与 `GET /runs/{id}/evidence` 的
   检索证据逐条一致；指标值与 `GET /runs/{id}/experiments` 的落库值**逐字相同**；
4. **报告落盘**：正文写入 `scratch/goal077-ec04-<run_id>.md` 供人读（本判据的交付面）。

**默认门**：与既有 live 判据同一道（`evaluate_live_run_gate`）：runtime **显式配置**为
`openhands` + 登记端点的凭据**可解析** + live 开关打开。三者缺一 ⇒ **如实 skip**。

跑它（凭据由操作者注入；本文件不读值、不回显、不落盘）：

    set -a; . ./.env; set +a
    RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 \
      uv run --frozen --no-sync python -B -m pytest \
      tests/e2e/test_research_report_chain_live.py -q -rs

**失败如何落终态**：失败**也是**终态。跑不绿就如实归类（端点面 / 协议面 / 装配面）并按
fix_policy 纠错 —— **不得**把 `FAILED` 写成成功、**不得**降低判据迁就实现。
按 GOAL 的降级梯：模型侧不可用 ⇒ 记 PENDING + 点名阻塞点（**不伪造**）。

**如实边界**：本判据证明「报告在**真实中转站**上的一次完整研究里被产出且可复核」；
它**不**声称报告是模型撰写的（那是确定性汇编），也**不**声称检索内容进了模型上下文。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from adapters.contracts.models_loaders import load_llm_endpoints
from adapters.relay.credential_resolver import EnvCredentialResolver
from packages.application.deliverable.research_report import (
    REPORT_ARTIFACT_NAME,
    REPORT_MIME,
    SECTION_HEADINGS,
)
from packages.application.model_relay.live_run_gate import (
    evaluate_live_run_gate,
    skip_record_for_gate,
)
from services.api.runtime_support import OPENHANDS_RUNTIME
from tests.e2e.live_switch_support import live_e2e_switch_enabled

pytestmark = pytest.mark.requires_live_llm

_ENDPOINTS = "examples/config/llm_endpoints.yaml"
_ENDPOINT = "main"
_PROTOCOL = "research_report_chain_v1.yaml"
_PROTOCOL_ID = "research_report_chain_v1_0_0"
_RUN_ID = "run-goal077-ec04-live-report"
#: 交付面：报告正文落盘（人能直接读的那一份）。
_SAMPLE_DIR = Path("scratch")
#: 装配方给出的沙箱实验脚本与镜像（合约 `experiment_execution` 不 pin 这两个量）。
_EXPERIMENT_SCRIPT = "examples/experiments/exact_match_index_benchmark.py"
_EXPERIMENT_IMAGE = "research-os-sandbox:m9-test"


def _endpoint() -> Any:
    return load_llm_endpoints(_ENDPOINTS)[_ENDPOINT]


def _gate() -> Any:
    return evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=_endpoint(),
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=live_e2e_switch_enabled(),
    )


def _live_deps(db_path: str) -> Any:
    """产品组合根 + 三段**执行体**缝（报告汇编 / 运行链检索 / 沙箱实验）。

    只注入执行体，**不**注入判词：`preflight_override` 必须为 `None`
    （与 `live_control_plane_support` 同一条纪律）。
    """
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.catalog_merge import merged_catalog_snapshot
    from services.api.composition import assemble
    from services.api.report_support import report_task_runner
    from services.api.settings import ApiSettings

    deps = assemble(ApiSettings(db_path=db_path))
    assert deps.preflight_override is None, "live 判据不得带任何 preflight_override"
    assert deps.runs is not None and deps.artifacts is not None, (
        "产品组合根必须给出编排服务与制品店（live 判据的直接前提）"
    )
    deps.tool_providers = _probeable_providers(deps)
    catalog = merged_catalog_snapshot(deps)
    inner = deps.runs._deps
    deps.runs = RunOrchestrationService(
        replace(
            inner,
            capabilities=_capability_step(deps, deps.tool_providers["europe_pmc"], catalog),
            experiment_task=_sandbox_runner(deps),
            report_task=report_task_runner(
                artifacts=deps.artifacts,
                ledger=deps.ledger,
                review_findings=deps.review_findings,
            ),
        )
    )
    _register_session_tools(deps)
    return deps


def _probeable_providers(deps: Any) -> dict[str, Any]:
    """两件 REST provider 的**可探测实例**（真传输；健康由**真探测**得出）。

    两件都要：本协议的能力面同时含 `europe_pmc`（运行链检索）与 `ncbi_eutils`
    （评审格的会话绑定）—— 只注册一件时另一件的健康是三态里的 `UNKNOWN`，而冻结对
    「未获接受通道的 EXECUTE 风险警示」**点名拒冻**（实测：`WARNING TOOL_HEALTH_UNPROVEN
    (provider:ncbi_eutils) is not an explicitly allowed EXECUTE risk`）。
    """
    from adapters.research_tools import EuropePmcProvider, NcbiEutilsProvider

    return {
        "europe_pmc": EuropePmcProvider(deps.artifacts, spill_threshold_bytes=1),
        "ncbi_eutils": NcbiEutilsProvider(
            deps.artifacts, credentials=deps.credentials, spill_threshold_bytes=1
        ),
    }


def _sandbox_runner(deps: Any) -> Any:
    """沙箱实验执行体（脚本与镜像由**装配上下文**给出：合约不 pin 这两个量）。"""
    from services.api.experiment_support import (
        docker_experiment_assembly,
        sandbox_experiment_runner,
    )

    return sandbox_experiment_runner(
        docker_experiment_assembly(
            artifacts=deps.artifacts,
            ledger=deps.ledger,
            policy=deps.policy_evaluator,
            script=_EXPERIMENT_SCRIPT,
            image=_EXPERIMENT_IMAGE,
            experiment_store=deps.experiment_store,
        )
    )


def _capability_step(deps: Any, provider: Any, catalog: Any) -> Any:
    from packages.application.run_orchestration.phase_capabilities import CapabilityDeps
    from tests.e2e.literature_chain_support import europepmc_calls

    spec = catalog.tool_providers["europe_pmc"]
    return CapabilityDeps(
        calls=europepmc_calls(),
        providers={str(spec.id): provider},
        provider_specs={str(spec.id): spec},
        policy=deps.policy_evaluator,
        artifacts=deps.artifacts,
        ledger=deps.ledger,
    )


def _register_session_tools(deps: Any) -> None:
    """把**出厂形态**的会话工具注册面接进真实 runtime（与产品组合根同一手法）。

    与产品组合根的区别只有一处：本判据的 runtime 由这里构造（`build_agent_runtime`
    需要 `register_session_tools` 才认得出协议声明的绑定）。

    `workspace_allow_host_shell=True`：本协议有**两个真实会话 phase**（立题 / 评审），
    而 workspace 的 host shell **默认 deny**（AGENTS.md §9）⇒ 不显式打开就建不起会话。
    这与既有 live 判据同一条做法（`openhands_deps(..., allow_localhost=False)` 那一条
    用的是测试侧 workspace 构造器；本判据走**产品**构造器，所以这个开关要显式给）。
    **生产默认不放松**：本处只影响这一次受判 run 的装配。
    """
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService
    from services.api.settings import ApiSettings

    settings = ApiSettings(agent_runtime=OPENHANDS_RUNTIME, workspace_allow_host_shell=True)
    register = _register_with_literature(deps)
    from services.api.runtime_support import build_agent_runtime

    runtime = build_agent_runtime(
        settings,
        credentials=deps.credentials,
        policy_evaluator=deps.policy_evaluator,
        budget_ledger=deps.budget,
        register_session_tools=register,
    )
    deps.runs = RunOrchestrationService(replace(deps.runs._deps, runtime=runtime))


def _register_with_literature(deps: Any) -> Any:
    """会话工具注册面 = **出厂绑定** ∪ **本协议声明的文献绑定**。

    为什么需要后一半（如实登记的产品缺口）：出厂绑定表
    （`session_tool_support.DEFAULT_SESSION_TOOL_BINDINGS`）只覆盖 canonical 读面；
    本协议还把 `literature.search` / `literature.read` 声明为**会话工具**
    （评审格的四条绑定之一），而协议声明的是**名字**——「那个名字桥到哪个 provider 的
    哪个 tool id」是**装配方**的事（`session_tool_register` 的既有分工）。
    本函数以装配方身份补上那两条：桥到**真** `EuropePmcProvider` / `NcbiEutilsProvider`，
    走与出厂绑定**同一个** `make_tool_invoker`（同一条策略 + 执行面）。

    **不改产品代码**：缺的只是装配方的一张实现表（与 GOAL-028 `W-1` 同一类缺口，
    如实登记在 GOAL-077 的残余里）。
    """
    from services.api.session_tool_support import (
        DEFAULT_SESSION_TOOL_BINDINGS,
        session_tool_register,
    )

    literature_bindings = (
        # (工具名 / 能力名, provider_id, provider 侧 tool_id)
        ("literature.search", "ncbi_eutils", "literature_search"),
        ("literature.read", "europe_pmc", "literature_read"),
    )
    instances = {
        provider_id: deps.tool_providers[provider_id] for _, provider_id, _ in literature_bindings
    }
    # 一张实例表要同时满足两类名字（出厂读面 + 本协议的文献）：出厂注册面只收一张表。
    providers = {**instances, **_read_provider_instances(deps)}
    return session_tool_register(
        providers=providers,
        provider_specs=_provider_specs(deps, tuple(providers)),
        artifacts=deps.artifacts,
        policy=deps.policy_evaluator,
        bindings=(*DEFAULT_SESSION_TOOL_BINDINGS, *literature_bindings),
    )


def _read_provider_instances(deps: Any) -> dict[str, Any]:
    """canonical 读面 provider 的实例（`m12_artifact` / `openhands_workspace` 共用一件）。

    与出厂 `canonical_read_register` 造的是**同一形态**的实例（读 canonical state）；
    本判据需要把它和文献实例放进**同一张**表 —— 出厂注册面只接受一张实例表，
    而本协议同时用到两类名字。
    """
    from adapters.canonical import CanonicalReadProvider

    reader = CanonicalReadProvider(
        deps.artifacts,
        deps.ledger,
        budget_ledger=deps.budget,
        experiment_store=deps.experiment_store,
        run_store=deps.runs_store,
        review_store=deps.review_findings,
        memory_store=deps.memory,
    )
    return {"m12_artifact": reader, "openhands_workspace": reader}


def _provider_specs(deps: Any, provider_ids: tuple[str, ...]) -> dict[str, Any]:
    """出厂目录里那几件 provider 的**声明**（不在测试里重写一份）。"""
    from services.api.catalog_merge import merged_catalog_snapshot

    catalog = merged_catalog_snapshot(deps)
    return {pid: catalog.tool_providers[pid] for pid in provider_ids}


def _execute(deps: Any) -> dict[str, Any]:
    """一次真实 run（产品组合根 + 既有 API），取回读面并**把报告落盘**。"""
    from services.api.app import create_app

    with TestClient(create_app(deps)) as client:
        created = client.post(
            "/projects/example-project/runs",
            json={"protocol_path": _PROTOCOL},
            headers={"Idempotency-Key": _RUN_ID},
        )
        assert created.status_code == 200, created.text
        run_id = str(created.json()["id"])
        run = client.get(f"/runs/{run_id}").json()
        events = client.get(f"/runs/{run_id}/events").json()
        artifacts = client.get(f"/runs/{run_id}/artifacts").json()
        report_id = f"{run_id}:{REPORT_ARTIFACT_NAME}"
        content = client.get(f"/artifacts/{report_id}/content")
        sample: dict[str, Any] = {
            "run_id": run_id,
            "state": run["state"],
            "protocol_id": run["protocol_id"],
            "manifest_digest": run["manifest_digest"],
            "failures": [
                event["payload"].get("message", "")
                for event in events
                if event["type"] in ("run.failed", "task.failed")
            ],
            "artifact_ids": [str(item["id"]) for item in artifacts],
            "report_status": content.status_code,
            "report_content_type": content.headers.get("content-type", ""),
            "evidence": client.get(f"/runs/{run_id}/evidence").json(),
            "experiments": client.get(f"/runs/{run_id}/experiments").json(),
        }
        if content.status_code == 200:
            report = content.content.decode("utf-8")
            sample["report_sha256_len"] = len(report)
            _write_report(sample, report)
            sample["report_path"] = str(_report_path(run_id))
    return sample


def _report_path(run_id: str) -> Path:
    return _SAMPLE_DIR / f"goal077-ec04-{run_id}.md"


def _write_report(sample: dict[str, Any], report: str) -> None:
    """报告正文落盘（交付面：人能直接读的那一份）。"""
    _SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    _report_path(sample["run_id"]).write_text(report, encoding="utf-8")
    sample["report_body"] = report


def _assert_live_report(sample: dict[str, Any]) -> None:
    """EC-04 的判据本体：终态 + 报告在位 + 四节 + 每数字可溯源。"""
    assert sample["protocol_id"] == _PROTOCOL_ID, sample
    assert sample["state"] == "SUCCEEDED", (
        "只有 SUCCEEDED 是成功（FAILED 也是终态，但不是通过）",
        sample["failures"],
        sample,
    )
    assert sample["manifest_digest"], "冻结必须真的发生"
    assert not sample["failures"], sample["failures"]

    report_id = f"{sample['run_id']}:{REPORT_ARTIFACT_NAME}"
    assert report_id in sample["artifact_ids"], (
        "报告制品必须在 run 的制品读面上",
        sample["artifact_ids"],
        sample["failures"],
    )
    assert sample["report_status"] == 200, sample["report_status"]
    assert REPORT_MIME in sample["report_content_type"], sample["report_content_type"]

    report = sample["report_body"]
    for heading in SECTION_HEADINGS:
        assert heading in report, (heading, report[:400])

    # 来源：报告里的标识与证据读面的检索来源逐条一致（真标识，不是自述）。
    retrieved = [item for item in sample["evidence"] if item.get("tool_refs")]
    assert retrieved, ("真实 run 必须有检索证据", sample["evidence"])
    report_digits = _identifiers_of(retrieved)
    assert report_digits, ("检索证据里必须读得出标识", retrieved)
    missing = sorted(item for item in report_digits if item not in report)
    assert missing == [], ("报告必须逐字给出检索到的标识", missing, report[:600])

    # 指标：报告里的值 == experiments 读面上的值（逐字）。
    entries = sample["experiments"]["experiments"]
    if entries:
        for name, value in (entries[0].get("metrics") or {}).items():
            assert str(name) in report, (name, report[:600])
            assert _metric_text(value) in report, (name, value, report[:600])


def _identifiers_of(retrieved: list[dict[str, Any]]) -> set[str]:
    """检索证据里可读的标识（逐条从 `source_ref` / `id` 里取 PMID / DOI 形态的串）。

    判据侧**不**去读制品内容重算一遍标识：报告自己已经给出标识，这里要判的是
    「报告给的标识确实是这次检索里的那些」——取自读面上那条证据的同一串。
    """
    found: set[str] = set()
    for item in retrieved:
        text = f"{item.get('id', '')} {item.get('source_ref', '')}"
        for token in text.replace(":", " ").replace("+", " ").split():
            if token.isdigit() and len(token) >= 7:
                found.add(token)
            elif token.count(".") >= 2 and "/" in token:
                found.add(token)
    return found


def _metric_text(value: object) -> str:
    """读面指标值 → 报告里应逐字出现的文本（与报告读取面同源；判据里重写这条规则）。"""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def test_the_new_relay_runs_the_full_chain_and_leaves_a_report(tmp_path: Path) -> None:
    """一次真实 run：新站 + 完整协议 ⇒ 终态 `SUCCEEDED` 且报告落盘可复核。"""
    gate = _gate()
    if not gate.open:
        pytest.skip(f"live run skipped: {skip_record_for_gate(_RUN_ID, gate).reason}")

    deps = _live_deps(str(tmp_path / "control-plane.db"))
    sample = _execute(deps)
    if sample["state"] != "SUCCEEDED":
        (tmp_path / "ec04-sample.json").write_text(
            json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    _assert_live_report(sample)
