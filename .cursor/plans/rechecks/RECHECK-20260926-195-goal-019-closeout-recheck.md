---
id: RECHECK-20260926-195
slug: goal-019-closeout-recheck
title: GOAL-019 收口独立复检（EC-05）：多面同结论 + 干净树按压 + 记录面真红归因与修复 + as-is m0 + 残余逐条
plan_id: PLAN-20260926-194
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-26
completed_at: 2026-09-26
owners:
  - root-agent
---

# RECHECK-20260926-195 — GOAL-019 收口复检

## 检查结果

**复检口径**：不复用 GOAL / PLAN 的结论叙述；每一项给出**可复核观察面**（命令、提交、日志）。
**未实跑的不记通过**。本轮复检**抓到一个真红**（cycle 2 的记录提交）并修好——见第四节。

### 一、多面同结论（交付 tip / 记录 tip / 终态）

脚本 `scratch/goal019-ec05-multitree.py`；三面各自是**真实推送过的提交**或终态工作树，
干净树用 `git worktree add --detach`（**只读用法**：按压后校验 sha256 还原）。

| # | 面 | 提交 | 定向判据（`tests/architecture/python` + `tests/tooling`） | 治理 | DOCS |
| --- | --- | --- | --- | --- | --- |
| 1.1 | `deliv`（干净 checkout） | `957fe05` | **`1359 passed` / exit=0** | `Cursor 治理验证通过` | `DOCS-CHECK PASS: 6` |
| 1.2 | `records`（干净 checkout） | `75155b2` | **exit=1**：`test_reproducibility_wording.py::…test_no_affirmative_fully_reproducible_claim` | 通过 | 通过 |
| 1.3 | `main`（终态工作树） | — | **exit=0** | 通过 | 通过 |
| 1.4 | **归因唯一性** | `git diff --name-only 957fe05..75155b2` = **恰好 6 个 `.cursor/**` 记录文件**（零产品/文档/测试文件）⇒ 红只可能来自记录面 | — | — | — |
| 1.5 | **同提交可复现**（两个独立 checkout @ `957fe05`） | deliv + mirror | 两树**同数**：`1359 passed` / exit=0（逐条清单同） | — | — |
| 1.6 | 调用口径校准 | 同一提交两种口径：`uv run --frozen --no-sync` ⇒ **1359 passed**；直接调 `.venv/Scripts/python.exe` ⇒ **1345 passed / 14 failed**（`lint-imports` 不在 PATH 的**已知假红**）⇒ 跨树比较前必须统一口径 | — | — | — |

### 二、判据非恒真（在干净树里按压）

| # | 检查 | 结果 |
| --- | --- | --- |
| 2.1 | 按压面 | 干净树 `D:\rs-goal019-deliv@957fe05` 的 `docs/api/CONTROL_PLANE_API.md`：`读面（GET / HEAD）未认证` → `已认证`（唯一命中） |
| 2.2 | 判红 | **`test_canonical_declaration_is_verbatim_in_all_four_docs`**（exit=1） |
| 2.3 | 逐字节还原 | sha256 `0cb60c3ee79ff14f` → `0cb60c3ee79ff14f` **一致** |
| 2.4 | 复原后复跑 | **exit=0**（干净树回到绿） |

### 三、as-is 本机 m0

| # | 检查 | 结果 |
| --- | --- | --- |
| 3.1 | **全量 m0**（独占、仓库 `.venv`、DSN 固化、`--keep-going`，且**在全部收口记录写完之后**跑） | 终态行 **`PASS: profile=m0; 23 deterministic checks`**、`M0_EXIT=0`、`PASS [` = **24**、`python/tests` = **4550 passed / 20 skipped**、`FAILED`/`ERROR` **0**（日志 `scratch/goal019-c3-m0-as-is.log`） |
| 3.2 | 这次 m0 与 cycle 2 那次的区别 | cycle 2 的 m0 跑在**记录写入之前** ⇒ 记录面未被覆盖（第四节的红就是这么漏过去的）；**本次 m0 覆盖完整树（含全部记录）** |
| 3.3 | 终态行填回记录之后的把关 | 填回只改一行字面量 ⇒ 用**记录面判据 + 治理 + `DOCS-CHECK` + `ruff`** 复盖（3.4） |
| 3.4 | 记录面复跑（填回后） | `tests/architecture/python` + `tests/tooling` = **1359 passed**；治理 = `Cursor 治理验证通过`；`DOCS-CHECK PASS: 6 deterministic checks` |

