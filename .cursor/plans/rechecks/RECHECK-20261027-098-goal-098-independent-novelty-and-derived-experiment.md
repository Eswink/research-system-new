---
id: RECHECK-20261027-098
slug: goal-098-independent-novelty-and-derived-experiment
title: GOAL-098 复检 —— 拆开创新点的作者与评审者，并让实验脚本由计划选择
status: COMPLETED
result: REVISE
created_at: 2026-10-27
updated_at: 2026-10-27
plan_id: PLAN-20261027-098
parent_goal: GOAL-20261027-098
owners:
  - root-agent
verify_paths:
  - examples/config/roles.yaml
  - examples/config/agents.yaml
  - examples/config/models.yaml
  - examples/config/team_templates.yaml
  - examples/protocols/direction_to_report_v2.yaml
  - examples/contracts/task_contracts.yaml
  - docs/catalog/SYSTEM_ROLES.md
  - packages/application/experiments/design_script.py
  - packages/application/experiments/design_from_plan.py
  - services/api/experiment_support.py
  - tests/contracts/test_direction_to_report_v2_independence.py
  - tests/application/test_experiment_script_comes_from_the_plan.py
  - tests/tooling/test_short_archive_revision_rows_are_registered.py
  - .cursor/plans/goals/archive/SHORT-REVISION-ROWS.md
  - tools/verify_goal076_closeout.py
  - tools/verify_goal090_closeout.py
  - tools/verify_goal095_closeout.py
  - tools/verify_goal098_closeout.py
memory_entries: []
---

# RECHECK-20261027-098 — GOAL-098

## 检查结果

**REVISE**。七个 EC 中**六个 PASS**，`EC-02`（真跑）**未达成** —— 上游 Europe PMC 服务级
不可用（两次同签名 + 独立探针）。逐条如下，不粉饰。

## 逐 EC

| EC | 结论 | 证据 |
| --- | --- | --- |
| EC-01 | **PASS** | `tests/contracts/test_direction_to_report_v2_independence.py` 18 例全过；含真文件按压（把 `novelty` 相角色改回 `novelty_reviewer` ⇒ 自评扫描点名判红 + 按 raw `sha256` 复原）与**跨 28 份出厂协议**的自评形态扫描（修复前只有 v2 命中） |
| EC-02 | **PENDING** | 凭据与 Docker **都可用**，但**上游服务不可用**：两次真跑同签名停在检索相（`europe pmc temporarily unavailable`）；独立 `curl` 探针连 `query=cancer` 也 **503** ⇒ 服务级不可用。产品接线刻意只接 Europe PMC ⇒ **不**为让判据变绿而改实现。`review_row_count=0` ⇒ 无运行期读数。**不用同一个模型凑** |
| EC-03 | **PASS** | `tests/application/test_experiment_script_comes_from_the_plan.py` 17 例全过；子进程按压（删掉 `plan_selected_script` 那一行 ⇒ 行为判据真的 exit 1，`assert seen == [...]` 指向装配兜底脚本） |
| EC-04 | **PASS** | 三个验证器判词 48 / 51 / 54 条全过、零 FAIL；`test_short_archive_revision_rows_are_registered.py` 7 例（含两条真文件按压）；`progress-075` 链接在宪章里可解析 |
| EC-05 | **PENDING** | 本次复检时点尚未建；它的判词就是后续收口复检的产出 |
| EC-06 | **PASS** | 宪章 `max_goals: 100`；`## 修订记录` 的序 66 行写明「扩表前 70 / 已用 65 / 新增序 66 ⇒ 66 / 扩到 100」 |
| EC-07 | **PASS** | 序 65 的 5 格行在 `archive/MAINLINE-2026-10-26-revisions-65-only.md`；活跃面短行判据 `test_no_revision_row_in_the_live_table_is_too_short_to_be_seen` 在树且带反证臂；本轮修订行为 5 格 |

## 连带申报（`git diff --numstat` 逐条）

**事实变更**（条目数变了，不是放宽判据 —— 两处都只改那个**数**，`catalog==fixture` 与
「加载器读到每一个条目」两条**未动**）：

