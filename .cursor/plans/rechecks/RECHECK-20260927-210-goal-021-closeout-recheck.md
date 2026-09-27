---
id: RECHECK-20260927-210
slug: goal-021-closeout-recheck
title: GOAL-021 收口独立复检（EC-05）：28/28 六面 + 按压逐字节复原 + 受保护判据零改动 + 残余与未覆盖逐条
plan_id: PLAN-20260927-209
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-27
completed_at: 2026-09-27
owners:
  - root-agent
---

# RECHECK-20260927-210 — GOAL-021 收口复检

## 检查结果

**复检口径**：不复用 GOAL / PLAN / 各 PLAN RECHECK 的结论叙述；
每一项给出**可复核观察面**（脚本、命令、文件、sha256）。**未实跑的不记通过**。

取证脚本：`scratch/goal021-ec05-closeout-recheck.py`（只读 + 按压/复原；
**28/28 通过**）。

### 一、交付面

| # | 观察 | 结果 |
| --- | --- | --- |
| 1.1 | `tests/api/test_write_face_cannot_be_bypassed.py`（EC-01） | 在位，**285 行**（≤ 450） |
| 1.2 | `tests/api/test_control_plane_token_never_leaks.py`（EC-02） | 在位，**312 行** |
| 1.3 | `tests/api/test_principal_cannot_be_forged.py`（EC-03） | 在位，**311 行** |
| 1.4 | `tests/api/test_frontend_token_is_not_access_control.py`（EC-04） | 在位，**163 行** |
| 1.5 | 四份子 PLAN | **全部在位** |

### 二、按压面（复检**独立**重跑，不采信各 PLAN 的按压叙述）

| # | 观察 | 结果 |
| --- | --- | --- |
| 2.1 | 收窄保护面（`_MUTATING_METHODS` 去掉 `DELETE`）后跑 EC-01 判据 | **exit=1（判红）** ⇒ 判据仍对被守护的事敏感 |
| 2.2 | 逐字节复原后复跑 | **exit=0（复绿）** |
| 2.3 | 复原复核（raw `sha256`） | **一致** |

**本轮复检暴露的复核自身缺陷（如实登记，已修）**：

| # | 缺陷 | 归因与修法 |
| --- | --- | --- |
| 2.4 | 首次运行时 2.3 **判 FAIL** | 按压/复原用 `read_text`/`write_text`（文本模式）⇒ **Windows 把 LF 写成 CRLF** ⇒ raw sha256 变化。**修法**：改 `read_bytes`/`write_bytes`。**关键**：`git diff` 因 `.gitattributes`（`* text=auto eol=lf`）归一化而**报「无改动」** ⇒ 该假象**只有 raw sha256 能抓**（落 `MEM-20260927-152`） |
| 2.5 | 凭据面首次「变量名在位」判 FAIL | 断言写错：期望变量名出现在 **GOAL 正文**，而它落在**实现 / 安全文档**面（GOAL 只沿用「只登记变量名」的纪律措辞）。**修法**：改为扫**正确落点**（中间件 + 两处安全文档）⇒ **3/3 在位** |

### 三、受保护判据零改动

| # | 文件 | `git diff --quiet` |
| --- | --- | --- |
| 3.1 | `tests/api/test_security_scan.py` | **UNCHANGED** |
| 3.2 | `tests/api/test_secret_redaction.py` | **UNCHANGED** |
| 3.3 | `tests/architecture/python/test_reproducibility_wording.py` | **UNCHANGED** |
| 3.4 | `tests/architecture/python/test_record_face_is_covered_by_the_gate.py` | **UNCHANGED** |
| 3.5 | `tests/architecture/python/test_control_plane_auth_same_source.py` | **UNCHANGED** |

### 四、承继残余逐条在位

