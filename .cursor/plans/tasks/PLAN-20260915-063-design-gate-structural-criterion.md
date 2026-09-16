---
id: PLAN-20260915-063
slug: design-gate-structural-criterion
title: 设计门禁结构判据：整块新增内容必须判红（DOM 结构签名）
status: DONE
created_at: 2026-09-16
updated_at: 2026-09-16
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 1 = EC-01（设计门禁结构判据）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」，以及 GOAL-20260915-002 收口结论表第 ① 项（设计门禁容差盲区）；push-to-main-for-CI 授权沿用 GOAL-001 批准口径。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-063-design-gate-structural-criterion.md
memory_entries:
  - MEM-20260915-038-structural-signature-complements-pixel-gate
---

# PLAN-20260915-063 — 设计门禁结构判据（GOAL-003 cycle 1 / EC-01）

## 目标

把"整块新增内容不会被设计门禁报警"这个盲区**变成红灯**，而不是继续靠流程纪律兜底。

现状（四次实测，全部低于 `maxDiffPixelRatio: 0.02` ⇒ 门禁静默）：

| cycle | 页面改动 | 旧基线差异 |
| --- | --- | --- |
| 2 | 节点表 4 列改整宽堆叠 | 1.73% |
| 5 | ops 写面板整块新增 | 1.02% / 0.93% |
| 6 | 注册治理面板整块新增 | 0.79% / 0.66% |
| 7 | 项目列表多一行 + 逐行删除动作 | 0.48% / 0.47% |

像素比率衡量的是"变了多少面积"，因此**与改动的重要性无关**：一页内容越满，
新增一块面板的占比越小。本计划补一个**结构判据**：把页面 DOM 归一化成"结构签名"，
节点增删立即改变签名——与面积无关。

## 口径（诚实边界，先写清楚再写代码）

1. **互补而非替代**：像素判据管"面积/样式/布局"，结构判据管"节点增删"。
   两者都不覆盖的：像素判据看不到视口外与低占比变化，结构判据看不到样式变化
   （只改颜色不改节点 → 结构签名不变，本计划用对照用例把这一点固定下来）。
2. **签名只取跨平台稳定的身份**：标签 / `data-testid` / `role` / `aria-label` /
   叶子文本 / 子节点数。**不取** CSS-module 哈希类名（随构建漂移）、不取样式、不取坐标。
3. **易变字面量先归一化**：ISO 时间戳、时钟时刻、UUID、长数字串 → `<ts>` / `<clock>` /
   `<uuid>` / `<n>`，避免"每次跑都不同"的假漂移。
4. **单一基线文件**（不是 per-platform 快照）：结构签名与平台无关，一份 JSON 同时服务
   win32 与 ubuntu CI——但"无关"必须**证明**，不能假设（见下 WP-B）。
5. **更新是显式意图**：`UPDATE_OUTLINES=1` 才改写基线（CI 不设该变量），
   与 `--update-snapshots` 同性质。

## 背景（决定实现形状的既有事实）

- 设计门禁跑在 stub 替身上（`stubApi`），页面内容确定 ⇒ 结构签名可做精确比对。
- CI 的 `console-frontend` job 在 ubuntu 上跑 `pnpm --dir apps/web test:e2e`
  ⇒ 新判据必须在 Linux 上同样成立（本机是 win32）。
- 该 job 不装额外依赖，且 GOAL 的 escalation_triggers 把"新依赖"列为需人工决策
  ⇒ 实现不能引入 PNG 解码/图像库，只能走 DOM（浏览器侧 `evaluate` 返回字符串）。

## 范围

- 新增：`apps/web/tests/e2e/design-outline.ts`（签名构建 + 基线读写 + 比对）、
  `apps/web/tests/e2e/design-outline-guard.spec.ts`（反证与对照）、
  `apps/web/tests/e2e/design-outlines.json`（33 路由基线）。
- 修改：`apps/web/tests/e2e/design-fidelity.spec.ts`（新增第二条主判据用例）。
- 脚本（scratch，gitignored）：`scratch/verify_linux_outlines.sh`（+ `_inner.sh`）、
  `scratch/outline-vs-pixel/measure.py`。
- 记录：本计划、RECHECK-063、MEM-038、GOAL-003 记账。

## 验收条件

- [x] AC-01：33 条路由结构签名入库（`design-outlines.json`，33 键），
  `design-fidelity` 的"33 路由结构签名"用例在**未设置** `UPDATE_OUTLINES` 时通过
  （即基线与当前渲染一致），且连跑两次结果相同（确定性）。
- [x] AC-02：反证——注入可见面板 / 注入视口外节点 / 列表多一行 / 删除一个节点行
  → `assertOutlines()` 抛"结构签名漂移"（4 条用例）。
- [x] AC-03：对照——只改颜色（不改节点）→ 签名不变、`assertOutlines()` 不抛
  （判据不退化成噪音）。
- [x] AC-04：归一化——时间戳/UUID/长数字/空白 4 条断言。
- [x] AC-05：**跨平台一致性证据**——在 pinned `mcr.microsoft.com/playwright:v1.56.1-noble`
  容器里重算 33 条签名，与 win32 结果**逐字节一致**（`drifted=[]`）。
- [x] AC-06：**对照实验**量化"同一改动两个判据"：多一行 = 0.079%、视口外面板 = 0.000%
  ⇒ 像素判据不报警而结构判据判红；可见面板 = 2.618% ⇒ 两者都报警。
