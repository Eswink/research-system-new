---
id: RECHECK-20261112-109
slug: paired-ablation
title: GOAL-109 复检 —— 配对消融让「内容采纳」成为可判形态（试点计划域 k=3）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-11-12
updated_at: 2026-11-12
plan_id: PLAN-20261111-109
parent_goal: GOAL-20261111-109
owners:
  - root-agent
verify_paths:
  - packages/application/run_orchestration/comparison_digest.py
  - packages/application/run_orchestration/ablation.py
  - packages/application/run_orchestration/output_readings.py
  - tools/ablation_report.py
  - tests/application/run_orchestration/test_comparison_digest.py
  - tests/application/run_orchestration/test_ablation_pair.py
  - tests/application/run_orchestration/test_output_readings.py
  - tests/tooling/test_ablation_report_gate.py
  - tests/tooling/test_ablation_report_wording.py
---

# RECHECK-20261112-109

## 复检范围

GOAL-20261111-109 的七条 EC 逐条取证。**两路以上**（`verify_paths` 每项都是独立取证路径）。

本轮的射程边界（写在前面，收口时逐条核对有没有越界）：

| 面 | 本轮**交付**什么 | 本轮**不**宣称什么 |
| --- | --- | --- |
| 可判性 | 「只差一个 slot」的机械证明 + 分布位移读数 | **不判**「模型采纳了 X」（意图归因）；措辞由闭集判据守住 |
| 试点 | 只改「计划」一格的 `下一级` | **不**宣称检索 / 复检 / 迭代三格可判——逐字不动 |
| 采样 | 如实登记全仓无 temperature/seed ⇒ 只比分布 | **不**引入采样控制（改契约面）；**不**宣称逐字可比 |
| live | 判据全部离线可跑 | 本轮**不**宣称已做过一次 live k=3 重复测量（那要 4+ 次真实 run） |

## 检查结果

### EC-01 run 级可比键（PASS）

- `comparison_digest.py`：剔除面**恰是** `run_id` / `frozen_at` / `project_id`，
  其余 **27** 个声明字段全参与（`comparison_fields()` 公开，新增字段自动纳入）；
- **正例**：仅三身份字段不同的两份 manifest ⇒ 键相等；
- **反向钉**：同一条对上 `semantic_digest()` **不等**——「它不能当配对键」由判据钉住，
  换回去必红；
- **反证**：12 个声明字段逐个漂移（参数化）⇒ 键不等。判据 **16 passed**。

### EC-02 只差一个 slot 的两臂（PASS）

- `AblationPair(slot, present, absent)`：构造期五处拒绝（未知段名 / present 缺席 /
  absent 在场 / manifest 漂移 / 非字符串段值）；
- **正例（判据 ①）**：六段**逐个**消融都成立，`differing_sections()` 恰是 `{slot}`；
  两臂 manifest 的 `comparison_digest` 相等；
- **反证（判据 ②）**：**别的**段换一个字 ⇒ `only_slot_differs()` 判**假**
  （证明它真在逐段比）；被消融段换一个字 ⇒ 两臂渲染必然不同；
- **夹具形状 = 产品形状**：slots 是**已渲染的 `str | None`**（`AgentSessionSpec` 携带的
  形状）。第一版夹具塞视图 dict ⇒ 被产品渲染器**静默丢段**、两臂假相等——判据当场抓到，
  该缝（`_section_of` 只认 str / 视图对象）是 GOAL-091 已登记的既有缺陷。判据 **8 passed**。

### EC-03 可数读数（PASS）

- 三种读数：design block 在场（经 `design_block_in` **同一个**解析器）/ 每臂参数
  （`parse_arms` 两种形态同读数）/ 引用标识数（**有分母**：只在已知 memory id 里找）；
- **两种「空」分得开**：`payload_absent`（读不到正文）≠ `block_absent`（正文在、没写设计）
  ——`source_state` 点名不同；臂解析**三态**（parsed / absent / malformed）不猜；
