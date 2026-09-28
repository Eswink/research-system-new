"""GOAL-025 EC-02 支撑：载体**正控制矩阵** + 未注入面金丝雀源的**结构化陈述** + 富化读面现场。

**为什么需要**：GOAL-024 的读面清单里，有 **6 条声明载体没有正控制**（模板 ×2 / 记忆 /
交付物 / 库 ×2 ⇒ 清单只要求「取得到响应」，**没有**要求「看得到它声明的内容」），
另有 **3 条路由取不到**（2 条 workspace 快照 + 1 条库条目），以及 **4 个金丝雀源在默认离线链上
没有注入面**（`task_input` / `tool_arguments` / `tool_output` / `failure_message`）——
后者当时只有一句**散文**式「未验证」。本模块把这三件事变成**可判定陈述**：

1. **载体正控制**：给 6 条载体各注入一份**合成**金丝雀（模板正文 / 记忆正文 / 库条目描述 /
   交付物载荷），证明「这些出口**能**被扫到、且**扫到内容时**看得见」；取不到的路由要么变成
   可取到，要么把「为何取不到」写成**机械事实**（离线装配下 `deps.workspace_snapshots is None`
   ⇒ 503 守卫在位），**不 skip、不 xfail**。
2. **源结构化陈述**：每个无注入面的源都给出**机械断言**（结构 / 属性 / 枚举），而不是散文；
   并逐条登记「需要真实 runtime / 工具面 / 凭据才能取证」的那一半为 **PENDING + 理由**。
3. **富化现场**：**不改** GOAL-024 的夹具与清单（它们是受判资产），只在本模块里换入
   金丝雀模板目录 / 追加 canonical 条目（走**产品自己的写面**：`POST /memory/proposals`、
   `POST /projects/{id}/library`）。

**边界**：canonical 允许持有用户内容 ⇒ 这些注入是**业务真相侧**的注入，不是泄漏；
受判命题仍是「非 canonical 出口零命中」。
"""

from __future__ import annotations

import contextlib
import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from packages.application.ports.protocol_draft_store import DraftTemplate
from packages.application.protocol_authoring.service import DraftTemplates
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from tests.observability.content_canary_support import (
    ARTIFACT_BODY,
    EVIDENCE_BODY,
    PROMPT_TEXT,
)
from tests.observability.read_face_canary_support import (
    ARTIFACT_ID,
    PROJECT_ID,
    ReadFace,
    open_read_face,
)

POSITIVE = "positive_control"
MECHANICAL = "mechanical_reason"
ABSENT_OFFLINE = "absent_offline"

#: 金丝雀模板目录里的模板 id（测试内合成；正文含 `PROMPT_TEXT` 的 token）。
TEMPLATE_ID = "canary-template"
#: 交付物制品的 id 形态（与 `services/api/routers/deliverable.py` 的 `_artifact_ref` 同形）。
DELIVERABLE_SUFFIX = "deliverable.json"
#: 模板正文的参考源（**只读**；与读面夹具用的是同一份协议）。
_TEMPLATE_SOURCE = Path("examples/protocols/m12_reference_research_v1.yaml")


@dataclass(frozen=True, slots=True)
class CarrierControl:
    """一条声明载体 / 取不到路由的判定（`status` 三档之一，`note` 理由非空）。"""

    path: str
    kind: str
    status: str
    note: str


#: 载体正控制矩阵：每条载体一行（`kind` 空 = 只判定「能否被扫到」）。
CARRIER_CONTROLS: tuple[CarrierControl, ...] = (
    CarrierControl(
        "/protocol-templates",
        "prompt",
        POSITIVE,
        "换入金丝雀模板目录（`CanaryTemplates` 子类：只换注入实例、不改产品文件、"
        "不动 `examples/protocols/` 参考资产）⇒ 列表里的 `yaml_text` 必须看得见金丝雀",
    ),
    CarrierControl(
        "/protocol-templates/{template_id}",
        "prompt",
        POSITIVE,
        "同上（单个模板正文）⇒ 必须看得见金丝雀",
    ),
    CarrierControl(
        "/projects/{project_id}/memory",
        "evidencebody",
        POSITIVE,
        "经**产品写面** `POST /memory/proposals` 落一条记忆（tier=RUN 走自动门；"
        "provenance 用已登记的 evidence source）⇒ `MemoryRecordDto.content` 必须看得见金丝雀",
    ),
    CarrierControl(
        "/runs/{run_id}/deliverable",
        "artifactbody",
        POSITIVE,
        "seed 交付物制品 `<run_id>:deliverable.json`（与 `_artifact_ref` 同形）"
        "⇒ `available=true` 且 `DeliverableDto.deliverable` 必须看得见金丝雀",
    ),
    CarrierControl(
        "/library/{resource_id}",
        "prompt",
        POSITIVE,
        "经**产品写面** `POST /projects/{id}/library` 建条目 ⇒ 该路由从「取不到」变成"
        "**可取到**，且 `LibraryResourceDto.description` 必须看得见金丝雀",
    ),
    CarrierControl(
        "/projects/{project_id}/library",
        "prompt",
        POSITIVE,
        "同上（库列表）⇒ 条目 DTO 的 `description` 必须看得见金丝雀",
    ),
    CarrierControl(
        "/workspace-snapshots/{digest}/files",
        "",
        MECHANICAL,
        "离线装配下 `deps.workspace_snapshots is None` ⇒ 路由按 503 守卫拒绝"
        "（产品明文：未配置快照根不返回空树）⇒ 取不到是**结构事实**，不是静默跳过；"
        "真实部署面（配置了快照根）**未验证**",
    ),
    CarrierControl(
        "/workspace-snapshots/{left}/diff/{right}",
        "",
        MECHANICAL,
        "同上（同一条守卫）",
    ),
)

