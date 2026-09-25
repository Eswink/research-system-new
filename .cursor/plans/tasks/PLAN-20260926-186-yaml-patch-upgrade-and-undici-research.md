---
id: PLAN-20260926-186
slug: yaml-patch-upgrade-and-undici-research
title: GOAL-018 cycle 1（EC-01 + EC-02 + EC-03）：`yaml` patch 升级 + `undici` 前置调研（零升级）+ 13 项 `D-NN` 决案结清
status: DONE
created_at: 2026-09-26
updated_at: 2026-09-26
parent_goal: GOAL-20260926-018
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260926-018 的 **EC-01**（`yaml` patch 升级）/ **EC-02**（`undici` 前置调研，
    **零升级**）/ **EC-03**（13 项 `D-NN` 决案结清）。授权沿用该 GOAL 的 `child_plans` 与
    `push-to-main-for-CI` 口径：**只推 main、不 force、不重写历史、不推旁支**；
    授权面**仅限**此三项，**不扩面**。**明文不做**：`undici` 升级（含 pnpm `overrides`）、
    hook 检测层安装、**任何鉴权 / 中间件 / 路由保护改动**（甲的内容）、D-01(a) / D-02(a) /
    D-12(a)、`ADR-0031` 的 `Status`、`yaml` 跨 minor。本 PLAN **不放宽任何判据 / 阈值 /
    放行面**，**不新增策略面 allow**，**不改 Canonical State 边界**。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260926-187-yaml-patch-upgrade-and-undici-research.md
memory_entries:
  - .cursor/memory/entries/MEM-20260926-142-patch-means-latest-patch-and-a-research-needs-a-verdict.md
---

# PLAN-20260926-186 — `yaml` patch 升级 + `undici` 前置调研 + 13 项决案结清

## 目标

把 GOAL-018 收尾轮里**互相独立**的三件事一次做完：

1. **EC-01 `yaml` patch 升级**：`apps/web/package.json` 的 `yaml` `2.8.1 → 2.8.4`
   （`2.8.x` 的**最新 patch**；告警 `GHSA-48c2-rrv3-qjmp` 的首个修复版本是 `2.8.3`，
   目标版本覆盖它）⇒ **只升一个包、只升 patch**，lockfile 除它之外**零变化**。
2. **EC-02 `undici` 前置调研（零升级）**：产出一份**可拍板**结论文档，回答三问
   （上游是否有带 `undici@6`+ 的版本 / pnpm `overrides` 是否安全 / 8 条告警的实际可利用性），
   并在简报 D-03 留下处置；**反证**：`pnpm-lock.yaml` 的 `undici@5.29.0` **一字不动**。
3. **EC-03 13 项 `D-NN` 决案结清**：给每项**唯一终态**（四值词汇表），
   **D-04 / D-05 / D-06 取维持现状**，**零「待定」**；判据**成对可按压**。

## 验收条件

- **AC-1（EC-01）**：`git diff` 证明**只有** `yaml` 一处 specifier 与它的 lockfile 解析项变化
  （`2.8.1 → 2.8.4`），**不得**出现第二个包的版本变化。
- **AC-2（EC-01）**：全量 web 门全绿——`lint` / `typecheck` / `test`（unit）/ `build` /
  `test:e2e`（stub）/ `test:e2e:live`，另加根 `pnpm run check`
  （format:check + lint + typecheck + boundaries + test）。
- **AC-3（EC-01）**：**设计基线不漂移**——`design-outline-guard` 绿且
  `apps/web/tests/e2e/design-outlines.json` **逐字节未改**；若漂移则按既有配方重生成 + 目检
  （**不得**调容差）。
- **AC-4（EC-01）**：`make validate-all` 等价的 canonical 调用（`uv run --frozen --no-sync
  python -B <runner> --profile m0 --keep-going`，独占、DSN 固化）到
  `PASS: profile=m0; 23 deterministic checks`。
