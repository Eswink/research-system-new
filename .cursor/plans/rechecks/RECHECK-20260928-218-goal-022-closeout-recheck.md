---
id: RECHECK-20260928-218
slug: goal-022-closeout-recheck
title: GOAL-022 收口复检：两树同结论（入口实跑留档）+ 自举实证（EC-02 判据在第一条真实受判记录上真的执法）+ 残余与未覆盖范围逐条
plan_id: PLAN-20260928-217
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-28
completed_at: 2026-09-28
verify_paths:
  - path: 当前树（主干工作树，`D:/research-system`）
    evidence: scratch/goal022-ec04-verdict-current.txt
  - path: 干净 checkout（`git worktree add --detach` @ 5359fab，落点 `D:/research-system-clean-tree`，用后移除）
    evidence: scratch/goal022-ec04-verdict-clean.txt
owners:
  - root-agent
---

# RECHECK-20260928-218 — GOAL-022 收口复检

**复检口径**：不复用任何 PLAN / GOAL 的叙述；每项给出**可复核观察面**。
**未实跑的不记通过**。本轮最要紧的一件事是**自举**：GOAL-022 的 EC-01 交付了一个
「两树复检入口」，EC-04 要求**用这个入口做本轮自己的收口复检** ——
即「机械化**真的被用起来了**」，而不是又一份手工补跑。

**本记录是 EC-02 判据（`tests/architecture/python/test_declared_recheck_paths_have_evidence.py`）
的第一条真实受判记录**：`slug` 以 `closeout-recheck` 结尾、`created_at >= 2026-09-28`
⇒ 它必须声明 `verify_paths` 且**路数 ≥ 2**、每条证据**互不相同**且**在正文被引用**。
下方「二」与「三」即是这件事的观察面。

## 检查结果

### 一、交付面

| # | 观察 | 结果 |
| --- | --- | --- |
| 1.1 | 入口 `tools/two_tree_recheck.py` | **在树**（EC-01 交付物，不是本轮的临时补丁） |
| 1.2 | 入口的判据 `tests/tooling/test_two_tree_recheck_entry.py` | **在树** |
| 1.3 | 本轮收口复检脚本 | `scratch/goal022-ec04-closeout-recheck.py`（12 条判词；只读结构性事实） |
| 1.4 | 新增依赖 / 新增树内文件 | **零**（探针与留档全在 gitignored 的 `scratch/`） |

### 二、两树实跑（EC-04 ①）

命令（`--script-mode shared`：探针在 `scratch/`，两树都取**同一份探针字节**）：

```text
uv run --frozen --no-sync python -B tools/two_tree_recheck.py \
  --script scratch/goal022-ec04-closeout-recheck.py --script-mode shared --root . \
  --verdict-current scratch/goal022-ec04-verdict-current.txt \
  --verdict-clean scratch/goal022-ec04-verdict-clean.txt
```

| 观察 | 结果 |
| --- | --- |
| 当前树 | `exit=0 verdicts=12 sha256=e6febee8713da51c9a166da88f27495a2ec0f036b1f312fdd2e085ce9538bbfb` |
| 干净 checkout | `exit=0 verdicts=12 sha256=e6febee8713da51c9a166da88f27495a2ec0f036b1f312fdd2e085ce9538bbfb` |
| 逐行比对 | `COMPARE identical=True`、**零** `DIFF` 行、**零** `NOT-GREEN` 行 |
| 入口退出码 | `TWO-TREE PASS` / `EXIT=0` |
| 留档 | 两路各自落盘：`scratch/goal022-ec04-verdict-current.txt`、`scratch/goal022-ec04-verdict-clean.txt`；两文件 raw `sha256` **同为** `e6febee8713da51c9a166da88f27495a2ec0f036b1f312fdd2e085ce9538bbfb`，`cmp` = `IDENTICAL` |
| 运行记录 | `scratch/goal022-ec04-two-tree.log` |

**两路不同源**：这一路在**当前树**跑（含本轮尚未提交的记录），另一路在
**干净 checkout**（`git worktree add --detach` 到 `5359fab`）跑，第二棵**由入口自己建、用后自己移除**
（`git worktree list` 复核：只剩 `D:/research-system` 与三个**历史遗留** worktree）。

**12 条判词（两树逐行相同）**：`ec01-entry-and-judge-present` / `ec01-entry-refuses-degradation` /
`ec02-paths-judge-present` / `ec02-requires-two-paths` / `ec03-conventions-judge-present` /
`ec03-doc-clause-and-six-items` / `ec03-registered-in-index` / `protected-judges-present` /
`entry-has-no-drive-letter-path` / `ec01-reverse-proof-case` / `ec01-no-single-path` /
`ec02-not-fed-by-prose`。

### 三、自举实证：EC-02 判据在**第一条真实受判记录**上真的执法（复检**独立**重跑）

