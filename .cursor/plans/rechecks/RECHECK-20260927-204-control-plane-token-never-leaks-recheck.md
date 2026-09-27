---
id: RECHECK-20260927-204
slug: control-plane-token-never-leaks-recheck
title: GOAL-021 cycle 2（EC-02）独立复检：六出口逐个判 + 反证 1/1 红 + 逐字节复原 + 既有判据零改动
plan_id: PLAN-20260927-203
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-27
completed_at: 2026-09-27
owners:
  - root-agent
---

# RECHECK-20260927-204 — token 不泄漏（GOAL-021 EC-02）

## 检查结果

**复检口径**：不复用 PLAN / GOAL 的结论叙述；每一项给出**可复核观察面**（命令、文件、
行号、sha256、实测输出）。**未实跑的不记通过**。

### 一、六个出口逐个判（判据**不是**一条笼统断言）

| # | 出口 | 观察面 | 结果 |
| --- | --- | --- | --- |
| 1.1 | **日志** | 认证开启 + 三类写请求（缺 token / 错 token / 对 token）⇒ 捕获 handler 收全部记录 | **token 值零命中**（正确 token 与被拒 token 都不出现） |
| 1.2 | **日志（判据自身对照）** | 哨兵记录 `capture-sentinel-…` 能否被同一装置截到 | **能截到** ⇒ 「零命中」不是「什么都没捕到」的假绿 |
| 1.3 | **遥测（结构）** | `sanitize_attributes` 对未知键 `authorization` / `raw_headers` / `request_body` | **整个丢弃**（闭集 allow-list；允许键 `provider` 仍在） |
| 1.4 | **遥测（形态）** | 允许键 `model_id` 塞 `Bearer <token>` | **被脱敏**（导出含 `REDACTED`，不含 token） |
| 1.5 | **遥测（现状）** | 允许键 `model_id` 塞**裸不透明串** | **原样导出** ⇒ 该边界**如实登记**（见 W-1） |
| 1.6 | **401 响应** | 缺头 / 不匹配两个 401 的整个 body | **零命中**；且两个成因**各自点名**（`Bearer` / `does not match`） |
| 1.7 | **成功响应** | 带对 token 的 `POST /projects`（201） | **不回显**凭据 |
| 1.8 | **事件 payload** | 带对 token 的 `approval.decided` 事件（逐个 payload 值） | **零命中**；`actor` = `service:leak-probe`（**主体标识**而非凭据） |
| 1.9 | **前端持久层** | 由既有 `test_security_scan.py` 判（条件字面量断言） | **未改该文件**（见三）；本判据只交叉引用 ⇒ **不重复** |
| 1.10 | **记录面** | `.cursor/plans` + `.cursor/memory` 的 `*.md` 实际内容 | **凭据值零命中**；且**变量名** `RESEARCHOS_CONTROL_PLANE_TOKEN` 确有出现（`names_only > 0`，排除「扫描面选错」） |

### 二、反证：泄漏 ⇒ 判红 ⇒ 逐字节复原

**复检动作**：在 `services/api/middleware.py` 的 `PrincipalAuthMiddleware.dispatch` 里
对 `provided` 记一条日志，跑判据，再复原。

| # | 观察 | 结果 |
| --- | --- | --- |
| 2.1 | 注入后跑 `test_control_plane_token_never_leaks.py` | **1 failed, 11 passed** —— 红的正是 **`TestTheTokenNeverReachesLogs::test_no_log_record_contains_the_token`** |
| 2.2 | 复原后 `sha256sum services/api/middleware.py` | `ca03dac36982d5509e34ae719e352fbc84cd70189a526bd3389621597c82691a`（与注入前**逐字相同**） |
| 2.3 | `git diff --quiet services/api/middleware.py` | **IDENTICAL TO HEAD** |
| 2.4 | 复原后复跑 | **12 passed** |

### 三、既有判据零改动（AC-7）

| # | 文件 | `git diff --quiet` |
| --- | --- | --- |
| 3.1 | `tests/api/test_security_scan.py` | **UNCHANGED** |
| 3.2 | `tests/api/test_secret_redaction.py` | **UNCHANGED** |
| 3.3 | `tests/architecture/python/test_reproducibility_wording.py` | **UNCHANGED** |
| 3.4 | `tests/architecture/python/test_record_face_is_covered_by_the_gate.py` | **UNCHANGED** |
| 3.5 | `tests/architecture/python/test_control_plane_auth_same_source.py` | **UNCHANGED** |

### 四、凭据纪律与规模

