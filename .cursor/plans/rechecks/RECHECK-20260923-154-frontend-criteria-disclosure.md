---
id: RECHECK-20260923-154
plan_id: PLAN-20260923-153
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-24
completed_at: 2026-09-24
reviewer: independent-recheck-script + root-agent-goal-013-ec03
baseline_ref: a09a0fa（cycle 4 派生 = cycle 4 的起点）
checked_head: 当前树 + 干净 checkout（cycle 4 最后一条功能提交）
---

# RECHECK-20260923-154 — EC-03 判据性质披露的机械落地（GOAL-013 cycle 4）

## 检查范围

本 GOAL 新增的**每条**前端判据（**16 条**：12 条页面级 live + 4 条离线矩阵判据）是否
① 都有一条性质披露、② 披露的两个字段都非空、③ 披露与实际按压结果**一致**。
不采信登记册与文档的自述：由机械判据 `frontend-criteria-disclosure.test.ts` 强制，
并对**每条披露做一次抽查实跑**（按数据 / 按页面成对）。

## 检查结果

### 一、披露登记册与机械判据

- **单一来源**：`apps/web/tests/unit/frontend-criteria-disclosure.ts` 的 `CRITERIA_DISCLOSURE`
  —— 16 条，与 D-1 的枚举口径（`git diff 50afb3b..HEAD -- apps/web/tests`）**双向**吻合。
- **机械判据**：`apps/web/tests/unit/frontend-criteria-disclosure.test.ts` 四条，
  实测 `pnpm run test` ⇒ **84 passed / 0 failed**（cycle 1 的 80 + 本 cycle 4 条）。
- **人读视图**：`docs/frontend/CONSOLE_FRONTEND_CRITERIA_DISCLOSURE.md`（16 行），
  由判据 ④ 与登记册同源。

### 二、反证表：每条判据**能被什么按压 / 不能被什么按压**（EC-03 的核心交付）

| # | 判据 | 能被什么按压 | **不能**被什么按压 | 红证（`scratch/`） |
| --- | --- | --- | --- | --- |
| 1 | ① 矩阵完备（20 行 / 零待定） | 把某行终态改成「待定」 | 改 spec 的断言强度（结构判据） | `goal013-c4-press-matrix-undecided.txt`（判词点名 row 3） |
| 2 | ② 三方同源 | 把保持行的缺口改写成「已交付」 | 同上 | `goal013-c1-press-matrix.txt` |
| 3 | ③ 收敛有证 | 把具名 live 文件改成不存在的文件名 | 同上 | `goal013-c1-press-live-route.txt` |
| 4 | ④ 不混写 | 往保持行的**缺口列**塞 `LIVE:` | 同上 | `goal013-c4-press-matrix-mixed.txt`（判词点名 row 3） |
| 5–6 | `plan/overview` 两条 | 钉住指标卡渲染值 | 改数据（两侧同源） | `goal013-c1-pressA-page.txt`（2 failed） |
| 7 | `library/lineage` 三表 | 钉住节点表渲染值 | 同上 | `goal013-c2-press-lineage-rows.txt` |
| 8 | `library/lineage` 空态 | 把空态文案改成 `…占位` | 同上 | `goal013-c2-press-empty-text.txt` |
| 9 | `govern/audit` 事件行数 | 钉住事件行渲染值 | 同上 | `goal013-c2-press-audit-rows.txt` |
| 10 | `govern/audit` 空态 | 把空态文案改成 `…占位` | 同上 | `goal013-c4-press-audit-empty.txt` |
| 11–12 | `portfolio/experiments` 两条 | 钉住指标列渲染值 | 同上 | `goal013-c3-press-experiments.txt`（2 failed） |
| 13 | `insights/reports` 正向 | 把 `objective` 段落钉成常量 | 同上 | `goal013-c3-press-reports.txt` |
| 14 | `insights/reports` 空态 | 把空态文案改成 `…占位` | 同上 | `goal013-c4-press-reports-empty.txt` |
| 15–16 | `ops/integrations` 两条 | 钉住 `health` 渲染值 | 同上 | `goal013-c3-press-integrations.txt`（2 failed） |

⇒ **16 条判据每条都有自己的红证**；cycle 1–3 遗留的两处缺口（矩阵判据 ①/④、
`govern/audit` 空态、`insights/reports` 空态）本 cycle **补按压**补齐，不是靠披露措辞绕开。

### 三、抽查实跑：证明披露为真（按数据 vs 按页面，成对）

披露说「**数据不敏感 / 页面敏感**」。取 `live-ops-integrations` 第 1 条做成对实跑：

