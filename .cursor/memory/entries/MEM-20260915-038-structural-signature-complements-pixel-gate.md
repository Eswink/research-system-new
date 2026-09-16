---
id: MEM-20260915-038
title: 结构签名（DOM outline）补像素门禁的盲区：整块新增不再静默
status: ACTIVE
created_at: 2026-09-16
updated_at: 2026-09-16
scope: repository
confidence: 0.92
review_after: 2027-09-16
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-063-design-gate-structural-criterion.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-063-design-gate-structural-criterion.md
supersedes: []
tags:
  - design-gate
  - pixel-diff-blind-spot
  - dom-outline
  - cross-platform-baseline
  - e2e
---

# 结构签名：让"整块新增"从静默变红灯

## 做了什么

`apps/web/tests/e2e/design-outline.ts` 把 33 条路由的页面 DOM 归一化成**结构签名**
（扁平前序节点表：标签 / `data-testid` / `role` / `aria-label` / 叶子文本 / 子节点数），
存在**单一** `design-outlines.json`；`design-fidelity.spec.ts` 第二条用例逐路由比对，
节点增删立即判红。更新基线的唯一方式是显式 `UPDATE_OUTLINES=1`（CI 不设）。

## 为什么这样做

像素判据（`maxDiffPixelRatio: 0.02`）衡量的是"变了多少面积"，与改动重要性无关：
四次实测整块新增内容全部低于阈值 ⇒ 门禁静默。

| cycle | 改动 | 旧判据差异 | 结构判据 |
| --- | --- | --- | --- |
| 2 | 节点表 4 列改整宽堆叠 | 1.73% | — |
| 5 | ops 写面板整块新增 | 1.02% / 0.93% | — |
| 6 | 注册治理面板整块新增 | 0.79% / 0.66% | — |
| 7 | 项目列表多一行 + 删除动作 | 0.48% / 0.47% | — |
| 本 cycle | 列表多一行 | **0.079%** | **判红** |
| 本 cycle | 视口外新增面板 | **0.000%** | **判红** |
| 本 cycle | 可见区新增面板 | 2.618%（会报警） | 判红 |

对照实验脚本：`scratch/outline-vs-pixel/measure.py`（YIQ 像素差，与门禁同口径）。

## 怎么做与复现

```ts
// 构建：浏览器侧采集 → 归一化 → 拼成一行
await buildOutline(page);            // "main testid=... kids=7 | <ts> 概览"
// 判定：增删 → 抛错；样式变化 → 不动
assertOutlines(observed);            // UPDATE_OUTLINES=1 时写回基线（人工审阅后）
```

```bash
cd apps/web && pnpm exec playwright test design-fidelity          # 33 路由像素 + 结构
cd apps/web && pnpm exec playwright test design-outline-guard     # 6 条反证/对照
UPDATE_OUTLINES=1 pnpm exec playwright test design-fidelity       # 结构变化后重生成
sh scratch/verify_linux_outlines.sh                               # 容器内重算，跨平台一致性
```

## 适用边界（踩过的坑）

- **跨平台必须证明，不能假设**：首版用 `toMatchSnapshot` 生成的是 `-win32.txt`，
  ubuntu CI 会直接缺文件。改成单一 JSON 基线后，在 pinned
  `mcr.microsoft.com/playwright:v1.56.1-noble` 容器里重算 33 条，与 win32
  **逐字节一致**（`drifted=[]`）才敢让 CI 用它。
- **易变字面量必须先归一化**，否则每次跑都是假漂移：ISO 时间戳（含 `+00:00` 残留，
  首版正则有漏）、时钟时刻、UUID、长数字 → `<ts>` / `<clock>` / `<uuid>` / `<n>`。
  归一化函数自身有 4 条断言（`design-outline-guard.spec.ts`）。
- **不取 CSS-module 哈希类名**：构建漂移会让签名每次不同；也不取样式/坐标。
- **签名盲区（刻意保留）**：只改文案（不增删节点）或只改样式 → 签名不变；
  页面中部的小面积文案改动两个判据都看不到。本轮**不做**文本指纹：
  会让门禁对日常改文案过敏。判断标准是"门禁的噪音成本 < 漏报成本"。
- **注入位置决定测量有效性**：注入 `document.body` 末尾的节点可能在视口外
  ⇒ 像素差 0.000%；要对比"像素判据是否会报警"必须注入到可见区（`main` 内）。
  这也是结构判据相对像素判据的优势：**与可见性无关**。
- **`test-results/` 每次运行被清空** ⇒ 对照截图必须整份 spec 跑完再测量。
- apps/web 是 `"type": "module"` ⇒ 用 `import.meta.dirname`，没有 `__dirname`。

## 来源

- PLAN-20260915-063 / RECHECK-20260915-063（GOAL-20260915-003 cycle 1 / EC-01）。
- 上游事实：GOAL-20260915-002 收口结论表 ①「设计门禁容差盲区」。
- 相关：[[MEM-20260915-035]]（写面必须被读面消费——同属"判据真的会红吗"这一族）。
