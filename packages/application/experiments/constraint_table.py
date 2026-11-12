"""三条实验策略约束的**唯一判定表**（GOAL-20261111-112 EC-01，`W-4` 的收口）。

**它补哪一格**：GOAL-107 让 `sandbox_required` / `path_prefix` / `max_seconds` 在
**实验执行边界**（`script_authority.check_constraints`）生效了，但同一条声明在
`tool_plane/resolver` 里**被丢掉**（注释写着「解析面等价放行」）、在
`preflight/policy_check` 里**只被复述**（`", ".join(sorted(...))`）⇒ 同一个声明
三个执行面效力不一致。

**本模块做什么**：把三键的**键名 / 类型 / 违反时的点名**收成唯一一份纯函数
（`validate` / `violations`），让三处都调它。

**它不做什么**（射程边界，逐条写明）：

- **不新造约束**。前三键与 GOAL-107 逐字相同；第四键（`requires_workspace_lease`）
  是**出厂策略文件里早已声明**的，本轮只做形状校验（见该常量上的说明）。
- **不实现第四键的执行语义**。`requires_workspace_lease` 要「租约是否已持有」这个事实，
  实验执行边界拿不到 —— 假装判它会是假绿。它的执行面留给后续轮次。
- **不发明默认值**。约束缺席 = 不检查那一条（「让既有声明生效」而不是「新加策略」）。
- **不判脚本质量**。判的是**声明形状**与**执行事实**的符合性。
- **不做 I/O、不读环境**。纯函数；谁在什么面调用由调用方决定。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

#: **四个**键。前三个（`sandbox_required` / `path_prefix` / `max_seconds`）是 GOAL-107
#: 让其在实验执行边界生效的那三条；第四个 `requires_workspace_lease` 是**真实
#: `policy.yaml` 里早已声明**的一条（`examples/config/policy.yaml` 的 `workspace.write.code`）
#: —— 它此前同样**零处执行**（全仓除该 YAML 外零命中）。
#:
#: **为什么把它加进来而不是判它「未知」**：本轮的判据是「同一张表三面对齐」，
#: 不是「重新发明合法约束集」。一条**出厂策略文件里写着**的键被判成「非法」会让真实
#: 控制面 preflight 直接 FAIL（实测：`policy_surface_consistency` 三条判据当场红）——
#: 那不是收紧，那是把既有声明打成错误。它在这里被**形状校验**（`bool`），
#: 但**本轮不实现它的执行语义**（见模块 docstring 的射程边界）。
SANDBOX_KEY = "sandbox_required"
PATH_PREFIX_KEY = "path_prefix"
MAX_SECONDS_KEY = "max_seconds"
WORKSPACE_LEASE_KEY = "requires_workspace_lease"

#: 键 → 期望的声明类型（`bool` 单独列出：`int` 是 `bool` 的父类，顺序要紧）。
EXPECTED_TYPES: Mapping[str, tuple[type, ...]] = {
    SANDBOX_KEY: (bool,),
    PATH_PREFIX_KEY: (str,),
    MAX_SECONDS_KEY: (int, float),
    WORKSPACE_LEASE_KEY: (bool,),
}

#: 闭集（新增键必须同轮改这里 + 三处消费点；判据钉住「三处都调本模块」）。
CONSTRAINT_KEYS: tuple[str, ...] = (
    SANDBOX_KEY,
    PATH_PREFIX_KEY,
    MAX_SECONDS_KEY,
    WORKSPACE_LEASE_KEY,
)

#: **本轮有执行语义**的键（其余键只过形状）。`requires_workspace_lease` 的执行面
#: 需要「租约是否已持有」这个事实 —— 实验执行边界拿不到它，因此**不**在这里假装判。
ENFORCED_KEYS: tuple[str, ...] = (SANDBOX_KEY, PATH_PREFIX_KEY, MAX_SECONDS_KEY)


@dataclass(frozen=True, slots=True)
class ConstraintViolation:
    """一条约束被违反（或声明形状不合法）——**可判依据**逐字可读。"""

    key: str
    reason: str

    def describe(self) -> str:
        return f"{self.key}: {self.reason}"


def shape_violations(constraints: Mapping[str, object] | None) -> tuple[ConstraintViolation, ...]:
    """**声明面**的形状检查（未知键 / 类型错）；空声明 ⇒ 无违反。

    这一支三面共用：工具面与 preflight 拿到的往往只是**声明**（没有执行事实），
    它们能判的就是形状。
    """
    if not constraints:
        return ()
    problems: list[ConstraintViolation] = []
    for key, value in sorted(constraints.items()):
        expected = EXPECTED_TYPES.get(key)
        if expected is None:
            problems.append(
                ConstraintViolation(
                    key=key,
                    reason=f"unknown constraint key; the closed set is {list(CONSTRAINT_KEYS)}",
                )
            )
            continue
        # `bool` 不能冒充 `int`：`max_seconds: true` 是声明错误，不是「1 秒」。
        if isinstance(value, bool) and bool not in expected:
            problems.append(
                ConstraintViolation(key=key, reason=f"expected {_names(expected)}, got bool")
            )
            continue
        if not isinstance(value, expected):
            problems.append(
                ConstraintViolation(
                    key=key, reason=f"expected {_names(expected)}, got {type(value).__name__}"
                )
            )
    return tuple(problems)


def _names(types: tuple[type, ...]) -> str:
    return "|".join(item.__name__ for item in types)


def is_well_formed(constraints: Mapping[str, object] | None) -> bool:
    """声明面是否合法（三面共用的一条判据；`False` ⇒ 调用方点名拒绝）。"""
    return not shape_violations(constraints)


def violations(
    constraints: Mapping[str, object] | None,
    *,
    sandboxed: bool = False,
    write_path: str | None = None,
    requested_seconds: float | None = None,
) -> tuple[ConstraintViolation, ...]:
    """**执行面**的完整判定：形状 + 三条约束各自的实际符合性。

    顺序固定（形状 → 沙箱 → 路径 → 超时），判词因此稳定；任一条成立即被点名。
    **约束缺席 = 不检查那一条**（不发明默认值）。
    """
    problems = list(shape_violations(constraints))
    if problems or not constraints:
        return tuple(problems)
    if constraints.get(SANDBOX_KEY) is True and not sandboxed:
        problems.append(
            ConstraintViolation(
                key=SANDBOX_KEY,
                reason="policy requires a sandbox but the execution is not sandboxed",
            )
        )
    prefix = constraints.get(PATH_PREFIX_KEY)
    if isinstance(prefix, str) and prefix:
        problems.extend(_path_violations(prefix, write_path))
    limit = constraints.get(MAX_SECONDS_KEY)
    if isinstance(limit, (int, float)) and not isinstance(limit, bool):
        if requested_seconds is not None and float(requested_seconds) > float(limit):
            problems.append(
                ConstraintViolation(
                    key=MAX_SECONDS_KEY,
                    reason=f"requested {requested_seconds}s exceeds the policy limit of {limit}s",
                )
            )
    return tuple(problems)


def _path_violations(prefix: str, write_path: str | None) -> list[ConstraintViolation]:
    """`path_prefix`：必须声明写入路径、不得向上越界、必须在声明前缀下。"""
    if write_path is None:
        return [
            ConstraintViolation(
                key=PATH_PREFIX_KEY,
                reason=f"policy requires writes under {prefix!r} but no write path is declared",
            )
        ]
    normalized = write_path.replace("\\", "/")
    if ".." in Path(normalized).parts:
        return [
            ConstraintViolation(
                key=PATH_PREFIX_KEY,
                reason=f"write path {write_path!r} escapes upward (..), which no prefix permits",
            )
        ]
    if not normalized.startswith(prefix.replace("\\", "/")):
        return [
            ConstraintViolation(
                key=PATH_PREFIX_KEY,
                reason=f"write path {write_path!r} is outside the policy prefix {prefix!r}",
            )
        ]
    return []


def digest_violation(expected: str, actual: str) -> ConstraintViolation | None:
    """`digest pin`：期望与实际的裸 hex 不等 ⇒ 点名（`None` = 相符）。"""
    want = expected.split(":", 1)[-1].strip().lower()
    got = actual.split(":", 1)[-1].strip().lower()
    if want and got and want == got:
        return None
    return ConstraintViolation(
        key="digest",
        reason=f"script bytes changed: expected {want or '<none>'}, got {got or '<none>'}",
    )


__all__ = [
    "CONSTRAINT_KEYS",
    "ENFORCED_KEYS",
    "WORKSPACE_LEASE_KEY",
    "ConstraintViolation",
    "EXPECTED_TYPES",
    "MAX_SECONDS_KEY",
    "PATH_PREFIX_KEY",
    "SANDBOX_KEY",
    "digest_violation",
    "is_well_formed",
    "shape_violations",
    "violations",
]
