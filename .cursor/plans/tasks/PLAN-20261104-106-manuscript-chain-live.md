---
id: PLAN-20261104-106
slug: manuscript-chain-live
title: GOAL-106 子计划 —— 十一相链首次真实成立
status: IN_PROGRESS
created_at: 2026-11-04
updated_at: 2026-11-05
parent_goal: GOAL-20261104-106
owners:
  - root-agent
subagent_parallel_limit: 2
latest_recheck: .cursor/plans/rechecks/RECHECK-20261104-106-manuscript-chain-live.md
memory_entries: []
---

# PLAN-20261104-106

## 背景与靶子

GOAL-20261104-106 的七个 EC。本轮**不是**「再造一层机制」，而是让**已经交付的四轮机制
真的跑一次**：GOAL-099（IMRaD 手稿）/ 100（编辑四值决定 + 逐条应答）/ 101（叙述质量口径）/
102（投稿包五件 + 改稿闭环）/ 105（引用结构读数 + 判词驱动改稿）全部落在
`direction_to_manuscript_v1.yaml` 这条链上，而它**真实 run 合计 0 次**。

按**提交面**分三个 cycle：

1. **cycle 1（探针 + 判据）**：先做一次**不改任何代码**的探针真跑，把卡点读数落盘；
   然后建 live 判据（EC-01）并用 mock 链自检它的取数函数（判据本身不能是假红来源）。
2. **cycle 2（按探针修 + 跑到绿）**：按探针读数逐条归类、修产品缺陷 / 合约措辞 / 配置，
   直到真实 run 收敛 `SUCCEEDED`（EC-02）；同轮取证 GOAL-105 两件机制（EC-03）。
3. **cycle 3（收口）**：失败形态台账（EC-04）+ 文档同步（EC-05）+ 收口资产（EC-06）+
   宪章记账与归档（EC-07）。

## 交付面（checkbox）

- [ ] WP-A 探针真跑（不改代码），读数落 `scratch/goal106-probe-*.json`
- [x] WP-B `tests/e2e/test_the_manuscript_chain_runs_live.py`（EC-01）
- [x] WP-C 判据取数自检（mock 链上跑判据函数，确认不是假红来源）
- [ ] WP-D 按探针读数修阻塞项，跑到一次真实 `SUCCEEDED`（EC-02）
- [ ] WP-E EC-03 取证：脚注读数可解析且与正文重算相等；应答实词重叠
- [ ] WP-F `## 真实 run 的失败形态台账`（EC-04）
- [ ] WP-G `docs/architecture/MANUSCRIPT_QUALITY.md` 补首次真实成立那句（EC-05）
- [ ] WP-H `verify_goal106_closeout.py` + `goal106_closeout_assertions.py` + `_VERIFIERS` 登记（EC-06）
- [ ] WP-I 宪章记账 + 归档最旧行（EC-07）

## 复检

收口复检：`tools/verify_goal106_closeout.py --root . --verdict-only`（两树入口跑
`--script-mode shared`，`verify_paths` ≥ 2 路，见 GOAL 的 `latest_recheck`）。

## 影响报告

（收口时填实测读数。）
