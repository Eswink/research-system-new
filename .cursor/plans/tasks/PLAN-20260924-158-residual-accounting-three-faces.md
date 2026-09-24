---
id: PLAN-20260924-158
slug: residual-accounting-three-faces
title: 残余清账（三项分类处置给终态）：Dependabot 23 条 / hook 侧 L3 门 / 450 行贴线文件（GOAL-014 EC-04）
status: DONE
created_at: 2026-09-24
updated_at: 2026-09-24
parent_goal: GOAL-20260924-014
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260924-014 建档授权（2026-09-24 用户 goal 模式指令）的 **EC-04**：
    「**残余清账（可选，视预算）**：对承继的三项残余做**分类处置**并给终态 ——
    ① `R-D1` 的 23 条 Dependabot 告警（4 high / 13 moderate / 6 low）分类；
    ② hook 侧 L3 门；③ 450 行贴线文件。**判据**：每一项有**终态**
    （已处置 / 如实登记为需拍板 / 点名为什么不属于本循环）且依据可核对。
    **诚实边界**：空间不足时如实登记为下一轮输入，**不得**为它**降级** EC-01 / EC-02 / EC-03；
    **不得**为清账而升级依赖 pin（那是 `escalation_triggers`）」。
    **本 PLAN 只做分类与登记，不改任何依赖 pin、不改 hook 面、不改任何源码**；
    证据取「当前实测」而不是引用旧记录：Dependabot 走 GitHub REST API 逐条取数（只读），
    行数走本仓门禁同口径的扫描，L3 门取既有审计记录 + 本 cycle 现场复现的 hook 提示。
    凭据纪律不放松：GitHub 令牌只从 `git credential fill` 读入内存、不打印、不落盘。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260924-160-residual-accounting-three-faces.md
memory_entries:
  - .cursor/memory/entries/MEM-20260918-067-security-audit-residual-recheck.md
---

# PLAN-20260924-158 — 残余清账（三项分类处置给终态）（GOAL-014 EC-04）

## 目标

把承继的三项残余（`R-D1` 告警 / hook 侧 L3 门 / 450 行贴线文件）**按当前实测**分类，
每项给一个**终态**并写明**可核对的依据**；**不**在本循环处置（不升 pin、不动 hook 面、
不动源码），因为它们各自命中「不进入循环 / 需人工拍板」的具体条目。

## 计划开始前的定案（写死）

- **D-1｜证据必须是当前实测**：三项都不引用旧记录的数字，全部现测（API / 扫描 / hook 提示原文）。
- **D-2｜终态只有三种**：**已处置**（须有 commit + 实跑证据）/ **登记为需拍板**
  （须指向「不进入循环」节的具体条目）/ **不属于本循环**（须点名为什么）。
  本 PLAN 预期三项都落在后两种 —— 若某项落在「已处置」，必须有本 cycle 的 commit 为证。
- **D-3｜不得为清账动任何东西**：不升级依赖 pin（`escalation_triggers` + 人工项 5）、
  不改 hook 面（人工项 6）、不为凑数拆分贴线文件（人工项 4：**只分类**）。
- **D-4｜凭据面**：GitHub 令牌只从 `git credential fill` 取，进程内使用，输出只打长度。

## 验收条件

- [x] **AC-1｜分类处置表落 RECHECK**：每项一行 `ID / 类别 / 终态 / 依据 / 证据路径`，
      依据可核对（API 输出的编号与修复版本、门禁同口径的行数、审计记录与 hook 原文）。
- [x] **AC-2｜`R-D1` 现测**：open 告警数、严重度分布、逐条（编号 / 生态 / 包 / 是否已有修复版本）
      落 `scratch/goal014-c4-residual-probe.txt`；**终态 = 登记为需拍板**（修复动作 = 依赖 pin
      升级 ⇒ 人工项 5 + `escalation_triggers`）。
- [x] **AC-3｜hook 侧 L3 门现测**：根因（检测层缺失）取既有审计记录，形态取**本 cycle 现场
      复现**的 hook 提示原文；**终态 = 登记为需拍板**（治理面 = 人工项 6；修法涉及安装检测层
      ⇒ 环境/依赖变更）。
- [x] **AC-4｜450 行贴线现测**：按门禁**同口径**（根 `apps/services/packages/adapters/tests`，
      硬上限 450、软阈值 300、函数 50 行）扫描，给出零余量文件与贴线清单；
      **终态 = 登记为需拍板**（人工项 4：大重构放大 diff 风险，需人工决定；本循环只分类）。
