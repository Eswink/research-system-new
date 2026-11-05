"""GOAL-20261104-106 EC-01/EC-03：**十一相链在真实模型 + 真实中转站下跑到一次 `SUCCEEDED`**。

**它补哪一格**（本轮建档实测，2026-11-04 全仓 115 个 SQLite 逐一普查）：
`direction_to_manuscript_v1.yaml`（十一相）的**真实 run 合计 0 次**。它此前只被两种东西验证过
—— ① `tests/e2e/test_direction_to_manuscript_product_path.py`（**mock 中转站**）；
② `tests/e2e/test_productive_entry_runs_the_whole_chain.py`，而那条跑的是
`direction_to_report_v2`（七相）。GOAL-099/100/101/102/105 交付的全部机制（IMRaD 手稿 /
编辑四值决定 / 逐条应答 / 投稿包五件 / 引用结构读数）都落在这条从未真跑的链上。
本判据补的就是那一格。

**判据的形态照抄既有 live 判据**（`test_productive_entry_runs_the_whole_chain.py`，GOAL-097）：
`assemble()` 出来的 deps **一律不补缝** —— 不 `replace(deps.runs._deps, ...)`、不
`deps.tool_providers = {...}`、不调 `_attach_capabilities`。只做两件**运维上下文**的事：

1. 注入凭据 —— 那是部署配置，不是缝；
2. 显式 `preflight_override` —— 出厂探测面对 REST provider 诚实地收敛为 `UNKNOWN` ⇒
   `TOOL_HEALTH_UNPROVEN` **没有接受通道** ⇒ 拒冻。这是**既有**语义不一致，本轮不改门禁。

**判什么**（每条独立取证，读数**先写盘再断言** —— GOAL-096 `W-1` 的教训：旧写法只在
断言前写，失败路径根本走不到写盘）：

1. 终态恰为 `SUCCEEDED`（`FAILED` 也是终态，但**不是通过**）；
2. **十一件产物全部落 canonical 且可从读面取回字节** —— 九个会话产物 + 报告/手稿 +
   投稿五件 + 改稿两件；
3. **十一相各相 `SUCCEEDED` 且各带自己的产物**（读 `RunDetailDto.phases`，不从 id 猜相）；
4. **GOAL-105 的两件机制在真实手稿上生效**（EC-03）：`manuscript.md` 脚注里三个引用读数
   可解析且与正文重算逐项相等；`response_letter.md` 的每条 `action_taken` 与**它自己那条**
   评审点有实词重叠。

装配与取数在 `tests/e2e/manuscript_chain_live_support.py`（规模门：本文件守 450 行上限）。

**默认门**：`evaluate_live_run_gate`（runtime 显式 `openhands` + 凭据可解析 + live 开关）。
缺一 ⇒ **如实 skip**（skip 不是 PASS）。Docker 不可用亦 skip —— 实验相要沙箱镜像。

跑它（凭据只由操作者注入；本文件不读值、不回显、不落盘）：

    set -a; . ./.env; set +a
    RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 \\
      uv run --frozen --no-sync python -B -m pytest \\
      tests/e2e/test_the_manuscript_chain_runs_live.py -q -rs

**如实边界**：本判据证明的是一条**机械**事实 —— 十一相在真实条件下于**一次 run** 内成链、
十一件产物落在 canonical 且字节可读、两个 GOAL-105 读数真的产出过。它**不**判手稿写得好
不好、创新点真的新不新、评审公正不公正（那要人评或外部评审面板 —— 后者未获授权）。
"""

from __future__ import annotations

import os
from typing import Any

import pytest

from packages.application.model_relay.live_run_gate import skip_record_for_gate
from services.api.app import create_app
from tests.e2e.manuscript_chain_live_support import (
    OUTPUT_NAMES,
    PHASES,
    action_overlaps,
    assembled_product,
    drive_one_run,
    footnote_matches_body,
    preflight_override,
    reported_readings,
    write_readings,
)

pytestmark = [pytest.mark.requires_live_llm, pytest.mark.requires_docker]

#: 九个**会话产物**必须各自挂在自己的相上（`report` 除外：它是汇编相）。
_PHASE_OUTPUTS: tuple[tuple[str, str], ...] = (
    ("question", "research_question"),
    ("retrieval", "retrieval_report"),
    ("novelty", "novelty_claim"),
    ("plan", "research_plan"),
    ("experiment", "metrics"),
    ("review", "review_decision"),
    ("manuscript", "manuscript_narrative"),
    ("editorial", "editorial_decision"),
    ("revision", "author_responses"),
    ("submission", "submission_package"),
)


