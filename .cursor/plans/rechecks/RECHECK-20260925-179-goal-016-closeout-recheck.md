---
id: RECHECK-20260925-179
plan_id: PLAN-20260925-178
attempt: 1
status: VERIFYING
created_at: 2026-09-25
completed_at: null
reviewer: root-agent-goal-016-cycle6 + 独立复检脚本（scratch/goal016-ec06-closeout-recheck.py）
baseline_ref: cycle 5 推送 tip `2293af9`
checked_head: 当前树（记录面 + gitignored 的 scratch/ 复检脚本；**无产品代码改动**）
---

# RECHECK-20260925-179 — GOAL-016 收口复检（cycle 6）

> **状态说明**：本复检**尚未完成**。7 条 AC 里 **5 条已实跑取到结论**（AC-2 / AC-3 / AC-4 /
> AC-5 / AC-6 / AC-7），**AC-1（两棵树同结论）只完成了「当前树」那一半** —— 「干净
> `git worktree` checkout」那一半**必须先有本 cycle 的提交**才能检出并运行 ⇒
> 按「未实跑不得记 PASS」，本文件保持 `status: VERIFYING`、**不写 `result`**，
> 待该半取到同结论后补全。

## 检查范围

① 独立复检脚本在两棵树上同判据同结论（AC-1，**进行中**）；② 脚本**非恒真**（AC-2）；
③ m0 **双终态行**且身份明确（AC-3）；④ 13 项 `D-NN` 终态表（AC-4）；
⑤ 治理与文档门（AC-5）；⑥ 承继残余原样保留（AC-6）；⑦ 零越界（AC-7）。

## 检查结果（已取到的部分）

### 一、AC-2｜复检脚本**非恒真**（已成立）

- 脚本：`scratch/goal016-ec06-closeout-recheck.py`（gitignored，**不入库**）。
- **先红取证**：在 13 项 `D-NN` 终态表**尚未落盘**时运行同一命令 ⇒
  `EC-06 FAIL` 且逐条报出 `EC-06 终态表缺 D-01 … D-13`（**13 条**）、`CONCLUSION failures=1`
  ⇒ 表若被整段删掉会被抓；**不是**「有表才查行」那种恒真写法
  （脚本里对此有显式注释：`不写成「有表才查行」——那样表被整段删掉反而恒绿`）。
- **另一处自我纠错（如实登记）**：脚本首版把「朴素枚举必须数到 0」写反成了
  `if not non_ascii(...)` ⇒ 在**正确**的环境下反而判红（`EC-04 FAIL :: 朴素枚举未复现转义假 0`
  ⇒ `CONCLUSION failures=1`）。修的是**脚本**的判断方向，**不是**判据、不是文档、
  不是仓库配置（未改 `core.quotepath`）。修后 `EC-04 PASS`。
- **另一处环境适配**：`Path.walk(followlinks=False)` 在本仓解释器上抛
  `TypeError: Path.walk() got an unexpected keyword argument 'followlinks'` ⇒ 改用
  `os.walk(path, followlinks=False)`（`node_modules` 里的悬空 pnpm 链接会让 `Path.rglob` 直接炸）。

### 二、AC-1｜当前树已取到结论（**干净 checkout 那一半待补**）

- 命令：`.venv/Scripts/python.exe -B scratch/goal016-ec06-closeout-recheck.py --root .`；
  留档 `scratch/goal016-c6-recheck-worktree.txt`：
  ```
  # tree = D:\research-system
  EC-01 PASS :: 4 passed in 0.31s
  EC-02 PASS :: 4 passed in 0.04s
  EC-03 PASS :: 7 passed in 5.17s
  EC-04 PASS :: 6 passed in 0.23s
  EC-05 PASS :: （无判据文件：本 EC 的结论由结构断言承载）
  EC-06 PASS :: （无判据文件：本 EC 的结论由结构断言承载）
  CONCLUSION failures=0
  REALITY non_ascii=30
  ```
- **脚本的独立性口径**（为什么它不只是把 GOAL 的话重念一遍）：每个 EC 的 PASS 由
  **两路同时成立**给出 —— ① 脚本自己**重新读树**断言结构事实（生产根里点名模板的
  **单一来源**、策略面相对基线 `a3b2cf3` 的 `git diff --name-only` **为空**、
  `package.json` 与 `pnpm-lock.yaml` 的 `vite` 解析版本、`ADR-0031` 前 12 行仍是
  `Status: Proposed` 且全文无 `Status: Accepted` 且含「否证条件」、
  `ADR-0032` 的 **非 ASCII 现实 ↔ 清单双向一致**且计数 = 30、
  朴素枚举**看不到**非 ASCII（转义陷阱方向）、`MODEL_COMPATIBILITY` 含
  「维持派生视图 / 必须先出 ADR」、威胁模型含 `BOLA` / `BFLA` / `未覆盖范围` / `M18`
  与 `## 6.`、六份记录与终态表 13 行在位）；② 该 EC 的判据文件在**被测树**里以
  子进程 `pytest` 实跑（`cwd = 被测树`）。
- **在干净 checkout 上必须同结论**的原因（本仓特有）：`pyproject.toml` 的
  `[tool.pytest.ini_options]` 设了 `pythonpath = ["."]` ⇒ pytest 把 **rootdir** 入
  `sys.path` ⇒ 在 checkout 里跑就是跑**那棵树自己的代码**（若项目改成 editable 安装
  指向工作树，这个验证就会退化成假的）。

