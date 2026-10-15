"""实验的**臂（arm）声明**（GOAL-20261015-079 EC-02）。

**它补哪一环**：实验今天**一次 run 一个实验**（`experiment_run_id_of(run_id)` 从 run id
派生 ⇒ 一 run 一实验 id）。于是「对照」只能靠**再跑一次 run** —— 而两次 run 的模型、
协议、甚至时钟都不同 ⇒ 差异**不可归因**。本模块把「一次 run 里跑几个臂、每个臂用什么
参数」做成**声明事实**。

**为什么臂声明在装配面**：与 `plan_parameters` 同一层理由 —— 「这次跑什么」是装配知识，
不是「这件工作由谁执行」的契约事实（契约的 docstring 逐字把「跑哪个脚本 / 哪个镜像」
留给装配上下文）。

**命名与派生**（本模块唯一的确定性）：

- 每个臂有**名字**（声明的键，如 `control` / `treatment`）；
- 臂的**实验 id** 由 `derived_id("experiment-arm", f"{run_id}:{arm}")` 派生
  ⇒ ① 合法 UUID4 布局（`ID` 的域不变量）；② **按 run + 臂确定性**（同一次 run 重跑得同一个
  id，重启后可复算）；③ **不与** `experiment_run_id_of(run_id)` 相撞（那个是「整条 run 的
  单个实验 id」，既有语义保留给**非多臂**路径）。

**零回归**：没有声明臂时，本模块产出的臂列表**为空** ⇒ 走既有单臂路径（`experiment_run_id_of`
+ 今天的参数环境），逐字不变。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from packages.application.ports.errors import InvalidInputError

#: 臂 id 的确定性命名空间（与 `derived_id` 的既有用法同形：`kind` + `seed` 字符串）。
_ARM_KIND = "experiment-arm"

#: 一个臂的默认名（声明只给参数、不给名字时用它 —— 单臂形态）。
DEFAULT_ARM = "default"


@dataclass(frozen=True, slots=True)
class ArmDeclaration:
    """一个实验臂的声明：**名字** + 它的**参数**（参数按 `plan_parameters` 的白名单校验）。

    `parameters` 为空 ⇒ 该臂用脚本的既有缺省（那时它通常是**对照**臂）。
    """

    name: str
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("arm name must not be empty")


def parse_arms(raw: object) -> tuple[ArmDeclaration, ...]:
    """装配声明 → 臂列表（**两种形态**，都点名拒绝非法输入）。

    - `None` / 空 ⇒ **空元组**（零回归：走既有单臂路径）；
    - `Mapping[str, Mapping]`：`{臂名: {参数}}`（planner 友好的紧凑形）；
    - `Sequence[Mapping]`：`[{name: ..., parameters: {...}}, ...]`（显式形，可携带顺序）。

    **不猜**：形态不符 / 臂名为空 / 臂名重复 ⇒ `InvalidInputError` 点名（不静默取其 一）。
    """
    if raw is None:
        return ()
    if isinstance(raw, Mapping):
        arms = tuple(
            ArmDeclaration(name=str(name), parameters=dict(params or {}))
            for name, params in raw.items()
        )
    elif isinstance(raw, (list, tuple)):
        arms = tuple(_arm_from_mapping(item) for item in raw)
    else:
        raise InvalidInputError(
            "arms declaration must be a mapping of name to parameters, or a list of "
            f"{{name, parameters}} entries; got {type(raw).__name__}"
        )
    if not arms:
        return ()
    names = [arm.name for arm in arms]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise InvalidInputError(f"duplicate arm names in the declaration: {', '.join(duplicates)}")
    return arms


def _arm_from_mapping(item: object) -> ArmDeclaration:
    if not isinstance(item, Mapping):
        raise InvalidInputError(f"arm entry must be a mapping, got {type(item).__name__}")
    name = str(item.get("name") or "").strip()
    if not name:
        raise InvalidInputError("arm entry must carry a non-empty 'name'")
    parameters = item.get("parameters") or {}
    if not isinstance(parameters, Mapping):
        raise InvalidInputError(f"arm {name!r} parameters must be a mapping")
    return ArmDeclaration(name=name, parameters=dict(parameters))


def arm_experiment_id(run_id: str, arm: str) -> str:
    """臂的**实验 id**（按 run + 臂确定性派生；合法 UUID4 布局）。

    与 `experiment_run_id_of(run_id)`（一 run 一实验）**不同域**：本函数只在**声明了臂**
    时使用 ⇒ 非多臂路径的实验 id 逐字不变。
    """
    from packages.application.m12_reference.clean_run_stages import derived_id

    return derived_id(_ARM_KIND, f"{run_id}:{arm}")


def declare_arms(assembly: Any) -> tuple[ArmDeclaration, ...]:
    """装配面声明的臂（缺省空 ⇒ 零回归）。"""
    return parse_arms(getattr(assembly, "arms", None))


__all__ = [
    "DEFAULT_ARM",
    "ArmDeclaration",
    "arm_experiment_id",
    "declare_arms",
    "parse_arms",
]
