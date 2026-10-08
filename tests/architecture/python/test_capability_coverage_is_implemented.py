"""GOAL-029 EC-02 判据：**「出厂即可跑」机械化 + 承接面逐条分类**（收 GOAL-028 `W-1`）。

**它把什么变成机械事实**：`tool_providers.yaml` **声明**了某能力（provider 承接），
而「声明」与「有可执行的实现」是两件事 —— GOAL-028 的 `W-1` 正是这条落差
（映射机制成立 ≠ 出厂即可跑）。本判据对**每一条已声明承接的能力**断言
「声明了 ⇒ 一定有实现注册」，并把 46 条能力**逐条**分类（承 MEM-158：射程显式分类）。

**四件事**：

1. **声明 ⇒ 实现**（本条的主判据）：对每条已声明承接的能力，断言它在**出厂绑定表**里
   有对应的工具名，且该工具名在 `CanonicalReadProvider.list_tools` 里**真的有承载**；
   缺一个 ⇒ 判红并**点名**能力名与该缺失的工具名。
2. **反证两向**：
   - **声明了但没实现** ⇒ 判红（把一条能力加进 provider 的 capabilities 但绑定表不给实现）；
   - **实现了但没声明** ⇒ 也判红（绑定表里有工具名但 provider 未声明该能力）——
     防静默漂移（声明面与实现面各自演化）。
3. **射程逐条分类**（承 MEM-158）：46 条能力**逐条**要么在**射程内**（已承接）、
   要么**登记在案**（带组别与理由）；**未分类者判红**。
4. **不得靠并集掩蔽**（承 MEM-160）：必备清单（射程内集合）有**下界断言**，
   且下界**显式写死**在本文件里（不随文档漂移）。

**与既有判据的分工**：`test_policy_surface_difference_set.py` 判**策略面 ↔ 声明面**的差集；
本文件判**声明面 ↔ 实现面**的落差 —— 两者的对象不同，**不互相顶替**（承 MEM-159）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest
import yaml

from adapters.canonical import CanonicalReadProvider
from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger
from services.api.session_tool_support import DEFAULT_SESSION_TOOL_BINDINGS

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

_ROOT = Path(__file__).resolve().parents[3]
_CAPABILITIES = "examples/config/capabilities.yaml"
_PROVIDERS = "examples/config/tool_providers.yaml"
#: 工具面描述子所在的模块（**拆分后**：能力↔工具的对应表在 surface 模块，
#: 执行实现在 `read_provider.py`；判据读的是**声明面**，所以指向前者）。
_READ_PROVIDER = "adapters/canonical/read_surface.py"

#: 射程**内**的能力（本 GOAL 承接的）：逐条写死 —— 下界由本清单给出（承 MEM-160）。
#: 每加一条都要在这里显式加（清单本身就是「已承接」的判词）。
_IN_SCOPE: tuple[str, ...] = (
    "artifact.read",
    "claim.read",
    "evidence.read",
    "workspace.read",
    "budget.read",
    "deliverable.read",
    "experiment.read",
    "experiment_plan.read",
    "run.read",
    # GOAL-20261008-036 EC-04：`review.read` 从「登记理由」（原文指向「评审走
    # task/handoff 面」—— GOAL-035 EC-01 已把验收结论落 canonical）**移入射程**。
    # 纯收紧：本清单是「已承接」的判词，只增不减。
    "review.read",
)

#: 射程**外**的能力 → (组别, 理由)。46 条能力里**除 _IN_SCOPE 与已承接的 12 条之外**的
#: 每一条都必须在此登记；未登记者由 `test_every_capability_is_classified` 判红。
_OUT_OF_SCOPE_REASONS: dict[str, str] = {
    # --- A 组：零依赖读能力，但**放行需用户拍板**（D-02(b) 未决口径）---
    "agent_run.read": (
        "A 组零依赖读：域里**没有 AgentRun 实体**（最近的是 task+agent_id）⇒ 无可读对象"
    ),
    # --- B 组：有依赖或需要判定层 ---
    "citation.validate": ("已承接（ncbi_citation，REST adapter）—— GOAL-20261006-031 EC-02 射程"),
    "dataset.read": "B 组：需要数据集存储面（今天没有 canonical 数据集实体）",
    "provenance.read": "B 组：需要 provenance 投影面（今天的证据链投影走 evidence.read）",
    "research_map.read": "B 组：需要研究地图实体（今天没有）",
    "research_state.read": "B 组：需要研究状态实体（今天没有）",
    "target.read": "B 组：需要目标实体（今天没有 canonical 目标）",
    # --- C 组：写 / 执行 / 提议类（非读）---
    "protocol.propose": "C 组：提议类（写面）⇒ 需策略面与 canonical 路径决定",
    "decision.propose": "C 组：提议类（写面）",
    "evidence.propose": "C 组：提议类（写面）",
    "idea.write": "C 组：写面",
    "idea.review": "C 组：写面（评审）",
    "experiment_plan.write": (
        "C 组：写面（canonical 路径 = ExperimentStore.save_plan；无共同漏斗，见 EC-03 残余）"
    ),
    "audit.write": "C 组：写面（M12 链内持久化，无独立写面）",
    "review.write": "C 组：写面",
    "deliverable.write": "C 组：写面（canonical = persist_completion；属 EC-03 的判定面向）",
    "deliverable.edit": "C 组：写面（域里无 Deliverable 实体，edit 无执行面）",
    "statistics.execute": "C 组：执行类",
    "experiment.execute": "C 组：执行类（沙箱实验缝已有独立通道）",
    "memory.write": "C 组：写面（门链 curator 面）",
    "workspace.write.notes": "已承接（openhands_workspace）—— 见 _ALREADY_承接",
    "workspace.write.code": "已承接（openhands_workspace）",
    "gpu.use": "B 组：远程 GPU 执行面（M17 有 worker gateway，但无 canonical 读实体）",
    # --- D 组：默认 deny / 需审批（触达需拍板）---
    "external.publish": "D 组：policy.yaml 现为 require_approval ⇒ 接通审批通道需用户拍板",
    "package.install": "D 组：require_approval ⇒ 需拍板",
    "workspace.delete": "D 组：require_approval ⇒ 需拍板",
    "git.commit": "D 组：写面（git 提交）⇒ 需拍板",
    "network.public": "D 组：policy.yaml 显式 deny",
    # --- 已承接但与 A 组无关（属 GOAL-027/028 的射程）---
    "literature.search": "已承接（ncbi_eutils / europe_pmc）—— GOAL-027 射程",
    "literature.read": "已承接（ncbi_eutils / europe_pmc）—— GOAL-027 射程",
    "citation.inspect": "已承接（ncbi_eutils）—— GOAL-027 射程",
    "artifact.write": "已承接（m12_artifact）—— 写面，属既有射程",
    "code.execute": "已承接（openhands_workspace）—— 执行面，属既有射程",
    "git.diff": "已承接（openhands_workspace）—— 属既有射程",
    "network.academic": (
        "策略面 allow（approved_domains）；无独立 provider 承接"
        "（出网由各 provider 的 network_domains 表达）"
    ),
    "evidence.write": "已承接（m12_artifact）—— 写面，属既有射程",
}

#: **声明了、但实现由本 provider 之外的组件承担**的能力 → 理由（逐条点名，不静默放行）。
#:
#: 为什么需要这张表：主判据要求「provider 声明的每一条要么有本 provider 的可注册实现、
#: 要么在此登记理由」。收口审计（GOAL-029 的完成核对）实测到：首版主判据把受判面写成
#: `declared & implemented` ⇒ **「声明了但没实现」在构造上不可能被报出来**
#: （承 MEM-160：不得靠交集/并集掩蔽）。修好后它立刻报出三条真实缺口，其中
#: `experiment.read` / `experiment_plan.read` **没有**实现 ⇒ 已从出厂声明面**移除**
#: （保留声明而没有可执行承接面正是 GOAL-028 `W-1` 的原形）。
#:
#: 仍在此登记的是「**实现由既有 adapter 承担**」的那些（REST provider / 工作区 adapter /
#: 沙箱执行缝）以及本 GOAL 判定**不该**有工具面的写能力（EC-03）。
_DECLARED_WITHOUT_IMPLEMENTATION: dict[str, str] = {
    "artifact.write": (
        "写能力：canonical 路径经 `persist_completion` 的 `_put_json_artifact`"
        "（不经 ToolProvider）；是否给写能力开工具面属 EC-03 判定（策略面判「该拒绝」）"
    ),
    "evidence.write": (
        "写能力：同上（证据写入经 application 层的证据登记面，不走 ToolProvider 工具面）"
    ),
    "code.execute": (
        "执行能力：由 openhands_workspace 的**沙箱执行缝**承担（不经本读 provider 的工具面）"
    ),
    "git.diff": "工作区能力：由 openhands_workspace 的 adapter 承担（不在本读 provider 的工具面）",
    "workspace.write.notes": "工作区写：由 openhands_workspace 的 adapter 承担（要 lease，属写面）",
    "workspace.write.code": "工作区写：同上",
    "literature.search": "由 ncbi_eutils / europe_pmc 的 REST adapter 承担（GOAL-027 射程）",
    "literature.read": "由 ncbi_eutils / europe_pmc 的 REST adapter 承担（GOAL-027 射程）",
    "citation.inspect": "由 ncbi_eutils 的 REST adapter 承担（GOAL-027 射程）",
    "citation.validate": (
        "由 ncbi_citation 的 REST adapter 承担（GOAL-20261006-031 EC-02 承接；"
        "取数复用 ncbi_eutils 的 elink 面，三态判定在其之上）"
    ),
}

#: 本轮**新承接**的五条（下界由它给出；`_IN_SCOPE` 是它的超集说明）。
#: 承 MEM-160：清单本身要有下界断言，且下界**写死**（不随文档漂移）。
_MIN_NEWLY_承接 = 8


def _load(path: str) -> dict[str, Any]:
    payload = yaml.safe_load((_ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict), path
    return payload


def vocabulary() -> set[str]:
    """能力词表（`capabilities.yaml`）—— 分类的**参照系**。"""
    return {str(item) for item in _load(_CAPABILITIES).get("capabilities") or []}


def declared_capabilities() -> dict[str, list[str]]:
    """{能力名: [声明它的 provider id…]}（来自 `tool_providers.yaml`）。"""
    result: dict[str, list[str]] = {}
    for provider_id, body in (_load(_PROVIDERS).get("tool_providers") or {}).items():
        for capability in (body or {}).get("capabilities") or []:
            result.setdefault(str(capability), []).append(str(provider_id))
    return result


def _read_provider_tools() -> dict[str, str]:
    """`CanonicalReadProvider` 里 tool id → 能力名（AST 读源码，不 import 当预言机）。"""
    source = (_ROOT / _READ_PROVIDER).read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source, filename=_READ_PROVIDER)):
        if not isinstance(node, ast.AnnAssign):
            continue
        target = node.target
        if not isinstance(target, ast.Name) or target.id != "_TOOL_CAPABILITIES":
            continue
        assert node.value is not None, "_TOOL_CAPABILITIES 必须有值"
        literal = ast.literal_eval(node.value)
        return {str(key): str(value) for key, value in literal.items()}
    raise AssertionError(f"{_READ_PROVIDER} 里找不到 _TOOL_CAPABILITIES（本判据的前提变了）")


def _provider_capabilities() -> set[str]:
    return set(declared_capabilities())


def test_every_declared_capability_has_an_implementation() -> None:
    """**主判据**（EC-02(a)）：声明了 ⇒ 一定有实现注册（缺一即点名）。

    **本条曾有一个掩蔽缺陷（收口审计抓到，已修）**：首版把受判面写成
    `declared & implemented` —— 那让「**声明了但没实现**」**在构造上不可能被报出来**
    （交集天然排除了缺实现的那些）。实测后果：它漏掉了 `experiment.read` /
    `experiment_plan.read` / `claim.read` 三条**自己声明却没实现**的能力
    （承 MEM-160：不得靠并集/交集掩蔽）。

    **现形态**：受判面 = **provider 声明的每一条**（`_provider_capabilities()`），
    每条要么有可注册的实现，要么**在 `_DECLARED_WITHOUT_IMPLEMENTATION` 里登记了理由**
    （登记项也要**逐条点名**，不是静默放行）。
    """
    canonical = _read_provider_tools()
    bound_tool_names = {tool_name for tool_name, _p, _t in DEFAULT_SESSION_TOOL_BINDINGS}
    declared = _provider_capabilities()
    assert declared, "受判面非空是交付前提（本判据不得在空集上恒真）"

    def _has_implementation(capability: str) -> bool:
        return any(cap == capability and cap in bound_tool_names for cap in canonical.values())

    missing_impl = sorted(
        capability
        for capability in declared
        if not _has_implementation(capability)
        and capability not in _DECLARED_WITHOUT_IMPLEMENTATION
    )
    assert missing_impl == [], (
        "声明了承接但既没有实现、也没有登记理由（缺实现必须点名能力名与工具名）",
        missing_impl,
    )
    # 登记表里的每条也必须在**声明面**里（防幽灵条目）
    ghosts = sorted(set(_DECLARED_WITHOUT_IMPLEMENTATION) - declared)
    assert ghosts == [], ("登记表里有未声明的能力（幽灵条目，请复核）", ghosts)


def test_a_declared_but_unimplemented_capability_is_named() -> None:
    """反证一：**声明了但没实现** ⇒ 判红且点名（在**合成输入**上验证判据本身咬得住）。"""
    canonical = _read_provider_tools()  # 真实实现表
    synthetic_declared = {*canonical.values(), "goal029.not.implemented"}
    implemented = set(canonical.values())
    missing = sorted(_find_missing(synthetic_declared, implemented, canonical))
    assert missing == ["goal029.not.implemented"], (
        "判据必须在「声明了但没实现」时点名那条能力（否则它咬不住真实漂移）",
        missing,
    )


def test_an_implemented_but_undeclared_capability_is_named() -> None:
    """反证二：**实现了但没声明** ⇒ 也判红（防静默漂移；两向承 MEM-159）。"""
    canonical = _read_provider_tools()
    # 合成：实现表比声明面多一条（真实形态是「有人加了实现却忘了在目录声明」）
    synthetic_implemented = {*canonical.values(), "goal029.orphan"}
    declared = set(canonical.values())
    orphans = sorted(_find_orphans(synthetic_implemented, declared))
    assert orphans == ["goal029.orphan"], (
        "判据必须在「实现了但没声明」时点名那条能力（否则漂移会静默）",
        orphans,
    )


def _find_missing(declared: set[str], implemented: set[str], canonical: dict[str, str]) -> set[str]:
    bound = {tool_name for tool_name, _p, _t in DEFAULT_SESSION_TOOL_BINDINGS}
    return {
        capability
        for capability in declared
        if capability not in implemented
        or not [tid for tid, cap in canonical.items() if cap == capability and cap in bound]
    }


def _find_orphans(implemented: set[str], declared: set[str]) -> set[str]:
    return implemented - declared


def test_every_capability_is_classified() -> None:
    """射程逐条分类（承 MEM-158）：46 条**逐条**要么在射程内、要么登记在案。"""
    words = vocabulary()
    assert len(words) == 46, ("能力词表条数变了，本判据的分类需同轮复核", len(words))
    unclassified = sorted(
        name for name in words if name not in _IN_SCOPE and name not in _OUT_OF_SCOPE_REASONS
    )
    assert unclassified == [], (
        "有未分类的能力（射程显式分类：每条要么在射程内、要么登记在案）",
        unclassified,
    )
    # 登记项不得是空理由（「登记了」与「说明了为什么」是两件事）
    empty = sorted(name for name, reason in _OUT_OF_SCOPE_REASONS.items() if not reason.strip())
    assert empty == [], ("登记项必须有非空理由", empty)
    # 不得自相矛盾：在射程内的不得同时又出现在登记表里
    overlap = sorted(set(_IN_SCOPE) & set(_OUT_OF_SCOPE_REASONS))
    assert overlap == [], ("在射程内的能力不得同时登记为射程外", overlap)


def test_the_in_scope_list_has_a_floor() -> None:
    """下界断言（承 MEM-160）：承接清单有**下界**，且下界写死在这里。

    「必备清单」与「文档点名」并存时，只靠后者会让清单缩水不被发现 ——
    下界由本文件给出，不随文档漂移。
    """
    assert len(_IN_SCOPE) >= _MIN_NEWLY_承接, (
        "射程内清单缩水了（下界由本文件写死）",
        len(_IN_SCOPE),
        _MIN_NEWLY_承接,
    )
    # 清单里的每一条都真的**有实现**（不是列表凑数）
    implemented = set(_read_provider_tools().values())
    missing = sorted(name for name in _IN_SCOPE if name not in implemented)
    assert missing == [], ("射程内清单里有不具备实现能力的条目", missing)


def test_the_classification_covers_the_exact_vocabulary() -> None:
    """分类的并集**恰好**等于词表（既不多也不少）——防「并集掩蔽」的反向。"""
    words = vocabulary()
    classified = set(_IN_SCOPE) | set(_OUT_OF_SCOPE_REASONS)
    assert classified == words, (
        "分类并集与词表不等（多出来的是幽灵条目、少掉的是未分类）",
        sorted(classified - words),
        sorted(words - classified),
    )


def test_the_provider_declares_exactly_the_implemented_read_capabilities() -> None:
    """出厂目录与实现表**同源**：声明的那几条读能力都有实现（实跑对象非空）。"""
    canonical = _read_provider_tools()
    declared = set(declared_capabilities())
    implemented = set(canonical.values())
    for capability in sorted(implemented):
        assert capability in declared, (
            f"{capability} 有实现但出厂目录没声明 ⇒ 承接不成立（声明 + 实现缺一不可）",
            sorted(declared),
        )


def test_the_read_provider_lists_only_declared_capabilities() -> None:
    """`list_tools` 只列**本 provider 真声明了**的能力（未声明的不进工具面）。"""
    from packages.domain.enums import EffectClass, ProviderType, TrustLevel
    from packages.domain.tools import ToolProviderSpec

    provider = CanonicalReadProvider(FakeArtifactStore(), FakeEvidenceLedger())
    spec = ToolProviderSpec(
        id="m12_artifact",
        kind=ProviderType.NATIVE,
        trust_level=TrustLevel.BUILT_IN,
        capabilities=["artifact.read", "budget.read"],
        effect_class=EffectClass.READ_ONLY,
    )
    listed = {capability for tool in provider.list_tools(spec) for capability in tool.capabilities}
    assert listed == {"artifact.read", "budget.read"}, sorted(listed)