- **AC-5（EC-02）**：结论文档在位且**三问各有答案与依据**；`pnpm-lock.yaml` 的
  `undici@5.29.0` 与 `@connectrpc/connect-node@1.7.0` 快照**逐字节未改**；
  `package.json` **未新增** `pnpm` / `overrides` / `resolutions` 字段；结论**可拍板**
  （给出"可升 / 不可升"+ 归属方）。
- **AC-6（EC-03）**：13 项 `D-NN` 在**简报终态表**与 **GOAL-018 人工面声明**里**逐条同词**
  （四值词汇表，零「待定」）；对齐表状态列取自**封闭词汇表**；
  机械判据（扩展后的 `tests/tooling/test_pending_decisions_briefing.py`）绿。
- **AC-7（EC-03）**：**反证成对**——删终态行 / 置空状态 / 改模糊表述 / 两侧不一致 /
  多出无人认领的编号项 ⇒ **判红**；未改动时 ⇒ **绿**。
- **AC-8**：`ruff check` / `ruff format --check` / `mypy` 绿；`tests/tooling` 全量绿；
  规模门禁（450 行文件 / 50 行函数）绿；治理 `validate.py` 绿。

## 实施清单

- [x] **WP1｜EC-01 `yaml` patch 升级**：`apps/web/package.json` `yaml: 2.8.1 → 2.8.4`
      + `pnpm install` 更新 `pnpm-lock.yaml`；逐 hunk 复核 lockfile 只有 `yaml` 变化。
