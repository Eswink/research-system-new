---
id: RECHECK-20261011-420
slug: goal-056-ec01-04-the-waiting-face-has-a-start-point
title: 独立复检：GOAL-20261011-056 cycle 1（EC-01…EC-04）—— 等待面有始点、可催办（有界）
plan_id: PLAN-20261011-419
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-11
completed_at: 2026-10-11
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: packages/application/run_orchestration/program_waiting.py（`_elapsed_note` + `GateClock`）
  - path: 独立重跑判据（新用例 8 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261011-056-press-two-way.txt
---

# RECHECK-20261011-420 — GOAL-20261011-056 cycle 1 独立复检

复检对象：`PLAN-20261011-419`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-waiting-clock.py` —— 四组读数与 GOAL 表逐条一致：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 时限面**零命中** | `gate_timeout` / `gate_deadline` / `nudge` / `escalat` / `awaiting_since` / `wait_since` 在三个产品根**（零命中）** |
| 2 | `ApprovalRecord` **无时间字段** | 9 个字段逐个读出（`id`/`run_id`/`action`/`risk`/`context`/`policy_source`/`requested_event_id`/`status`/`version`）—— 时间类：**（无）** |
| 3 | 等待面点名句**不含时长** | 三处（`declared_gate_pending` ×2 + `waiting_round_decision`）都只点「等人拍板」+ 待审批 id |
| 4 | 三种闸门声明**语义已定** | 单点 / 条件式 / 多点逐行在位（本轮**不改**）|

### 2. EC-02 始点可读（独立重跑）

等待面判词加**已等待秒数**（`_elapsed_note`）。**不读挂钟**：两个时点都由**调用方**给
（`GateClock(now, waited_since)` 参数对象）⇒ 同一份记录 + 同一对时点 ⇒ 判词**必相同**。
**独立复核「不读挂钟」**：那个函数体里**没有** `Timestamp.now(`（用 AST/切片读，不按整文件搜 ——
后者会被同模块别的函数骗过）。

### 3. EC-03 超期可判定（独立重跑）

域字段 `gate_nudge_after_seconds`（缺省 `None` ⇒ **不催、不报超期** ⇒ 既有行为逐字不变）；
**与三种闸门声明正交** ⇒ **不参与互斥**。三态**互不混用**：未给时点 ⇒ 空串（**不猜**）；
给了时点未声明界 ⇒ 只报时长；声明了界 ⇒ 报时长 + **是否超期**（超 ⇒ **点名「等太久了」**
**且**写明**「决定权仍在人」**）。界必须**正整数**（零 / 负 ⇒ **点名拒绝**）。

### 4. EC-04 两向反证（独立重跑 `scratch/goal056_press.py`）

| 按压 | 读数 |
| --- | --- |
| **BASELINE**（未按压） | **GREEN**（8 passed） |
| `S-1` 始点**读不出**（不再报时长） | **RED**（4 failed） |
| `S-2` **超期不点名** | **RED**（2 failed） |
| `S-3` **未声明的界被改动**（未声明也催） | **RED**（1 failed） |
| `S-4` **坏界被接受**（零 / 负不拒） | **RED**（2 failed） |
| 复原 | 四条 `sha 复原一致=True`（二进制读写） |

归档：`.cursor/plans/goals/evidence/GOAL-20261011-056-press-two-way.txt`
（**660 B / 15 行 / `CR=0`** / `sha256 451f0848eb2f9a13…`）。

### 5. 规模门两度触顶（如实登记 —— **都是实测抓到的**）

| 门 | 逐字 | 处置 |
| --- | --- | --- |
| 文件 ≤ 450 行 | `program_runner.py 超过 450 行硬上限 / assert 462 <= 450` | 把「声明闸门 → 判定值」那一对**原样搬去** `program_gate_evaluation.py`（语义一字未动）⇒ 回到 416 行 |
| 函数 ≤ 50 行 | `program_runner.py 存在超过 50 行的函数: [('_evaluate', 55)]` | 把闸门那一支抽成 `_gate_branch`（语义未动）⇒ `program_runner.py` **444 行** |

**两次都选了「抽函数 / 抽模块」而不是「放宽门禁」**（这正是本 GOAL `forbidden` 的第一条）。
**另**：`max-args = 5` ⇒ 两个时点合成 `GateClock`、再与 `verdicts` 合成 `GateInputs`
（**兼容裸元组** ⇒ 既有调用点与判据**逐字不变**）；跨模块的 `dataclass` 不同形 ⇒
调用点**显式转换**（不让 mypy 接受两个不同 `dataclass`）。

### 6. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | +/- | 改了什么 | 谓词比对 | 删除行读数 |
| --- | --- | --- | --- | --- |
| （**无**）| — | 本轮**未改任何既有判据文件** —— 改的都是**产品面**（域 / 等待面 / 推进面 / 抽出模块），新用例是**新增文件** | — | `0` |

**射程分类（逐条）**：① 本轮**没有**改动既有判据断言；② **无一处收窄受判面**；
③ 产品面改动的后果面已由既有套件逐条核对（`tests/application/run_orchestration` **204 passed**；
`tests/{application,domain,api}` **1945 passed, 5 skipped**；`tests/architecture` **1486 passed**）。

### 7. 收口面（EC-05，独立重跑）

| 检查 | 读数 |
| --- | --- |
| 两个脚本在树 | `tools/verify_goal056_closeout.py` / `tools/goal056_closeout_assertions.py` |
| `ruff` / `format` / **全量 mypy** | 全绿（**1189 files** Success）|
| `IN_SCOPE` / `_VERIFIERS` **纯收紧** | `+2` / `+1` 行；判据全绿 |
| 收口验证器（本树）| **61 判词 / 0 FAIL** |
| 两树复检 | **`TWO-TREE PASS`**（两路 **61 判词** / `sha256` 相同 `ebc0ee1ee7182fa0…`）|
| 判词归档 | 两份各 **2263 B / 61 行 / `CR=0` / 0 FAIL** |
| 治理 / 宪章判据 | `validate.py` 通过；`test_mainline_program_is_intact.py` **8 passed** |
| **as-is m0** | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` **24** / `FAILED [` **0** / **5653 passed, 21 skipped** / `EXIT=0`；**独占**、仓库 `.venv`、不接管道、**在全部记录写完之后**）；日志 `scratch/m0-goal056-c3.log` — **+10 逐条归因**（8 + 1 + 1）|

**两轮真红（如实登记，不抹掉）**：第一轮 `1 failed` —— 三处既有断言因本轮抽出 `_gate_branch`
**假红**（`goal046` / `goal047` / `goal048`，逐字读数见 §5）；第二轮 `1 failed` ——
判据按关系修好后 `goal048` 的 `_ec03_verdicts` **撞 50 行门限** ⇒ 抽命名助手。
**两处都按「判关系 + 抽函数」解决，未放宽任何门禁**（这正是本 GOAL `forbidden` 的第一条）。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01…EC-04 逐条独立成立：勘察读数与 GOAL 表逐条一致；
始点**不读挂钟**且同一时点同结论；超期**只点名**（写明决定权仍在人）；四向反证**基线绿 +
全红 + 复原一致**；两处规模门触顶均以**抽函数**解决而**未**放宽门禁。

### Warnings

- **W-1（只做「时限信号」侧）**：本轮给出**可判定的信号**（等多久 / 是否超期），
  **不**做**通知外发**（邮件 / webhook / IM）与**升级链**（往上级转派）—— 那是 `Z-3` 的
  **另一半**，仍未做。
- **W-2（已接线，登记接线口径）**：产品路径（HTTP 推进路由）现在**传**那两个时点 ——
  `waited_since` = **最后一条 run 的 `updated_at`**（状态转移会刷新它 ⇒ 停在等待态的 run 上
  它就是**进入等待的时刻**）；`now` = **本请求到达的时刻**。
  **取不到就传 `None`**（**不猜、不编假时点**）⇒ 等待面此时报**不含时长**的既有判词。
  **一处口径边界（如实登记）**：`updated_at` 是「run 最后一次状态转移」的时刻 ——
  在**停在等待态**的 run 上它**就是**始点；但若某 run 在等待期间被**其它原因**改过
  （`with_manifest` / `with_protocol_source` 也会刷新它），那个时刻会**晚于**真正进入等待的时刻
  ⇒ 报出的时长**偏短**（**不**偏长，**不**会假报超期之外的错），且**不**静默（时长照报）。
- **W-3（`Z-1` 的混合式仍未做）**：多点与条件式的**混合式**声明（第三种形态）未做。
- **W-4（承继残余原样保持）**：`W-2` 的内容级检测 / `CC-1`…`CC-3` / `BB-3` /
  `DD-1`…`DD-3` / `AA-*` / `Y-*` / `X-*` / `V-*` / `U-*` / `T-*` / `S-*` / `R-*` / `Q-*` /
  `P-*` / `O-1`·`O-3`·`O-4`·`O-5` / `R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
