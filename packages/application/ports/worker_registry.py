"""WorkerRegistry Port：worker 生命周期注册表（M16 / ADR-0027）。

职责：worker 注册（新世代）、心跳（服务端时间权威）、状态迁移（claim/
settle/drain/offline）、LOST 判定支撑（list_stale）、只读查询。
非职责：不做租约/队列（WorkflowEngine 唯一权威）；不认证 token
（worker gateway 职责）；不执行作业（worker 进程职责）。

时钟语义（M16 计划 §5）：服务端时间是唯一权威。实现必须用服务端时间
写 `last_heartbeat` 并做 stale 判定；worker 自报时间戳一律不参与。
心跳幂等：`last_heartbeat = greatest(stored, server_now)`，重复/回拨
心跳不会把时间往回拨；`registration_generation` 小于库中值即拒绝
（旧 session 一律 fail closed）。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.workers import WorkerRegistration


@runtime_checkable
class WorkerRegistry(Protocol):
    """worker 注册表契约；所有写路径以服务端时间为准。"""

    def register(self, registration: WorkerRegistration) -> WorkerRegistration:
        """创建/重注册 worker（upsert）。

        返回存储后的注册记录：`registration_generation` 由 registry 分配
        （首次 1，重注册单调 +1，作废旧世代 token），`state` 置
        REGISTERING，`last_heartbeat` 置服务端当前时间。
        """
        ...

    def heartbeat(self, worker_id: str, generation: int) -> bool:
        """心跳（幂等）。

        仅当 `generation` 等于库中当前世代才接受；接受时
        `last_heartbeat = greatest(stored, server_now)`。
        worker 未知或世代过期/超前 → False（fail closed），不抛错。
        """
        ...

    def transition(self, worker_id: str, event: str) -> WorkerRegistration:
        """按 WorkerState 迁移表推进状态（CLAIM/JOB_SETTLED/...）。

        非法迁移抛 InvalidTransitionError；worker 未知抛 InvalidInputError。
        """
        ...

    def drain(self, worker_id: str) -> WorkerRegistration:
        """请求下线（DRAIN_REQUESTED）：READY/BUSY → DRAINING，置
        drain_requested=True；此后 claim 不再分配新作业。"""
        ...

    def mark_lost(self, worker_id: str) -> WorkerRegistration:
        """服务端判定心跳过期（HEARTBEAT_EXPIRED → LOST）。

        仅对非终态 worker 合法；租约释放仍只走
        `WorkflowEngine.recover_expired_leases`（单一租约权威）。
        """
        ...

    def set_session_token(self, worker_id: str, generation: int, token_sha256: str) -> bool:
        """绑定 session token 的 sha256（仅存哈希，绝不存明文）。

        仅当 `generation` 等于库中当前世代才写入（旧世代 fail closed）。
        重新注册会清空旧 token（register 置 session_token_sha256=NULL）。
        """
        ...

    def authenticate(self, token_sha256: str) -> WorkerRegistration | None:
        """按 token sha256 解析当前有效世代的 worker；无匹配返回 None。

        只匹配当前 `registration_generation` 绑定的 token，因此旧世代
        token 一经重新注册即失效（反重放）。
        """
        ...

    def list_stale(self, stale_seconds: float) -> tuple[str, ...]:
        """返回服务端时间下 last_heartbeat 落后超过 stale_seconds 的非终态
        worker id（确定性排序）；供 WorkerReaperScheduler 判定 LOST。"""
        ...

    def get(self, worker_id: str) -> WorkerRegistration | None: ...

    def list_workers(self) -> tuple[WorkerRegistration, ...]:
        """全部 worker 注册记录（确定性按 worker_id 排序）。"""
        ...
