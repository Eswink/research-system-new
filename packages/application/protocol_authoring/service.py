"""协议草稿应用服务：校验、模板目录、修订引用解析（PLAN-20260908-033）。

安全约束：
- YAML 解析只允许安全加载（safe_load），拒绝重复键与自定义标签；
- 体积/复杂度限制，拒绝超限输入；
- 校验经由 schemas/protocol.schema.json（与 load_protocol 同一 Schema）；
- 校验是纯只读操作：不编译执行、不写 Memory、不预留预算。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema  # type: ignore[import-untyped]
import yaml

from packages.application.ports.protocol_draft_store import (
    DraftQuery,
    DraftRevisionRef,
    DraftSaveResult,
    DraftStoreConflictError,
    DraftTemplate,
    DraftValidationIssue,
    DraftValidationResult,
    ProtocolDraftRecord,
    ProtocolDraftRevision,
    ProtocolDraftStore,
)

_ROOT = Path(__file__).resolve().parents[3]
_SCHEMA_PATH = _ROOT / "schemas" / "protocol.schema.json"
_PROTOCOLS_DIR = _ROOT / "examples" / "protocols"

MAX_YAML_BYTES = 128 * 1024
MAX_PHASES = 64

_SCHEMA_CACHE: dict[str, Any] = {}


class ProtocolDraftValidationError(ValueError):
    """草稿保存被服务端校验拒绝（API 层映射 422）。"""

    def __init__(self, issues: tuple[DraftValidationIssue, ...]) -> None:
        rendered = "; ".join(issue.message for issue in issues)
        super().__init__(f"protocol draft validation failed: {rendered}")
        self.issues = issues


class ProtocolDraftSizeError(ValueError):
    """草稿超出体积/复杂度限制（API 层映射 422）。"""


@dataclass(frozen=True, slots=True)
class DraftTemplateSource:
    """模板注册来源：受控目录内的协议文件（不接受任意路径）。"""

    template_id: str
    display_name: str
    description: str
    relative_path: str  # 相对 examples/protocols/


def _load_schema() -> dict[str, Any]:
    if "protocol" not in _SCHEMA_CACHE:
        _SCHEMA_CACHE["protocol"] = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    schema: Any = _SCHEMA_CACHE["protocol"]
    return schema  # type: ignore[no-any-return]


def parse_yaml_strict(text: str) -> Any:
    """安全解析 YAML：拒绝重复键、拒绝自定义标签、限制体积。

    PyYAML safe_load 本身不执行任意构造；重复键检测通过自定义
    SafeLoader 钩子实现（后键覆盖前键是静默数据丢失，必须拒绝）。
    """
    if len(text.encode("utf-8")) > MAX_YAML_BYTES:
        raise ProtocolDraftSizeError(f"yaml text exceeds {MAX_YAML_BYTES} bytes")

    class _StrictLoader(yaml.SafeLoader):
        """safe_load 家族 Loader（无任意对象构造能力）+ 重复键拒绝。"""

    def _no_duplicates(
        loader: yaml.SafeLoader, node: yaml.Node, deep: bool = False
    ) -> dict[Any, Any]:
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise yaml.constructor.ConstructorError(
                    None, None, f"duplicate key in mapping: {key!r}", key_node.start_mark
                )
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    _StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates)
    try:
        # _StrictLoader 继承 yaml.SafeLoader：与 yaml.safe_load 同一安全级别，
        # 仅追加重复键拒绝；不使用 unsafe FullLoader/Loader。
        return yaml.load(text, Loader=_StrictLoader)  # noqa: S506 - SafeLoader 子类
    except yaml.YAMLError as exc:
        raise ProtocolDraftValidationError((
            DraftValidationIssue(path="$", code="YAML_PARSE", message=str(exc)),
        )) from exc


def validate_yaml_document(text: str) -> DraftValidationResult:
    """服务端校验：解析 + Schema 校验；只读、零副作用。"""
    try:
        document = parse_yaml_strict(text)
    except ProtocolDraftSizeError:
        raise
    except ProtocolDraftValidationError as exc:
        return DraftValidationResult(ok=False, issues=exc.issues)
    except Exception as exc:  # noqa: BLE001 - 任何解析异常都收敛为校验失败
        return DraftValidationResult(
            ok=False,
            issues=(DraftValidationIssue(path="$", code="YAML_PARSE", message=str(exc)),),
        )
    if not isinstance(document, dict):
        return DraftValidationResult(
            ok=False,
            issues=(
                DraftValidationIssue(path="$", code="SCHEMA_TYPE", message="must be a mapping"),
            ),
        )
    errors = sorted(
        jsonschema.Draft202012Validator(_load_schema()).iter_errors(document),
        key=lambda item: list(item.path),
    )
    if errors:
        issues = tuple(
            DraftValidationIssue(
                path="$." + ".".join(str(part) for part in error.path) if list(error.path) else "$",
                code="SCHEMA_INVALID",
                message=error.message,
            )
            for error in errors
        )
        return DraftValidationResult(ok=False, issues=issues)
    protocol_id = str(document["id"])
    return DraftValidationResult(
        ok=True,
        issues=(),
        protocol_id=protocol_id,
        protocol_digest="sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest(),
        phase_count=len(document.get("phases", [])),
    )


class DraftTemplates:
    """受控模板目录：只从 examples/protocols/ 注册的文件提供正文。"""

    def __init__(self, sources: tuple[DraftTemplateSource, ...]) -> None:
        self._sources = {source.template_id: source for source in sources}
        self._cache: dict[str, DraftTemplate] = {}

    def list(self) -> tuple[DraftTemplate, ...]:
        return tuple(self._load(source) for source in self._sources.values())

    def get(self, template_id: str) -> DraftTemplate | None:
        source = self._sources.get(template_id)
        return None if source is None else self._load(source)

    def _load(self, source: DraftTemplateSource) -> DraftTemplate:
        cached = self._cache.get(source.template_id)
        if cached is not None:
            return cached
        path = _PROTOCOLS_DIR / source.relative_path
        if not path.is_file():
            raise ProtocolDraftSizeError(f"template source missing: {source.relative_path}")
        text = path.read_text(encoding="utf-8")
        template = DraftTemplate(
            template_id=source.template_id,
            display_name=source.display_name,
            description=source.description,
            yaml_text=text,
            source=f"examples/protocols/{source.relative_path}",
        )
        self._cache[source.template_id] = template
        return template


class DraftService:
    """草稿应用服务：校验 + 保存编排（存储注入）。

    text_loader 由 composition root 注入（adapters 的 YAML→Domain 实现）；
    供运行入口从不可变修订正文构造 ProtocolDefinition。
    """

    def __init__(
        self,
        store: ProtocolDraftStore,
        templates: DraftTemplates,
        *,
        project_id: str = "example-project",
        text_loader: Any | None = None,
    ) -> None:
        self._store = store
        self._templates = templates
        self._project_id = project_id
        self._text_loader = text_loader

    def load_protocol(self, yaml_text: str) -> Any:
        """修订正文 → ProtocolDefinition（loader 未注入时报错）。"""
        if self._text_loader is None:
            raise RuntimeError("protocol text loader not configured")
        return self._text_loader(yaml_text)

    # ── 校验 ──
    def validate(self, yaml_text: str) -> DraftValidationResult:
        return validate_yaml_document(yaml_text)

    # ── 模板 ──
    def list_templates(self) -> tuple[DraftTemplate, ...]:
        return self._templates.list()

    def get_template(self, template_id: str) -> DraftTemplate | None:
        return self._templates.get(template_id)

    # ── 草稿 CRUD ──
    def create(self, *, name: str, yaml_text: str, idempotency_key: str) -> ProtocolDraftRecord:
        result = validate_yaml_document(yaml_text)
        if not result.ok:
            raise ProtocolDraftValidationError(result.issues)
        digest = result.protocol_digest
        if digest is None:  # pragma: no cover - ok=True 必有 digest
            raise ProtocolDraftValidationError((
                DraftValidationIssue(path="$", code="DIGEST_MISSING", message="no digest"),
            ))
        return self._store.create(self._project_id, name, yaml_text, digest, idempotency_key)

    def get(self, draft_id: str) -> ProtocolDraftRecord | None:
        return self._store.get(draft_id)

    def list(self, *, limit: int = 50, offset: int = 0) -> tuple[ProtocolDraftRecord, ...]:
        return self._store.list(DraftQuery(project_id=self._project_id, limit=limit, offset=offset))

    def save(
        self,
        draft_id: str,
        *,
        yaml_text: str,
        expected_revision: int,
        idempotency_key: str,
    ) -> DraftSaveResult:
        result = validate_yaml_document(yaml_text)
        if not result.ok:
            raise ProtocolDraftValidationError(result.issues)
        digest = result.protocol_digest
        if digest is None:  # pragma: no cover - ok=True 必有 digest
            raise ProtocolDraftValidationError((
                DraftValidationIssue(path="$", code="DIGEST_MISSING", message="no digest"),
            ))
        return self._store.save(
            draft_id,
            yaml_text=yaml_text,
            source_digest=digest,
            expected_revision=expected_revision,
            idempotency_key=idempotency_key,
        )

    def list_revisions(self, draft_id: str) -> tuple[ProtocolDraftRevision, ...]:
        return self._store.list_revisions(draft_id)

    def get_revision(self, draft_id: str, revision: int) -> ProtocolDraftRevision | None:
        return self._store.get_revision(draft_id, revision)

    def revision_ref(self, draft_id: str, revision: int) -> DraftRevisionRef:
        record = self._store.get_revision(draft_id, revision)
        if record is None:
            raise KeyError(f"draft revision not found: {draft_id}@{revision}")
        return DraftRevisionRef(draft_id=draft_id, revision=revision)

    def delete(self, draft_id: str) -> bool:
        """物理删除草稿（Port delete 透传；不存在返回 False）。"""
        return self._store.delete(draft_id)


def conflict_revision(exc: DraftStoreConflictError) -> int:
    """冲突错误的当前修订号（API 层 412 响应体使用）。"""
    return exc.current_revision
