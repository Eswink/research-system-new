"""OpenHands Runtime Adapter（M6）。

Research OS AgentRuntime Port → OpenHandsRuntimeAdapter → OpenHands SDK v1.42.0。
OpenHands 类型只存在于本包；Domain/Application 不 import OpenHands。
"""

from adapters.openhands.error_mapping import (
    map_agent_error_event,
    map_conversation_error_event,
    map_conversation_run_error,
    map_unexpected_exception,
    port_cancelled,
)
from adapters.openhands.event_mapping import map_event, map_event_stream
from adapters.openhands.runtime_adapter import OpenHandsRuntimeAdapter
from adapters.openhands.session_types import (
    AdapterDependencies,
    map_status_to_domain,
)

__all__ = [
    "OpenHandsRuntimeAdapter",
    "AdapterDependencies",
    "map_status_to_domain",
    "map_event",
    "map_event_stream",
    "map_agent_error_event",
    "map_conversation_error_event",
    "map_conversation_run_error",
    "map_unexpected_exception",
    "port_cancelled",
]