| 按压方式 | 做法 | 实测 | 证据 |
| --- | --- | --- | --- |
| **按数据** | 把 provider id 在 `examples/config/tool_providers.yaml` 改名（读面与页面**一起**变） | **2 passed** | `scratch/goal013-c4-spotcheck-data.txt` |
| **按页面** | 把 `providerColumns` 的 `health` 渲染钉成常量 | **2 failed** | `scratch/goal013-c4-spotcheck-page.txt` |

⇒ 披露**为真**：等式对数据不敏感（两边一起变），只有按压页面那一段才敏感。

### 四、机械判据自己也按压（防判据恒真）

新判据自己必须能红，四条各按一次：

| 判据 | 按压 | 实测 |
| --- | --- | --- |
| ②③ | 把某条 `insensitiveFace` 改成空话「判据绿」 | **2 failed**（判词点名该条 + 「必须点名数据不敏感那一面」） |
| ① | 从登记册删掉一条 | **1 failed**（判词：登记册与实际 test 不一致） |
| ④ | 从人读文档删掉一行 | **1 failed**（判词点名缺的那条 test） |

证据：`goal013-c4-press-judge.txt` / `-press-judge-missing.txt` / `-press-judge-docdrift.txt`。

### 五、两棵树同结论（含本 cycle 查出的**三处复检脚本自身缺陷**）

复检脚本 `scratch/verify_goal013_c4.py` 沿用 cycle 3 修好的 ROOT 口径
（**由调用目录决定**，见 `MEM-20260923-120`）—— 本 cycle 不再出现「同一棵树跑两次」。

| 树 | 结果 |
| --- | --- |
| 主树（当前） | `checked=49 failures=0` |
| 干净 checkout `7d3eecf`（cycle 4 最后一条功能提交 = 功能 + 两门修复） | `checked=43 failures=3`：`F2 PLAN-153 not DONE`、`F3 PLAN-153 still has unchecked boxes`、`F6 recheck missing: null` |

干净树多出的三条红**内容**全是「尚未收口」时序项（PLAN 转 `DONE`、复检落盘都在**收口提交**里，
故干净树看不到），不是分歧。另有**一条具名的环境差异**（不是失败、也非静默跳过）：
`E1/E2 未跑：本树无 scratch/` —— 按压/抽查证据按**策略**只存本机 `scratch/`、**不进仓库**
（GOAL-013 授权第 (5) 条与 §5 安全纪律），干净 checkout 天然没有；主树（有 `scratch/`）
仍**强制**要求两份日志存在且内容对得上（`2 passed` / `2 failed`）。

**本 cycle 查出的脚本自身缺陷三处（当轮修掉，如实记录）**：

1. **A4 的口径在提交后才生效 ⇒ 一度把「机器件」当判据点名**。A4 用
   `git diff 50afb3b..HEAD -- apps/web/tests` 枚举「本 GOAL 新增/改动的测试文件」并要求
   登记册逐条登记。cycle 4 里登记册模块与它的机械判据**提交之前是未跟踪**的
   ⇒ 提交那一刻 A4 立刻判红两条：`frontend-criteria-disclosure.ts`、
   `frontend-criteria-disclosure.test.ts` —— **这两条红本身即 A4 非恒真的实测证据**
   （它对「新出现且未登记的测试文件」敏感）。修法：**按名**排除这两个**机器件**
   （`MACHINERY` 常量，只有这两条路径；它们是 EC-03 的执行装置，不是需要被披露的判据）。
   **排除后重新按压证明未削弱**（在 `7d3eecf` 上复按）：临时 worktree 里加一个**新**测试文件并提交
   ⇒ `FAIL A4 git 口径里的判据文件未登记: apps/web/tests/unit/zz-press-new-criterion.test.ts`
   （同时两条机器件**不再**误报）。证据 `scratch/goal013-c4-press-A4.txt`。
   性质披露：A4 是**读 git 历史**的结构判据 ⇒ 只对**已提交**的改动敏感，
   工作树里未提交的新测试文件它**看不见**（这条已写进脚本 docstring）。
2. **E 组把「本机证据策略」误记成失败**：E1/E2 原本无条件要求 `scratch/` 下两份抽查日志，
   于是干净 checkout 必然带两条**永远不可能转绿**的红，会被读成「两棵树不同结论」。
   修法：无 `scratch/` 树记成**具名环境差异**（输出 `ENV` 行），主树口径**不变**。
   这条差异与收口时序项分开列，收口后主树仍为 `failures=0`。
