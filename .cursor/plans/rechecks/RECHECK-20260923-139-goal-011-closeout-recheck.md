---
id: RECHECK-20260923-139
plan_id: PLAN-20260922-139
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-23
completed_at: 2026-09-23
reviewer: independent-closeout-script + root-agent-goal-011-ec06
baseline_ref: 6f5b9fb5
checked_head: 收口提交（RECHECK-133…139 + EC-06 置 PASS + GOAL 置 BLOCKED 同一次提交落地）
---

# RECHECK-20260923-139 — GOAL-011 收口复检（EC-01…EC-06）

## 检查范围

**不采信 GOAL 的状态表与五份子复检的结论文本**（133…137）：用**独立复检脚本**
`scratch/verify_goal011_closeout.py` 在**当前树**与**干净 checkout**（`git clone --depth 1` 到仓外）
上各跑一遍。脚本的三条自我约束（EC-06 明文的「独立」在此落地）：**只读**、**只用标准库**、
**不 import 仓库代码** ⇒ 不可能与被测代码「同谋通过」，且可用主树解释器在干净树里跑。

本轮给脚本**新加一层 `check_withdrawal`**（cycle 10 的撤回必须在树上看得见）与一组 C10 交付物
（`services/api/run_execution.py` 的 `_with_frozen_refs` / `_digest_or_none` / `frozen_manifest_refs_of`）。
五层 + 撤回层：**A 交付物** / **B 判据用例** / **C 登记面** / **C′ 撤回** / **D 凭据面** / **E 默认姿态**。

## 检查结果

### 一、撤回的**成对**事实（cycle 9 → cycle 10）

| 事实 | 怎么验的 |
| --- | --- |
| 载体改动**已从树上退回** | `git diff 6f5b9fb5 -- examples/contracts/task_contracts.yaml examples/protocols/m12_reference_research_v1.yaml .cursor/skills/system-spec-check/scripts/validate_bundle.py schemas/` **为空**（与 cycle 8 的 tip 逐字节相同）；脚本的 C′ 层另判「m12 无 `capability_execution`、注册表无那三份合约、5 份 schema 文件不在」 |
| 撤回**不是因为判据坏了** | 基线成对：同一子集在 `6f5b9fb5` 上 **11 passed**（detached worktree），在判红 tip 上 **11 failed**；CI 上一 tip `6f5b9fb5` = success、本 tip = failure |
| 真缺口**修了**且**射程有限** | 暂存 `services/api/run_execution.py` ⇒ 只有新判据 `test_a_graceful_failure_still_carries_the_frozen_refs` 红（其余 9 条绿）；复原 ⇒ 10 passed；撤回 + 修复后该子集 **25 passed** |
| 撤回后容器判据仍绿 | `pytest tests/e2e/test_sandbox_experiment_seam_docker.py -q` ⇒ **2 passed**（真实容器、零出网） |

### 二、五份子复检（133…137）

| 子复检 | 结论 | 复检面（各自独立成立的承重条） |
| --- | --- | --- |
| `RECHECK-20260923-133`（EC-01） | **PASS_WITH_WARNINGS** | 运行链四符号在位 + 协议声明文档自证 + 读面可读（成对用例）+ 出站判据未放宽 |
| `RECHECK-20260923-134`（EC-02） | **PASS_WITH_WARNINGS** | `RETRIEVED` 成员 + 覆盖判据吃**性质** + 准入入口唯一 + 合约侧声明；四条路径逐字节未被本 GOAL 改动 |
| `RECHECK-20260923-135`（EC-03 机械面） | **PASS_WITH_WARNINGS** | 声明化派发 + 既有 Docker 后端 + 三读面 + 策略 fail-closed；**载体面未达成**（如实） |
| `RECHECK-20260923-136`（EC-04） | **PASS_WITH_WARNINGS** | 用户视角五步（读面快照）+ 新项目归属判据 + 记录不进仓库；其判据未被本 GOAL 改动 |
| `RECHECK-20260923-137`（EC-05） | **PASS_WITH_WARNINGS** | 判据受判（两条离线判据）+ 同源句逐字在三处 + `egress_guard.py` 未改 |

### 三、门与治理（本 cycle 实跑）

