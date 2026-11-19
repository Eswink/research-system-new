"""GOAL-116 EC-01 判据：**PRD 的说法 == 树的事实**（逐条断言 + 每条一个反证臂）。

**它补哪一格**：`docs/product/PRD.md` 是产品需求面的单一权威。没有判据时，把 §7.1 的
读数留在旧值、把需求表的状态从 `未实现` 改成 `已实现`、或把树里的
`AUTHORED_ALLOWED_BY_DEFAULT` 翻成 `True`，全仓不会有任何东西变红。

**判什么**（每条违反以**条号**开头；实现见 `prd_claim_checks.violations`）：

- `C-STR`：九节齐全、需求表列序 `ID | 需求 | 状态 | 判据`、状态只用四值词表、ID 连续；
- `C-CITE`：需求表引用的每条仓库路径都在树里；
- `C-INDEX` / `C-LEGACY`：`docs/INDEX.md` 登记 PRD 与基准接入说明；两份历史档案顶部有
  指针且内容未被删；
- `C-CONSOLE` / `C-OPENAPI` / `C-CAPS` / `C-PHASES`：console 三态计数、后端路径与操作数、
  能力声明 / 有 provider / 被协议使用的条数、旗舰协议的相数与角色实例数；
- `C-R05/R07/R08/R09/R10/R12/R13/R14/R15/R16/R19/R20`：EC-01 点名的需求条 —— PRD 的
  状态与数字必须等于从树里算出来的值（不是等于判据里写死的常数）。

**反证臂**：`prd_claim_arms` 注册两类臂（改**文档** / 改**树**）。每个臂都真的跑一次
`violations()`，断言**自己的条号**出现在判词里 —— 只红不点名不算通过。
`test_every_required_claim_has_a_counter_arm` 保证「新增断言却没配臂」不可能静默通过；
`test_facts_are_not_vacuous` 保证 `0 == 0` 式的空真不算绿。

**射程边界**（如实登记）：事实提取是词表 / 结构级的（见 `prd_tree_facts` 的模块
docstring）—— 换一种完全不同的全文抓取 API、或把科学栈装进另一个镜像，本判据抓不到。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.tooling.prd_claim_arms import (
    EXPECTED_ARM_CLAIMS,
    TEXT_ARMS,
    TREE_ARMS,
    TextArm,
    TreeArm,
    temporary_tree,
)
from tests.tooling.prd_claim_checks import documents, violations
from tests.tooling.prd_tree_facts import Facts, collect_facts

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def real_facts() -> Facts:
    return collect_facts(ROOT)


def _mutated_documents(arm: TextArm) -> tuple[str, str, dict[str, str]]:
    prd, index, legacy = documents(ROOT)
    target = {"prd": prd, "index": index}
    if arm.doc in target:
        assert arm.old in target[arm.doc], f"反证臂前置文本不在 {arm.doc}: {arm.old!r}"
        target[arm.doc] = target[arm.doc].replace(arm.old, arm.new)
        return target["prd"], target["index"], legacy
    assert arm.doc in legacy, f"反证臂指向未知文档 {arm.doc}"
    assert arm.old in legacy[arm.doc], f"反证臂前置文本不在 {arm.doc}: {arm.old!r}"
    legacy[arm.doc] = legacy[arm.doc].replace(arm.old, arm.new)
    return prd, index, legacy


def test_the_prd_matches_the_tree(real_facts: Facts) -> None:
    prd, index, legacy = documents(ROOT)
    found = violations(prd, index, legacy, real_facts)
    assert found == [], "\n".join(found)


def test_facts_are_not_vacuous(real_facts: Facts) -> None:
    """空真守卫：提取器静默返回 0 时，`0 == 0` 不得算绿。"""
    assert real_facts.console_total > 0
    assert real_facts.console_full + real_facts.console_partial + real_facts.console_gap
    assert real_facts.openapi_paths > 0 and real_facts.openapi_operations > 0
    assert real_facts.declared_capabilities > 0
    assert real_facts.provider_capabilities > 0
    assert real_facts.protocol_capabilities > 0
    assert real_facts.phases_total > 0 and real_facts.phases_deterministic > 0
    assert real_facts.session_role_instances > 0
    assert real_facts.default_retmax > 0 and real_facts.max_retmax > 0
    assert real_facts.review_thresholds and real_facts.not_judged
    assert real_facts.sandbox_base
    assert real_facts.submission_pieces
    assert real_facts.retrieval_adapters


@pytest.mark.parametrize("arm", TEXT_ARMS, ids=lambda arm: f"{arm.claim}:{arm.doc}")
def test_document_side_arms_go_red(arm: TextArm, real_facts: Facts) -> None:
    prd, index, legacy = _mutated_documents(arm)
    found = violations(prd, index, legacy, real_facts)
    assert any(item.startswith(arm.claim) for item in found), found


@pytest.mark.parametrize("arm", TREE_ARMS, ids=lambda arm: f"{arm.claim}:{arm.name}")
def test_tree_side_arms_go_red(arm: TreeArm, real_facts: Facts) -> None:
    with temporary_tree(arm.files) as tmp:
        arm.mutate(tmp)
        mutated = arm.merge(real_facts, tmp)
    assert mutated != real_facts, f"反证臂没有改变任何读数: {arm.name}"
    prd, index, legacy = documents(ROOT)
    found = violations(prd, index, legacy, mutated)
    assert any(item.startswith(arm.claim) for item in found), found


def test_every_required_claim_has_a_counter_arm() -> None:
    registered = {arm.claim for arm in TEXT_ARMS} | {arm.claim for arm in TREE_ARMS}
    missing = [claim for claim in EXPECTED_ARM_CLAIMS if claim not in registered]
    extra = sorted(registered - set(EXPECTED_ARM_CLAIMS))
    assert not missing, f"这些条号没有反证臂: {missing}"
    assert not extra, f"反证臂注册了未登记的条号: {extra}"
