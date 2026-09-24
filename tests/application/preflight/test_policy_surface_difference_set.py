"""GOAL-20260924-014 EC-03：策略面 ↔ 声明面**双向差集**的完备性判据（离线、零出网）。

判据与 `docs/architecture/POLICY_SURFACE_AUDIT.md` 的差集表**同源**：本文件重算差集与逐行终态，
再逐行与文档比对。任一侧单独改动都会被抓住：

- 声明面新增一条**未登记**的能力 ⇒ 差集里出现没有对应行的能力 ⇒ 红；
- 把某行的终态改成「待定 / 待确认」⇒ 终态闭环断言 ⇒ 红；
- 终态与机制不符（例如把读类潜在缺口写成「该拒绝」）⇒ 逐行判定断言 ⇒ 红。

口径（与文档「口径」节逐条对应，改口径必须两处一起改）：

1. 策略面只取每条规则的 `capability:` 字段（`action:` 是门面动作、不在比较范围）；
2. 声明面 = roles / skills / tool_providers / protocols 四个**使用声明面**
   （词表 `capabilities.yaml` 不参与 —— 它会令差集退化成空集）；
3. **协议可达** = 能力出现在某 phase 的 `required_capabilities`，或出现在该 phase 所引合约的
   `required_capabilities`（与 `phase_capabilities()` 同口径）；
4. **读类** = 末段 ∈ {read, inspect, validate}，且若被某 provider 声明则该 provider
   `effect_class` 为 `READ_ONLY`；
5. **终态只判差集内的条目**：两侧都出现的交集能力由现网规则处理，不进表、不判终态。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "examples" / "config"
PROTOCOLS = ROOT / "examples" / "protocols"
CONTRACTS = ROOT / "examples" / "contracts" / "task_contracts.yaml"
AUDIT_DOC = ROOT / "docs" / "architecture" / "POLICY_SURFACE_AUDIT.md"

POLICY_SECTIONS = ("allow", "allow_with_constraints", "require_approval", "deny")
ALLOWING_SECTIONS = ("allow", "allow_with_constraints")
READ_SUFFIXES = ("read", "inspect", "validate")
STATES = ("该放行", "该拒绝", "该登记")
OUTSIDE_DIFF = "不在差集内"
PENDING_TOKENS = ("待定", "待确认", "含糊", "TBD", "TODO", "?")
COLUMNS = ("能力", "差集侧", "声明面", "协议可达", "读类", "终态", "依据")


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _capabilities_of(body: Any, key: str) -> list[str]:
    return [str(item) for item in (body or {}).get(key) or []]


def _contract_ids(phase: Any) -> list[str]:
    raw = (phase or {}).get("task_contract")
    if isinstance(raw, str):
        return [raw]
    return [str(item) for item in raw or []]


#: （文件名、容器键、能力键、差集表里的声明面名）——四个**使用声明面**中的三个
_SURFACES: tuple[tuple[str, str, str, str], ...] = (
    ("roles.yaml", "roles", "requested_capabilities", "roles"),
    ("skills.yaml", "skills", "capabilities", "skills"),
    ("tool_providers.yaml", "tool_providers", "capabilities", "tool_providers"),
)


def policy_rules() -> dict[str, list[str]]:
    policy = _load(CONFIG / "policy.yaml")["policy"]
    rules: dict[str, list[str]] = {}
    for section in POLICY_SECTIONS:
        for rule in policy.get(section) or []:
            if rule.get("capability"):
                rules.setdefault(str(rule["capability"]), []).append(section)
    return rules


def _one_surface(relative: str, container: str, key: str, surface: str) -> dict[str, list[str]]:
    sites: dict[str, list[str]] = {}
    for body in (_load(CONFIG / relative).get(container) or {}).values():
        for capability in _capabilities_of(body, key):
            if surface not in sites.setdefault(capability, []):
                sites[capability].append(surface)
    return sites


def declared() -> dict[str, list[str]]:
    """四个使用声明面 → {capability: [声明面…]}（词表不参与）。"""
    sites: dict[str, list[str]] = {}
    for relative, container, key, surface in _SURFACES:
        for capability, where in _one_surface(relative, container, key, surface).items():
            sites.setdefault(capability, []).extend(where)
    for path in sorted(PROTOCOLS.glob("*.yaml")):
        for phase in _load(path).get("phases") or []:
            for capability in _capabilities_of(phase, "required_capabilities"):
                if "protocols" not in sites.setdefault(capability, []):
                    sites[capability].append("protocols")
    return sites


def reachable() -> dict[str, set[str]]:
    contracts = _load(CONTRACTS)["task_contracts"]
    reach: dict[str, set[str]] = {}
    for path in sorted(PROTOCOLS.glob("*.yaml")):
        for phase in _load(path).get("phases") or []:
            capabilities = set(_capabilities_of(phase, "required_capabilities"))
            for contract_id in _contract_ids(phase):
                capabilities.update(
                    _capabilities_of(contracts.get(contract_id), "required_capabilities")
                )
            for capability in capabilities:
                reach.setdefault(str(capability), set()).add(path.name)
    return reach


def provider_effect(capability: str) -> str | None:
    for body in (_load(CONFIG / "tool_providers.yaml").get("tool_providers") or {}).values():
        if capability in _capabilities_of(body, "capabilities"):
            return str((body or {}).get("effect_class") or "")
    return None


def is_read_class(capability: str) -> bool:
    if capability.rsplit(".", 1)[-1] not in READ_SUFFIXES:
        return False
    effect = provider_effect(capability)
    return effect is None or effect == "READ_ONLY"


def difference_set() -> dict[str, str]:
    """{capability: 差集侧}——策略面独有 ∪ 声明面独有。"""
    rules = policy_rules()
    sites = declared()
    result = {name: "策略面独有" for name in set(rules) - set(sites)}
    result.update({name: "声明面独有" for name in set(sites) - set(rules)})
    return result


def expected_state(capability: str) -> str:
    """机制推出的终态（文档必须与它一致）；不在差集内的能力返回 `OUTSIDE_DIFF`。"""
    if capability not in difference_set():
        return OUTSIDE_DIFF
    covering = [name for name in policy_rules().get(capability, []) if name in ALLOWING_SECTIONS]
    if capability in reachable():
        return "该放行" if not covering else "该拒绝"
    if capability not in policy_rules():
        return "该登记" if is_read_class(capability) else "该拒绝"
    return "该拒绝"


def audit_rows() -> list[dict[str, str]]:
    """解析文档里的差集表（表头必须与 COLUMNS 一致）。"""
    rows: list[dict[str, str]] = []
    lines = AUDIT_DOC.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("| 能力 |"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        assert tuple(cells) == COLUMNS, f"差集表表头变了：{cells}"
        for row in lines[index + 2 :]:
            if not row.startswith("|"):
                break
            values = [cell.strip() for cell in row.strip().strip("|").split("|")]
            assert len(values) == len(COLUMNS), f"列数不齐：{row}"
            rows.append(dict(zip(COLUMNS, values, strict=True)))
        break
    assert rows, "差集表未找到"
    return rows


def _capability_of(row: dict[str, str]) -> str:
    return row["能力"].strip("`")


def test_every_row_has_exactly_one_terminal_state_and_no_pending_token() -> None:
    """终态闭环：三选一、零待定、依据非空。"""
    for row in audit_rows():
        state = row["终态"]
        assert state in STATES, f"{_capability_of(row)} 的终态不在三选一内：{state!r}"
        for token in PENDING_TOKENS:
            assert token not in state, f"{_capability_of(row)} 的终态含待定词 {token!r}"
        assert row["依据"].strip(), f"{_capability_of(row)} 缺依据"


def test_the_difference_set_and_the_table_are_two_way_complete() -> None:
    """双向完备：差集 == 表格能力集（缺行、陈旧行都抓）。"""
    table = {_capability_of(row) for row in audit_rows()}
    diff = difference_set()
    assert table == set(diff), (
        f"差集有而表缺：{sorted(set(diff) - table)}；表有而差集无：{sorted(table - set(diff))}"
    )
    assert len(audit_rows()) == len(table), "表格出现重复能力行"


def test_each_row_state_matches_the_mechanical_rule() -> None:
    """逐行判定可核对：四列机械值都必须等于机制算出的值（不是散文）。"""
    sites = declared()
    for row in audit_rows():
        capability = _capability_of(row)
        assert row["终态"] == expected_state(capability), (
            f"{capability}：文档判 {row['终态']}，机制判 {expected_state(capability)}"
        )
        expected_sites = "、".join(sites[capability]) if capability in sites else "（无）"
        assert row["声明面"] == expected_sites, (
            f"{capability}：文档写声明面 {row['声明面']!r}，机制算出 {expected_sites!r}"
        )
        assert (row["协议可达"] == "是") is (capability in reachable()), capability
        assert (row["读类"] == "是") is is_read_class(capability), capability
        assert row["差集侧"] == difference_set()[capability], capability


def test_no_protocol_reachable_capability_lacks_a_rule() -> None:
    """本 EC 的核心断言：协议可达面上**没有第二个 `W-A`**。

    这条与差集表无关、直接对机制断言——任何人给某协议加一条没人放行的能力，
    这里立刻红（同时差集表也会因缺行而红）。
    """
    rules = policy_rules()
    holes = {
        capability: sorted(protocols)
        for capability, protocols in reachable().items()
        if not [name for name in rules.get(capability, []) if name in ALLOWING_SECTIONS]
    }
    assert holes == {}, f"协议可达却无放行规则（W-A 同类活缺口）：{holes}"


def test_the_registry_vocabulary_is_not_part_of_the_declaration_side() -> None:
    """词表是参照系、不是声明面：两个方向都不许混进来（口径回归护栏）。

    方向一：声明面/策略面读到的名字必须都在词表里 —— 防止把 `scope` 值、域名等
    非能力串当成能力读进差集；方向二：词表里必须存在「仅词表」的名字 —— 一旦有人把
    `capabilities.yaml` 也算进声明面，这些名字会消失、差集退化成空集。
    """
    vocabulary = {
        str(item) for item in _load(CONFIG / "capabilities.yaml").get("capabilities") or []
    }
    for label, names in (("声明面", set(declared())), ("策略面", set(policy_rules()))):
        stray = names - vocabulary
        assert not stray, f"{label}出现词表外的名字（疑似把非能力串当能力读）：{sorted(stray)}"
    vocabulary_only = vocabulary - set(declared())
    assert vocabulary_only, (
        "词表里没有「仅词表」的名字 ⇒ 声明面疑似把词表算进去了（差集会退化成空集）"
    )
    policy_only = {name for name, side in difference_set().items() if side == "策略面独有"}
    assert policy_only, "策略面独有侧为空 ⇒ 差集口径被破坏（词表并入声明面即此形态）"
    assert policy_only <= vocabulary_only, "策略面独有的名字应在「仅词表」集合里"


@pytest.mark.parametrize("capability", ["evidence.read", "literature.search"])
def test_allowed_capabilities_are_not_reported_as_gaps(capability: str) -> None:
    """已放行的能力不得被判成缺口（`W-A` 的修复面不许回退）。"""
    assert capability not in difference_set()
    assert expected_state(capability) == OUTSIDE_DIFF
    assert capability in reachable(), f"{capability} 已不协议可达，本断言前提变了"
    covering = [name for name in policy_rules().get(capability, []) if name in ALLOWING_SECTIONS]
    assert covering, f"{capability} 的放行规则被拿掉了：{policy_rules().get(capability)}"
