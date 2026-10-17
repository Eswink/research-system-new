"""GOAL-20261016-081 EC-04 的 **live 判据**：模型**引用**了它看到的检索标识。

**它判什么**（在本 GOAL 的阶梯上是最关键的一格）：cycle 1/2 在受控装配上证了
「摘录进提示词」与「逐条逐字可核对」；本判据判**真实模型侧的下一步** ——
**模型是否真的用上了它看到的东西**。

两条读数（**成对**，缺一即不可信）：

1. **它看到了什么**：提示词里带**本次 run** 的检索标识（PMID / DOI 形态）——
   与读面制品的 `entries[].identifier` **同源**（不是随便一串数字）；
2. **它用上了什么**：模型写出的计划正文里**引用了**其中**至少一条**标识。

**为什么第 2 条是「立题因检索而不同」的最小可判证据**：GOAL-080 EC-04 的真实 run 里
模型自陈「I have no source list, abstracts, or retrieved records in my context …
doing so would require inventing a citation, which I won't do」—— 它**明确拒绝编造引用**。
⇒ 若这条 run 里它**引用了**某个标识，那个标识只可能来自**它看到的那一段**。

**降级梯**（GOAL 原文逐字）：模型侧不可用**或模型不引用** ⇒ 记 PENDING + 点名阻塞点，
**不得**伪造。判据因此把「没引用」与「没看到」分开点名。

**离线纪律**：默认门下如实 skip（`requires_live_llm` + 显式开关）。

用法（与既有 live 判据同一口令形态）：

    set -a; . ./.env; set +a
    RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 \
      uv run --frozen --no-sync python -B -m pytest
      tests/e2e/test_the_model_cites_the_retrieved_identifiers_live.py -q
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

_RUN_ID = "run-goal081-ec04-live-cites"
#: **带独立侦察相**的协议（检索在 `plan` 之前跑完 ⇒ 立题能看见它）。
_PROTOCOL = "grounded_report_chain_v1.yaml"
#: 与 GOAL-080 的 live 判据同一条装配（**只改实验段那一行**，其余同源）。
pytestmark = pytest.mark.requires_live_llm

#: 标识形态（与 `retrieval_context._identifier_of` 同一口径：PMID 数字串 / DOI 形态）。
_PMIDish = re.compile(r"^\d{7,}$")


def _gate() -> Any:
    import os

    from adapters.relay.credential_resolver import EnvCredentialResolver
    from packages.application.model_relay.live_run_gate import evaluate_live_run_gate
    from services.api.runtime_support import OPENHANDS_RUNTIME
    from tests.e2e.live_switch_support import live_e2e_switch_enabled
    from tests.e2e.test_research_report_chain_live import _endpoint

    return evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=_endpoint(),
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=live_e2e_switch_enabled(),
    )


def _live_deps(db_path: str) -> Any:
    """**既有 live 装配**（连报告汇编与检索上下文一起接好）+ 本判据要的那一段。

    与 GOAL-080 EC-04 的 live 判据同源：那段装配已经把三段执行体缝接好；本判据只需要
    **报告与上下文**（它判的是「模型引用」），因此**不改**实验段。
    """
    from tests.e2e.test_research_report_chain_live import _live_deps as _base

    return _base(db_path)


def _run_once(deps: Any) -> dict[str, Any]:
    """跑一次真实 run，取回本判据要的三样：提示词那段 / 计划正文 / 读面标识。"""
    from fastapi.testclient import TestClient

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
        artifacts = client.get(f"/runs/{run_id}/artifacts").json()
        sample: dict[str, Any] = {
            "run_id": run_id,
            "state": run["state"],
            "artifact_ids": [str(item["id"]) for item in artifacts],
        }

        # ① 读面：检索标识（上下文制品里的 `entries[].identifier`）。
        context_ids = [
            str(item["id"]) for item in artifacts if str(item["id"]).endswith(":retrieval_context")
        ]
        identifiers: set[str] = set()
        for artifact_id in context_ids:
            payload = client.get(f"/artifacts/{artifact_id}/content").json()
            for entry in payload.get("entries", ()):
                if entry.get("identifier"):
                    identifiers.add(str(entry["identifier"]))
        sample["retrieved_identifiers"] = sorted(identifiers)

        # ② 计划正文（模型写的；含它引用的东西）。
        sample.update(_plan_content(client, sample["artifact_ids"]))

        # ③ 会话提示词那段（本 GOAL 的接缝；判「它看到了什么」）。
        sample["prompt_sections"] = _prompt_sections(deps)
        sample["sections_by_contract"] = _sections_by_contract(deps)
    return sample


def _plan_content(client: Any, artifact_ids: list[str]) -> dict[str, Any]:
    """计划制品 → `{plan_artifact_id, plan_status, plan_content}`（只经既有读面取数）。"""
    plan_ids = [item for item in artifact_ids if item.endswith(":research_plan")]
    where: dict[str, Any] = {"plan_artifact_id": plan_ids[0] if plan_ids else None}
    if not plan_ids:
        return where
    body = client.get(f"/artifacts/{plan_ids[0]}/content")
    where["plan_status"] = body.status_code
    if body.status_code == 200:
        raw = json.loads(body.content.decode("utf-8", errors="replace"))
        if isinstance(raw, Mapping):
            where["plan_content"] = str(raw.get("content") or "")
    return where


def _prompt_sections(deps: Any) -> list[str]:
    """本 run 里**带检索那一段**的会话提示词（逐个会话读 spec 上的 `retrieval_prompt`）。"""
    recorder = deps.session_specs
    if recorder is None:
        return []
    return [
        str(spec.retrieval_prompt)
        for spec in recorder.specs.values()
        if getattr(spec, "retrieval_prompt", None)
    ]


def _sections_by_contract(deps: Any) -> dict[str, str]:
    """**逐合约**的检索段（`{contract_id: 段落}`）—— 判据要能说出「哪个会话拿到了它」。

    只判「存在某段」会让「它进了**下游**而不是写计划的那个会话」这种形态**假绿**；
    本读数把它区分开（EC-04 实测正是这个形态）。
    """
    recorder = deps.session_specs
    if recorder is None:
        return {}
    return {
        contract_id: str(spec.retrieval_prompt)
        for contract_id, spec in recorder.specs.items()
        if getattr(spec, "retrieval_prompt", None)
    }


def _assert_the_model_cited_what_it_saw(sample: dict[str, Any]) -> None:
    """两条成对读数：**看到了**（提示词带本次 run 的标识）+ **用上了**（正文引用 ≥ 1 条）。"""
    assert sample["state"] == "SUCCEEDED", (sample["state"], sample)
    identifiers = set(sample["retrieved_identifiers"])
    assert identifiers, (
        "**先决条件**：真实 run 必须取回可读标识（否则本判据在空集上恒真）",
        sample["artifact_ids"],
    )

    # **必须点名 `research_report_plan`**：只判「某个会话拿到了」会让
    # 「它进了**下游** `multi_role_review` 而不是写计划的会话」这种形态**假绿**
    # —— 那正是本 cycle 实测到的形态（下游有、plan 没有）。
    by_contract = sample.get("sections_by_contract") or {}
    assert by_contract.get("research_report_plan"), (
        "**它看到了什么**：**写计划的那个会话**（`research_report_plan`）的提示词里必须有检索那一段。"
        "（只判「某个会话有」不够 —— 下游 `multi_role_review` 有而 plan 没有，"
        "正是实测抓到的形态。）",
        sorted(by_contract),
    )
    prompt_sections = [by_contract["research_report_plan"]]
    # **逐字拼接**再判包含（`set().union(*strings)` 会按**字符**并集 —— 实测踩过：
    # 那种写法把「哪些标识在提示词里」判成空集）。
    shown = "".join(prompt_sections)
    cited_in_prompt = {name for name in identifiers if name in shown}
    assert cited_in_prompt, (
        "提示词那段必须携带**本次 run** 的检索标识（不是随便一串数字）",
        sorted(identifiers),
        [text[:200] for text in prompt_sections],
    )

    content = sample.get("plan_content") or ""
    assert content, (
        "模型必须留下计划正文",
        sample.get("plan_artifact_id"),
        sample.get("plan_status"),
    )
    cited = {name for name in identifiers if name in content}
    assert cited, (
        "**它用上了什么**：模型的计划正文必须**引用**至少一条它看到的标识 —— "
        "这正是「立题因检索而不同」的最小可判证据。"
        "（GOAL-080 的真实 run 里模型明确拒绝编造引用 ⇒ 引用只可能来自它看到的那段。）",
        sorted(identifiers),
        content[:600],
    )


def test_the_model_cites_a_retrieved_identifier(tmp_path: Path) -> None:
    """真实 run：模型**看到了**检索标识，且在计划里**引用**了它。"""
    gate = _gate()
    if not gate.open:
        from packages.application.model_relay.live_run_gate import skip_record_for_gate

        pytest.skip(f"live run skipped: {skip_record_for_gate(_RUN_ID, gate).reason}")

    deps = _live_deps(str(tmp_path / "control-plane.db"))
    sample = _run_once(deps)
    Path("scratch").mkdir(exist_ok=True)
    (Path("scratch") / f"goal081-ec04-{sample['run_id']}.json").write_text(
        json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _assert_the_model_cited_what_it_saw(sample)
