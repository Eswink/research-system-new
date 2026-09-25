"""GOAL-20260925-016 EC-02（D-02(b)）：读类能力**逐条授权**、**不成类放行**。

**要钉住的决定（D-02(b)，用户 2026-09-25 拍板）**：策略面上被登记为「该登记」的读类能力
（`agent_run.read` / `experiment.read` / `provenance.read` 等 **15 条**）**维持逐条放行**——
**不**成类预放行（**不**加 `read.*` 之类的一条规则覆盖一类），**不**新增任何 `allow`。
理由是 AGENTS.md §9 的**默认 deny** 粒度不允许从能力级降到类别级：一次误判的影响面更大。

**判据口径（三条，各自机械可判）**：

1. **逐条 = 每条规则只命名一个具体能力**：策略面每个 `capability:` 的值都必须是能力词表的
   **精确成员**，且**没有任何规则的能力是另一个能力的段前缀**（`read` 覆盖 `read.x` 正是
   「成类放行」的形态）。⇒ 「一条规则覆盖一类」在结构上不可能成立。
2. **否定判据：不存在类别级 / 通配形态**：策略面全部 `capability:` 里不存在通配符（`*`）、
   不以 `.` 结尾（前缀形态）。该检测器**必须可被按压**（注入 `read.*` ⇒ 判红），
   否则它只是个恒真的空转断言。
3. **证据面：15 条「该登记」没有被成类放行**：从
   `docs/architecture/POLICY_SURFACE_AUDIT.md` 的差集表读出终态为「该登记」的行，
   断言**恰好 15 条**、**全部是读类**、且**一条都没有**出现在策略面的任何 `capability:` 里
   ⇒ 「未取成类预放行」这件事有**可核对的证据**，而不是靠口头承诺。

**零策略面改动的证据**：本判据**只读** `examples/config/policy.yaml` 与
`packages/application/preflight/policy_check.py`；本 GOAL 的改动集里**不得**出现这两个文件。
判据自身不改任何策略（按压用的是**内存内构造的字典**，不落盘）。

**边界**：本判据**不**判定某个读能力**该不该**放行（那是逐次授权时的判断）；
它只钉住「放行的**形态**」——**逐条**，而非**成类**。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
POLICY_FILE = ROOT / "examples" / "config" / "policy.yaml"
VOCABULARY_FILE = ROOT / "examples" / "config" / "capabilities.yaml"
AUDIT_FILE = ROOT / "docs" / "architecture" / "POLICY_SURFACE_AUDIT.md"

POLICY_SECTIONS = ("allow", "allow_with_constraints", "require_approval", "deny")
GRANTING_SECTIONS = ("allow", "allow_with_constraints")
READ_SUFFIXES = ("read", "inspect", "validate")
REGISTERED_STATE = "该登记"
EXPECTED_REGISTERED = 15
WILDCARDS = ("*", "?")


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def policy_body() -> dict[str, Any]:
    """策略面正文（`policy:` 下的四段规则）。"""
    body = _load(POLICY_FILE).get("policy")
    assert isinstance(body, dict), "policy.yaml 必须含 `policy:` 映射，否则本判据在空转"
    return body


def vocabulary() -> set[str]:
    return {str(item) for item in _load(VOCABULARY_FILE).get("capabilities") or []}


def capability_entries(policy: dict[str, Any]) -> list[tuple[str, str]]:
    """策略面全部 (段, capability) —— 只取声明了 `capability:` 的规则。"""
    entries: list[tuple[str, str]] = []
    for section in POLICY_SECTIONS:
        for rule in policy.get(section) or []:
            if rule.get("capability"):
                entries.append((section, str(rule["capability"])))
    return entries


def granted_capabilities(policy: dict[str, Any]) -> set[str]:
    return {
        capability
        for section, capability in capability_entries(policy)
        if section in GRANTING_SECTIONS
    }


def is_read_class(capability: str) -> bool:
    return capability.rsplit(".", 1)[-1] in READ_SUFFIXES


def category_forms(names: list[str]) -> list[str]:
    """类别级 / 通配形态的检测器（返回命中的名字，便于判词点名）。"""
    hits: list[str] = []
    for name in names:
        if any(marker in name for marker in WILDCARDS) or name.endswith("."):
            hits.append(name)
    return sorted(hits)


def prefix_grants(names: list[str]) -> list[str]:
    """段前缀形态的规则：`read` 覆盖 `read.x`（「成类放行」的结构特征）。"""
    hits: list[str] = []
    for name in names:
        if any(other != name and other.startswith(f"{name}.") for other in names):
            hits.append(name)
    return sorted(hits)


def registered_rows() -> list[str]:
    """差集表里终态为「该登记」的能力（去掉反引号与空白）。"""
    rows: list[str] = []
    for line in AUDIT_FILE.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or REGISTERED_STATE not in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and cells[0] and not cells[0].startswith("**"):
            rows.append(cells[0].strip("`"))
    return rows


def test_every_rule_names_exactly_one_concrete_capability() -> None:
    """逐条：每个 `capability:` 都是词表的精确成员，且无段前缀形态的规则。"""
    policy = policy_body()
    names = [capability for _, capability in capability_entries(policy)]
    assert names, "策略面必须至少有一条规则，否则本判据在空转"

    unknown = sorted(set(names) - vocabulary())
    assert unknown == [], f"策略面出现词表外的名字（疑似类别级 / 手写串）：{unknown}"

    prefixes = prefix_grants(names)
    assert prefixes == [], (
        f"存在段前缀形态的规则（一条规则覆盖一类能力）：{prefixes}——D-02(b) 明文不取成类放行"
    )


def test_no_category_level_rule_exists() -> None:
    """否定判据：策略面**不存在**通配 / 前缀形态的 capability；且检测器可被按压。"""
    names = [capability for _, capability in capability_entries(policy_body())]
    assert category_forms(names) == [], f"策略面出现类别级 / 通配形态：{category_forms(names)}"

    injected = [*names, "read.*"]
    assert category_forms(injected) == ["read.*"], (
        "注入 `read.*` 后检测器仍未命中 ⇒ 本判据是恒真断言，不是在判「没有成类放行」"
    )
    assert category_forms([*names, "literature."]) == ["literature."], "前缀形态未被检出"


def test_registered_read_capabilities_are_not_granted_as_a_class() -> None:
    """证据面：15 条「该登记」齐全、全为读类、且**一条都没被放行**。"""
    rows = registered_rows()
    assert len(rows) == EXPECTED_REGISTERED, (
        f"差集表的「该登记」应为 {EXPECTED_REGISTERED} 条，实测 {len(rows)} 条：{rows}"
    )
    not_read = sorted(name for name in rows if not is_read_class(name))
    assert not_read == [], f"「该登记」里出现非读类条目（口径变了）：{not_read}"

    policy = policy_body()
    touched = sorted(name for name in rows if name in granted_capabilities(policy))
    assert touched == [], f"「该登记」的读能力被放行了（D-02(b) 明文不取成类预放行）：{touched}"


def test_read_grants_are_enumerated_one_by_one() -> None:
    """读类放行**逐条**：每条放行都是它自己的规则，且未借任何前缀规则进入放行面。"""
    policy = policy_body()
    granted_read = sorted(name for name in granted_capabilities(policy) if is_read_class(name))
    assert granted_read, "本判据需要至少一条读类放行做载体，否则在空转"

    names = [capability for _, capability in capability_entries(policy)]
    for capability in granted_read:
        sections = [
            section
            for section, name in capability_entries(policy)
            if name == capability and section in GRANTING_SECTIONS
        ]
        assert sections, f"{capability} 在放行面里找不到**精确命名**它的规则"
        covering_prefixes = [
            name for name in prefix_grants(names) if capability.startswith(f"{name}.")
        ]
        assert covering_prefixes == [], (
            f"{capability} 的放行同时也被前缀规则 {covering_prefixes} 覆盖 ⇒ 放行形态不是逐条"
        )
