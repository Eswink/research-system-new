"""实验的**声明参数面**（GOAL-20261015-079 EC-01；缝在 `ExperimentExecutionRequest.environment`）。

**它补哪一环**：实验脚本的参数今天是**模块常量**（`examples/experiments/*.py` 里
`SEED = 7` / `N_ITEMS = 800` 一类）—— 也就是说「跑什么实验」在**代码里写死**，
计划对实验**没有任何发言权**。本模块把「参数由**声明**给出」做成可判定的传递面：
**装配声明 → 执行请求 → 容器环境**（`experiment_support` → `ExperimentExecutionRequest`
→ `docker_backend`），脚本从环境取值、缺省回落既有常量。

**为什么声明点是装配面而不是契约**：`TaskContract.experiment` 的 docstring 逐字写着
「工作区、会话 id、**种子**属于装配上下文，**不进契约**」—— 参数是**这次跑什么**的
装配知识，不是「这件工作由谁执行」的契约事实。本模块因此挂在装配面：与
`--seed` 一类命令行旗标同一层次。

**§9 纪律（白名单，不是转发）**：只有本模块 `ALLOWED_PARAMETERS` 里列出的键能被传进
容器；未声明的键**点名拒绝**（`UndeclaredExperimentParameterError`），**不**静默丢弃、
**不**原样转发任意环境变量。容器里看到的键名带固定前缀（`EXPERIMENT_PARAM_`），
与执行器自己的键（`EXPERIMENT_RUN_ID`）**命名空间不相交**。

**零回归**：没有任何声明时，本模块产出的环境是**空映射** ⇒ 请求里的 `environment`
与今天逐字相同（脚本回落既有常量）。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from packages.application.ports.errors import InvalidInputError

#: 容器环境里参数键的固定前缀（与执行器自己的 `EXPERIMENT_RUN_ID` 不相交）。
PARAMETER_PREFIX = "EXPERIMENT_PARAM_"

#: **允许传入容器**的参数名（白名单；未列入者点名拒绝 —— §9：声明式放行，不是转发）。
#: 这三个与 `examples/experiments/exact_match_index_benchmark.py` 的既有常量同名同义。
ALLOWED_PARAMETERS: frozenset[str] = frozenset({"seed", "n_items", "duplicate_pairs"})


class UndeclaredExperimentParameterError(InvalidInputError):
    """声明了白名单之外的参数（点名拒绝，不静默丢弃、不原样转发）。"""


def parameter_environment(parameters: Mapping[str, Any] | None) -> dict[str, str]:
    """声明的参数 → 容器环境（**白名单 + 逐键点名**）。

    - 空 / `None` ⇒ **空映射**（零回归：请求里的环境与今天逐字相同）；
    - 白名单外的键 ⇒ `UndeclaredExperimentParameterError`（点名该键与白名单）；
    - 值一律转成字符串（环境变量只能承载文本）；`None` 值 ⇒ 点名拒绝
      （「声明了一个空值」与「没声明」是两件事 —— 前者多半是上游写错了）。
    """
    if not parameters:
        return {}
    unknown = sorted(set(parameters) - ALLOWED_PARAMETERS)
    if unknown:
        raise UndeclaredExperimentParameterError(
            "experiment parameters outside the declared whitelist: "
            f"{', '.join(unknown)} (allowed: {', '.join(sorted(ALLOWED_PARAMETERS))})"
        )
    environment: dict[str, str] = {}
    for key, value in sorted(parameters.items()):
        if value is None:
            raise UndeclaredExperimentParameterError(
                f"experiment parameter {key!r} was declared with a null value "
                "(declare a value or omit the key)"
            )
        environment[f"{PARAMETER_PREFIX}{key.upper()}"] = str(value)
    return environment


def declared_parameters(environment: Mapping[str, str]) -> dict[str, str]:
    """容器环境里**属于本参数面**的键（读面/判据用；把前缀剥回去）。"""
    return {
        key[len(PARAMETER_PREFIX) :].lower(): value
        for key, value in environment.items()
        if key.startswith(PARAMETER_PREFIX)
    }


__all__ = [
    "ALLOWED_PARAMETERS",
    "PARAMETER_PREFIX",
    "UndeclaredExperimentParameterError",
    "declared_parameters",
    "parameter_environment",
]
