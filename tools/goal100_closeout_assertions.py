"""GOAL-20261029-100 收口复检的**特有断言**（与 `verify_goal100_closeout.py` 配对）。

**为什么单列**：收口验证器与工具集之间有 450 行硬上限（规模门），而断言又要逐条可读 ——
与 `goal099_closeout_assertions.py` 同一手法：验证器只写「记录面」，产品面收在这里。

**本 GOAL 的四块产品面**（每条都是「按掉实现就判红」的可观测后果）：

1. **引用编号注入**（EC-01）：渲染器**调**唯一编号权威 `numbered_records`；
   标题逐字说「by number」；`[n]` 前缀的构造点在树。
2. **投稿决策面**（EC-02）：`EditorialDecision` 四值在域里；`editorial` 相在协议里且
   `scientific_editor` 被点名；决定块的解析器在树。
3. **返修底座**（EC-03）：`author_response` 契约 + `revision` 相 + 应答信装配在树；
   点表**唯一**派生点（提示词与汇编共用同一函数）。
4. **`retmax` 可配**（EC-04）：缺省常量是 3、配置面是具名变量、非法值点名。

**不 import 产品常量当预言机**：这里断言的是**名字与句子在位**（产品面**存在**），
行为面由各自的判据文件负责（本文件只证明「那些判据的对象在树」）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

RENDERER = "packages/application/run_orchestration/retrieval_prompt.py"
REFERENCES = "packages/application/deliverable/references.py"
ENUMS = "packages/domain/enums.py"
EDITORIAL = "packages/application/deliverable/editorial_decision.py"
AUTHOR_RESPONSE = "packages/application/deliverable/author_response.py"
REVIEW_POINTS = "packages/application/run_orchestration/review_points.py"
MANUSCRIPT_PROTOCOL = "examples/protocols/direction_to_manuscript_v1.yaml"
CONTRACTS = "examples/contracts/task_contracts.yaml"
WIRING = "services/api/retrieval_wiring.py"
AGENTS = "examples/config/agents.yaml"
MODELS = "examples/config/models.yaml"
TEAM = "examples/config/team_templates.yaml"
ASSEMBLY = "packages/application/run_orchestration/manuscript_assembly.py"

#: EC-01 的判据文件（三向：正向 + 两条反证）。
CITATION_CASES = "tests/application/test_citation_numbers_reach_the_prompt.py"
#: EC-02 / EC-03 / EC-04 的判据文件。
EDITORIAL_CASES = "tests/application/test_editorial_decision.py"
RESPONSE_CASES = "tests/application/test_author_response.py"
RETMAX_CASES = "tests/api/test_retmax_is_configurable.py"
#: EC-02 / EC-03 的**产品入口**判据（同一份 e2e 文件里各有用例）。
PRODUCT_CASES = "tests/e2e/test_direction_to_manuscript_product_path.py"

#: 受判文件与它们的**最小判据条数**（`def test_` 条数下界；只增不减）。
#:
#: 口径是**函数定义数**（不是收集数）：参数化用例一个 `def test_` 展开成多条收集项，
#: 而这里要钉的是「这个文件里有多少条独立判据」。下界取交付时的实际条数 —— 削掉任何
#: 一条都会红，加用例不会红。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    (CITATION_CASES, 8),
    (EDITORIAL_CASES, 19),
    (RESPONSE_CASES, 26),
    (RETMAX_CASES, 11),
    (PRODUCT_CASES, 9),
)


def _case_count(text: str) -> int:
    """文件的 `def test_` 条数（与既有收口断言同一口径）。"""
    return sum(1 for line in text.splitlines() if line.strip().startswith("def test_"))


def _present(text: str, needles: tuple[str, ...]) -> tuple[bool, str]:
    """逐条都在 ⇒ `(True, "")`；否则 `(False, 缺的那些)`。"""
    missing = [needle for needle in needles if needle not in text]
    return not missing, ",".join(missing)


def citation_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：编号**注入**提示词，且编号权威只有一处。"""
    renderer = toolbox.text(root, RENDERER)
    references = toolbox.text(root, REFERENCES)
    ok_renderer, missing_renderer = _present(
        renderer,
        (
            # 渲染器**调**共享编号权威（不是自己数）。
            "from packages.application.deliverable.references import numbered_records",
            "numbered_records(",
            # 每一行以编号开头（前缀的构造点在树）。
            'prefix = f"[{numbers[identifier]}] " if identifier in numbers',
            # 标题逐字：按**编号**引用（模型不再自己数）。
            'PROMPT_SECTION_TITLE = "RETRIEVED SOURCES (system-fetched; cite these by number)"',
            # 不可引用的条目不占编号（否则其后整体错位）。
            'NOT_CITABLE_MARK = "[not citable]"',
        ),
    )
    ok_references, missing_references = _present(
        references,
        ("def numbered_records(", "去重后首次出现顺序"),
    )
    return [
        toolbox.verdict("citation-injection-in-tree", ok_renderer, missing_renderer),
        toolbox.verdict("citation-numbering-authority-in-tree", ok_references, missing_references),
        toolbox.verdict(
            "citation-title-says-by-number",
            "cite these by number" in renderer,
            "标题必须逐字说「按编号引用」—— 编号现在随行给到模型",
        ),
    ]