- [x] AC-07：全量 stub e2e **66 passed**（含新用例 7 条）、live e2e **31 passed**、
  web 单测 **76 passed**、根 eslint 0 error、`tsc --noEmit` 通过。
- [x] AC-08：本地 m0 = `profile=m0; 23 deterministic checks`。
- [x] AC-09：GOAL-003 的 SOP 写入结构签名基线更新命令，避免后继 cycle 卡在"忘了重生成"。

## 实施清单

- [x] WP-A 结构签名构建器（归一化 + 扁平前序节点表）与单一 JSON 基线读写
- [x] WP-B 33 路由签名生成 + 跨平台一致性验证（linux 容器重算逐字节比对）
- [x] WP-C 反证/对照用例（6 条）+ 像素对照实验脚本
- [x] WP-D 全量套件与门禁（stub/live/unit/eslint/tsc/m0）+ 记录与 CI

## 证据

| WP | 证据 | 结果 |
| --- | --- | --- |
| WP-A | `apps/web/tests/e2e/design-outlines.json` = 33 键；`normalizeText` 4 条断言（`<n>` / `<ts>` / `<uuid>` / 空白归一） | PASS |
| WP-B | 容器重算 vs win32：`host routes=33 linux routes=33 / only-in-host=[] / only-in-linux=[] / drifted=[]` ⇒ `PASS: 33 条结构签名跨平台一致` | PASS |
| WP-C | `npx playwright test design-outline-guard` → **6 passed**（可见面板/视口外/多一行/删节点 → 判红；只改样式 → 不误报；归一化） | PASS |
| WP-C | `python scratch/outline-vs-pixel/measure.py` → 多一行 **0.079%**、视口外 **0.000%**（像素判据不报警）；可见面板 **2.618%**（会报警）——同一改动结构判据全部判红 | PASS |
| WP-D | `npx playwright test`（stub）= **66 passed**；`--config playwrightLive.config.ts` = **31 passed**；`pnpm test` = **76 passed**；eslint 0 error；`tsc --noEmit` 通过；m0 = `profile=m0; 23 deterministic checks` | PASS |

## 已知风险

- **结构判据的盲区**：只改文案（不增删节点）或只改样式不会变签名——这类变化仍由像素
  判据负责；两者叠加后仍有一个窄缝：**页面中部的小面积文案改动**（既不增删节点、
  像素占比又 < 2%）。要覆盖它需要"文本指纹"判据（把可见文本整段入基线），
  本轮**刻意不做**：那会让门禁对文案微调过敏，且与"修订文案"的日常操作冲突。
- **文本截断**：签名里的文本截断到 120 字符 ⇒ 长文案后半段变化不看。这是为了控制基线
  体积（否则一个 pageSupport 说明就可能上千字符）与 diff 可读性。
- **基线体积**：33 条签名 ≈ 156 KB（可读文本、非二进制）。每次页面结构变化的 diff
  可能很长——这是**有意的**：门禁的价值就在于让人看见"多了什么"。
- **更新流程依赖记忆**：忘记 `UPDATE_OUTLINES=1` 时用例会红（这是正确的失败），
  提示信息里写了更新命令。
- **CI 不校验基线是否被人工审阅**：与像素基线同性质——判据只保证"变了就会红"，
  "变化是否可接受"仍由人决定（`--update-snapshots` 的基线也一样）。

## 状态历史

- 2026-09-16 创建（IN_PROGRESS）：GOAL-20260915-003 cycle 1，取 EC-01。
- 2026-09-16 WP-A/WP-B 完成：签名构建器 + 33 条基线；首版用 Playwright
  `toMatchSnapshot` 生成的是 `-win32.txt`（CI 在 ubuntu 上会缺文件）⇒ 改为单一 JSON 基线；
  ISO 正则修正后基线重生成；容器重算与 win32 逐字节一致。
- 2026-09-16 WP-C/WP-D 完成：反证/对照 6 用例 + 像素对照实验（0.079% / 0.000% / 2.618%）；
  全量套件与 m0 绿；RECHECK-063 = PASS_WITH_WARNINGS。

## 影响报告

- 改动：新增 `apps/web/tests/e2e/{design-outline.ts,design-outline-guard.spec.ts,design-outlines.json}`、
  `scratch/{verify_linux_outlines.sh,verify_linux_outlines_inner.sh,outline-vs-pixel/measure.py}`；
  修改 `apps/web/tests/e2e/design-fidelity.spec.ts`（第二判据用例）；
  新增记录 `.cursor/plans/goals/GOAL-20260915-003-*.md`、本计划、`RECHECK-063`、`MEM-038`。
- lint/typecheck/test：stub e2e **66 passed**、live e2e **31 passed**、web 单测 **76 passed**、
  eslint 0 error、`tsc --noEmit` 通过、m0 = `profile=m0; 23 deterministic checks`。
- Domain/API/schema 变化：**无**（只动测试与记录面；产品代码、API、DTO、schema 未改）。
- 安全/凭据变化：无（无新依赖、无新凭据面）。新增的容器脚本只读工作树副本。
- 兼容性/迁移风险：无。新增门禁会使**未来的页面结构改动**需要同步重生成结构签名基线
  （流程变化，非代码兼容性问题）；历史基线不受影响。
- 上游版本影响：无（未引入任何新依赖；这正是放弃"PNG 解码 + 局部区块比对"方案的原因）。
- 下一项任务：GOAL-003 cycle 2 = EC-02（ToolPack install/approve 供应链面），
  子 PLAN 编号 = PLAN-20260915-064。
