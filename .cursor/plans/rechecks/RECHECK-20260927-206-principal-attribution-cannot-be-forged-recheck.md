---
id: RECHECK-20260927-206
slug: principal-attribution-cannot-be-forged-recheck
title: GOAL-021 cycle 3（EC-03）独立复检：自报不可生效 + 读面基线 + 顺序形态可判红（4 failed）+ 逐字节复原
plan_id: PLAN-20260927-205
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-27
completed_at: 2026-09-27
owners:
  - root-agent
---

# RECHECK-20260927-206 — 主体归因不可伪造（GOAL-021 EC-03）

## 检查结果

**复检口径**：不复用 PLAN / GOAL 的结论叙述；每一项给出**可复核观察面**
（命令、文件、sha256、实测输出）。**未实跑的不记通过**。

### 一、最要紧的发现：`TestClient` 会让本 EC 的判据**不可证伪**（先红后绿的关键）

**复检动作**：把 `PrincipalAuthMiddleware` 的 `finally: reset_current_principal(token)`
换成 `pass`（等价于删掉复原），**分别**用两种驱动跑判据。

| # | 驱动形态 | 基线（有 reset） | 按压（去掉 reset） | 可证伪？ |
| --- | --- | --- | --- | --- |
| 1.1 | `TestClient`（同步 portal） | `read=None` | **`read=None`** | **否**（假绿） |
| 1.2 | `httpx.ASGITransport` + **同任务 `await`** | `read=None` | **`read=service:probe-principal`** | **是** |
| 1.3 | 说明 | `TestClient` **每个请求在自己的任务里跑** ⇒ 请求内 `contextvar` 的 set 不回传给调用方 ⇒ 「写请求主体残留给下一个读请求」这一现象**在该驱动下不可见** | | |

**处置**：判据**全部改走 `ASGITransport` + 同任务 `await`**（`_BASE_URL` 为不触网的虚拟基址）。
**若不改**：本 EC 会交付一组**永远绿**的判据 —— 那正是「判据自身恒真」（MEM-141）要求排除的情形。
**取证脚本**：`scratch/goal021-ec03-probe-driver-shape.py`（三层输出：基线 / 按压 / 复原）。

### 二、自报不可生效（EC-03(a)）

| # | 观察 | 结果 |
| --- | --- | --- |
| 2.1 | 带对 token + 自报头（`X-Principal-Id` / `X-Actor` / `X-Principal`） | 主体**仍是** `service:forge-probe`（自报头**无效**） |
| 2.2 | 带对 token + query（`?principal_id=attacker&actor=user:attacker`）+ body 字段 | 主体**仍是**配置主体 |
| 2.3 | 真实控制面：带自报头的 `POST /projects` | 照常 **201**（请求成功，但主体**不变**——身份只能来自配置） |
| 2.4 | **机制**：`ControlPlaneAuth.principal` 由**配置字段**推导 | 主体构造**不读请求**；换 `principal_id` 只影响配置侧（`ServicePrincipal` 语义） |
| 2.5 | `Principal` **字段集** | 恰为 `{id, kind}` —— **无** tenant / organization / role / scopes（**M18 边界**为机械事实） |
| 2.6 | `Principal(id="evil:user:admin")` | **抛 ValueError**（id 不得含 `:`，否则 actor 的类型 / 标识切分有歧义） |

### 三、读面基线与不串（EC-03(b)(c)）

| # | 观察 | 结果 |
| --- | --- | --- |
| 3.1 | **在前有一个写请求**，随后不带 token 的读请求 | 读请求主体 `None`（不被前一个写请求污染） |
| 3.2 | 认证**关闭** | 写 / 读均放行且主体 `None`（「无认证」不是「已认证」） |
| 3.3 | 被拒的写请求（401）之后 | 读请求主体 `None`（不能「拒了但归因已生效」） |
| 3.4 | 连续 **5 个**写请求之后 | 读请求仍 `None`（复原是真的，不是一次性的） |
| 3.5 | 写 / 读**交替 4 轮** | 每个写看到主体、每个读看到 `None` |
| 3.6 | 真实 app 的读请求之后 | `current_principal()` 为 `None`（无残留） |
| 3.7 | 并发（**前提：父上下文干净**）40 个读写混发 | **0 violations** —— **仅**说明「本形态下未观察到污染」，**不**作并发安全结论（见 W-1） |

### 四、反证（先红后绿，逐字节复原）

**复检动作**：把 `finally: reset_current_principal(token)` 换成 `pass`，跑判据，再复原。

| # | 观察 | 结果 |
| --- | --- | --- |
| 4.1 | 修好驱动形态**之后**按压 | **4 failed, 11 passed** —— 红的正是四条**顺序形态**判据：`test_a_read_after_a_write_sees_no_subject` / `test_a_series_of_writes_then_a_read_leaves_no_residue` / `test_alternating_write_read_keeps_each_request_isolated` / `test_a_write_then_a_read_in_one_task_is_observably_ordered` |
| 4.2 | 修好驱动形态**之前**按压（首版 `TestClient` 版） | **14 passed（未红）** ⇒ 记为**按压打偏**（探针/判据形态写错），**已按纪律记为失败并改正** |
| 4.3 | 复原后 `sha256sum services/api/middleware.py` | `ca03dac36982d5509e34ae719e352fbc84cd70189a526bd3389621597c82691a`（与按压前**逐字相同**） |
| 4.4 | `git diff --quiet services/api/middleware.py` | **IDENTICAL TO HEAD** |
| 4.5 | 复原后复跑 | **15 passed** |

