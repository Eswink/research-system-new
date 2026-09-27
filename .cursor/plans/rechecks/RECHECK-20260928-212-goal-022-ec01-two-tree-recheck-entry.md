---
id: RECHECK-20260928-212
slug: goal-022-ec01-two-tree-recheck-entry
title: GOAL-022 EC-01 独立复检：两树入口行为 11/11 + 按压红与逐字节复原 + 真实两树 12×2 同结论 + 受保护判据与产品代码零改动
plan_id: PLAN-20260928-211
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-28
completed_at: 2026-09-28
owners:
  - root-agent
---

# RECHECK-20260928-212 — GOAL-022 EC-01（两树复检的机械化）

## 检查结果

**复检口径**：不复用 PLAN 的结论叙述；每一项给出**可复核观察面**（命令 / 文件 / `sha256`）。
**未实跑的不记通过**。复检脚本 `scratch/goal022-ec01-recheck.py`（只读，12 条判词）。

### 一、交付面

| # | 观察 | 结果 |
| --- | --- | --- |
| 1.1 | `tools/two_tree_recheck.py` | 在位，**301 行**，raw `sha256` = `3c6262c0070b33f86dac51d10382e326df6202c07c8fdd509d6b107a13b1560e`（纯 LF）；`ruff format --check` **clean**（自愿纪律，`tools/` 不在该 check 的扫面内） |
| 1.2 | `tests/tooling/test_two_tree_recheck_entry.py` | 在位，**277 行**，**11 passed**；`ruff format --check` **clean** |
| 1.3 | `docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md` | 在位，**68 行**，含条款小节 + 六条口径 |
| 1.4 | `bb7a7ec` 的改动面 | **恰好 3 个文件**（上述三项）⇒ 无夹带；`5e73211` 的改动面 = **2 个文件**（纯格式化） |

### 二、行为面（复检**独立**跑，不采信 PLAN 的转述）

| # | 观察 | 结果 |
| --- | --- | --- |
| 2.1 | 两树同结论 | `TWO-TREE PASS` / `exit=0` / 两份判词 `sha256` 相同 |
| 2.2 | **反证：第二树不同** | `COMPARE identical=False` + `DIFF 第 1 行：current='PASS probe-marker value=same' clean='PASS probe-marker value=different'` + `TWO-TREE RED` + **`exit=1`** |
| 2.3 | 输出不纯（非判词行） | `SETUP 入口失败：输出不纯：出现非判词行 -> 'elapsed 0.0000s'` + `exit=2`；**无** `TWO-TREE PASS` |
| 2.4 | 判词嵌本树路径 | `SETUP 入口失败：判词与路径相关（含 …）-> 'PASS probe-pathy root=…'` + `exit=2`；**无** `TWO-TREE PASS` |
| 2.5 | 干净树缺失（**只跑一路**） | `SETUP 入口失败：干净树不存在：…` + `exit=2`；**无** `TWO-TREE PASS` ⇒ 不会降级成单树 PASS |
| 2.6 | 两树都不绿但判词相同 | `NOT-GREEN` 登记 + `exit=1` ⇒「一致」没有被当成「成立」 |
| 2.7 | 两树脚本字节不同 | `SETUP 入口失败：两树的复检脚本字节不同 ⇒ 比的不是同一组断言` |
| 2.8 | 共用解释器 | 两棵树记录到的 `sys.executable` 相同，且等于调用入口的解释器 |

### 三、真实两树实跑（不是 tmp 夹具）

| # | 观察 | 结果 |
| --- | --- | --- |
| 3.1 | 命令 | `tools/two_tree_recheck.py --script scratch/goal022-ec01-recheck.py --script-mode shared --root . --base-ref HEAD --worktree-dir …` |
| 3.2 | 当前树 | `D:\research-system` exit=0 verdicts=**12** sha256=`7af577bb…` |
| 3.3 | 干净 checkout | `git worktree add --detach <dir> HEAD`（同 tip `bb7a7ec`）⇒ exit=0 verdicts=**12** sha256=`7af577bb…` |
| 3.4 | 逐行比对 | `COMPARE identical=True` / `TWO-TREE PASS` / **`EXIT=0`** |
| 3.5 | 落档 | `scratch/goal022-ec01-verdict-current.txt` / `-clean.txt`；`cmp` **IDENTICAL**；两份 raw `sha256` **相同** |
| 3.6 | 进程卫生 | worktree **已移除**（`ls` 不存在）；`tasklist` python 进程 **0** ⇒ 零泄漏 |

