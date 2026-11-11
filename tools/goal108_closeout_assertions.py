"""GOAL-20261111-108 的**产品面断言集**（收口验证器的另一半）。

与 `tools/verify_goal108_closeout.py`（记录面）分工：本文件判**交付物真的在、且形态就是
声明的那一个**；主文件判 EC 终态与宪章记账。

**本轮的判法**（每条都指向具体字节或具体闭集，不判「模块存在」）：

* 换站（EC-02）：`llm_endpoints.yaml` 的 `main` 指向局域网地址、超时提到 300、
  `allow_models` 恰是四个免费模型 —— 且**不是**靠改判据换来的绿。
* 分工（EC-03）：五个 `model_name` 的**写作组 ∩ 评审组 = ∅**（这是关键的那一面）；
  被用户拍板放宽的那一面（创新点评审 = 评审 A）由判据**逐字枚举**，不是静默。
* 可靠性（EC-04…07）：四件的**实现面**在（guard / `NO_PROGRAM` / 三个重试字段 /
  同一开关读取口），而不是只有文档说「修了」。
* 文档（EC-09）：两页文档**真的写了**站点、开关名、租约陷阱。
* 探针（EC-01）：台账里的构建者判据文件**在树**（此前只写在 `verify:` 字段里）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

#: 换站与分工的声明面（唯一来源，不是散落在注释里）。
ENDPOINTS = "examples/config/llm_endpoints.yaml"
MODELS = "examples/config/models.yaml"
CONTRACTS = "examples/contracts/task_contracts.yaml"

#: 四个免费模型（`credits: x0.00` 且实测支持 `tool_calls`）。
FREE_MODELS: tuple[str, ...] = ("hy4free", "hy4-preview-f", "hy4flash-exp4", "hy3")

#: 局域网站点（**私有 IP**；放行靠环境开关，不改产品默认）。
LAN_HOST = "192.168.101.9:8798"

#: `R-1`…`R-4` 四件的实现面（缺一件 = 那条 EC 没交付）。
RELIABILITY_FILES: tuple[tuple[str, str], ...] = (
    ("R-1", "packages/application/run_orchestration/spec_assembly_guard.py"),
    ("R-2", "packages/application/run_orchestration/review_outcome.py"),
    ("R-4", "tests/e2e/manuscript_chain_live_support.py"),
)

#: 四件各自的行为判据（在树且是真的判据，不是空壳）。
RELIABILITY_JUDGES: tuple[str, ...] = (
    "tests/application/test_spec_assembly_guard.py",
    "tests/application/test_review_outcome_no_program.py",
    "tests/application/test_session_contract_retries.py",
    "tests/tooling/test_goal108_live_harness_reads_the_switch.py",
    "tests/tooling/test_goal108_probe_readings.py",
)

#: 五份会话合约（`R-3` 的受判面）。
SESSION_CONTRACTS: tuple[str, ...] = (
    "research_manuscript",
    "retrieval_report_from_the_run_chain",
    "multi_role_review",
    "author_response",
    "submission_package",
)

#: `R-3` 的类别字段（显式列出，不靠空表的通配语义）。
RETRY_FIELDS: tuple[str, ...] = (
    "max_attempts: 2",
    "backoff_seconds: 30",
    "MODEL_RELAY_UNAVAILABLE",
    "MODEL_RATE_LIMIT",
    "MODEL_TIMEOUT",
)

#: 两页文档（EC-09）与各自必须写到的三件事。
DOCS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "docs/integration/LLM_ENDPOINTS.md",
        (LAN_HOST, "RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS", "private", "300"),
    ),
    (
        "docs/integration/LIVE_MODEL_RUNBOOK.md",
        (LAN_HOST, "RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS", "workflow_lease_ttl_seconds", "3600"),
    ),
)

#: 真实 run 的读数文件（EC-08：成功或失败都算达成，但**必须有读数**）。
LIVE_EVIDENCE: tuple[str, ...] = (".cursor/plans/goals/evidence/GOAL-20261111-108-live-run2.json",)

#: 收口资产（EC-11 自指）。
VERIFIER = "tools/verify_goal108_closeout.py"
ASSERTIONS = "tools/goal108_closeout_assertions.py"


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _file_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """交付面在位（缺一件 = 该 EC 没交付）。"""
    verdicts: list[Any] = []
    for relative in (
        ENDPOINTS,
        MODELS,
        CONTRACTS,
        *(path for _label, path in RELIABILITY_FILES),
        *RELIABILITY_JUDGES,
        *(path for path, _sub in DOCS),
        *LIVE_EVIDENCE,
        VERIFIER,
        ASSERTIONS,
    ):
        verdicts.append(
            toolbox.verdict(
                f"delivered-{Path(relative).name}",
                (root / relative).is_file(),
                f"{relative} 不在树",
            )
        )
    return verdicts


def _station_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：`main` 指向局域网、超时 300、`allow_models` 恰是四个免费模型。"""
    text = _text(root, ENDPOINTS)
    main_block = text.split("  agnes-anthropic:", 1)[0]
    listed = [model for model in FREE_MODELS if f"- {model}" in main_block]
    return [
        toolbox.verdict(
            "station-points-at-the-lan-relay",
            LAN_HOST in main_block,
            "`main.base_url` 必须指向局域网中转站",
        ),
        toolbox.verdict(
            "station-timeout-is-raised",
            "request_timeout_seconds: 300" in main_block,
            "`main.request_timeout_seconds` 必须是 300（依据实测延迟分布）",
        ),
        toolbox.verdict(
            "station-allow-models-are-the-four-free-ones",
            len(listed) == len(FREE_MODELS),
            f"`main.discovery.allow_models` 必须恰是四个免费模型，实得 {listed}",
        ),
        toolbox.verdict(
            "station-does-not-allowlist-a-paid-model",
            "hy4std" not in main_block and "hy3-x" not in main_block,
            "`allow_models` 不得列入收费模型（hy4std / hy3-x）",
        ),
    ]


