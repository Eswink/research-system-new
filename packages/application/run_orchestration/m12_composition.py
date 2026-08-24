"""M12 Reference Workflow composition（WP1：Single Production Run Composition）。

不建立第二套 Research Workflow：复用 M2 `compile_and_preflight` / `freeze_manifest`
正式链，在 composition 层把 M12 真实运行维度补全到 `RunManifest` 后冻结：

- model_runtime_fingerprints：真实 probe 结果或 NOT_VERIFIED 占位（WP7）；
- endpoint_config_digest / probe_suite_digest：relay 配置与 probe suite 的
  canonical digest（不含 credential 明文）；
- fallback_audit：显式冻结 fallback 语义（无 fallback 必须为 {"mode": "none"}）；
- image_digest：实验沙箱镜像 digest（M9 真实容器执行）；
- skill_versions：M8 Skill Registry 版本 pin；
- evaluation_dataset_digest：M11 评测数据集冻结 digest。

下游所有阶段（experiment / evidence / evaluation / budget / deliverable）
必须以本 composition 产出的 manifest digest 作为 provenance 根；
preflight 未通过时禁止冻结（ManifestFreezeError，与 M7 语义一致）。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Mapping

from packages.application.ports import CatalogSnapshot, PreflightContext, ProjectSettings
from packages.application.preflight.preflight import (
    ManifestFreezeError,
    compile_and_preflight,
    freeze_manifest,
)
from packages.domain.core import Digest
from packages.domain.manifest import RunManifest
from packages.domain.protocols import CompiledRunPlan, PreflightReport


@dataclass(frozen=True, slots=True)
class FallbackFreeze:
    """显式冻结 fallback 语义（可审计运行事实，不允许缺省模糊）。"""

    mode: str = "none"  # "none" | "planned"
    from_model: str | None = None
    to_model: str | None = None
    trigger: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.mode not in ("none", "planned"):
            raise ValueError("fallback mode must be 'none' or 'planned'")
        if self.mode == "planned":
            if not (self.from_model and self.to_model and self.trigger):
                raise ValueError("planned fallback requires from_model, to_model and trigger")

    def to_audit(self) -> dict[str, object]:
        if self.mode == "none":
            return {"mode": "none"}
        return {
            "mode": "planned",
            "from_model": self.from_model,
            "to_model": self.to_model,
            "trigger": self.trigger,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class M12ManifestExtras:
    """M12 真实运行维度（全部 optional；None/空 = 不冻结，不伪填充）。"""

    model_runtime_fingerprints: dict[str, object] = field(default_factory=dict)
    endpoint_config_digest: str | None = None
    probe_suite_digest: str | None = None
    fallback: FallbackFreeze = field(default_factory=FallbackFreeze)
    image_digest: str | None = None
    skill_versions: dict[str, str] = field(default_factory=dict)
    evaluation_dataset_digest: str | None = None

    def bind(self, manifest: RunManifest) -> RunManifest:
        """把 M12 维度绑定到基础 manifest（不修改原对象；digest 自动覆盖）。"""
        return replace(
            manifest,
            model_runtime_fingerprints=dict(self.model_runtime_fingerprints),
            endpoint_config_digest=self.endpoint_config_digest,
            probe_suite_digest=self.probe_suite_digest,
            fallback_audit=self.fallback.to_audit(),
            image_digest=self.image_digest,
            skill_versions=dict(self.skill_versions),
            evaluation_dataset_digest=self.evaluation_dataset_digest,
        )


@dataclass(frozen=True, slots=True)
class M12CompositionRequest:
    """一次 M12 组合请求（参数对象，避免函数参数超限）。"""

    run_id: str
    protocol: Any
    catalog: CatalogSnapshot
    project: ProjectSettings
    context: PreflightContext
    extras: M12ManifestExtras | None = None


@dataclass(frozen=True, slots=True)
class M12CompositionResult:
    """组合产物：plan/report/manifest 与冻结 digests。"""

    plan: CompiledRunPlan
    report: PreflightReport
    manifest: RunManifest
    manifest_digest: Digest
    semantic_digest: Digest


def compose_m12_run(request: M12CompositionRequest) -> M12CompositionResult:
    """compile → preflight → freeze（含 M12 维度）单入口。

    失败语义：preflight 未通过时抛 ManifestFreezeError（与 M7 一致），
    绝不冻结未通过预检的 manifest。
    """
    plan, report = compile_and_preflight(
        request.protocol, request.catalog, request.project, request.context
    )
    if plan is None or not report.passed:
        codes = sorted({item.code for item in report.findings})
        raise ManifestFreezeError(
            f"cannot freeze M12 manifest: preflight failed ({', '.join(codes)})"
        )
    base = freeze_manifest(request.run_id, plan, report, request.context)
    manifest = request.extras.bind(base) if request.extras else base
    return M12CompositionResult(
        plan=plan,
        report=report,
        manifest=manifest,
        manifest_digest=manifest.digest(),
        semantic_digest=manifest.semantic_digest(),
    )


def manifest_anchors(manifest: RunManifest) -> dict[str, object]:
    """M12 完成态要求的 manifest 锚点检查（供 harness/review 使用）。

    返回 {"ok": bool, "missing": [锚点名, ...]}；不抛异常，只报告缺口。
    必须锚点：fallback 显式冻结 / fingerprint 已冻结（NOT VERIFIED 占位也算）/
    镜像 digest / 评测数据集 digest。
    endpoint/probe suite digest 仅在 relay 已配置时要求（未配置 = NOT VERIFIED
    诚实占位，不视为缺口）。
    """
    missing: list[str] = []
    if not manifest.fallback_audit:
        missing.append("fallback_audit")
    if not manifest.model_runtime_fingerprints:
        missing.append("model_runtime_fingerprints")
    if manifest.endpoint_config_digest is None and manifest.model_runtime_fingerprints:
        verified = any(
            isinstance(item, Mapping) and item.get("verified") is True
            for item in manifest.model_runtime_fingerprints.values()
        )
        if verified:
            missing.append("endpoint_config_digest")
    if manifest.image_digest is None:
        missing.append("image_digest")
    if manifest.evaluation_dataset_digest is None:
        missing.append("evaluation_dataset_digest")
    return {"ok": not missing, "missing": missing}


def fingerprint_payload(fingerprint: object) -> dict[str, object]:
    """把 ModelRuntimeFingerprint（或占位 dict）转为可审计 dict（脱敏）。"""
    if isinstance(fingerprint, Mapping):
        return dict(fingerprint)
    fields = getattr(fingerprint, "__dataclass_fields__", None)
    if fields is None:
        return {"unserializable": str(type(fingerprint).__name__)}
    return {
        name: (str(getattr(fingerprint, name)) if getattr(fingerprint, name) is not None else None)
        for name in (
            "endpoint_config_digest",
            "requested_model_id",
            "returned_model_identifier",
            "system_fingerprint",
            "probe_suite_digest",
            "calibration_prompt_version",
            "calibration_result_digest",
        )
        if name in fields
    }


__all__ = [
    "FallbackFreeze",
    "M12CompositionRequest",
    "M12CompositionResult",
    "M12ManifestExtras",
    "compose_m12_run",
    "fingerprint_payload",
    "manifest_anchors",
]