### 四、按压面（复检**独立**重跑 + 逐字节复原）

| # | 观察 | 结果 |
| --- | --- | --- |
| 4.1 | 破坏比对逻辑（`compare_runs` 首行插 `return True, []`） | 判据 **`1 failed, 10 passed`**；红的是 `test_second_tree_differing_makes_the_entry_red` ⇒ 判据对「入口退化成打印两份」敏感（**在终态字节上重做**） |
| 4.5 | 全量门独立抓到的**真红** | 首跑全量门 = `FAILED: 1 check(s): python/format-check=1`（两个新文件的探测串引号形态不符 `ruff format`）。**复检不采信「定向判据绿」**：该 check **只**在全量门里跑 ⇒ 修复 `5e73211` 后复跑得 `PASS: profile=m0; 23 deterministic checks` |
| 4.6 | 修复后的按压是否仍然成立 | 格式化改变了入口字节 ⇒ 按压与复原**重跑**（4.1 / 4.2 均为新值）⇒ **不复用**格式化之前的证据 |
| 4.2 | 逐字节复原 | raw `sha256` = `3c6262c0070b33f86dac51d10382e326df6202c07c8fdd509d6b107a13b1560e`，**与按压前一致**（在**终态字节**上重做：格式化后此值由 `82dda861…` 变为本值，故按压与复原**重跑一遍**，不复用旧证据） |
| 4.3 | 复原后复跑 | **`11 passed`** |
| 4.4 | 复原证据形态 | 用 **raw `sha256`** 而非 `git diff`（承 `MEM-20260927-152`：`.gitattributes` 归一化会吞掉行尾差异） |

### 五、口径可复跑检查（规范页第 ③ 条）

| # | 观察 | 结果 |
| --- | --- | --- |
| 5.1 | 文本模式读写是否改字节 | 临时文件实测 `byte-identical False`（Windows：`\n` → `\r\n`）⇒ 规范页第 ③ 条在本机**可复现**，不是照抄历史结论 |

### 六、零改动面

| # | 观察 | 结果 |
| --- | --- | --- |
| 6.1 | 六个受保护判据（自 GOAL-021 收口 `2f87812` 起） | `test_control_plane_auth_same_source.py` / `test_reproducibility_wording.py` / `test_record_face_is_covered_by_the_gate.py` / `test_m2_audit.py` / `tests/egress_guard.py` / `tests/tooling/test_m0_ci_coverage.py` —— **全部 UNCHANGED** |
| 6.2 | 产品代码（自 `2f87812` 起） | `apps` / `services` / `packages` / `adapters` **零改动**（`git diff --stat` 空） |
| 6.3 | m0 条数 | 新判据落 `tests/tooling/`（`python/tests` 收集面内）⇒ 仍是 **23**（本 cycle 的全量门另行复跑） |
| 6.4 | 依赖 | 入口只用标准库 + 既有 `git` ⇒ **零**依赖改动 |

### 七、本次复检**未**复核的面（范围的诚实边界）

- **EC-01 之外的 EC**（EC-02 多路证据判据 / EC-03 规范六条的判据计数 / EC-04 收口）
  本复检**不覆盖**；它们由后续 cycle 各自的 RECHECK 承载。
- **Linux 侧的入口行为**未逐条复验：本复检在本机（Windows）跑。CI 的
  `quality-ubuntu-latest` 覆盖的是**判据运行**面（`pytest tests/` 会跑到本判据），
  不覆盖「`git worktree` + `taskkill` 的平台分支」本身。
- **m0 全量门**不在本脚本内跑（按 MEM-145 的顺序，记录写完之后单独跑）。
  **本 cycle 的实测结果**：`PASS: profile=m0; 23 deterministic checks`（`PASS [` = 24、
  **4625 passed / 21 skipped**、零 `FAILED` / `ERROR`；日志 `scratch/goal022-c1-m0-final3.log`），
  **第 5 轮**才拿到终态行。
