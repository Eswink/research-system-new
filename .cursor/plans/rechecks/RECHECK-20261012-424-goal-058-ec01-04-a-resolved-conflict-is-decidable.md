---
id: RECHECK-20261012-424
slug: goal-058-ec01-04-a-resolved-conflict-is-decidable
title: 独立复检：GOAL-20261012-058 cycle 1（EC-01…EC-04）—— 被消解的冲突读得出来
plan_id: PLAN-20261012-423
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-12
completed_at: 2026-10-12
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: packages/domain/memory.py（`ConflictResolution` + `unresolved_conflicts`）
  - path: 独立重跑判据（新用例 8 + 3 + 1 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261012-058-press-two-way.txt
---

# RECHECK-20261012-424 — GOAL-20261012-058 cycle 1 独立复检

复检对象：`PLAN-20261012-423`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-conflict-resolution.py` —— 五组读数与 GOAL 表逐条一致：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 消解面**全零命中** | 五组标识符在 `packages/`·`adapters/` **（零命中）** |
| 2 | **改既有声明的路径全零命中** | 四组标识符**（零命中）** |
| 3 | 五态枚举**逐个读出** | `USE` / `ANNOTATE` / `SKIP` / `SUPERSEDED` / `CONFLICTED` —— **无**「已消解」 |
| 4 | 三个写路径**都不碰冲突维** | `deactivate_memory` / `delete_memory` / `supersede_memory` |
| 5 | 声明语义已收口（本轮**不动**） | 域上两个字段 + 非空字符串校验 |

### 2. EC-02 消解可记录（独立重跑）

`MemoryRecord.resolutions`（缺省空 ⇒ 既有行为**逐字不变**）+ `ConflictResolution`
（`other_id` / `resolved_by` / `resolved_at`）。四种坏形态**逐条点名**（域校验 +
存储层**双保险** —— 存储层用端口错误域 `InvalidInputError`）。**逐对消解**
（`unresolved_conflicts` 属性 —— 读面与处置面**同源**分派）。**SQLite 往返**（读-改-写；
重开连接后消解记载仍在；**声明一字不动**）。

### 3. EC-03 读面披露（独立重跑）

编排读面 `conflict_resolutions`（逐对：对端 id / 消解者 / 时点）+ HTTP 面
`MemoryConflictResolutionDto`（**同源同值** —— 两处逐项相等）。**未消解 ⇒ 逐字仍是
`CONFLICTED`**。**处置随未消解对分派**：`conflicted=bool(record.unresolved_conflicts)`
（**两处同口径**）。快照**同轮**重生成（`+32 / -0`，纯附加）。

### 4. EC-04 两向反证（独立重跑 `scratch/goal058_press.py`）

| 按压 | 读数 |
| --- | --- |
| **BASELINE**（未按压） | **GREEN**（11 passed） |
| `U-1` **未消解被判已消解**（conflicted 恒真） | **RED**（2 failed） |
| `U-2` **消解后被判未消解**（conflicted 恒假） | **RED**（1 failed） |
| `U-3` **声明被删除 / 改写**（披露把消解当声明清空） | **RED**（1 failed） |
| `U-4` **未知冲突对被接受**（重复对不拒 —— 受判面在 **Fake 的存储实现**） | **RED**（1 failed） |
| 复原 | 四条 `sha 复原一致=True`（二进制读写） |

归档：`.cursor/plans/goals/evidence/GOAL-20261012-058-press-two-way.txt`
（**714 B / 15 行 / `CR=0`** / `sha256 b6f292268323052e…`）。

### 5. 三处触顶 / 类型修正（如实登记 —— **都是实测抓到的**）

| 门 | 逐字 | 处置 |
| --- | --- | --- |
| 首轮替换**误伤了 `MemoryWriteProposal`**（把消解校验塞进提案） | `proposal contradictions must be…` 出现在提案校验里 | **revert 后用 Edit 工具精准落点**（跨类成对改动**不得**用宽锚替换）|
| `_record_dto` 撞 **50 行**（61 行） | 函数 ≤ 50 行 | 抽 `_time_and_linkage_fields` + `_resolution_dtos` |
| `**base` 展开 ⇒ mypy 6 个 arg-type | `dict[str, object]` 无法核对键名 | 走 **pydantic 校验入口**（`MemoryRecordDto.model_validate(base)`）|
| `PostgresMemoryStore` **不满足** `MemoryStore` 协议 | `Argument "memory"… expected "MemoryStore"` | `resolve_conflict` 一度落到**模块级** ⇒ 移回类内（**isinstance 复核** = True）|

**四处都选了「抽函数 / 精准落点 / 校验入口」而**不是**放宽门禁**（本 GOAL `forbidden` 的第一条）。

### 6. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | +/- | 改了什么 | 谓词比对 | 删除行读数 |
| --- | --- | --- | --- | --- |
| `tests/api/test_memory_api.py` | 见 `git diff --numstat` | `NEW_FIELDS` **+1**（`conflict_resolutions`）+ **新增同值用例 1** | **纯收紧**（受判形态未变；新增字段另有正证）| **0** |

**射程分类（逐条）**：① 属**同轮同步集**（新增字段若不同步进「既有字段集」会把**新键**
误报成「既有键被改」）；② **无一处收窄受判面**；③ 产品面改动的后果面已由既有套件核对
（`tests/{domain,adapters,application,api,contracts}` **4294 passed, 80 skipped**）。

### 7. 收口面（EC-05，独立重跑）

| 检查 | 读数 |
| --- | --- |
| 两个脚本在树 | \`tools/verify_goal058_closeout.py\` / \`tools/goal058_closeout_assertions.py\` |
| \`ruff\` / \`format\` / **全量 mypy** | 全绿（**1194 files** Success）|
| \`IN_SCOPE\` / \`_VERIFIERS\` **纯收紧** | \`+2\` / \`+1\` 行；判据全绿 |
| 收口验证器（本树）| **66 判词 / 0 FAIL** |
| 两树复检 | **\`TWO-TREE PASS\`**（两路 **66 判词** / \`sha256\` 相同 \`5916d15d8fb16a0e…\`）|
| 判词归档 | 两份各 **2517 B / 66 行 / \`CR=0\` / 0 FAIL** |
| 按压归档 | **714 B / 15 行 / \`CR=0\`** |
| 治理 / 宪章判据 | \`validate.py\` 通过；\`test_mainline_program_is_intact.py\` **8 passed** |
| **as-is m0** | **待收口轮实测回填**（记录写完之后、独占、仓库 \`.venv\`、不接管道）|

## 结论

**result: PASS_WITH_WARNINGS**。EC-01…EC-04 逐条独立成立：勘察五组读数与 GOAL 表逐条一致；
消解可记录且**声明一字不动**；两读面**同源同值**且**未消解逐字不变**；四向反证**基线绿 +
全红 + 复原一致**；四处触顶均以**抽函数 / 精准落点**解决。

### Warnings

- **W-1（只做「消解记载」，判定仍由人给）**：本 GOAL **不**做自动消解 ——「谁对谁错」
  **仍由人**消解；本轮只是让**那个决定**能被记录与读出。
- **W-2（PG 迁移需要手工执行）**：`023_memory_conflict_resolutions.sql` 已进树，但
  **既有 PG 实例**需要跑该迁移（`ADD COLUMN IF NOT EXISTS`，可重复执行）。
- **W-3（`W-2` 的内容级检测仍未做）**：本轮是 `CC-1` 的**记载侧**；「两条记忆的说法
  是否矛盾」**仍不可判定**（`detect_content_conflict` 仍零命中）。
- **W-4（承继残余原样保持）**：`Z-1`（混合式）/ `Z-3`（通知外发 / 升级链）/
  `CC-2`·`CC-3` / `BB-3` / `DD-1`…`DD-3` / `AA-*` / `Y-*` / `X-*` / `V-*` / `U-*` / `T-*` /
  `S-*` / `R-*` / `Q-*` / `P-*` / `O-1`…`O-5` / `R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
