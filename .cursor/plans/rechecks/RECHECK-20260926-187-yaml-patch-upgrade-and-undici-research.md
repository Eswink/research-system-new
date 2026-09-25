---
id: RECHECK-20260926-187
slug: yaml-patch-upgrade-and-undici-research
title: 独立复检：`yaml` patch 升级（EC-01）+ `undici` 前置调研（EC-02）+ 13 项 `D-NN` 结清（EC-03）
plan_id: PLAN-20260926-186
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-26
completed_at: 2026-09-26
owners:
  - root-agent
---

# RECHECK-20260926-187 — 独立复检（PLAN-20260926-186）

## 检查结果

**复检口径**：不复用 PLAN 的结论叙述，直接读树 + 跑判据；每一项都给出**可复核的观察面**
（命令 / 文件 / 计数）。**未实跑的不记通过**。

### 一、EC-01 交付物：真的只动了 `yaml` 一个包吗

| # | 检查 | 结果 |
| --- | --- | --- |
| 1.1 | `apps/web/package.json` 的 `yaml` specifier | `2.8.4`；文件 **823 字节**（改前同为 823）⇒ 只换了一行，无附带重排 |
| 1.2 | lockfile 变化的包数 | **只有 `yaml`**：diff 覆盖 importer specifier、解析项、`@vitejs/plugin-react` 与 `vite` 的 peer 后缀、`packages`、`snapshots` 五处，全部是 `2.8.1 ↔ 2.8.4` |
| 1.3 | 是否出现第二个包的版本变化 | **无**（逐 hunk 复核 `git diff -- pnpm-lock.yaml`） |
| 1.4 | 是否跨 minor | **否**：`2.8.1 → 2.8.4` 同属 `2.8.x`；`engines: {node: '>= 14.6'}` 未变 |
| 1.5 | 是否覆盖告警修复版本 | 是：`GHSA-48c2-rrv3-qjmp` 的首个修复版本是 `2.8.3`，目标是 `2.8.4`（`2.8.x` 最新 patch） |

### 二、EC-01 门禁：六道 web 门 + 根 check + m0

| # | 检查 | 结果 |
| --- | --- | --- |
| 2.1 | `pnpm --dir apps/web lint` | 退出 0（`eslint src --max-warnings 0`） |
| 2.2 | `pnpm --dir apps/web typecheck` | 退出 0（`tsc --noEmit`） |
| 2.3 | `pnpm --dir apps/web test` | **88 passed** |
| 2.4 | `pnpm --dir apps/web build` | 成功（`tsc --noEmit && vite build`，1001 modules transformed） |
| 2.5 | `pnpm --dir apps/web test:e2e`（stub） | **98 passed**（3.6m） |
| 2.6 | `pnpm --dir apps/web test:e2e:live` | **53 passed**（`RESEARCHOS_LIVE_E2E` 未设 ⇒ 无 LLM 出网，跑的是本地 console-live 面） |
| 2.7 | 根 `pnpm run check` | 退出 0（format:check + lint + typecheck + boundaries + 19 个 node 测试） |
| 2.8 | 设计基线 | `design-outline-guard.spec.ts` **6 passed**；`git diff -- apps/web/tests/e2e/design-outlines.json` **空**；**容差未动**（未触发重生成） |
| 2.9 | m0 全量（canonical 调用、独占、DSN 固化、`--keep-going`） | **`PASS: profile=m0; 23 deterministic checks`**；`PASS [` = 24；`FAILED`/`ERROR` 零命中；日志 `scratch/goal018-c1-m0.log`（1640 行） |

### 三、EC-02 调研：结论可拍板吗、有没有偷偷升级

| # | 检查 | 结果 |
| --- | --- | --- |
| 3.1 | 结论文档在位 | `docs/roadmap/UNDICI_TRANSITIVE_DEPENDENCY_RESEARCH.md` |
| 3.2 | 问题①（上游是否有带 `undici@6`+ 的版本） | 有答案 + 依据：33 个版本逐个读 `dependencies` ⇒ **1.x 全线 `undici ^5`；2.x 起 `dependencies` 为空**；2.x 的 peer 要求（`@bufbuild/protobuf ^2.x`、`@connectrpc/connect 2.x`）与 `engines` 一并列出；并**否证**了「升 `@cursor/sdk` 即可」这条路径（最新 `1.0.32` 仍声明 `^1.6.1`） |
| 3.3 | 问题②（pnpm `overrides` 是否安全） | 有答案 + 依据：影响面实测为 **1 个包 / 1 个 import**；列出两种写法、逐条回归风险（越界 / 主版本破坏面 / engines 收窄 —— 并指出 `undici@8` 要 `node >=22.19.0` 而本树是 `22.18.0` ⇒ 上限是 `7.30.0`）/ 回滚方式 / 「告警消失 ≠ 风险已评估」 |
| 3.4 | 问题③（8 条告警的实际可利用性） | 有答案 + 依据：**谁调用**（唯一 importer = 框架技能脚本；CI 只做 prettier 检查）/ **什么路径**（`node-headers-polyfill.js` 的 `Headers`，`if (major < 18)` 守卫 ⇒ Node 22.18.0 下**死分支**）/ 逐条可达性表 + **诚实边界**（import 仍会求值、不得据此宣称安全、`undici-types` 不参与计数） |
| 3.5 | 结论是否**可拍板** | 是：明确「**不可在本仓正确升级**」+ 归属方（`@cursor/sdk` 的上游）+ 单独授权清单（§5.3） |
| 3.6 | **反证**：`undici@5.29.0` 是否被改动 | **未改动**：`grep -n "undici: 5.29.0" pnpm-lock.yaml` 命中**恰好 1 条**，仍在 `@connectrpc/connect-node@1.7.0` 的依赖块内 |
| 3.7 | **反证**：是否写入 overrides | **否**：`package.json` / `apps/web/package.json` 均无 `overrides` / `resolutions` / `packageExtensions` |

