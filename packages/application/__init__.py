"""Research OS application 层包。"""

from packages.application.policy.native import NativePolicyEvaluator
from packages.application.preflight.preflight import (
    DryRunProjection,
    ManifestFreezeError,
    compile_and_preflight,
    dry_run_projection,
    freeze_manifest,
    run_preflight,
)
from packages.application.protocol_compile.compiler import CompileResult, compile_protocol
from packages.application.protocol_compile.ports import (
    CatalogSnapshot,
    PreflightContext,
    ProjectSettings,
)

__all__ = [
    "CatalogSnapshot",
    "CompileResult",
    "DryRunProjection",
    "ManifestFreezeError",
    "NativePolicyEvaluator",
    "PreflightContext",
    "ProjectSettings",
    "compile_and_preflight",
    "compile_protocol",
    "dry_run_projection",
    "freeze_manifest",
    "run_preflight",
]
