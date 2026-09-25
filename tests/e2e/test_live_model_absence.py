"""「模型不存在」的 provider 侧真实样本（GOAL-010 EC-04 / PLAN-20260921-130 WP3）。

**起点**（`RECHECK-124` W-2 的如实登记 + PLAN-130 的 E-8）：这条情形此前**只有装配层判据**
——`llm_factory` 只消费一个 `ModelDefinition`、「run 的装配路径不消费 fallback」的结构断言；
provider 侧的真实样本只有「无效凭据 ⇒ 401」那一条。本模块补的就是**缺的那一条**。

**为什么必须实测**（定案取舍 #3）：中转站完全可能把未知 model **静默映射**到别的模型
（那正是 AGENTS.md §4 要防的同名漂移）。所以「provider 会拒绝未知模型」这句话**不能推断**，
只能在一次真实调用里观测；观测结果**模糊就如实记模糊**，不改判据凑绿。

**预置条件（显式开关，单条命令内联前缀，不写任何文件）**：

    RESEARCHOS_LIVE_E2E=1 RESEARCHOS_LIVE_MODEL_ABSENCE_CASE=1 LLM_MAIN_KEY=<值> \
      pytest tests/e2e/test_live_model_absence.py -s

**两道门都关着就跑不成**：`RESEARCHOS_LIVE_E2E=1` 是 live run 的通用显式开关（D-11），
`RESEARCHOS_LIVE_MODEL_ABSENCE_CASE=1` 是本**反证样本**自己的预置条件（它会故意失败，
不该被顺手跑掉）。任一未声明 ⇒ **SKIP 并点名**缺的是哪一个。

**它判什么 / 不判什么**：

- 判：这一次调用**有没有**以「点名模型标识」的方式被拒；若它居然**成功**，返回的 model 名
  是不是**不同于**请求的那个（是 ⇒ 那就是一份**真实漂移样本**，如实留下）。
- 判：**是哪一步拒的**（连通性 `GET /models` 还是那次 chat）——两步都会产出同一个失败类别，
  不区分就可能把「中转站的 /models 挂了」写成「provider 拒了未知模型」。
- 不判：**不**声称「该 provider 对所有未知模型都如此」——单次观测的射程只到这一次
  （这一句是这条判据的射程声明，不是客套）。

**凭据纪律**：值由操作者用内联前缀给出（本文件**不**写任何可用字面量），只从环境读出；
失败消息**不得**含该值（断言在下面）。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from adapters.contracts.models_loaders import load_llm_endpoints
from adapters.relay.credential_resolver import EnvCredentialResolver
from adapters.relay.gateway import OpenAIChatGateway
from packages.application.model_relay.probe import run_endpoint_test
from packages.application.ports import (
    CompletionRequest,
    CompletionResult,
    ModelGateway,
    ModelsListResult,
    SecretValue,
)
from packages.domain.models import EndpointProbeSnapshot, LLMEndpoint
from tests.e2e.live_switch_support import live_e2e_switch_enabled, live_run_switch_off_reason

pytestmark = pytest.mark.requires_live_llm

_ENDPOINTS = "examples/config/llm_endpoints.yaml"
_ENDPOINT = "agnes-anthropic"
#: 一个**不可能存在**的 model 标识：不是任何厂商的命名形态，也不该撞上中转站的别名表。
_ABSENT_MODEL = "research-os-absent-model-v1"
#: 预置条件开关名。**改它要同步改**同一-source 判据
#: （`tests/architecture/python/test_live_failure_paths_same_source.py` 的
#: `TestTheModelAbsenceRowPointsAtAMeasuredSample`）——那边按**行为**判，不是按字符串判。
_CASE_ENV = "RESEARCHOS_LIVE_MODEL_ABSENCE_CASE"


@dataclass(slots=True)
class _StepRecorder:
    """记下每一步的**结果面**（ok / 类别 / 消息是否点名模型，**没有正文**）。

    包在真网关外面，产品代码一行不改：`run_endpoint_test` 只经 `ModelGateway` 面调用。
    """

    inner: ModelGateway
    steps: list[dict[str, object]] = field(default_factory=list)

    def list_models(self, endpoint: LLMEndpoint, credential: SecretValue) -> ModelsListResult:
        return self.inner.list_models(endpoint, credential)

    def complete(
        self, endpoint: LLMEndpoint, credential: SecretValue, request: CompletionRequest
    ) -> CompletionResult:
        return self.inner.complete(endpoint, credential, request)

    def probe_connectivity(
        self, endpoint: LLMEndpoint, credential: SecretValue
    ) -> EndpointProbeSnapshot:
        snapshot = self.inner.probe_connectivity(endpoint, credential)
        self.steps.append(_step("connectivity", snapshot, None))
        return snapshot

    def probe_endpoint(
        self, endpoint: LLMEndpoint, credential: SecretValue, request: CompletionRequest
    ) -> EndpointProbeSnapshot:
        snapshot = self.inner.probe_endpoint(endpoint, credential, request)
        self.steps.append(_step("chat", snapshot, request.model))
        return snapshot


def _step(
    step: str, snapshot: EndpointProbeSnapshot, request_model: str | None
) -> dict[str, object]:
    message = snapshot.error_message_redacted or ""
    return {
        "step": step,
        "request_model": request_model,
        "ok": snapshot.ok,
        "error_category": None if snapshot.error_category is None else str(snapshot.error_category),
        "message_names_the_absent_model": _ABSENT_MODEL in message,
    }


def _require_case() -> None:
    if not live_e2e_switch_enabled():
        pytest.skip(live_run_switch_off_reason())
    if os.environ.get(_CASE_ENV, "") != "1":
        pytest.skip(f"{_CASE_ENV} is not set to '1' — this sample spends a real call")


def _endpoint() -> Any:
    return load_llm_endpoints(_ENDPOINTS)[_ENDPOINT]


def _probe(endpoint: Any) -> tuple[Any, list[dict[str, object]]]:
    """**一次**端到端测试调用（连通性 + 一次 chat），结果机器可读、消息已脱敏。

    `url_policy` 不覆盖：走产品默认策略（拒 localhost / 环回 / 私有 / 保留），
    所以能出网的只可能是公网端点——本样本不放松任何门。
    """
    recorder = _StepRecorder(
        inner=OpenAIChatGateway(default_timeout_seconds=endpoint.request_timeout_seconds)
    )
    result = run_endpoint_test(
        gateway=recorder,
        credential_resolver=EnvCredentialResolver(),
        endpoint=endpoint,
        model_name=_ABSENT_MODEL,
    )
    return result, recorder.steps


def _observation(result: Any, steps: list[dict[str, object]]) -> dict[str, object]:
    """这一次调用的**可判事实**（全脱敏：没有正文，只有布尔与标识）。"""
    return {
        "endpoint_id": _ENDPOINT,
        "requested_model": result.model_id,
        "ok": result.ok,
        "error_category": None if result.error_category is None else str(result.error_category),
        "returned_model_name": result.returned_model_name,
        "returned_name_differs_from_requested": (
            result.returned_model_name is not None and result.returned_model_name != _ABSENT_MODEL
        ),
        "steps": steps,
    }


def _the_step(steps: list[dict[str, object]], name: str) -> dict[str, object]:
    found = next((step for step in steps if step["step"] == name), None)
    assert found is not None, f"the {name!r} step never ran: {steps}"
    return found


def _assert_the_refusal_is_about_the_model(steps: list[dict[str, object]]) -> None:
    """先钉「连通性过了」再钉「拒的是那次 chat」——否则结论会被误读成别的东西。"""
    connectivity = _the_step(steps, "connectivity")
    assert connectivity["ok"] is True, (
        f"connectivity itself failed, so this run says nothing about model absence: {connectivity}"
    )
    chat = _the_step(steps, "chat")
    assert chat["request_model"] == _ABSENT_MODEL, f"the chat asked for another model: {chat}"


def test_an_absent_model_identifier_is_measured_not_assumed(tmp_path: Path) -> None:
    """一个不存在的 model 标识：**实测** provider 怎么回应（拒绝 or 静默映射）。"""
    _require_case()
    endpoint = _endpoint()
    credential = os.environ.get(endpoint.credential_ref, "")
    assert credential, "this sample needs the credential in the environment (never in a file)"

    result, steps = _probe(endpoint)
    observation = _observation(result, steps)
    rendered = json.dumps(observation, ensure_ascii=False, sort_keys=True)
    (tmp_path / "absent-model-observation.json").write_text(rendered + "\n", encoding="utf-8")
    # 打到 stdout：这一次调用的**可判事实**要能被操作者原样带走（`-s` 或失败时可见）。
    # 否则「跑过了」就等于「什么也没记下」——而这条样本存在的意义就是留下事实。
    print(f"[model-absence] {rendered}")

    _assert_the_refusal_is_about_the_model(steps)
    # 记录必须**点名**被请求的那个 model 标识——这就是判定细则里「点名模型标识」的结构面。
    assert result.model_id == _ABSENT_MODEL, observation
    assert credential not in (result.error_message or ""), "the failure record leaked the value"

    if result.ok:
        # 没被拒 ⇒ 只可能是中转站把未知 model 映射到了**别的**模型：这是漂移样本，
        # 不是「用例失败」。它必须被留下而不是被断言掉（AGENTS.md §4：漂移必须可见）。
        assert result.returned_model_name != _ABSENT_MODEL, observation
    else:
        assert result.error_category is not None, (
            "a refusal must carry a category — otherwise the read face cannot tell "
            f"'provider rejected the model' from 'something else broke': {observation}"
        )
