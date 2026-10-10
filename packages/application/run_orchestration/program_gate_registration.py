"""**声明闸门的注册面**（GOAL-20261010-047 EC-02）。

**为什么单列**（与 `phase_pause.py` 之于 `phase_runner.py` 同一手法）：判定面
（`program_waiting.py`）是**只读**的 —— 它回答「这条闸门现在是否仍在等人拍板」，
**不**写任何审批状态。注册是**有副作用**的另半件事：往既有 `ApprovalStore` 里放一条待决记录，
使这条闸门**可被裁决**。两件事的判据不同（只读面被判据钉住不得出现写方法），
所以实现分列；`program_runner` 先注册、再判。

**与 phase 面的关系**：语义**同源可对照**（`phase_pause.pause_for_human_gate` 注册
`risk="HUMAN_GATE"` 的 `ApprovalSpec`），但 `action` 用**本模块自己的前缀** ——
裁决面的准入条件不同（程序闸门允许 run 已终态，见 `services/api/approvals.py`），
混用前缀会让两种语义互相串台。
"""

from __future__ import annotations

from typing import Any

from packages.application.ports.approval_store import ApprovalSpec
from packages.application.run_orchestration.program_waiting import declared_gate_trigger

#: 审批读取 / 写入面（`ApprovalStore` 的形状）。
ApprovalFace = Any

#: 程序级闸门的 `action` 前缀。**必须**与裁决面（`services/api/approvals.py`）同源 ——
#: 那边 import 本常量，两处各写一份字面量会静默串台。
PROGRAM_GATE_ACTION = "program-gate:"
#: `policy_source`（让审批记录**自证**它是谁注册的）。
PROGRAM_GATE_POLICY_SOURCE = "program-gate"


def register_declared_gate(
    program: Any,
    last_index: int,
    approvals: ApprovalFace | None,
    run_id: str,
    verdicts: tuple[str, ...] = (),
) -> tuple[str | None, str | None]:
    """为**触发中的**声明闸门注册一条待决审批；返回 `(审批标识 | None, 点名句 | None)`。

    `(None, None)` = **不需要注册**（未声明 / 未触发 / 已有该闸门的记录 ⇒ 幂等命中）。
    `(None, <点名句>)` = **该注册却注册不了**（缺审批面、面只读、查询失败、注册失败）。

    **触发**由 `program_waiting.declared_gate_trigger` 判（**单一来源**）：序号声明（序 14）
    或**条件声明**（GOAL-20261010-048：上一轮落库判词命中声明的取值集合）。本函数只负责
    「触发之后把等待项放进审批面」这半边。

    语义与 phase 面（`phase_pause.pause_for_human_gate`）**逐字段可对照**：
    `risk="HUMAN_GATE"`、`policy_source` 同名、`context` 换成程序侧的轮次标识、
    `requested_event_id=""`（与 phase 面同一处留空理由）。

    **幂等**：查 `list_for_run` 里**同 action** 的记录 —— 已有（无论待决或已裁决）即视为
    **已注册**，不再新增（重复推进不得堆积待决记录，否则「等人拍板」会堆成一串）。
    """
    if declared_gate_trigger(program, last_index, verdicts) is None:
        return None, None
    write_face = _open_write_face(approvals, run_id, f"{PROGRAM_GATE_ACTION}{program.id}")
    if isinstance(write_face, str):
        return None, write_face
    register, already = write_face
    if already:
        return None, None  # 幂等命中：已有该闸门的记录（待决或已裁决）⇒ 不重复注册
    try:
        record = register(
            ApprovalSpec(
                run_id=run_id,
                action=f"{PROGRAM_GATE_ACTION}{program.id}",
                risk="HUMAN_GATE",
                context=f"program-round:{last_index}",
                policy_source=PROGRAM_GATE_POLICY_SOURCE,
                requested_event_id="",
            )
        )
    except Exception as error:  # noqa: BLE001 - 注册失败必须**点名**（不静默当成已注册）
        return None, f"（注册失败：{type(error).__name__}: {error}）"
    return str(getattr(record, "id", "")) or None, None


def _open_write_face(
    approvals: ApprovalFace | None, run_id: str, action: str
) -> tuple[Any, bool] | str:
    """注册前的四道检查；返回 `(register 可调用对象, 是否已有同 action 的记录)` 或**点名句**。

    四个失败形态各自**点名**（缺面 / 面只读 / 查询失败 / 已有记录 ⇒ 幂等命中**不是**失败，
    故与前三者分开返回）：把「该注册却注册不了」与「不需要注册」**在类型上**区分开，
    免得调用方把幂等命中当成故障。抽出成函数是为了守住 **50 行上限**（注册本体此前 51 行）。
    """
    if approvals is None:
        return "（尚无可注册的审批面）"
    register = getattr(approvals, "register", None)
    if not callable(register):
        return "（该审批面**只读**，无法注册等待项）"
    try:
        rows = approvals.list_for_run(run_id)
    except Exception as error:  # noqa: BLE001 - 注册前的查询失败必须**点名**
        return f"（注册前查询失败：{type(error).__name__}: {error}）"
    already = any(str(getattr(row, "action", "")) == action for row in rows)
    return register, already


__all__ = ["PROGRAM_GATE_ACTION", "PROGRAM_GATE_POLICY_SOURCE", "register_declared_gate"]