3. **A4 把「已删除的判据文件」也当成未登记项**（改名后暴露：旧名出现在 `git diff` 的删除侧）。
   **修法与边界披露**：A4 只枚举**当前树里存在**的文件；**删除**不再由 A4 兜 ——
   由**仓内机械判据**兜：它对本 GOAL 的每条 `CRITERIA_SPECS` 断言
   `assert.ok(existsSync(...), "判据文件不存在")`（`frontend-criteria-disclosure.test.ts` 判据 ① 首行），
   而矩阵判据 ③ 另要求收敛行点名的 live spec 存在 ⇒ 删除**仍会红**，只是红在别处。
   **实测**：在临时 worktree 里 `git rm` 掉 `live-govern-audit.spec.ts` 并提交后，
   A4 **不再**新增红（`scratch/goal013-c4-press-A4-deleted.txt`：仍只报那个新文件）——
   这条是 A4 的**已知盲区**，如实登记，不当作已解决。

### 六、本地门（**m0 首轮判红两条，均落在本 cycle 自己的新文件上**）

| 门 | 结果 |
| --- | --- |
| `pnpm run test`（unit，含新判据 4 条） | **84 passed / 0 failed** |
| `pnpm run test:e2e:live`（真实数据，`7d3eecf`） | **53 passed** |
| `pnpm run test:e2e`（stub） | **96 passed** |
| web `lint`（`--max-warnings 0`）/ `typecheck` / `build` | 全绿（根 `eslint .` 覆盖 `apps/web/tests/**`） |
| `validate.py` / `docs_consistency_check.py` | 绿 / `DOCS-CHECK PASS: 6 deterministic checks` |
| `m0`（`MEM-20260923-116` 配方） | **22/23**：首轮 `python/tests` 两条红（本 cycle 自己的文件）→ 修 → 复跑后 `python/tests` / `typescript/*` / `framework/validate` / `framework/docs_consistency_check` 等全绿；**唯一未绿项 `framework/validate_bundle` 判红的原因不是本 GOAL 的改动**，见下 |

**m0 首轮的两条真红（`2 failed, 4411 passed`），两条都在本 cycle 新增的文件上**：

1. `tests/architecture/test_module_file_naming.py`：
   `apps/web/tests/unit/frontendCriteriaDisclosure.ts: TypeScript test or fixture filename
   must use kebab-case` —— `tests/` 下的测试/夹具 TS 文件名必须 kebab-case
   （`LEGACY_PATH_EXCEPTIONS` 里那批既有 camelCase 文件是**基线豁免**，并在注释里写明
   「新文件仍受规则约束」）⇒ **改名为** `frontend-criteria-disclosure.ts`，
   **不动门禁、不加豁免**（加豁免就是「改门禁使其通过」，本 GOAL 明文禁止）。
2. `tests/tooling/test_docs_consistency_check.py`：7 条 `[backtick-ref]`——
   新文档把 spec 路径写成**相对 `apps/web`** 的 `tests/unit/...`，而
   `KNOWN_PREFIXES` 含 `tests/` 且按**仓根**解析 ⇒ 解析不到；本仓既有文档
   （`CONSOLE_REAL_DATA_MATRIX.md` / `CONSOLE_PAGE_MAP.md` / `CONSOLE_DELIVERY.md`）
   一律写 `apps/web/tests/...` ⇒ **改齐房规**（7 处）后转绿。

两条修复合并在 `7d3eecf`；修复后 unit / stub / live / typecheck / build / docs 全部**重跑**
（上表数字均取自修复后的树）。

**H1（本 cycle 新加的判组，防同类复发）**：复检脚本扫**已跟踪**的 `.md`，报 basename
会被 Win32 归一化的链接 target（`...` / 尾点）⇒ 主树实测 `checked=50 failures=0`。
口径与跨平台边界见 `MEM-20260923-122`。

**一处必须更正的口径**：第三节之前在本表记过的 `DOCS-CHECK PASS: 6` 是**文档落盘之前**跑的，
不能当作过门证据 —— 文档落盘后该门判红 7 条（上面第 2 条）。改齐后重跑为
`DOCS-CHECK PASS: 6 deterministic checks`。这条更正落在此处，不改旧句不留假绿。

