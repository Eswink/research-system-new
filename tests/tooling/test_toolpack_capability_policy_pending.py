"""待拍板决策的同源登记：`tool_pack.*` 能力策略与「事实名 → 合约名」（GOAL-20260919-007 EC-06）。

平台默认策略（`examples/config/policy.yaml`）里**没有任何 `tool_pack.*` 能力规则**，
`default_effect: DENY`，因此真实部署下控制台供应链写面（`tool_pack.install/update/revoke`）
一律被拒；live 套件跑得通只是因为**夹具层**放行了这几个能力（`tests/api/console_api_app.py`）。
同文件 `require_approval` 段那条 `action: TOOL_PACK_INSTALL_OR_UPDATE` **按构造不可能匹配**：
生命周期求值只传 `capability=`，而 `PolicyRule.matches` 要求 action 相等 —— 意图写在策略里，
策略面却从不消费它。另一条同源的待决事实是「事实名 → 合约名」：真实会话的交付物键名是
`session_message`（事实名），示例合约要求 `analysis_report`，验收门按**字面包含**判定，
中间没有别名映射。

这三件事都是产品决策（放松默认 deny / 审批语义 / 谁能声明合约 artifact 名），循环内不得
自行决定。本仓库对这件事的处置是"如实登记、等人工拍板"：ADR-0031 是 `Proposed` 草案。

本文件把那份登记的**形状**钉成判据（读真实文件与真实求值器，不是断言注释文案）：

1. 决策记录在树：`docs/adr/ADR-0031-toolpack-capability-policy.md`，且 `Status: Proposed`
   （不得出现 `Status: Accepted` —— 它还没被拍板）；
2. 权威登记在索引：`docs/INDEX.md` 的条目行内含 `Proposed`；
3. 声明面**同源**：控制面 API 文档 / 控制台页面图 / live 夹具注释三处都同时提到
   `tool_pack` 与该 ADR 文件名 ⇒ 读者从任一处都能走到同一份决策；
4. **行为没变**（否则就只是一份漂亮的文档）：真实平台策略仍判 `tool_pack.*` DENY、
   那条 action 规则对生命周期形态的请求仍不生效、验收门仍按字面名判拒。

反证签名（实测登记在 RECHECK-20260919-112）：① ADR 改 `Status: Accepted` ⇒ 第 1 条红；
② 删任一声明面的 ADR 指针 ⇒ 第 3 条红；③ 给 `policy.yaml` 加 `tool_pack.install` 的
allow 规则 ⇒ 第 4 条红。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path

import pytest

from adapters.contracts import load_policy, load_task_contracts
from adapters.fakes import FakeEventPublisher, FakeToolPackStore
from packages.application.policy import NativePolicyEvaluator
from packages.application.ports.errors import PermanentPortError
from packages.application.ports.policy_evaluator import (
    PolicyEvaluation,
    PolicyEvaluator,
    PolicyRequest,
)
from packages.application.tool_plane import ToolPackLifecycle
from packages.domain.acceptance import CriterionInputs, evaluate_criterion
from packages.domain.core import Digest, Version
from packages.domain.enums import AcceptanceCriterionType, PolicyDecision
from packages.domain.policy import PolicyDefinition
from packages.domain.tools import (
    ToolPackManifest,
    toolpack_content_digest,
)

_ROOT = Path(__file__).resolve().parents[2]
_ADR_NAME = "ADR-0031-toolpack-capability-policy.md"
_ADR = _ROOT / "docs" / "adr" / _ADR_NAME
_INDEX = _ROOT / "docs" / "INDEX.md"
_POLICY_PATH = "examples/config/policy.yaml"
_CONTRACTS_PATH = "examples/contracts/task_contracts.yaml"
# 三处声明面：控制面 API 文档 / 控制台页面图 / live 夹具注释。
_SURFACES = (
    _ROOT / "docs" / "api" / "CONTROL_PLANE_API.md",
    _ROOT / "docs" / "frontend" / "CONSOLE_PAGE_MAP.md",
    _ROOT / "tests" / "api" / "console_api_app.py",
)
_KEY = "tool_pack"
_LIFECYCLE_CAPABILITIES = ("tool_pack.install", "tool_pack.update", "tool_pack.revoke")
_ACTION_RULE = "TOOL_PACK_INSTALL_OR_UPDATE"
# 真实会话交付物的**事实名**（adapters/openhands/runtime_adapter.py 的 `_deliverable`）。
_FACT_NAME = "session_message"
_CONTRACT_KEY = "console_demo_deliverable"
_ADAPTER = _ROOT / "adapters" / "openhands" / "runtime_adapter.py"


def _platform_policy() -> PolicyDefinition:
    return load_policy(_POLICY_PATH)


@dataclass(slots=True)
class _RecordingEvaluator:
    """记录每次求值的请求，决定仍交给真实求值器。"""

    real: PolicyEvaluator
    requests: list[PolicyRequest] = field(default_factory=list)

    def evaluate(self, request: PolicyRequest) -> PolicyEvaluation:
        self.requests.append(request)
        return self.real.evaluate(request)


def _manifest(pack_id: str) -> ToolPackManifest:
    placeholder = ToolPackManifest(
        id=pack_id,
        version=Version("1.0.0"),
        source="test://toolpack-capability-policy-pending",
        resolved_revision="rev-capability-policy-pending",
        digest=Digest.of_bytes(b"placeholder"),
        license="MIT",
        requested_capabilities=["dataset.read"],
    )
    return replace(placeholder, digest=toolpack_content_digest(placeholder))


def test_the_decision_record_is_a_proposal_not_a_decision() -> None:
    text = _ADR.read_text(encoding="utf-8")
    assert "Status: Proposed" in text, "草案必须是 Proposed：它还没被人工拍板"
    assert "Status: Accepted" not in text, "未拍板不得冒充 Accepted"


def test_the_index_registers_the_pending_decision() -> None:
    text = _INDEX.read_text(encoding="utf-8")
    assert _ADR_NAME in text, "待拍板的决策要有唯一入口（docs/INDEX.md 登记）"
    entry = next(line for line in text.splitlines() if _ADR_NAME in line)
    assert "Proposed" in entry, "索引条目必须写明它是 Proposed，不冒充已接受"


def test_every_declaration_surface_points_at_the_same_record() -> None:
    for surface in _SURFACES:
        text = surface.read_text(encoding="utf-8")
        assert _KEY in text, f"{surface.name} 必须提到这条声明"
        assert _ADR_NAME in text, f"{surface.name} 必须指向同一份决策记录（同源收敛）"


@pytest.mark.parametrize("capability", _LIFECYCLE_CAPABILITIES)
def test_platform_policy_still_denies_tool_pack_capabilities(capability: str) -> None:
    evaluation = NativePolicyEvaluator(_platform_policy()).evaluate(
        PolicyRequest(actor="admin", capability=capability, resource="any-pack")
    )
    assert evaluation.decision is PolicyDecision.DENY
    assert evaluation.reason == "used default policy effect", "拒绝要来自 default deny，不是规则"


def test_platform_policy_declares_no_tool_pack_capability_rule() -> None:
    policy = _platform_policy()
    rules = policy.allow + policy.allow_with_constraints + policy.require_approval + policy.deny
    offenders = [
        rule for rule in rules if rule.capability and rule.capability.startswith(f"{_KEY}.")
    ]
    assert offenders == [], "松绑只能来自改 policy.yaml；本轮不得新增任何 tool_pack 能力规则"


def test_the_declared_action_rule_needs_an_action_no_caller_supplies() -> None:
    policy = _platform_policy()
    rule = next(item for item in policy.require_approval if item.action == _ACTION_RULE)
    assert rule.matches(_LIFECYCLE_CAPABILITIES[0], None, "any-pack") is False
    assert rule.matches(_LIFECYCLE_CAPABILITIES[0], _ACTION_RULE, "any-pack") is True


def test_the_lifecycle_never_asks_with_an_action() -> None:
    """走公共 use case：请求形态由实现决定，不由测试编造。"""
    recorder = _RecordingEvaluator(real=NativePolicyEvaluator(_platform_policy()))
    lifecycle = ToolPackLifecycle(FakeToolPackStore(), recorder, FakeEventPublisher())
    with pytest.raises(PermanentPortError):
        lifecycle.submit(_manifest("capability-policy-pending-pack"))
    assert [item.capability for item in recorder.requests] == ["tool_pack.install"]
    assert recorder.requests[0].action is None, (
        "生命周期只传 capability ⇒ 那条 action 规则永不生效："
        "今天把它改成待批准会静默放行（这正是要拍板的原因）"
    )


def test_the_acceptance_gate_still_matches_artifact_names_literally() -> None:
    contracts = load_task_contracts(_CONTRACTS_PATH)
    criteria = contracts[_CONTRACT_KEY].acceptance_criteria
    criterion = next(
        item for item in criteria if item.type is AcceptanceCriterionType.ARTIFACT_EXISTS
    )
    assert criterion.artifact == "analysis_report"
    assert _FACT_NAME in _ADAPTER.read_text(encoding="utf-8"), "事实名的来源应仍是该 adapter"
    facts = CriterionInputs(artifacts={_FACT_NAME: {"content": "…"}})
    assert evaluate_criterion(criterion, facts).passed is False, "没有事实名→合约名的映射"
    literal = CriterionInputs(artifacts={"analysis_report": {"content": "…"}})
    assert evaluate_criterion(criterion, literal).passed is True
