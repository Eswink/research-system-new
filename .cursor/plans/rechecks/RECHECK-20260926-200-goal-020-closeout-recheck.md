---
id: RECHECK-20260926-200
slug: goal-020-closeout-recheck
title: GOAL-020 收口独立复检（EC-04）：两树同结论 + 按压 + as-is m0 23/23（覆盖记录面）+ 残余终态
plan_id: PLAN-20260926-199
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-26
completed_at: 2026-09-26
owners:
  - root-agent
---

# RECHECK-20260926-200 — GOAL-020 收口复检

## 检查结果

**复检口径**：不复用 GOAL / PLAN 的结论叙述；每一项给出**可复核观察面**（脚本、命令、run id）。
**未实跑的不记通过**。

### 一、独立复检脚本（32 项，六面）

**观察面**：`scratch/goal020-ec04-closeout-recheck.py`（只读 + 自复原）。**结果 32/32**：

| 面 | 项数 | 关键判词 |
| --- | --- | --- |
| 交付面在位（三个 EC 的六件交付物） | 6 | 全部在位 |
| 请求层行为（注入 / 不加空头） | 2 | `MUTATING_METHODS` + `Authorization` 在位；`authorization !== null` 约束在位 |
| token 模块**代码面**不碰持久化 API | 3 | `localStorage` / `sessionStorage` / `indexedDB` 均**不在代码面**（剥注释后判） |
| 运维面五标志**各文档各自**在位 | 3 | 三处 `missing=[]`（不互相顶替） |
| 残余登记 | 5 | `W-10`…`W-14` 逐条在位 |
| 未覆盖范围 | 3 | 读面未认证 / 多租户 / `R-M1` 在位 |
| **受保护判据零改动** | 3 | `test_reproducibility_wording.py` / `test_control_plane_auth_same_source.py` / `test_security_scan.py` 的 `git diff` **全空** |
| **按压**（非恒真） | 2 | 删话术判据的 `.cursor/plans` 扫描根 ⇒ 覆盖判据 **2 failed** ⇒ 判红；sha256 `eb5cd6289de31710` **逐字节还原** |
| **两树同结论** | 3 | 干净 checkout **1368 passed** / 当前树 **1368 passed** / 判词行**一致** |

**两树口径校正（本轮实测发现）**：干净 checkout 的 `.venv` 由 `uv` **现场创建**（首次装依赖，
一次对照会超时）⇒ 两树必须**共用主树的解释器**跑，否则比的是两份环境。
**判词比对要剔除耗时**：首版逐字比 `… passed in 53.01s` vs `… in 50.40s` 会**假红**；
改为只比「通过/失败数与结论」（`_verdict()`）。

### 二、as-is 本机 m0（**记录写完之后**跑，覆盖记录面）

| # | 观察 | 结果 |
| --- | --- | --- |
| 2.1 | 终态行 | `PASS: profile=m0; 23 deterministic checks` |
| 2.2 | `PASS [` 行数 | **24**（= 23 计数项 + `release-assets-immutable` 不计数项） |
| 2.3 | pytest 计数 | **4365 passed / 214 skipped**，`FAILED`/`ERROR` **0** |
| 2.4 | 运行顺序 | **在全部收口记录写入之后**（按 EC-02 修好的顺序：写记录 → 记录面判据 → 全量门） |
| 2.5 | 日志 | `scratch/goal020-c4-m0-as-is.log` |

### 三、治理

`validate.py` = **`Cursor 治理验证通过`**（七条 bullet 全绿）；`DOCS-CHECK PASS:
6 deterministic checks`。

### 四、CI 台账（四次推送，逐 run 逐 job 实查）

