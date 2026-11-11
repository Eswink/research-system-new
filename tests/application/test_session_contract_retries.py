"""会话合约重试声明的判据（GOAL-20261111-108 EC-06）与 live harness 开关（EC-07）。

**EC-06 封住的失败形态**：五份会话合约此前 `max_attempts: 1` + `retryable_categories: []`
⇒ 一次 `MODEL_RELAY_UNAVAILABLE` 就走 `retry budget exhausted`（终态），而根因是上游
延迟分布（实测 99.8/76.1/78.4s，一条 120.1s 超时）。现在 `max_attempts: 2` +
`backoff_seconds: 30` + **显式列类别**。

**EC-07 封住的失败形态**：live harness 写死 `allow_localhost_endpoints=False` ⇒ 换到
局域网后「产品能跑、判据不能跑」，那条判据永远证明不了产品面可用。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "examples" / "contracts" / "task_contracts.yaml"
LIVE_SUPPORT = ROOT / "tests" / "e2e" / "manuscript_chain_live_support.py"

#: 十一相链里十个**会话**契约中会在长会话上撞上游延迟的五个（其余会话契约同样受益，
#: 但这五个是实测失败过的：`manuscript` / `retrieval` / `review` / `revision` / `submission`）。
SESSION_CONTRACTS = (
    "research_manuscript",
    "retrieval_report_from_the_run_chain",
    "multi_role_review",
    "author_response",
    "submission_package",
)

#: 三个瞬时类别（与 `adapters/relay/transport.py` 的 `_RETRYABLE_CATEGORIES` 同源，
#: 加上 `MODEL_TIMEOUT`：OpenHands 路径把超时折成 `MODEL_RELAY_UNAVAILABLE`，但两条路径
#: 都声明才能同时覆盖）。
EXPECTED_CATEGORIES = {"MODEL_RELAY_UNAVAILABLE", "MODEL_RATE_LIMIT", "MODEL_TIMEOUT"}


def _contracts() -> dict[str, Any]:
    document: Any = yaml.safe_load(CONTRACTS.read_text(encoding="utf-8"))
    return dict(document.get("task_contracts") or document)


@pytest.mark.parametrize("name", SESSION_CONTRACTS)
def test_the_session_contract_retries_a_transient_upstream_failure(name: str) -> None:
    """每份会话合约：`max_attempts >= 2` + 声明退避 + 三个瞬时类别都在。"""
    policy: Any = _contracts()[name]["retry_policy"]
    assert policy["max_attempts"] >= 2, f"{name}: 一次瞬时失败仍是终态"
    assert policy.get("backoff_seconds", 0) > 0, (
        f"{name}: 没有退避 ⇒ 走不到 `retry deferred to the dispatcher`（→ PAUSED → 调度器）"
    )
    declared = set(policy.get("retryable_categories") or [])
    assert EXPECTED_CATEGORIES <= declared, f"{name}: 缺 {sorted(EXPECTED_CATEGORIES - declared)}"


@pytest.mark.parametrize("name", SESSION_CONTRACTS)
def test_the_retry_policy_is_not_an_empty_wildcard(name: str) -> None:
    """**反证臂**：`retryable_categories` **不得为空**。

    空表在本仓两处语义自相矛盾（`task_executor._retryable`：空 = 通配；
    `TaskContract.decide_failure`：空 = 全不重试）。显式列出来才不赌哪一处生效。
    """
    policy: Any = _contracts()[name]["retry_policy"]
    assert policy.get("retryable_categories"), f"{name}: 空类别表语义在两处相反"


def test_the_contracts_file_keeps_lf_line_endings() -> None:
    """**本轮踩过的坑**：把这份文件写成 CRLF 会打断一条用 LF 锚点的判据
    （`test_a_report_executor_on_the_manuscript_contract_is_refused` 在真文件上做字节按压）。

    这条判据把「行尾」也钉住 —— 它不是风格偏好：**有判据在字节层面读这个文件**。
    """
    raw = CONTRACTS.read_bytes()
    assert b"\r" not in raw, "task_contracts.yaml 必须保持 LF（有判据用 LF 锚点做字节按压）"


# ---------------------------------------------------------------- EC-07


def test_the_live_harness_reads_the_product_switch() -> None:
    """**EC-07**：live harness 必须读与产品**同一个**环境开关，不得写死 `False`。"""
    source = LIVE_SUPPORT.read_text(encoding="utf-8")
    assert "_allow_local_endpoints()" in source, "harness 没有读开关的入口"
    assert "RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS" in source, (
        "harness 必须读产品那个变量名（写别的名字 = 两套口径）"
    )
    assert "allow_localhost_endpoints=False" not in source, (
        "写死 False ⇒ 换到局域网后「产品能跑、判据不能跑」"
    )