### 五、既有判据零改动与规模

| # | 观察 | 结果 |
| --- | --- | --- |
| 5.1 | `tests/api/test_principal_auth.py` / `test_control_plane_auth_same_source.py` / `test_reproducibility_wording.py` / `test_record_face_is_covered_by_the_gate.py` | 四个文件 `git diff --quiet` **全空**（UNCHANGED） |
| 5.2 | 判据规模 | **311 行**（≤ 450 硬上限）；单函数 ≤ 50 行；`ruff check` + `ruff format --check` + `mypy` 全过 |
| 5.3 | 凭据纪律 | token 为本文件内构造的**合成假值**，不从环境读取、不落盘、不进日志 |
| 5.4 | m0 收集面 | 落 `tests/**` ⇒ 属既有 `python/tests` 收集面 ⇒ **不新增 m0 check** |

### 六、本轮是否证明产品缺陷

| # | 观察 | 结果 |
| --- | --- | --- |
| 6.1 | 主体可否被伪造 | **不可**（2.1 / 2.2 / 2.3 全部无效） |
| 6.2 | 读面是否被污染 | **没有**（3.1 / 3.3 / 3.4 / 3.5 / 3.6 全部 `None`） |
| 6.3 | ⇒ 产品代码改动 | **零**（`services/api/middleware.py` 按压后 `git diff` 为空） |
| 6.4 | 自检结论 | **边界成立** |
| 6.5 | 但本轮修掉的缺陷 = **判据自身 1 处（形态选择错）** | 首版用 `TestClient` ⇒ **不可证伪**；改走 `ASGITransport` + 同任务 `await`。**如实登记**，**不**算产品缺陷 |

## 结论

**`PASS_WITH_WARNINGS`**。GOAL-021 **EC-03** 三条**全部成立且有实跑证据**：
自报不可生效（头 / query / body 三类输入 + 真实 app）、读面无主体且不被污染
（含被拒写请求之后、连续写之后、交替形态）、顺序形态**可判红**（按压 **4 failed**，逐字节复原，
且**先证明了驱动形态本身可证伪**）。**零产品缺陷**；既有判据**零改动**。

**警告（如实登记，不构成 PASS 的例外）**：

- **`W-1`（最要紧）**：**并发形态不能单独读作「并发安全」**。实测：`asyncio.gather`
  的结果**取决于父任务上下文** —— **干净 ⇒ 0 violations**；**已污染 ⇒ 20 violations**
  （子任务**继承**父上下文）。本判据的并发用例**已在断言与文档里写明前提**
  （父上下文干净），并**明确不作安全结论**。**未收口**：这属于 `contextvar` 语义的固有性质，
  不是本仓可「修」的缺陷。
- **`W-2`**：`TestClient` 与 `ASGITransport` 在**该面上行为不同** ⇒ 本仓其它
  依赖请求级 `contextvar` 的判据（若有）**可能**同属「不可证伪」而未自知。
  本轮只修了本 EC 的判据，**未普查**全仓（范围诚实保留）。
- **`W-3`**：本 EC 判的是**控制面请求级主体**；**后台线程 / 调度器触发**的路径没有请求主体
  （`current_principal()` 为 `None` 并按设计回退既有常量）——本判据**不覆盖**那些路径的归因。
- **`W-4`**：单 token ⇒ 单主体。**逐调用方身份**（谁调的）**不存在**，因此
  「归因不可伪造」只到「主体 == 配置主体」这一层；**对象级授权（BOLA/BFLA）未做**。
- **`W-5`**：合成假 token ⇒ 不验证真实 token 的形态分布；与 `W-4` 一起，
  **不得**把本 EC 读成「有身份就有授权」。

### 七、全量门（记录写完之后）

| # | 观察 | 结果 |
| --- | --- | --- |
| 7.1 | `run_all_checks.py --profile m0 --keep-going` | 终态行 **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4606 passed / 21 skipped**、零 `FAILED`/`ERROR`；日志 `scratch/goal021-c3-m0-v2.log`） |
| 7.2 | 记录面判据 | `tests/architecture/python/` + `tests/tooling/` ⇒ **1371 passed**（记录面在受判集合内） |
| 7.3 | m0 条数 | 仍为 **23** ⇒ 新增判据**未**新增 check |
| 7.4 | 顺序 | 记录（PLAN / RECHECK / GOAL / MEM）写入**先**，全量门运行**后**（承 MEM-145） |
| 7.5 | **首跑的一次红（已归因，非代码缺陷）** | `framework/run_cursor_framework_evals` 抛 `PermissionError: [WinError 5]`（`.cursor/runtime/evolution_state.json.tmp` → `.json` 的 `os.replace`）。**归因**：并发 / 残留 tmp（`.cursor/runtime/**` 是 gitignored 运行态）。**取证**：清残留 tmp + **单独**跑该 check ⇒ **`FRAMEWORK EVAL PASS`** ⇒ **独占重跑完整门** ⇒ 全绿 23/23。**未改该 check 的任何阈值 / 断言** |

**未覆盖范围（承 GOAL-021 的边界，原样保留）**：读面未认证 / 多租户与 RBAC 未做 /
BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口（**不得**宣称项目安全）。
