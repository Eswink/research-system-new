"""Console demo 输出与占位事件工厂(composition 私有拆分,规模阈值)。"""

from __future__ import annotations

from pathlib import Path

from packages.application.ports import EventPublisher

_ROOT = Path(__file__).resolve().parents[2]

#: 协议**声明**的输入制品（`ProtocolPhase.inputs`）→ 其内容来源文件。
#: 值是**制品 id**，与协议文件里的声明必须逐字一致（同源判据钉住这条对齐，
#: 见 `tests/architecture/python/test_declared_input_sources.py`）。
#:
#: 为什么要有这张表：`EVIDENCE_COVERAGE` 在 GOAL-010 EC-02 之后**只认非模型自述的
#: 来源**，所以协议声明的输入必须真的存在于 ArtifactStore，且其 digest 能由文件字节
#: 重算。取不到 ⇒ 任务点名失败，**不**降级成「没有来源但照样通过」。
#:
#: 注意：**上游 phase 的产出不算非模型来源**——它是另一个 agent 的输出，仍是模型
#: 自述。所以 `inputs` 只声明**外部供应**的输入，不解析 phase 间的产物引用。
DECLARED_INPUTS: dict[str, str] = {
    "input-corpus:console_demo_v1": "examples/inputs/console-demo-corpus-v1.json",
    "input-corpus:sort_analysis_v1": "examples/inputs/sort-analysis-corpus-v1.json",
}


class FakeEventPublisherFactory:
    """占位（dataclass default 惰性构造用）；真实装配走 assemble()。"""

    def __call__(self) -> EventPublisher:
        from adapters.fakes.event_publisher import FakeEventPublisher

        return FakeEventPublisher()


def seed_declared_inputs(store: object) -> None:
    """把 demo 协议声明的输入制品种入 ArtifactStore（组合根职责）。

    内容取自仓库内文件（字节即真相，任何人都能重算 digest），`created_by` 记为
    组合根而不是任何 agent——这正是它**不是**模型自述的原因。
    """
    from packages.domain.artifacts import Artifact
    from packages.domain.core import Digest
    from packages.domain.enums import ArtifactState

    for artifact_id, relative in DECLARED_INPUTS.items():
        content = _ROOT.joinpath(relative).read_bytes()
        artifact = Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
            storage_uri=None,
            created_by="composition-root",
            source_refs=[f"file:{relative}"],
            classification="declared_input",
        )
        store.put(artifact, content)  # type: ignore[attr-defined]
        store.mark(artifact_id, ArtifactState.VERIFIED)  # type: ignore[attr-defined]


def demo_session_output() -> dict[str, object]:
    """控制面 demo 会话输出（受控 Fake agent loop；UI 如实披露执行体性质）。

    只用于 console_demo 协议使验收 gate 可求值，不冒充真实研究结果。
    """
    return {
        "analysis_report": {
            "summary": "controlled fake session output (M13-R1 console demo)",
            "status": "ok",
        }
    }


def _default_events() -> EventPublisher:
    """ApiDeps events 默认值工厂（dataclass default_factory 用）。"""
    return FakeEventPublisherFactory()()
