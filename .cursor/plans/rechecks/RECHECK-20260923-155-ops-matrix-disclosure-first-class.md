---
id: RECHECK-20260923-155
plan_id: PLAN-20260923-154
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-24
completed_at: 2026-09-24
reviewer: independent-recheck-script + root-agent-goal-013-ec04
baseline_ref: 0be3efa（cycle 5 = cycle 4 的收口 tip）
checked_head: 当前树 + 干净 checkout（cycle 5 功能提交 168aa48）
---

# RECHECK-20260923-155 — EC-04 `ops/matrix` 取 (ii) 一等事实（GOAL-013 cycle 5）

## 检查范围

`ops/matrix`（20 条里唯一的 `gap`）是否已按 **(ii)** 处置成**一等事实**：
① 「界面状态说明页（非实时运维状态）」在**四处同源**（`pageSupport.reason` /
`CONSOLE_PAGE_MAP.md` 小节 / 矩阵第 15 行 / **页面可见文案**）；
② 「为什么不做实时运维状态」**可核对**（点名真实存在、等级如实的运维页）；
③ 有一条**页面判据**断言该说明文案可见（EC-04 要求 stub 或 live）；
④ 硬约束未破：`reason` 文字与 `level` **逐字未改**、既有 live spec 与 stub spec 未动。

## 检查结果

### 一、四处同源（独立脚本 A 组实查）

| 来源 | 内容（逐字） |
| --- | --- |
| `pageSupport.reason` | 界面状态说明页（非实时运维状态） |
| `CONSOLE_PAGE_MAP.md` §`#/ops/matrix` | 「界面状态说明」+「不冒充实时运维状态」+「**为什么不做实时运维状态**」+ 等级标注 |
| 矩阵第 15 行 | 「界面状态说明页（非实时运维状态）」+ `DESIGN:not-a-live-ops-surface` |
| **页面可见文案** `matrix.hint` | 本页为界面状态说明：呈现加载/空/错误/权限/未知等组件状态，非实时运维状态。 |

四处都含「界面状态说明」且都带**否定说法**（`非/不冒充/不是/不做`），且都提到
「实时运维状态」这一概念 —— 独立脚本 `scratch/verify_goal013_c5.py` 的 A1–A3 实查。

### 二、「为什么不做」可核对（并被自己的判据抓出一处**假声明**）

文档给出的理由**不是**「设计如此」，而是可核对的事实：实时运维状态有它自己的读面与页面
—— `#/ops/observability`、`#/ops/compute`（`FULL`，各有具名读面）与 `#/ops/data-health`
（`partial`，`GET /projects/{id}/ops/data-health` 已交付，未建的是聚合质量报告）。

**本 cycle 的一处实际更正（如实记录）**：我起草时写成「三页均 `FULL`」，
被**本 PLAN 自己的一致性判据**判红（`③ 点名了 ops/data-health，但它在 pageSupport 里不是 full`）
⇒ 回读代码确认 `ops/data-health` 是 `partial`，遂把两处文档与 PLAN 的措辞一并改对。
判据在此处**不是**恒真：它读的是产品源码里的真实等级。

### 三、两条按压（先红后绿，实跑）

| # | 按压对象 | 做法 | 实测 | 证据 |
| --- | --- | --- | --- | --- |
| 1 | **文档源**（page map 小节） | 把「不冒充实时运维状态。」改成肯定式、并把标题「**为什么不做**实时运维状态」改成「为什么做」 | 一致性判据 **1 failed**（判词点名该来源缺否定说法） | `scratch/goal013-c5-press-doc.txt` |
| 2 | **页面那一段**（可见文案） | 给 `matrix.hint` 加 `占位：` 前缀 | 页面判据 **1 failed**（另一条 identity 判据仍绿，成对） | `scratch/goal013-c5-press-page.txt` |

**按压 1 的第一版太弱（如实记录）**：第一次只把「不冒充实时运维状态」改成肯定式，
判据**仍绿** —— 因为同小节里还有「为什么**不**做实时运维状态」这处否定说法，
满足「至少一处否定」的口径。于是把标题也改成肯定式再按，才转红。
这说明判据的口径是「本节不得读成运维状态面」，而不是「某个词必须在」。

### 四、判据性质披露（EC-03 口径）

- **一致性判据**（`apps/web/tests/unit/matrix-disclosure.test.ts`，离线 unit）：
  敏感面是**四处的措辞**（删短语 / 去掉否定 / 点名不存在的路由 / 等级瞎标 ⇒ 红）；
  **不敏感面**是运行时渲染是否正确（它不渲染页面）与读面数据（本页没有数据面）。
