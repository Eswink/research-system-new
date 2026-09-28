"""GOAL-025 EC-02 判据：载体**正控制矩阵** + 未注入面源的**判定化**（收 `G24-6` + `G24-1`）。

**受判命题**：
- 6 条**无正控制**的声明载体（模板 ×2 / 记忆 / 交付物 / 库 ×2）必须各自**看到**它声明承载的
  内容 —— 证明这些出口**能**被扫到、且**扫到内容时会红**；
- 3 条**取不到**的路由：能建正控制的就建成可取到（`/library/{resource_id}`），
  不能的就把「为何取不到」断言成**机械事实**（workspace 快照：`deps.workspace_snapshots is None`
  ⇒ 路由按 503 守卫拒绝）；**不 skip、不 xfail**；
- 4 个**无注入面**的金丝雀源（`task_input` / `tool_arguments` / `tool_output` / `failure_message`）
  从散文式「未验证」收窄为**结构化断言**（结构 / 属性 / 枚举 / 行为），
  且**每条都登记**「需要真实 runtime 才能取证」的那一半为 PENDING + 理由。

**判据形态**（承 MEM-158 / MEM-156 / MEM-159 / MEM-160）：载体矩阵与源矩阵都写在**判据源码**里；
必做正控制的载体集合**从 GOAL-024 的登记推出**（`DECLARED_CONTENT` 里 `kinds` 为空的行 +
`UNEXERCISED_*`），不是另写一份清单；正控制面有**下界**；反证两向（凑不出内容 ⇒ 判红；
**不加注入**时看不到内容 ⇒ 零命中不是原现场就有的）。
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from packages.application.ports.agent_runtime import RuntimeEventKind
from packages.application.run_orchestration.commands import StartRunCommand
from packages.domain.core import ID
from tests.observability.content_canary_support import (
    FailingRuntime,
    run_default_offline,
)
from tests.observability.positive_control_support import (
    ABSENT_OFFLINE,
    CARRIER_CONTROLS,
    MIN_POSITIVE_CARRIERS,
    SOURCE_ADJUDICATIONS,
    TOOL_SURFACE_ATTRS,
    EnrichedFace,
    carrier_findings,
    open_enriched_read_face,
    positive_controls,
)
from tests.observability.read_face_canary_support import fill_path, open_read_face, scan
from tests.observability.read_face_route_registry import (
    DECLARED_CONTENT,
    UNEXERCISED_DECLARED,
    UNEXERCISED_ZERO_HIT,
)

#: workspace 快照守卫的期望状态码（未配置快照根 ⇒ 503 + 原因，不返回空树）。
_GUARDED_STATUS = 503
#: 正控制里用到的模板 id（与支撑模块一致）。
_TEMPLATE_ID = "canary-template"


@pytest.fixture(scope="module")
def enriched() -> Iterator[EnrichedFace]:
    with open_enriched_read_face() as opened:
        yield opened


def _text(response: Any) -> str:
    return bytes(response.content).decode("utf-8", errors="ignore")


def test_carrier_matrix_covers_every_registry_entry_without_control() -> None:
    """矩阵不是另一份清单：它必须覆盖 GOAL-024 登记里**没有正控制**的那些行。"""
    needed = {rule.path for rule in DECLARED_CONTENT if not rule.kinds}
    needed |= set(UNEXERCISED_DECLARED) | set(UNEXERCISED_ZERO_HIT)
    covered = {item.path for item in CARRIER_CONTROLS}
    assert needed <= covered, f"这些登记行没有判定:{sorted(needed - covered)}"
    empty = [item.path for item in CARRIER_CONTROLS if not item.note.strip()]
    assert not empty, f"这些行没有理由:{empty}"


def test_positive_control_floor_is_intact() -> None:
    """正控制面**下界**：不许把「都改判成机械理由」当成通过（承 MEM-160）。"""
    assert len(positive_controls()) >= MIN_POSITIVE_CARRIERS, (
        f"正控制载体只有 {len(positive_controls())} 条 < 下界 {MIN_POSITIVE_CARRIERS}"
    )


def test_positive_carriers_really_surface_their_declared_content(enriched: EnrichedFace) -> None:
    """主判据：每条正控制载体都**真的看到**它声明承载的金丝雀（看不到即判红）。"""
    face = enriched.face
    face.ids["template_id"] = _TEMPLATE_ID
    face.ids["resource_id"] = enriched.library_id
    failures: list[str] = []
    for rule in positive_controls():
        filled = fill_path(rule.path, face.ids)
        assert filled is not None, f"路径参数没凑齐:{rule.path}"
        response = face.client.get(filled)
        assert response.status_code < 400, f"{rule.path} 取不到:{response.status_code}"
        failures.extend(carrier_findings(rule.path, scan(_text(response)), rule.kind))
    assert not failures, f"正控制失败（载体看不到它声明的内容）:{failures}"


def test_the_unreachable_library_route_is_now_reachable(enriched: EnrichedFace) -> None:
    """取不到的三条之一建成可取到：`/library/{resource_id}` 现在真的可取到。"""
    face = enriched.face
    face.ids["resource_id"] = enriched.library_id
    filled = fill_path("/library/{resource_id}", face.ids)
    assert filled == f"/library/{enriched.library_id}", filled
    response = face.client.get(filled)
    assert response.status_code == 200, response.text
    assert "prompt" in scan(_text(response)), "库条目没有回它声明的正文"


def test_snapshot_routes_are_refused_by_a_guard_not_skipped(enriched: EnrichedFace) -> None:
    """取不到 = **结构性拒绝**：离线装配无快照读面 ⇒ 守卫 503（真跑这两条路由，不 skip）。"""
    face = enriched.face
    assert face.deps.workspace_snapshots is None, (
        "离线装配下不该有快照读面；若已配置 ⇒ 本行的机械理由失效，必须重新判定"
    )
    files = face.client.get("/workspace-snapshots/deadbeef/files")
    diff = face.client.get("/workspace-snapshots/deadbeef/diff/feedface")
    assert files.status_code == _GUARDED_STATUS, files.text
    assert diff.status_code == _GUARDED_STATUS, diff.text


def test_every_source_adjudication_is_mechanical_and_registers_pending() -> None:
    """源矩阵：四个源逐条在位，机械证据与 PENDING 理由都非空。"""
    sources = {item.source for item in SOURCE_ADJUDICATIONS}
    assert sources == {"task_input", "tool_arguments", "tool_output", "failure_message"}, sources
    for item in SOURCE_ADJUDICATIONS:
        assert item.status == ABSENT_OFFLINE, item.source
        assert item.evidence.strip(), f"{item.source} 没有机械证据"
        assert item.pending_reason.strip(), f"{item.source} 没有登记 PENDING 理由"


def test_task_input_has_no_free_text_carrier_in_the_offline_chain() -> None:
    """`task_input`：`StartRunCommand` 的自由文本面只有 `notes`（离线链为空）与协议正文。"""
    names = {field.name for field in dataclasses.fields(StartRunCommand)}
    assert {"project_id", "protocol_id", "run_id", "trace_id", "notes"} <= names
    empty = StartRunCommand(
        project_id="p",
        protocol_id="x",
        run_id=ID.generate(),
        trace_id="t",
    )
    assert empty.notes == {}, "离线链的 notes 应为空 ⇒ 没有独立的『任务输入』承载体"
    assert empty.protocol_body is None, "离线链的协议正文由草稿冻结进 canonical（见读面夹具）"


def test_tool_sources_have_no_carrier_and_the_vocabulary_exists() -> None:
    """`tool_arguments` / `tool_output`：Fake 无工具面（非空转：枚举里真的有工具调用 kind）。"""
    runtime = FailingRuntime()
    present = [name for name in TOOL_SURFACE_ATTRS if hasattr(runtime, name)]
    assert not present, f"Fake runtime 出现了工具调用面 ⇒ 该源的判定必须重做:{present}"
    assert RuntimeEventKind.TOOL_CALL_REQUESTED.value == "tool_call.requested"


def test_failure_message_source_is_product_generated(receiver: Any, tmp_path: Path) -> None:
    """`failure_message`：失败分支**无用户文本通道**（结构化输出为空）⇒ 文本由产品生成。"""
    failing_runtime = FailingRuntime()
    # 失败分支的 runtime 不带任何结构化输出 ⇒ 该分支上不存在用户内容；失败文本只能由产品侧生成。
    assert failing_runtime._structured_output == {}, "失败分支出现了结构化输出"  # noqa: SLF001
    run = run_default_offline(tmp_path, receiver, failing=True)
    payload = str(getattr(run.outcome, "message", "") or "")
    assert payload.strip(), "失败载荷为空 ⇒ 该面没有被真的观测到"
    assert not scan(payload), f"失败载荷出现金丝雀:{scan(payload)}"


def test_the_positive_control_is_caused_by_our_injection() -> None:
    """反证两向①：**不加**注入时模板路由看不到金丝雀 ⇒ 零命中不是原现场就有的。"""
    with open_read_face() as face:
        response = face.client.get("/protocol-templates")
        assert response.status_code == 200, response.text
        assert not scan(_text(response)), "原现场就有金丝雀 ⇒ 本轮正控制不成立"


def test_a_carrier_that_hides_its_content_is_red() -> None:
    """反证两向②（纯函数）：载体看不到声明内容 ⇒ 判红并点名路由与 kind。"""
    findings = carrier_findings("/protocol-templates", [], "prompt")
    assert findings and "/protocol-templates" in findings[0] and "prompt" in findings[0], findings
