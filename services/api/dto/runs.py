"""Run 生命周期 DTO。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RunStartDto(BaseModel):
    """启动运行：旧 `protocol_path` 与新草稿修订引用二选一。

    草稿修订引用（PLAN-20260908-033）：服务端加载不可变修订正文后走
    与 path 完全相同的 Compile → Preflight → Freeze 链；草稿后续变化
    不改写已冻结运行。
    """

    protocol_path: str | None = Field(default=None, min_length=1, max_length=500)
    draft_id: str | None = Field(default=None, min_length=1, max_length=120)
    draft_revision: int | None = Field(default=None, ge=1)
    trace_id: str | None = Field(default=None, max_length=200)


class PausedDispatchDto(BaseModel):
    """`PAUSED` 的派发语义（GOAL-004 cycle 2 = EC-02）。

    只由 canonical 事实推出（run 行状态 + 任务行 `RETRY_SCHEDULED`/`retry_at`），
    不是"停车原因"字段：没有第二个会被别的状态变更写脏的标志位。

    - `kind=RETRY_SCHEDULED`：任务面有重排 ⇒ 守护线程会在到期后自己续跑；
      `due_now=true` 表示**现在**就已经到期（含"重建被拒后放回停车"这一种，
      拒绝原因不在读面）。
    - `kind=USER_PAUSED`：任务面没有任何重排 ⇒ 只有人工 resume/cancel 会动它。
    - `kind=UNKNOWN`：没有 workflow 读面（或读面读不到）⇒ 不猜。
    """

    kind: str
    next_retry_at: str | None = None
    due_now: bool = False


class DispatchRetryDto(BaseModel):
    """重排读面（与 `PausedDispatchDto` 同一判据、同一次读出的数字）。"""

    scheduled: int = 0
    due: int = 0
    next_retry_at: str | None = None


class LeaseHolderDto(BaseModel):
    """一个**活着**的租约持有者（读面不复制作业面凭据 `lease_id`）。

    `worker_id` 为空 = 租约由控制面自己持有（agent session 投递），非空 = worker plane
    的 claim；`expires_at` 是 canonical 租约行上的到期时刻。
    """

    task_id: str
    worker_id: str | None = None
    fence: int = 0
    expires_at: str | None = None


class RebuildReadinessDto(BaseModel):
    """重建能力读面：这份**记录**够不够重建、缺哪条事实。

    历史行（旧 run 没有冻结正文、旧 `manifest.frozen` 事件没有 `semantic_digest`）此前
    只能读到一个 `None`，分不清"功能前历史行"与"还没冻结"。这个读面正面回答：

    - `status=SELF_CONTAINED`：冻结正文 + 两个 digest 齐 ⇒ 重建只用行上的字节；
    - `status=SOURCE_DEPENDENT`：两个 digest 齐、无冻结正文 ⇒ 重建依赖来源仍可解析
      （路径 / 草稿修订还在）；
    - `status=REFUSED`：缺阻塞事实 ⇒ 重建会被拒绝，出路是 fork run 或 revision；
      `missing` **点名**缺的是哪条事实（`manifest_digest` / `manifest_semantic_digest` /
      `protocol_body` / `protocol_source`，即 canonical 行上的字段名）。

    诚实边界：只回答"输入齐不齐"，不回答"该不该重建"（状态机 / 策略 / 预算不在这里），
    也不承诺"重建必过"（漂移校验与 preflight 仍在 `/resume` 真跑时判）。
    """

    status: str
    missing: list[str] = Field(default_factory=list)


class DispatchOwnershipDto(BaseModel):
    """统一派发读面（GOAL-004 cycle 6 = EC-05 ②）：这条 run 现在谁在派发它。

    与 `PausedDispatchDto` 的区别：那一个只回答 `PAUSED` 的**停车语义**（会不会自己走），
    这一个对**任何状态**回答"有没有活的派发方、是哪一个"。两者由**同一次** port 读
    （`WorkflowEngine.dispatch_ownership`）分解而来，不会各说各话。

    - `kind=WORKER_CLAIM`：有**活着**的租约持有者（工人 claim 或控制面自身的投递）；
    - `kind=RETRY_DISPATCH`：任务面有重排（等时钟或已到期）⇒ 派发守护会（或马上会）续跑；
    - `kind=BOTH`：两件事实同时存在；
    - `kind=NONE`：都没有（停车等人工介入的 run 通常落在这里）；
    - `kind=UNKNOWN`：没有 workflow 读面（或读面读不到）⇒ 不猜。

    "活"由 adapter 用权威时钟判定（回收判据的补集）；读面只读 canonical 事实，不回答
    执行健康度（心跳新鲜度、进度、卡死与否都不在这里）。
    """

    kind: str
    retry: DispatchRetryDto = Field(default_factory=DispatchRetryDto)
    holders: list[LeaseHolderDto] = Field(default_factory=list)


class RuntimeFingerprintDto(BaseModel):
    """运行时指纹槽位的**诚实状态**（AGENTS.md §4 / GOAL-007 EC-04）。

    `status` 取 `NOT_VERIFIED` 时 `reason` 点名为什么（默认受控 demo 执行体不发起模型
    调用，§4 的七件事实一件也不存在）。它是**状态**不是**指纹值**：读面不得把它当作
    「已验证的指纹」，也不得在 `status != VERIFIED` 时渲染成指纹结论。
    """

    status: str
    substrate: str | None = None
    reason: str | None = None


class RunExecutionDto(BaseModel):
    """执行体读面（GOAL-007 cycle 4 = EC-04）：这条 run 是哪个执行体跑的。

    事实来源是冻结的 `manifest.frozen` 事件。`execution_backend is None` 有两种情形，
    由外层区分：外层为 `None` = 这条 run **尚未冻结**；外层非 `None` 而
    `execution_backend is None` = **冻结时未声明**（M7 不伪填充口径）。两者都**不得**
    读作某一个具体执行体。
    """

    execution_backend: str | None = None
    runtime_fingerprint: RuntimeFingerprintDto | None = None


class RunDetailDto(BaseModel):
    id: str
    project_id: str
    protocol_id: str
    state: str
    manifest_digest: str | None = None
    # GOAL-004 cycle 4：冻结的**语义 digest**（排除 frozen_at，resume 漂移校验的输入）。
    # 非空 = 这条 run 冻结过 manifest 且事件里带这项；执行期失败收敛的 run 同样带
    # （此前只带 manifest_digest）。None = 未冻结或事件早于本轮，不保证可重建。
    manifest_semantic_digest: str | None = None
    # GOAL-004 cycle 1：冻结协议正文的 digest。None = 旧 run 没有冻结正文
    # （重启续跑仍依赖那份外部来源可解析），非 None = 这条 run 自足可重建。
    protocol_body_digest: str | None = None
    # GOAL-004 cycle 2：仅当 state == PAUSED 时非 None（其余状态"不适用"）。
    paused_dispatch: PausedDispatchDto | None = None
    # GOAL-004 cycle 6：统一派发读面（任何状态都给；与 paused_dispatch 同一次读分解而来）。
    dispatch: DispatchOwnershipDto | None = None
    # GOAL-005 cycle 6 = EC-06：重建能力读面（任何状态都给）。把上面两个 None 与
    # "冻结正文缺席"合成一个**点名事实**的回答——历史行不再是含糊的 None。
    rebuild: RebuildReadinessDto
    # GOAL-007 cycle 4 = EC-04：执行体读面（**仅详情路径**给）。列表路径不带它：那是批量
    # 读面，逐 run 回读冻结事件会变成 N+1；列表要披露时另开批量读面，不在这里静默省略。
    execution: RunExecutionDto | None = None
    created_at: str
    updated_at: str


class TaskDto(BaseModel):
    task_id: str
    contract_id: str
    agent_id: str | None = None
    status: str
    attempt: int