#: EC-02 的「必须逐字在位」清单（逐组一个判词，便于读数）。
_EDITORIAL_NEEDLES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "editorial-values-in-domain",
        ENUMS,
        (
            "class EditorialDecision(StrEnum):",
            'ACCEPT = "accept"',
            'MINOR_REVISION = "minor_revision"',
            'MAJOR_REVISION = "major_revision"',
            'REJECT = "reject"',
            # 越界值点名拒绝的机械面（`parse` 是判据的靶子）。
            "def parse(cls, raw: object)",
        ),
    ),
    (
        "editorial-phase-is-activated",
        MANUSCRIPT_PROTOCOL,
        (
            "  - id: editorial\n",
            "{role: scientific_editor,",
            "task_contract: editorial_decision",
            "outputs: [editorial_decision]",
        ),
    ),
    (
        "editorial-parser-in-tree",
        EDITORIAL,
        (
            "class EditorialDecisionError(RuntimeError):",
            "def parse_editorial_decision(",
            "requires changes but required_changes is",
        ),
    ),
    (
        "editor-agent-is-bound",
        AGENTS,
        ("role: scientific_editor",),
    ),
    (
        "editor-model-is-declared",
        MODELS,
        ("scientific_editor_model:",),
    ),
    (
        "editor-role-is-in-the-standard-pool",
        TEAM,
        ("scientific_editor:",),
    ),
)


def _needle_verdicts(root: Path, toolbox: Any, spec: Any) -> list[Any]:
    """`(名字, 文件, 必须逐字在位的句子)` 序列 → 逐组判词（单列守 50 行门）。"""
    verdicts: list[Any] = []
    for name, relative, needles in spec:
        ok, missing = _present(toolbox.text(root, relative), needles)
        verdicts.append(toolbox.verdict(name, ok, missing))
    return verdicts


def editorial_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：决定词表进域 + 相被激活 + 解析器 + agent / 模型 / 角色池在位。"""
    return _needle_verdicts(root, toolbox, _EDITORIAL_NEEDLES)


#: EC-03 的「必须逐字在位」清单（逐组一个判词）。
_RESPONSE_NEEDLES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "response-points-and-letter-in-tree",
        AUTHOR_RESPONSE,
        (
            "def points_of(",
            "class ReviewPoint:",
            "class AuthorResponse:",
            "def validate_responses(",
            "def response_letter(",
            "def remarks_of(",
            'RESPONSE_LETTER_NAME = "response_letter.md"',
            'WEAKEST_LINK_FIELD = "weakest_link"',
        ),
    ),
    (
        "revision-phase-is-activated",
        MANUSCRIPT_PROTOCOL,
        (
            "  - id: revision\n",
            "task_contract: author_response",
            "outputs: [author_responses]",
        ),
    ),
    (
        "response-contract-in-tree",
        CONTRACTS,
        ("  author_response:\n", "artifact: author_responses"),
    ),
    (
        "review-points-assembly-in-tree",
        REVIEW_POINTS,
        ("def review_points_of_run(", "def wants_review_points("),
    ),
    (
        "response-letter-assembly-in-tree",
        ASSEMBLY,
        (
            "def maybe_assemble_response_letter(",
            # **唯一**派生点：汇编器调的是提示词那一侧同一个函数。
            "review_points_of_run(artifacts, ledger, run_id)",
            "def _register_response_letter(",
        ),
    ),
)


def response_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：点表 + 应答契约 + 应答信装配都在树，且点表**只有一个**派生点。"""
    verdicts = _needle_verdicts(root, toolbox, _RESPONSE_NEEDLES)
    assembly = toolbox.text(root, ASSEMBLY)
    points = toolbox.text(root, REVIEW_POINTS)
    verdicts.append(
        toolbox.verdict(
            "review-points-have-one-derivation",
            assembly.count("review_points_of_run(") >= 1
            and points.count("def review_points_of_run(") == 1,
            "点表必须只有一处派生（提示词与应答信用同一个函数）",
        )
    )
    return verdicts


def retmax_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：`retmax` 可配而默认不变。"""
    wiring = toolbox.text(root, WIRING)
    ok, missing = _present(
        wiring,
        (
            "DEFAULT_RETMAX = 3",
            'RETMAX_ENV = "RESEARCHOS_RETMAX"',
            "def configured_retmax(",
            "def retrieval_calls(retmax: int | None = None)",
            'fixed_arguments={"retmax": hits}',
        ),
    )
    return [
        toolbox.verdict("retmax-is-configurable-with-default-3", ok, missing),
    ]


def case_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """判据文件在位，且条数不低于下界（只增不减）。"""
    verdicts: list[Any] = []
    for relative, floor in CASE_FLOORS:
        text = toolbox.text(root, relative)
        count = _case_count(text)
        verdicts.append(
            toolbox.verdict(
                f"cases-{Path(relative).stem}",
                count >= floor,
                f"{relative} 的判据用例数 {count} 低于下界 {floor}",
            )
        )
    return verdicts


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 的**全部**特有断言（验证器只调这一个入口）。"""
    return [
        *citation_verdicts(root, toolbox),
        *editorial_verdicts(root, toolbox),
        *response_verdicts(root, toolbox),
        *retmax_verdicts(root, toolbox),
        *case_verdicts(root, toolbox),
    ]