### 三、AC-3｜m0 **双终态行**（已成立，两行身份不同、**不可互换**）

- **as-is**（**未**代管，直跑 `run_all_checks.py --profile m0 --keep-going`）：
  **`FAILED: 1 check(s): framework/validate_bundle=1`** ⇒ **22/23**，
  唯一红项 = **`R-3`**；`PASS [` 行数 = **23**（22 项过 + 计数之外的 `release-assets-immutable`）。
  红项判词逐字：`- Markdown 本地链接不存在: scratch\self-governance-bootstrap-prompt.md -> [A-Za-z]:\\|/(home|mnt|data|Users`
  —— 即**仓库外 / gitignored** 的 `scratch/` 文件被 `validate_bundle` 扫到（**别人的**文件，
  与 GOAL-016 的改动无关）。日志 `scratch/goal016-c6-m0-as-is.log`。
- **代管后**（`tools/quarantine_and_run_m0.py` 把该文件临时移出）：
  **`PASS: profile=m0; 23 deterministic checks`**（退出码 **0**、**首次即过**；
  `PASS [` = **24** 行；`FAIL` 行数 = **0**）；逐字节复核**一致**：
  `size=69944` / `mtime_ns=1790187424185178900` /
  `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2`。
  日志 `scratch/goal016-c6-m0-quarantined.log`；轮次输出 `scratch/goal016-c6-m0-quarantine-run.txt`。
- **口径**：**22/23 是 as-is 的**、**23/23 是代管后的**。
  **不得**把任一行读成另一行的意思，**不得**只写一个「23/23」。
- **记录时序声明**：两跑都在**冻结树**上完成；本 RECHECK 的补写发生在其后，属**只写记录**
  （不改判据 / 产品代码 / 门禁 / 阈值 / 依赖 / 文档正文）。

### 四、AC-4｜13 项 `D-NN` 终态表（已成立）

- GOAL-016 落表，列 = **拍板结论 / 本轮是否实施 / 依据 / 不做会怎样**，
  `D-01 … D-13` **逐条在位**（脚本 `EC-06` 会对 13 条逐条查）。
- **汇总**：已实施 **4**（D-01 / D-02 / D-07 / D-08）＋ 部分实施 **2**
  （D-03 只升 high 批；D-09 与 D-08 同轮）＋ 未实施 **6**
  （D-04 / D-05 / D-06 / D-10 / D-11 / D-13，全部因**明文不授权**）。
- **未授权项一律原样保留**：表里逐条写明「未实施（原样保留）」并给出阻断依据，
  **未**被本 GOAL 收口，也**未**被掩盖。

### 五、AC-5｜治理与文档门（已成立）

- `validate.py` ⇒ **`Cursor 治理验证通过`**（首跑曾因 `MEM-20260925-137` 缺四个必需章节而红
  —— 按既有章节集重写该 MEM，**未**改校验器、**未**加豁免；本 cycle 另有一次
  `MEM-20260925-139` 必须同时引用计划与复检 ⇒ 本 RECHECK 的存在即为满足条件）。
- `DOCS-CHECK` ⇒ **`PASS: 6 deterministic checks`**（本 GOAL 全程首跑即过）。

### 六、AC-6｜承继残余原样保留（已成立）

| 残余 | 内容 | 本轮处置 |
| --- | --- | --- |
| `R-3` | 门禁 scoping：`validate_bundle` 扫到仓库外的 `scratch/` 文件 ⇒ as-is 22/23 | **原样保留**（属 **D-10**，未授权；只引用不改） |
| `R-M1` | hook 面安全结论 | **原样保留**（D-12 第 6 节**明确不覆盖**它） |
| `R-D1` | 依赖告警未清部分 | **原样保留**（升级后 open **9**：0 high / 7 medium / 2 low，全在 `undici`(8) 与 `yaml`(1)） |
| `R-B1` | 四个 450 行零余量文件 | **原样保留**（D-05 未授权） |
| `R-N1` | 非 ASCII 历史路径豁免 | **原样保留**；由 `ADR-0032` 记录（**不重命名**，30 条） |
| `W-7` | live 判据会真出网、结论随环境变 | **原样保留**（D-11 未授权；本 GOAL 未改任何 live 开关语义） |

### 七、AC-7｜零越界（已成立）

- 本 cycle 的**入库**改动集**只含记录面**（`.cursor/plans/`、`.cursor/memory/`）；
  复检脚本与全部日志在 `scratch/`（**gitignored ⇒ 不入库**）。
- **不含**：产品代码、门禁脚本、策略面（`policy.yaml` / `_CAPABILITY_SCOPE`）、
  判据口径、阈值、依赖 pin、运行时默认值；**未**动三个并发写者的文件。

## 结论（**部分**）

- **AC-2 … AC-7 成立**；**AC-1 的「干净 checkout」那一半尚未跑**。
- ⇒ **本复检不给出最终结论**（`status: VERIFYING`，无 `result`）；
  **GOAL-016 EC-06 亦保持 `IN_PROGRESS`**，**不记 PASS**。
- 待办（本 cycle 内完成）：在本 cycle 的提交上 `git worktree add` 出干净 checkout，
  用 `--root <checkout>` 跑同一脚本 ⇒ 期望 `CONCLUSION failures=0` 且逐 EC 结论逐字一致；
  取到后补齐本节与 GOAL-016 的 EC-06 / 台账尾巴。