def _model_split(text: str) -> dict[str, tuple[str, ...]]:
    """按 `model_name:` 行抽出每个模型块的模型名（块边界 = 下一个**同缩进**的键）。

    **缩进是 `models:` 下的一段**：每个模型块是 2 空格缩进的 `name:`，字段是 4 空格。
    按「列 0 才算块」切会把整份文件当成一块（本文件第一版正是这样，三条断言全空）。
    只读**声明行**，不读注释 —— 注释里写旧名字不会让判据变绿。
    """
    split: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 2 and line.rstrip().endswith(":"):
            current = line.strip().rstrip(":")
            split.setdefault(current, [])
            continue
        stripped = line.strip()
        if current and stripped.startswith("model_name:"):
            value = stripped.split(":", 1)[1].split("#", 1)[0].strip()
            split[current].append(value)
    return {key: tuple(values) for key, values in split.items()}


def _resolved_targets(root: Path) -> dict[str, set[tuple[str, str]]]:
    """五个受判 agent 的**解析目标**（用产品自己的解析器，不手写 YAML 解析）。

    判据要判的是「**生产实际会解析到的**目标」，而不是「文件里某个字符串长什么样」。
    手写解析还有一个具体陷阱：`model_name:` 是 4 空格缩进的字段，按列 0 切块会把整份
    文件当成一块（本文件第一版正是这样，三条断言全空但都「绿」）。

    `root` 必须在 `sys.path` 上才 import 得到产品包（验证器是从 `tools/` 起的进程）。
    """
    import sys

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from adapters.contracts.models_loaders import load_model_profiles, load_models
    from adapters.contracts.roles_loaders import load_agents
    from packages.application.ports.resource_catalog import CatalogSnapshot
    from packages.application.preflight.review_independence import resolve_agent_targets

    snapshot = CatalogSnapshot(
        models=load_models(str(root / MODELS)),
        model_profiles=load_model_profiles(str(root / "examples/config/model_profiles.yaml")),
        agents=load_agents(str(root / "examples/config/agents.yaml")),
        roles={},
    )
    return {
        agent_id: set(resolve_agent_targets(agent_id, snapshot.agents[agent_id], snapshot).targets)
        for agent_id in ("writer", "reviewer_a", "reviewer_b", "novelty_a", "novelty_writer")
    }


