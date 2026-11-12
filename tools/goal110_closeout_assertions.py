"""GOAL-20261111-110 的**产品面断言集**（收口验证器的另一半）。

与 `tools/verify_goal110_closeout.py`（记录面）分工：本文件判**交付物真的在、且形态就是
声明的那一个**；主文件判 EC 终态与宪章记账。

**本轮的判法**（每条指向具体闭集或具体行为）：

* 仲裁闭集（EC-01）：三值齐备；**缺省 `REQUIRE_HUMAN`** 在断言集里**重放**（不靠判据文件）；
  `TrustLabel` 成员集与读序键集同源（改枚举即红）；阈值必填。
* 路由（EC-02）：路径在 OpenAPI 快照里、`Idempotency-Key` 由中间件强制（快照可见的写面
  与代码里的路由都在）。
* 判据（EC-03）：三条正例与两条反证的**存在性**（文件在树且含对应断言形态）——
  行为由判据文件自己跑；断言集判「它们真的被交付了」，不重复判行为。
* 闭环（EC-04）：阶梯「证据」行带新 bar；其余六行不被推广。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

#: 交付面（少一件 = 该 EC 没交付）。
DELIVERABLES: tuple[str, ...] = (
    "packages/application/memory/arbitration.py",
    "services/api/routers/memory_conflicts.py",
    "services/api/dto/memory.py",
)

#: 判据文件（`verify:` 字段点名的每一个都必须**在树**——GOAL-108 的教训）。
JUDGES: tuple[str, ...] = (
    "tests/application/memory/test_arbitration.py",
    "tests/api/test_memory_conflict_resolve_route.py",
    "tests/tooling/test_goal110_ladder_evidence_scope.py",
)

#: 收口资产（自指）。
VERIFIER = "tools/verify_goal110_closeout.py"
ASSERTIONS = "tools/goal110_closeout_assertions.py"

#: OpenAPI 快照与路由锚（新路由必须**进快照**：前端类型由它生成）。
OPENAPI = "docs/api/openapi.m13.json"
RESOLVE_PATH = "/memory/{memory_id}/conflicts/{other_id}/resolve"

#: 阶梯锚。
EVIDENCE_BAR = "处置闭环成立（策略闭集 + 可判依据）"
OTHER_LADDER_PREFIXES: tuple[str, ...] = (
    "| 检索 |",
    "| 计划 |",
    "| 复检 |",
    "| 实验 |",
    "| 报告 |",
    "| 迭代 |",
)


def _module(root: Path, relative: str, name: str) -> ModuleType | None:
    path = root / relative
    if not path.is_file():
        return None
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _file_verdicts(root: Path, toolbox: Any) -> list[Any]:
    return [
        toolbox.verdict(
            f"delivered-{Path(relative).name}",
            (root / relative).is_file(),
            f"{relative} 不在树",
        )
        for relative in (*DELIVERABLES, *JUDGES, VERIFIER, ASSERTIONS)
    ]


def _goal110_record(memory_id: str, day: int, confidence: float = 0.9) -> Any:
    """断言集自带的记忆摆件（不进产品、不读盘；只给仲裁喂可判输入）。"""
    from datetime import datetime, timezone

    from packages.domain.core import Timestamp
    from packages.domain.enums import MemoryTier, MemoryType
    from packages.domain.memory import MemoryRecord

    return MemoryRecord(
        id=memory_id,
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content=f"content {memory_id}",
        provenance="goal110-assertions",
        confidence=confidence,
        valid_from=Timestamp(value=datetime(2026, 11, day, tzinfo=timezone.utc)),
    )


def _trust_ranking_covers_every_label(module: ModuleType) -> bool:
    from packages.domain.enums import TrustLabel

    return {label.value for label in TrustLabel} == set(module.TRUST_RANKING)


def _arbitration_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：闭集齐备、缺省 `REQUIRE_HUMAN` **重放**、读序同源、阈值必填。"""
    module = _module(root, "packages/application/memory/arbitration.py", "g110_arbitration")
    if module is None:
        return [toolbox.verdict("arbitration-importable", False, "arbitration 不可加载")]
    left, right = _goal110_record("mem-a", 1), _goal110_record("mem-b", 10)
    default = module.arbitrate(left, right)
    newer = module.arbitrate(
        left, right, policy=module.DeclaredPolicy(strategy="NEWER_WINS", min_confidence=0.6)
    )
    below = module.arbitrate(
        _goal110_record("mem-low", 12),
        right,
        policy=module.DeclaredPolicy(strategy="NEWER_WINS", min_confidence=0.95),
    )
    ranking_ok = _trust_ranking_covers_every_label(module)
    return [
        toolbox.verdict(
            "arbitration-closed-set-is-three-valued",
            module.OUTCOMES == {"NEWER_WINS", "SOURCE_TRUST_WINS", "REQUIRE_HUMAN"},
            f"三值闭集实得 {sorted(module.OUTCOMES)}",
        ),
        toolbox.verdict(
            "arbitration-default-is-require-human",
            default.outcome == "REQUIRE_HUMAN" and default.winner_id is None,
            f"缺省必须是 REQUIRE_HUMAN，实得 {default.outcome!r}",
        ),
        toolbox.verdict(
            "arbitration-newer-wins-names-its-basis",
            newer.outcome == "NEWER_WINS" and newer.winner_id == "mem-b",
            f"NEWER_WINS 应留 mem-b，实得 {newer.outcome!r}/{newer.winner_id!r}",
        ),
        toolbox.verdict(
            "arbitration-refuses-below-threshold",
            below.outcome == "REQUIRE_HUMAN" and bool(below.missing),
            "低于阈值必须拒自动消解并点名",
        ),
        toolbox.verdict(
            "trust-ranking-covers-every-label",
            ranking_ok,
            "TrustLabel 成员集必须与仲裁读序键集同源（改枚举即红）",
        ),
        toolbox.verdict(
            "declared-policy-requires-a-threshold",
            _requires_threshold(module),
            "声明自动策略必须带 min_confidence（无凭据的口子开不出来）",
        ),
    ]