EC-02 的复检曾如实登记 `W-1`：「受判集合当前为空 ⇒ 判据今天**没有真实执法对象**；
**会不会在第一条真实记录上生效**要到 EC-04 才算实证」。本节就是那个实证。

| # | 观察 | 结果 |
| --- | --- | --- |
| 3.1 | **受判集合不再为空**：实测扫描面（`slug` 以 `closeout-recheck` 结尾者）**4 → 5** 条（+ 本条 `goal-022-closeout-recheck`）；而**受判**（`created_at >= 2026-09-28`）**0 → 1** 条 —— 那一条就是本条记录 | 判据的 `W-1`（「今天没有真实执法对象」）**在此刻被消除** |
| 3.1b | 判定明细（判据的公开面，不是本记录的自述） | `scan face = 5 \| obligated = 1`；`declared_path_problems(本条) = []`；`outstanding = 0` |
| 3.2 | 本条记录被**真的执法**且判绿 | 定向套件 **全绿**（本记录声明了 `verify_paths` **两路**、证据互不相同、均在正文被引用） |
| 3.3 | **按压**（把本记录 frontmatter 的 `verify_paths` 整块抹掉）⇒ 判据**判红** | **`1 failed, 8 passed`** |
| 3.4 | 逐字节复原（raw `sha256`）⇒ 判绿 | `485fcee7…` 前后一致；复跑 **9 passed** |

**按压记录**：对**本记录自身**做一次临时改写（抹掉 `verify_paths` 整块）⇒ 判据判红，
失败理由**逐字点名本记录**：

```text
AssertionError: 有收口复检的「路数 × 证据」对不上：
  RECHECK-20260928-218-goal-022-closeout-recheck.md: ['缺少 verify_paths（收口复检必须声明它跑过的每一路）']
1 failed, 8 passed
```

随后按 raw `sha256` **逐字节复原**同一文件（`485fcee7c64ef97184f83720a30bf18601473e6c25a57c76a5eb9cb1b3982062`
前后一致）⇒ 判据判绿（**9 passed**）。
这证明判据**不是**只在 `tmp_path` 夹具上成立，而是在**仓库里第一条真实记录**上成立 ——
EC-02 的 `W-1`（「会不会在第一条真实记录上生效」要到 EC-04 才算实证）**因此收口**。

### 四、承继残余逐条在位（EC-04 ⑤）

以 GOAL-20260928-022 正文为观察面（`rg` 逐 ID 计数，均 **≥ 1**）：

| ID | 内容 | 状态 |
| --- | --- | --- |
| `R-M1` | Mimosa 钩子侧 `scanner_enobufs` 未得完整结论 ⇒ **不得**宣称项目安全 | **原样保留** |
| `R-D1` | Dependabot 告警：`yaml` 已升、`vite` 已清；**`undici` 8 条**归上游 | **原样保留** |
| `R-B1` / `R-N1` | 承继残余 / 非 ASCII 路径豁免 | **原样保留** |
| `R-F1` | 收敛 / 一致性判定含主观面时必须先操作化 | **原样保留** |
| `R-F2` | 真实数据 / 调用规模不足时的诚实边界 | **原样保留** |
| `W-4` | 本机 m0 仍同进程跑阈值判据 | **原样保留** |
| `W-5` | 新作业多一次冷装 | **原样保留** |
| `W-6` | `tests/e2e/live_run_support.py` 只剩 1 行余量（规模门禁零余量告警） | **原样保留** |
| `W-10` | 单一共享 token ⇒ 单一主体，**不接受**调用方自报身份 | **原样保留**（本 GOAL 不碰认证面） |
| `W-11` | 对象级授权（BOLA / BFLA）**一个都没做** | **原样保留** |
| `W-12` | **部署面未验证**（反代 / TLS / 多副本） | **原样保留**（本轮**不**把它变成已验证） |

### 五、未覆盖范围逐条明写（EC-04 ⑥）

- **读面未认证**（`GET` / `HEAD` 一律不认证 —— 本 GOAL 未改，也不放行「已加认证」的说法）；
- **多租户 / RBAC / organization scope 未做**；
- **BOLA / BFLA 未做**（`W-11`）；
- **部署面未验证**（反代 / TLS / 多副本；`W-12`）；
- **`R-M1` 未收口** ⇒ **不得**宣称项目安全。
  **本 GOAL 交付的是「复检过程机械化」，过程机械化 ≠ 项目安全。**

### 六、零改动面

| 面 | 结果 |
| --- | --- |
| 六个受保护判据（认证同源 / 话术 / 记录面覆盖 / `m2_audit` / `egress_guard` / m0 CI 覆盖） | **零改动**（探针逐条断言其**在位**；本轮不碰其内容） |
| 既有判据 / 门禁 / 阈值 / 放行面 | **零改动** |
| 产品代码 / Domain / API / schema | **零改动** |
| 依赖 | **零新增** |
| 历史 RECHECK | **零回填**（受判起点 = 建档日，历史记录是不可变证据） |
| 树内新增文件 | **零**（本轮交付的探针与留档全在 gitignored 的 `scratch/`） |

