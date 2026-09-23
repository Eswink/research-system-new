---
id: RECHECK-20260923-150
plan_id: PLAN-20260923-149
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-23
completed_at: 2026-09-23
reviewer: independent-closeout-script + root-agent-goal-012-ec06
baseline_ref: 0584276
checked_head: 01bd789（收口提交）前的当前树与干净 checkout `01bd789` 同结论；收口提交只增加记录
---

# RECHECK-20260923-150 — GOAL-012 收口复检（EC-01…EC-06）

## 检查范围

**不采信 GOAL 的状态表与五份子复检的结论文本**（141/143/145/146/148）：用**独立复检脚本**
`scratch/verify_goal012_c6.py` 在**当前树**与**干净 checkout**（仓外 `git worktree` 到 `01bd789`）
上各跑一遍。脚本三条自我约束（EC-06 明文的「独立」在此落地）：**只读**、**只用标准库**、
**不 import 仓库代码** ⇒ 不可能与被测代码「同谋通过」，且可用主树解释器在干净树里跑。
六组判据：**A** 五个 EC 的判定面（frontmatter `status` + `status_note` + **正文状态表一致**）、
**B** 每个 EC 的载体件在位、**C** 子 PLAN 全 `DONE` + `latest_recheck` 是**仓库相对路径** + 复检通过、
**D** 残余不得消失、**E** 只读历史不动、**F** 姿态不变。

## 检查结果

### 一、两棵树同结论

| 树 | 脚本结果 | 说明 |
| --- | --- | --- |
| **当前树** | `checked=70 failures=0`（收口记录落盘后） | A 12 + B 13 + C 25 + D 7 + E 3 + F 2 组判据全绿 |
| **干净 checkout**（`01bd789`，仓外 worktree） | `checked=70 failures=1` | 唯一那条红是 **「EC-06 尚未判定」**（收口前该 EC 的状态字段仍是未判定值）——收口记录（EC-06 的状态与这份复检）正是在**收口提交**里落盘；两棵树在**同一判据、同一判词**上给同一结论（干净树多出的这一条红的**内容**与「待收口」一致，不是分歧） |

⇒ 收口提交把该条判据转绿（见「五」），**收口提交只增加记录**（PLAN-149 / 本复检 / GOAL 回写），
不含任何产品面改动。

### 二、五个 EC 的判定面（**交叉核对，不采信子复检的文本**）

| EC | 载体件（脚本 B 组实测在位） | 子 PLAN / 复检 |
| --- | --- | --- |
| EC-01 | `packages/application/preflight/policy_acceptance.py` | PLAN-140 → `RECHECK-141` |
| EC-02 | `tests/e2e/test_ec02_experiment_chain_offline.py`、`test_ec02_experiment_live.py` | PLAN-142 → `RECHECK-143` |
| EC-03 | `tests/e2e/test_ec03_experiment_evidence_chain.py` | PLAN-144 → `RECHECK-145` |
| EC-04 | `docs/roadmap/PATH_B_REFUTATION_RECORD.md` + PLAN-146 | PLAN-146 → `RECHECK-146` |
| EC-05 | `apps/web/tests/e2e/live-experiments.spec.ts` + `live-specs.ts` + `tests/api/console_api_app.py` | PLAN-147 → `RECHECK-148` |

五份子 PLAN 全部 `status: DONE`，`latest_recheck` 全是**仓库相对路径**且指向 `result: PASS` 的复检。

### 三、只读历史与姿态（脚本 E/F 组）

- GOAL-011 的 `W-P` / `W-Q` 仍在原文；`PLAN-20260922-138` 仍 `status: BLOCKED`；
  `docs/roadmap/PATH_B_REFUTATION_RECORD.md` 仍写「**已否证 / 待重新设计**」。
- `tests/egress_guard.py` 在位；`.env` 里**没有** `RESEARCHOS_AGENT_RUNTIME` 这个键
  （脚本**只看键名、不读任何值**）。

### 四、残余原样保留（脚本 D 组）

