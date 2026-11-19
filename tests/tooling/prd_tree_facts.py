"""GOAL-116 EC-01 的**树一侧**：把 PRD 点名的每条事实从树里算出来（离线、只读）。

**为什么不把数字直接写进判据**：写死常数只能证明「判据没变」，不能证明「文档 == 树」。
本模块把 PRD 的每个说法变成**从树里算出来的读数**；判词侧
（`prd_claim_checks.violations`）再逐条比对。于是**任一侧**改动都会判红：

- 改 PRD 的数字 ⇒ 判词找不到树算出来的那个数；
- 改树里的事实（常量 / 配置 / 快照 / 前端清单）⇒ 树算出来的数变了，PRD 没跟上。

**射程（写在这里，不靠文档）**：

- 只提取 PRD 明确点名的事实；不解释语义、不评估这些事实「好不好」。
- 「代码面无 `HypothesisSet` 实体」的扫描面 = `packages` / `services` / `adapters` /
  `apps/web/src`（域实体必落在这些根；`tests/` 与文档不计）。
- 「文献全文未实现」是**词汇层**判据（`rettype=full` / `full text` / `db=pmc` /
  `/pmc/articles`）；换一种完全不同的抓取 API 它抓不到 —— 登记为射程边界。
- Dockerfile 与 `models.yaml` 的扫描**先剔注释行**，注释不算「装了 / 声明了」。
"""

from __future__ import annotations

import ast
import json
import os
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PRD_PATH = "docs/product/PRD.md"
INDEX_PATH = "docs/INDEX.md"
LEGACY_POINTERS: tuple[str, ...] = ("docs/PRODUCT.md", "docs/product/PRD_GAP_ANALYSIS.md")
CAPABILITIES_PATH = "examples/config/capabilities.yaml"
PROVIDERS_PATH = "examples/config/tool_providers.yaml"
PROTOCOLS_DIR = "examples/protocols"
MANUSCRIPT_PROTOCOL = "examples/protocols/direction_to_manuscript_v1.yaml"
OPENAPI_PATH = "docs/api/openapi.m13.json"
CONSOLE_PATH = "apps/web/src/navigation/pageSupport.ts"
RETMAX_PATH = "services/api/retrieval_wiring.py"
AUTHORED_PATH = "packages/application/experiments/script_authority.py"
QUALITY_PATH = "packages/application/deliverable/manuscript_quality.py"
SUBMISSION_PATH = "packages/application/run_orchestration/submission_assembly.py"
PRINCIPAL_PATH = "packages/domain/principal.py"
MODELS_PATH = "examples/config/models.yaml"
SANDBOX_PATH = "adapters/execution/sandbox/Dockerfile"
RETRIEVAL_DIR = "adapters/research_tools"

#: 需求登记表的状态闭集（PRD §6 的机器可读约定，四值，不许别的词）。
STATUS_VOCAB: tuple[str, ...] = ("已实现", "部分", "未实现", "不宣称")

#: 九节：编号 → 标题必须含有的主题词。
SECTION_TOPICS: tuple[tuple[int, tuple[str, ...]], ...] = (
    (1, ("产品是什么", "不是什么")),
    (2, ("用户", "场景")),
    (3, ("工作流",)),
    (4, ("能力矩阵",)),
    (5, ("差距", "优先级")),
    (6, ("需求登记表",)),
    (7, ("验收", "读数")),
    (8, ("声称边界",)),
    (9, ("非目标",)),
)

#: EC-01 点名的需求条（每条都必须有断言 + 反证臂）。
REQUIRED_CLAIMS: tuple[str, ...] = (
    "R-05",
    "R-07",
    "R-08",
    "R-09",
    "R-10",
    "R-12",
    "R-13",
    "R-15",
    "R-16",
    "R-19",
    "R-20",
)