### 七、本次复检**未**复核的面

- **判据的断言集是否完备**：本轮只证明「入口对给定两棵树行为正确」+
  「EC-02 判据在第一条真实记录上执法」，**不证明**收口复检的 12 条断言**覆盖了所有该断言的事**；
- **跨提交形态**：两树比的是**同 tip**（`--base-ref HEAD` = `5359fab`）；跨提交 / 跨平台的形态
  不属本轮用法，**未**复验；
- **`tools/` 的类型与格式**：`tools/` **不在** `PRODUCT_ROOTS` ⇒ 入口**不被** ruff / mypy /
  规模门禁覆盖（承 EC-01 的 `W-1`，收口需改 `PRODUCT_ROOTS` ⇒ 超出本 GOAL 授权）；
- **断言集自身未进树**：收口复检探针落在 `scratch/`（gitignored）⇒ 两树结论**可复跑**但
  **不可随仓库归档**；证据引用因此走「`scratch/` 豁免存在性」这一既有口径（承 EC-02 的 `W-4`）。

### 八、as-is 本机 m0（**记录写入之后**，承 MEM-145）

顺序：**写记录 → 记录面判据 → 全量门**。本轮全量门是**独占**运行的（跑门期间未改工作树），
解释器用仓库 `.venv`（`uv run --frozen --no-sync`），DSN 按既有配方钉死。

| 观察 | 结果 |
| --- | --- |
| 终态行 | `PASS: profile=m0; 23 deterministic checks` |
| `PASS [` 行数 | **24**（`release-assets-immutable` 在计数之外，与既有台账一致） |
| 用例计数 | **4642 passed / 21 skipped** |
| `FAILED` / `ERROR` | **零** |
| 进程卫生 | 跑门前 `tasklist` 零 python 进程；跑门期间不写工作树 |
| 日志与时刻 | `scratch/goal022-ec04-m0.log`；其文件时刻**晚于**本轮记录写入时刻（`PLAN-20260928-217` 的 `ls -l` 时刻 `2026-09-28T05:09:15`）⇒ **门在记录之后**（可用 `ls -l` 复核，不依赖此处抄写的时刻字面） |
| 治理 | `validate.py` = `Cursor 治理验证通过`（含 `DOCS-CHECK`） |

## 结论

**PASS_WITH_WARNINGS。** 六项验收（EC-04 ①…⑥）**全部成立且有实跑证据**：
本轮**用 EC-01 交付的入口**（`tools/two_tree_recheck.py`，**在树**）对**当前树**与
**干净 checkout** 跑了收口复检 —— **两树 12 条判词逐行相同、`sha256` 相同**
（`e6febee8…`）、两路留档 `cmp` 一致、入口 `TWO-TREE PASS` / `EXIT=0`；
**自举实证**成立：本记录是 EC-02 判据的**第一条真实受判记录**，受判集合由 4 条变 5 条，
判据在本记录上**真的执法**（抹掉 `verify_paths` ⇒ 判红；逐字节复原 ⇒ 判绿）；
**承继残余 12 个 ID 逐条在位**、**未覆盖范围五条逐条明写**、
**六个受保护判据与既有门禁零改动、产品代码零改动、零新依赖**。

**警告（如实登记）**：

- **`W-1`**：EC-02 判据的受判起点是**建档日**（2026-09-28），所以 `goal-018`…`goal-021`
  四条历史收口复检**仍在射程之外**（它们是不可变证据，回填等于改写历史）。
  「本仓所有收口复检都已被判据覆盖」**不成立** —— 判据只覆盖**此后新增**的记录。
- **`W-2`**：本轮两树比的是**同 tip**，所以它证明的是「**探针的结论不依赖工作树里
  未提交的残留**」，**不**证明跨提交 / 跨平台行为。
- **`W-3`**：收口复检的**断言集本身**（12 条判词）落在 gitignored 的 `scratch/` ⇒
  **可复跑但不可归档**；引用它依赖「`scratch/` 豁免存在性」这一口径。
  代价是：**别人 clone 仓库后无法直接复核那 12 条判词**，只能按同样的口径重写探针。
- **`W-4`**：`tools/` **不在** `PRODUCT_ROOTS` ⇒ 入口**不被** ruff / mypy / 规模门禁覆盖
  （承 EC-01 `W-1`，**未收口**；收口需改 `PRODUCT_ROOTS` ⇒ 超出授权）。
- **`W-5`**：本轮收口**不包含**任何「授权面 / 认证面」的新结论。
  `W-10` / `W-11` / `W-12` 与 `R-M1` **原样保留** —— 本 GOAL 交付的是
  **复检过程机械化**，它**不等于**项目安全，**不得**引作安全结论。

**未覆盖范围（承 GOAL-022 的边界，原样保留）**：读面未认证 / 多租户与 RBAC 未做 /
BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口（**不得**宣称项目安全）。
