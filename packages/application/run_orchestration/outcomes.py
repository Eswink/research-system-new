"""执行链的结果值对象（GOAL-004 cycle 3：从 `phase_runner` 拆出，供多个模块共用）。

`phase_runner` 触到 450 行硬上限，把两个**纯数据**结果对象搬到这里；`phase_runner`
仍然从本模块导入并对外保持同名可见（既有 `from ...phase_runner import RunOutcome`
不受影响），依赖方向是 phase_runner → outcomes，无环。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.domain.tasks import ResearchTask


@dataclass(frozen=True, slots=True)
class TaskOutcome:
    task: ResearchTask
    outcome: str
    verdict: str | None = None
    message: str = ""
    # GOAL-004 cycle 3：这条终局失败是**哪条策略允许的**（None = 成功 / 未走策略；
    # "CONTINUE" = 契约声明容忍 ⇒ 失败被记账但没停住 run）。
    failure_policy: str | None = None
    # GOAL-20261006-031 EC-03：本任务里**声明式跳过**的调用（逐字带理由）。任务照常
    # 成功——跳过不是失败；这条字段是「不触发」臂在读面上的可判形态（缺省 = 没跳过）。
    skipped: tuple[str, ...] = ()
    # GOAL-20261008-034 EC-01：本任务运行链的**返回内容**（多轮循环的停止判据读它）。
    # 缺省空 = 既有行为逐字节不变。
    chain_outputs: tuple[object, ...] = ()
    # GOAL-20261009-042 EC-03：**记忆时效门的标注**（待复核的记忆：执行了但带标注）。
    # 与 `skipped` **互不混用**（那是「没执行」）。缺省空 = 既有行为逐字节不变。
    annotations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RunOutcome:
    run_id: str
    state: str
    message: str = ""
    tasks: tuple[TaskOutcome, ...] = ()
    manifest_digest: str | None = None
    # cycle 20：语义 digest 与定价引用同源处理——不随执行结果回填，HTTP 边界就会
    # 静默丢字段，而 resume 的漂移校验（assert_semantics_frozen）恰恰只认它。
    manifest_semantic_digest: str | None = None
    # M15 定价冻结引用(BLOCKER-6):service 在 Manifest freeze 后把这两个
    # 字段回填执行结果，API 再持久化到 ResearchRun；不能只存 manifest digest
    # 否则 run 行会在 HTTP 边界静默丢失冻结价格引用。
    pricing_version: str | None = None
    pricing_digest: str | None = None
    handoff_digests: tuple[str, ...] = ()
    # GOAL-20261008-034 EC-01：多轮循环的**停止事实**（判据 / 类别 / 读数 / 轮数）。
    # 缺省 `None` = 这条 run 没跑循环 ⇒ 既有读面与载荷逐字节不变。
    rounds: dict[str, object] | None = None
    #: 本次执行里各任务运行链的**返回内容**（多轮循环的停止判据读它）。
    #: 缺省空 = 既有行为逐字节不变。
    chain_outputs: tuple[object, ...] = ()
    system_failure: bool = False


def handoff_digests(handoffs: dict[str, object]) -> tuple[str, ...]:
    """各任务 HandoffBundle 的 **digest** 序列（确定性排序）。

    修复（GOAL-027 EC-04）：`RunOutcome.handoff_digests` 此前填的是
    `tuple(sorted(handoffs))` —— `handoffs` 的键是 **task id**，于是名叫
    `handoff_digests` 的字段装的其实是任务 id（实测：三条 UUID）。全仓没有消费者，
    所以这个错名从未被暴露；EC-04 要求「HandoffBundle 的 digest 序列」可取证，
    故修正为真 digest：取每个 bundle 的 `digest`（`build_handoff` 的
    `digest_of(content)`），按 digest 确定性排序（沿用既有排序口径）。
    缺 `digest` 属性的对象（测试里传的裸 dict）**跳过**而不是伪造一个值。
    """
    digests: list[str] = []
    for bundle in handoffs.values():
        digest = getattr(bundle, "digest", None)
        if digest is not None:
            digests.append(str(digest))
    return tuple(sorted(digests))
