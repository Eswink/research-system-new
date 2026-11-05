"""GOAL-20261104-106 live 判据的**装配与取数**支持件（十一相位手稿链）。

**为什么单列**：判据文件贴着 450 行硬上限（规模门），而「产品组合根 + 门 + 四个读面的取数 +
两个读数解析器」是可独立读的一段装配 —— 与 `direction_to_manuscript_support` /
`direction_to_report_support` 同一手法。本模块**不含用例**。

**它守的纪律**（与判据文件的 docstring 同一套，逐条对应）：

1. **`assemble()` 之后不补任何缝** —— 本模块里没有 `deps.tool_providers = ...`、
   没有 `replace(deps.runs._deps, ...)`、没有 `_attach_*`（收口验证器的
   `live-judge-patches-no-seam` 按 **AST** 判这件事，两向按压留证）。
2. **读数先写盘再断言** —— `write_readings()` 是唯一的落盘口，判据在它之后才 assert。
3. **取数只用产品自己的读面** —— 相归属读 `RunDetailDto.phases`（**不**从制品 id 的段猜，
   那个形状里没有相）；内容读 `GET /artifacts/{id}/content`。
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

#: 本轮的取证文件（读数逐条落盘；**失败路径也写**）。
EVIDENCE = Path(".cursor/plans/goals/evidence/GOAL-20261104-106-manuscript-chain-live.json")
#: 十一相协议。
PROTOCOL = "direction_to_manuscript_v1.yaml"
PROTOCOL_ID = "direction_to_manuscript_v1_0_0"
#: 方向（与 mock e2e / 既有 live 判据同一个：检索词由模型自己从它提出）。
DIRECTION = "retrieval augmentation for scientific hypothesis generation"

#: 十一相（与 `direction_to_manuscript_support.PHASES` 逐字一致；本模块不 import 那个模块
#: —— 它拖进 mock 中转站与离线 Europe PMC，live 判据不该把它们带进来）。
PHASES: tuple[str, ...] = (
    "question",
    "retrieval",
    "novelty",
    "plan",
    "experiment",
    "review",
    "manuscript",
    "editorial",
    "revision",
    "submission",
    "report",
)

#: 本 run 应当落库的产物（九个会话产物 + 报告/手稿 + 投稿五件 + 改稿两件）。
OUTPUT_NAMES: tuple[str, ...] = (
    "research_question",
    "retrieval_report",
    "novelty_claim",
    "research_plan",
    "review_decision",
    "manuscript_narrative",
    "editorial_decision",
    "author_responses",
    "submission_package",
    "research_report.md",
    "manuscript.md",
    "cover_letter.md",
    "author_contributions.md",
    "conflicts_of_interest.md",
    "data_availability.md",
    "supplementary.md",
    "manuscript_v2.md",
    "response_letter.md",
)

#: 脚注里那三条读数的**形状**（`manuscript._citation_readings_line` 的固定格式；判据按它取数）。
READINGS_LINE = re.compile(
    r"- \*\*Citation distribution \(readings, not a judgement\)\*\*: "
    r"(\d+) sentence\(s\) scored / (\d+) mark\(s\) / (\d+) cited reference\(s\) / "
    r"single-support section\(s\): ([^.\n]+)\."
)

#: 节标题（汇编器写的就是这些字面量；与 `MANUSCRIPT_KEYS` 的八个键一一对应）。
SECTION_HEADINGS: dict[str, str] = {
    "abstract": "## Abstract",
    "introduction": "## 1. Introduction",
    "related_work": "## 2. Related Work",
    "methods": "## 3. Methods",
    "results": "## 4. Results",
    "discussion": "## 5. Discussion",
    "conclusion": "## 6. Conclusion",
}


def unique() -> str:
    """一次性的幂等键（同进程内多次起 run 不互相顶掉）。"""
    import uuid

    return uuid.uuid4().hex[:12]


def write_readings(readings: dict[str, Any]) -> None:
    """读数落盘（**先写再断言**；失败路径同样有读数）。"""
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(
        json.dumps(readings, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def live_gate() -> Any:
    """live run 门（runtime 显式 openhands + 凭据可解析 + live 开关；缺一如实 skip）。"""
    from adapters.contracts.models_loaders import load_llm_endpoints
    from adapters.relay.credential_resolver import EnvCredentialResolver
    from packages.application.model_relay.live_run_gate import evaluate_live_run_gate
    from services.api.runtime_support import OPENHANDS_RUNTIME
    from tests.e2e.live_switch_support import live_e2e_switch_enabled

    endpoints = load_llm_endpoints("examples/config/llm_endpoints.yaml")
    return evaluate_live_run_gate(
        credentials=EnvCredentialResolver(),
        endpoint=endpoints["main"],
        agent_runtime=os.environ.get("RESEARCHOS_AGENT_RUNTIME", ""),
        live_agent_runtime=OPENHANDS_RUNTIME,
        live_switch=live_e2e_switch_enabled(),
    )


def assembled_product() -> Any:
    """**产品组合根**（`assemble()`）；不补任何缝（补了就与 GOAL-097 的口径分叉）。"""
    from services.api.composition import assemble
    from services.api.runtime_support import OPENHANDS_RUNTIME
    from services.api.settings import ApiSettings

    deps = assemble(
        ApiSettings(
            # 每次一个全新的库（pid 会复用 ⇒ 按 pid 命名会让上一次的 lease 残留进来）。
            db_path=f"data/goal106-live-{os.getpid()}-{unique()}.db",
            agent_runtime=OPENHANDS_RUNTIME,
            allow_localhost_endpoints=False,
            # 真实会话要能建工作区（§9 的 host shell 默认 deny 不变：显式开发开关）。
            workspace_allow_host_shell=True,
            # 实验设计来自**本 run 的计划产物**（GOAL-080 的机制，装配面声明）。
            experiment_design_source="plan",
            # 租约 TTL：同步执行路径只在会话**开始前**心跳一次，而真实会话常超 300 秒
            # ⇒ 租约过期 ⇒ `no matching lease for task`（GOAL-097 实测反复出现）。
            workflow_lease_ttl_seconds=3600,
        )
    )
    register_credential(deps)
    return deps


def register_credential(deps: Any) -> None:
    """把部署凭据注册进**产品根自己那个**解析器（值只从环境来，不读、不回显、不落盘）。"""
    value = os.environ.get("LLM_MAIN_KEY")
    if not value:
        return
    register = getattr(deps.credentials, "register", None)
    if callable(register):
        register("LLM_MAIN_KEY", value)


def preflight_override(deps: Any) -> Any:
    """显式运维上下文：目录 + provider 健康（既有路径，非缝）。

    为什么需要：出厂探测面对 REST provider 诚实 `UNKNOWN` ⇒ `TOOL_HEALTH_UNPROVEN`
    是 WARNING 且**没有接受通道** ⇒ `freeze_manifest` 拒冻
    （`examples/protocols/real_retrieval_research_v1.yaml:11-19` 已登记这条既有缺口）。
    本判据不改门禁，走**显式声明**这条既有路径。
    """
    from packages.application.ports.resource_catalog import PreflightContext
    from packages.domain.enums import EndpointHealth
    from services.api.catalog_merge import merged_catalog_snapshot, merged_project_settings

    catalog = merged_catalog_snapshot(deps)
    project = merged_project_settings(deps, "example-project")
    return PreflightContext(
        catalog=catalog,
        project=project,
        # 凭据解析面必须与产品根**同一个实例**（`CREDENTIAL_MISSING` 就是漏了它）。
        credentials=deps.credentials,
        policy_evaluator=deps.policy_evaluator,
        endpoint_health={endpoint_id: EndpointHealth.HEALTHY for endpoint_id in catalog.endpoints},
        provider_health={
            provider_id: EndpointHealth.HEALTHY for provider_id in catalog.tool_providers
        },
    )


def artifact_ids(client: Any, run_id: str) -> list[str]:
    payload = client.get(f"/runs/{run_id}/artifacts").json()
    rows = payload.get("items") if isinstance(payload, dict) else payload
    return [str(row.get("id")) for row in rows or [] if isinstance(row, dict)]


def content_of(client: Any, ids: list[str], name: str) -> str | None:
    """按产物名后缀取**内容字节**（读面不在场 ⇒ `None`，不猜）。"""
    for artifact_id in ids:
        if not artifact_id.endswith(f":{name}"):
            continue
        response = client.get(f"/artifacts/{artifact_id}/content")
        if response.status_code != 200:
            continue
        return str(response.content.decode("utf-8", errors="replace"))
    return None


def failure_events(client: Any, run_id: str) -> list[str]:
    """失败/拒收事件的 payload.message（CI 上的失败不需要第二趟复跑就能定位）。"""
    try:
        rows = client.get(f"/runs/{run_id}/events").json()
    except Exception:  # noqa: BLE001 - 取证失败不得掩盖判据本身
        return []
    items = rows.get("items") if isinstance(rows, dict) else rows
    out: list[str] = []
    for row in items or []:
        if not isinstance(row, dict):
            continue
        kind = str(row.get("event_type") or row.get("type") or "")
        if not kind.endswith(("failed", "rejected", "cancelled")):
            continue
        payload = row.get("payload") or {}
        message = payload.get("message") if isinstance(payload, dict) else payload
        out.append(f"{kind}: {message}")
    return out[-12:]


def phase_progress(client: Any, run_id: str) -> list[dict[str, Any]]:
    """相级进度的**唯一读面**（`RunDetailDto.phases`，GOAL-20261101-103 EC-01）。

    为什么不用制品 id 的段去猜相：真实形状是 `{task_id}:{name}`（**没有**相那一段）⇒
    按段解析只能得到 `None`（本轮实测）。相→制品的归属由产品自己给出，本判据读它。
    """
    run = client.get(f"/runs/{run_id}").json()
    rows = run.get("phases") if isinstance(run, dict) else None
    return [row for row in rows or [] if isinstance(row, dict)]


def drive_one_run(client: Any) -> dict[str, Any]:
    """声明方向 → 起 run → 读四个读面 → **先写盘**再返回读数（失败路径同样有读数）。"""
    declared = client.put(
        "/projects/example-project/direction",
        json={"direction": DIRECTION},
        headers={"Idempotency-Key": f"goal106-direction-{unique()}"},
    )
    readings: dict[str, Any] = {
        "protocol": PROTOCOL_ID,
        "direction": DIRECTION,
        "direction_status": declared.status_code,
        "interface": "assemble() product root, no seams patched",
    }
    started = client.post(
        "/projects/example-project/runs",
        json={"protocol_path": PROTOCOL},
        headers={"Idempotency-Key": f"goal106-run-{unique()}"},
    )
    readings["http_status"] = started.status_code
    readings["http_body"] = started.text[:1200]
    payload = started.json() if started.status_code == 200 else {}
    run_id = str(payload.get("id") or "")
    readings["run_id"] = run_id
    readings["state"] = payload.get("state")
    if run_id:
        collect_readings(client, run_id, readings)
    write_readings(readings)
    return readings


def collect_readings(client: Any, run_id: str, readings: dict[str, Any]) -> None:
    """读面读数：制品 id / 各产物字节 / 相级进度 / 实验行 / 失败原因。"""
    ids = artifact_ids(client, run_id)
    readings["artifact_ids"] = ids
    suffixes = {item.rsplit(":", 1)[-1] for item in ids}
    readings["missing_artifacts"] = [n for n in OUTPUT_NAMES if n not in suffixes]
    readings["artifact_count"] = len(ids)
    for name in OUTPUT_NAMES:
        body = content_of(client, ids, name)
        readings[f"present:{name}"] = body is not None
        readings[f"length:{name}"] = 0 if body is None else len(body)
    readings["manuscript"] = content_of(client, ids, "manuscript.md")
    readings["response_letter"] = content_of(client, ids, "response_letter.md")
    readings["author_responses"] = content_of(client, ids, "author_responses")
    readings["review_decision"] = content_of(client, ids, "review_decision")
    progress = phase_progress(client, run_id)
    readings["phase_states"] = {row.get("phase_id"): row.get("state") for row in progress}
    readings["phase_artifact_ids"] = {
        row.get("phase_id"): row.get("artifact_ids") for row in progress
    }
    experiments = client.get(f"/runs/{run_id}/experiments").json()
    rows = experiments.get("experiments") if isinstance(experiments, dict) else experiments
    readings["experiment_rows"] = len(rows or [])
    readings["failure_events"] = failure_events(client, run_id)


def reported_readings(manuscript: str) -> tuple[int, int, int, str] | None:
    """脚注里的三条读数（句数 / 标记数 / 条目数 / 单支撑节）。"""
    match = READINGS_LINE.search(manuscript)
    if match is None:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)), match.group(4))


def body_sections(manuscript: str, keys: tuple[str, ...]) -> dict[str, str]:
    """从 `manuscript.md` 的**编号节标题**切出各键的正文（与汇编器同一分界）。"""
    sections: dict[str, str] = {}
    for key in keys:
        marker = SECTION_HEADINGS.get(key)
        if marker is None or marker not in manuscript:
            continue
        start = manuscript.index(marker) + len(marker)
        cut = len(manuscript)
        for value in SECTION_HEADINGS.values():
            if value in manuscript[start:]:
                cut = min(cut, manuscript.index(value, start))
        for stop in ("### Table 1.", "## References"):
            if stop in manuscript[start:]:
                cut = min(cut, manuscript.index(stop, start))
        sections[key] = manuscript[start:cut]
    return sections


def footnote_matches_body(manuscript: str, reported: tuple[int, int, int, str]) -> bool:
    """脚注读数必须与**从正文重算**的结果相等（同一份字节、同一个函数）。"""
    from packages.application.deliverable.citation_sufficiency import measure_citation_sufficiency
    from packages.application.deliverable.manuscript import MANUSCRIPT_KEYS

    sections = body_sections(manuscript, MANUSCRIPT_KEYS)
    if not sections:
        return False
    readings = measure_citation_sufficiency(sections)
    recomputed = (
        len(readings.per_sentence),
        sum(item.marks for item in readings.per_sentence),
        len(readings.per_reference),
        ", ".join(readings.single_support_sections) or "none",
    )
    return recomputed == reported


def letter_pairs(letter: str) -> list[tuple[str, str]]:
    """应答信 → `[(该段的原意见引用, 该段的 action_taken), …]`（按 `### P<n>` 分段）。"""
    pairs: list[tuple[str, str]] = []
    quote: str | None = None
    for line in letter.splitlines():
        stripped = line.strip()
        if line.startswith("### P"):
            quote = None
        elif stripped.startswith("> "):
            quote = stripped[2:].strip() if quote is None else f"{quote} {stripped[2:].strip()}"
        elif "**Action taken.**" in line and quote is not None:
            pairs.append((quote, line.split("**Action taken.**", 1)[1].strip()))
            quote = None
    return pairs


def action_overlaps(response_letter: str, review_decision: str) -> tuple[int, int]:
    """应答信里 `**Action taken.**` 行与**它自己那条**评审点的实词重叠读数。

    返回 `(条数, 有效重叠条数)`。**按点配对，不按整段评审**：每个 `### P<n>` 段带着它回应的
    原意见（`> …` 引用行），本条只拿那段引用与**同段**的行动比。拿整份 `review_decision`
    当词库会把「与**任何一条**评审点重叠」算成通过 —— 那是假的宽松（GOAL-105 `W-2` 的射程
    说的是「与它回应的那条」）。

    词口径复用产品侧 `content_words`（与 `validate_action_references` 判据 ③ 同一份），
    因此这条读数证明的是**产品判据真的跑过**，不是另造一套判法。
    """
    from packages.application.deliverable.manuscript_quality import content_words

    pairs = letter_pairs(response_letter)
    if not pairs:
        # 信的形状不含 `### P<n>` 段（旧形状）：退回整段口径，但**如实标注**
        # —— 调用方据 `pairs` 为空知道这条读数比的是宽松口径。
        actions = [
            line.split("**Action taken.**", 1)[1].strip()
            for line in response_letter.splitlines()
            if "**Action taken.**" in line
        ]
        point_words = content_words(review_decision)
        return (len(actions), sum(1 for a in actions if content_words(a) & point_words))
    overlapped = sum(1 for quote, action in pairs if content_words(action) & content_words(quote))
    return (len(pairs), overlapped)


__all__ = [
    "DIRECTION",
    "EVIDENCE",
    "OUTPUT_NAMES",
    "PHASES",
    "PROTOCOL",
    "PROTOCOL_ID",
    "SECTION_HEADINGS",
    "action_overlaps",
    "artifact_ids",
    "assembled_product",
    "body_sections",
    "collect_readings",
    "content_of",
    "drive_one_run",
    "failure_events",
    "footnote_matches_body",
    "letter_pairs",
    "live_gate",
    "phase_progress",
    "preflight_override",
    "register_credential",
    "reported_readings",
    "unique",
    "write_readings",
]