- **`framework/run_cursor_framework_evals` 的环境类 flake（本 cycle 复检独立观察到的新事实）**：
  5 轮全量门里 **3 轮**红在该 check，签名恒为 `PermissionError: [WinError 5]` at
  `hooks/common.py:161` 的 `os.replace`。**独立取证**：① **单跑该 check 3/3 全 PASS**；
  ② **复现实验**：连跑「`run_cursor_hook_evals` + `run_cursor_framework_evals`」3 轮
  ⇒ **第 1 轮红、第 2/3 轮绿** ⇒ 根因是**前序活动遗留的文件句柄**在短时间内仍持有目标文件
  （Windows 上 `os.replace` 报 ACCESS_DENIED），**非**代码缺陷。本会话 7 次全量门命中 **4 次**
  ⇒ 登记为**环境残余观察**（**未改 check、未改阈值、未查产品代码**）。

## 结论

**`PASS_WITH_WARNINGS`**。EC-01 的六项验收全部成立且有**实跑证据**：
入口对两棵树跑同一组断言并逐行比对（真实两树 12×2 同结论、`sha256` 相同）、
三条环境口径**各有行为判据**、只跑一路**不可能**（拒绝服务而非降级）、
SOP 条款**被判据钉住**（改名即判红）、反证**真的会红**（`exit=1` + 点名差异行）、
判据**被按压**且**逐字节复原**。**既有判据零改动、产品代码零改动、零新依赖。**

**本轮被全量门抓到并修掉的真红（1 处）**：`python/format-check`（新文件的探测串引号形态）。
**定向判据全绿仍然被全量门判红** ⇒ 与 GOAL-021 cycle 1 的 `python/typecheck` 是**同一形态**：
某些 check **只**在全量门里跑。修复 `5e73211` 为**纯格式化**（无语义变化），
且因其改变了入口字节 ⇒ **按压与复原在终态字节上重跑**，不复用旧值。

**警告（如实登记）**：

- **`W-1`**：`tools/` **不在** `PRODUCT_ROOTS` 内 ⇒ 入口**不被** ruff / mypy / 规模门禁覆盖。
  本 cycle 的对策是「由 `tests/tooling/` 判据按**行为**钉住 + 自愿遵守规模与风格」，
  但**类型与格式**确实没有机器门。**未收口**（收口它需要改 `PRODUCT_ROOTS`，
  而那会改既有门禁的覆盖面 ⇒ 不在本 GOAL 授权内）。
- **`W-2`**：判据的**行为面**是「入口对给定两棵树的行为」；它**不证明**任何具体收口复检的
  **断言集**是对的（断言集由各自的复检脚本承载）。
- **`W-3`**：真实两树实跑那次比的是**同 tip 的两棵树**（`--base-ref HEAD`）。
  「结论是否依赖未提交产物」这一面由该形态排除；但**跨提交**（两树不同 tip）不属本入口用法。
- **`W-4`**：第 ③ 条口径的**可复跑检查**只在本机（Windows）实测到危害；非 Windows 平台
  该检查会输出 `True`（危害不出现）⇒ 规范仍然适用，但**该条在本平台的证据形态**是「复现」，
  在别的平台是「不适用」。**未跨平台复验**。
- **`W-5`**：工作树里存在**三个历史遗留 worktree**（`g013final` / `goal015-c3-clean` /
  `rs-goal018-clean`，属 GOAL-013/015/018）。本入口**只清理自己建的**那一棵；
  这三个**不在本 GOAL 范围**，**原样保留**（删除它们会动到别的 GOAL 的证据面）。
- **`W-6`（本 cycle 新观察，值得单列）**：`framework/run_cursor_framework_evals` 的
  `WinError 5` flake 在本会话**不再是偶发**——7 次全量门里命中 **4 次**，且**连续命中 3 次**。
  取证已把根因收敛到「前序遗留句柄」的竞态（见第七节），**没有**改任何 check。
  但它意味着**「跑一次全量门就拿到终态行」在本机不再可靠** ⇒ 后续 cycle 的
  `per_cycle_minutes` 预算要按「可能要多轮」估。**未收口**（收口需要动
  `atomic_json` 的重试语义 ⇒ 那是改产品 hook，超出本 GOAL 授权）。

**未覆盖范围（承 GOAL-022 的边界，原样保留）**：读面未认证 / 多租户与 RBAC 未做 /
BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口（**不得**宣称项目安全）。
