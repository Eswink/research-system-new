---
id: MEM-20260926-142
title: "「patch 升级」的落地目标是最新 patch；前置调研的交付标准是可拍板；按压必须落在判据自己的块内"
status: ACTIVE
created_at: 2026-09-26
updated_at: 2026-09-26
scope: repository
confidence: 0.9
review_after: 2027-03-26
source_plans:
  - .cursor/plans/tasks/PLAN-20260926-186-yaml-patch-upgrade-and-undici-research.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260926-187-yaml-patch-upgrade-and-undici-research.md
supersedes: []
tags: [dependency-pin, patch-upgrade, advisory, transitive-dependency, research-deliverable, gate-design, press-test, goal-018, d-03]
---

## 做了什么

三件可独立复用的事：

1. **`yaml` `2.8.1 → 2.8.4`**（`apps/web`）：`git diff` 逐 hunk 证明 lockfile 只有这一个包变化；
   六道 web 门 + 根 `check` + m0（`PASS: profile=m0; 23 deterministic checks`）全绿；
   设计基线 `design-outlines.json` **逐字节未改**（无漂移 ⇒ 未触发重生成）。
2. **`undici@5.29.0`（8 条告警）前置调研**：产出一份**可拍板**结论文档
   （`docs/roadmap/UNDICI_TRANSITIVE_DEPENDENCY_RESEARCH.md`），**零升级动作**
   （反证：lockfile 里 `undici: 5.29.0` 仍**恰好 1 条**入边；无 `overrides` 字段）。
3. **13 项 `D-NN` 结清**：简报新增终态表（四值词汇表）+ GOAL 侧 13 条同词声明 +
   对齐表状态列改封闭词汇表；判据 `tests/tooling/test_pending_decisions_briefing.py`
   **只增不减**地扩到 **14 passed**（1 现状 + 13 按压）。

## 为什么这样做

1. **「patch 可升」写进授权时，落地目标要认「最新 patch」而不是「首个修复版本」。**
   告警 `GHSA-48c2-rrv3-qjmp` 的 `first_patched_version` 是 **`2.8.3`**，而 `2.8.x` 的
   **最新 patch 是 `2.8.4`**（版本表 `2.8.0/1/2/3/4`）。停在 `2.8.3` 会把"最新 patch"
   读成"最低可修版本"，等于**主动少升一版**；两者都在 patch 面内，但只有后者符合授权口径。
2. **传递依赖的"能不能升"只有一个可靠读法：逐版本读上游的 `dependencies`，再核对父包的声明区间。**
   实测 `@connectrpc/connect-node` 33 个版本：**1.x 全线 `undici ^5`**（`0.13.2`…`1.7.0`），
   **2.x 起 `dependencies` 为空**（不再需要 undici，因为 `engines` 提到了 `>=18.14.1`）。
   同时 `undici` 的**全部修复版本都 ≥ `6.23.0`** ⇒ **不存在 5.x 修复** ⇒ 修复必然跨主版本。
   再看父包：`@cursor/sdk` 最新版仍锁 `^1.6.1` ⇒ **升 `@cursor/sdk` 去不掉 undici**。
   ⇒ 结论是「**不可在本仓正确升级**，归属方在上游」，而不是"用 overrides 硬来"。
3. **前置调研的交付标准是"可拍板"，不是"写了很多"。**
   可拍板 = 三问各有**答案 + 可复核依据** + **归属方** + 若要动手的**授权清单与回滚方式**。
   "不可在本仓修复"同样是一个**有效结论**——它把下一步的决策面从"要不要改代码"变成
   "要不要向上游提要求"。
4. **overrides 这类"越界修复"要同时给出反面证据：告警消失 ≠ 风险已评估。**
   强制提升会让 `pnpm audit` / Dependabot **不再提示**该包；若不留一份记录，越界组合会被
   静默掩盖。所以结论文档必须写明"影响面 1 个包 / 1 个 import"这种**可核对的边界**，
   以及 engines 上限（`undici@8` 要 `node >=22.19.0`，本树 `22.18.0` ⇒ 上限 `7.30.0`）。
5. **按压（press）必须落在判据**自己**读的那个块内。** 简报里存在**同形状的两张表**
   （索引表与终态表都以 `| D-05 | …` 开头）⇒ 第一版按压用「按行首删一行」命中了索引表，
   **判据没被触碰**，于是"按下去的绿"看起来像"判据在管"。这是 `MEM-20260925-141` 的
   「判据自身恒真」的一个**新形态**：不是判据被文档引用喂饱，而是**按压打偏了目标**。
   修法：先切出判据自己的块（`_terminal_block`），在块内替换，并**在块内未命中时断言失败**。

## 怎么做与复现

```bash
# 1) 「只升了一个包」的证据（应当只看到 yaml 2.8.1 <-> 2.8.4）
git diff -- apps/web/package.json pnpm-lock.yaml
# 2) 零升级的反证（应当恰好 1 条，且位于 connect-node 的依赖块内）
grep -n "undici: 5.29.0" pnpm-lock.yaml
# 3) 传递依赖的真实归属：逐版本读上游 dependencies
curl -s https://registry.npmjs.org/@connectrpc%2Fconnect-node | python -c "import json,sys; d=json.load(sys.stdin); [print(v, d['versions'][v].get('dependencies')) for v in ('1.7.0','2.0.0','2.2.0')]"
# 4) 唯一用点（Node >= 18 下是死分支）
cat node_modules/.pnpm/@connectrpc+connect-node@1.7.0*/node_modules/@connectrpc/connect-node/dist/esm/node-headers-polyfill.js
# 5) 决案结清判据（含 13 条按压）
python -m pytest tests/tooling/test_pending_decisions_briefing.py -q
# 6) 本地全量门（独占、DSN 固化、仓库 .venv）
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
```

## 适用边界

- **"最新 patch"的判定要现查版本表**，不能只看 `first_patched_version`；
  也不要把它读成"必须升到 latest"（`yaml` 的 `latest` 已经是 `2.9.x`，**跨 minor ⇒ 不在授权内**）。
- **"不可在本仓修复"是有条件的结论**：`undici` 的评估建立在
  **当前 Node（22.18.0）+ 当前调用路径（唯一 importer 是框架技能脚本）** 上；
  Node 降到 < 18、或本仓开始直接调用 undici 客户端 API、或 `connect-node` 改用 undici 做传输
  ⇒ **立即失效**。
- **本文档的 `undici` 结论不构成"安全"声明**：`R-M1`（Mimosa 钩子侧结论未得）仍原样保留，
  hook 面仍是**失败开放**。
- **判据扩展只增不减**：既有四条按压与六要素 / 孤儿 / 对齐规则**原样保留**；
  若将来还要动这张表，先确认"引用收集与状态解耦"这条改动方向**没有**放松任何原有断言。
- 规模门禁：`tests/tooling/test_pending_decisions_briefing.py` 现 **399 行**（450 行上限），
  再扩按压要注意余量。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260926-186-yaml-patch-upgrade-and-undici-research.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260926-187-yaml-patch-upgrade-and-undici-research.md`
- 结论文档：`docs/roadmap/UNDICI_TRANSITIVE_DEPENDENCY_RESEARCH.md`
- 相关记忆：`MEM-20260925-141`（一个开关一个读取点 / 判据自身恒真的两种形态）、
  `MEM-20260925-139`（收口需要两棵树与两条终态行）
