---
id: RECHECK-20260928-224
slug: goal-023-ec03-recheck-scope-boundary
title: GOAL-023 EC-03 复检：受判射程边界是可复核的机械事实（起点 + 四条历史 + 计数；两向反证各判红一次）
plan_id: PLAN-20260928-223
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-28
completed_at: 2026-09-28
owners:
  - root-agent
---

# RECHECK-20260928-224 — GOAL-023 EC-03 复检

**复检口径**：不复用 PLAN 的叙述；每项给出**可复核观察面**；**未实跑的不记通过**。
本轮要证明的是：**边界**（不是记录质量）已经**可机械复核**，且**两个方向**都能判红。

## 检查结果

### 一、边界事实（实跑，非叙述）

| 观察 | 结果 |
| --- | --- |
| 受判起点（读既有判据的 `CUTOFF`） | `2026-09-28` |
| slug 约定 / 路数下界 | `closeout-recheck` / `2` |
| 扫描面（`slug` 以 `closeout-recheck` 结尾） | **5** |
| **射程内** | **1**：`RECHECK-20260928-218-goal-022-closeout-recheck.md` |
| **射程外** | **4**：`RECHECK-20260926-189-goal-018-closeout-recheck.md`、`RECHECK-20260926-195-goal-019-closeout-recheck.md`、`RECHECK-20260926-200-goal-020-closeout-recheck.md`、`RECHECK-20260927-210-goal-021-closeout-recheck.md` |

### 二、交付面与自洽门

| 观察 | 结果 |
| --- | --- |
| 新判据 | `tests/architecture/python/test_recheck_scope_boundary_is_mechanical.py`（**6 例**） |
| 落在 m0 收集面内 | **是**（`tests/**`）⇒ m0 条数**仍 23** |
| `ruff check` / `ruff format --check` / `mypy` | **全绿**（`mypy`：`Success: no issues found in 1 source file`） |
| 规模 | **192 行**；**无**超 50 行函数 |
| 定向套件 | 本判据 **6 passed**；与既有判据合跑 **15 passed** |

### 三、既有那条判据**逐字节未改**（形式硬约束）

```
git diff HEAD -- tests/architecture/python/test_declared_recheck_paths_have_evidence.py
```

结果**为空**。新判据**只读**它的公开面：`CUTOFF` / `CLOSEOUT_SLUG_SUFFIX` /
`MIN_DECLARED_PATHS` / `is_obligated` / `closeout_records`；且有一条用例断言这五个绑定值
没漂移（漂移即判红 ⇒ 边界不是「本判据自己另说一套」）。

### 四、反证两向（AC-3 / AC-4）

**hermetic（`tmp_path` 夹具，可反复复跑、不碰仓库）**

| 方向 | 夹具 | 结果 |
| --- | --- | --- |
| 基线 | 4 条历史（`2026-09-26`）+ 1 条新记录（`2026-09-28`） | `boundary_problems == []` |
| ① **backdate 逃逸** | 新记录改成 `2026-09-27` | **判红**，消息点名该文件 |
| ② **回填历史** | `…-189-goal-018-…` 改成 `2026-09-28` | **判红**，消息点名该文件 |

**仓库级（真实记录；按压 / 复原一律用 Edit 工具）**

| # | 按压 | 判据结果 | 复原（raw `sha256`） |
| --- | --- | --- | --- |
| ① | `RECHECK-20260928-218-goal-022-closeout-recheck.md`：`created_at` `2026-09-28` → `2026-09-27` | **`2 failed, 4 passed`** | 回到 `b46e551ffd4f83071c29cd5f5ce13dc11f1aae8e03129cea91580e2b9736edd9`（与按压前一致） |
| ② | `RECHECK-20260927-210-goal-021-closeout-recheck.md`：`created_at` `2026-09-27` → `2026-09-28` | **`1 failed, 5 passed`** | 回到 `b459e3a36dd1671fbd6bbb203dc152a25d5feecccd0ed4a35237eacce51a8ab7`（与按压前一致） |

**两条判据结论一致（交叉观察）**：按压 ② 状态下，**既有那条判据也同时判红**
（`test_no_obligated_closeout_recheck_has_a_declaration_gap`）—— 被回填的历史记录没有
`verify_paths`，所以「回填」同时违反**边界登记**与**质量义务**。这**不**意味着两条判据重叠：
边界判据**不读** `verify_paths`（见第五节），它只是在这个具体形态上给出同样的红。

**复原后**：两条判据合跑 **15 passed**；`git status --short .cursor/plans/rechecks/` **为空**
⇒ 历史 RECHECK **零回填**。