#: 正控制载体**下界**（不许收缩成「都不做正控制」；承 MEM-160）。
MIN_POSITIVE_CARRIERS = 6


@dataclass(frozen=True, slots=True)
class SourceAdjudication:
    """一个金丝雀源在默认离线链上的判定（机械证据 + 真实面的 PENDING 理由）。"""

    source: str
    status: str
    evidence: str
    pending_reason: str


#: 四个「无注入面」源的结构化陈述（替代 GOAL-024 里的散文式「未验证」）。
SOURCE_ADJUDICATIONS: tuple[SourceAdjudication, ...] = (
    SourceAdjudication(
        "task_input",
        ABSENT_OFFLINE,
        "`StartRunCommand` 的自由文本面只有 `notes`（离线链为空 dict）与 `protocol_body`"
        "（= `prompt_text` 源，已注入且已扫描）⇒ 默认离线链上**没有独立的『任务输入』对象面**",
        "真实 runtime / 工具面启用后，任务输入可能经 `notes` / 工具参数进链 ⇒ 需重新取证",
    ),
    SourceAdjudication(
        "tool_arguments",
        ABSENT_OFFLINE,
        "Fake runtime **没有工具调用面**（`execute_tool` / `call_tool` / `invoke_tool` / `tools` "
        "四个属性全无）⇒ 离线链上没有工具参数的承载体；"
        "`RuntimeEventKind.TOOL_CALL_REQUESTED` 在枚举里**真实存在** ⇒ 该断言不是空转",
        "真实工具面（MCP / Native / REST / Remote Worker）启用后才承载工具参数"
        " ⇒ 需真实 runtime 取证",
    ),
    SourceAdjudication(
        "tool_output",
        ABSENT_OFFLINE,
        "同上：链上没有工具输出的承载体（同一个属性面断言）",
        "同上（真实工具面的回包）⇒ 需真实 runtime 取证",
    ),
    SourceAdjudication(
        "failure_message",
        ABSENT_OFFLINE,
        "失败分支的 runtime **结构化输出为空**（`FailingRuntime`）⇒ 失败文本只能由产品侧生成；"
        "GOAL-024 cycle 2 已证失败载荷面零命中 ⇒ 该源在离线链上无用户内容通道",
        "真实 runtime 的失败文本可能含调用方内容（异常消息 / 端点回包）⇒ 需真实 runtime 取证",
    ),
)

#: 工具调用面的属性名（断言 Fake **没有**这些面；加一个就要重新判定）。
TOOL_SURFACE_ATTRS: tuple[str, ...] = ("execute_tool", "call_tool", "invoke_tool", "tools")


class CanaryTemplates(DraftTemplates):
    """受控模板目录的金丝雀变体：只**提供**带合成金丝雀的 `DraftTemplate`。

    与 `DraftTemplates` 同面（`list()` / `get()`），但**不读文件** ⇒ 不动 `examples/protocols/`
    的任何参考资产（那些资产被别的套件复用，改它们等于改夹具的失败形态）。
    """

    def __init__(self, template_id: str, yaml_text: str) -> None:
        super().__init__(())
        self._canary = DraftTemplate(
            template_id=template_id,
            display_name="Canary Template",
            description="GOAL-025 EC-02 正控制：模板正文携带合成金丝雀",
            yaml_text=yaml_text,
            source=f"tests://{template_id}",
        )

    def list(self) -> tuple[DraftTemplate, ...]:
        return (self._canary,)

    def get(self, template_id: str) -> DraftTemplate | None:
        return self._canary if template_id == self._canary.template_id else None


