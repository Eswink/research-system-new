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

### 六之二、**两树同结论**（EC-05 的显式条款；**首轮跳过，本轮补跑**）

**条款原文**（GOAL-021 EC-05 ①）：「独立复检脚本（**当前树 + 干净 checkout** 同结论）」，
即判词列**逐行相同**。

**如实登记的过程缺陷**：本 RECHECK **首轮未跑干净 checkout**，却在「本次复检未复核的面」里
**没有登记该跳过**，且 EC-05 仍随 GOAL 一起记 PASS ⇒ 被完成核验判为**未达成**
（属「未实跑不得记 PASS」）。**本轮补跑**，结论如下。

**做法（两处环境口径）**：`git worktree add --detach ../goal021-clean-tree HEAD`（同 tip、
独立目录、无工作树改动）；**两树共用主树解释器**（干净 checkout 无自己的 `.venv`，
现场建会超时且**比的是两套环境**）；脚本新增 `--root` 与 `--verdict-only`
（只输出判词行，不含耗时 / 路径）。

| # | 观察 | 结果 |
| --- | --- | --- |
| T1 | 当前树 `--verdict-only` | **28 行判词，全 PASS** |
| T2 | 干净 checkout 同脚本 | **28 行判词，全 PASS**；完整输出 **`28/28 通过`** |
| T3 | `diff` 逐行比对 | **IDENTICAL**（无差异行） |
| T4 | 两个判词文件 `sha256` | **相同**：`5bb9bc08398eac789f9a07814b71b0586f7b1b34252a3c3cbb797efe119487f3` |
| T5 | 留档 | `scratch/goal021-c5-verdict-current.txt` / `-clean.txt` |
| T6 | 按压后两树是否干净 | 干净 checkout `git status --short` **空**；主树 `middleware.py` `git diff --numstat` **空** ⇒ **逐字节复原在两树都成立** |

⇒ **该条款达成**。**该跳过本身记为过程缺陷**（复检**范围**登记不完整），**非**产品缺陷。

**补跑后的门（记录再写完之后的复跑）**：全量 m0 = `PASS: profile=m0; 23 deterministic checks`
（`PASS [` = 24、**4613 passed / 21 skipped**、零 `FAILED`；日志 `scratch/goal021-c5-m0-definitive.log`）。
**关于「记录定稿」与门的先后（如实说明，避免一个无解的回退）**：
本地门**不可能**在「记录**最后一次**编辑之后」跑——因为**写下那次门的日志本身也是记录**，
写记录 ⇒ 上一跑失效（承 MEM-145）。本 GOAL 沿用的既有闭合约定是：
**本地最近一次门**跑在「当时记录已写完」的状态（`scratch/goal021-c5-m0-definitive.log`），
而**记录面的最终覆盖由 CI 承担**——CI 的 M0 跑在**该记录提交本身**上，
即 GOAL 台账里的**记录提交那一行**（逐 job 实查、含 `run_attempt`）。
⇒ 「门覆盖记录面」的终局证据是 **CI 跑在记录提交上**，不是某次本地跑的日志。

### 七、本次复检**未**复核的面（范围的诚实边界）

- **各 EC 的行为证据未逐条重跑**（本脚本只跑 EC-01 判据作按压面）：EC-02 的六出口、
  EC-03 的顺序/并发、EC-04 的后端独立性，其证据由各自 RECHECK（202 / 204 / 206 / 208）承载。
  本复检判的是**交付面 / 按压面 / 零改动 / 残余 / 未覆盖 / 凭据**六面。
- ~~两树同结论~~ —— **已补跑**（见「六之二」节）；本项**不再**属于未复核面。
- **CI 台账**（八 job + CodeQL + `run_attempt`）由 GOAL 的台账节承载，本脚本不查 CI。
- **m0 全量门**在记录写完之后单独跑（承 MEM-145），本脚本不跑它。

## 结论

**`PASS_WITH_WARNINGS`**（**补跑两树对照后维持**）。GOAL-021 的**收口面六项全部成立且有实跑证据**：
交付面在位且不越界、按压面**独立重跑**能判红并**逐字节复原**、受保护判据**零改动**、
承继残余**逐条在位**、未覆盖范围**逐条明写**、凭据面干净。
**零产品缺陷**；本轮修掉的是**复检脚本自身 2 处**缺陷（行尾 / 落点断言），
外加**补跑**了首轮跳过的**两树同结论**条款（判词 sha256 相同 ⇒ **同结论成立**）。

**警告（如实登记）**：

- **`W-0`（最要紧）**：本 RECHECK **首轮把「干净 checkout 同结论」这条显式条款静默跳过**，
  且未在「未复核的面」里登记 ⇒ 被完成核验判负。**已补跑并达成**（判词 sha256 相同），
  但**该跳过是真实的过程缺陷**：复检脚本的**范围登记不完整**。
  **教训**：复检条款里写明的**每一路**（当前树 / 干净 checkout / 两树比对）都要**各自留档**；
  「跑了一路 + 结论看起来一样」**不能**替代——那正是本轮被抓到的形态。
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