### 五、「只判边界，不判质量」以**行为**证明（AC-5）

| 观察 | 结果 |
| --- | --- |
| 一条**质量全坏**（frontmatter 没有 `verify_paths`、正文不引用任何证据）但**边界正确**的收口复检 | `boundary_problems == []`（**不判红**） |
| 判据源码是否引用质量侧谓词 | **不引用**（它只用 `is_obligated` 与 `closeout_records`） |

⇒ 本判据**不**冒充质量判据。射程内记录的实质质量仍由
`tests/architecture/python/test_declared_recheck_paths_have_evidence.py` 承载。

### 六、as-is 本机 m0（**记录写入之后**，承 MEM-145）

| 观察 | 结果 |
| --- | --- |
| 终态行 | `PASS: profile=m0; 23 deterministic checks`（退出码 `0`） |
| `PASS [` 行数 | **24**（`release-assets-immutable` 在计数之外） |
| 用例计数 | **4665 passed / 21 skipped**（较交付前 **+7** = 新判据 **6 例** + 新文件进入既有规模门判据的参数化面 **1 项**） |
| `FAILED` / `ERROR` | **零** |
| 日志与时刻 | `scratch/goal023-c3-m0.log`，文件时刻 `14:37:56` **晚于**本记录写入 `14:22:03` ⇒ 门在记录之后 |
| 进程卫生 | 跑完 `tasklist` python 进程 **0** |
| 治理 | `validate.py` = `Cursor 治理验证通过` |

### 七、本次复检**未**复核的面

- **边界是「今天」的事实**：`EXPECTED_OUT_OF_SCOPE` 是本轮实测后**写死在判据源码里**的四个
  文件名。将来新增的历史资产若也以 `closeout-recheck` 结尾且早于起点，会让这条判据判红 ——
  那是**有意的**（要求显式决定），但**不**等于「本仓所有历史收口复检都被穷尽识别」。
- **不判质量**：射程内记录写得对不对，本轮**未**复核（那是既有判据的事）。
- **`created_at` 是记录自述字段**：本判据把它当**声明的边界**来判，**不**校验它的真实性
  （例如与提交时间是否一致）。回填是「写下一个不同的日期」，不是「伪造时间戳」——
  **过程纪律**，**不是**对抗性控制。
- **跨平台**：全部实测在本机（Windows）。
- **历史遗留 `tools/` 脚本**：仍不受任何判据覆盖（`RECHECK-222` 的 `W-1`，收口需另行授权）。

## 结论

**PASS_WITH_WARNINGS。** 五条验收（AC-1…AC-5）**全部成立且有实跑证据**：
受判起点逐字 `2026-09-28`、射程外**恰好四条**历史收口复检（**逐条点名**）、射程内 **1** 条、
两集互斥；**两向反证**（hermetic 与仓库级各一轮）都**判红**且 `raw sha256` **逐字节复原**；
既有那条判据**逐字节未改**；「只判边界不判质量」以**行为**证明；
as-is m0 = `PASS: profile=m0; 23 deterministic checks`（在记录之后）；治理绿。
**零产品代码改动、零既有判据改动、零依赖、零历史回填。**

**警告（如实登记）**：

- **`W-1`**：`EXPECTED_OUT_OF_SCOPE` 是**本轮的实测快照写死在源码里**。它能把**后续变化**
  判红（多一条 / 少一条都会红），但**不**声称「本仓所有历史收口复检已被穷尽识别」——
  一个从未以 `closeout-recheck` 结尾命名的收口复检**不进扫描面**，本判据看不见。
- **`W-2`**：`created_at` 是**记录自述**字段。本判据判的是「**声明的**边界」，**不**校验日期
  的真实性（与提交时间是否一致）。这是**过程纪律**，**不得**据此宣称「边界不可伪造」。
- **`W-3`**：本判据**只判边界**。射程内记录的**实质质量**（路数是否各有留档、证据是否真的
  来自一次实跑）**不在**本判据的断言范围内 —— 由既有判据承载，且既有判据本身也只判
  「声明的路数 × 证据」这一层。
- **`W-4`**：按压用的是「改 `created_at`」这一种形态（Edit 做、逐字节复原）；
  **没有**做「把记录改名 / 删除」这类形态的按压（那会破坏 `closeout_records` 的扫描面）。
- **`W-5`**：本条复检**不含**任何授权面 / 认证面新结论。`W-10` / `W-11` / `W-12` 与
  `R-M1` **原样保留**；**不得**引作安全结论。

**未覆盖范围（承 GOAL-023 的边界，原样保留）**：读面未认证 / 多租户与 RBAC 未做 /
BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口（**不得**宣称项目安全）。