SCIENCE_STACK: tuple[str, ...] = ("numpy", "pandas", "scipy", "matplotlib", "h5py")
SUBMISSION_PIECES: tuple[str, ...] = (
    "cover_letter",
    "author_contributions",
    "conflicts_of_interest",
    "data_availability",
    "supplementary",
)
NOT_JUDGED_THEMES: tuple[str, ...] = (
    "citation supports",
    "argument",
    "method",
    "sufficient",
    "writing style",
)
#: `(标签, 正则)`：命任一条 ⇒ 「能取正文」这件事在树里出现了。
FULL_TEXT_PATTERNS: tuple[tuple[str, str], ...] = (
    ("rettype=full", r"rettype\s*=\s*['\"]?full"),
    ("full text", r"full[-_ ]?text"),
    ("db=pmc", r"db\s*=\s*pmc"),
    ("/pmc/articles", r"/pmc/articles"),
)
#: OpenAPI 的方法顺序（与 PRD §7.1 的写法同序，便于逐字对拍）。
METHOD_ORDER: tuple[str, ...] = ("get", "post", "patch", "put", "delete")


@dataclass(frozen=True)
class Facts:
    """一次树扫描的读数（判词的唯一输入；`root` 用于解析引用存在性）。"""

    root: Path
    default_retmax: int
    max_retmax: int
    authored_by_default: bool
    authored_profile: str
    review_thresholds: tuple[float, ...]
    review_operators: tuple[str, ...]
    not_judged: tuple[str, ...]
    models_vision_keys: int
    sandbox_base: str
    sandbox_science_stack: tuple[str, ...]
    openapi_paths: int
    openapi_operations: int
    openapi_methods: tuple[tuple[str, int], ...]
    openapi_submission_hits: int
    console_total: int
    console_full: int
    console_partial: int
    console_gap: int
    declared_capabilities: int
    provider_capabilities: int
    protocol_capabilities: int
    phases_total: int
    phases_session: int
    phases_deterministic: int
    session_role_instances: int
    full_text_terms: tuple[str, ...]
    code_hypothesis_files: int
    submission_pieces: tuple[str, ...]
    principal_mentions_m18: bool
    retrieval_adapters: tuple[str, ...]


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _yaml(root: Path, relative: str) -> Any:
    text = _text(root, relative)
    return yaml.safe_load(text) if text else None


def _module_literals(root: Path, relative: str) -> dict[str, Any]:
    """模块级字面量赋值（`NAME = <literal>` / `NAME: T = <literal>`）。"""
    text = _text(root, relative)
    if not text:
        return {}
    values: dict[str, Any] = {}
    for node in ast.parse(text, filename=relative).body:
        target: ast.expr | None = None
        value: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            target, value = node.target, node.value
        if not isinstance(target, ast.Name) or value is None:
            continue
        try:
            values[target.id] = ast.literal_eval(value)
        except (ValueError, TypeError):
            continue
    return values


