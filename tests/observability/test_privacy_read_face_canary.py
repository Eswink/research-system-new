"""GOAL-024 EC-02 读面判据：应用级读面白名单 + 逐路由实取 + 两向反证 + 按压。

**受判命题**：沿默认离线链注入合成内容金丝雀后，读面响应里**只**在**契约声明返回内容**
的路由（草稿正文 / 制品正文 / claim 正文）能看到它；其余路由**零命中**。

判据形态（承 MEM-158 / MEM-156 / MEM-160）：

- 清单是**分区**（逐条显式、理由非空、无第三种状态），并有**上下界**（声明面 ≤ 15、
  零命中面 ≥ 45）——把任何路由标成"声明内容"就能全绿的退路被上界堵死；
- **非空真**：先证明 canonical 里真的写进了三种金丝雀（否则零命中是空真），
  再要求实取到非空响应的零命中路由 ≥ 40 条；
- **两向反证**：声明载体必须真的看得到它声明的内容；零命中路由出现任何金丝雀都判红
  （失败消息**点名路由与 kind**）；
- **按压**：真实应用上新增一条未登记路由 ⇒ 判红；登记里出现路由树没有的路径 ⇒ 判红。
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from tests.observability.read_face_canary_support import (
    ReadFace,
    fill_path,
    open_read_face,
    read_routes,
    response_text,
    scan,
)
from tests.observability.read_face_route_registry import (
    DECLARED,
    MIN_EXERCISED,
    UNEXERCISED_DECLARED,
    UNEXERCISED_ZERO_HIT,
    ZERO_HIT_ROUTES,
    all_rules,
    partition_findings,
    verify_route,
)

#: 七个金丝雀源在**默认离线链**上的注入面：逐条登记（做不到的写理由，不许静默）。
#: (源, 是否注入, 依据/理由)
CANARY_SOURCE_INJECTION: tuple[tuple[str, bool, str], ...] = (
    (
        "prompt_text",
        True,
        "注入：用户起草的协议正文（草稿 `yaml_text`，随 run 冻结进 canonical）",
    ),
    (
        "task_input",
        False,
        "未单独注入：默认离线链没有独立的『任务输入』对象面（run 的输入来自协议声明与"
        "结构化输出），与 prompt_text 同载体 ⇒ 该源未分面验证",
    ),
    (
        "artifact_body",
        True,
        "注入：会话结构化输出 → 内容寻址制品（`SqliteArtifactStore`/`FakeArtifactStore`）",
    ),
    (
        "evidence_body",
        True,
        "注入：claim 正文（`Claim.statement`，走 ledger 的 canonical 写面）",
    ),
    (
        "tool_arguments",
        False,
        "未注入：Fake runtime 不产生工具调用事件（`RuntimeEvent` 只有 session 级 kind）"
        "⇒ 默认链上没有工具参数的承载体",
    ),
    (
        "tool_output",
        False,
        "未注入：同上（链上没有工具输出的承载体）",
    ),
    (
        "failure_message",
        False,
        "未注入：失败文本由产品生成（验收门拒绝理由），不是用户内容 ⇒ 该源在默认链上"
        "没有用户内容注入面（cycle 2 的失败载荷面判的是产品文本不含金丝雀）",
    ),
)


@pytest.fixture(scope="module")
def face() -> Iterator[ReadFace]:
    with open_read_face() as opened:
        yield opened


def test_registry_is_an_exact_partition_of_the_read_face(face: ReadFace) -> None:
    """清单 = 路由树的读面（未分类 / 重复 / 陈旧 / 空理由 / 上下界，五条都判）。"""
    findings = partition_findings(read_routes(face.app))
    assert not findings, f"读面清单不是分区:{findings}"


def test_canonical_state_really_holds_the_canaries(face: ReadFace) -> None:
    """非空真：canonical 侧真的写进了金丝雀（否则零命中是空真）。"""
    found = scan(face.canonical_text)
    missing = sorted({"prompt", "artifactbody", "evidencebody"} - set(found))
    assert not missing, f"canonical 里没有这些金丝雀 ⇒ 读面零命中会是空真:{missing}"


def test_declared_content_routes_carry_their_declared_content(face: ReadFace) -> None:
    """正控制：声明载体必须真的看得到它声明的内容（白名单不许说谎）。"""
    failed: list[str] = []
    unfillable: list[str] = []
    for rule in all_rules():
        if rule.verdict != DECLARED:
            continue
        filled = fill_path(rule.path, face.ids)
        if filled is None:
            unfillable.append(rule.path)
            continue
        response = face.client.get(filled)
        if rule.kinds:
            failed.extend(verify_route(rule, scan(response_text(response))))
    assert not failed, f"声明载体的正控制失败:{failed}"
    assert sorted(unfillable) == sorted(UNEXERCISED_DECLARED), (
        f"取不到的声明载体与登记不一致:{sorted(unfillable)} / {sorted(UNEXERCISED_DECLARED)}"
    )


def test_no_canary_on_any_zero_hit_read_route(face: ReadFace) -> None:
    """零命中：非声明载体的读面路由一个金丝雀都不许出现；失败消息点名路由与 kind。"""
    violations: list[str] = []
    exercised = 0
    unexercised: list[str] = []
    for rule in ZERO_HIT_ROUTES:
        filled = fill_path(rule.path, face.ids)
        if filled is None:
            unexercised.append(rule.path)
            continue
        response = face.client.get(filled)
        if response.content:
            exercised += 1
        violations.extend(verify_route(rule, scan(response_text(response))))
    assert not violations, f"读面越界(未声明载体出现金丝雀):{violations}"
    assert sorted(unexercised) == sorted(UNEXERCISED_ZERO_HIT), (
        f"无法实取的路由集合与登记不一致:实取 {sorted(unexercised)} / 登记 "
        f"{sorted(UNEXERCISED_ZERO_HIT)}"
    )
    assert exercised >= MIN_EXERCISED, (
        f"实取到非空响应的零命中路由只有 {exercised} 条 < 下界 {MIN_EXERCISED} ⇒ 空转绿"
    )


def test_a_canary_on_a_zero_hit_route_is_red() -> None:
    """反证：把金丝雀塞进零命中路由的响应文本 ⇒ 判红并点名路由与 kind。"""
    rule = next(item for item in ZERO_HIT_ROUTES if item.path == "/health")
    findings = verify_route(rule, ["prompt"])
    assert findings and "/health" in findings[0] and "prompt" in findings[0], findings


def test_a_declared_carrier_without_its_content_is_red() -> None:
    """反证：声明载体没看到声明的内容 ⇒ 判红（白名单不能靠"什么也不返回"过关）。"""
    from tests.observability.read_face_route_registry import DECLARED_CONTENT

    rule = DECLARED_CONTENT[0]
    findings = verify_route(rule, [])
    assert findings and rule.path in findings[0], findings


def test_an_unregistered_read_route_is_red(face: ReadFace) -> None:
    """按压（真实应用）：新增一条未登记的读路由 ⇒ 分区自审判红并点名。"""

    async def press_probe() -> dict[str, str]:
        return {"status": "ok"}

    face.app.get("/__press-probe")(press_probe)
    findings = partition_findings(read_routes(face.app))
    assert any("/__press-probe" in item for item in findings), findings


def test_a_stale_registry_entry_is_red(face: ReadFace) -> None:
    """按压：登记里出现路由树没有的路径 ⇒ 判红并点名。"""
    paths = tuple(path for path in read_routes(face.app) if path != "/health")
    findings = partition_findings(paths)
    assert any("陈旧登记" in item and "/health" in item for item in findings), findings


def test_unclassified_path_is_red() -> None:
    """反证：路由树里多出一条完全没登记的路由 ⇒ 判红并点名。"""
    findings = partition_findings(("/health", "/__never-registered"))
    assert any("未分类" in item and "/__never-registered" in item for item in findings), findings


def test_canary_sources_are_registered_item_by_item() -> None:
    """七个源逐条登记：注入了的写清观测面，没注入的写清理由（不许空着）。"""
    assert len(CANARY_SOURCE_INJECTION) == 7
    kinds = [item[0] for item in CANARY_SOURCE_INJECTION]
    assert sorted(kinds) == sorted(
        ["prompt_text", "task_input", "artifact_body", "evidence_body", "failure_message"]
        + ["tool_arguments", "tool_output"]
    )
    empty = [item[0] for item in CANARY_SOURCE_INJECTION if not item[2].strip()]
    assert not empty, f"这些源没有登记依据/理由:{empty}"
    injected = [item for item in CANARY_SOURCE_INJECTION if item[1]]
    assert len(injected) >= 3, f"注入面太少:{[item[0] for item in injected]}"
