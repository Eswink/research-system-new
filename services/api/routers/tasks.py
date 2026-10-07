"""任务级人工干预控制面路由（GOAL-20261008-033 EC-01）。

**它补的是什么**：ADR-0033 把「人工恢复一条死信任务」做成了 Port 上的一等能力
（`WorkflowEngine.requeue`），但**产品面没有入口** —— 建档实测：`services/` 内
`requeue` / `DEAD_LETTER` 零命中、无 HTTP 路由、`engine.requeue` 的调用方**全部**在
`tests/` 下。也就是说这项能力只在引擎面成立，运维要恢复一条死信只能进 REPL 或改库。

本路由把它接成**产品路径**：`POST /tasks/{task_id}/retry`。
`docs/api/CONTROL_PLANE_API.md` 的 Tasks 节此前把这条路径逐字登记为
「**未提供**：retry 属 WorkflowEngine 内部策略」—— 本轮把它从「未提供」推进到「提供」，
实现体就是那条既有策略的**人工入口**（不是第二套策略）。

**不建第二套恢复逻辑**：路由只做两件事 —— 找 workflow 面、把引擎的结论翻译成稳定
HTTP 语义。状态机、点名拒绝文案、事件、尝试预算与 `fence_seq` 的处置全部沿用
ADR-0033 的既有实现，本层**不做**任何状态判定。

错误语义（**点名失败**，不静默）：

- 未装配 workflow 面 ⇒ **503**（不伪造成功）；
- 任务不存在 ⇒ **404**（消息含任务 id）；
- 状态不是 `DEAD_LETTER`（含「已恢复」与其它终态）⇒ **409**（消息含任务 id 与实际状态）。

**幂等两层**：控制面 `Idempotency-Key` 中间件在**本路由之前**截住同 key 重放（同 key +
同 payload 复用首次响应，**不**第二次触达引擎）；**新**请求打在已恢复的任务上走上面那条
409 点名拒绝。两层合起来即 ADR-0033 决定 3 的「重复恢复零第二次副作用」。

**响应面故意很小**：只回报引擎的权威结论（`restored`）。"这条任务现在是什么状态"由既有的
`GET /runs/{id}/tasks` 投影回答 —— 本端点**不**复制一份状态读面，因为引擎的 `requeue`
按 task_id 定位、**不**携带 run_id，本层若去凑一个状态回读就得先猜任务属于哪个 run
（猜错就是编事实）。

**认证面自动覆盖**：本端点是写类 POST ⇒ 落在 `_MUTATING_METHODS` 造成的保护面内。
保护面的定义是**方法分类**而非路径清单，所以这里**不需要**登记；
`tests/api/test_write_face_cannot_be_bypassed.py` 从 `app.openapi()` **枚举**写面端点
（该文件自己声明：树新增写面端点时不需要改它就能覆盖）。
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import WorkflowEngine
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.tasks import TaskRetryDto
from services.api.errors import ApiError

router = APIRouter(prefix="/tasks", tags=["tasks"])

#: 引擎点名拒绝的**唯一**「任务不存在」形态（三实现同判；见 `adapters/sqlite/requeue.py`）。
_UNKNOWN_TASK_PREFIX = "unknown task:"

#: 响应注记：把「这次动作能做到什么、做不到什么」逐条写在响应里，不留给调用方猜。
_NOTE = (
    "task returned to the dispatchable face; attempt budget and fence_seq are unchanged "
    "(ADR-0033), so a new claim may deliver it again. This is a task-level action: it does "
    "not touch run state, and the run-level entry point is unchanged "
    "(POST /runs/{run_id}/resume)."
)


def _workflow(deps: ApiDeps) -> WorkflowEngine:
    if deps.workflow is None:
        raise ApiError(503, "Workflow Unavailable", "workflow engine not configured")
    return deps.workflow


def _refusal_status(message: str) -> int:
    """把引擎的点名拒绝映射成稳定 HTTP 语义（按**引擎的消息形态**分类，不看成败）。

    两条形态（三实现同判）：`unknown task: …` ⇒ 404；`… only DEAD_LETTER can be requeued`
    ⇒ 409。未命中的第三种形态归 409（状态面拒绝）并在 detail 里保留引擎原话 ——
    宁可把原因原样交给调用方，也不编一个「未知错误」的壳把它盖掉。
    """
    return 404 if message.startswith(_UNKNOWN_TASK_PREFIX) else 409


@router.post("/{task_id}/retry", response_model=TaskRetryDto)
async def retry_task(task_id: str, request: Request) -> TaskRetryDto:
    """人工恢复一条 `DEAD_LETTER` 任务（ADR-0033 的产品入口）。

    成功 ⇒ 任务回 `QUEUED`（"回到可交付面"），下一次派发（claim / run 级重建续跑）就能
    再取到它。本端点**不**提供「重置尝试预算」这类语义：恢复是"把这条任务放回交付面"，
    不是"把计数器清零"（ADR-0033 决定 4）。
    """
    deps: ApiDeps = get_deps(request)
    workflow = _workflow(deps)
    try:
        result = workflow.requeue(task_id)
    except InvalidInputError as exc:
        status = _refusal_status(str(exc))
        title = "Task Not Found" if status == 404 else "Invalid Task Transition"
        raise ApiError(status, title, str(exc)) from exc
    return TaskRetryDto(task_id=task_id, result=str(result), note=_NOTE)
