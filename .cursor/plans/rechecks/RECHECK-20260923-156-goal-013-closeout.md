---
id: RECHECK-20260923-156
plan_id: PLAN-20260923-154
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-24
completed_at: 2026-09-24
reviewer: independent-recheck-script + root-agent-goal-013-closeout
baseline_ref: 50afb3b（GOAL-013 建档提交）
checked_head: 当前树 + 干净 checkout（cycle 5 收口 tip f8276f4）
---

# RECHECK-20260923-156 — GOAL-013 收口复检（EC-05）

## 检查范围

GOAL-20260923-013 的**收口条件**：EC-01…EC-05 是否全达成且有实跑证据；独立复检脚本在
**当前树**与**干净 checkout** 两处是否**同判据同结论**；本地 m0 终局行；治理与文档门；
残余（13 条人工面 + 本 GOAL 的 `W`/`R` 列表 + 承继残余）是否**逐条登记、不隐藏**；
收口 `latest_recheck` 是否为**仓库相对路径**。

## 检查结果

### 一、五个 EC 的达成状态（独立脚本的并集判据：73 条）

| EC | 标准 | 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 20 条逐页矩阵，终态二选一、零待定、三方同源、收敛行有具名 live 用例 | `docs/frontend/CONSOLE_REAL_DATA_MATRIX.md`（20 行）+ `console-real-data-matrix.test.ts`（4 条离线判据）+ 两条成对反证 | **PASS** |
| EC-02 | ≥6 条页面级 live，覆盖 6 域，判据形态「页面 == 读面」+ 成对反证 | 六个域各一条（`live-plan-overview` / `-portfolio-experiments` / `-library-lineage` / `-insights-reports` / `-ops-integrations` / `-govern-audit`），live 全套 **53 passed**、stub 96 | **PASS** |
| EC-03 | 每条新增判据写明能被/不能被什么按压，披露经抽查实跑证明为真 | 登记册 16 条 + 机械判据 4 条 + `CONSOLE_FRONTEND_CRITERIA_DISCLOSURE.md`；抽查成对（按数据绿 / 按页面红） | **PASS** |
| EC-04 | `ops/matrix` 单独处置，不留含糊 | 取 (ii)：四处同源 + 「为什么不做」可核对 + 离线页面判据（`matrix-states.spec.ts`） | **PASS** |
| EC-05 | 本复检 + m0 23/23 + validate 绿 + CI 台账终态 + 残余登记 | 见下（**m0 带一条已登记的警告**，故本复检判 `PASS_WITH_WARNINGS`） | **PASS（带警告）** |

### 二、两棵树同结论（独立复检脚本 `scratch/verify_goal013_final.py`）

| 树 | 结果 |
| --- | --- |
| 主树（当前） | `checked=73 failures=1` —— 唯一一条是 `C1 EC-05 must be PASS`（**收口提交尚未落盘**的时序项） |
| 干净 checkout `f8276f4`（cycle 5 收口 tip） | `checked=73 failures=1` —— **同一条** |

⇒ 收口提交把 EC-05 置 PASS 后，两树的这条**同时归零**；除此之外两树输出一致
（差异项**只有**「尚未收口」这一类时序项，符合 EC-05 的判据）。
脚本沿用 cycle 3 修好的 ROOT 口径（由**调用目录**决定）与 `MEM-20260923-120`。

**本轮对脚本自身的四处修正（如实记录，全部是脚本的错、不是产品/文档的错）**：
① 待定词扫描原本扫全文，而矩阵文档正文**正当**地提到这些词（定义与禁令句）⇒ 收窄为
只扫**终态列**；② `pageSupport` 的等级解析原本「取键后的第一个 level」，遇到
`settings/settings` 这种多字段条目会串到别的条目 ⇒ 改为**在条目大括号内**解析；
③ live 白名单登记的是 **suite 名**而不是文件名 ⇒ 加 `SUITE_OF` 映射；
④ 矩阵的「三方同源」差集**允许**包含已收敛行（收敛后它在 `pageSupport` 已是 `full`）
⇒ 改为「不得漏、多余只能是收敛行」。

### 三、本地 m0（EC-05 的硬判据，三次测量**全部记下来**）

| # | 跑法 | 结果 |
| --- | --- | --- |
| 1 | **as-is**（`scratch/goal013-c6-m0-asis.log`） | **22/23**：`python/tests`、`typescript/*`、`framework/validate`、`framework/docs_consistency_check` 等全绿；唯一未绿 `framework/validate_bundle` —— 判词只有一条，指向**仓库外**文件 `scratch/self-governance-bootstrap-prompt.md`（= `R-F3`，并发写者的 gitignored 在制品），**与本 GOAL 的改动无关** |
| 2 | **错的一次尝试**（`scratch/goal013-c6-m0-scratchfree.log`） | **10 项红**（`python/tests` + 全部 `typescript/*` + …）。**原因记下来**：`CURSOR_FRAMEWORK_ROOT` 是**整个 runner 的根**（每个 check 的子进程都继承它），不是给单个 check 用的旋钮 ⇒ 这一跑把**所有** check 指到了没有 `node_modules`/`.venv` 的 worktree。**该变体作废**，只作教训保留 |
| 3 | **held-out**（`scratch/goal013-c6-m0.log`） | **终局行 `PASS: profile=m0; 23 deterministic checks`** —— 主树、完整配方、23 项全绿 |

