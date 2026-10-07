"""工具面（GOAL-20261008-033 EC-03）：`run_resume` 续跑覆盖度的**声明集**与逐条分类。

GOAL-032 EC-03 的八行矩阵里，「不处理」清单**是代表而非穷尽**（该轮 `W-4` 明文登记）。
本模块把那件事变成机器可检的结构：把 `services/api/run_resume.py::rebuild_and_resume`
的结局面写成一张**声明集**，每条要么有可复核判据（点名文件 + 用例名）、要么带非空理由，
**没有第三种状态**。

## 声明集的来源（为什么是这些条目）

不是拍脑袋列的：逐条从**入口源码**枚举（`rebuild_and_resume` 的返回/抛出面）：

| 来源 | 条目 |
| --- | --- |
| `ResumeAttempt(refusal=...)` 三个字面量 | 服务未装配 / preflight 不过 |
| `rebuild_readiness(run).early_refusal()` 两条 | 无来源（旧 run）/ 无冻结 digest |
| `_resume_from_source` 的异常路径（`dependency_prefix()` + 异常名） | 来源不可解析 / **语义漂移** |
| 成功路径 | `ResumeAttempt(outcome=...)` |

`tests/tooling/test_resume_coverage_declaration_matches_source.py` 用 AST + 行为把
这张表与源码**对上账**：新增一条返回/抛出形态而没登记 ⇒ 判红；登记了却不存在 ⇒ 判红。

## 边界（如实登记）

- `DeclaredCase.verdict` 的**三值**是 `HANDLED` / `REFUSED` / `NOT_THIS_ENTRY`：
  前两者描述本入口的处置（成功续跑 / 点名拒绝），第三者描述「这份情形**不归它管**」
  （例如任务级租约过期、死信恢复）—— 三者都必须有判据或理由。
- 本模块**只**拥有声明集与分类；具体行为判据落在各判据文件里（`evidence` 点名）。
"""

from __future__ import annotations

from dataclasses import dataclass

#: 判定词表（没有第四种）。
HANDLED = "HANDLED"
REFUSED = "REFUSED"
NOT_THIS_ENTRY = "NOT_THIS_ENTRY"
_VERDICTS = (HANDLED, REFUSED, NOT_THIS_ENTRY)


@dataclass(frozen=True, slots=True)
class DeclaredCase:
    """声明集里的一条：情形 + 判定 + **判据落点**或**理由**（恰好一个非空）。

    `source_literals` 是**与入口源码的绑定**：该情形对应 `services/api/run_resume.py` 里
    哪些可枚举字面量（空元组 = 该情形不由字面量承载，例如异常路径与成功面）。
    绑定写成字段而不是在判据里用关键词猜散文 —— 猜关键词会把「换了措辞」误判成「覆盖丢了」，
    也会把「没覆盖」误判成「覆盖了」（首版就是这样：英文口径与中文情形描述对不上）。
    """

    id: str
    situation: str
    verdict: str
    evidence: str = ""
    reason: str = ""
    source_literals: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.verdict not in _VERDICTS:
            raise ValueError(f"未知判定: {self.verdict!r}")
        if bool(self.evidence) == bool(self.reason):
            raise ValueError(f"{self.id}: 判据与理由必须**恰好一个**非空（没有第三种状态）")


