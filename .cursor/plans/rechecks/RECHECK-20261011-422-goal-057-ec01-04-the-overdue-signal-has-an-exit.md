---
id: RECHECK-20261011-422
slug: goal-057-ec01-04-the-overdue-signal-has-an-exit
title: 独立复检：GOAL-20261011-057 cycle 1（EC-01…EC-04）—— 超期信号的可注入出口
plan_id: PLAN-20261011-421
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-11
completed_at: 2026-10-11
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: packages/application/ports/nudge_sink.py（端口 + 静默缺省）
  - path: 独立重跑判据（新用例 8 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261011-057-press-two-way.txt
---

# RECHECK-20261011-422 — GOAL-20261011-057 cycle 1 独立复检

复检对象：`PLAN-20261011-421`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-nudge-exit.py` —— 五组读数与 GOAL 表逐条一致：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 出口面**零命中** | `NudgeSink` / `notify(` / `dispatch_notification` / `escalate` 在三个产品根**（零命中）** |
| 2 | 序 24 的产物**在树** | 「等太久了」2 处 + 「决定权仍在人」2 处（**都在**）|
| 3 | 同类 seam 的**形状** | `TelemetrySink` 方法 `['begin_operation','end_operation','record_metric']`；`NullTelemetrySink` 同名 + `calls` |
| 4 | 同类 seam 的**静默缺省** | `telemetry_sink.py:33`：「telemetry off 的默认实现(fail-open,零开销)」|
| 5 | **注入点** | `composition.py:136`：`telemetry: TelemetrySink = field(default_factory=NullTelemetrySink)` |

**一处**设计张力**（本探针读出来的，已在本轮落地时分辨）**：先例的 docstring 明写 **fail-open**
（「实现必须吞掉自身错误，不得把 exporter 失败传播到业务路径」）—— 那是**观测面**的口径
（丢掉可接受）。而本 GOAL 的纪律是**点名而非静默降级** ⇒ 两者**必须分辨**：
业务路径**不**因送失败而断，**但**失败**要被读出来**（写进被引事实）。

### 2. EC-02 端口与静默缺省（独立重跑）

`NudgeNotice` 的字段**逐个核对**：`program_id` / `run_id` / `index` / `waited_seconds` /
`declared_bound_seconds` —— **只有摘要**，**无** `content` / `prompt` / `token` / 凭据类字段
（§10 口径）。`NullNudgeSink.nudge` 是空操作且 `calls` 恒空（静默的**可复核证据**）。

### 3. EC-03 接线与只读纪律（独立重跑）

交付在**调用方那侧**（桥模块的 `_deliver_nudge`）；**只读判定面**（`program_waiting`）里
**没有** `.nudge(` 也**没有** `NudgeSink`（新用例逐条断言 —— 序 12/14 起的既有判据钉住这条）。
三态**互不混用**：未超期 / 未给时点 / 未声明界 ⇒ 不送；超期未注入 ⇒ 不送（**缺省不送**）；
超期注入 ⇒ 交端口，**成功与失败各留一条可读事实**（`nudge delivered` / `nudge not delivered`）。

### 4. EC-04 两向反证（独立重跑 `scratch/goal057_press.py`）

| 按压 | 读数 |
| --- | --- |
| **BASELINE**（未按压） | **GREEN**（8 passed） |
| `T-1` **缺省不送被改动**（缺省也送） | **RED**（1 failed） |
| `T-2` **超期不送** | **RED**（2 failed） |
| `T-3` **端口故障被静默**（异常被吞） | **RED**（1 failed） |
| `T-4` **只读判定面被塞进写方法** | **RED**（1 failed） |
| 复原 | 四条 `sha 复原一致=True`（二进制读写） |

归档：`.cursor/plans/goals/evidence/GOAL-20261011-057-press-two-way.txt`
（**657 B / 15 行 / `CR=0`** / `sha256 939ac49c8fa854a3…`）。

### 5. 四处规模门 / 参数门触顶（如实登记 —— **都是实测抓到的**）

| 门 | 逐字 | 处置 |
| --- | --- | --- |
| `max-args = 5` | `declared_gate_evaluation` / `_gate_result` 各 6 参 | 合出 `NudgeDelivery`（`index` + `clock` + `nudges`）|
| 文件 ≤ 450 行 | `program_runner.py … assert 455 <= 450` | 把「闸门那一支」搬进桥（`gate_outcome`）|
| 函数 ≤ 50 行 | `_evaluate` 55 / 61 行 | 抽 `_gated_outcome`（桥**返回纯元组** ⇒ 调用点构自己的值对象）|
| 严格 mypy | `Incompatible return value type (got "GateEvaluation", expected "_Evaluation")` | 同上一行：**桥不传 `dataclass`**（避免跨模块互转）|

**四处都选了「抽函数 / 换返回形态」而不是「放宽门禁」**（本 GOAL `forbidden` 的第一条）。

### 6. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | +/- | 改了什么 | 谓词比对 | 删除行读数 |
| --- | --- | --- | --- | --- |
| （**无**）| — | 本轮**未改任何既有判据文件** —— 改的都是**产品面**（新端口 / 桥 / 推进面），新用例是**新增文件** | — | `0` |

**射程分类（逐条）**：① 本轮**没有**改动既有判据断言；② **无一处收窄受判面**；
③ 产品面改动的后果面已由既有套件逐条核对（`tests/application tests/domain tests/api`
**3153 passed, 5 skipped**；`tests/architecture` **1486 passed**）。

### 7. 收口面（EC-05，待本轮随后回填）

收口验证器 + 断言集进树；两处射程纯收紧；两树复检 + 归档；as-is m0 23/23（记录写完之后）。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01…EC-04 逐条独立成立：勘察四组读数与 GOAL 表逐条一致
（含一处**设计张力**的读出与分辨）；端口只收摘要、缺省静默；交付在调用方侧且送失败**点名**；
四向反证**基线绿 + 全红 + 复原一致**；四处规模门 / 参数门触顶均以**抽函数**解决。

### Warnings

- **W-1（只有缝，没有真实外发）**：本轮给的是**进程内可注入的出口** ——
  **不**做邮件 / webhook / IM / 短信（**明确不做**），也**不**做**重试 / 去重 / 投递保证**
  （本 Port 只保证「信号**被交给**实现」，**不**保证送达）。**投递语义仍不是**「恰好一次」。
- **W-2（组合根尚未注入真实实现）**：`NudgeDelivery` 由调用方传；**产品路径（HTTP 推进路由）
  目前不注入**（⇒ 缺省静默）。**这是刻意的**（缺省逐字不变），但**点名**：控制面**还没有**
  一个真实出口接上 —— 接线位置与形状已就绪（`NudgeSink` + `NudgeDelivery`）。
- **W-3（升级链未做）**：往上级转派未做（`Z-3` 的第三半）。
- **W-4（`Z-1` 混合式仍未做）**：多点与条件式的**混合式**声明（第三种形态）未做。
- **W-5（承继残余原样保持）**：`W-2` 的内容级检测 / `CC-1`…`CC-3` / `BB-3` /
  `DD-1`…`DD-3` / `AA-*` / `Y-*` / `X-*` / `V-*` / `U-*` / `T-*` / `S-*` / `R-*` / `Q-*` /
  `P-*` / `O-1`…`O-5` / `R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