13 条人工面登记仍在 GOAL 正文；本 GOAL 的 `W-A` / `W-C` 仍在；建档残余
`R-M1`（Mimosa `scanner_enobufs` 未得完整结论 ⇒ **不得宣称项目安全**）、
`R-D1`（23 条 Dependabot 告警：4 high / 13 moderate / 6 low，既有未处置）、
`R-B1`（已由 EC-04 落成独立记录）、`R-N1`（30 条非 ASCII 路径登记豁免）全在。

### 五、门、治理与 CI

| 项 | 结果 |
| --- | --- |
| 本地 m0（`--profile m0 --keep-going`，CI 同形 env） | **`PASS: profile=m0; 23 deterministic checks`**（`scratch/goal012-c6-m0.log`：24 条 `PASS [` 行 = 23 项 + 计数之外的 `release-assets-immutable`；无 `FAILED` 行；`python/tests` **4411 passed / 19 skipped / 0 failed**） |
| 治理 `validate.py` | **绿**（收口记录落盘后复跑；`latest_recheck` 为仓库相对路径、`child_plans` 覆盖五份子 PLAN + 本收口 PLAN、`ALL_PLAN` 投影一致） |
| `docs_consistency_check` | `DOCS-CHECK PASS: 6 deterministic checks` |
| 出站 | `egress guard: judged 788; blocked 8`——**8 条全部**来自故意探针 `tests/architecture/python/test_default_egress_guard.py`；本 cycle **零真实出网、零凭据读取** |
| CI 台账（cycle 5，两棵树之外的第三方） | `d5baf05`：M0 [35847860197](https://github.com/Eswink/research-system-new/actions/runs/35847860197) **red**（两个 quality job：`MEM-113` 引用的复检落在下一个提交 ⇒ 治理判据报「工程记忆来源不存在」）；`0584276`：M0 [35849811097](https://github.com/Eswink/research-system-new/actions/runs/35849811097) **六 job 全 success**（含 `console-frontend` 在 Linux 上跑新增的 live spec）+ CodeQL [35849810499](https://github.com/Eswink/research-system-new/actions/runs/35849810499) **3/3 success** |

**CI 那次判红如实入册**（不是产品缺陷、不是判据缺陷，是**提交切分错误**）⇒ 处置 = 让引用与产物
同源落地，**判据未放宽**；事实进 `MEM-20260923-114`。

### 六、收口形态（脚本 A/C 组 + 本提交）

GOAL-012 的 frontmatter：EC-01…EC-06 全 `status: PASS` 且各带 `status_note`；
`status: ACHIEVED`；`latest_recheck` 指向本文件（**仓库相对路径**）；`child_plans` 六项、
`memory_entries` 五项（`MEM-109`…`MEM-114`）；正文状态表六行与 frontmatter **一致**。

## 诚实边界

- 本复检**不重跑**五个 EC 的判据本身（那五份子复检各自做了实跑与按压）；它判的是**判定面、
  载体、登记、残余、姿态**在收口时仍然成立——即「收口没有把任何东西弄丢或改写」。
- GOAL-012 的**真实 live 调用**只在 EC-02 做过**最小必要次数**（一次真实 run，样张
  `scratch/goal012-c2-live-sample.json`）；本 cycle 未做任何真实调用（`ANTHROPIC` run 腿仍记为可选）。
- EC-05 的判据覆盖「读面 → DTO → 页面」；其夹具**执行体不是真容器**（真实容器全链在
  EC-02/EC-03 的 pytest 层），这一边界在 PLAN-147、`RECHECK-148` 与 spec 文件头三处写明。

## 结论

**PASS**。GOAL-012 的五个 EC 全部 PASS 且判定面/载体/复检交叉一致；残余（13 条人工面 +
`W-A`/`W-C` + `R-M1`/`R-D1`/`R-B1`/`R-N1`）与 GOAL-011 的历史登记**原样保留**；两棵树同结论、
m0 **23/23**、治理与文档检查绿、CI 台账到终态（含一次判红及其修复）。⇒ **GOAL-012 收为 `ACHIEVED`**。
