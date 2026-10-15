---
id: MEM-20261015-222
title: "把写死的量变成声明量时的五个决定点：声明层选在哪、白名单还是转发、缺省怎么回落、命名空间会不会撞"
status: ACTIVE
created_at: 2026-10-15
updated_at: 2026-10-15
scope: repository
confidence: 0.9
review_after: 2027-04-15
source_plans:
  - .cursor/plans/tasks/PLAN-20261015-477-goal-079-ec01-experiment-parameters-come-from-the-declaration.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261015-478-goal-079-ec01-experiment-parameters-come-from-the-declaration.md
supersedes: []
tags: [research-loop, experiment, parameter-surface, whitelist, fail-closed, sandbox]
---

## 做了什么

把实验脚本里**写死的量**（`SEED = 7` / `N_ITEMS = 800` / `N_DUPLICATE_PAIRS = 40`）
变成**声明量**（GOAL-20261015-079 EC-01）：声明经「装配 → `ExperimentExecutionRequest.environment`
→ 容器」到达脚本，脚本读环境、**缺省回落**既有常量。

## 为什么这样做（五个决定点，都可复用）

1. **声明层选在哪** —— 参数放在**装配面**（`SandboxExperimentAssembly.parameters`），
   **不是**契约。依据是既有文档逐字写着的边界：`TaskContract.experiment` 的 docstring
   明说「工作区、会话 id、**种子**属于装配上下文，**不进契约**」。契约放「这件工作由谁执行」，
   装配放「这次跑什么」。**别把两者混起来**：把参数塞进契约会让「同一个合约」有两种含义。
2. **白名单还是转发** —— 参数面是**声明白名单**（`ALLOWED_PARAMETERS`），
   白名单外的键**点名拒绝**。「把调用方给的环境原样塞进容器」是另一个更危险的设计
   （§9 默认 deny 的镜像）；判据断言**未声明的键传不进去**。
3. **缺省怎么回落** —— **缺席 ⇒ 回落既有常量**（零回归）；**值非法 ⇒ 点名失败**
   （**不静默回落**）。两件事必须分开：静默回落会把「声明被吞掉」伪装成「跑成功」，
   而那正是这类改造最典型的隐性缺陷。
4. **命名空间会不会撞** —— 参数键带固定前缀（`EXPERIMENT_PARAM_`），与执行器自己的键
   （`EXPERIMENT_RUN_ID`）**不相交**；判据显式断言这一点（参数面**覆盖不了**执行器的键）。

5. **派生 id 的命名空间**（GOAL-20261015-079 EC-02 实测补） —— 新概念（**臂**）必须有自己的
   **id 派生**，**不能**复用「一 run 一个 X」那条既有派生：实测 `experiment_run_id_of(run_id)`
   只吃 run id ⇒ **两个臂会撞同一个实验 id**。正确做法是**两条派生并存**（单臂路径逐字不变 +
   `arm_experiment_id(run_id, arm)` 按 run+臂确定性派生），而不是改既有派生 —— 改它会动到
   已冻结的 M12 参考身份。

## 怎么做与复现

```bash
# 11 例：白名单 / 逐键传递 / 零回归 / 脚本真读 / 非法值点名 / 命名空间
uv run --frozen --no-sync python -B -m pytest tests/application/test_experiment_parameters.py -q

# 三向按压（白名单 / 传递链 / 脚本读取各先红后绿 + 逐字节复原）
uv run --frozen --no-sync python -B scratch/goal079_press.py
```

实测：**11 passed**；缺省跑出 `seed=7` / `n_items=800`（与改动前逐字相同）；
`EXPERIMENT_PARAM_SEED=11` ⇒ `seed=11`；非法值 ⇒ 退出码非 0 + stderr 点名。
三向按压 `V9-1…V9-3` 全 `RED`、`sha 复原一致=True`。

## 适用边界

- **参数只支持整数**（脚本侧 `_declared_int`）：现有三个参数都是整数 ⇒ 不假装通用；
  加字符串/浮点参数时**同轮**加对应的读取与判据。
- **参数进容器环境 ⇒ 沙箱内可读**（这是目的）；**不得**把凭据放进参数面。
- **「参数由声明给出」≠「计划驱动实验」**：`ExperimentPlan` 今天仍**无参数位**；
  「哪个臂用哪组参数」的声明位是**下一格**（多臂/对照）的事，别把前者读成后者已完成。
- 本记忆**不**作任何安全结论（`R-M1` 未收口）。

## 来源

- `PLAN-20261015-477` / `RECHECK-20261015-478`；
- 落点：`packages/application/experiments/plan_parameters.py`（84 行）+
  `services/api/experiment_support.py`（装配面）+ `examples/experiments/exact_match_index_benchmark.py`（脚本侧）；
- 判据：`tests/application/test_experiment_parameters.py`（11 例）。