#: 声明集。**顺序即读序**：先成功面，再本入口的拒绝面，最后不归本入口管的边界。
DECLARED_CASES: tuple[DeclaredCase, ...] = (
    DeclaredCase(
        id="self-contained-rebuild",
        situation="run 行有**冻结正文** ⇒ 只用行上的字节重装配（不碰外部来源）",
        verdict=HANDLED,
        evidence="tests/e2e/test_restart_rebuild_resume.py::"
        "test_a_rebuild_from_the_frozen_body_finishes_the_remaining_work",
    ),
    DeclaredCase(
        id="source-dependent-rebuild",
        situation="digest 齐、无冻结正文，来源仍可解析 ⇒ 按来源重建",
        verdict=HANDLED,
        evidence="tests/e2e/test_restart_rebuild_resume.py::"
        "test_a_restarted_process_finishes_a_parked_run_from_its_recorded_source",
    ),
    DeclaredCase(
        id="refused-no-source",
        situation="装配输入全缺（早于来源登记的旧 run）⇒ 点名拒绝，不猜协议",
        verdict=REFUSED,
        evidence="tests/application/run_orchestration/test_rebuild_readiness.py::"
        "test_a_legacy_row_without_body_or_source_names_both_facts",
    ),
    DeclaredCase(
        id="refused-no-frozen-digest",
        situation="缺 `manifest_digest` ⇒ 无法校验重建 ⇒ 点名拒绝",
        verdict=REFUSED,
        evidence="tests/application/run_orchestration/test_rebuild_readiness.py::"
        "test_a_row_without_a_frozen_digest_names_that_fact",
    ),
    DeclaredCase(
        id="refused-unresolvable-source",
        situation="有 digest、无冻结正文，但来源不可解析（路径消失 / 修订不在）⇒ 点名拒绝",
        verdict=REFUSED,
        evidence="tests/api/test_run_source_and_rebuild_api.py::"
        "test_a_run_without_a_frozen_body_names_both_missing_facts",
    ),
    DeclaredCase(
        id="refused-preflight",
        situation="重编译的 preflight 不过 ⇒ 拒绝（文案 `rebuilt preflight does not pass`）",
        verdict=REFUSED,
        evidence="tests/api/test_run_source_and_rebuild_api.py::test_resume_reports_why_a_rebuild_was_refused",
        source_literals=("rebuilt preflight does not pass; refusing to resume",),
    ),
    DeclaredCase(
        id="refused-semantic-drift",
        situation="冻结语义漂移（plan/catalog/契约/定价）⇒ `assert_semantics_frozen` 拒绝",
        verdict=REFUSED,
        evidence="tests/e2e/test_restart_rebuild_resume.py::"
        "test_a_drifted_catalog_is_rejected_by_the_semantic_check",
    ),
    DeclaredCase(
        id="refused-service-absent",
        situation="组合根没装 run orchestration service ⇒ 拒绝（不伪造续跑）",
        verdict=REFUSED,
        evidence="tests/api/test_run_source_and_rebuild_api.py::"
        "test_without_an_orchestration_service_the_rebuild_refuses",
        source_literals=("run orchestration service is not configured",),
    ),
    DeclaredCase(
        id="boundary-expired-lease",
        situation="**租约过期**：任务被回收 ⇒ `QUEUED` ⇒ 可再交付",
        verdict=NOT_THIS_ENTRY,
        evidence="tests/e2e/test_research_continuity_coverage_matrix.py::"
        "test_an_expired_lease_is_recovered_to_queued_and_redeliverable",
    ),
    DeclaredCase(
        id="boundary-dead-letter",
        situation="**死信任务**：本入口的续跑路径上被终态守卫点名拒绝（恢复是另一条入口）",
        verdict=NOT_THIS_ENTRY,
        evidence="tests/e2e/test_research_continuity_coverage_matrix.py::"
        "test_a_dead_letter_is_not_recovered_by_the_resume_path",
    ),
    DeclaredCase(
        id="boundary-already-succeeded",
        situation="**已成功任务不重跑**（幂等：重建重算剩余工作时跳过它）",
        verdict=NOT_THIS_ENTRY,
        evidence="tests/e2e/test_research_continuity_coverage_matrix.py::"
        "test_a_rebuild_does_not_deliver_already_finished_work",
    ),
    DeclaredCase(
        id="boundary-auto-dispatch-after-restart",
        situation="**重启后重排到期** ⇒ 守护线程自动续跑（不经过 HTTP 入口）",
        verdict=NOT_THIS_ENTRY,
        evidence="tests/e2e/test_research_continuity_coverage_matrix.py::"
        "test_a_parked_run_is_actually_finished_by_the_retry_dispatch_pass",
    ),
    DeclaredCase(
        id="boundary-run-level-auto-continuation",
        situation="**死信恢复后 run 的自动继续**：run 级没有自动交付方（见 GOAL-033 EC-02）",
        verdict=NOT_THIS_ENTRY,
        evidence="tests/e2e/test_dead_letter_run_coordination_matrix.py::"
        "test_the_retry_dispatcher_never_even_considers_a_dead_letter_run",
    ),
    DeclaredCase(
        id="boundary-sqlite-vs-pg-attachment",
        situation="**装配面差异**：本入口经 `ApiDeps` 取装配；SQLite 与 PG 两个组合根各自装配",
        verdict=NOT_THIS_ENTRY,
        reason=(
            "两个组合根的装配差异由各自的组合根判据承载"
            "（`tests/api/test_composition_sqlite_persistence.py` 与 `tests/postgres/`），"
            "不属『续跑覆盖度』这一轴；本 GOAL 不借它凑数"
        ),
    ),
)

#: 声明集**下界**（承 MEM-160：受判面不得被写窄；条数掉下来要有人解释）。
MIN_DECLARED_CASES = 14

#: 各判定的下界（三类都必须有成员，否则声明集只是形状）。
MIN_HANDLED = 2
MIN_REFUSED = 6
MIN_NOT_THIS_ENTRY = 5


def declared_ids() -> tuple[str, ...]:
    return tuple(case.id for case in DECLARED_CASES)


def findings(cases: tuple[DeclaredCase, ...] = DECLARED_CASES) -> list[str]:
    """声明集自审：重复 id / 空情形 / 面规模下界。**空清单 = 没有第三种状态**。"""
    problems: list[str] = []
    ids = [case.id for case in cases]
    duplicated = sorted({name for name in ids if ids.count(name) > 1})
    problems.extend(f"重复的声明条目: {name}" for name in duplicated)
    problems.extend(f"情形描述为空: {case.id}" for case in cases if not case.situation.strip())
    if len(cases) < MIN_DECLARED_CASES:
        problems.append(f"声明集规模 {len(cases)} < 下界 {MIN_DECLARED_CASES}（受判面被写窄）")
    counts = {verdict: sum(1 for c in cases if c.verdict == verdict) for verdict in _VERDICTS}
    for verdict, floor in (
        (HANDLED, MIN_HANDLED),
        (REFUSED, MIN_REFUSED),
        (NOT_THIS_ENTRY, MIN_NOT_THIS_ENTRY),
    ):
        if counts[verdict] < floor:
            problems.append(f"{verdict} 面只有 {counts[verdict]} 条 < 下界 {floor}")
    return problems