def _run_guarded(gate_name: str) -> dict[str, Any]:
    """过门 → 产品组合根起一次 run → 关 deps。门不开 ⇒ **如实 skip**（不是 PASS）。

    门**在本文件里**求值（`evaluate_live_run_gate(..., live_switch=...)`），不外包给支持件：
    `tests/architecture/python/test_live_switch_is_single_source.py` 要求每个带
    `requires_live_llm` 的模块**自己**经门或调同一个谓词 —— 否则「凭据在场就能起跑」
    这条单读点性质在这个模块上就断了。
    """
    from fastapi.testclient import TestClient

    from adapters.contracts.models_loaders import load_llm_endpoints
    from adapters.relay.credential_resolver import EnvCredentialResolver
    from packages.application.model_relay.live_run_gate import evaluate_live_run_gate
    from services.api.runtime_support import OPENHANDS_RUNTIME
    from tests.e2e.live_switch_support import live_e2e_switch_enabled

    endpoints = load_llm_endpoints("examples/config/llm_endpoints.yaml")
    gate = evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=endpoints["main"],
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=live_e2e_switch_enabled(),
    )
    if not gate.open:
        pytest.skip(str(skip_record_for_gate(gate_name, gate)))
    deps = assembled_product()
    try:
        deps.preflight_override = preflight_override(deps)
        with TestClient(create_app(deps)) as client:
            return drive_one_run(client)
    finally:
        deps.close()


def _assert_artifacts(readings: dict[str, Any]) -> None:
    """十一件产物全部落库且字节可读（投稿五件 + 改稿两件一并判）。"""
    assert readings["missing_artifacts"] == [], {
        "missing": readings["missing_artifacts"],
        "artifacts": readings["artifact_ids"],
    }
    for name in OUTPUT_NAMES:
        assert readings[f"present:{name}"], (name, readings["artifact_ids"])
        assert readings[f"length:{name}"] > 0, name


def _assert_phases(readings: dict[str, Any]) -> None:
    """十一相全 `SUCCEEDED`，且各相带着**自己的**产物（不是某一相冒充全部）。

    为什么 `report` 只判「有产物」：七件汇编制品（`manuscript.md` / 投稿五件 / 改稿两件）是
    **run 级** id（`{run_id}:manuscript.md`），不属于任何任务 ⇒ 相归属读面不把它们挂到
    `report` 相（本轮实测：该相只列 `research_report.md`）。它们由产物面判在场与字节。
    """
    states = readings["phase_states"]
    assert set(states) == set(PHASES), (sorted(states), sorted(PHASES))
    assert all(state == "SUCCEEDED" for state in states.values()), states
    for phase in PHASES:
        assert readings["phase_artifact_ids"].get(phase), f"phase {phase!r} owns no artifact"
    for phase, name in _PHASE_OUTPUTS:
        owned = [str(item) for item in readings["phase_artifact_ids"].get(phase) or []]
        assert any(item.endswith(f":{name}") for item in owned), (phase, name, owned)
    assert readings["experiment_rows"] >= 1, readings["experiment_rows"]


def test_the_eleven_phase_chain_runs_live() -> None:
    """真实模型 + 真实中转站：十一相一次 run 走完，产物落在 canonical 且字节可读。"""
    readings = _run_guarded("goal106-manuscript-chain")
    # ① 终态：`FAILED` 也是终态，但不在这里算通过（失败原因随读数落盘，可归因）。
    assert readings["http_status"] == 200, readings.get("http_body")
    assert readings["state"] == "SUCCEEDED", readings.get("failure_events")
    # ② ③ 产物面 + 相级面。
    _assert_artifacts(readings)
    readings["artifact_owners"] = {
        phase: readings["phase_artifact_ids"].get(phase) for phase in PHASES
    }
    write_readings(readings)
    _assert_phases(readings)


def test_the_goal105_readings_hold_on_the_real_manuscript() -> None:
    """GOAL-105 的两件机制在**真实手稿**上生效（EC-03）：读数可读 + 应答逐点有实词重叠。"""
    readings = _run_guarded("goal106-goal105-readings")
    if readings.get("state") != "SUCCEEDED":
        pytest.fail(f"the run did not succeed: {readings.get('failure_events')}")

    manuscript = str(readings.get("manuscript") or "")
    letter = str(readings.get("response_letter") or "")
    review = str(readings.get("review_decision") or "")

    # ① 脚注里的三条读数**可解析**、与正文重算**逐项相等**（不是抄来的数字）。
    reported = reported_readings(manuscript)
    readings["citation_readings"] = reported
    readings["readings_match_body"] = bool(
        reported is not None and footnote_matches_body(manuscript, reported)
    )
    # ② 应答信每条的 `action_taken` 与**它自己那条**评审点有实词重叠（按 `### P<n>` 配对）。
    readings["action_overlap"] = action_overlaps(letter, review)
    write_readings(readings)

    assert reported is not None, "manuscript.md 的脚注里没有引用读数行"
    assert reported[0] > 0 and reported[1] > 0, reported
    assert readings["readings_match_body"], (reported, "脚注数字与正文重算不一致")
    actions, overlapped = readings["action_overlap"]
    assert actions >= 1, "response_letter.md 里没有任何 `**Action taken.**` 行"
    assert overlapped == actions, (actions, overlapped)