| # | 残余 | 在 GOAL 正文 |
| --- | --- | --- |
| 4.1 | `R-M1`（Mimosa 钩子未得完整结论 ⇒ **不得**宣称项目安全） | **在位** |
| 4.2 | `R-D1`（`undici` 归属上游；`yaml` / `vite` 已升） | **在位** |
| 4.3 | `W-10`（单 token ⇒ 单主体） | **在位**（原样保留） |
| 4.4 | `W-11`（BOLA·BFLA 未做） | **在位**（原样保留） |
| 4.5 | `W-12`（部署面未验证） | **在位**（原样保留） |

### 五、未覆盖范围逐条明写

| # | 项 | 在 GOAL 正文 |
| --- | --- | --- |
| 5.1 | 读面未认证 | **在位** |
| 5.2 | 多租户 / RBAC 未做 | **在位** |
| 5.3 | BOLA·BFLA 未做 | **在位** |
| 5.4 | 部署面未验证 | **在位** |
| 5.5 | `R-M1` 未收口 ⇒ **不得**宣称项目安全 | **在位** |

### 六、凭据面

| # | 观察 | 结果 |
| --- | --- | --- |
| 6.1 | 4 个判据 + 4 份 PLAN + GOAL 正文里的 `Bearer <长随机串>` 字面量 | **零命中**（扫 9 文件） |
| 6.2 | 变量名落点 | 中间件 + `IDENTITY_AND_ACCESS.md` + `THREAT_MODEL.md` ⇒ **3/3 在位** |
| 6.3 | `tools/credential_audit.py` | 四面 `offenders=0` |

### 七、本次复检**未**复核的面（范围的诚实边界）

- **各 EC 的行为证据未逐条重跑**（本脚本只跑 EC-01 判据作按压面）：EC-02 的六出口、
  EC-03 的顺序/并发、EC-04 的后端独立性，其证据由各自 RECHECK（202 / 204 / 206 / 208）承载。
  本复检判的是**交付面 / 按压面 / 零改动 / 残余 / 未覆盖 / 凭据**六面。
- **CI 台账**（八 job + CodeQL + `run_attempt`）由 GOAL 的台账节承载，本脚本不查 CI。
- **m0 全量门**在记录写完之后单独跑（承 MEM-145），本脚本不跑它。

## 结论

**`PASS_WITH_WARNINGS`**。GOAL-021 的**收口面六项全部成立且有实跑证据**：
交付面在位且不越界、按压面**独立重跑**能判红并**逐字节复原**、受保护判据**零改动**、
承继残余**逐条在位**、未覆盖范围**逐条明写**、凭据面干净。
**零产品缺陷**；本轮修掉的是**复检脚本自身 2 处**缺陷。

**警告（如实登记）**：

- **`W-1`**：本复检脚本的按压面**只覆盖 EC-01**（其余 EC 的按压证据在各自 RECHECK 里）。
  ⇒ 本 RECHECK **不能**被读成「四个 EC 的按压都又被独立重跑了一遍」。
- **`W-2`**：`git diff` **不足以**证明「逐字节复原」（`.gitattributes` 归一化会掩盖行尾变化）
  ⇒ 凡声称逐字节复原处，证据**必须**是 raw `sha256`。已落 `MEM-20260927-152`。
- **`W-3`**：本复检在本机（Windows）跑；**平台相关面**（行尾、路径大小写）在 Linux 侧
  未逐条复验。CI 的 `quality-ubuntu-latest` 覆盖了**判据运行**面，不覆盖本脚本。
- **`W-4`**：GOAL-021 的四条自检结论都是**「已声明的边界成立」**——
  **不能**证明「不存在未声明的缺口」（承各 RECHECK 的同一判词）。
- **`W-5`**：`R-M1` 未收口 ⇒ **不得**据本 GOAL 的任一结论宣称项目安全。

**未覆盖范围（承 GOAL-021 的边界，原样保留）**：读面未认证 / 多租户与 RBAC 未做 /
BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口（**不得**宣称项目安全）。
