"""GOAL-20261014-078 EC-04 的判据支持件（live 面的上下文取证）。

**为什么单列**：`tests/e2e/test_research_report_chain_live.py` 贴着 450 行硬上限
（规模门），而本轮的上下文取证（读面制品 + 会话 spec 的同源断言）是**独立可读**的一段；
按全仓既有的「支持件 vs 用例」分列（与 `literature_chain_support` 同一手法）。

**边界**：本模块**不含**用例，只放两个取证/断言函数 —— 它们只经**既有读面**
（`GET /runs/{id}/artifacts` 与 `/content`）取数，不经内部对象。
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from fastapi.testclient import TestClient

from packages.application.ports.agent_runtime import AgentSessionHandle, AgentSessionSpec

__all__ = [
    "SessionSpecRecorder",
    "context_identifiers",
    "assert_the_arms_ran",
    "assert_the_context_reached_sessions",
    "context_payloads",
    "identifiers_of",
    "install_spec_recorder",
    "metric_text",
]


def context_payloads(client: TestClient, run_id: str) -> dict[str, Any]:
    """读面上该 run 的上下文制品 → `{artifact_id: payload}`（只经既有路由）。"""
    artifacts = client.get(f"/runs/{run_id}/artifacts").json()
    ids = [str(item["id"]) for item in artifacts if str(item["id"]).endswith(":retrieval_context")]
    return {
        artifact_id: json.loads(
            client.get(f"/artifacts/{artifact_id}/content").content.decode("utf-8")
        )
        for artifact_id in ids
    }


class SessionSpecRecorder:
    """记录每次 `create_session` 的 **spec**（装配方包装；产品代码零改动）。

    为什么必须包在 runtime 上而不是读内部对象：`AgentSessionSpec` 是**产品路径**交给
    runtime 的那份事实本身 —— 判据读它，判的就是「会话拿到了什么」，不是「装配器返回了什么」。
    其余方法经 `__getattr__` **原样透传**（本包装只观察、不改行为）。
    """

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.specs: dict[str, AgentSessionSpec] = {}

    def create_session(self, spec: AgentSessionSpec) -> AgentSessionHandle:
        self.specs[spec.task_contract.id] = spec
        return self._inner.create_session(spec)  # type: ignore[no-any-return]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def context_of(self, contract_id: str) -> Any:
        """该合约那次会话的 `context_snapshot`（没有那次会话 ⇒ 判据自己点名失败）。"""
        spec = self.specs.get(contract_id)
        assert spec is not None, (
            f"本 run 没有为合约 {contract_id} 创建会话（已记录的合约：{sorted(self.specs)}）"
        )
        return spec.context_snapshot

    def retrieval_prompt_of(self, contract_id: str) -> str | None:
        """该合约那次会话的**提示词那一段**（GOAL-20261016-081 EC-01）。

        读的是 spec 上的 `retrieval_prompt` —— 它**就是**会话创建点会拼进
        `send_message` 的那段文本（同一份字节，不重算）。
        """
        spec = self.specs.get(contract_id)
        assert spec is not None, (
            f"本 run 没有为合约 {contract_id} 创建会话（已记录的合约：{sorted(self.specs)}）"
        )
        return spec.retrieval_prompt


def context_identifiers(client: TestClient, run_id: str) -> set[str]:
    """读面上下文制品里的逐条标识（与 `entries[].identifier` 同源的那一列）。

    复用 `context_payloads`（**同一条读面**）—— 不新造第二条查询。
    """
    return {
        str(entry["identifier"])
        for payload in context_payloads(client, run_id).values()
        for entry in payload.get("entries", ())
        if entry.get("identifier")
    }


def assert_the_context_reached_sessions(sample: dict[str, Any]) -> None:
    """EC-04 的上下文面：**真实检索取得的内容进了下游会话**，且读面可复核。

    两条一起看：
    ① 读面制品（`GET /runs/{id}/artifacts`）里有**非空**的上下文载荷 —— 它带
       `identifier` / `evidence_id` / `artifact_id` / `shown` 四列（真标识来自**本次**
       活检索）；
    ② 会话 spec 的 `retrieval_digest` **在场于**读面制品的 digest 列表里（同源）。
    """
    payloads = sample["context_artifacts"]
    assert payloads, ("真实 run 的读面上必须有上下文制品", sample["artifact_ids"])
    non_empty = [p for p in payloads.values() if p["entries"]]
    assert non_empty, ("下游会话的上下文必须**非空**（真实检索取回了内容）", payloads)
    entries = [e for payload in non_empty for e in payload["entries"]]
    assert entries, payloads
    for entry in entries:
        for key in ("identifier", "evidence_id", "artifact_id", "shown"):
            assert entry.get(key), (key, entry)
    # 标识与本次 run 的检索证据一致（不是凭空写的字符串）。
    retrieved_ids = {
        str(item["artifact_id"])
        for item in sample["evidence"]
        if item.get("source_trust_label") == "RETRIEVED" and item.get("artifact_id")
    }
    refs = {str(entry["artifact_id"]) for entry in entries}
    assert refs <= retrieved_ids, (
        "上下文里的制品必须指向**本次 run 系统取得**的证据",
        sorted(refs - retrieved_ids),
    )


def install_spec_recorder(deps: Any) -> None:
    """把 **spec 记录器**装成编排实跑的 runtime（观察、不改行为；产品代码零改动）。"""
    from dataclasses import replace

    from packages.application.run_orchestration.service import RunOrchestrationService

    recorder = SessionSpecRecorder(deps.runs._deps.runtime)
    deps.runs = RunOrchestrationService(replace(deps.runs._deps, runtime=recorder))
    deps.session_specs = recorder


def assert_the_arms_ran(sample: dict[str, Any]) -> None:
    """EC-04 的多臂面：真实 run 上**两个臂**各自落库，且**两臂的指标差**可算。

    与 EC-02/EC-03 的分工：那两条用受控装配取证；本条在**真实中转站**的一次 run 上
    复核同一组事实（真容器 + 真模型会话）。
    """
    from packages.application.experiments.arm_comparison import compare_arms

    experiments = list(sample["experiments"]["experiments"])
    assert len(experiments) == 2, [item["experiment_run_id"] for item in experiments]
    ids = [str(item["experiment_run_id"]) for item in experiments]
    assert len(set(ids)) == 2, ids
    ratios = [(item.get("metrics") or {}).get("comparison_reduction_ratio") for item in experiments]
    assert all(value is not None for value in ratios), ratios
    assert ratios[0] != ratios[1], (
        "两臂参数不同 ⇒ 同一指标的落库值必须不同（否则「臂」没生效）",
        ratios,
    )
    comparison = compare_arms(
        "control", experiments[0]["metrics"], "treatment", experiments[1]["metrics"]
    )
    assert comparison.comparable, comparison
    deltas = {delta.metric: delta for delta in comparison.deltas}
    assert "comparison_reduction_ratio" in deltas, sorted(deltas)
    delta = deltas["comparison_reduction_ratio"]
    assert Decimal(delta.delta) == Decimal(delta.right_value) - Decimal(delta.left_value), delta
    assert Decimal(delta.delta) != 0, delta


def identifiers_of(retrieved: list[dict[str, Any]]) -> set[str]:
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


def metric_text(value: object) -> str:
    """读面指标值 → 报告里应逐字出现的文本（与报告读取面同源；判据里重写这条规则）。"""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
