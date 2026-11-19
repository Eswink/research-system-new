"""GOAL-116 EC-01 的**反证臂注册表**：每条断言都要能真红，并点名自己的条号。

**两类臂，改的是两侧**：

- `TextArm` —— 改**文档**（PRD 的数字 / 需求表的状态 / 引用路径、INDEX 登记、历史档案指针）；
- `TreeArm` —— 改**树**：把被改动的那几个文件复制进临时树、就地改写，再用同一批
  提取器重算**这一个方面**（其余读数沿用真实树）。因此红的原因是「树的事实变了、
  文档没跟上」，不是「临时树里缺文件」。

**覆盖纪律**：`EXPECTED_ARM_CLAIMS` 列出 EC-01 要求有断言的全部条号；判据
`test_every_required_claim_has_a_counter_arm` 断言注册表覆盖它 —— 新增一条断言却
忘记给它反证臂会判红。
"""

from __future__ import annotations

import dataclasses
import json
import shutil
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.tooling import prd_tree_facts as facts_module
from tests.tooling.prd_tree_facts import (
    AUTHORED_PATH,
    CAPABILITIES_PATH,
    CONSOLE_PATH,
    MANUSCRIPT_PROTOCOL,
    MODELS_PATH,
    OPENAPI_PATH,
    PRINCIPAL_PATH,
    PROTOCOLS_DIR,
    PROVIDERS_PATH,
    QUALITY_PATH,
    RETMAX_PATH,
    SANDBOX_PATH,
    SUBMISSION_PATH,
    Facts,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_PATH = "examples/contracts/task_contracts.yaml"
NCBI_PATH = "adapters/research_tools/ncbi.py"


@dataclass(frozen=True)
class TextArm:
    claim: str
    doc: str  # "prd" | "index" | 历史档案的仓库相对路径
    old: str
    new: str


@dataclass(frozen=True)
class TreeArm:
    claim: str
    name: str
    files: tuple[str, ...]
    mutate: Callable[[Path], None]
    merge: Callable[[Facts, Path], Facts]


def _edit(root: Path, relative: str, old: str, new: str, count: int = -1) -> None:
    path = root / relative
    text = path.read_text(encoding="utf-8")
    assert old in text, f"反证臂前置文本不在 {relative}: {old!r}"
    updated = text.replace(old, new) if count < 0 else text.replace(old, new, count)
    assert updated != text, f"反证臂没有改动 {relative}"
    path.write_text(updated, encoding="utf-8")


def _append(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")


def _rewrite_json(root: Path, update: Callable[[dict[str, object]], None]) -> None:
    path = root / OPENAPI_PATH
    document = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    update(document)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")


def _add_openapi_path(document: dict[str, object]) -> None:
    paths = document["paths"]
    assert isinstance(paths, dict)
    paths["/arm-probe"] = {"get": {"responses": {}}}


def _rename_openapi_path(document: dict[str, object]) -> None:
    paths = document["paths"]
    assert isinstance(paths, dict)
    paths["/submission-approvals"] = paths.pop("/approvals")


def _merge_capabilities(facts: Facts, tmp: Path) -> Facts:
    declared, provider, protocol = facts_module._capability_facts(tmp)
    return dataclasses.replace(
        facts,
        declared_capabilities=declared,
        provider_capabilities=provider,
        protocol_capabilities=protocol,
    )


def _merge_retmax(facts: Facts, tmp: Path) -> Facts:
    literals = facts_module._module_literals(tmp, RETMAX_PATH)
    return dataclasses.replace(
        facts,
        default_retmax=facts_module._int_literal(literals, "DEFAULT_RETMAX"),
        max_retmax=facts_module._int_literal(literals, "MAX_RETMAX"),
    )


def _merge_console(facts: Facts, tmp: Path) -> Facts:
    total, full, partial, gap = facts_module._console_facts(tmp)
    return dataclasses.replace(
        facts, console_total=total, console_full=full, console_partial=partial, console_gap=gap
    )


def _merge_openapi(facts: Facts, tmp: Path) -> Facts:
    paths, operations, methods, submission_hits = facts_module._openapi_facts(tmp)
    return dataclasses.replace(
        facts,
        openapi_paths=paths,
        openapi_operations=operations,
        openapi_methods=methods,
        openapi_submission_hits=submission_hits,
    )


def _merge_not_judged(facts: Facts, tmp: Path) -> Facts:
    literals = facts_module._module_literals(tmp, QUALITY_PATH)
    value = literals.get("NOT_JUDGED")
    items = tuple(str(item) for item in value) if isinstance(value, tuple) else ()
    return dataclasses.replace(facts, not_judged=items)


def _merge_sandbox(facts: Facts, tmp: Path) -> Facts:
    base, stack = facts_module._sandbox_facts(tmp)
    return dataclasses.replace(facts, sandbox_base=base, sandbox_science_stack=stack)


def _merge_full_text(facts: Facts, tmp: Path) -> Facts:
    return dataclasses.replace(facts, full_text_terms=facts_module._full_text_terms(tmp))


def _merge_vision(facts: Facts, tmp: Path) -> Facts:
    return dataclasses.replace(facts, models_vision_keys=facts_module._models_vision_keys(tmp))


def _merge_authored(facts: Facts, tmp: Path) -> Facts:
    literals = facts_module._module_literals(tmp, AUTHORED_PATH)
    return dataclasses.replace(
        facts,
        authored_by_default=literals.get("AUTHORED_ALLOWED_BY_DEFAULT") is True,
        authored_profile=str(literals.get("AUTHORED_SAFETY_PROFILE") or ""),
    )


def _merge_review(facts: Facts, tmp: Path) -> Facts:
    thresholds, operators = facts_module._review_facts(tmp)
    return dataclasses.replace(facts, review_thresholds=thresholds, review_operators=operators)


def _merge_phases(facts: Facts, tmp: Path) -> Facts:
    total, session, deterministic, instances = facts_module._phase_facts(tmp)
    return dataclasses.replace(
        facts,
        phases_total=total,
        phases_session=session,
        phases_deterministic=deterministic,
        session_role_instances=instances,
    )


def _merge_submission(facts: Facts, tmp: Path) -> Facts:
    return dataclasses.replace(facts, submission_pieces=facts_module._submission_facts(tmp))


def _merge_principal(facts: Facts, tmp: Path) -> Facts:
    return dataclasses.replace(facts, principal_mentions_m18=facts_module._principal_facts(tmp))


def _merge_retrieval(facts: Facts, tmp: Path) -> Facts:
    return dataclasses.replace(facts, retrieval_adapters=facts_module._retrieval_facts(tmp))


def _merge_hypothesis(facts: Facts, tmp: Path) -> Facts:
    return dataclasses.replace(
        facts, code_hypothesis_files=facts_module._code_hypothesis_files(tmp)
    )


def _append_capability(tmp: Path) -> None:
    _append(tmp, CAPABILITIES_PATH, "  - arm.fake-capability\n")


def _bump_retmax(tmp: Path) -> None:
    _edit(tmp, RETMAX_PATH, "DEFAULT_RETMAX = 3", "DEFAULT_RETMAX = 4")


def _flip_console_level(tmp: Path) -> None:
    _edit(tmp, CONSOLE_PATH, 'level: "partial"', 'level: "full"', count=1)


def _drop_not_judged(tmp: Path) -> None:
    _edit(tmp, QUALITY_PATH, '    "writing style, readability, grammar",\n', "")


def _install_numpy(tmp: Path) -> None:
    _append(tmp, SANDBOX_PATH, "RUN pip install --no-cache-dir numpy==2.1.0\n")


def _declare_full_text(tmp: Path) -> None:
    _append(tmp, NCBI_PATH, '\nFULL_TEXT_ENDPOINT = "rettype=full"\n')


def _declare_vision(tmp: Path) -> None:
    _edit(tmp, MODELS_PATH, "      CHAT:", "      VISION:", count=1)


def _open_authored(tmp: Path) -> None:
    _edit(
        tmp,
        AUTHORED_PATH,
        "AUTHORED_ALLOWED_BY_DEFAULT = False",
        "AUTHORED_ALLOWED_BY_DEFAULT = True",
    )


def _relax_review(tmp: Path) -> None:
    _edit(tmp, CONTRACTS_PATH, "threshold: 0.8", "threshold: 0.7", count=1)


def _make_a_session_phase_deterministic(tmp: Path) -> None:
    _edit(tmp, MANUSCRIPT_PROTOCOL, "strategy: single_agent", "strategy: deterministic", count=1)


def _drop_submission_piece(tmp: Path) -> None:
    _edit(tmp, SUBMISSION_PATH, "supplementary", "appendix")


def _promote_m18(tmp: Path) -> None:
    _edit(tmp, PRINCIPAL_PATH, "M18", "M19")


def _create_hypothesis_entity(tmp: Path) -> None:
    path = tmp / "packages" / "application" / "hypothesis_entities.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        'class HypothesisSet:\n    """反证臂：代码里出现了域实体。"""\n', encoding="utf-8"
    )


def _no_op(_: Path) -> None:
    """射程臂：不需要改文件 —— 临时树里**只放了 ncbi.py**，这本身就是「少一个适配器」。"""


TEXT_ARMS: tuple[TextArm, ...] = (
    TextArm("C-CONSOLE", "prd", "14 full / 18 partial / 1 gap", "15 full / 18 partial / 1 gap"),
    TextArm("C-OPENAPI", "prd", "109 paths / 134 operations", "108 paths / 133 operations"),
    TextArm("C-CAPS", "prd", "47 条声明", "46 条声明"),
    TextArm("C-PHASES", "prd", "11 相", "12 相"),
    TextArm("C-STR", "prd", "## 8. 声称边界", "## 8. 声称口径"),
    TextArm("C-STR", "prd", "| 部分 | 机制在", "| 进行中 | 机制在"),
    TextArm(
        "C-CITE",
        "prd",
        "`packages/application/run_orchestration/submission_assembly.py`",
        "`packages/application/run_orchestration/missing_assembly.py`",
    ),
    TextArm("C-INDEX", "index", "- `product/PRD.md`", "- （已撤下）"),
    TextArm("C-LEGACY", "docs/PRODUCT.md", "[`product/PRD.md`](product/PRD.md)", "（无）"),
    TextArm(
        "C-R05",
        "prd",
        "| 已实现 | `packages/application/run_orchestration/submission_assembly.py`",
        "| 未实现 | `packages/application/run_orchestration/submission_assembly.py`",
    ),
    TextArm("C-R07", "prd", "REVIEW_SCORE ≥ 0.8", "REVIEW_SCORE ≥ 0.7"),
    TextArm("C-R09", "prd", "无 PMC 正文", "已有 PMC 正文"),
    TextArm("C-R10", "prd", "DEFAULT_RETMAX=3", "DEFAULT_RETMAX=5"),
    TextArm(
        "C-R12", "prd", "AUTHORED_ALLOWED_BY_DEFAULT = False", "AUTHORED_ALLOWED_BY_DEFAULT = True"
    ),
    TextArm("C-R13", "prd", "无 numpy", "已含 numpy"),
    TextArm("C-R14", "prd", "HypothesisSet", "HypothesisBucket"),
    TextArm("C-R15", "prd", "零命中", "一处命中"),
    TextArm("C-R16", "prd", "M18 DEFERRED", "M18 PENDING"),
    TextArm("C-R19", "prd", "NOT_JUDGED", "UNJUDGED"),
    TextArm("C-R20", "prd", "零 `VISION` 声明", "零 `AUDIO` 声明"),
)

TREE_ARMS: tuple[TreeArm, ...] = (
    TreeArm(
        "C-CAPS",
        "extra-capability",
        (CAPABILITIES_PATH, PROVIDERS_PATH, PROTOCOLS_DIR),
        _append_capability,
        _merge_capabilities,
    ),
    TreeArm(
        "C-CONSOLE",
        "level-flip",
        (CONSOLE_PATH,),
        _flip_console_level,
        _merge_console,
    ),
    TreeArm(
        "C-OPENAPI",
        "extra-path",
        (OPENAPI_PATH,),
        lambda tmp: _rewrite_json(tmp, _add_openapi_path),
        _merge_openapi,
    ),
    TreeArm(
        "C-PHASES",
        "session-becomes-deterministic",
        (MANUSCRIPT_PROTOCOL,),
        _make_a_session_phase_deterministic,
        _merge_phases,
    ),
    TreeArm(
        "C-R05",
        "drop-submission-piece",
        (SUBMISSION_PATH,),
        _drop_submission_piece,
        _merge_submission,
    ),
    TreeArm("C-R07", "relax-threshold", (CONTRACTS_PATH,), _relax_review, _merge_review),
    TreeArm("C-R08", "missing-europe-pmc", (NCBI_PATH,), _no_op, _merge_retrieval),
    TreeArm("C-R09", "full-text-fetch", (NCBI_PATH,), _declare_full_text, _merge_full_text),
    TreeArm("C-R10", "retmax-bump", (RETMAX_PATH,), _bump_retmax, _merge_retmax),
    TreeArm("C-R12", "authored-open", (AUTHORED_PATH,), _open_authored, _merge_authored),
    TreeArm("C-R13", "numpy-installed", (SANDBOX_PATH,), _install_numpy, _merge_sandbox),
    TreeArm("C-R14", "hypothesis-entity", (), _create_hypothesis_entity, _merge_hypothesis),
    TreeArm(
        "C-R15",
        "submission-endpoint",
        (OPENAPI_PATH,),
        lambda tmp: _rewrite_json(tmp, _rename_openapi_path),
        _merge_openapi,
    ),
    TreeArm("C-R16", "m18-promoted", (PRINCIPAL_PATH,), _promote_m18, _merge_principal),
    TreeArm("C-R19", "not-judged-drops-one", (QUALITY_PATH,), _drop_not_judged, _merge_not_judged),
    TreeArm("C-R20", "vision-declared", (MODELS_PATH,), _declare_vision, _merge_vision),
)

#: EC-01 要求有断言的条号（缺一个 ⇒ 覆盖判据红）。
EXPECTED_ARM_CLAIMS: tuple[str, ...] = (
    "C-STR",
    "C-CITE",
    "C-INDEX",
    "C-LEGACY",
    "C-CONSOLE",
    "C-OPENAPI",
    "C-CAPS",
    "C-PHASES",
    "C-R05",
    "C-R07",
    "C-R08",
    "C-R09",
    "C-R10",
    "C-R12",
    "C-R13",
    "C-R14",
    "C-R15",
    "C-R16",
    "C-R19",
    "C-R20",
)


@contextmanager
def temporary_tree(files: tuple[str, ...]) -> Iterator[Path]:
    """临时树里只复制臂需要的那几个文件 / 目录（其余缺席，但不参与本臂的 merge）。"""
    with TemporaryDirectory() as name:
        tmp = Path(name)
        for relative in files:
            source = ROOT / relative
            destination = tmp / relative
            if source.is_dir():
                shutil.copytree(source, destination)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        yield tmp
