---
id: PLAN-20260922-132
slug: goal-010-closeout-recheck
title: GOAL-010 收口复检：独立复检脚本（当前树 + 干净 checkout 同结论）+ m0 23/23 + 残余登记 + 本文件自检（EC-06）
status: IN_PROGRESS
created_at: 2026-09-22
updated_at: 2026-09-22
parent_goal: GOAL-20260921-010
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    GOAL-20260921-010 cycle 6 = EC-06（收口复检 + 残余登记）。授权来源：2026-09-21 用户 goal 模式指令
    frontmatter `authorization.ref`——(5) push-to-main-for-CI（只推 main、不 force、不重写历史、不推旁支）。
    **本 PLAN 不发起任何真实调用**：复检脚本**只读**（记录/文档/索引/被跟踪文件），凭据面**只输出命中数与
    相对路径、永不打印值**；不改门禁/断言强度、不新增依赖、不改 pin、不改 Domain / Canonical State。
    **明文不做**：为凑绿而改 validator/门禁/快照/测试断言；skip 或降低断言强度；
    把「脚本没报错」当成「判据成立」；把未实跑的项写成 PASS。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260922-132 — GOAL-010 收口复检（EC-06）

## 目标

按 EC-06 的判定细则做**收口复检**：一份**不 import 仓库代码**的独立复检脚本在**当前树**与
**干净 checkout** 上给出**同一结论**，外加全量 m0、治理 `validate.py`、CI 台账逐 run 到终态，
以及**残余登记**（GOAL-008 的六项人工面 + GOAL-009 的 W 列表**原样保留** + 本 GOAL 自己的 W 列表）。

**本 PLAN 的产出是复检结论，不是新功能**：除「登记/收口」类改动外，**不改产品代码、不改判据**。
任何被复检抓出的真问题，要么当场修（独立 commit + 重跑），要么**如实登记为残余**——不得为了让
复检变绿而改复检脚本的判据（GOAL-009 收口时那条教训：脚本第一版判据写错、第二版是**让判据更准**）。

## 验收条件（本 PLAN 自己的）

- 复检脚本在**两棵树**上跑出**同一结论**；两树差异只允许出现在「干净树缺少工作树专有资产」这类
  **如实降级**上（如无 `.env` ⇒ 凭据面报「无法比对」而不是「通过」）。
- 脚本的每一层都**能被反证**：至少一次「改一处期望值 ⇒ 该层红」的按压（不是只跑一遍绿）。
- m0 全量 **23/23**（独占运行，DSN 固化配方）；治理 `validate.py` 绿。
- 残余：GOAL-008 六项人工面 + GOAL-009 的 W 列表 + 本 GOAL 的 W/残余列表**逐条仍在**。
- 本文件自检：`latest_recheck` 是**仓库相对路径**且指向 PASS/PASS_WITH_WARNINGS；
  `child_plans` / `memory_entries` 与实际一致；`ALL_PLAN` 投影一致。

## 实施清单

- [ ] WP1 **复检脚本** `scratch/verify_goal010_closeout.py`（**只读**、不 import 仓库代码、只用标准库）：
      五层 —— A **EC 交付物**（每个 EC 的承重符号/文件在位）/ B **判据用例**（代表性 nodeid 可收集）/
      C **登记面**（EC 表逐行 PASS、`latest_recheck` 是相对路径且指向 PASS*、`child_plans`/`memory_entries`
      与实况一致、ALL_PLAN 投影一致、残余字样在位）/ D **凭据面**（被跟踪文件命中 **0**、磁盘副本都在
      **已登记集合**内）/ E **默认姿态**（组合根仍注入 Fake runtime、`.env` 无 `RESEARCHOS_AGENT_RUNTIME`、
      workflow 不含 live 凭据、m0 workflow 的预热门在位）。**先写清每层的判定式再跑**。
- [ ] WP2 **按压**：至少三处「改期望/去掉一项 ⇒ 对应层红」的实测（含「脚本不 import 仓库代码」这条
      本身的自证：脚本里出现的字符串不得让被测对象参与判定）。**按压后复原，`git diff` 不留痕**。
- [ ] WP3 **两棵树**：当前树 + 干净 checkout（`git worktree`/`git archive` 到仓外目录，**不**碰主树），
      各跑一次，**核对同结论**；差异逐条解释（不许「差不多」）。
- [ ] WP4 **门禁 + 台账**：全量 m0（独占、DSN 配方）+ 治理 `validate.py` + CI 台账逐 run 到终态。
- [ ] WP5 **收口回写**：`RECHECK-20260922-132`（PASS / PASS_WITH_WARNINGS）→ EC-06 置 PASS →
      `status: ACHIEVED` → `latest_recheck` / `child_plans` / `memory_entries` / 迭代日志 / 状态历史 /
      「终止与收口」写明收口结论与**仍未处理项** → commit/push（单次）/ CI 到终态（台账尾巴口径）。

## 证据

（WP2…WP5 实测后逐条落此节：脚本层结论表、按压表、两树比对表、门禁输出、CI run 明细。）

## 影响报告

- **Domain / Canonical State**：零改动（本 PLAN 只做复检与登记）。
- **安全/凭据**：脚本只读、只输出命中数与相对路径；不打印任何凭据值或片段。
- **CI / 上游**：不新增 workflow、不改 pin；不把凭据写进 CI。
- **回退路径**：本 PLAN 的产出是记录与一个 `scratch/` 脚本（gitignored）⇒ 回退 = 删脚本 + 撤回记录。

## 状态历史

- 2026-09-22 derive：由 GOAL-20260921-010 的 EC-06 派生（`parent_goal` 投影 ALL_PLAN）。
  **只读仓库，未发起任何真实调用**。cycle 5 已收口（EC-05 PASS，`RECHECK-20260922-131` =
  PASS_WITH_WARNINGS；CI 台账含 `87208aa` 的一红与 `cf777fb` 的修复后全绿）⇒ 本 cycle 是**最后一个 EC**。