### 四、本轮抓到的真红（记录面）与修复

**这是本 GOAL 最重要的一条复检发现**：cycle 2 的**记录提交**把真红带进了 main。

| # | 检查 | 结果 |
| --- | --- | --- |
| 4.1 | 现象 | `75155b2` 的 M0 = **failure**（`quality-ubuntu-latest` + `quality-windows-latest`；其余 6 job success），CodeQL 3/3 success |
| 4.2 | 根因 | `tests/architecture/python/test_reproducibility_wording.py` 的 `_SCAN_ROOTS` **包含 `.cursor/plans`** ⇒ `RECHECK-20260926-193` 里**裸写**了**不得**单写的词表条目「完全可复现」，被判为**肯定式宣称**。该判据的豁免是「加引号的提及」或「同行含否定标记」 |
| 4.3 | **为什么本地 m0 是绿的** | 本地全量 m0 跑在**记录写入之前** ⇒ 记录面**从未被门覆盖**。「先跑门、后写记录」这个顺序下，本地绿**不可能**覆盖记录面（W-5 的必然结果，不是偶然） |
| 4.4 | 修复 | `RECHECK-20260926-193` 该行改为 `**不得**出现的肯定式断言：… / 「完全可复现」 / …`（**加否定标记 + 加引号**，与既有记录的写法一致） |
| 4.5 | 修复验证（本地） | `tests/architecture/python` = **186 passed**（cycle 1 为 175 ⇒ +11 = 新增判据）；`main` 面 exit=0 |
| 4.6 | 修复验证（CI） | 收口提交的 run（**见回合汇报 / 台账尾巴**）——`75155b2` 的红**如实登记**，不掩盖 |
| 4.7 | 第二处（本 PLAN 自己的）| `PLAN-20260926-194` 的清单第 4 条**先于 CI 就把这条写成流程要求**（"记录写完之后必须再跑一次记录面判据"）——顺序教训已被吸收进流程 |

### 五、CI 台账（逐 run 逐 job 实查；全部落在 main）

| 推送 | 提交 | run | 结论 |
| --- | --- | --- | --- |
| 建档 | `d4e559e` | M0 **36206487801** / CodeQL **36206486979** | 八 job 全 success / 3-3 success（`run_attempt=1`） |
| cycle 1（EC-01+02+03） | `c87823e` + `8ed413b` | M0 **36228978492** / CodeQL **36228978213** | 八 job 全 success / 3-3 success（`run_attempt=1`） |
| cycle 2 交付（文档 + 判据） | `957fe05` | M0 **36232944933** / CodeQL **36232944628** | 八 job 全 success / 3-3 success（`run_attempt=1`，一次成功无 flake） |
| cycle 2 记录 | `75155b2` | M0 **36234092175** / CodeQL **36234091938** | M0 = **failure**（`quality-ubuntu-latest` + `quality-windows-latest`）；CodeQL 3-3 success ⇒ **原因见第四节** |
| 收口 | 本行所在的提交 | **依「固定口径」只在回合汇报记账** | — |

**外部旁证**：三次 push 回执均报 **8 条**告警（6 moderate + 2 low，全为 `undici`）⇒ 本 GOAL **零依赖改动**。

### 六、残余（逐条，原样承继 + 本轮新增）

**承继的诚实边界（不是待办，是如实保留）**：

- `R-F1`｜收敛 / 一致性判定含主观面时必须先**操作化**。**原样保留**。
- `R-F2`｜真实数据 / 调用规模不足时的**诚实边界**。**原样保留**。
- **`R-M1`｜Mimosa 钩子侧 `scanner_enobufs` 未得完整结论**——**不得**宣称项目安全。
  **原样保留**（本轮两次 commit / push 的钩子回执都写着「未得到完整扫描结论」，与之印证）。
- **`R-D1`｜Dependabot 告警**：`yaml` 已升、`undici` **已调研未升** ⇒ **8 条**（6 medium + 2 low）
  原样保留；**归属方 = 上游**（`@connectrpc/connect-node` 1.x 锁 `undici ^5`；
  `undici` 全部修复版本 ≥ `6.23.0` ⇒ 本仓**不可正确升级**，见
  `docs/roadmap/UNDICI_TRANSITIVE_DEPENDENCY_RESEARCH.md`）。
