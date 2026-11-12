"""实验脚本的**执行权威**与策略约束的执行面（GOAL-20261107-107 EC-09 / EC-10）。

**它补哪两格**（都是实测出来、不是推断的）：

1. **脚本来源只有「选择级」**：`experiments/design_script.py:47-51` 把实验脚本钉在**3 个
   出厂文件**的白名单上，`plan_selected_script` 只允许「从闭集里点名一个」。北极星要求的
   「为新问题设计实验」因此停在选择级 —— 模型产出脚本（`AUTHORED`）根本没有承载它的类型。

2. **策略约束声明了但零处执行**（更严重，且与脚本来源独立）：`policy/native.py` 的
   `evaluate` 把 `allow_with_constraints` 规则的 `constraints` **原样返回**，而全仓**没有
   任何消费方**读它 —— `sandbox_required` / `path_prefix` / `max_seconds` 三条声明因此在
   执行边界上**不存在**。`governed._enforce_policy` 只对 `decision` 分支，不看约束。

**本模块做什么**：

* `ExecutionAuthority` 闭集：`SHIPPED`（仓库里的出厂脚本 + digest pin）| `AUTHORED`
  （模型产出）。`authority_for` 判定一次执行属于哪一面。
* `check_constraints`：把 `PolicyEvaluation.constraints` 落成**可执行**的判定 ——
  无沙箱 / 越界路径 / 超时 / digest 不匹配各**点名拒绝**。

**本模块不做什么**（射程边界）：

* **不打开 `AUTHORED`**。`AUTHORED_ALLOWED_BY_DEFAULT = False`；要放行必须由调用方显式
  传 `authored_allowed=True`。出厂行为与改动前**逐字节相同**（白名单三条）。
* **不改任何策略规则文件**。只让既有声明生效 —— 改规则文件是另一件事（且属安全姿态面）。
* **不判「脚本写得好不好」**。权威判的是**来源与形状**，不是质量。
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

#: 出厂脚本的**闭集**（与 `design_script.SHIPPED_EXPERIMENT_SCRIPTS` 同一份名单）。
#: 本模块**不重复维护**它 —— 由 `shipped_scripts()` 从那个模块取，避免两份清单漂移。
SHIPPED = "SHIPPED"
#: 模型产出的脚本。
AUTHORED = "AUTHORED"

#: `AUTHORED` 是否**默认**放行。`False` = 出厂行为不变（白名单三条）。
#: 打开它是一次**安全姿态决定**，不是配置调优 —— 因此这里不读环境变量。
#:
#: **GOAL-20261111-112 EC-04：这一行逐字不动。** 本轮交付的是「可启用的那张网」：
#: 放行口是下面那个**具名安全 profile**，而不是把这个常量改成 `True`。
AUTHORED_ALLOWED_BY_DEFAULT = False

#: **具名安全 profile**：唯一能放行 `AUTHORED` 的显式声明（与序 76 的开关同形态）。
#:
#: 语义：`RESEARCHOS_AUTHORED_SAFETY_PROFILE` **恰好等于**这个名字 ⇒ 该进程内可显式
#: 传 `authored_allowed=True`；任何其它取值（含 `1` / `true`）⇒ **不**放行。
#: 与 `RESEARCHOS_LIVE_E2E` 同一条纪律：**值必须一眼判**，不做真值解析。
#:
#: **它不改变缺省**：即使 profile 在场，`authored_allowed=None` 仍取
#: `AUTHORED_ALLOWED_BY_DEFAULT`（`False`）。profile 只是让「显式传 True」这件事
#: 在一个**具名**的运维模式下有意义 —— 调用方仍要显式传。
AUTHORED_SAFETY_PROFILE = "authored-experiments-v1"

#: 策略约束里本模块认识的三个键（其余键**原样忽略**，不猜语义）。
SANDBOX_KEY = "sandbox_required"
PATH_PREFIX_KEY = "path_prefix"
MAX_SECONDS_KEY = "max_seconds"


class AuthorityError(ValueError):
    """一次执行**不允许**（来源 / 约束不成立）—— 点名，不静默降级。"""


class ExecutionAuthority(StrEnum):
    """脚本的来源面（闭集）。"""

    SHIPPED = SHIPPED
    AUTHORED = AUTHORED


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    """一次实验脚本执行**要过权威面**的事实（全部由调用方给，本模块不读盘猜）。"""

    #: 脚本路径（仓库相对或绝对，`shipped` 面要求命中闭集里的某一条）。
    script_path: str
    #: 脚本字节的 `sha256`（`sha256:<hex>` 或裸 hex 都认）。
    digest: str
    #: 是否声明为模型产出（`False` ⇒ 必须命中出厂闭集）。
    authored: bool = False
    #: 执行期声明的约束（来自 `PolicyEvaluation.constraints`）。
    constraints: Mapping[str, object] | None = None
    #: 实际要写的路径（与 `path_prefix` 比对；缺省 = 不声明写入）。
    write_path: str | None = None
    #: 声明的执行秒数上限（与 `max_seconds` 比对；缺省 = 不声明）。
    requested_seconds: float | None = None
    #: 是否真的在沙箱里执行（与 `sandbox_required` 比对）。
    sandboxed: bool = False


def authored_profile_declared() -> bool:
    """本进程是否处在**具名**的 `authored` 安全 profile 下（缺省 `False`）。"""
    import os

    return os.environ.get("RESEARCHOS_AUTHORED_SAFETY_PROFILE", "").strip() == (
        AUTHORED_SAFETY_PROFILE
    )


def shipped_scripts() -> tuple[str, ...]:
    """出厂脚本闭集（从 `design_script` 取，**不在本模块复制**）。"""
    from packages.application.experiments.design_script import SHIPPED_EXPERIMENT_SCRIPTS

    return tuple(SHIPPED_EXPERIMENT_SCRIPTS)


def normalized_digest(digest: str) -> str:
    """`sha256:<hex>` 与裸 hex 归一成裸 hex（比较前用）。"""
    return digest.split(":", 1)[-1].strip().lower()


def digest_of(path: Path) -> str:
    """文件字节的 `sha256`（裸 hex）。**只有调用方明确要验盘时才用**（本模块其余部分纯函数）。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authority_for(
    request: ExecutionRequest, *, authored_allowed: bool | None = None
) -> ExecutionAuthority:
    """这次执行属于哪一面；不允许 ⇒ **点名拒绝**。

    `authored_allowed is None` ⇒ 取 `AUTHORED_ALLOWED_BY_DEFAULT`（出厂 `False`）。
    """
    allowed = AUTHORED_ALLOWED_BY_DEFAULT if authored_allowed is None else authored_allowed
    if request.authored:
        if not allowed:
            raise AuthorityError(
                "model-authored experiment scripts are not enabled: this round builds the "
                "mechanism, and turning AUTHORED on is a security-posture decision, not a "
                "configuration tweak"
            )
        # GOAL-20261111-112 EC-04：显式放行还不够 —— 必须处在**具名**安全 profile 下。
        # 两道门是两件事：`authored_allowed` 是调用方的意图，profile 是**运维模式**。
        if not authored_profile_declared():
            raise AuthorityError(
                "model-authored scripts require the named safety profile: set "
                f"RESEARCHOS_AUTHORED_SAFETY_PROFILE={AUTHORED_SAFETY_PROFILE!r} "
                "(exact value) for the process that runs them"
            )
        return ExecutionAuthority.AUTHORED
    script = request.script_path.replace("\\", "/")
    if script not in shipped_scripts():
        raise AuthorityError(
            f"experiment script {request.script_path!r} is not one of the shipped scripts: "
            f"{list(shipped_scripts())}"
        )
    return ExecutionAuthority.SHIPPED


