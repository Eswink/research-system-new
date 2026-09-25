---
id: MEM-20260925-136
title: "升 pin 的判据是「解析版本对照 + 全量门 + 容差不动」；主版本跳跃与重生成基线都不许混进来"
status: ACTIVE
created_at: 2026-09-25
updated_at: 2026-09-25
scope: repository
confidence: 0.9
review_after: 2027-03-25
source_plans:
  - .cursor/plans/tasks/PLAN-20260925-172-upgrade-high-dependency-vite.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260925-173-upgrade-high-dependency-vite.md
supersedes: []
tags: [dependencies, dependabot, vite, supply-chain, goal-016, d-03]
---

## 做了什么

GOAL-016 的 **EC-03（D-03(b)）**执行了本轮唯一动产品依赖的改动：4 条 Dependabot **high**
告警全部落在 `vite` 上（`first_patched_version` = `6.4.2` / `6.4.3`），as-is `vite@6.3.5`
⇒ 一次上移到 **`6.4.3`**（**6.x 内的 minor**）同时覆盖全部 4 条。

落地确认的可复用要点：

1. **授权范围要按「修复版本 vs 当前版本」判，不按「包名 / 告警条数」判**：
   4 条 high 全在 `vite`（minor 可达 ⇒ **做**）；`undici` 是 `5.29.0 → 6.24.0+`
   （**主版本跳跃** ⇒ **不做**，哪怕它告警最多、有 8 条）；`yaml` 是 patch（**可做但非 high**
   ⇒ 排下一批）。**「high 先升」是范围，不是优先级提示。**
2. **锁面证据要逐行看 `git diff`**：`pnpm-lock.yaml` 的 diff 只有 **9 增 9 删**，
   全落在 `vite@6.3.5 → 6.4.3` 与 `@vitejs/plugin-react` 的 **peer 引用行**
   （插件自己版本没变）⇒ 「只改了被授权的那个包」是**可核对的**，不是靠 `pnpm` 的提示语。
3. **装包只用 `--frozen-lockfile`**：先 `pnpm install --lockfile-only` 改锁面，
   再 `pnpm install --frozen-lockfile` 按锁装；**不** `pnpm add`、**不**手工装包。
4. **设计基线要么零漂移、要么重生成 + 目检，绝不动容差**：本轮结构签名门
   （`design-outline-guard.spec.ts` 比对 `design-outlines.json`）在 stub e2e 内**通过**
   ⇒ **零漂移**、无需重生成。这是「依赖上移会不会改渲染」的**机械答案**。
5. **升级后必须复查凭据隔离**：默认门**仍不得**看到凭据
   （`R-2` 的判据 + 探针 `3 passed`；全程 `egress guard: judged 0 …; blocked 0`、
   零 `FAIL` 行）——依赖上移**可以**悄悄改变出网面，这一步不能省。

## 为什么这样做

- **主版本跳跃是 breaking 面，不是同一条判据能盖住的**：`5.x → 6.x` 的 undici
  可能在 API / 默认值上断链，而本轮没有针对它的验收面 ⇒ 强行升级等于**把未验证的
  破坏面**带进仓库。**如实登记为下一轮输入**比「顺手升掉」正确。
- **容差是判据强度**：基线漂移时调容差 = 放宽门禁。正确动作是**重生成基线 + 目检**，
  且必须在记录里写清「重生成而非放宽容差」。
- **peer 引用行也在 diff 里**：只看 `specifier` 会漏掉解析链的变化；
  逐行看 diff 才能证明「只有被授权的包变了」。

## 怎么做与复现

- 改声明 → 改锁 → 按锁装：
  `apps/web/package.json` 的 `vite` 改 `6.4.3` →
  `pnpm install --lockfile-only` → `pnpm install --frozen-lockfile` →
  `node -e "require('./apps/web/node_modules/vite/package.json').version"` ⇒ `6.4.3`。
- 逐包对照：`git diff pnpm-lock.yaml`（本仓实测 9 增 9 删，只含 `vite` 与 peer 引用）。
- 全量 web 门：根 `pnpm run check`（exit 0）；`pnpm --dir apps/web run
  {lint,typecheck,test,build}`；`test:e2e`（stub，含结构签名门）；`test:e2e:live`。
- 告警面留档：`scratch/goal014_c4_residual_probe.py`（只读、单一固定主机 `api.github.com`、
  凭据只读入内存不打印）⇒ 升级前 open 23（4 high / 13 medium / 6 low）。
- `R-2` 复查：`pytest tests/architecture/python/test_default_gate_credential_isolation.py
  tests/architecture/python/test_default_gate_isolation_probe.py -q` ⇒ `3 passed`。

## 适用边界

- 判据只覆盖**被授权范围内的包**；`undici` / `yaml` / 剩余 19 条**不在**本轮，
  **不得**把本轮读成「依赖告警已清零」。
- 本机 live e2e 与 m0 依赖**真实网络 + 真实凭据**（`W-7`）⇒ 终态行必须标注跑法，
  **不得**声称「本机全量门纯离线」。
- `vite` 的 high 已清；若后续出现 `vite` 的**新** high 且修复版本跨主版本 ⇒ 同一条纪律：
  **不做**、登记，不降级别项。

## 来源

- `.cursor/plans/tasks/PLAN-20260925-172-upgrade-high-dependency-vite.md`（WP1–WP5）
- `.cursor/plans/rechecks/RECHECK-20260925-173-upgrade-high-dependency-vite.md`
- `.cursor/plans/goals/GOAL-20260925-016-decisions-landed-and-threat-model.md`（EC-03）
- `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` D-03（判词与范围同源）
