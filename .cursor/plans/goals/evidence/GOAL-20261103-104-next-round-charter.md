# 下一轮 charter 骨架（GOAL-20261101-103 → GOAL-20261103-104）

> 本文件由 `tools/next_round_charter.py` **确定性**产出：零出网、零模型、零时钟。
> 同输入 ⇒ 逐字节相同。**判断面**（objective / EC 的内容）不在这里 —— 见末节，
> 那些位置显式留空（`<待填：判断>`），不由本工具猜。

## 一、输入（内容寻址）

- 上一个 GOAL：`.cursor/plans/goals/GOAL-20261101-103-phase-events-and-frontend-visible-chain.md`（`status: ACHIEVED`）
- 上一个复检：`.cursor/plans/rechecks/RECHECK-20261101-103-phase-events-and-frontend-visible-chain.md`（`result: PASS`）
- 宪章：`.cursor/plans/goals/MAINLINE.md`
- 摘要：goal `sha256:06f90675358a7ff5`；recheck `sha256:4484dc16f1bf9a6c`；charter `sha256:0455b41851ca9044`

## 二、上一轮的残余与未覆盖范围（逐条原文，**不摘要**）

共 6 条（`W-0`…`W-5`）。搬运时**不得删、不得改写**；每一条都要在下一轮里被处置
（做掉 / 明确承接 / 登记为不做并给理由）—— 处置**不是**本工具的事。

- `W-0`｜**已修（真跑才发现）**：`experiment` 相是**确定性执行缝**，它**不注册
  `ResearchTask` 行** ⇒ `run_phase_view` 第一版只按任务行推状态，把一个 `SUCCEEDED`、
  `phase.completed` 在场、两份 `experiment_result.json` 已落库的 run 读成
  `experiment: PENDING`。**两相合成协议发现不了它**（合成协议每相都有任务行）——
  是十一相真跑判据抓到的。修法：`state` 改为**相级事件优先、任务行兜底**
  （`_state_from`），制品取两条来源的并集。
- `W-1`｜**相级事件的时刻在事件本身，而 `state` 从任务状态推**：`started_at` /
  `completed_at` 取自 `phase.started` / `phase.completed` 的 `occurred_at`，而
  `PhaseProgressDto.state` 走的是**任务 canonical 状态**。两者在正常情况下一致，
  但**续跑（resume）后重放**的相可能出现「有 completed 时刻而任务状态仍是 RUNNING」
  （或反之）；读面此时以任务状态为准。**没有判据覆盖这个分叉** —— 它需要一次真正的
  续跑取证，本轮没有跑（`U-1`）。
- `W-2`｜**`phases` 只在详情路径给**：列表路径（`GET /projects/{id}/runs`）恒为 `null`。
  这是刻意的（避免 N+1：逐 run 解析冻结协议正文 + 扫制品表），但**用户在多 run 列表上
  看不到进度**。要做就要一条批量读面，本轮不做。
- `W-3`｜**相级事件的 payload 没有 `task_ids`**：`phase.started` 带 `contract_ids`（声明面），
  但「本相实际派了哪几个任务」要从 `task.created` 序列里对。前端展开某相时显示的是
  **该相声明的**制品，不是「按任务归属的制品」（后者要额外的读面字段）。
- `W-4`｜**`retmax` 只在检索类调用上生效**：`apply_retmax` 只改带 `retmax` 键的调用。
  一个声明了别的条数参数（如 `page_size`）的 provider **不会被本项目声明影响** ——
  射程如实登记在 `apply_retmax` 的 docstring 里，没有为它造通用机制。
- `W-5`｜**Windows quality job 20 分钟超时**（GOAL-101 `W-5` 的同一形态，**不是本轮新缺陷**）：
  本轮 CI 可能再次出现 `cancelled`。改 `.github/workflows/**` 属 `escalation_triggers`，
  本轮**未动**。如实记 `cancelled`，不冒充绿。

## 三、阶梯：收录本 GOAL 的域，以及那些域的「下一级是什么」

| 域 | 下一级是什么（原文） |
| --- | --- |
| 复检 | → 评审者与作者分开：novelty 相的作者角色从 novelty_reviewer 拆成新增的 novelty_author（agent novelty_writer / deepseek-v4-pro-0813）⇒ 角色 id、agent id、(endpoint, model_name) 三者都不同；判据跨 28 份出厂协议遍历「评审者不得评自己写的产物」（此前缺陷与 v2 无关，换协议同样能写出该形状）。这属独立性，不是「评审者是否真的判得对」。 判词改写了下一轮的计划/立题（现判到「上一轮的判词在下一轮的会话里可见、可归因、分歧不丢」；「模型据此真的改了立题或计划」仍无判据 —— 与 GOAL-082 EC-04 的未决取舍同源：模型对内容采纳不可判，子串判据会假绿） |

- 收录本 GOAL 的域：复检
- 这些「下一级」是本轮的**候选靶子**；做哪一个、做几个，**是判断**，不是提取。
- 若某域的「下一级」为空串 ⇒ 该域已到头（宪章口径），不要凭空造下一格。

## 四、CI 台账结论（机械读数，不是独立取证）

- 结论：**有判红（5 行）**
- 行数：12（全 success 2 / 无 run 0 / 判红 5）
- 最后一条：ef755a99 ⇒ M0 cancelled（7/8 job success，quality-windows-latest 撞 20 分钟超时窗口 —— W-5 的同一形态）；Push 全 success（CodeQL 三语言 success）
- 未识别行：24e3418b ⇒ 本地 m0 终态行 PASS: profile=m0; 23 deterministic checks（24 条 PASS [ 行 = 23 + 计数外的 release-assets-immutable）；零 run（covered_by: ef755a99） —— 同批推送
- 未识别行：6420d868 ⇒ 覆盖：与 1274e279 同批推送，被合并进那一条 M0 run
- 未识别行：79d02c28 ⇒ 零 run（covered_by: 52f7ed35）
- 未识别行：52f7ed35 ⇒ 交付提交；CI 读数见下（本行为本轮的真跑取证提交）
- 未识别行：a889872f ⇒ 零 run（covered_by: ef755a99）

## 五、下一轮 GOAL 的骨架（可由提取得到的那部分）

```yaml
id: GOAL-20261103-104
status: DRAFT
created_at: 2026-11-03
updated_at: 2026-11-03
objective: <待填：判断>
exit_criteria: <待填：判断（每条自带 verify 与反证臂）>
budget:
  max_cycles: <待填：判断>
  per_cycle_minutes: <待填：判断>
  no_progress_stop_cycles: <待填：判断>
authorization:
  source: user-request
  ref: <待填：本轮授权的原文要点>
latest_recheck: null
```

## 六、不可自动推导的部分（**判断**，本工具不猜）

- `objective`：本轮要达成的**一句话目标**；
- `exit_criteria`：每条可机检（命令 + 期望值），且**自带反证臂**（改事实 ⇒ 判据翻向）；
- 靶子选择：第三节里挑哪一个「下一级」，为什么是它而不是别的（写清依赖与代价）；
- 预算与授权：`max_cycles` / 授权要点 / 是否需要停下登记。
