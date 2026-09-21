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


#: 指纹读面的事实来源：**冻结占位**（这次 run 没有实测记录）vs **run 观测**
#: （调用后落下的实测记录）。两者**都**是 canonical 事实，读面必须分得开。
FINGERPRINT_SOURCE_FROZEN = "FROZEN_PLACEHOLDER"
FINGERPRINT_SOURCE_OBSERVED = "RUN_OBSERVATION"

#: 读面呈现的四要素字段名（GOAL-010 EC-04：返回 model 名 / 端点头 / probe 版本 /
#: 兼容性结论中的前三个；结论是 `status`）。`missing_fields` 至少要点名这些项里为空的。
FINGERPRINT_ELEMENT_FIELDS = (
    "endpoint_config_digest",
    "returned_model_identifier",
    "probe_suite_digest",
    "system_fingerprint",
)


class RuntimeFingerprintDto(BaseModel):
    """运行时指纹读面（AGENTS.md §4；GOAL-007 EC-04 建槽，GOAL-010 EC-04 加实测）。

    `status` **只有两态**：`REPEATABLE_CONFIGURATION`（配置已被一次真实运行确认）或
    `NOT_VERIFIED`。**没有**、也不接受「模型完全可复现」这类表述——两态穷举由域枚举
    保证，读面只呈现、不另判。

    `source` 说明这份事实从哪来：

    - `FROZEN_PLACEHOLDER`：冻结快照里的**状态**记录（这次运行没有实测记录）。此时四要素
      全为空，`missing_fields` 点名全部四项——「没观测到」**不是**「无漂移」。
    - `RUN_OBSERVATION`：run 收敛后落下的**实测**记录。四要素里取不到的项仍点名列在
      `missing_fields` 里（`system_fingerprint` 给不给取决于 provider，缺失是**如实的
      缺口**，不降级结论、也不拿它冒充「模型可复现」）。

    `returned_model_identifier` 是**本次 run 的 usage 度量报告**的 model 名（不是原始响应
    头、也不是请求里写的那个 id）。观测到**多个不同**值时单值槽位留 `None`（缺项 ⇒
    结论必为 `NOT_VERIFIED`，不挑一个），多值本身在 `observed_model_identifiers` 里。

    `missing_fields` = 上面四要素里取值为空的项 ∪ 实测记录自报的缺项（后者可能含
    `safe_response_metadata`——白名单响应头，本 DTO 不作为字段单独呈现，但记录会如实点名）。
    """

    status: str
    substrate: str | None = None
    reason: str | None = None
    source: str = FINGERPRINT_SOURCE_FROZEN
    endpoint_config_digest: str | None = None
    returned_model_identifier: str | None = None
    probe_suite_digest: str | None = None
    system_fingerprint: str | None = None
    observed_model_identifiers: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


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