- 引用计数反证：分母外的 id 形 token（`mem-999999-999`）不计。判据 **9 passed**。

### EC-04 读数表 + `MIN_CORPUS=3` 拒绝门（PASS）

- **反证（判据 ③）**：k=2 ⇒ 门判「不足」并**点名** `ablation pairs: 2 of 3 required`；
  **CLI 退码 1**（认证被拒是可观测事实）；k=3 ⇒ 认证 + 四列位移表；
- **配对完整性**：同一对两臂 `comparison_digest` 不等 ⇒ 点名拒绝；
- **常量同值**：`tools/` 自持的 `MIN_CORPUS` 与产品侧
  `citation_distribution.MIN_CORPUS` 由判据跨模块比对（漂移即红）。判据 **11 passed**。

### EC-05 措辞边界（PASS）

- 闭集非空（`adopt` 族 + `采纳` 族）；**正例**：k=3 / k=2 / k=0 三种报告对闭集零命中；
- **反证（判据 ④）**：往报告文本注入闭集词 ⇒ `render_report` **出口自检判红**
  （守卫在渲染函数体内——「文本出口唯一」由源码判据钉住：`sys.stdout.write` 恰一处且
  只经 `render_report`）；工具源码自身（词表行外）对闭集零命中。判据 **7 passed**。

### EC-06 阶梯改写（PASS —— 只动一格）

- 「计划」行 `下一级` **替换**为消融 bar（新句三锚在位、旧句**不在**——改写不是追加）；
  新 bar 点名本轮交付的机制（`GOAL-20261111-109` / `comparison_digest` / `MIN_CORPUS=3`）；
- **其余三格逐字未动**：检索 / 复检 / 迭代各带改写前锚点短语，且**不含**「配对消融」句
  （越级推广判红）。宪章四判据 **28 passed**。判据 **4 passed**。

### EC-07 收口资产（PASS）

- `tools/verify_goal109_closeout.py` + `tools/goal109_closeout_assertions.py`
  （**65 PASS / 0 FAIL**；断言集在树内**重放**键与两臂的真 manifest 行为，
  不只查文件存在）；登记 `_VERIFIERS` 与 `IN_SCOPE` 两处；
- `R-1`（无采样控制 ⇒ 只能比分布）在 GOAL 声称边界逐字登记，验证器点名它。

## 反证臂汇总（**判据咬得住**的证据）

| 判据 | 反证臂 | 结果 |
| --- | --- | --- |
| `test_comparison_digest` | 12 个声明字段逐个漂移（参数化） | 各自判红 |
| `test_ablation_pair` | 别的段漂移 ⇒ 证明判假；被消融段漂移 ⇒ 渲染必不同 | 红 |
| `test_output_readings` | 分母外的 id 形 token 不计；臂形态非法点名 malformed | 红 |
| `test_ablation_report_gate` | k=2 拒绝 + 点名；两臂键不等拒绝；缺列/类型错拒绝 | 红 |
| `test_ablation_report_wording` | 注入闭集词 ⇒ 出口守卫红 | 红 |
| `test_goal109_ladder_pilot_scope` | 三格出现消融句即红；计划行旧句残留即红 | 红 |

## 结论

**PASS_WITH_WARNINGS**。七条 EC 全 PASS；两条残余（`W-1` 均值差无显著性检验 /
`W-2` 观测汇总靠调用方喂 JSON）、两条未覆盖（`U-1` live k=3 实测未做 /
`U-2` 试点只面向计划域）、两条声称边界（`R-1` 无采样控制只比分布 /
`R-2` 判位移不判采纳）逐条明写，**一条都没藏**。

**本轮一条方法论收获**：**「消融的输入侧证明」与「输出侧读数」必须分开交付**——
`only_slot_differs` 证明「两臂只差一个变量」（可机械判），分布位移是**输出侧读数**的
事实（要 k≥3 次真实 run 取证）；把两者混在一个判据里，要么把输入证明冒充输出结论，
要么把输出结论降格成输入检查。