| # | 观察 | 结果 |
| --- | --- | --- |
| 4.1 | 判据中的 token | 本文件内构造的**合成假值**（`fixture-` 前缀），**不**从环境读取、**不**落盘、**不**进日志 |
| 4.2 | `tools/credential_audit.py` | 四面 **offenders=0**（tracked `96/96` 放行、records `3/3` 放行、config_db `0`、logs `0`） |
| 4.3 | 判据规模 | **312 行**（≤ 450 硬上限）；单函数均 ≤ 50 行；`ruff check` + `ruff format --check` + `mypy` 全过 |
| 4.4 | 受影响套件 | `tests/api/` + `tests/architecture/python/` ⇒ **745 passed, 4 skipped** |
| 4.5 | m0 收集面 | 新判据落 `tests/**` ⇒ 属既有 `python/tests` 收集面 ⇒ **不新增 m0 check**（条数仍 23） |

### 五、本轮是否证明产品缺陷

| # | 观察 | 结果 |
| --- | --- | --- |
| 5.1 | 六个出口有没有真的泄漏**控制面 token** | **没有**（1.1 / 1.6 / 1.7 / 1.8 / 1.10 全部零命中） |
| 5.2 | ⇒ 产品代码改动 | **零**（`services/api/middleware.py` 反证后 `git diff` 为空） |
| 5.3 | 自检结论 | **边界成立**（不是「修好了」） |
| 5.4 | 但有一处**判据自身**的缺陷被本轮修掉 | 首版记录面判据用了 `(root/"goals").glob("*.md").__next__()`（取**任意**第一个文件）⇒ **判据自己判红**且理由是错的。**修法**：改为**跨全部记录文件**统计 `names_only`。**如实登记**为「本轮修掉的缺陷 = 判据自身 1 处」，**不**算产品缺陷 |

## 结论

**`PASS_WITH_WARNINGS`**。GOAL-021 **EC-02** 六出口**全部成立且有实跑证据**：
日志（含捕获对照）/ 遥测（结构 + 形态 + 现状三档）/ 401 body（含两个点名文案）/
成功响应 / 事件 payload（actor 是标识）/ 记录面（零值命中且变量名在位）。
反证 **1/1 红**、逐字节复原、既有判据**零改动**、**零**产品缺陷。

**警告（如实登记，不构成 PASS 的例外）**：

- **`W-1`（最要紧）**：脱敏是**形态匹配**而非**值匹配** ⇒ **裸不透明串**放在
  **允许清单内**的字符串键里**会被原样导出**（1.5 实测）。判据**如实断言**了这一点
  （不假装更强）。**风险口径**：这要求「允许键的值本身不得承载凭据」靠**上游纪律**
  （属性填值处不塞凭据）保证，而不是靠脱敏兜底。**未收口**，如实保留。
- **`W-2`**：日志面判的是**本进程捕获到的记录**（根 logger + 已装 handler）。
  **外部采集链**（OTLP collector / 日志聚合 / 反代的 access log）**不在**本轮范围。
- **`W-3`**：`_MEASURED` 类告警线不适用于本判据（本判据无计数断言）；
  但记录面判据依赖「变量名至少出现一次」⇒ 若将来 GOAL 记录被归档删除，
  该断言会红（属**提示**，不是漏洞）。
- **`W-4`**：前端持久层由既有 `test_security_scan.py` 判（**未改**）——
  本 EC **不重复**其断言，因此本 RECHECK 对前端面的结论是**引用**而非**独立复验**。
- **`W-5`**：合成假 token ⇒ **不**验证真实 token 的形态分布。若真实 token 恰含某种
  **会被形态匹配命中**的前缀，脱敏行为可能不同；反过来说，若真实 token 是纯随机串
  （推荐），则 `W-1` 的暴露面**更**需要上游纪律兜底。

### 六、全量门（记录写完之后）

| # | 观察 | 结果 |
| --- | --- | --- |
| 6.1 | `run_all_checks.py --profile m0 --keep-going` | 终态行 **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` = **24**、**4590 passed / 21 skipped**、零 `FAILED`/`ERROR`；日志 `scratch/goal021-c2-m0.log`） |
| 6.2 | 记录面判据 | `tests/architecture/python/` + `tests/tooling/` ⇒ **1370 passed**（记录面在受判集合内） |
| 6.3 | m0 条数 | 仍为 **23** ⇒ 新增判据**未**新增 check |
| 6.4 | `W-1` 的独立复现 | `sanitize_attributes({"model_id": <裸不透明串>})` ⇒ 原样返回；同一值加 `Bearer ` 前缀 ⇒ 被替换为 `REDACTED` ⇒ **形态匹配**得到独立确认 |

**未覆盖范围（承 GOAL-021 的边界，原样保留）**：读面未认证 / 多租户与 RBAC 未做 /
BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口（**不得**宣称项目安全）。
**本 RECHECK 证明的是「已声明的出口不泄漏」，不能证明「不存在未声明的泄漏出口」。**