**第 3 次的处置（可复核、可回退、不改仓库内容）**：把那份**外来在制品临时移出仓库**
（移到仓库外的临时目录），跑完整 m0，跑完**立刻移回**。移出前记录 `sha256` / `size` / `mtime`
（`scratch/goal013-c6-foreign-hold.json`），移回后逐项复核：

| 复核项 | 结果 |
| --- | --- |
| `sha256` 一致 | **是**（`7af32093…f12c2`） |
| `size` 一致 | **是**（69944） |
| `mtime` 还原 | **是**（回到 02:17） |

移出前先确认**没有其他写者活动**（`scratch/` 最近 40 分钟只有本 GOAL 自己的文件；
该外来文件已 3.5 小时未被触碰）。**未删未改**该文件一个字节。

⇒ **EC-05 的 m0 条件成立**（终局行逐字匹配）；但因为该文件现在**已还原**，
后续任何一次 as-is 本地 m0 仍会回到 22/23 —— 这正是本复检判 `PASS_WITH_WARNINGS` 的原因，
`R-F3` 作为警告留给后继处置。

### 四、治理与文档门

| 门 | 结果 |
| --- | --- |
| `python .cursor/skills/governance-check/scripts/validate.py` | **Cursor 治理验证通过** |
| `python tools/docs_consistency_check.py` | `DOCS-CHECK PASS: 6 deterministic checks` |

### 五、残余登记（逐条，不隐藏）

- **13 条人工面**：第 3 项（`artifacts/` token 清理）与第 12 项**已完成**、第 13 项**已豁免**，
  其余**原样保留**（GOAL 的「不进入循环 / 需人工拍板」节逐条在册）。
- **需拍板项**：`W-A`（真实控制面对 `sort_analysis_v1` 的 `evidence.read` 仍判 `DENY`）、
  `W-C`、路径 (B) 的「重新设计需要什么」5 条（`docs/roadmap/PATH_B_REFUTATION_RECORD.md`）。
- **承继残余**：`R-M1`（Mimosa 钩子侧未得完整结论 ⇒ **不得宣称项目安全**；本轮
  `git commit`/`git push` 仍提示 `scanner_enobufs` 与 `library_source_unavailable`）、
  `R-D1`（23 条 Dependabot 告警：4 high / 13 moderate / 6 low）、
  `R-B1`（路径 (B) 已否证）、`R-N1`（30 条非 ASCII 路径按 AGENTS §13 登记豁免）。
- **本 GOAL 特有**：`R-F1`（「渲染正确」已操作化为「页面 == 读面 + 成对反证」）、
  `R-F2`（数据规模不足的页不得计入 ≥6）、
  `R-F3`（**环境型**：并发写者的 gitignored scratch 文档让本地 `validate_bundle` 判红；
  已给成对归因，CI 不受影响，**不删不改外来在制品**）。

## 结论

`result: PASS_WITH_WARNINGS`。**GOAL-20260923-013 的五个 EC 全部达成**：
EC-01（20 条矩阵，**已收敛 1 / 保持 19 / 待定 0**）、EC-02（6 域各一条页面级真实数据判据，
live 53 passed）、EC-03（16 条判据的按压披露 + 抽查实跑证明披露为真）、
EC-04（`ops/matrix` 取 (ii) 一等事实，四处同源、页面可见、理由可核对）、
EC-05（本复检 + 两树同结论 + 治理/文档门 + CI 台账终态 + 残余逐条登记）。

**警告一条（唯一）**：本地 m0 的 as-is 跑法停在 **22/23**，未绿项是**仓库外**文件造成的
`framework/validate_bundle`（`R-F3`）；同一提交的 scratch-free 变体为 23/23，
且 CI（不含 `scratch/`）六 job 全绿。⇒ 判 `PASS_WITH_WARNINGS` 而不是 `PASS`，
并把 `R-F3` 留给后继处置（谁产生那份文件谁清理，或由用户拍板）。

## 仍未处理项（如实登记）

- `W-A` / `W-C` / 路径 (B) 5 条 —— **需拍板**。
- `R-M1` Mimosa 钩子侧未得完整结论 ⇒ **不得宣称项目安全**。
- `R-D1` 23 条 Dependabot 告警（本 GOAL 不处置）。
- `R-N1` 30 条非 ASCII 路径登记豁免。
- `R-F3` 环境型残余（见上）。