**`framework/validate_bundle` 那条红的归因（实跑成对，不靠推断）**：判词只有一条 ——
`Markdown 本地链接不存在: scratch\self-governance-bootstrap-prompt.md ->
[A-Za-z]:\|/(home|mnt|data|Users`。该文件是**并发写者**今天 02:17 落进 `scratch/` 的
**gitignored** 文档（作者与主题都不属于本 GOAL），它的正文里有一段**正则字面量**恰好长成
Markdown 链接形状；而该判据的链接扫描是**纯文本正则、不识别围栏代码块**
（`validate_bundle.py` 的 `(?<!!)\[[^\]]+\]\(([^)]+)\)` 直接吃全文）⇒ 把「方括号紧接
圆括号」的形状（`[...]` 紧跟 `(...)`）读成一条本地链接。**归因证据（同一脚本、同一命令、只换 `CURSOR_FRAMEWORK_ROOT`）**：

**CI 首轮判红的第三条（同一判据，但根因不同 —— 本 cycle 自己的记录）**：CI 的
`quality-ubuntu-latest` 判红，判词是 `Markdown 本地链接不存在:
.cursor/plans/rechecks/RECHECK-20260923-154-frontend-criteria-disclosure.md -> ...`——
本文件上一行**原文**里我写了链接形状的字面量，其 target 是 `...`。
**为什么本地 m0 看不见**：Win32 会**剥掉尾随的点**，`...` 归一化成「本目录」⇒ `exists()` 为真
⇒ 本地假绿；Linux 上它是普通名字 ⇒ 判红。⇒ 这是一条**平台相关的假绿**，
已落 `MEM-20260923-122`，并把「尾点 target」扫进本复检脚本（见第六节的扫描口径）。

| 跑法 | 结果 |
| --- | --- |
| A：`CURSOR_FRAMEWORK_ROOT=<主树>` | **exit 1**，且**只有这一条** error（`scratch/goal013-c4-validate-bundle-main.txt`） |
| B：`CURSOR_FRAMEWORK_ROOT=<`7d3eecf` 干净 worktree>`（无 `scratch/`） | **exit 0**，全绿（`scratch/goal013-c4-validate-bundle-clean.txt`） |

⇒ 差异**恰好**是那份外来 scratch 文档。**CI 不受影响**：`scratch/` 在 `.gitignore`
（`.gitignore:43`），CI 检出里没有它。**本 GOAL 不处置**：那是别的写者的在制品，
不删不改（并发工作树纪律）；本地 23/23 的复测留给 EC-05 收口时重测，并登记为本 GOAL 的
环境型残余。**不把这条写成「已解决」，也不把它算作本 cycle 的失败。**

### 七、本 cycle 的一处操作陷阱（如实记录）

按压**未跟踪**的新文件（本 cycle 的登记册与文档）时，`git checkout -- <文件>`
**不会**还原改动（文件不在索引里）⇒ 本 cycle 按压后一度把改动留在盘上（判据随即判红）。
处置：改用**手工还原 + 重跑确认 `# fail 0`**。这条已落 `MEM-20260923-121`。

## 结论

`result: PASS`。**GOAL-013 EC-03 达成**：本 GOAL 新增的 **16 条**前端判据，每条都有
① 性质披露（按压对象 + 不敏感面，两栏非空且非空话）、② 自己的红证、
③ 与机械判据核对的同源文档。披露与实际按压结果**一致**，并由**抽查实跑**（按数据绿 /
按页面红，成对）证明为真。

**过门过程如实记录**：功能提交 `5b9f2c2` 后，本地 m0 首轮判红两条（命名门 kebab-case、
文档 `[backtick-ref]`），两条**都在本 cycle 新增的文件上**，当轮修掉并在 `7d3eecf` 合并；
修复后 unit / stub / live / typecheck / build / docs / m0 **全部重跑**。此外**本复检脚本自身**
查出并修掉三处缺陷（A4 的提交后口径、E 组的本机证据策略、A4 对删除项的处置），
其中第三处留下一处**已知盲区**（删除由仓内判据兜，不由 A4 兜）。

## 仍未处理项（如实登记）

- `W-A` 真实控制面对 `sort_analysis_v1` 的 `evidence.read` 仍判 `DENY` —— **需拍板**。
- 路径 (B) 的「重新设计需要什么」5 条 —— **需拍板**。
- `R-M1` Mimosa 钩子侧 `scanner_enobufs` 未得完整结论 ⇒ **不得宣称项目安全**。
- `R-D1` 23 条 Dependabot 告警，本循环不处置。
- `R-N1` 30 条非 ASCII 路径按 AGENTS.md §13 登记豁免。
- `R-F1` 「渲染正确」已操作化为「页面 == 读面 + 成对反证」。
- `R-F2` 数据规模不足时不得计入 ≥6。
- **本 GOAL 仍未达成的 EC**：EC-04（`ops/matrix` 单独处置）、EC-05（收口复检）。