- [x] **WP2｜EC-02 `undici` 前置调研**：新增 `docs/roadmap/UNDICI_TRANSITIVE_DEPENDENCY_RESEARCH.md`
      （三问 + 结论 + 复现命令）；在 `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的 D-03 记处置。
- [x] **WP3｜EC-03 决案结清**：简报新增「13 项 `D-NN` 终态表」+ 对齐表状态列改为封闭词汇表
      + D-04 / D-05 / D-06 逐条落「拍板结果」；GOAL-018 人工面为 13 项补 `**D-NN 终态 = …**`
      声明；扩展既有判据使其**可按压**。
- [x] **WP4｜本地验证**：web 六道门 + 根 `check` + m0 全量 + 定向套件 + 规模门禁 + 治理校验。

## 证据

- **EC-01 版本面**：`apps/web/package.json` `"yaml": "2.8.4"`（823 字节，与改前同字节数 ⇒
  只换了一行）；`pnpm-lock.yaml` 的 5 处 `2.8.1 → 2.8.4`（importer specifier / 解析项 /
  `@vitejs/plugin-react` 与 `vite` 的 peer 后缀 / `packages` / `snapshots`），
  **其余包零变化**。
- **EC-01 门禁面**：`lint` 退出 0；`typecheck` 退出 0；unit **88 passed**；
  `build` 成功（1001 modules transformed）；stub e2e **98 passed**（3.6m）；
  live e2e **53 passed**（`RESEARCHOS_LIVE_E2E` 未设 ⇒ 走本地 console-live 面，无 LLM 出网）；
  根 `pnpm run check` 退出 0（含 19 个 node 测试）。
- **EC-01 基线面**：`design-outline-guard.spec.ts` **6 passed**；
  `git diff -- apps/web/tests/e2e/design-outlines.json` **空**（逐字节未改）⇒ **无漂移**，
  因此本 PLAN **未**触发重生成。
- **EC-01 m0**：`PASS: profile=m0; 23 deterministic checks`（`PASS [` = 24，
  `FAILED`/`ERROR` 零命中，日志 1640 行 = `scratch/goal018-c1-m0.log`）。
- **EC-02**：`docs/roadmap/UNDICI_TRANSITIVE_DEPENDENCY_RESEARCH.md` 在位；
  关键事实均有可复核来源（npm registry 元数据 / Dependabot REST / `node_modules` 里的
  `node-headers-polyfill.js`）；`undici@5.29.0` 在 lockfile 里**唯一入边 1 条**；
  结论 = **不可在本仓正确升级**（1.x 全线带 `undici ^5`；2.x 不再依赖 undici 但为破坏性主版本，
  且 `@cursor/sdk` 最新版仍锁 `^1.6.1`）⇒ 取维持现状并登记。
- **EC-02 反证**：本 PLAN 的 `pnpm-lock.yaml` 唯一改动是 `yaml`；
  `grep -n "undici: 5.29.0" pnpm-lock.yaml` 仍命中**恰好 1 条**；
  `package.json` 无 `overrides` / `resolutions` 字段。
- **EC-03**：简报终态表 **13 行** + GOAL-018 人工面 **13 条声明**（`D-01`…`D-13`，逐条同词）；
  汇总 = 已实施 9 + 部分实施 1 + 已拍板为维持现状 3 = 13，**未授权待拍板 0**。
- **EC-03 判据**：`tests/tooling/test_pending_decisions_briefing.py` **14 passed**
  （1 条现状断言 + 13 条按压/反证）；按压日志 `scratch/goal018-c1-ec03-press.log`。
- **EC-03 一次判据自身缺陷（当场发现并修）**：按压第一版用「按行首匹配」删行，命中的是简报里
  **同形状的索引表**（也以 `| D-05 | …` 开头）⇒ **看着变红其实没动判据**（正是
  `MEM-141` 记的「判据自身恒真」那一类）。改为**只在终态表块内**替换（`_terminal_block`
  + 块内未命中即断言失败）后，按压才真正落在判据上。
- **定向面**：`tests/tooling` **1169 passed**；`ruff check` = `All checks passed!`；
  `ruff format --check` = 已格式化；规模门禁 `test_python_source_limits.py` = **1029 passed**。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-26 | IN_PROGRESS | 派生自 GOAL-20260926-018（cycle 1）：EC-01 / EC-02 / EC-03 合并为一个可独立验收的主题面。 |
| 2026-09-26 | VERIFYING | WP1…WP4 落地：`yaml` 2.8.4 + lockfile 单包变化；`undici` 调研文档 + 简报 D-03；13 项终态表 + 13 条 GOAL 声明 + 判据扩展；web 六门 + 根 check + m0 23/23 + 定向套件全绿。 |
| 2026-09-26 | DONE | 独立复检 `RECHECK-20260926-187` = `PASS_WITH_WARNINGS`（W-1/W-2 见该记录）；child_plans 已投影 `ALL_PLAN`；GOAL-018 的 CI 证据在 GOAL 台账登账。 |

## 影响报告

- **改动面**：`apps/web/package.json`、`pnpm-lock.yaml`（依赖 pin）；
  `docs/roadmap/UNDICI_TRANSITIVE_DEPENDENCY_RESEARCH.md`（新增文档）；
  `docs/roadmap/OPEN_DECISIONS_BRIEFING.md`（终态表 + 对齐表 + 三处拍板结果）；
  `tests/tooling/test_pending_decisions_briefing.py`（判据扩展）；
  `.cursor/plans/goals/GOAL-20260926-018-*.md`（人工面声明）；本 PLAN 与其复检。
- **Domain / API / schema**：**零变化**（无 DTO、无路由、无迁移、无 OpenAPI 快照变化）。
- **安全 / 凭据**：**零变化**；`undici` **一字未升**；无新增依赖、无新策略面 allow、
  无鉴权 / 中间件 / 路由保护改动。
- **判据强度**：**只增不减**——引用收集与状态解耦（结案项不再被判成孤儿）
  **同时**新增「终态词汇表 + 简报↔GOAL 逐条同词 + 对齐表状态词汇表」三项断言，
  并补齐 9 条按压；既有 4 条按压与全部六要素/孤儿/对齐规则**原样保留**。
- **上游版本影响**：`yaml` `2.8.1 → 2.8.4`（同 minor 的 patch，`engines` 不变）；
  `undici` 维持 `5.29.0`（8 条告警**登记**，不修）。
- **兼容性 / 迁移风险**：`yaml` 只被 web 构建链消费（vite 配置解析），
  patch 内无 API 变化；设计基线**逐字节未改**即为其无行为漂移的证据。
- **下一项任务**：GOAL-018 cycle 2 = **EC-04 收口复检**（两树复检脚本 + m0 终态行 +
  CI 台账 + 承继残余登记）。
