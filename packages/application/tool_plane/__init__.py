"""M8 Tool Plane：ToolCatalog / ToolResolver / ToolPack lifecycle / health / execution。"""

from __future__ import annotations

from packages.application.tool_plane.catalog import (
    ToolCatalog,
    build_tool_catalog,
    catalog_from_pack_records,
    provider_preference_key,
)
from packages.application.tool_plane.execution import (
    ExecuteToolCallOutcome,
    execute_tool_call,
    require_frozen_tool_set,
)
from packages.application.tool_plane.health import (
    ToolHealthSnapshot,
    health_for_resolver,
    mark_disabled,
    record_probe,
    record_probe_failure,
)
from packages.application.tool_plane.lifecycle import (
    PermissionDiff,
    ToolPackLifecycle,
    permission_diff,
)
from packages.application.tool_plane.resolver import (
    CapabilityResolution,
    ResolutionInput,
    ToolBinding,
    freeze_tool_set,
    resolve_all,
    resolve_capability,
    resolve_tool_call,
    unresolved_capabilities,
)
from packages.application.tool_plane.results import (
    ToolOutputResult,
    fetch_spilled_result,
    spill_large_result,
)

__all__ = [
    "CapabilityResolution",
    "ExecuteToolCallOutcome",
    "PermissionDiff",
    "ResolutionInput",
    "ToolBinding",
    "ToolCatalog",
    "ToolHealthSnapshot",
    "ToolOutputResult",
    "ToolPackLifecycle",
    "build_tool_catalog",
    "catalog_from_pack_records",
    "execute_tool_call",
    "fetch_spilled_result",
    "freeze_tool_set",
    "health_for_resolver",
    "mark_disabled",
    "permission_diff",
    "provider_preference_key",
    "record_probe",
    "record_probe_failure",
    "require_frozen_tool_set",
    "resolve_all",
    "resolve_capability",
    "resolve_tool_call",
    "spill_large_result",
    "unresolved_capabilities",
]