- **页面判据**（`apps/web/tests/e2e/matrix-states.spec.ts`，离线 stub）：
  敏感面是**页面那一段**（改文案即红，按压 2 实测）；**不敏感面**是数据 ——
  本页**按设计不消费任何读面**，所以这条判据证明的是「说明文案确实渲染出来了」，
  **不是**「某个读面的值对」。这是本页判据的**固有边界**，不是本 cycle 的疏漏。
- **独立脚本**（`scratch/verify_goal013_c5.py`）：结构判据（存在/包含/等级一致），
  不读断言强弱、不跑浏览器。

### 五、两棵树同结论

| 树 | 结果 |
| --- | --- |
| 主树（当前） | `checked=50 failures=0` |
| 干净 checkout `168aa48` | `checked=46 failures=2`：`F2 PLAN-154 not DONE`、`F5 recheck missing: null` |

干净树多出的两条**全是「尚未收口」时序项**（PLAN 转 `DONE` 与本复检落盘都在收口提交里）；
另有**一条具名环境差异**（`E1/E2 未跑：本树无 scratch/`，按压证据按策略只存本机、不进仓库）。
脚本沿用 cycle 3 修好的 ROOT 口径与 cycle 4 的 `ENV` 记法。

### 六、本地门

| 门 | 结果 |
| --- | --- |
| `pnpm run test`（unit，含新判据 4 条） | **88 passed / 0 failed** |
| `pnpm run test:e2e`（stub，含新 spec 2 条） | **98 passed** |
| `pnpm run test:e2e:live`（真实数据） | **53 passed** |
| 根 `eslint .` / `typecheck` / `build` | 全绿 |
| `validate.py` / `docs_consistency_check.py` | 绿 / `DOCS-CHECK PASS: 6 deterministic checks` |
| m0（`MEM-20260923-116` 配方） | **22/23**（`scratch/goal013-c5-m0.log`）：`python/tests` / `typescript/*` / `framework/validate` / `framework/docs_consistency_check` 等**全绿**；**唯一未绿项 `framework/validate_bundle` 与本 cycle 的改动无关**（= `R-F3`，见下） |

**`framework/validate_bundle` 那条红的归因（成对实跑，与 cycle 4 同口径）**：`R-F3` 未变 ——
并发写者那份 **gitignored** scratch 文档仍在（`scratch/self-governance-bootstrap-prompt.md`，
mtime 02:17），其正文里的正则字面量被该判据的**纯文本**链接扫描读成本地链接。**本 cycle 复测**：

| 跑法（同一脚本、同一命令，只换 `CURSOR_FRAMEWORK_ROOT`） | 结果 |
| --- | --- |
| A：主树 | **exit 1**，`Markdown 本地链接不存在` **1 条**（`scratch/goal013-c5-validate-bundle-main.txt`） |
| B：`168aa48` 干净 worktree（无 `scratch/`） | **exit 0**，该判据全绿（`scratch/goal013-c5-validate-bundle-clean.txt`） |

⇒ 差异**恰好**是那份**仓库外**的在制品；CI 检出无 `scratch/`，**CI 不受影响**。
**不删不改外来在制品**；本地 23/23 的判定留到 EC-05 收口时重测。

**过门过程（如实记录）**：功能提交 `779b8a9` 后本地 `typecheck`/`build` 判红一条 ——
`matrix-disclosure.test.ts` 在 `noUncheckedIndexedAccess` 下把 `string | undefined` 传进
`Map.set` ⇒ 在 `168aa48` 加两行守卫修掉（**不是**改断言，也不是放宽 tsconfig）；
修复后 unit / stub / live / lint / typecheck / build / docs **全部重跑**（上表数字取自修复后）。

## 结论

`result: PASS`。**GOAL-013 EC-04 达成**：`ops/matrix` 以 **(ii) 一等事实**处置 ——
四处同源、页面可见、且「为什么不做实时运维状态」是**可核对**的理由（点名真实页面与等级），
不是一句「设计如此」。硬约束全部守住：`pageSupport.reason` 文字与 `level` 逐字未改
（独立脚本 H1/H2），`presentationPolicy` 与页面组件未动，既有 live/stub spec 未动（G 组）。

## 仍未处理项（如实登记）

- `W-A` 真实控制面对 `sort_analysis_v1` 的 `evidence.read` 仍判 `DENY` —— **需拍板**。
- 路径 (B)「重新设计需要什么」5 条 —— **需拍板**。
- `R-M1` Mimosa 钩子侧未得完整结论 ⇒ **不得宣称项目安全**（本轮 `git commit` 侧提示的
  `scanner_enobufs` / `library_source_unavailable` 同属此项）。
- `R-D1` 23 条 Dependabot 告警；`R-N1` 30 条非 ASCII 路径登记豁免。
- `R-F3` 环境型残余（并发写者的 gitignored scratch 文档让本地 `validate_bundle` 判红）。
- **本 GOAL 仍未达成的 EC**：EC-05（收口复检）。