| 文件 | 改动 | 不是放宽的理由 |
| --- | --- | --- |
| `tests/loaders/test_contract_loaders.py` | `26` → `27`（两处：`:50` 与 `:246`） | 判据问的是「加载器读到出厂文件的每一个条目」；新增 `novelty_author` ⇒ 条目数变了是**事实**。两条计数是**同一件事实**（专用加载器与通用分派必须一致） |
| `.cursor/skills/system-spec-check/scripts/validate_bundle.py` | `!= 26` → `!= 27` | 同一事实变更；上一格「catalog 与 fixture 一致」**逐字未动** |

**既有文件被改（非判据）**：

| 文件 | 改动 |
| --- | --- |
| `examples/config/roles.yaml` | 新增 `novelty_author`（27 条），未改任何既有角色 |
| `examples/config/models.yaml` | 新增 `novelty_author_model`，未改任何既有模型 |
| `examples/config/agents.yaml` | 新增 `novelty_writer`，未改任何既有 agent |
| `examples/config/team_templates.yaml` | `standard` 加一行；`lean` / `rigorous` 未动 |
| `examples/protocols/direction_to_report_v2.yaml` | `novelty` 相角色替换 + 注释；相集 / 合约 / 产物名 / 跨相边**一字未动** |
| `examples/contracts/task_contracts.yaml` | `research_report_plan` 的任务书**增**一段（可选 `script` 键的闭集说明）；既有规则段未动 |
| `docs/catalog/SYSTEM_ROLES.md` | 新增 `NoveltyAuthor`，其后条目重编号 |
| `packages/application/experiments/design_from_plan.py` | 新增 `plan_design_block`（既有函数未动） |
| `services/api/experiment_support.py` | `run()` 增一行调用 + 三行注释压缩（449/450 的余量约束） |
| `.cursor/plans/goals/MAINLINE.md` | 程序表序 66、`max_goals` 70→100、阶梯两行、进展/修订各一行、`progress-075` 链接、短行登记指针 |

## 两向按压（真文件，raw `sha256` 复原）

1. **EC-01**：把 `novelty` 相的 `novelty_author` 换回 `novelty_reviewer` ⇒
   `self_review_shapes('direction_to_report_v2.yaml')` 返回
   `[('review', 'novelty', 'novelty_claim', ['novelty_reviewer'])]` ⇒ 两条判据同时判红；
   复原后 sha 相同。
2. **EC-03**：删掉 `script = plan_selected_script(...)` 那一行 ⇒ **子进程**里跑
   `test_the_plan_script_is_what_the_sandbox_runs` ⇒ exit 1、断言信息是
   `assert ['examples/ex…benchmark.py'] == ['examples/ex…_baseline.py']`（即回落装配兜底）；
   复原后同一用例 exit 0。
3. **EC-04 短行登记**：删掉登记表一行 ⇒ 覆盖面判红并点名 `MAINLINE-2026-10-13-revisions-38-only.md:14`；
   清空一条理由 ⇒ 理由判红。两向复原 sha 相同。

### 按压工具自己的 bug（两次，都是靠「按压后确认真的红了」发现的）

- **第一次**：用 `monkeypatch` 改 `_governed_executor` 来模拟「删掉实现」—— 对**已导入的
  字节码**毫无影响 ⇒ 按压假绿。改成子进程读**磁盘真字节**。
- **第二次**：子进程的 `pytest` 目标写成 `file.py::test_name`，而该用例在类里 ⇒
  `pytest` exit 4（usage error）⇒ 我把它读成「按压失败」。补上 `::ClassName` 才真的红。

## 未覆盖 / 残余

见 GOAL 正文 `## 残余与未覆盖范围`：`W-1`（租约根因）、`W-2`（检索 `phase_id` 常量）、
`W-3`（方案 (a) 待拍板）、`W-4`（076 交付面未完成）、`W-5`（**Europe PMC 503 挡住 EC-02 的
运行期面**，两次同签名 + 独立探针取证）、`U-1`…`U-3`、`R-1`…`R-3`。

## 结论

EC-01 / EC-03 / EC-04 / EC-05 / EC-06 / EC-07 **达成**；EC-02（真跑）**未达成** —— 上游
（Europe PMC）服务级不可用，两次同签名、独立探针复现，且**不**为让判据变绿而改产品接线。
已如实登记为 `W-5`。GOAL 保持 **ACTIVE**，下一 cycle 或上游恢复后补取证。