- [x] **AC-5｜不降级**：EC-01 / EC-02 / EC-03 的状态与判据**一字未动**；本 cycle
      **零产品代码 / 零策略面 / 零依赖 pin / 零 hook 面改动**（`git diff --stat` 可核）。

## 实施清单

- [x] **WP1｜三面现测**（`scratch/goal014_c4_residual_probe.py`）：Dependabot（REST，
      `http.client` + 写死主机 + 路径结构校验，避免动态 URL 进服务端请求）、hook 面扫描、
      行数扫描。
- [x] **WP2｜分类判定**：逐项按 D-2 给终态并写依据。
- [x] **WP3｜记录**：分类处置表落 `RECHECK-20260924-160`；本 PLAN 置 `DONE`；
      GOAL 回写（EC-04 `PASS` + 迭代日志 + 台账）。

## 证据

- **Dependabot 现测**（`scratch/goal014-c4-residual-probe.txt` 第 1 节）：**23 条 open** =
  **4 high / 13 medium / 6 low**；生态全部 npm；包分布 **vite 14 / undici 8 / yaml 1**；
  **每一条**都有 `first_patched_version`（high = 6.4.2 / 6.4.3；medium = 6.4.1…6.4.3 /
  6.24.0 / 6.27.0 / 6.28.0 / 2.8.3；low = 6.3.6 / 6.27.0）；
  当前 `apps/web/package.json` 直连 pin 为 `vite 6.3.5` / `yaml 2.8.1`，
  `undici` **不在**任何 `package.json`（只在 `pnpm-lock.yaml` 里 = 传递依赖）。
- **hook 面现测**（同文件第 2 节）：`.cursor/hooks/*.py` **零处** `L3` 字面量 ⇒
  「L3」是**外部分析器（Mimosa）的检测层级**，不是本仓 hook 自己的命名；
  其形态在**本 cycle 现场复现**：本次 `git commit` 与 `git push` 均收到
  `Mimosa 在 git commit/push 前没有得到完整扫描结论（scanner_enobufs）…按兼容策略继续`
  ⇒ **失败开放**（fail-open），与 `docs/audits/MIMOSA_POST_CLOSURE_AUDIT_20260918.md` 的
  根因（`semgrep` 检测层未安装）一致。
- **行数现测**（同文件第 3 节 + 门禁同口径复算）：门禁根内 `.py` **1011 个**；
  **硬上限 450 命中 3 个且都是「正好 450、零余量」**（`services/api/composition.py`、
  `adapters/postgres/workflow_engine.py`、`adapters/execution/docker_backend.py`）；
  **400–449 行 10 个**（`...run_orchestration/service.py` 449、`...live_run_support.py` 448、
  `...phase_runner.py` 448、`services/worker/loop.py` 445、`adapters/sqlite/workflow_ops.py` 430、
  `tests/api/console_api_app.py` 427、`services/api/scheduler.py` 425、
  `tests/distributed/test_scenarios.py` 422、`tests/e2e/test_restart_rebuild_resume.py` 410、
  `services/api/routers/approvals.py` 403）；**软阈值 300–449 共 70 个**。
  另：`tools/PA1R运行演练v1.py` 433 行**不在门禁根内**（门禁只扫
  `apps/services/packages/adapters/tests`），且其文件名含非 ASCII（§13 已登记的豁免面）。

## 状态历史

- 2026-09-24：derive + 执行（GOAL-014 cycle 4）。三项**全部现测**（不引用旧数字）。
  本 cycle **零改动**：不改依赖 pin、不改 hook 面、不动源码，只产出分类处置表与登记。
- 2026-09-24（同日，一次如实登记）：探针初稿用 `urllib.request.urlopen(动态 URL)`，
  被 Mimosa 判 **SSRF 高危并拦截写入** ⇒ 改写为「写死主机常量 + `http.client` +
  路径结构校验（禁 `://` / `..` / `@`）」，既过闸也更贴合本仓的出网纪律。

## 影响报告

- **改动面**：本 PLAN + `RECHECK-20260924-160` + GOAL 回写；**零产品代码 / 零策略面 /
  零依赖 pin / 零 hook 面 / 零判据改动**。
- **Domain/API/schema 变化**：无。
- **安全/凭据变化**：无。GitHub 令牌仅在探针进程内存中（只打印长度）；探针只读。
- **兼容性/迁移风险**：无（未改任何被引用面）。
- **上游版本影响**：**无**（明文不升级 pin —— 那是 EC-04 明确只分类的对象）。
- **下一项任务**：EC-05 收口复检（独立脚本两树同结论 + m0 23/23 + `validate.py` 绿 +
  CI 台账到终态 + 残余逐条登记）。
