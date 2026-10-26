"""沙箱实验的**装配工厂**（GOAL-20261026-097 EC-01/EC-03；自 `experiment_support` 分列）。

**为什么分列**：`experiment_support.py` 卡在 450 行硬上限上，而本轮要在装配面上加两件
东西 —— 「执行后端可以惰性到手」（组合根必须在装配期零 Docker 连接）与「脚本/镜像
可以按契约 pin 覆盖」（声明优先）。派发逻辑留在 `experiment_support`，工厂搬到这里，
与全仓既有的「装配面 vs 执行面分列」同一手法。

**两个出口，差别只有后端怎么来**：

- `docker_experiment_assembly(...)` —— 调用时就 `DockerExecutionBackend(image=...)`，
  而那个构造函数**立刻** `docker.from_env()`（连 daemon）。**判据/工具侧**用它；
- `lazy_docker_experiment_assembly(...)` —— 只把一个「按镜像造后端」的闭包放进装配面，
  **首次派发**才构造。**组合根**用它：`assemble()` 在没有 Docker 的机器上（默认门的
  `quality-windows-latest`）必须仍然成功。

两者其余的量（Port / 脚本 / 参数 / 臂 / 设计来源 / 缺省语义）**逐字同形**。
"""

from __future__ import annotations

from typing import Any

from adapters.execution import DockerExecutionBackend
from services.api.experiment_support import SandboxExperimentAssembly


def docker_experiment_assembly(  # noqa: PLR0913 -- 装配面的量就这么多；缺省值让调用点只给必需的
    *,
    artifacts: Any,
    policy: Any,
    script: str,
    image: str = "research-os-sandbox:m9-test",
    ledger: Any | None = None,
    experiment_store: Any | None = None,
    parameters: dict[str, object] | None = None,
    arms: object | None = None,
    design_source: str | None = None,
) -> SandboxExperimentAssembly:
    """本地装配：执行体 = **既有** `DockerExecutionBackend`（不新增后端/依赖）。

    `parameters` / `arms`（GOAL-20261015-079）与 `design_source`（GOAL-20261015-080）
    由调用方声明；缺省 ⇒ **既有单臂语义逐字不变**。

    **构造即连 Docker**：只在判据/工具侧直接用；组合根走
    `lazy_docker_experiment_assembly(...)`。
    """
    return SandboxExperimentAssembly(
        execution=DockerExecutionBackend(image=image),
        artifacts=artifacts,
        policy=policy,
        image=image,
        ledger=ledger,
        experiment_store=experiment_store,
        script=script,
        parameters=dict(parameters or {}),
        arms=arms,
        design_source=design_source,
    )


def lazy_docker_experiment_assembly(  # noqa: PLR0913 -- 与上一个工厂同一组量（多一个出口）
    *,
    artifacts: Any,
    policy: Any,
    script: str | None,
    image: str = "research-os-sandbox:m9-test",
    ledger: Any | None = None,
    experiment_store: Any | None = None,
    parameters: dict[str, object] | None = None,
    arms: object | None = None,
    design_source: str | None = None,
) -> SandboxExperimentAssembly:
    """组合根用的本地装配：**装配期零 Docker 连接**，首次派发才构造后端。

    `script` 可为 `None`（契约 pin 脚本的装配形态）：那时脚本由契约给出（`declared_or_
    assembled` 声明优先），两者都没有 ⇒ 沙箱工作区里没有 `experiment.py` ⇒ 容器跑不起来
    （**不**静默成功，也**不**猜一个脚本）。
    """
    return SandboxExperimentAssembly(
        execution=None,
        execution_factory=docker_backend_factory,
        artifacts=artifacts,
        policy=policy,
        image=image,
        ledger=ledger,
        experiment_store=experiment_store,
        script=script,
        parameters=dict(parameters or {}),
        arms=arms,
        design_source=design_source,
    )


def docker_backend_factory(image: str) -> Any:
    """按镜像造一个**真实的** `DockerExecutionBackend`（首次派发时才被调用）。"""
    return DockerExecutionBackend(image=image)


__all__ = [
    "docker_backend_factory",
    "docker_experiment_assembly",
    "lazy_docker_experiment_assembly",
]
