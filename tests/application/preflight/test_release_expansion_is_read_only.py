"""GOAL-20261006-031 EC-01 判据：**放行面扩容的三条机械事实 + 两向反证**（授权 1）。

**它把什么变成机械事实**：`examples/config/policy.yaml` 的 `allow` **新增了 8 条只读
能力** —— EC-01 的 6 条（`run.read` / `claim.read` / `deliverable.read` / `budget.read` /
`experiment.read` / `experiment_plan.read`，「已承接但未放行」的承接面收口）+ EC-02 的
`citation.validate`（判定层，本 GOAL 第二次逐条放行）+ GOAL-20261008-036 EC-02 的
`review.read`（第 8 条，承接 provider `m12_artifact` 的 `review_read` 工具）。
放行是一次**有界放宽**——
本文件把这条边界的**三个面**逐条钉住，且**不得**被写成任何形式的交集 / 过滤
（承 `MEM-20260922-160`；受判面就是**声明集本身**：本文件里逐字写死的 6 条能力名）。

**四条断言（每条的受判面与按压形态都在这里写明）**：

1. **只读面**（`TestTheExpansionIsReadOnly`）：本轮新增的**每一条**放行项
   ① 是 `capabilities.yaml` 词表的精确成员；② 末段 ∈ {`read`, `inspect`, `validate`}；
   ③ 若被某个 provider 声明，该 provider 的 `effect_class` 必须是 `READ_ONLY`。
   受判面 = 本文件写死的 `_RELEASED`（等值于声明集，不是交集）；缺一条、换一条都判红。
2. **`deny` 面零改动**（`TestTheDenyFaceIsByteIdentical`）：`require_approval` 与 `deny`
   两段的规则集合与**建档基线**逐条相等 —— 基线是**片段形态**（*能力/动作集合*）而不是
   字节 `sha256`（字段顺序、注释、缩进都不是本判据的对象），并由基线指纹
   `_DENY_SEGMENT_SHA256` 交叉钉住（对 LF 归一化的段正文取 `sha256`；它变了说明**段正文**
   动了，与集合断言互为两道门）。
3. **`default_effect` 仍为 `DENY`**（`TestTheDefaultEffectIsStillDeny`）：同一份文件里
   逐字断言，且用**真实求值器**对一条**未放行**能力求值，确认它落 `default_effect`
   （即 `used default policy effect`）—— 这条把「文件里写了 DENY」与「DENY 真的生效」
   分成两句断言（前者不蕴含后者）。
4. **未放行的护栏仍在**（`TestTheUnreleasedSideStaysDenied`）：`citation.inspect` /
   `dataset.read` / `provenance.read` / `research_map.read` /
   `research_state.read` / `target.read` / `agent_run.read` 七条读能力
   **仍未被放行**，三件套（`package.install` / `workspace.delete` / `external.publish`）
   仍 `REQUIRE_APPROVAL`，`network.public` 仍 `DENY`。

**两向反证（承 MEM-20260922-159）**：

- `test_a_non_read_capability_in_the_release_set_is_named`：把 `workspace.delete` 这类
  **非只读**能力代入只读面清单 ⇒ 判据的**同一个谓词**必须报出它（不是另写一条断言）；
- `test_removing_a_release_rule_returns_that_capability_to_default_deny`：从 `allow` 里
  删掉一条放行 ⇒ 用**真实求值器**对同一能力求值 ⇒ `DENY` + `used default policy effect`
  （该能力在 run 里**被拒且点名**，不是静默跳过）。

**不 import 产品常量当预言机**：6 条能力名与两段基线都是**字面量**写在本文件里；
`policy.yaml` / `_CAPABILITY_SCOPE` 是**被测对象**，不是判据的输入源。
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml

from packages.application.policy.native import NativePolicyEvaluator
from packages.application.ports.policy_evaluator import PolicyRequest
from packages.domain.enums import PolicyDecision

ROOT = Path(__file__).resolve().parents[3]
POLICY_FILE = ROOT / "examples" / "config" / "policy.yaml"
VOCABULARY_FILE = ROOT / "examples" / "config" / "capabilities.yaml"
PROVIDERS_FILE = ROOT / "examples" / "config" / "tool_providers.yaml"

#: **本 GOAL 新增的放行项**（逐字写死；受判面 = 这份声明集本身，不做任何交集 / 过滤）。
#: EC-01 = 前 6 条（只读读能力）；EC-02 = `citation.validate`（判定层，末段 `validate`
#: 属只读后缀 —— 谓词对它的判定与另六条**同一套**，不另开口子）。
_RELEASED: tuple[str, ...] = (
    "run.read",
    "claim.read",
    "deliverable.read",
    "budget.read",
    "experiment.read",
    "experiment_plan.read",
    "citation.validate",
    # GOAL-20261008-036 EC-02（授权承继 (0)）：第 8 条逐条放行 —— `review.read`
    # （只读后缀 `read`；承接 provider `m12_artifact` 的 `effect_class: READ_ONLY`）。
    # 登记表随本轮放行**新增一条**；谓词与其余断言一字未改。
    "review.read",
)

#: 只读后缀（与差集口径同一组）。
_READ_SUFFIXES = ("read", "inspect", "validate")

#: 建档基线（GOAL-20261006-031「事实层结论」第 7 条）：`require_approval` 段起始到文件末的
#: **LF 归一化正文** `sha256`。任何对该两段（含注释）的字节级改动都会改变它。
_DENY_SEGMENT_SHA256 = "bf04fa4efdbbafb8449c4f0248f4e4dc6ed9daae1f3dc7125f20fc2d4ad537a4"

#: 基线片段里的规则集合（逐条写死）：`require_approval` 3 条能力 + 2 条动作。
_BASELINE_REQUIRE_APPROVAL: tuple[tuple[str, str], ...] = (
    ("capability", "package.install"),
    ("capability", "workspace.delete"),
    ("capability", "external.publish"),
    ("action", "TOOL_PACK_INSTALL_OR_UPDATE"),
    ("action", "MODEL_OR_TOOLSET_CHANGE_DURING_RUN"),
)

#: 基线片段里的 `deny` 集合：1 条能力 + 2 条动作。
_BASELINE_DENY: tuple[tuple[str, str], ...] = (
    ("capability", "network.public"),
    ("action", "MOUNT_DOCKER_SOCKET"),
    ("action", "PRIVILEGED_CONTAINER"),
)

#: 仍**未**被放行的读数（受判面非空：这些名字必须逐条继续落 DENY）。
_UNRELEASED_READS: tuple[str, ...] = (
    "agent_run.read",
    "citation.inspect",
    "dataset.read",
    "provenance.read",
    "research_map.read",
    "research_state.read",
    "target.read",
)

#: **建档基线的放行面**（GOAL-20261006-031 建档当日的 `allow` 能力集合，逐条写死）。
#: 本 GOAL 的授权是「**新增** 6 条只读放行」⇒ 放行面里**除**这 12 条基线之外的**每一条**
#: 都必须是本轮新增、且必须是只读 —— 这才是「非只读能力塞进放行 ⇒ 判红」的完整谓词
#: （只查 `_RELEASED` 会漏掉「额外塞进来一条」这一形态：实测过，见记录）。
_BASELINE_ALLOW: tuple[str, ...] = (
    "workspace.read",
    "artifact.read",
    "evidence.read",
    "artifact.write",
    "literature.search",
    "literature.read",
    "network.academic",
    "memory.write",
)


def _load(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict), f"{path} 必须是 YAML 映射"
    return payload


def policy_body() -> dict[str, Any]:
    body = _load(POLICY_FILE).get("policy")
    assert isinstance(body, dict), "policy.yaml 必须含 `policy:` 映射，否则本判据在空转"
    return body


def policy_text() -> str:
    return POLICY_FILE.read_text(encoding="utf-8")


def vocabulary() -> set[str]:
    return {str(item) for item in _load(VOCABULARY_FILE).get("capabilities") or []}


def provider_effect_class(capability: str) -> str | None:
    """能力 → 承载它的 provider 的 `effect_class`（无 provider 声明 ⇒ `None`）。"""
    for body in (_load(PROVIDERS_FILE).get("tool_providers") or {}).values():
        if capability in ((body or {}).get("capabilities") or []):
            return str((body or {}).get("effect_class") or "")
    return None


def rule_pairs(section: Any) -> list[tuple[str, str]]:
    """`(字段, 值)` 对：只取 `capability` / `action` 两个键（与差集口径同源）。"""
    pairs: list[tuple[str, str]] = []
    for rule in section or []:
        for key in ("capability", "action"):
            if rule.get(key):
                pairs.append((key, str(rule[key])))
    return pairs


def release_rule_violations(capabilities: tuple[str, ...]) -> list[str]:
    """只读面谓词（**唯一一处**——反证臂也调它，确保「判红」与「判绿」同源）。"""
    words = vocabulary()
    violations: list[str] = []
    for capability in capabilities:
        if capability not in words:
            violations.append(f"{capability}: 不在 capabilities.yaml 词表内")
            continue
        if capability.rsplit(".", 1)[-1] not in _READ_SUFFIXES:
            violations.append(f"{capability}: 末段不是只读后缀 {_READ_SUFFIXES}")
            continue
        effect = provider_effect_class(capability)
        if effect is not None and effect != "READ_ONLY":
            violations.append(f"{capability}: provider effect_class={effect!r}（非 READ_ONLY）")
    return violations


def _evaluator(policy: Any = None) -> NativePolicyEvaluator:
    """真实求值器（缺省读产品策略本体；传入副本用于反证臂）。"""
    from services.api.catalog import load_policy_definition

    definition = policy if policy is not None else load_policy_definition()
    assert definition is not None, "policy.yaml must be loadable"
    return NativePolicyEvaluator(definition)


def _decision(capability: str, *, policy: Any = None) -> Any:
    from packages.application.preflight.policy_check import policy_scope_for

    return _evaluator(policy).evaluate(
        PolicyRequest(
            actor="goal031:release-check",
            capability=capability,
            action="execute",
            scope=policy_scope_for(capability),
            resource=capability,
        )
    )


def allowed_capabilities(body: dict[str, Any]) -> set[str]:
    """策略面 `allow` 段里出现的全部能力（**真实声明集**，不是写法清单）。"""
    return {str(rule["capability"]) for rule in body.get("allow") or [] if rule.get("capability")}


def expansion_set(body: dict[str, Any]) -> set[str]:
    """放行面 **−** 建档基线 = 本轮**实际新增**的放行项（受判面就是这个差集）。"""
    return allowed_capabilities(body) - set(_BASELINE_ALLOW)


class TestTheExpansionIsReadOnly:
    """① 本轮新增放行项**逐条**是只读能力（受判面 = **策略面实际算出的扩集**）。"""

    def test_every_released_capability_is_read_only(self) -> None:
        violations = release_rule_violations(_RELEASED)
        assert violations == [], (
            "本轮新增放行项必须逐条是只读能力（违者逐条点名）",
            violations,
        )

    def test_the_release_set_is_exactly_what_the_policy_grants_beyond_the_baseline(self) -> None:
        """**受判面 = 声明集本身**：放行面 − 基线 == `_RELEASED`（多一条、少一条都判红）。

        为什么必须从**文件**算而不是只查写法：只校验写死清单会漏掉「**额外塞进来一条**」
        这一形态 —— 实测过（把 `workspace.delete` 插进 `allow` ⇒ 只看 `_RELEASED` 的
        写法**全绿**）。本谓词把「策略面实际多出来的每一条」都拉进受判面。
        """
        body = policy_body()
        actual = expansion_set(body)
        assert actual == set(_RELEASED), (
            "放行面相对建档基线的新增项必须恰好是声明的 6 条只读能力"
            "（多出来的是未申报放宽、少掉的是放行被删）",
            sorted(actual - set(_RELEASED)),
            sorted(set(_RELEASED) - actual),
        )
        assert _RELEASED, "受判面非空是交付前提"

    def test_the_actual_expansion_set_passes_the_read_only_predicate(self) -> None:
        """**扩集本身**过只读谓词（与 `_RELEASED` 的写法检查是两句独立断言）。"""
        violations = release_rule_violations(tuple(sorted(expansion_set(policy_body()))))
        assert violations == [], (
            "策略面相对基线多出来的放行项必须逐条是只读能力",
            violations,
        )

    def test_each_release_rule_carries_the_aligned_scope(self) -> None:
        """scope 对齐**同级既有放行形态**——逐条断言，不是「看起来像」。

        两条不同的对齐基准（都不是本判据的偏好，而是该能力在既有放行面上的**邻居**）：
        EC-01 的 6 条读能力与 `artifact.read` / `evidence.read` 同级 ⇒ `project`；
        EC-02 的 `citation.validate` 是**取数面**能力 ⇒ 与同 provider 形态的
        `literature.search` / `literature.read` 同级 = `approved_tool_providers`。
        """
        expected = {
            "run.read": "project",
            "claim.read": "project",
            "deliverable.read": "project",
            "budget.read": "project",
            "experiment.read": "project",
            "experiment_plan.read": "project",
            "citation.validate": "approved_tool_providers",
            # GOAL-20261008-036 EC-02：与同级读能力（`artifact.read` / `evidence.read` /
            # `run.read`）对齐 = `project`。
            "review.read": "project",
        }
        scopes: dict[str, set[str]] = {}
        for rule in policy_body().get("allow") or []:
            if rule.get("capability"):
                scopes.setdefault(str(rule["capability"]), set()).add(str(rule.get("scope") or ""))
        wrong = {
            name: sorted(scopes.get(name, set()))
            for name in _RELEASED
            if scopes.get(name) != {expected[name]}
        }
        assert wrong == {}, ("放行项的 scope 必须逐条等于其对齐基准", wrong, expected)


class TestTheDenyFaceIsByteIdentical:
    """② `require_approval` 与 `deny` 两段**零改动**（集合逐条 + 段正文指纹两道门）。"""

    def test_the_require_approval_set_matches_the_baseline(self) -> None:
        pairs = rule_pairs(policy_body().get("require_approval"))
        assert sorted(pairs) == sorted(_BASELINE_REQUIRE_APPROVAL), (
            "require_approval 段被改动了（本 GOAL 的授权**只**动 allow）",
            sorted(pairs),
            sorted(_BASELINE_REQUIRE_APPROVAL),
        )

    def test_the_deny_set_matches_the_baseline(self) -> None:
        pairs = rule_pairs(policy_body().get("deny"))
        assert sorted(pairs) == sorted(_BASELINE_DENY), (
            "deny 段被改动了（AGENTS.md §9 默认 deny 的护栏）",
            sorted(pairs),
            sorted(_BASELINE_DENY),
        )

    def test_the_deny_segment_body_is_byte_identical_to_the_baseline(self) -> None:
        """段正文（含注释）的 LF 归一化 `sha256` == 建档基线 —— 与集合断言互为两道门。"""
        text = policy_text()
        index = text.index("require_approval:")
        segment = text[index:].replace("\r\n", "\n")
        digest = hashlib.sha256(segment.encode("utf-8")).hexdigest()
        assert digest == _DENY_SEGMENT_SHA256, (
            "`require_approval` + `deny` 两段的正文动了（本 GOAL 的授权只动 allow）",
            digest,
            _DENY_SEGMENT_SHA256,
        )


class TestTheDefaultEffectIsStillDeny:
    """③ `default_effect` 仍是 `DENY`，且**真的生效**（两句断言不作一句）。"""

    def test_the_default_effect_is_declared_as_deny(self) -> None:
        assert policy_body().get("default_effect") == "DENY", policy_body().get("default_effect")

    def test_an_unreleased_capability_falls_to_the_default_effect(self) -> None:
        """用真实求值器确认：未放行能力落 `default_effect`（而不是被别处碰巧放过）。"""
        decision = _decision("dataset.read")
        assert decision.decision is PolicyDecision.DENY, decision
        assert decision.reason == "used default policy effect", decision.reason


class TestTheUnreleasedSideStaysDenied:
    """④ 未放行的护栏仍在（逐条点名，不用汇总计数顶替）。"""

    def test_every_unreleased_read_still_uses_the_default_effect(self) -> None:
        for capability in _UNRELEASED_READS:
            decision = _decision(capability)
            assert decision.decision is PolicyDecision.DENY, (capability, decision)
            assert decision.reason == "used default policy effect", (capability, decision.reason)

    def test_the_approval_set_is_still_approval(self) -> None:
        for capability in ("package.install", "workspace.delete", "external.publish"):
            decision = _decision(capability)
            assert decision.decision is PolicyDecision.REQUIRE_APPROVAL, (capability, decision)
            assert decision.reason == "matched approval rule", (capability, decision.reason)

    def test_the_deny_set_is_still_denied(self) -> None:
        decision = _decision("network.public")
        assert decision.decision is PolicyDecision.DENY, decision
        assert decision.reason == "matched deny rule", decision.reason


class TestBothRefutationDirectionsBite:
    """两向反证（承 MEM-20260922-159）：判据**咬得住**两个方向，且与判绿同源。"""

    def test_a_non_read_capability_in_the_release_set_is_named(self) -> None:
        """反向一：非只读能力代入只读面 ⇒ **同一个谓词**必须点名报出。"""
        violations = release_rule_violations((*_RELEASED, "workspace.delete"))
        assert violations == [
            "workspace.delete: 末段不是只读后缀 ('read', 'inspect', 'validate')"
        ], violations
        # 与正控制对照：不含它的声明集必须报空（否则本谓词是恒真断言）
        assert release_rule_violations(_RELEASED) == []

    def test_a_non_read_capability_injected_into_the_real_allow_face_is_named(self) -> None:
        """反向一（**真实文件形态**）：把非只读能力插进 `allow` ⇒ 扩集断言与只读谓词同时判红。

        这条与上一条**不是同一件事**：上一条只证明谓词对合成清单有效，本条证明
        **「策略面实际多出来的一条」会被拉进受判面** —— 这正是初版判据的缺口（实测：
        只看 `_RELEASED` 写法时，插入 `workspace.delete` 后 14 条断言**全绿**）。
        按压在**内存内的副本**上做（不落盘、不动产品文件）。
        """
        body = policy_body()
        injected = {
            **body,
            "allow": [*body.get("allow", []), {"capability": "workspace.delete", "scope": "run"}],
        }
        actual = expansion_set(injected)
        assert actual == {*_RELEASED, "workspace.delete"}, sorted(actual)
        violations = release_rule_violations(tuple(sorted(actual)))
        assert violations == [
            "workspace.delete: 末段不是只读后缀 ('read', 'inspect', 'validate')"
        ], violations
        # 反面对照：未注入的真实文件必须报空（本条判据在真树上不空转）
        assert release_rule_violations(tuple(sorted(expansion_set(body)))) == []

    def test_removing_a_release_rule_returns_that_capability_to_default_deny(self) -> None:
        """反向二：删掉一条放行规则 ⇒ 该能力**回落** `default_effect`（被拒且点名）。"""
        from services.api.catalog import load_policy_definition

        base = load_policy_definition()
        assert base is not None
        trimmed = replace(
            base,
            allow=tuple(rule for rule in base.allow if rule.capability != "budget.read"),
        )
        before = _decision("budget.read")
        assert before.decision is PolicyDecision.ALLOW, ("前提：放行规则在场时它被允许", before)

        after = _decision("budget.read", policy=trimmed)
        assert after.decision is PolicyDecision.DENY, (
            "删掉放行规则后该能力必须回落 default_effect（不是静默跳过）",
            after,
        )
        assert after.reason == "used default policy effect", after.reason

    def test_the_predicate_does_not_silently_accept_an_unknown_name(self) -> None:
        """谓词对**词表外**名字也必须点名（防「只校验认识的名字」式空转）。"""
        violations = release_rule_violations(("goal031.not.a.capability",))
        assert violations == ["goal031.not.a.capability: 不在 capabilities.yaml 词表内"], violations
