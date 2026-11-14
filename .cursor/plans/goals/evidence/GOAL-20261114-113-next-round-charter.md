# 下一轮 charter 骨架（GOAL-20261111-112 → GOAL-20261114-113）

> 本文件由 `tools/next_round_charter.py` **确定性**产出：零出网、零模型、零时钟。
> 同输入 ⇒ 逐字节相同。**判断面**（objective / EC 的内容）不在这里 —— 见末节，
> 那些位置显式留空（`<待填：判断>`），不由本工具猜。

## 一、输入（内容寻址）

- 上一个 GOAL：`.cursor/plans/goals/GOAL-20261111-112-experiment-generation-enablement-surface.md`（`status: ACHIEVED`）
- 上一个复检：`.cursor/plans/rechecks/RECHECK-20261112-112-authored-enablement.md`（`result: PASS_WITH_WARNINGS`）
- 宪章：`.cursor/plans/goals/MAINLINE.md`
- 摘要：goal `sha256:073f6664b0c0681a`；recheck `sha256:6eaafe7e5c4fbf10`；charter `sha256:50afc50555dec91a`

## 二、上一轮的残余与未覆盖范围（逐条原文，**不摘要**）

共 2 条（`W-1`…`W-2`）。搬运时**不得删、不得改写**；每一条都要在下一轮里被处置
（做掉 / 明确承接 / 登记为不做并给理由）—— 处置**不是**本工具的事。

- `W-1` **第四键只有形状校验、没有执行语义**：`requires_workspace_lease` 是
  `examples/config/policy.yaml` 的 `workspace.write.code` 里**早已声明**的一条
  （全仓除该 YAML 外零命中）。本轮的判据是「同一张表三面对齐」，不是「重新发明合法约束集」
  ——把出厂策略里写着的键判成「非法」会让真实控制面 preflight 直接 FAIL（实测三条判据当场红）。
  因此它进了闭集并过形状校验（`bool`），但**执行语义未实现**：判它需要「租约是否已持有」
  这个事实，实验执行边界拿不到。**这是本轮之前就存在的缺口，本轮没有扩大也没有假装补上。**
- `W-2` **`script_source: authored` 只接在声明面与权威面**：`declared_script_source`
  读得出、`authority_for` 拦得住，但**派发路径还没有把它串起来**
  （`plan_selected_script` 目前仍按白名单选脚本，不看 `script_source`）。串起来要改派发体
  如何把「脚本字节从哪来」交给执行后端 —— 那是**执行面**改动，不是声明面，本轮未做。

## 三、阶梯：收录本 GOAL 的域，以及那些域的「下一级是什么」

| 域 | 下一级是什么（原文） |
| --- | --- |
| 实验 | → 参数由计划声明 + 三条约束在全部执行面生效（GOAL-20261111-112）：sandbox_required / path_prefix / max_seconds 的判定收进唯一一张表（experiments/constraint_table.py），实验执行边界 / 工具面 / preflight 三面同判——此前工具面丢掉约束、preflight 只复述键名（W-4）。requires_workspace_lease 是出厂策略里早已声明的一条，本轮只过形状、不假装执行。script_source 闭集 shipped / authored 已可声明，authored 需具名安全 profile；AUTHORED_ALLOWED_BY_DEFAULT 仍 False（只交付可启用的网，不宣称生成级已启用） — GOAL-20261111-112 |

- 收录本 GOAL 的域：实验
- 这些「下一级」是本轮的**候选靶子**；做哪一个、做几个，**是判断**，不是提取。
- 若某域的「下一级」为空串 ⇒ 该域已到头（宪章口径），不要凭空造下一格。

## 四、CI 台账结论（机械读数，不是独立取证）

- 结论：**有判红（3 行）**
- 行数：3（全 success 0 / 无 run 0 / 判红 3）
- 最后一条：ab97a4b9 ⇒ M0 failure：同上两个 job 红，其余 6 success；Push 3/3 success

## 五、下一轮 GOAL 的骨架（可由提取得到的那部分）

```yaml
id: GOAL-20261114-113
status: DRAFT
created_at: 2026-11-14
updated_at: 2026-11-14
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