def _int_literal(values: dict[str, Any], name: str) -> int:
    value = values.get(name)
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _walk_dicts(node: Any) -> Iterator[dict[str, Any]]:
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk_dicts(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_dicts(item)


def _review_facts(root: Path) -> tuple[tuple[float, ...], tuple[str, ...]]:
    doc = _yaml(root, "examples/contracts/task_contracts.yaml")
    thresholds: list[float] = []
    operators: list[str] = []
    for node in _walk_dicts(doc):
        if node.get("type") != "REVIEW_SCORE":
            continue
        threshold = node.get("threshold")
        thresholds.append(float(threshold) if isinstance(threshold, int | float) else -1.0)
        operators.append(str(node.get("operator")))
    return tuple(thresholds), tuple(operators)


def _console_facts(root: Path) -> tuple[int, int, int, int]:
    """解析 `pageSupport.ts` 的 `SUPPORT` 对象（括号配平；不跑 Node）。"""
    text = _text(root, CONSOLE_PATH)
    if "const SUPPORT" not in text:
        return (0, 0, 0, 0)
    body = text[text.index("const SUPPORT") : text.index("export function pageSupport")]
    counts = {"full": 0, "partial": 0, "gap": 0}
    total = 0
    cursor = body.index("{") + 1
    key = re.compile(r'"[a-z0-9/-]+"\s*:\s*\{')
    while True:
        match = key.search(body, cursor)
        if match is None:
            break
        depth, index = 0, match.end() - 1
        while index < len(body):
            if body[index] == "{":
                depth += 1
            elif body[index] == "}":
                depth -= 1
                if depth == 0:
                    break
            index += 1
        level = re.search(r'level:\s*"(full|partial|gap)"', body[match.end() : index])
        if level is not None:
            counts[level.group(1)] += 1
            total += 1
        cursor = index + 1
    return total, counts["full"], counts["partial"], counts["gap"]


def _openapi_facts(root: Path) -> tuple[int, int, tuple[tuple[str, int], ...], int]:
    raw = _text(root, OPENAPI_PATH)
    if not raw:
        return 0, 0, (), 0
    doc = json.loads(raw)
    paths = doc.get("paths") if isinstance(doc, dict) else None
    if not isinstance(paths, dict):
        return 0, 0, (), len(re.findall("submission", raw, re.IGNORECASE))
    method_counts: dict[str, int] = {method: 0 for method in METHOD_ORDER}
    operations = 0
    for item in paths.values():
        if not isinstance(item, dict):
            continue
        for method in METHOD_ORDER:
            if method in item:
                method_counts[method] += 1
                operations += 1
    methods = tuple((method, method_counts[method]) for method in METHOD_ORDER)
    return len(paths), operations, methods, len(re.findall("submission", raw, re.IGNORECASE))


def _capability_facts(root: Path) -> tuple[int, int, int]:
    declared_doc = _yaml(root, CAPABILITIES_PATH) or {}
    declared = declared_doc.get("capabilities") if isinstance(declared_doc, dict) else None
    provider_doc = _yaml(root, PROVIDERS_PATH) or {}
    providers = provider_doc.get("tool_providers") if isinstance(provider_doc, dict) else None
    provider_union: set[str] = set()
    for spec in (providers or {}).values():
        if isinstance(spec, dict):
            provider_union |= {str(item) for item in (spec.get("capabilities") or [])}
    protocol_union: set[str] = set()
    for path in sorted((root / PROTOCOLS_DIR).glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for phase in doc.get("phases") or []:
            protocol_union |= {str(item) for item in (phase.get("required_capabilities") or [])}
    return len(declared or []), len(provider_union), len(protocol_union)


def _phase_facts(root: Path) -> tuple[int, int, int, int]:
    doc = _yaml(root, MANUSCRIPT_PROTOCOL) or {}
    phases = doc.get("phases") if isinstance(doc, dict) else None
    if not isinstance(phases, list):
        return 0, 0, 0, 0
    session = [phase for phase in phases if phase.get("strategy") != "deterministic"]
    deterministic = [phase for phase in phases if phase.get("strategy") == "deterministic"]
    instances = 0
    for phase in session:
        for role in phase.get("required_roles") or []:
            instances += int(role.get("min_instances", 1))
    return len(phases), len(session), len(deterministic), instances


def _science_stack_terms(body: str) -> tuple[str, ...]:
    lowered = body.lower()
    return tuple(term for term in SCIENCE_STACK if term in lowered)


def _sandbox_facts(root: Path) -> tuple[str, tuple[str, ...]]:
    lines = [
        line for line in _text(root, SANDBOX_PATH).splitlines() if not line.strip().startswith("#")
    ]
    base = ""
    for line in lines:
        if line.strip().upper().startswith("FROM "):
            base = line.split()[1].split("@")[0]
            break
    return base, _science_stack_terms("\n".join(lines))


def _models_vision_keys(root: Path) -> int:
    doc = _yaml(root, MODELS_PATH)
    models = doc.get("models") if isinstance(doc, dict) else None
    if not isinstance(models, dict):
        return 0
    hits = 0
    for spec in models.values():
        capabilities = spec.get("capabilities") if isinstance(spec, dict) else None
        if isinstance(capabilities, dict) and "VISION" in capabilities:
            hits += 1
    return hits


def _full_text_terms(root: Path) -> tuple[str, ...]:
    directory = root / RETRIEVAL_DIR
    if not directory.is_dir():
        return ()
    body = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore") for path in directory.glob("*.py")
    ).lower()
    return tuple(label for label, pattern in FULL_TEXT_PATTERNS if re.search(pattern, body))


def _retrieval_facts(root: Path) -> tuple[str, ...]:
    return tuple(
        adapter
        for adapter in ("ncbi.py", "europe_pmc.py")
        if (root / RETRIEVAL_DIR / adapter).is_file()
    )


def _submission_facts(root: Path) -> tuple[str, ...]:
    text = _text(root, SUBMISSION_PATH)
    return tuple(piece for piece in SUBMISSION_PIECES if piece in text)


def _principal_facts(root: Path) -> bool:
    return "M18" in _text(root, PRINCIPAL_PATH)


def _mentions_hypothesis(path: Path) -> bool:
    if path.suffix not in (".py", ".ts", ".tsx"):
        return False
    return "HypothesisSet" in path.read_text(encoding="utf-8", errors="ignore")


def _code_hypothesis_files(root: Path) -> int:
    roots = ("packages", "services", "adapters", "apps/web/src")
    skip_dirs = {"__pycache__", "node_modules", ".venv", ".mypy_cache"}
    hits = 0
    for name in roots:
        base = root / name
        if not base.is_dir():
            continue
        for current, dirnames, filenames in os.walk(base, followlinks=False):
            dirnames[:] = [item for item in dirnames if item not in skip_dirs]
            hits += sum(_mentions_hypothesis(Path(current) / item) for item in filenames)
    return hits


def collect_facts(root: Path) -> Facts:
    """从 `root` 算一次全量读数（判词的唯一输入）。"""
    retmax = _module_literals(root, RETMAX_PATH)
    authored = _module_literals(root, AUTHORED_PATH)
    quality = _module_literals(root, QUALITY_PATH)
    thresholds, operators = _review_facts(root)
    openapi_paths, operations, methods, submission_hits = _openapi_facts(root)
    total, full, partial, gap = _console_facts(root)
    declared, provider, protocol = _capability_facts(root)
    phases, session, deterministic, instances = _phase_facts(root)
    base, stack = _sandbox_facts(root)
    not_judged = quality.get("NOT_JUDGED")
    return Facts(
        root=root,
        default_retmax=_int_literal(retmax, "DEFAULT_RETMAX"),
        max_retmax=_int_literal(retmax, "MAX_RETMAX"),
        authored_by_default=authored.get("AUTHORED_ALLOWED_BY_DEFAULT") is True,
        authored_profile=str(authored.get("AUTHORED_SAFETY_PROFILE") or ""),
        review_thresholds=thresholds,
        review_operators=operators,
        not_judged=tuple(str(item) for item in not_judged) if isinstance(not_judged, tuple) else (),
        models_vision_keys=_models_vision_keys(root),
        sandbox_base=base,
        sandbox_science_stack=stack,
        openapi_paths=openapi_paths,
        openapi_operations=operations,
        openapi_methods=methods,
        openapi_submission_hits=submission_hits,
        console_total=total,
        console_full=full,
        console_partial=partial,
        console_gap=gap,
        declared_capabilities=declared,
        provider_capabilities=provider,
        protocol_capabilities=protocol,
        phases_total=phases,
        phases_session=session,
        phases_deterministic=deterministic,
        session_role_instances=instances,
        full_text_terms=_full_text_terms(root),
        code_hypothesis_files=_code_hypothesis_files(root),
        submission_pieces=_submission_facts(root),
        principal_mentions_m18=_principal_facts(root),
        retrieval_adapters=_retrieval_facts(root),
    )