def _requires_threshold(module: ModuleType) -> bool:
    try:
        module.DeclaredPolicy(strategy="NEWER_WINS")
    except TypeError:
        return True
    return False


def _route_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：路由在 OpenAPI 快照里，且路由文件引用仲裁与 lifecycle。"""
    snapshot_path = root / OPENAPI
    if not snapshot_path.is_file():
        return [toolbox.verdict("openapi-snapshot-present", False, f"{OPENAPI} 不在树")]
    schema = json.loads(snapshot_path.read_text(encoding="utf-8"))
    paths = schema.get("paths") or {}
    router_source = (root / "services/api/routers/memory_conflicts.py").read_text(encoding="utf-8")
    dto_source = (root / "services/api/dto/memory.py").read_text(encoding="utf-8")
    return [
        toolbox.verdict(
            "resolve-route-is-in-the-openapi-snapshot",
            RESOLVE_PATH in paths,
            f"快照里必须有 {RESOLVE_PATH}",
        ),
        toolbox.verdict(
            "resolve-route-declares-a-request-body",
            RESOLVE_PATH in paths and "requestBody" in json.dumps(paths[RESOLVE_PATH]),
            "消解路由必须声明请求体（策略 / 阈值 / 人来裁决的 resolved_by）",
        ),
        toolbox.verdict(
            "router-uses-the-arbitration-closed-set",
            "arbitrate(" in router_source and "DeclaredPolicy(" in router_source,
            "路由必须经仲裁纯函数，不另写第二套判定",
        ),
        toolbox.verdict(
            "router-records-through-the-existing-lifecycle",
            "resolve_memory_conflict(" in router_source,
            "落账必须走既有 lifecycle 用例（不新造第二套写面）",
        ),
        toolbox.verdict(
            "resolve-dtos-are-declared",
            "MemoryConflictResolveDto" in dto_source and "MemoryConflictVerdictDto" in dto_source,
            "消解请求/判词 DTO 必须在 DTO 模块里声明",
        ),
    ]


def _judge_shape_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：判据文件里**三正例 + 两反证**的形态在位（行为由它们自己跑）。"""
    domain = (root / "tests/application/memory/test_arbitration.py").read_text(encoding="utf-8")
    route = (root / "tests/api/test_memory_conflict_resolve_route.py").read_text(encoding="utf-8")
    return [
        toolbox.verdict(
            "judges-cover-three-strategies",
            all(
                marker in domain
                for marker in (
                    "test_newer_wins",
                    "test_source_trust_wins",
                    "the_default_is_require",
                )
            ),
            "三策略各一条正例（NEWER_WINS / SOURCE_TRUST_WINS / 缺省 REQUIRE_HUMAN）",
        ),
        toolbox.verdict(
            "judges-cover-below-threshold-refusal",
            "below_the_declared_threshold" in domain,
            "反证一：低于阈值必须拒自动消解",
        ),
        toolbox.verdict(
            "judges-cover-duplicate-resolution",
            "second_resolution" in route and "already resolved" in route,
            "反证二：同一对不能重复消解（路由层按压）",
        ),
        toolbox.verdict(
            "judges-cover-idempotency",
            "idempotency_key" in route and "replays_the_same_response" in route,
            "幂等键的正例与复用反证都在路由判据里",
        ),
    ]


def _ladder_verdicts(root: Path, toolbox: Any) -> list[Any]:
    charter = toolbox.text(root, ".cursor/plans/goals/MAINLINE.md")
    evidence = next((line for line in charter.splitlines() if line.startswith("| 证据 |")), "")
    return [
        toolbox.verdict(
            "ladder-evidence-row-carries-the-new-bar",
            EVIDENCE_BAR in evidence,
            "「证据」行的 下一级 必须是处置闭环 bar",
        ),
        *(
            toolbox.verdict(
                f"ladder-{prefix.strip('| ').strip()}-not-promoted",
                EVIDENCE_BAR
                not in next((line for line in charter.splitlines() if line.startswith(prefix)), ""),
                f"{prefix.strip('| ')} 行不得被越级推广",
            )
            for prefix in OTHER_LADDER_PREFIXES
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 的产品面全量断言（验证器按路径加载并调用它）。"""
    return [
        *_file_verdicts(root, toolbox),
        *_arbitration_verdicts(root, toolbox),
        *_route_verdicts(root, toolbox),
        *_judge_shape_verdicts(root, toolbox),
        *_ladder_verdicts(root, toolbox),
    ]