def canary_template_text() -> str:
    """模板正文：把金丝雀放进协议正文的一等字段（`name`），而不是注释。"""
    text = _TEMPLATE_SOURCE.read_text(encoding="utf-8")
    return text.replace("name: Domain Discovery", f"name: Tpl {PROMPT_TEXT.value}", 1)


def _swap_templates(face: ReadFace) -> None:
    """换入金丝雀模板目录（草稿存储与既有装配同源：同一 SQLite 连接）。"""
    from adapters.contracts.protocol_text_loader import load_protocol_from_text
    from adapters.sqlite.protocol_draft_store import SqliteProtocolDraftStore
    from packages.application.protocol_authoring.service import DraftService

    face.deps.protocol_draft_service = DraftService(
        SqliteProtocolDraftStore(connection=face.deps._connection),  # noqa: SLF001 - 同源装配
        CanaryTemplates(TEMPLATE_ID, canary_template_text()),
        text_loader=load_protocol_from_text,
    )


def _register_evidence_source(face: ReadFace) -> None:
    """把制品登记为 **evidence source**（canonical 侧登记；记忆门的 provenance 白名单据此放行）。"""
    from packages.domain.evidence import SourceRecord

    meta = face.deps.artifacts.meta(ARTIFACT_ID)
    face.deps.ledger.register_source(
        SourceRecord(origin=ARTIFACT_ID, content_digest=str(meta.digest))
    )


def _commit_memory(face: ReadFace) -> str:
    """走**产品写面**落一条带金丝雀的记忆（tier=RUN ⇒ 自动门；provenance 用已登记来源）。"""
    response = face.client.post(
        "/memory/proposals",
        json={
            "tier": "RUN",
            "kind": "FACT",
            "content": EVIDENCE_BODY.value,
            "provenance": ARTIFACT_ID,
            "confidence": 0.9,
        },
        headers={"Idempotency-Key": f"memory-{face.run_id}"},
    )
    assert response.status_code == 201, response.text
    return str(response.json()["record"]["id"])


def _create_library_resource(face: ReadFace) -> str:
    """走**产品写面**建一条带金丝雀的库条目。"""
    response = face.client.post(
        f"/projects/{PROJECT_ID}/library",
        json={
            "kind": "prompt",
            "name": "canary-library-resource",
            "description": PROMPT_TEXT.value,
            "content_ref": ARTIFACT_ID,
            "tags": [],
        },
        headers={"Idempotency-Key": f"library-{face.run_id}"},
    )
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def _seed_deliverable(face: ReadFace) -> str:
    """seed 交付物制品（与 `/runs/{run_id}/deliverable` 的 `_artifact_ref` 同形）。"""
    artifact_id = f"{face.run_id}:{DELIVERABLE_SUFFIX}"
    payload = json.dumps({"text": ARTIFACT_BODY.value}, ensure_ascii=False).encode("utf-8")
    artifact = Artifact(
        id=artifact_id,
        digest=Digest.of_bytes(payload),
        size_bytes=len(payload),
        media_type="application/json",
        source_refs=[f"run:{face.run_id}"],
        classification="execution_result",
    )
    face.deps.artifacts.put(artifact, payload)
    return artifact_id


@dataclass(slots=True)
class EnrichedFace:
    """富化后的读面现场（原 `ReadFace` + 本轮注入的对象 id）。"""

    face: ReadFace
    memory_id: str
    library_id: str
    deliverable_id: str


@contextlib.contextmanager
def open_enriched_read_face() -> Iterator[EnrichedFace]:
    """在 GOAL-024 的现场之上**加**四类注入（不改任何既有夹具与清单）。"""
    with open_read_face() as face:
        _swap_templates(face)
        _register_evidence_source(face)
        memory_id = _commit_memory(face)
        library_id = _create_library_resource(face)
        deliverable_id = _seed_deliverable(face)
        yield EnrichedFace(
            face=face,
            memory_id=memory_id,
            library_id=library_id,
            deliverable_id=deliverable_id,
        )


def positive_controls() -> tuple[CarrierControl, ...]:
    return tuple(item for item in CARRIER_CONTROLS if item.status == POSITIVE)


def carrier_findings(route: str, kinds: list[str], expected: str) -> list[str]:
    """纯函数：正控制载体**没看到**它声明的内容 ⇒ 判红（白名单不许靠「不返回」过关）。"""
    if not expected or expected in kinds:
        return []
    return [f"正控制载体没看到它声明的内容:{route} 缺 {expected}（实测命中 {kinds}）"]