- **`R-B1` / `R-N1`**——承继残余 / 非 ASCII 路径豁免，**原样保留**。
- **`W-4`（本机 m0 仍同进程跑阈值判据）/ `W-5`（新作业多一次冷装）/
  `W-6`（`tests/e2e/live_run_support.py` 只剩 1 行余量）**——**原样保留**。

**本 GOAL 新增（如实登记）**——**编号续 `RECHECK-20260926-191` 的 `W-1…W-9`**；
上方承继清单里的 `W-4` / `W-5` / `W-6` 是 **`GOAL-018` 的残余编号**（另一命名空间，勿与本 GOAL 的
复检 W 序号混读）：

- **`W-10`｜写面认证只到"是不是经过认证的调用方"**，**不回答"是哪一个调用方"**：
  单一共享 token ⇒ 单一主体（`service:<principal_id>`），本实现**不接受**调用方自报身份。
  归属方 = **如要逐调用方身份 ⇒ 需另行授权**（属 D-12 (a) 面）。与 `RECHECK-191` 的 `W-4` 同义，
  此处按"收口残余"口径**再次登记**。
- **`W-11`｜对象级授权（BOLA / BFLA）一个都没做**：`IDENTITY_AND_ACCESS.md` 未覆盖范围第 3 条、
  §6.7 都写明「有认证、无授权」；**归属方 = 另行授权**。
- **`W-12`｜部署面未验证**：反代 / TLS / 多副本下的认证行为**没有**实测面，文档如实写"未验证"
  （与 `RECHECK-191` 的 `W-8` 同义）。
- **`W-13`｜前端无 token 输入面**：`apps/web/**` 本 GOAL 零改动 ⇒ 认证开启时浏览器侧写操作
  需要外部注入 header（runbook §2.1 已写明两条设置形态）。归属方 = **按需另立**。
- **`W-14`｜记录面判据的扫描面未逐一核实**：本 GOAL 实测 `test_reproducibility_wording.py`
  会扫 `.cursor/plans`；**是否还有别的判据扫记录面未逐条核实** ⇒ 收口的稳妥做法是记录写完后
  跑整个 `tests/architecture/python` + `tests/tooling`（本轮已跑）。

### 七、本轮第二处同类真红：**收口记录自己又犯了一次**（如实登记）

写本复检时，`4.2` 那一行**再次**把该词表条目写成裸词（判据只认「加引号」或「同行含否定标记」，
而反引号不在引号集内）⇒ `tests/architecture/python/test_reproducibility_wording.py`
**再判红一次**（`…/RECHECK-20260926-195-…md:57`）。

| # | 检查 | 结果 |
| --- | --- | --- |
| 7.1 | 发现面 | 手写的记录面复跑（`tests/architecture/python` + `tests/tooling`）**在本轮内**抓住——**先于 CI** |
| 7.2 | 修法 | 改为 `**不得**单写的词表条目「完全可复现」`（加否定标记 + 加引号） |
| 7.3 | 意义 | **这条教训的形状是"复述禁令时最容易违反禁令"**：写"某词被禁"的句子本身就带着那个词 ⇒ 记录面判据的豁免必须覆盖"引用形态"，而**反引号不算引用**（本仓的引号集是 `「」「」“‘\"'`） |

## 结论

**GOAL-019 的五个 EC 全部达成**：EC-01（主体模型 + 归因落 canonical）/ EC-02（写面认证三态 +
凭据纪律）/ EC-03（既有链路零回归）/ EC-04（四处文档同源 + 可按压判据）/
EC-05（收口复检 + 残余登记）。**产品面净改动**：`Principal` 域值对象 + 请求级主体上下文 +
写面认证中间件（复用唯一的 `_MUTATING_METHODS`）+ 两处归因读取点 + 一条同源判据 +
四处文档；**零新依赖**、**零读面认证**、**零多租户/RBAC**、**零 `Idempotency-Key` 语义改动**。

**六条承继残余（`R-F1` / `R-F2` / `R-M1` / `R-D1` / `R-B1` / `R-N1`）
+ 三条承继 W（`W-4` / `W-5` / `W-6`，GOAL-018 残余编号）
+ 五条本轮新增 W（`W-10`…`W-14`）**全部是**已知边界 / 归属说明**，**无一项**推翻上述结论。

**本地不绿不得 push**：本轮把「记录面也是受判面」这条教训落成流程（`PLAN-194` 清单第 4 条 +
`MEM-20260926-145`），并把 m0 压在**记录写完之后**。