### 四、EC-03 决案结清：13 项是不是都有唯一终态

| # | 检查 | 结果 |
| --- | --- | --- |
| 4.1 | 简报终态表 | 13 行（`D-01`…`D-13`），终态全部取自四值词汇表，依据列非空壳 |
| 4.2 | GOAL-018 人工面声明 | 13 条 `**D-NN 终态 = …**`，与终态表**逐条同词** |
| 4.3 | 零「待定」 | 是：汇总 = 已实施 **9** + 部分实施 **1**（D-03）+ 已拍板为维持现状 **3**（D-04 / D-05 / D-06）= **13**，**未授权待拍板 0** |
| 4.4 | 对齐表状态列 | 全部取自封闭词汇表（终态四值 + `待拍板` / `标准禁令` / `已了结`） |
| 4.5 | 是否**只增不减** | 是：既有四条按压（删简报条目 / 空要素 / 删对齐行 / 删非编号行）**原样保留**；既有六要素、孤儿、对齐规则**未删** |
| 4.6 | 判据实跑 | `tests/tooling/test_pending_decisions_briefing.py` **14 passed**（1 现状 + 13 按压） |
| 4.7 | 判据**非恒真**（成对） | 删终态行 / 置空状态（归一化后为空）/ 行形状坏掉 / 改模糊表述 / 两侧终态不一致 / 少一条 GOAL 声明 / 多出无人认领的编号项 ⇒ **各判红且报出预期消息**；未改动 ⇒ **绿**。日志 `scratch/goal018-c1-ec03-press.log` |
| 4.8 | 按压是否真的落在判据上 | 是 —— **第一版按压不是**：按行首删行命中了简报里**同形状的索引表**（也以 `| D-05 | …` 开头），判据没被触碰。改为**只在终态表块内**替换后按压才生效（见 W-1） |

### 五、交叉面

| # | 检查 | 结果 |
| --- | --- | --- |
| 5.1 | `tests/tooling` 全量 | **1169 passed** |
| 5.2 | `ruff check` / `ruff format --check` | `All checks passed!` / 已格式化 |
| 5.3 | 规模门禁（450 行 / 50 行函数） | `test_python_source_limits.py` **1029 passed**；改动文件 `test_pending_decisions_briefing.py` = **399 行** |
| 5.4 | 治理校验 | `validate.py` = `Cursor 治理验证通过` |
| 5.5 | 文档一致性 | `DOCS-CHECK PASS: 6 deterministic checks` |
| 5.6 | 鉴权 / 中间件 / 路由保护改动 | **零**（甲的内容未触碰） |
| 5.7 | `ADR-0031` 的 `Status` | 未触碰 |

## 结论

**`PASS_WITH_WARNINGS`**。

- **EC-01**：`yaml` 只升 patch 且**只动这一个包**；六道 web 门 + 根 check + m0 全绿；
  设计基线**逐字节未改**（无漂移 ⇒ 未重生成）；**CI 八 job** 的证据由 GOAL-018 的台账登账。
- **EC-02**：三问各有**可复核**答案与依据，结论**可拍板**（不可在本仓正确升级 + 归属方）；
  **零升级动作**已由两条反证（`undici@5.29.0` 未改 + 无 `overrides` 字段）钉住。
- **EC-03**：13 项终态齐、唯一、同词、零「待定」；判据**只增不减**且**13 条按压全部判红**。

**Warnings（如实登记，不构成不通过）**：

- **W-1｜按压必须落在判据自己的块内**：简报里存在**同形状**的两张表（索引表与终态表都以
  `| D-05 | …` 开头）⇒ 「按行首删一行」的按压会命中错的那张、**看着红其实没动判据**。
  这正是 `MEM-20260925-141` 记的「判据自身恒真」那一类；本 PLAN 已把按压改为
  **块内替换**（`_terminal_block` + 块内未命中即断言失败），但**同类风险**在别的判据里仍需逐一自查。
- **W-2｜CI 证据在 GOAL 侧登账，不在本复检内**：本记录只对**本地可验证面**给结论；
  `git push` 后的 M0 八 job 与 CodeQL 由 GOAL-20260926-018 的 CI 台账记录
  （**flake 判定必须靠同一代码的复跑对照**）。
- **W-3｜`undici` 的可利用性评估有前提**：结论是「当前 Node（22.18.0）+ 当前调用路径下不可达」，
  **不是**「无风险」；若 Node 降到 < 18、或本仓开始直接调用 undici 客户端 API、
  或 `connect-node` 改用 undici 做传输 ⇒ **该评估立即失效**（已写进结论文档 §4.4）。
- **W-4｜`undici` 告警仍挂在告警面上**：8 条（6 medium + 2 low）**原样保留**；
  缓解动作在**本仓之外**（`@cursor/sdk` 上游），本 PLAN 只登记，**不得**读成已解决。
- **W-5｜本机与 CI 的 Node 版本一致但**都 `22.18.0`**：若将来授权 overrides 提到 `undici@8`
  会撞 `engines`
  （`>=22.19.0`）——上限是 `7.30.0`；这一点只在结论文档里登记，本 PLAN 不实施。
- **W-6｜`R-M1` 原样保留**：Mimosa 钩子侧 `scanner_enobufs` 仍未得完整结论
  （本 PLAN 的 `commit` / `push` 两次钩子都如实报了该状态）⇒ **不得**宣称项目安全。