def _split_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：写作组 ∩ 评审组 = ∅；被放宽的那一面逐字可枚举。"""
    targets = _resolved_targets(root)
    writer = targets["writer"]
    reviewer_a = targets["reviewer_a"]
    reviewer_b = targets["reviewer_b"]
    novelty_a = targets["novelty_a"]
    novelty_writer = targets["novelty_writer"]
    return [
        toolbox.verdict(
            "writer-and-reviewer-targets-are-disjoint",
            bool(writer)
            and bool(reviewer_a)
            and bool(reviewer_b)
            and not (writer & reviewer_a)
            and not (writer & reviewer_b),
            "写作组与两位评审者的解析目标必须不交："
            f"writer={sorted(writer)} reviewer_a={sorted(reviewer_a)} "
            f"reviewer_b={sorted(reviewer_b)}",
        ),
        toolbox.verdict(
            "the-two-reviewers-are-distinct",
            bool(reviewer_a) and bool(reviewer_b) and not (reviewer_a & reviewer_b),
            f"两位评审者必须互不相同：a={sorted(reviewer_a)} b={sorted(reviewer_b)}",
        ),
        toolbox.verdict(
            "novelty-reviewer-shares-reviewer-a",
            bool(novelty_a) and novelty_a == reviewer_a,
            "被拍板放宽的那一面必须**就是**这一面（创新点评审 = 评审 A）："
            f"novelty_a={sorted(novelty_a)} reviewer_a={sorted(reviewer_a)}",
        ),
        toolbox.verdict(
            "novelty-author-is-outside-both-sides",
            bool(novelty_writer)
            and not (novelty_writer & writer)
            and not (novelty_writer & reviewer_a)
            and not (novelty_writer & reviewer_b),
            f"创新点作者必须独立于写作组与两位评审者：novelty_writer={sorted(novelty_writer)}",
        ),
    ]


def _retry_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-06（`R-3`）：五份会话合约各自带三个重试字段。"""
    lines = _text(root, CONTRACTS).splitlines()
    verdicts: list[Any] = []
    for name in SESSION_CONTRACTS:
        marker = f"  {name}:"
        index = next((i for i, line in enumerate(lines) if line == marker), None)
        if index is None:
            verdicts.append(toolbox.verdict(f"retry-contract-{name}", False, f"合约 {name} 不在树"))
            continue
        end = next(
            (
                i
                for i, line in enumerate(lines[index + 1 :], start=index + 1)
                if line and not line.startswith((" ", "#"))
            ),
            len(lines),
        )
        block = "\n".join(lines[index:end])
        missing = [field for field in RETRY_FIELDS if field not in block]
        verdicts.append(
            toolbox.verdict(
                f"retry-contract-{name}",
                not missing,
                f"{name} 缺重试字段：{missing}",
            )
        )
    return verdicts


def _doc_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-09：两页文档写到站点、开关名与各自的陷阱。"""
    verdicts: list[Any] = []
    for relative, facts in DOCS:
        text = _text(root, relative)
        missing = [fact for fact in facts if fact not in text]
        verdicts.append(
            toolbox.verdict(
                f"docs-{Path(relative).stem.lower()}",
                not missing,
                f"{relative} 缺：{missing}",
            )
        )
    endpoints = _text(root, "docs/integration/LLM_ENDPOINTS.md")
    verdicts.append(
        toolbox.verdict(
            "docs-name-the-misleading-switch",
            "名字" in endpoints and "RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS" in endpoints,
            "端点文档必须写出开关名字的误导（名字写 localhost，实际覆盖 private）",
        )
    )
    return verdicts


def _reliability_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04 / EC-05 / EC-07：三件的实现面真的读得出来。"""
    guard = _text(root, "packages/application/run_orchestration/spec_assembly_guard.py")
    outcome = _text(root, "packages/application/run_orchestration/review_outcome.py")
    harness = _text(root, "tests/e2e/manuscript_chain_live_support.py")
    return [
        toolbox.verdict(
            "r1-assembly-guard-is-wired",
            "def guarded_assembly" in guard and "def fail_on_assembly_error" in guard,
            "R-1：`spec_assembly_guard.py` 必须有 guarded_assembly / fail_on_assembly_error",
        ),
        toolbox.verdict(
            "r2-no-program-is-a-named-empty-view",
            "NO_PROGRAM" in outcome,
            "R-2：非程序 run 必须返回点名的 NO_PROGRAM 视图，不是抛错",
        ),
        toolbox.verdict(
            "r2-non-program-does-not-raise",
            "raise ValueError" not in outcome.split("NO_PROGRAM", 1)[0],
            "R-2：NO_PROGRAM 分支前不得再对非程序 run 抛 ValueError",
        ),
        toolbox.verdict(
            "r4-harness-reads-the-product-switch",
            "def _allow_local_endpoints()" in harness,
            "R-4：live harness 必须读产品同一个放行开关",
        ),
        toolbox.verdict(
            "r4-no-hardcoded-allow-flag",
            "allow_localhost_endpoints=False" not in harness,
            "R-4：不得写死 `allow_localhost_endpoints=False`",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 的产品面全量断言（验证器按路径加载并调用它）。"""
    return [
        *_file_verdicts(root, toolbox),
        *_station_verdicts(root, toolbox),
        *_split_verdicts(root, toolbox),
        *_retry_verdicts(root, toolbox),
        *_reliability_verdicts(root, toolbox),
        *_doc_verdicts(root, toolbox),
    ]
