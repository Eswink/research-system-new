"""Console demo 输出与占位事件工厂(composition 私有拆分,规模阈值)。"""

from __future__ import annotations

from packages.application.ports import EventPublisher


class FakeEventPublisherFactory:
    """占位（dataclass default 惰性构造用）；真实装配走 assemble()。"""

    def __call__(self) -> EventPublisher:
        from adapters.fakes.event_publisher import FakeEventPublisher

        return FakeEventPublisher()


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
