---
id: PLAN-20261111-109
slug: paired-ablation
title: GOAL-109 子计划 —— 配对消融让「内容采纳」成为可判形态（试点计划域 k=3）
status: DONE
created_at: 2026-11-12
updated_at: 2026-11-12
parent_goal: GOAL-20261111-109
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261112-109-paired-ablation.md
memory_entries: []
---

# PLAN-20261111-109

## 背景与靶子

序 77：四格里检索 / 计划 / 复检 / 迭代卡在「内容采纳不可机械判」。GOAL-082 的阻塞论证
只针对**子串判据**（组内论证），不针对因果；配对消融（组间对比）消解这个混淆。
试点**计划域**：只改「计划」一格的 `下一级`。

## 交付面（checkbox）

- [x] `comparison_digest.py`（剔除 run_id / frozen_at / project_id 的 run 级可比键）
- [x] `ablation.py`（`AblationPair`，只差一个 slot 的两臂 + 机械证明）
- [x] `output_readings.py`（计划信封的可数读数；两种「空」分得开）
- [x] `tools/ablation_report.py`（k×2 读数表 + 位移统计 + `MIN_CORPUS=3` 拒绝门）
- [x] 四条判据（正例 / 两个反证 / 措辞边界）各有两向按压
- [x] 阶梯「计划」行 `下一级` 改写；其余三格逐字不动
- [x] 收口资产 + 宪章记账

## 复检

`.cursor/plans/rechecks/RECHECK-20261112-109-paired-ablation.md`

## 验收条件

- 七条 EC 全部 PASS；
- 每条新增判据有反证臂且按压后确认判红；
- 全量 m0 终态行 `PASS: profile=m0; 23 deterministic checks`。

## 实施清单

- [x] EC-01 可比键
- [x] EC-02 两臂
- [x] EC-03 读数
- [x] EC-04 报告与拒绝门
- [x] EC-05 措辞边界
- [x] EC-06 阶梯改写
- [x] EC-07 收口资产

## 证据

四件交付的判据读数（2026-11-12 实跑）：
`test_comparison_digest.py` **16 passed**（含逐字段参数化反证 12 臂 + semantic_digest 不能配对的反向钉）；
`test_ablation_pair.py` **8 passed**（六段各消融 + 别段漂移判假 + 五处构造期拒绝）；
`test_output_readings.py` **9 passed**（两种空分开 + 分母计数 + 三态臂解析）；
`test_ablation_report_gate.py` **11 passed**（k=2 拒绝点名 / k=3 位移表 / CLI 退码 / 常量同值）；
`test_ablation_report_wording.py` **7 passed**（闭集非空 / 出口守卫 / 源码洁净）；
`test_goal109_ladder_pilot_scope.py` **4 passed**（计划行新 bar / 三格未推广）。
收口验证器 **65 PASS / 0 FAIL**。

## 影响报告

**Domain / API / schema 变化**：**零**。四个新件全部落在 `packages/application/run_orchestration/`
（纯函数）与 `tools/`（汇总入口）；没有新增或修改 Domain 实体、HTTP 路由、schema 或
`RunManifest` 字段。`RunManifest` 只被**读**（投影 digest），冻结面逐字未动。

**判据口径**：阶梯「计划」行的 `下一级` 由旧 bar（「计划改变下一轮问题…仍无判据」）
**替换**为消融 bar——旧 bar 的判据（若有）不受影响（它判的是别的东西）；
检索 / 复检 / 迭代三格逐字未动（`test_goal109_ladder_pilot_scope.py` 钉住）。

**兼容性 / 迁移风险**：零运行时风险——四件交付没有被任何产品路径调用
（它们是**实验机制**，调用方是跑消融实验的一方）；`MIN_CORPUS` 在 `tools/` 自持一份、
与产品侧常量由判据钉同值。

## 工程记忆

无可复用事实——本轮的全部机制性事实都**内化为代码与判据**：可比键的剔除面与
「semantic_digest 不能当配对键」由 `comparison_digest.py` 的 docstring +
`test_comparison_digest.py` 钉住；两臂的「slots 必须是已渲染 str」（视图 dict 会被
`_section_of` 静默丢段）由 `ablation.py` 模块 docstring + `test_ablation_pair.py`
第一版的假红钉住；「两种空分得开」「引用计数有分母」由 `output_readings.py` +
`test_output_readings.py` 钉住；`MIN_CORPUS=3` 与措辞闭集由 `ablation_report.py` +
两个 tooling 判据钉住。tip 债终结手法已记 `MEM-20261112-241`（GOAL-108 轮），
本轮无新增跨会话事实。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-12 | IN_PROGRESS | 建档 |
| 2026-11-12 | DONE | 七条 EC 全 PASS；四件交付 + 六个判据文件 + 收口资产到位 |