def check_constraints(
    request: ExecutionRequest, *, authored_allowed: bool | None = None
) -> ExecutionAuthority:
    """权威 + 策略约束**一起**判；任一不成立 ⇒ `AuthorityError`（点名缺哪条）。

    四条检查（顺序固定，判词稳定）：

    1. **来源**（`authority_for`）：白名单命中 / `AUTHORED` 是否被放行。
    2. **digest pin**：`SHIPPED` 面要求 `digest` 非空（形状对得上）；空摘要 = 没有 pin。
    3. `sandbox_required: true` ⇒ `request.sandboxed` 必须为真。
    4. `path_prefix` ⇒ 声明的写入路径必须以它为前缀（`..` 一律拒，不管前缀）。
    5. `max_seconds` ⇒ 声明的执行秒数不得超它。

    **约束缺席 = 不检查那一条**（不发明默认值）：`sandbox_required` 没声明就不要求沙箱，
    这正是「让既有声明生效」而不是「新加一条策略」。
    """
    authority = authority_for(request, authored_allowed=authored_allowed)
    digest = normalized_digest(request.digest)
    if authority is ExecutionAuthority.SHIPPED and not digest:
        raise AuthorityError(
            f"shipped script {request.script_path!r} carries no digest: without a pin the bytes "
            "that run are not the bytes that were reviewed"
        )
    # GOAL-20261111-112 EC-01：三条约束的**判定**来自唯一一张表
    # （`experiments/constraint_table.py`）——本处只把违反落成 `AuthorityError`。
    # 工具面与 preflight 调**同一张表**，因此三面对同一条声明的结论不会漂。
    from packages.application.experiments.constraint_table import violations

    found = violations(
        request.constraints,
        sandboxed=request.sandboxed,
        write_path=request.write_path,
        requested_seconds=request.requested_seconds,
    )
    if found:
        raise AuthorityError("; ".join(item.describe() for item in found))
    return authority


def describe_authority(authority: ExecutionAuthority) -> Mapping[str, Any]:
    """读面形态（`Artifact.created_by` / 证据登记用）。"""
    return {
        "authority": str(authority),
        "authored_allowed_by_default": AUTHORED_ALLOWED_BY_DEFAULT,
    }


__all__ = [
    "AUTHORED",
    "AUTHORED_ALLOWED_BY_DEFAULT",
    "AUTHORED_SAFETY_PROFILE",
    "authored_profile_declared",
    "MAX_SECONDS_KEY",
    "PATH_PREFIX_KEY",
    "SANDBOX_KEY",
    "SHIPPED",
    "AuthorityError",
    "ExecutionAuthority",
    "ExecutionRequest",
    "authority_for",
    "check_constraints",
    "describe_authority",
    "digest_of",
    "normalized_digest",
    "shipped_scripts",
]