| 推送 | 提交 | M0 run（八 job） | CodeQL | `run_attempt` |
| --- | --- | --- | --- | --- |
| 建档 GOAL-020 | `6cc7561` | [36246070820](https://github.com/Eswink/research-system-new/actions/runs/36246070820) **八 job 全 success** | [36246070729](https://github.com/Eswink/research-system-new/actions/runs/36246070729) **3/3** | **1** |
| cycle 1（EC-02） | `41c81e3` | [36252399295](https://github.com/Eswink/research-system-new/actions/runs/36252399295) **八 job 全 success** | [36252398986](https://github.com/Eswink/research-system-new/actions/runs/36252398986) **3/3** | **1** |
| cycle 2（EC-01） | `e1e20a6` | [36261915272](https://github.com/Eswink/research-system-new/actions/runs/36261915272) **八 job 全 success** | [36261914950](https://github.com/Eswink/research-system-new/actions/runs/36261914950) **3/3** | **1** |
| cycle 3（EC-03） | `c12af0c` | [36264448948](https://github.com/Eswink/research-system-new/actions/runs/36264448948) **八 job 全 success** | [36264448739](https://github.com/Eswink/research-system-new/actions/runs/36264448739) **3/3** | **1** |

**四次全部一次成功、无 flake、无重跑**（`run_attempt=1` ×4）。八 job = `quality-ubuntu-latest` /
`quality-windows-latest` / `console-frontend` / `observability-overhead-ubuntu-latest` /
`observability-overhead-windows-latest` / `container-quality` / `eval-gate` / `collector-quality`。
**上游 push 回执每次报 8 条告警**（6 moderate + 2 low，全为 `undici`）⇒ 本 GOAL **零依赖改动**。

### 五、残余终态（逐条）

**承继（GOAL-019 的九条）**：`R-M1`（Mimosa 钩子 `scanner_enobufs` 未得完整结论 ⇒
**不得**宣称项目安全）/ `R-D1`（`undici` 8 条，**归属上游**）/ `R-B1` / `R-N1` / `R-F1` /
`R-F2` / `W-4` / `W-5` / `W-6`（`tests/e2e/live_run_support.py` 余量 1 行）—— **原样保留**。

**GOAL-019 的五条新残余 → 终态**：

| 残余 | 终态 |
| --- | --- |
| `W-10` 单一共享 token ⇒ 单一主体 | **原样保留**（归属方 = 另行授权） |
| `W-11` BOLA / BFLA 未做 | **原样保留**（归属方 = 另行授权） |
| `W-12` 部署面未验证 | **部分收口**：已给**可复核检查项**（反代透传 / TLS / 多副本）并**如实登记本机不可验证**；**仍未**把它变成已验证 |
| `W-13` 前端无 token 输入面 | **已收口**（EC-01：三态实跑 + 成对反证） |
| `W-14` 记录面扫描面未逐一核实 | **已收口**（EC-02：11 条清单逐行核实） |

### 六、未覆盖范围（逐条明写）

**读面未认证**（GET/HEAD 放行，`GET /health` 无豁免清单）/ **多租户与 RBAC 未做**（M18
`DEFERRED` 不变）/ **BOLA·BFLA 未做**（D-12(a) 仍在）/ **`R-M1` 未收口** ⇒ **不得**宣称项目安全 /
**部署面未验证**（只给检查项）/ **前端 token 面不是访问控制**（`THREAT_MODEL.md` §6.3 第 3 条）。

## 结论

**PASS_WITH_WARNINGS**。EC-04 的全部验收条件有实跑证据：**独立复检 32/32**（含**按压判红 +
逐字节还原**与**两树同结论 1368 passed**）、**as-is m0 = 23/23 且跑在记录写完之后**、
**治理绿**、**CI 四次推送全绿且 `run_attempt=1`**、**残余逐条终态**、**未覆盖范围明写**、
**三个受保护判据零改动**。

**警告**（不影响 PASS，且**不得**被读成更强结论）：

- **W-1｜部署面仍未验证**：本轮只把它收成**检查项 + 不可验证登记**。
- **W-2｜`W-10` / `W-11` 原样保留**：单一主体与对象级授权未做，需**另行授权**。
- **W-3｜前端三态证据是本机实跑**：CI 的 `console-frontend` 跑的是**关闭态**；
  **开启态**三态未进 CI 判据（本轮不改 workflow 结构）。
- **W-4｜`R-M1` 未收口** ⇒ **不得**宣称项目安全；`R-D1` 归属上游。
- **W-5｜`W-6`**（`tests/e2e/live_run_support.py` 只剩 1 行余量）**原样保留**。
- **W-6｜本收口轮与前三轮同源**（同一驱动）；复检脚本独立于实施叙述，但**不比 GOAL-019 的
  「两独立 checkout」更强**。
