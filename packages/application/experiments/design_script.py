"""`design_source="plan"` 的**脚本选择面**：计划可以从**出厂脚本白名单**里挑一个（GOAL-098）。

**它补哪一格**（本轮建档实测，不是推断）：`design_source="plan"` 到目前为止只让**臂与参数**
由计划派生 —— 而「跑哪个脚本」仍是装配常量。读面证据：`services/api/executor_wiring.py`
的 `DEFAULT_EXPERIMENT_SCRIPT` 是一个模块常量，`experiment_support.declared_or_assembled`
只在**契约 pin** 时改它（契约自己也是静态文件）⇒ 同一个方向换多少次，跑的都是
`exact_match_index_benchmark.py`。「实验由方向派生」因此只到**参数级**，没到**选择级**。

**本模块把选择级接上，但刻意只接一半**（用户 2026-10-27 已拍板走 (b)）：

- **走 (b)：白名单选择。** 计划在 `experiment_design.script` 里点一个**出厂已有**的脚本名，
  沙箱里跑的就是它；名字不在白名单里 ⇒ **点名拒绝**（列出白名单），**不**当成「没选」。
- **不走 (a)：模型写代码进容器。** 那会把「模型产出的任意 Python」变成执行面 —— 属安全面
  变更，`policy` / `classify_risk` / `EXECUTE` 类 HIGH 的既有门**没有**覆盖它（本轮的取值
  不是「门不够严」，而是「这类产物根本不在受判面里」）。⇒ 登记为下一轮待拍板的子项，
  见 GOAL 的 `U-*`。

**为什么「白名单」不是「回落」**：没有 `script` 键 ⇒ **逐字**回到装配面的既有语义
（零回归：本轮之前任何计划都能跑）。写了 `script` 但名字不认识 / 形态不对 / 想用绝对路径
⇒ **点名拒绝**，因为「计划点名了一个跑不了的脚本」与「计划没点名」是两件事，静默回落会
把前者伪装成后者。

**为什么路径必须精确**：白名单的键是**仓库相对路径**（如
`examples/experiments/sort_analysis_baseline.py`）。任一处不接受绝对路径、`..` 或别名，
因为脚本会被**复制进沙箱工作区**执行 —— 一个能指到白名单之外的路径选择面等于把
「选择」变成「任意文件执行」。

**确定性 / 零出网 / 零模型**：本模块只读计划制品里已经落库的那一个键，不建会话、
不发请求。臂与参数的解析仍归 `design_from_plan`（同一份设计块，一个解析器）。
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import PurePosixPath

from packages.application.experiments.design_from_plan import ExperimentDesignUnreadableError

#: 设计块里**脚本选择**那个键（与 `arms` 并列，同一个 `experiment_design` 对象里）。
SCRIPT_KEY = "script"

#: **出厂脚本白名单**（仓库相对路径 → 它测什么）。计划只能从这里面挑。
#:
#: 为什么是**闭集**而不是「仓库里所有 `.py`」：能被计划点名的脚本，就是能被一条模型写的
#: 正文**间接选定并执行**的脚本。闭集让这件事的范围在**目录声明**上就可见（改这个元组
#: 要改一次代码、过一次门），而不是「答案取决于仓库里此刻有哪些文件」。
SHIPPED_EXPERIMENT_SCRIPTS: tuple[str, ...] = (
    "examples/experiments/exact_match_index_benchmark.py",
    "examples/experiments/m12_reference_classification.py",
    "examples/experiments/sort_analysis_baseline.py",
)


def script_whitelist() -> frozenset[str]:
    """白名单的**只读**投影（判据与拒绝消息共用这一处，不各写一份）。"""
    return frozenset(SHIPPED_EXPERIMENT_SCRIPTS)


def declared_script(design: object, *, where: str) -> str | None:
    """设计块 → 计划点名的脚本路径（没写 ⇒ `None`；写了但非法 ⇒ 点名拒绝）。

    `design` 是 `design_from_plan.design_block_in` 读出来的那个对象（本模块**不**
    重新解析制品 —— 两个来源共用同一个解析器是既有纪律）。
    """
    if not isinstance(design, Mapping):
        # 设计块本身畸形由 `design_from_plan` 点名（它先跑）；到这里说明调用方传错了。
        raise ExperimentDesignUnreadableError(
            f"the experiment design in {where} is not an object "
            f"(got {type(design).__name__}); a script cannot be selected from it"
        )
    if SCRIPT_KEY not in design:
        return None
    raw = design[SCRIPT_KEY]
    if not isinstance(raw, str) or not raw.strip():
        raise ExperimentDesignUnreadableError(
            f"the {SCRIPT_KEY!r} entry in the experiment design of {where} must be a "
            f"non-empty repository-relative path (got {type(raw).__name__}); declare a "
            "path or omit the key to keep the assembled script"
        )
    candidate = raw.strip()
    _refuse_unsafe_path(candidate, where)
    allowed = script_whitelist()
    if candidate not in allowed:
        raise ExperimentDesignUnreadableError(
            f"the experiment design of {where} selects {candidate!r}, which is not a "
            f"shipped experiment script (allowed: {', '.join(sorted(allowed))})"
        )
    return candidate


def _refuse_unsafe_path(candidate: str, where: str) -> None:
    """绝对路径 / `..` / Windows 盘符 ⇒ 点名拒绝（**先于**白名单判定）。

    为什么单独一条：白名单比对已经能挡住这些（它们不在白名单里），但**拒绝理由**不同 ——
    「你写了一个越界的路径」与「你写了一个不在白名单里的名字」对调用方是两件事，而
    §9 的姿态是**点名**而不是含糊地拒绝。
    """
    pure = PurePosixPath(candidate.replace("\\", "/"))
    if pure.is_absolute() or ".." in pure.parts or (len(candidate) > 1 and candidate[1] == ":"):
        raise ExperimentDesignUnreadableError(
            f"the experiment design of {where} selects {candidate!r}, which is not a "
            "repository-relative path under the shipped experiment scripts "
            "(absolute paths, parent traversal and drive letters are refused)"
        )


def script_override(design: object, *, where: str, assembled: str | None) -> str | None:
    """计划点名的脚本 ∪ 装配面兜底（**计划优先**，没写 ⇒ 逐字回到装配面）。

    与 `experiment_support.declared_or_assembled` 的「声明优先、装配面兜底」**同一条**纪律：
    两个字段各自独立判。区别只在**谁**声明 —— 那里是**契约** pin（静态文件），这里是
    **本 run 的计划**（模型正文）。两者都在时契约仍赢（契约是更强的承诺，见
    `declared_or_assembled` 的 docstring）；本函数只处理「计划 vs 装配面」这一对。
    """
    selected = declared_script(design, where=where)
    return assembled if selected is None else selected


def selected_script_of(design: object, *, where: str, assembled: str | None) -> str | None:
    """`script_override` 的**只读**别名（读面/判据用；行为完全相同）。"""
    return script_override(design, where=where, assembled=assembled)


def plan_selected_script(
    assembly: object,
    task: object,
    *,
    contract: object | None = None,
    assembled: str | None,
) -> str | None:
    """派发体的**唯一选择点**：本 run 的脚本 = 契约 pin ∪ 计划选择 ∪ 装配面兜底。

    **优先级**（三档，强承诺在前）：

    1. **契约 pin 了脚本** ⇒ 用它（`declared_or_assembled` 的既有语义，逐字不变）；
    2. `design_source` 不是 `"plan"` ⇒ **逐字**回到 `assembled`（零回归：检索来源与
       装配面来源都**不**参与脚本选择，本轮不动它们的语义）；
    3. `design_source == "plan"` ⇒ 读本 run 的计划产物，看 `experiment_design.script`：
       没写 ⇒ `assembled`（**逐字**回到今天）；写了 ⇒ 白名单校验后用它。

    为什么要传 `contract` 而不是在调用方先判：契约是**静态文件**里的承诺，计划是**本 run
    的模型正文** —— 强弱不同，让「谁说了算」只有这一处（两处各判一次就会漂）。
    """
    declaration = getattr(contract, "experiment", None)
    script_pin = getattr(declaration, "script", "") if declaration is not None else ""
    if script_pin:
        return assembled
    if getattr(assembly, "design_source", None) != "plan":
        return assembled
    from packages.application.experiments.design_from_plan import plan_design_block

    artifact_id, design = plan_design_block(
        getattr(assembly, "artifacts"),
        getattr(assembly, "ledger"),
        run_id=str(getattr(getattr(task, "run_id"), "value")),
    )
    return script_override(design, where=artifact_id, assembled=assembled)


__all__ = [
    "SCRIPT_KEY",
    "SHIPPED_EXPERIMENT_SCRIPTS",
    "declared_script",
    "plan_selected_script",
    "script_override",
    "script_whitelist",
    "selected_script_of",
]