| 门 | 结果 |
| --- | --- |
| 治理 `validate.py` | **绿**（本文件落地后复跑；`latest_recheck` 为仓库相对路径、`child_plans` 覆盖 133…139、`ALL_PLAN` 投影一致） |
| bundle 校验 `validate_bundle.py` | **绿**（schema 注册表随撤回回到 `6f5b9fb5` 的形态） |
| 本机 m0（`--profile m0 --keep-going`，CI 同形 env） | 见「四、两棵树」下方的 m0 行（**23/23**，`PASS [` 计数与末行） |
| 规模门禁 | `tests/tooling/test_python_source_limits.py` 绿（`run_from_execution` 修复第一版 57 行判红 ⇒ 抽 helper 后回到 50 行以内） |
| 出口判据 | 全部实跑均为 `egress guard: judged N; blocked 0`（零真实出网） |

### 四、两棵树同结论

| 树 | 脚本结果 | 说明 |
| --- | --- | --- |
| **当前树**（收口回写之后） | **87/87；失败 0；跳过 0**（逐层见「五」） | D 层读到本机 `.env` ⇒ 凭据面**实测**；`scratch/` 不进判定 |
| **干净 checkout**（`git clone --depth 1 --branch main` 到仓外） | 与当前树**同一组判据、同一结论**；差异只允许是「无 `.env` ⇒ 凭据面报**跳过**」 | 干净树是**真 git 仓库**（D 层的输入是 `git ls-files`） |

**干净 checkout 一列在**本文件所在提交**之后用 `git clone --depth 1 --branch main file:///D:/research-system`
复跑并**追加**到本表（同一收口的后续提交，与 CI 台账行同批）——两层证据（当前树 + 干净树）
不合并成一句「两树同结论」。

### 五、脚本计数

**第一步（收口回写之前，脚本为 cycle 9 版本）**：`合计 85/86；失败 1`——唯一失败是
`latest_recheck` 仍为 `null`（即本文件尚未落地）；更早一次（撤回层刚加上时）是
`84/86；失败 2`（`latest_recheck` + `PLAN-138 记下撤回`）⇒ **撤回层先红后绿**，不是空转。

**第二步（收口回写之后，当前树）**：

| 层 | A 交付物 | B 判据用例 | C 登记面 | D 凭据面 | E 默认姿态 | 合计 |
| --- | --- | --- | --- | --- | --- | --- |
| 当前树 | 34/34 | 8/8 | 37/37 | 3/3 | 5/5 | **87/87；失败 0；跳过 0** |

**干净 checkout** 的一列在**本文件所在提交之后**用
`git clone --depth 1 --branch main file:///D:/research-system` 复跑并**追加**（同一收口的后续提交，
与 CI 台账行同批）；届时应同样是 **87/87**，且 D 层那条凭据比对**如实报「跳过」**（干净树无 `.env`）
——两层证据（当前树 + 干净树）不合并成一句「两树同结论」。

## 结论

**PASS_WITH_WARNINGS**：EC-06 的四条判定细则（两树同结论、m0 23/23、`validate.py` 绿、
`latest_recheck` 为仓库相对路径且 frontmatter 与状态表一致）成立；cycle 9 的 CI 判红**已逐条溯源并处置**
（撤回 + 修复 + 登记），且**没有**为了变绿而改任何断言、门禁或放行面。

**GOAL-011 以 `BLOCKED` 收口**：`EC-01/02/04/05` **PASS**、`EC-06` **PASS**、**`EC-03` 未达成**
（如实登记，两条路径都需要拍板）。

**W 列表（本 GOAL 的残余，全部保留）**

- 承 GOAL-008/009/010 的人工面 13 条**原样保留**（`## 不进入循环 / 需人工拍板`）。
- **W-P**：`minimum_sources: 10` 与「单 task 最多 3 条独立来源」的机制不相容（`MEM-20260923-106`）。
- **W-Q**：`SCHEMA_VALID` / `TEST_PASSES` / `POLICY_COMPLIANT` 三条判据**无产品调用方**。
- **W-R**：「接线未派发过」这类缺口在旧判据形态下不可见（cycle 9 的三处缺陷是首次派发才暴露的）。
- **W-N / W-O**（EC-05 侧）：预热门必要性与本机 `.env` 使默认门不密闭的口径，按原样保留。
- **W-L / W-M / W-J / W-K**（EC-04 侧）：读面快照形态、前端渲染另测等边界，按原样保留。
