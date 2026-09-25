---
id: PLAN-20260925-172
slug: upgrade-high-dependency-vite
title: D-03(b) 依赖 pin：4 条 high 升到已修复版本（vite 6.3.5 → 6.4.3）+ 全量 web 门
status: DONE
created_at: 2026-09-25
updated_at: 2026-09-25
parent_goal: GOAL-20260925-016
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260925-016 的 **2026-09-25 用户拍板（goal 模式）第 (3) 条**：
    **D-03 → 取 (b)** —— 依赖 pin **分批升级**、**high 先升**、minor/patch 合批、
    **每批单独 cycle 验证**。范围 = **4 条 high 先升**（若都在 patch/minor 范围内）。
    **这是本轮唯一动产品依赖的项**。若某条 high 的修复版本落在**主版本跳跃**（breaking）⇒
    **不做该条**、如实登记为下一轮输入（**不改判据、不降级其余项**）。升级必须：改
    `pnpm-lock.yaml` + 相应 `package.json` 后跑**全量 web 门**（lint / typecheck / unit /
    build / stub e2e / live e2e）+ m0；设计基线若漂移 ⇒ 按既有流程**强制重生成 + 目检**
    （**不得**调容差）。**授权边界**：只允许「high 且在 patch/minor 内」的 pin 变更；
    `undici`（`5.29.0 → 6.24.0+`，**主版本跳跃**）与 `yaml`（patch 但**非 high**）**不在本轮**；
    任何越界 pin 变更 = **BLOCKED**。**本 PLAN 的其它边界**：零产品代码改动（除依赖声明）、
    零策略面改动、零门禁改动、零判据改动；不在 `pnpm install --frozen-lockfile`
    之外手工装包。push-to-main-for-CI（只推 main、不 force、不重写历史、不推旁支）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260925-173-upgrade-high-dependency-vite.md
memory_entries:
  - .cursor/memory/entries/MEM-20260925-136-pin-bump-needs-a-resolved-version-and-a-full-gate.md
---

# PLAN-20260925-172 — D-03(b) high 依赖升级（GOAL-016 / EC-03）

## 目标

把 D-03(b) 从「明文禁令」变成**已执行的 high 升级 + 全量门证据**：4 条 Dependabot **high**
告警全部落在 `vite` 上，`first_patched_version` = `6.4.2` / `6.4.3`；
as-is 解析版本 `vite@6.3.5` ⇒ 修复版本在 **6.x 内的 minor** ⇒ **属于授权范围**。

**只升 `vite`**：`undici`（`5.29.0 → 6.24.0+`）= **主版本跳跃 ⇒ 不做**（且无 high）；
`yaml`（`2.8.1 → 2.8.3` = patch，但**非 high**）排下一批。

## 验收条件

- **AC-1｜解析版本变化（逐包 before → after）**：`pnpm-lock.yaml` 里 `vite` 的解析版本
  由 `6.3.5` 变为 `6.4.3`，且**它是唯一变化的解析版本**（`diff` 只含 `vite` 及其
  peer 引用行）；`apps/web/package.json` 的声明面同步为 `6.4.3`。
- **AC-2｜全量 web 门**：根 `pnpm run check`（`format:check` / `lint` / `typecheck` /
  `boundaries` / `test`）与 `apps/web` 的 `lint` / `typecheck` / `test` / `build`
  全部通过；**stub e2e** 与 **live e2e** 全部通过。
- **AC-3｜设计基线不漂移**：结构签名门（`design-outline-guard.spec.ts`）在 stub e2e 内通过
  ⇒ **无需重生成基线**（若漂移则按既有流程强制重生成 + 目检，**不得**调容差）。
- **AC-4｜m0 全绿**：`make validate-all` 的终态行（**标明树与跑法**）。
- **AC-5｜`R-2` 复查**：依赖升级后默认门**仍不得**看到凭据
  （`tests/architecture/python/test_default_gate_credential_isolation.py` 及其探针仍通过、
  `egress guard` 判词 `blocked 0`）。
- **AC-6｜越界项如实登记**：`undici`（主版本跳跃）与 `yaml`（非 high）**不做**，
  逐条写明理由，作为下一轮输入（**不改判据、不降级其余项**）。

## 实施清单

- [x] WP1：`apps/web/package.json` 的 `vite` 声明 `6.3.5 → 6.4.3`。
- [x] WP2：`pnpm install --lockfile-only` 更新 `pnpm-lock.yaml`（只改 `vite` 解析版本与
  peer 引用）；`pnpm install --frozen-lockfile` 按锁装包（**未**手工装包）。
- [x] WP3：全量 web 门（根 `check` + web `lint`/`typecheck`/`test`/`build` + stub e2e +
  live e2e）。
