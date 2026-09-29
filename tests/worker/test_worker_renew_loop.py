"""GOAL-026 EC-02（AC-6）：worker 面的**续租真的发生**。

既有判据的缺口（建档实测）：`tests/worker/test_worker_loop.py` 的 `_FakeClient` 有
`self.renews = 0` 且 `renew(...)` 自增，**但没有任何用例断言它非零** ⇒
「`services/worker/loop.py:399-416` 的 `_renew_loop` 守护线程真的续租过」从未被证。

本判据：① 处理一个作业后 **续租至少一次**，且每次携带的是**被持有的那一份身份**
（`task_id` / `lease_id` / `fence`）；② 对照：没有作业时**零续租**（证明计数不是恒真）。
"""

from __future__ import annotations

import time
from pathlib import Path

from adapters.fakes.execution_backend import FakeExecutionBackend
from packages.domain.workspace import ExecutionStatus
from services.worker.loop import WorkerLoop, WorkerLoopConfig

_JOB: dict[str, object] = {
    "task_id": "task-1",
    "lease_id": "lease-1",
    "fence": 1,
    "spec_json": '{"backend_kind":"DOCKER","command":"echo hi","workdir":"/workspace"}',
    "timeout_seconds": 5,
}


class _RecordingClient:
    """最小 fake：只记录 `renew` 的**身份三元组**，其余按既有 fake 的形状回话。"""

    def __init__(self, job: dict[str, object] | None) -> None:
        self._job = job
        self.renews: list[tuple[str, str, int]] = []
        self.heartbeat_interval_seconds = 0.2
        self.generation = 1

    def renew(self, task_id: str, lease_id: str, fence: int) -> None:
        self.renews.append((task_id, lease_id, fence))

    def cancel_requested(self, task_id: str) -> bool:
        return False

    def register(
        self, gpu_observation: object | None = None, *, capabilities: tuple[str, ...] | None = None
    ) -> dict[str, object]:
        self.generation += 1
        return {"session_token": "t", "registration_generation": self.generation}

    def heartbeat(self) -> dict[str, object]:
        return {"accepted": True, "state": "READY", "drain_requested": False}

    def claim(self) -> dict[str, object] | None:
        job, self._job = self._job, None
        return job

    def download_bundle(
        self, artifact_id: str, *, task_id: str, lease_id: str, fence: int
    ) -> bytes:
        return b""

    def upload_bundle(
        self, bundle: bytes, *, task_id: str, lease_id: str, fence: int
    ) -> dict[str, object]:
        return {"artifact_id": "out-1", "digest": "sha256:x"}

    def submit_result(self, task_id: str, payload: object) -> dict[str, object]:
        return {"accepted": True, "task_id": task_id}


def _wait_for_renew(client: _RecordingClient, *, timeout: float = 5.0) -> bool:
    """有界等待：续租线程是守护线程，作业结束得很快 ⇒ 给它一个明确的窗口。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if client.renews:
            return True
        time.sleep(0.01)
    return bool(client.renews)


def test_renew_loop_renews_the_held_lease_identity(tmp_path: Path) -> None:
    client = _RecordingClient(dict(_JOB))
    loop = WorkerLoop(
        client,  # type: ignore[arg-type]
        FakeExecutionBackend(status=ExecutionStatus.SUCCEEDED),
        config=WorkerLoopConfig(max_iterations=2, scratch_root=str(tmp_path / "scratch")),
    )
    assert loop.run() == 1
    assert _wait_for_renew(client), "续租线程必须真的续租过至少一次（renews 非零）"
    assert set(client.renews) == {("task-1", "lease-1", 1)}, "续租必须携带被持有的身份三元组"


def test_no_renew_when_no_job_is_claimed(tmp_path: Path) -> None:
    """对照：没有作业 ⇒ 零续租（否则上面的「非零」可能是恒真计数）。"""
    client = _RecordingClient(None)
    loop = WorkerLoop(
        client,  # type: ignore[arg-type]
        FakeExecutionBackend(),
        config=WorkerLoopConfig(max_iterations=3, scratch_root=str(tmp_path / "scratch")),
    )
    assert loop.run() == 0
    assert client.renews == []