- [x] WP4：设计基线核对（结构签名门在 stub e2e 内通过 ⇒ 零漂移）。
- [x] WP5：`R-2` 复查 + m0 + 记录（本 PLAN + RECHECK + MEM）与 GOAL-016 回写。

## 证据（本地）

- **解析版本对照**：`pnpm-lock.yaml` 由 `vite@6.3.5`（`sha512-cZn6NDFE…`）变为
  `vite@6.4.3`（`sha512-NTKlcQjl…`）；`@vitejs/plugin-react` 的 peer 引用行随之更新；
  实际安装版本 `node -e "require('./apps/web/node_modules/vite/package.json').version"`
  ⇒ **`6.4.3`**。
- **告警面（升级前留档）**：`scratch/goal016-c3-alerts-before.txt` —— open **23**
  （4 high / 13 medium / 6 low）；4 条 high **全部是 `vite`**
  （`#5`/`#7` 在 `apps/web/package.json`，`#18`/`#20` 在 `pnpm-lock.yaml`；
  `first_patched_version` = `6.4.2` / `6.4.3`）⇒ **6.4.3 同时覆盖两条修复版本**。
- **全量 web 门**（逐条留档在 `scratch/goal016-c3-*`）：
  - 根 `pnpm run check` ⇒ **exit 0**；
  - `apps/web`：`lint` / `typecheck` / `test` / `build` ⇒ **四项全 PASS**；
  - **stub e2e** `test:e2e` ⇒ **`98 passed`**（含结构签名门 ⇒ **设计基线零漂移**）；
  - **live e2e** `test:e2e:live` ⇒ **`53 passed`**。
- **`R-2` 复查**：`pytest tests/architecture/python/test_default_gate_credential_isolation.py
  tests/architecture/python/test_default_gate_isolation_probe.py -q` ⇒ **`3 passed`**；
  `egress guard: judged 0 connection attempt(s); blocked 0`；
  全程无 `egress guard: FAIL` 行。
- **m0**：见 GOAL-016 的 CI 台账与 RECHECK-173（两个终态行分开写清）。

## 残余（本 PLAN 不处置）

- **`undici`**（`5.29.0 → 6.24.0+`）：**主版本跳跃**（breaking）⇒ D-03(b) 明文**不做**，
  如实登记为下一轮输入。它涉及 8 条告警（低 / 中），**无 high**。
- **`yaml`**（`2.8.1 → 2.8.3`）：patch 且**可安全升级**，但**非 high** ⇒ 按「high 先升」
  排**下一批**。
- **剩余 19 条**（13 medium + 6 low）**原样保留**（`R-D1` 的未清部分）。
- **设计基线**：本轮**零漂移**（结构签名门通过）；未重生成任何基线，**未**调容差。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | IN_PROGRESS | derive：从 GOAL-016 的 EC-03 圈定主题（4 条 high 全是 `vite`、修复版本在 6.x minor），本文件 + `ALL_PLAN` 投影 + `parent_goal` 同提交。 |
| 2026-09-25 | IN_PROGRESS | WP1–WP2：声明面 + 锁面升级（`6.3.5 → 6.4.3`），`--frozen-lockfile` 按锁装包。 |
| 2026-09-25 | IN_PROGRESS | WP3–WP4：全量 web 门全绿（根 `check` exit 0；web 四项 PASS；stub e2e `98 passed`；live e2e `53 passed`）；设计基线**零漂移**。 |
| 2026-09-25 | DONE | WP5：`R-2` 复查通过；m0 与记录回写完成；复检 `RECHECK-20260925-173` 见 `latest_recheck`。 |

## 影响报告

- **改动**：`apps/web/package.json`（`vite` 声明）+ `pnpm-lock.yaml`（解析版本）；
  新增记录文件。**无产品代码改动**。
- **lint / typecheck / test**：根 `pnpm run check` = **exit 0**；web `lint` / `typecheck` /
  `test` / `build` 全 PASS；stub e2e `98 passed`；live e2e `53 passed`。
- **Domain / API / schema 变化**：无。
- **安全 / 凭据变化**：**供应链告警面收敛**——4 条 high（全为 `vite`）升到已修复版本；
  `R-2` 复查证明默认门**仍不得**看到凭据。未引入任何新依赖（只是版本上移）。
- **兼容性 / 迁移风险**：`vite` 在 **6.x 内**的 minor 上移（非主版本跳跃）；
  全量 web 门与 m0 作为回归证据；**设计基线零漂移**。
- **上游版本影响**：`vite` `6.3.5 → 6.4.3`（`sha512` 变化已留档）；
  `@vitejs/plugin-react` 的 peer 解析随之更新（`5.1.0` 本身未变）。
- **下一项任务**：GOAL-016 的 **EC-04（D-07 + D-08 + D-09 三处文档固化）**。
