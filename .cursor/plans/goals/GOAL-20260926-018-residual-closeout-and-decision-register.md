---
id: GOAL-20260926-018
slug: residual-closeout-and-decision-register
title: 收尾轮：`yaml` patch 升级 + `undici` 前置调研（零升级）+ 13 项 `D-NN` 决案结清
status: ACHIEVED
created_at: 2026-09-26
updated_at: 2026-09-26
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-26 用户会话指令（goal 模式）：**建档 GOAL-20260926-018（收尾轮）并授权本驱动自动化
    循环推进、无需逐轮确认**。authorization 原文要点如下：
    (0) **判词来源**：用户指令 = **「先收尾，然后再甲」**——本轮做**收尾轮**（把 13 项 `D-NN`
    全部结案 + **可做**的依赖升级），**下一轮**再开「甲」（主体模型 + 最小认证面）。
    因此 **本轮不做甲的内容**。来源同时包括 **push-to-main-for-CI 口径**（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**；push 前 `git pull --ff-only origin main`）
    与 **默认姿态不变**（默认 runtime 保持 **Fake**、默认 CI **离线**，AGENTS.md §11）。
    (1) **`yaml` 升级（授权实施）**：`apps/web/package.json` 的 `yaml` 从 `2.8.1` 升到
    **最新 patch**（简报原文：非 high、patch 可升）。授权边界：a) 只升 **`yaml` 一个包**，
    且**只升 patch**；b) 升后必须跑**全量 web 门**（lint / typecheck / unit / build /
    stub e2e / live e2e）+ m0；c) **设计基线漂移 ⇒ 按既有流程强制重生成 + 目检**，
    **不得**调容差；d) **若非 patch（需跨 minor / major）⇒ 不做并如实登记**，不得越界升级；
    e) 不得顺手升任何别的包（`undici` 明文只调研）。
    (2) **`undici` 只做前置调研（授权范围仅限调研，不得升级）**：建模档时已核实的事实——
    `undici@5.29.0` 是**传递依赖**，来源 `@connectrpc/connect-node@1.7.0`（**不在**本仓
    `package.json` 里）；8 条告警全部来自它。调研须回答三问：
    ① 上游 `@connectrpc/connect-node` 是否有带 `undici@6`+ 的版本（若有，升级路径是什么）；
    ② 用 pnpm **overrides** 强制提升传递依赖是否安全（影响面、回归风险、回滚方式）；
    ③ 若不升，8 条告警的**实际可利用性**评估（谁在什么路径下调用 `connect-node`）。
    产出 = 一份**可拍板**的调研结论（写进 `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的 D-03
    小节或独立文档），**零升级动作**；若要升 ⇒ **单独授权**（本 GOAL 不做）。
    授权边界：**不得**改 `pnpm-lock.yaml` 的 `undici` 分辨率、**不得**新增 `pnpm` 字段
    （`overrides` / `resolutions` / `packageExtensions` 一律不得写入仓库）、**不得**为了调研
    而在树内安装任何包。反证取证：`git diff -- pnpm-lock.yaml` 里 `undici@5.29.0` 一字不动。
    (3) **D-06 → 取 (c) 维持（授权登记）**：「路径 (B)」维持「**已否证 / 待重新设计**」**原状**，
    **不重启、不改记录状态词**；把它从「未拍板」改为「**已拍板为维持现状**」。
    (4) **D-05 → 取 (b) 维持（授权登记）**：450 行贴线文件维持「**触线即拆**」；
    **本 GOAL 不专项拆分**。交付 = 把该决定**固化**（写进 `OPEN_DECISIONS_BRIEFING.md` 的
    D-05 或 ADR 引用面），使**下轮不再重复提问**。
    (5) **D-04 → 本 GOAL 拍板为取 (c) 维持现状（授权登记，理由随判词落记录）**：
    简报**建议 (a) 但明确要求先修误报面**；本仓的**已知误报**（正则字面量 / `f-string` SQL /
    URL 形状 / 大文件写盘被拒）**仍在发生**，在误报面未修的情况下安装**阻塞型**检测层会让
    **每轮提交被噪声拦住** ⇒ **本轮维持现状**，并把「**先修误报面**」作为**重启 D-04 的前置
    条件**登记。授权边界：**不安装检测层、不改 hook 面、不改 `MIMOSA_GIT_GATE_MODE`**。
    (6) **明确不授权（本 GOAL 一律不做，命中即 BLOCKED）**：
    a) **`undici` 升级**（含 pnpm `overrides` 强制提升）——**只调研不实施**；
    b) **D-04（hook 侧 L3 检测层）**——本 GOAL 取 (c) **维持现状**（见 (5)），
    **不安装检测层、不改 hook 面、不改 `MIMOSA_GIT_GATE_MODE`**；
    c) **甲的全部内容**（主体模型 / 认证面 / 请求主体归因 / 任何鉴权语义改动）——**留给下一轮**；
    本 GOAL **不得**新增任何**鉴权 / 中间件 / 路由保护**改动（取证：`git diff` 中
    `services/api/middleware.py` 与路由层**零改动**）；
    d) **D-01(a)**（组合根接执行体缝）/ **D-02(a)**（读类成类放行）/
    **D-12(a)**（BOLA / BFLA 专项测试）——均**未授权**（本 GOAL 不取 (a) 面）；
    e) **`ADR-0031` 的 `Status`**——仍 `Proposed`，**不得**改；
    f) **`yaml` 的跨 minor / 跨 major 升级**——授权仅限 **patch**，跨 minor 即 BLOCKED。
    (7) **不做真实出网**：本 GOAL **不需要** `.env` 凭据；`pnpm` 网络**仅**用于依赖升级与
    上游元数据调研。若确需校验 URL，仅允许 http/https 且**发请求前校验 host**并拒绝
    localhost / 环回 / 私有 / 保留地址（**复用** `endpoint_policy`，不另写判据）；
    SQL 一律**参数绑定**；凭据**只从环境变量**读取；Domain **不得**出现厂商名；
    观测隐私**不记录完整 Prompt**（§10）。默认门一律**离线**
    （`tests/egress_guard.py` 是**结构判据**，不得为本地变绿而放宽）。
    (8) **边界**：GOAL-001…017 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    如需指名只允许按**只追加**补一行事实更正。GOAL-017 的承继残余**原样保留**（本 GOAL 只把
    本轮获授权的两项依赖动作与三条登记落地，其余继续挂着）。
    (9) **下一轮输入 = 甲（主体模型 + 最小认证面，需用户另行授权）**——本 GOAL **不做**。
objective: >
    把 GOAL-017 遗留的**收尾面**一次做完，使 `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的
    13 项 `D-NN` **全部结案、零「待定」**：(1) **`yaml` patch 升级**：`apps/web` 的
    `yaml` `2.8.1 → 最新 patch`（实测：首个修复版本 = **`2.8.3`**，而 `2.8.x` 的**最新 patch
    = `2.8.4`** ⇒ 落地目标 = **`2.8.4`**；对应
    `GHSA-48c2-rrv3-qjmp` / `CVE-2026-33532`，severity = **medium**、修复在 **2.8.x 内**），
    升后**全量 web 门 + m0 + CI 八 job** 全绿；**设计基线漂移 ⇒ 强制重生成 + 目检**
    （**不得**调容差）；(2) **`undici` 前置调研（零升级）**：产出一份**可拍板**结论，
    回答「上游是否有带 `undici@6`+ 的版本 / pnpm `overrides` 是否安全 / 8 条告警的
    实际可利用性」三问，并**逐条给出依据**；**反证**：`pnpm-lock.yaml` 的 `undici@5.29.0`
    **未被改动**；(3) **13 项 `D-NN` 决案结清**：每条给**唯一终态**（已实施 / 部分实施 /
    已拍板为维持现状 / 未授权待拍板），D-05 / D-06 **已拍板为维持现状**、D-04 **拍板为 (c)
    维持 + 重启前置 = 先修误报面**；判据 = 简报对齐面与 GOAL 人工面**双向一致**且**可被按压**；
    (4) **收口复检 + 残余登记**：两棵树同结论的独立复检脚本 + **as-is 本机 m0 = 23/23** +
    治理 `validate.py` 绿 + CI 台账到终态（M0 **八 job** + CodeQL，含 `run_attempt`）+
    承继残余逐条在位。
    **硬约束**：**不放宽 / 削弱任何判据、门禁、放行面或阈值**；**零**策略面 allow 新增；
    **零**鉴权 / 中间件 / 路由保护改动（甲留给下一轮）；不改 `ADR-0031` 的 `Status`；
    不碰 Canonical State 边界；默认 runtime 仍为 **Fake**、默认 CI 仍**离线**；
    **`undici` 一字不升**（含 `overrides`）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **`yaml` patch 升级**：`apps/web/package.json` 的 `yaml` 从 `2.8.1` 升到**最新 patch**。
      **建档当日实测**：`2.8.x` 的可用版本 = `2.8.0/2.8.1/2.8.2/2.8.3/2.8.4` ⇒ **最新 patch = `2.8.4`**；
      告警的首个修复版本是 `2.8.3` ⇒ 目标 `2.8.4` **既是最新 patch 又 ≥ 修复版本**（仍属 `2.8.x`，
      不需要跨 minor）。
      交付 = ①`apps/web/package.json` 与 `pnpm-lock.yaml` 两处的版本变化；②**全量 web 门**
      （lint / typecheck / unit / build / stub e2e / live e2e）全绿；③**m0 全绿**；
      ④**CI 八 job 全绿** + CodeQL；⑤**设计基线**：无漂移；**若漂移 ⇒ 强制重生成 + 目检**，
      **不得**调容差。**若非 patch（需跨 minor / major）⇒ 不做并如实登记**（本项不强制升级）。
    verify: >-
      ① `git diff` 逐行证明只有 `yaml` 一处 specifier 变化（`2.8.1 → 2.8.4`）+
      `pnpm-lock.yaml` 的 `yaml@2.8.1` 解析项变为 `yaml@2.8.4`（**其余包零变化**——
      `git diff --stat` 与逐 hunk 复核，**不得**出现第二个包的版本变化）；
      ② 逐条实跑：`pnpm --dir apps/web lint` / `typecheck` / `test` / `build` /
      `test:e2e` / `test:e2e:live`（**live e2e 在本 GOAL 的口径下是「默认离线 ⇒ 如实 skip」**，
      以 `RESEARCHOS_LIVE_E2E` 未开为判据，**不引入凭据**）；另跑根门
      `pnpm run check`（format:check + lint + typecheck + boundaries + test）；
      ③ `make validate-all`（独占、仓库 `.venv`、`--keep-going`）到
      `PASS: profile=m0; 23 deterministic checks`；
      ④ CI 台账：本 cycle 推送提交的 M0 run **八 job 全 success** + CodeQL 3/3（记 `run_attempt`）；
      ⑤ 设计基线判据（`apps/web/tests/e2e/design-outline-guard.spec.ts`）绿；
      **若判红** ⇒ 按既有配方 `UPDATE_OUTLINES=1` 重生成 + win32 单路由像素 + Linux 侧
      `verify_linux_outlines` 复验 + 目检，并**逐字节证明容差未动**。
    status: PASS
  - id: EC-02
    criterion: >-
      **`undici` 前置调研（零升级）**：产出一份**可拍板**结论，三问各有答案与依据：
      ① 上游 `@connectrpc/connect-node` **是否有**带 `undici@6`+ 的版本（若有 ⇒ 升级路径；
      若无 ⇒ 依据）；② 用 pnpm **overrides** 强制提升传递依赖**是否安全**（影响面 / 回归风险 /
      回滚方式）；③ 若不升，**8 条告警的实际可利用性**（谁在什么路径下调用 `connect-node`）
      评估。交付物 = 结论文档在位（简报 D-03 小节或独立文档）。
      **反证（成对）**：全文搜索 + `git diff` 确认 `pnpm-lock.yaml` 的 `undici@5.29.0`
      **未被改动**、**未新增**任何 `pnpm.overrides` / `resolutions`。
    verify: >-
      ① 结论文档在位且三问各有「答案 + 依据（可复核的命令或上游元数据）」；
      ② `git diff -- pnpm-lock.yaml` 中 `undici@5.29.0` 与 `'@connectrpc/connect-node@1.7.0'`
      快照**逐字节未变**（本 GOAL 的 `pnpm-lock.yaml` 唯一允许的变化是 EC-01 的 `yaml`）；
      ③ `git diff -- package.json` 中**不得**出现 `pnpm` / `overrides` / `resolutions` 字段；
      ④ 结论必须**可拍板**：给出「可升 / 不可升」的明确判词 + 若可升的**前置条件**与
      **归属方**（若升级面在本仓之外 ⇒ 点名归属方）。**零升级动作**取证如上。
    status: PASS
  - id: EC-03
    criterion: >-
      **13 项 `D-NN` 决案结清**：把 13 项逐条给**唯一终态**（只能取
      「已实施 / 部分实施 / 已拍板为维持现状 / 未授权待拍板」四值之一），每项附依据；
      **D-05(b)** 与 **D-06(c)** 从「未拍板」改为「**已拍板为维持现状**」；
      **D-04** 从「未拍板」改为「**本 GOAL 拍板为 (c) 维持**，重启前置 = **先修误报面**」。
      判据 = `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的对齐面与 GOAL 的
      「不进入循环 / 需人工拍板」节**双向一致**（每项都能互相指认）+ **机械判据**
      （既有 `tests/tooling/test_pending_decisions_briefing.py` 覆盖此面 ⇒ **按它的口径同步**）。
      **新增判据必须可被按压**：删一项 / 空白字段 / 改终态为模糊表述 / 去掉对齐行 ⇒ **判红**。
    verify: >-
      ① 简报侧：13 行**终态表**（`D-01…D-13` 各一行，终态取自四值词汇表、依据非空）
      + 对齐面每行的状态列**非空**且与终态表**一致**；
      ② GOAL 侧：「不进入循环 / 需人工拍板」节的 **13 条编号项**逐条点名其 `D-NN` **与终态**，
      与简报**同词**；
      ③ 机械判据：`tests/tooling/test_pending_decisions_briefing.py`（扩展后）绿；
      ④ **反证（成对，逐条留档）**：删掉终态表任一行 ⇒ 红；把某格终态置空 ⇒ 红；
      把某格改成词汇表外的模糊表述（如「待定」）⇒ 红；把 GOAL 侧某条的终态改成与简报
      **不一致** ⇒ 红；把对齐行删掉 ⇒ 红；**逐字节复原** ⇒ 绿。
      ⑤ 汇总判词：`已实施 + 部分实施 + 已拍板为维持现状 = 13`，**零「未授权待拍板」**。
    status: PASS
  - id: EC-04
    criterion: >-
      **收口复检 + 残余登记**：① **独立复检脚本**（不复用本 GOAL 的叙述）在**当前树**与
      **干净 checkout** 两路给出**同一结论**，且**非恒真**（按压必须判红）；
      ② **as-is 本机 m0 到 23/23**（GOAL-017 起 `R-3` 已消除 ⇒ 应能**直接**给出；
      若不能 ⇒ **如实说明哪种跑法与哪条拦着**，不得含糊）；③ 治理
      `.cursor/skills/governance-check/scripts/validate.py` **绿**；④ **CI 台账到终态**
      （M0 **八 job** + CodeQL，含 `run_attempt`）；⑤ 承继残余**逐条在位**：
      `R-M1` / `R-D1`（更新为「`yaml` 已升、`undici` 已调研未升」）/ `R-B1` / `R-N1` /
      `R-F1` / `R-F2` / `W-4` / `W-5` / `W-6`。
    verify: >-
      ① 复检脚本两路输出留档（`scratch/`）且**判词列逐行相同**；整份输出差异只允许出现在
      「本 GOAL 自身的 EC 状态文字」上（干净 checkout 停在更早的提交）；
      ② `make validate-all`（独占、仓库 `.venv`、`--keep-going`）终态行
      `PASS: profile=m0; 23 deterministic checks`，日志留档；
      ③ `validate.py` 输出 `Cursor 治理验证通过`（含 `DOCS-CHECK`）；
      ④ 台账逐 run 逐 job 记录（含 `run_attempt`；flake 判定**必须**靠**同一代码的复跑对照**）；
      ⑤ 残余清单在 GOAL 内**逐条**出现且措辞与判词一致。
    status: PASS
budget:
  max_cycles: 20
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator / 门禁 / 快照 / 测试断言使其通过
    - 放宽被扫内容的任何检查项（`validate_bundle` 的链接存在性 / 版本号 / schema / 引用一致性）
    - 放宽 `tests/egress_guard.py` 的目的地判定 / 放行面 / 豁免 fake-IP（`198.18.0.0/15`）
    - 放宽 m0 任一 check 的阈值（含 450 行 / 50 行规模门禁；含 RSS 与线程阈值）
    - 改 `tests/observability/test_telemetry_overhead.py` 的阈值 / 测量语义 / 断言行
    - 改 `tests/application/test_m2_audit.py` 的镜像一致性判据使其通过
    - 让 CI 作业失败不再传播为整体判红（`continue-on-error` / `if: always()` 吞失败）
    - skip / 删除测试、加 xfail、或调整收集顺序以掩盖顺序依赖
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 新增任何策略面 allow 或类别级规则（D-02 明文不取 (a)）
    - 改 `ADR-0031` 的 `Status`（D-07 明文维持 `Proposed`）
    - 改 `ModelCompatibilityProfile` 的 Domain 面 / Canonical State 边界
    - >-
      动 `undici` 的 pin，或写 pnpm `overrides` / `resolutions` / `packageExtensions`
      （明文**只调研不实施**）
    - >-
      把 `yaml` 升到**跨 minor / major**，或顺手升任何别的包（授权仅限 `yaml` 的 patch）
    - 新增任何**鉴权 / 中间件 / 路由保护**改动（甲的内容，留给下一轮）
    - 安装 hook 检测层 / 改 `.cursor/hooks/` 的阻塞面 / 改 `MIMOSA_GIT_GATE_MODE`
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 同一失败签名超过 fix_policy 上限
  - >-
    **动 `undici`（含 pnpm overrides / resolutions）** —— **立即 BLOCKED**（明文只调研不实施）
  - >-
    **安装 hook 检测层**、改 `.cursor/hooks/` 面、或改 `MIMOSA_GIT_GATE_MODE` ——
    **立即 BLOCKED**（D-04 本 GOAL 取 (c) 维持）
  - >-
    **任何鉴权 / 中间件 / 路由保护改动**（甲的内容：主体模型 / 认证面 / 请求主体归因）——
    **立即 BLOCKED**
  - >-
    **改门禁 / 阈值 / 作业结构**（`validate_bundle` 检查项、m0 任一 check、
    `.github/workflows/**` 的 job 结构、`test_m2_audit.py` 镜像判据）—— **立即 BLOCKED**
  - >-
    **放宽任一判据 / 放行面 / 阈值**（含 `tests/egress_guard.py` 目的地判定与放行面、
    450 行 / 50 行规模门禁、RSS 与线程阈值）—— **立即 BLOCKED**
  - >-
    **放宽 §9 默认 deny**，或新增任何策略面 allow / 类别级规则 —— **立即 BLOCKED**
  - >-
    `yaml` 需要**跨 minor** 才能修（授权只到 patch）—— **不做并如实登记**；
    擅自跨 minor ⇒ **立即 BLOCKED**
  - Canonical State 边界 —— **立即 BLOCKED**
  - 把真实 runtime 设为**默认**（默认必须仍是 Fake）—— **立即 BLOCKED**
  - 改 `ADR-0031` 的 `Status`（D-07 明文维持 `Proposed`）—— **立即 BLOCKED**
  - >-
    默认门出现**非环回**出站（`tests/egress_guard.py` 判红整轮）—— 先归因再处置；
    若是本 GOAL 引入的 ⇒ 修复方向是**恢复离线**，**不得**放宽放行面
  - 明文凭据泄露（**即使是可弃用的免费额度**）—— 立即停止并报告
child_plans:
  - .cursor/plans/tasks/PLAN-20260926-186-yaml-patch-upgrade-and-undici-research.md
  - .cursor/plans/tasks/PLAN-20260926-188-goal-018-closeout-recheck.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260926-189-goal-018-closeout-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260926-142-patch-means-latest-patch-and-a-research-needs-a-verdict.md
---

## 目标与退出标准

**一句话**：把 GOAL-017 遗留的**收尾面**一次做完——**`yaml` patch 升级**（唯一授权的依赖变更）、
**`undici` 前置调研**（**零升级**，只出结论）、**13 项 `D-NN` 决案结清**（零「待定」）、
**收口复检 + 残余登记**——并且 **`undici` 一字不升、鉴权 / 中间件零改动**（甲留给下一轮）。

| EC | 标准（简） | 主要交付物 | 状态 |
| --- | --- | --- | --- |
| EC-01 | **`yaml` `2.8.1 → 2.8.4`**（最新 patch）+ 全量 web 门 + m0 + CI 八 job 全绿 | 两处版本变化 + 六道 web 门证据 + m0 终态行 + 基线判据 | **PASS** |
| EC-02 | **`undici` 前置调研**（三问各有答案与依据），**零升级** | 结论文档 + `undici@5.29.0` 未改动反证 | **PASS** |
| EC-03 | **13 项 `D-NN` 唯一终态**（四值词汇表）| 简报终态表 + GOAL 人工面 13 条 + 可按压判据 + 反证 | **PASS** |
| EC-04 | 收口复检 + 残余登记 | 两树复检脚本 + as-is m0 **23/23** + CI 台账 + 残余逐条 | **PASS** |

**收口判词（EC-04 要求的三问，逐条给出）**：

1. **as-is 本机 m0 的终态行** = **`PASS: profile=m0; 23 deterministic checks`**
   （`PASS [` = 24、`FAILED`/`ERROR` 零命中、退出码 0；**不再需要任何代管跑法**；
   日志 `scratch/goal018-c2-m0-as-is.log`）。跑法 = canonical：`uv run --frozen --no-sync python -B
   .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going`
   （= `make validate-all` 的展开；本机 `make` 不在 PATH ⇒ 逐字用展开式），独占 + DSN 固化。
2. **`undici` 调研结论** = **不可在本仓正确升级**（1.x 全线 `undici ^5`、2.x 起不再依赖 undici
   但为**破坏性主版本**、`@cursor/sdk` 最新版仍锁 `^1.6.1` ⇒ 归属方在上游）⇒ **维持现状并登记**；
   **零升级动作**已由两条反证 + 外部告警面（剩余 8 条**全是** undici）钉住。
3. **EC-01 是否真的只升了 patch** = **是**：`2.8.1 → 2.8.4` 同属 `2.8.x`；
   `git diff --name-only` 的依赖面**恰为** `apps/web/package.json` + `pnpm-lock.yaml`
   两个文件，且 lockfile 里**只有** `yaml` 一个包的解析项变化；设计基线**逐字节未改**。

**依赖关系**：EC-01 / EC-02 / EC-03 **互相独立**（一个依赖 pin / 一份调研文档 / 一张决策面），
三者的**判据都不依赖**另外两项；EC-04 **最后**做，且**必须**在 EC-01 落地后重跑 m0
（because EC-01 改变 `pnpm-lock.yaml` 与 `apps/web/package.json`）。

**建档当日已核实的文件层事实（决定可行性与判据形态；全部实测，非推测）**：

1. **`yaml` 的授权面与修复版本**（实测 `registry.npmjs.org` + Dependabot REST）：
   - 现状 `apps/web/package.json` `devDependencies.yaml = "2.8.1"`；`pnpm-lock.yaml`
     有 `yaml@2.8.1`（入边来自 `apps/web` 以及 `vite` 的 peer 后缀 `vite@6.4.3(...)(yaml@2.8.1)`）。
   - 告警：`GHSA-48c2-rrv3-qjmp` / `CVE-2026-33532`（`yaml` **Stack Overflow via deeply nested
     YAML collections**），severity = **medium**，`first_patched_version = 2.8.3`；
     而 `2.8.x` 的**最新 patch = `2.8.4`**（实测版本表 `2.8.0/2.8.1/2.8.2/2.8.3/2.8.4`）
     ⇒ **修复在 `2.8.x` 内 ⇒ patch 升级**，落地目标 = **`2.8.4`**（`2.8.1 → 2.8.4`）。
   - 该告警**不是 high**（与简报「D-03：非 high、patch 可升」一致）。
2. **Dependabot 的权威告警计数（实测，`/dependabot/alerts?state=open`，2026-09-26）= 9 条**：
   `undici` **8 条**（6 medium + 2 low）+ `yaml` **1 条**（medium）。
   ⇒ 与本 GOAL 建模档的「`undici` 8 条」一致；`vite` 的 4 条 high 已由 GOAL-016 EC-03 清掉。
   留档：`scratch/goal018-gh-alerts.json`。
3. **`undici@5.29.0` 的真实归属（实测，这是 D-03 剩余面的关键事实）**：
   - 依赖链 = **`@cursor/sdk@1.0.30`（根 `devDependencies`，`package.json:28`）→
     `@connectrpc/connect-node@1.7.0` → `undici@5.29.0`**；
   - `pnpm-lock.yaml` 中 `undici@5.29.0` 的入边**只有一条**：
     `'@connectrpc/connect-node@1.7.0(...)'` 的 `dependencies.undici: 5.29.0`
     ⇒ **影响面 = 1 个包**（不是「到处都是」）；
   - `@cursor/sdk` 在**全仓**的导入点**只有一处**：
     `.cursor/skills/parallel-agent-orchestration/scripts/sdk-adapter.ts`
     （其自述「The only module in the repository allowed to import `@cursor/sdk`」）；
   - 本仓**没有任何**直接 `import "undici"` / `import "@connectrpc/*"` 的代码。
4. **`connect-node` 里 undici 的唯一用法（实测 `node_modules`）**：
   `dist/esm/index.js` 只为一个**副作用导入** `./node-headers-polyfill.js`，而该模块**唯一**的
   undici 引用是 `import { Headers as HeadersPolyfill } from "undici"`，且赋值有**代际守卫**：
   `if (major < 18) { if (typeof globalThis.Headers === "undefined") globalThis.Headers = HeadersPolyfill; }`
   ⇒ 本机 `.node-version = 22.18.0`（CI 亦用 `node-version-file: .node-version`）下该分支**不可达**。
5. **上游是否有带 `undici@6`+ 的版本（实测 npm 元数据，回答 EC-02 问题①）**：
   `@connectrpc/connect-node` **1.x 全线**（`0.13.2` … `1.7.0`，最后发布 2025-09-08）都声明
   `undici: ^5.x`；**没有任何 1.x 版本**带 `undici@6`+。**2.x 起 `dependencies` 为空**
   （`2.0.0-beta.1` 之后即**不再依赖 undici**）。但 2.x 是**破坏性主版本**：
   `peerDependencies` = `@bufbuild/protobuf ^2.2.0`（2.2.0 起）/ `@connectrpc/connect 2.x`，
   且 `engines.node` 提到 `>=18.14.1` / `>=22`；本树现锁 `protobuf 1.10.0` + `connect 1.7.0`。
   而 `@cursor/sdk` **最新版 `1.0.32`（2026-09-22）仍声明 `@connectrpc/connect-node: ^1.6.1`**
   ⇒ **升级 `@cursor/sdk` 并不能去掉 undici**。⇒ 结论方向：**升级面在 `@cursor/sdk` 的
   上游（Cursor），不在本仓**（EC-02 需把这一点写成可拍板结论）。
6. **`undici` 各主版本的 `Headers` 公开导出（实测，用于评估 overrides 可行性）**：
   `require('undici').Headers` 在 `5.29.0` / `6.29.0` / `7.30.0` / `8.11.2` **都在**
   （`undici@6` 调整了内部路径 `lib/fetch/headers` → `lib/web/fetch/headers`，但**公开导出名未变**）
   ⇒ 若将来授权 overrides，**唯一的实际用点不会因 5→6 而消失**；但**越界**（`^5.28.4` 之外）
   ⇒ 本 GOAL **不实施**，只归档以支撑 EC-02 的结论。
7. **13 项 `D-NN` 的终态口径**：简报的 **对齐表** 只覆盖 GOAL-015 的 13 条编号项 + 6 条
   特有 / 残余行（`特-1…特-5` / `残-1`），**没有** 13 行 `D-NN` 终态表；
   既有机械判据 `tests/tooling/test_pending_decisions_briefing.py` 的**引用收集规则**是
   「**状态列含 `待拍板`** 的行才把 `D-NN` 计入 `referenced`」⇒ **一旦把某行改成「已拍板」，
   该 `D-NN` 会立刻被判定为「孤儿」而判红**——这正是 EC-03 必须**同步判据口径**的原因
   （口径改动方向必须是**更强**：引用收集与状态解耦 + 新增终态词汇表 + 覆盖面扩到本 GOAL）。
8. **承继起点（事实，不是待办）**：GOAL-017 的 13 项 `D-NN` 终态表 + 承继残余
   （`R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` / `W-1…W-7`）**原样保留**；
   本 GOAL 只把**本轮获授权的两项依赖动作 + 三条登记**从「未实施 / 未拍板」改为终态。
   `R-F3` 已由 GOAL-017 EC-01 收口（`R-3` 消失）。
9. **工作树有并发写者**的未提交条目（`apps/web/src/features/models/ModelDetails.tsx`、
   `packages/domain/model_drift.py`、`services/api/dto/models.py`，建档实测**内容 diff 为空**、
   仅行尾差异）⇒ **不碰、不提交**这三处；只按显式路径提交本 GOAL 自己的产物。
10. **规模门禁的零余量文件**（`tests/tooling/test_python_source_limits.py`，450 行）：
    `services/api/composition.py` / `adapters/postgres/workflow_engine.py` /
    `adapters/execution/docker_backend.py` / `packages/application/run_orchestration/service.py`
    **四个正好 450 行**（零余量）⇒ 本 GOAL 若需改它们，**必须先搬代码**；
    `tests/e2e/live_run_support.py` 只剩 **1 行**余量（`W-6`）。
    **本 GOAL 的授权动作不要求改任何一个上述文件**。

**预算**：`max_cycles: 20`、`per_cycle_minutes: 120`（软）、`no_progress_stop_cycles: 2`。
**本 GOAL 默认门一律离线**（不需要 `.env` 凭据；`pnpm` 网络仅用于依赖升级与上游元数据调研）。

## 循环入口协议

驱动方（会话 / 定时自动化 / 客户端 goal 模式）进入时，按**迭代日志最后一行** +
**工作树 / 远端实况**判定续点；**禁止凭记忆假设上一轮状态**：

1. 最后一 cycle 无记录 → 开 cycle 1：执行 ①（先 derive 子 PLAN）。
2. 有子 PLAN 但仍在 `IN_PROGRESS` → 继续该 PLAN 的执行（②）。
3. 本地验证已过、有未推送 commit → 执行 ④⑤（push + CI）。
4. CI 在跑或未记录结论 → 执行 ⑤（等待 / 判定），**禁止猜测绿**。
5. CI 有失败且修复次数未达上限 → 执行 ⑥（纠错）。
6. 最后一 cycle 的 commit + CI 全绿且 EC 未满足 → 执行 ①（生成下一子 PLAN）。
7. 判定条件按「终止与收口」：ACHIEVED / BLOCKED / 超预算。

任何一步完成后**立即回写本文件**（状态历史 / 迭代日志），保证任意时刻崩溃后重入可续。
同时只允许一个驱动持有 ACTIVE cycle 的推进权；**另一驱动持有未收口 ACTIVE cycle 时等待**。

**每轮只读入口必需的最小集**（`per_cycle_minutes=120` 是硬预算）：本文件 + 当前子 PLAN +
其引用的判据 / 证据；不整目录通读。

**幂等建档**：`glob .cursor/plans/goals/GOAL-*-018-*.md` 已存在 ⇒ 跳过建档，直接进循环。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；
  写子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 带 `parent_goal: GOAL-20260926-018`
  并投影 `ALL_PLAN`，**同一提交**）。子 PLAN 编号续**全局 NNN**（建档当日实测：
  `.cursor/plans/tasks/` 最大 = `PLAN-20260925-184`、`.cursor/plans/rechecks/` 最大 =
  `RECHECK-20260925-185` ⇒ 下一个 PLAN / RECHECK 从 **186** 起；`MEM` 下一个 = **142**）。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**显式路径**）。
- **③ 本地验证**：先自查**规模门禁**（50 行函数 / 450 行文件；覆盖面 =
  `apps` / `services` / `packages` / `adapters` / `tests`；**四个文件正好 450 行零余量**，
  见「目标与退出标准」第 10 条）与**快照类门禁**（OpenAPI / **设计基线**），再跑
  `make validate-all`（m0 全量 23 项，**独占运行**，**用仓库 `.venv`**，
  避免 `evolution_state.json` 的 `WinError 5` 与假红）+ 受影响定向套件 + **web 门**
  （`pnpm --dir apps/web` 的 lint / typecheck / test / build / test:e2e / test:e2e:live
  + 根 `pnpm run check`）。
  **默认门一律离线**（`tests/egress_guard.py` 是结构判据——**不得**为本地变绿而放宽它）；
  **本地不绿不得 push**（承 `MEM-20260924-125`）。
  **写记录时不要跑 m0**（承 `W-5`：m0 运行中改工作树会让 `framework/validate` 判红）。
  **`CURSOR_FRAMEWORK_ROOT` 的作用域**：它重定向**整个 m0 runner**（不是单个 check）
  ⇒ 用它做定向复验时，注意别把「根」指偏而让别的 check 看到别的树。
  **Linux 侧复验**：`...` 形式链接在 Win32 会**剥尾点** ⇒ 涉及路径 / 链接的判据必须在
  **Linux 侧**（CI 的 `quality-ubuntu-latest`）复验；本机绿不等于跨平台绿。
- **④ commit**：显式路径；**绝不 `git add -A`**（并发工作树）。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（只推 main）→
  轮询 CI 到终态（`scratch/poll_ci_all.sh <sha>`：M0 **八 job** + CodeQL），记录 run id /
  链接 / 逐 job 结论 / **`run_attempt`**（**flake 判定必须靠同一代码的复跑对照**，
  不得只看一次结论）；**本机无法验证记 PENDING 并停止推进**。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；超 `fix_policy` 或命中 `escalation_triggers`
  ⇒ `status: BLOCKED`。
- **⑦ 回写**：EC / 迭代日志 / `child_plans` / `latest_recheck` / 状态历史；
  **收尾前必须回写**；`child_plans` 与 `memory_entries` 每轮与实际派生对齐。
  **记录自洽**：新增 MEM / RECHECK 引用时确保被引用文件在**同一提交**内。
  **CI 台账沿用既有闭合约定**：写下本条的那个提交自身的 run 只在**回合汇报**记账。

**撤回纪律**（承 GOAL-011…017）：改共享夹具 / 契约 / 依赖时先数清谁拿它的
**失败形态**当夹具 —— **本 GOAL 有两处高危面**：① EC-01 改的是**依赖 pin**
（`yaml` 被 `vite` 的 peer 后缀引用、被 web 构建链消费 ⇒ 可能影响**设计基线**渲染）；
② EC-03 改的是**简报的结构**，而 `tests/tooling/test_pending_decisions_briefing.py`
以文本变体做**非恒真**断言（改结构即可能同时打到该判据的按压用例口径）。
CI 判红且根因是夹具语义冲突 ⇒ **优先撤回载体改动**；撤回复核用**逐字节 `git diff`** 证明。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；修产品优先，**禁改断言迁就** |
| **设计基线漂移**（EC-01 主场） | `design-outline-guard` 判红 / 结构签名不一致 | **按既有配方重生成**（`UPDATE_OUTLINES=1` + win32 单路由像素 + Linux 侧 `verify_linux_outlines`）+ **目检**；**不得**调容差 |
| **`yaml` 语义变化**（EC-01 主场） | web 构建 / vite 配置解析 / e2e 启动失败 | 判「是否 `2.8.1→2.8.4` 引入」：是 ⇒ 复核是否**只升 patch**（若非 patch ⇒ 撤回并如实登记）；否 ⇒ 真红，修产品或夹具 |
| **判据结构变化**（EC-03 主场） | `tests/tooling/test_pending_decisions_briefing.py` 判红 | 判「是本 GOAL 要改的**口径**还是既有断言」：是口径 ⇒ 使改动**更强**并补按压；是既有断言 ⇒ **不得**为迁就而放宽，回头改简报 |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境、`W-7` live 上游瞬时） | 按 `docs/architecture/LOCAL_GATE_PROTOCOL.md` 归因；**资源阈值型**判红 ⇒ **(ii) 类 + 复跑对照**，**判据与阈值一字不动** |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | Mimosa/validator 命中新增项 | 按各处置文档修或登记误报；**不得绕过**；**不得宣称安全** |

**固定口径**：CI 台账逐条记录每个推送提交触发的 run 到终态；写下某条记录的那个提交自身
的 run 只在回合汇报记账、**不再回写文件**。

## 终止与收口

- **ACHIEVED**：EC-01…EC-04 **全部 PASS** 且有**实跑证据** + 独立 RECHECK
  `PASS` / `PASS_WITH_WARNINGS` + 本文件收口（`latest_recheck` 为**仓库相对路径**）
  + CI 台账到终态 + **13 项 `D-NN` 全部有唯一终态、零「待定」**。
  **未实跑不得记 PASS**；本机无法验证记 PENDING 并停止推进。
- **BLOCKED**：命中任一 `escalation_triggers`（尤其**动 `undici`（含 overrides）**、
  **安装 hook 检测层**、**任何鉴权 / 中间件 / 路由保护改动**、**改门禁 / 阈值 / 作业结构超出
  授权**、**放宽 §9 默认 deny**、**`yaml` 被迫跨 minor**、**Canonical State 边界**、
  **把真实 runtime 设为默认**、改 `ADR-0031` 的 `Status`）、同一失败签名超过 `fix_policy`
  上限、`max_cycles` 触顶、或连续 `no_progress_stop_cycles` 个 cycle 未推进任何 EC
  ⇒ `status: BLOCKED`，**留人工决策**，逐条写明卡在哪、需要拍板什么。
- **ABORTED**：用户撤销目标或授权。
- 收口动作：① RECHECK 定稿；② 本文件 EC 置终态 + 状态历史追加 + 迭代日志补全；
  ③ `child_plans` / `memory_entries` 对齐；④ 残余逐条登记（含 13 项 `D-NN` 终态表）；
  ⑤ CI 台账终态；⑥ `validate.py` 绿。
- **本 GOAL 的收口判词必须写明**：**as-is 本机 m0 的终态行**（应为 **23/23**；
  若未达 ⇒ 如实登记**是哪一条**拦着、**哪种跑法**）、**`undici` 调研结论**
  （可升 / 不可升 + 依据）、**13 项 `D-NN` 终态表（零「待定」）**、
  以及 **EC-01 是否真的只升了 patch**。

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 BLOCKED。
**本节照抄 GOAL-017 的 13 条 + 其特有项 + 承继残余**，并在每条注明**本 GOAL 的决案结果**
（用户 2026-09-26 判词「先收尾，然后再甲」）。

**GOAL-016 / 017 的 13 条编号项（原样承继 + 本 GOAL 决案结果）**：

1. **ADR-0031（`tool_pack.*` 能力策略，`Status: Proposed`）是否采纳**——**已拍板：D-07 取 (b)**
   ⇒ 维持 `Proposed` + 已有「否证条件」节（GOAL-016 EC-04 已实施）；
   **本 GOAL 不动它的 `Status`**。⇒ **D-07 终态 = 已实施**。
2. **威胁建模 / 授权面覆盖（BOLA / BFLA）**——**已拍板：D-12 取 (b)** ⇒ 文档级草案已在位
   （GOAL-016 EC-05 已实施）；**本 GOAL 不做 (a)**（专项测试与门）。
   ⇒ **D-12 终态 = 已实施**（面 (a) 未授权）。
3. **`artifacts/` token 清理**——**【已完成】**（GOAL-011 建档实测 `git ls-files artifacts/` = 0）
   ⇒ **本项无待办**。
4. **450 行纪律的贴线文件**——**本轮决案：D-05 取 (b) 维持「触线即拆」**；
   **本 GOAL 不专项拆分**（本 GOAL 的授权动作不要求改那四个文件）。
   ⇒ **D-05 终态 = 已拍板为维持现状**；决定**固化**进简报 D-05 与索引，**下轮不再重复提问**。
5. **依赖 pin 升级**（`undici` / `yaml`）——**本轮决案：D-03 继续「分批升」**：
   `yaml` **本轮 patch 升到 `2.8.4`**（EC-01）；`undici` **只调研不升**（EC-02），
   升级面**不在本仓**（依赖链经 `@cursor/sdk`）⇒ 若将来要升，**需单独授权**。
   ⇒ **D-03 终态 = 部分实施**（`vite` 已升 + `yaml` 本轮已升；`undici` 已调研未升）。
6. **hook 侧 L3 门**——**本轮决案：D-04 取 (c) 维持现状**。理由（写进记录供后续引用）：
   简报**建议 (a) 但明确要求先修误报面**；本仓的**已知误报**（正则字面量 / `f-string` SQL /
   URL 形状 / 大文件写盘被拒）**仍在发生**，在误报面未修的情况下安装**阻塞型**检测层会让
   **每轮提交被噪声拦住** ⇒ **本轮维持现状**，并把「**先修误报面**」登记为
   **重启 D-04 的前置条件**。**不安装检测层、不改 hook 面、不改 `MIMOSA_GIT_GATE_MODE`**。
   ⇒ **D-04 终态 = 已拍板为维持现状**（重启前置 = 先修误报面）。
7. **把真实 runtime 设为默认**——**标准禁令（无需拍板）**：默认必须仍是 Fake。
8. **为 anthropic 形态引入 SDK / 新依赖**——**标准禁令（无需拍板）**：需要新依赖即 BLOCKED。
9. **把凭据写进 CI**——**标准禁令（无需拍板）**：CI 必须保持离线。
10. **`ModelCompatibilityProfile` 是否按 AGENTS.md §1 建为一等域实体**——**已拍板：D-08 取 (b)**
    ⇒ 维持**派生视图**（GOAL-016 EC-04 已把依据写成可引用文档）；**本 GOAL 不碰**。
    ⇒ **D-08 终态 = 已实施**。
11. **放宽 `AcceptanceCriteria`（或改合约）使其通过**——**标准禁令（无需拍板）**：明文禁止。
12. **`secrets/llm_key.txt`（gitignored、untracked 的第二份凭据副本）**——**【已完成】**
    （GOAL-011 获删授权并执行完毕）⇒ **本项无待办**。
13. **30 条已跟踪路径含非 ASCII（中文）文件名，违反 AGENTS.md §13**——**已拍板：D-09 取 (a)**
    ⇒ `ADR-0032` 已在位（GOAL-016 EC-04）；**不重命名**、不触碰不可变历史资产。
    ⇒ **D-09 终态 = 已实施**。

**GOAL-016 / 017 特有的项（原样承继 + 本 GOAL 决案结果）**：

- **路径 (B) 的 5 条重设计项**（`docs/roadmap/PATH_B_REFUTATION_RECORD.md`）——
  **本轮决案：D-06 取 (c) 维持** ⇒ 维持「**已否证 / 待重新设计**」**原状**，
  **不重启、不改记录状态词**。⇒ **D-06 终态 = 已拍板为维持现状**。
- **`W-A` 之外的策略面放宽**——**已拍板：D-02 取 (b)** ⇒ **维持逐条**、
  **不成类预放行**、**不新增任何 allow**；**本 GOAL 零策略面改动**。
  ⇒ **D-02 终态 = 已实施**（面 (a) 未授权）。
- **门禁 scoping 的自我修正**（`R-3`）——**已拍板：D-10 取 (a)** 且**已实施**
  （GOAL-017 EC-01）⇒ 本 GOAL 只做**复检**（EC-04）。⇒ **D-10 终态 = 已实施**。
- **本机环境的 DNS / 代理特殊性**（fake-IP `198.18.0.0/15`）——**不改机器网络配置**，
  也不改判据；只做归因与登记。**本 GOAL 的 URL 校验一律复用 `endpoint_policy`**，
  **不另写**「地址须全球单播」这类会拒绝所有域名的判据。
- **`M-1`（出厂组合根是否自己接执行体缝 `ApiDeps.tool_providers`）**——**已拍板：D-01 取 (b)**
  ⇒ 维持装配方补执行体；判据已由 GOAL-016 EC-01 落地。
  **D-01 的 (a) 明确不取** ⇒ **本 GOAL 不碰执行体缝语义**。
  ⇒ **D-01 终态 = 已实施**（面 (a) 未授权）。
- **live 判据的开门条件**——**已拍板：D-11 取 (a)** 且**已实施**（GOAL-017 EC-02）⇒
  本 GOAL 的 **live e2e** 在默认门（无开关）下**如实 skip**，**不引入凭据**。
  ⇒ **D-11 终态 = 已实施**。
- **CI 资源阈值型判据的负载敏感性**——**已拍板：D-13 取 (a)+(b)** 且**已实施**
  （GOAL-017 EC-03）⇒ 本 GOAL 只做**复检**，**作业结构与阈值一律不动**。
  ⇒ **D-13 终态 = 已实施**。

**承继的诚实边界（如实保留，不是待办）**：

- `R-F1`｜收敛 / 一致性判定含主观面时必须先**操作化**。**本 GOAL 原样保留**。
- `R-F2`｜真实数据 / 调用规模不足时的**诚实边界**。**本 GOAL 原样保留**。
- `R-F3`｜~~仓库外并发写者文件致 as-is 本地 m0 可能停在非全绿~~ ⇒ **已由 GOAL-017 EC-01
  收口**（`R-3` 消失，as-is 本机 m0 = 23/23）；本 GOAL 的 EC-04 只做**再确认**。
- **`R-M1`｜Mimosa 钩子侧 `scanner_enobufs` 未得完整结论**——**不得**宣称项目安全。
  **本 GOAL 原样保留**（D-04 维持现状使其**继续存在**）。
- **`R-D1`｜Dependabot 告警**——**本轮更新**：`vite` 4 条 high 已由 GOAL-016 EC-03 清除；
  **`yaml` 1 条（medium）由本 GOAL EC-01 升到 `2.8.4` 清掉**；
  **`undici` 8 条（6 medium + 2 low）原样保留**，**本 GOAL 只调研不升**
  ⇒ 终态表述 = 「`yaml` 已升、`undici` 已调研未升」。
- **`R-B1` / `R-N1`**——承继残余 / 非 ASCII 路径豁免，**原样保留**。
- **`W-1…W-3` / `W-7`**（GOAL-015 / 017 的观察项）——**原样保留**。
- **`W-4`（本机 m0 仍同进程跑阈值判据）/ `W-5`（新作业多一次冷装）/
  `W-6`（`tests/e2e/live_run_support.py` 只剩 1 行余量）**——**原样保留**，
  且 `W-6` 是**规模门禁的零余量告警**：本 GOAL 若需改该文件**必须先搬代码**。

**下一轮 = 甲（主体模型 + 最小认证面）**：

- 内容 = **主体模型**（请求主体 / 身份模型）+ **最小认证面** + **请求主体归因**；
- **需用户另行授权**：本 GOAL **不做**（明文不授权清单第 (6) c 条），
  且本 GOAL 的取证要求是 `git diff` 中 `services/api/middleware.py` 与**路由层零改动**；
- 本 GOAL 的 EC-03 **把「甲」登记为下一轮输入**，使该轮**不需要重新盘点决策面**。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | `869f815`（推送 tip，推送区间 `2208dd5..869f815`） | 治理 `validate.py` = `Cursor 治理验证通过`（`DOCS-CHECK PASS`） | M0 [36185808007](https://github.com/Eswink/research-system-new/actions/runs/36185808007) **八 job 全 success** + CodeQL [36185807208](https://github.com/Eswink/research-system-new/actions/runs/36185807208) **3/3 success**（`run_attempt=1`，轮询 `ALL_TERMINAL`；日志 `scratch/goal018-c0-ci-poll.log`）。上游同时返回 **9 条**告警（7 moderate + 2 low），与 `/dependabot/alerts?state=open` 实测一致 | — | EC-01…EC-04 全 PENDING；授权与边界已落 frontmatter；起点已定位（`yaml` 首个修复版本 `2.8.3`、**`2.8.x` 最新 patch = `2.8.4`**；Dependabot 实际 9 条 = `undici` 8 + `yaml` 1；`undici@5.29.0` 依赖链 = `@cursor/sdk@1.0.30` → `@connectrpc/connect-node@1.7.0` → `undici@5.29.0`，**唯一入边 1 条**；`connect-node` 对 undici 的唯一用法 = `node-headers-polyfill.js` 的 `Headers` 且 **Node ≥ 18 下不可达**；1.x 全线带 `undici ^5`、2.x 起**不再依赖 undici** 但为**破坏性主版本**；`@cursor/sdk` 最新 `1.0.32` **仍锁 `^1.6.1`**） | cycle 1 = **EC-01 `yaml` patch 升级** + **EC-02 `undici` 调研** + **EC-03 13 项决案结清** |
| 1 | PLAN-20260926-186（EC-01 + EC-02 + EC-03） | `411ee25`（WP1 = `yaml`）+ `cfd9a4e`（WP2 = 调研文档 + 简报）+ `83b782c`（WP3 = 判据 + 记录；**推送 tip**，推送区间 `869f815..83b782c`） | **EC-01**：`yaml` `2.8.1 → 2.8.4` 且 `git diff` 逐 hunk 证明**只有这一个包**变化（823 字节同长）；web 六门全绿 = `lint` 0 / `typecheck` 0 / unit **88 passed** / `build` 成功 / stub e2e **98 passed** / live e2e **53 passed**（无开关 ⇒ 无 LLM 出网）+ 根 `check` 0；**设计基线无漂移**（`design-outline-guard` **6 passed**、`design-outlines.json` 逐字节未改 ⇒ 未重生成、容差未动）；**as-is m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24、`FAILED`/`ERROR` 零命中、日志 `scratch/goal018-c1-m0.log`）。**EC-02**：`docs/roadmap/UNDICI_TRANSITIVE_DEPENDENCY_RESEARCH.md` 在位（三问各有答案与依据 + 复现命令 + 授权清单）；**反证** = `grep -n "undici: 5.29.0" pnpm-lock.yaml` 仍**恰好 1 条**、两个 `package.json` 均无 `overrides` / `resolutions`。**EC-03**：简报终态表 **13 行** + GOAL 人工面 **13 条同词声明**（已实施 9 + 部分实施 1 + 已拍板为维持现状 3 = 13，**未授权待拍板 0**）；判据 `tests/tooling/test_pending_decisions_briefing.py` **14 passed**（1 现状 + 13 按压，日志 `scratch/goal018-c1-ec03-press.log`）；`tests/tooling` = **1169 passed**；`ruff check` = `All checks passed!`、`ruff format --check` = 已格式化、规模门禁 = **1029 passed**；治理 `validate.py` + `DOCS-CHECK` 绿 | M0 [**36191382569**](https://github.com/Eswink/research-system-new/actions/runs/36191382569) **八 job 全 success**（`run_attempt=1`，一次成功）：`quality-ubuntu-latest` / `console-frontend` / `quality-windows-latest` / `observability-overhead-windows-latest` / `observability-overhead-ubuntu-latest` / `container-quality` / `eval-gate` / `collector-quality` **全 `success`**；CodeQL [**36191381460**](https://github.com/Eswink/research-system-new/actions/runs/36191381460) **3/3 success**（`run_attempt=1`）；另有一条 **Dependabot run** [**36191504926**](https://github.com/Eswink/research-system-new/actions/runs/36191504926)（`npm_and_yarn in / for yaml`，`success`）。轮询日志 `scratch/goal018-c1-ci-poll.log`（`ALL_TERMINAL`）。**外部旁证**：`?state=open` 告警 **9 → 8**，剩余**全部**是 `undici`（6 medium + 2 low）⇒ 既证明 `yaml` 那条已清、又独立印证 `undici` 一字未升 | **一次判据缺陷（当场发现并修）**：EC-03 的按压第一版用「按行首删一行」，命中的是简报里**同形状的索引表**（也以 `| D-05 | …` 开头）⇒ **判据没被触碰**（看着红其实没动判据）。改为 **只在终态表块内替换 + 块内未命中即断言失败**后，按压才生效 ⇒ 记入 `MEM-20260926-142`（`MEM-141` 的同类新形态）。**一次 `yaml` 目标版修正**：授权写「最新 patch」而建模档一度按**首个修复版本 `2.8.3`** 写；实测 `2.8.x` 版本表为 `2.8.0/1/2/3/4` ⇒ **落地目标改为 `2.8.4`**（仍 patch 面内，且覆盖修复版本），记录已同步 | **EC-01 / EC-02 / EC-03 = PASS**（CI 证据已在下方台账登账：M0 八 job + CodeQL 3/3 + Dependabot 全 `success`，`run_attempt=1`）；`RECHECK-20260926-187` = `PASS_WITH_WARNINGS`（W-1 按压打偏 / W-2 CI 证据在 GOAL 侧登账 / W-3 可利用性评估有前提 / W-4 `undici` 8 条仍挂 / W-5 engines 上限 `7.30.0` / W-6 `R-M1` 原样）。EC-04 当时仍 PENDING | cycle 2 = **EC-04 收口复检**（两树复检 + m0 终态行 + 13 项终态表 + CI 台账到终态 + 承继残余） |
| 2 | PLAN-20260926-188（EC-04 收口） | **收口提交**（记录面 + GOAL `ACTIVE → ACHIEVED`）：**本行由该提交写入** ⇒ 依「固定口径」其 SHA **只在回合汇报记账、不回写文件** | **两树复检**（`scratch/goal018-ec04-recheck.py`，**不含任何进程执行**：改动面由 git 清单喂入、判据由调用方实跑）：结构半 **14 条** ⇒ `FAILED=[]` / `RECHECK: PASS`；**两树同结论** = 工作树 vs 干净 `git worktree`（`D:\rs-goal018-clean`，detached HEAD `83b782c`）**判词列 14/14 相同**且**整份输出逐字节相同**（`diff` 无输出）；**非恒真 6/6 判红**（`yaml-pin` / `undici-upgrade` / `terminal-row` / `terminal-state` / `goal-decl` / `residual`）；判据面两树同结论 = **14 passed** / **1029 passed** / `Cursor 治理验证通过` / `DOCS-CHECK PASS`；**as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24、`FAILED` 零命中、退出码 0；`scratch/goal018-c2-m0-as-is.log`）；13 项终态表 13 行 + 人工面 13 条同词；残余 `R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` / `W-4` / `W-5` / `W-6` **逐条在人工面节内**。**本 cycle 只动记录面 + 一条判据口径收紧**（见「修复」列） | 待轮询（**收口提交自身的 run 依「固定口径」只在回合汇报记账**，沿用既有闭合约定） | **两次同类缺陷（当场发现并修）**：① `terminal-row` 与 `residual` 第一版**没判红**——简报里有一张**同形状的索引表**（也以 `| D-05 | …` 开头）导致整份替换命中错表；残余检查当时扫**整份 GOAL** 而 `R-M1` 在别处还有一处提及 ⇒ 修法：按压加**作用域**（`terminal-block` 块内替换 + 块内未命中即断言失败）、残余检查收到**人工面节内**。② **节边界缺陷（同一根因）**：`_GOAL_SECTION` 的前置 `.*` 是**贪婪**的，匹配会从文件里**更早的** `##`（实测「目标与退出标准」）起算，把别处的编号项与 `**D-NN 终态 = …**` 声明一并吸进来 ⇒「13 条声明」**不是**绑在人工面节上；收紧为**标题行自身必须含该短语**后重新通过（这是**加强**，不是放宽） | **GOAL-018 收口：EC-01…EC-04 全 PASS**。**残余（原样保留，未收口也未掩盖）** = `R-M1`（Mimosa 钩子侧结论未得，**不得**宣称项目安全）+ `R-D1`（**`yaml` 已升、`undici` 已调研未升** ⇒ 告警面 **8 条**全为 `undici`）+ `R-B1` / `R-N1` + `R-F1` / `R-F2` + `W-4` / `W-5` / `W-6`；**D-04 重启前置 = 先修误报面** | —（**终态，无下一轮输入**）；**下一轮 = 甲（主体模型 + 最小认证面，需用户另行授权）** |

### CI 台账（逐 run 逐 job 实查；全部落在 main）

| 推送 | 提交 | run | 八 job 结论 |
| --- | --- | --- | --- |
| 建档（GOAL-018 落地） | `869f815` | M0 [36185808007](https://github.com/Eswink/research-system-new/actions/runs/36185808007) / CodeQL [36185807208](https://github.com/Eswink/research-system-new/actions/runs/36185807208) | **绿（八 job 全 success + CodeQL 3/3）**（`run_attempt=1`，一次成功）：M0 `conclusion=success`，逐 job `quality-ubuntu-latest` / `console-frontend` / `observability-overhead-windows-latest` / `observability-overhead-ubuntu-latest` / `container-quality` / `collector-quality` / `quality-windows-latest` / `eval-gate` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (actions)` / `Analyze (javascript-typescript)` / `Analyze (python)` **3/3 `success`**。轮询日志 `scratch/goal018-c0-ci-poll.log`（第 38 轮 `completed=2/2`、`ALL_TERMINAL`）。上游 push 回执同时报 **9 条**告警（7 moderate + 2 low） |
| cycle 1 实施（EC-01 + EC-02 + EC-03） | `411ee25` + `cfd9a4e` + `83b782c`（tip） | M0 [36191382569](https://github.com/Eswink/research-system-new/actions/runs/36191382569) / CodeQL [36191381460](https://github.com/Eswink/research-system-new/actions/runs/36191381460) | **绿（八 job 全 success + CodeQL 3/3）**（`run_attempt=1`，一次成功）：M0 `conclusion=success`，逐 job `quality-ubuntu-latest` / `console-frontend` / `quality-windows-latest` / `observability-overhead-windows-latest` / `observability-overhead-ubuntu-latest` / `container-quality` / `eval-gate` / `collector-quality` **全 `success`**；CodeQL `Push on main` `conclusion=success`，`Analyze (javascript-typescript)` / `Analyze (actions)` / `Analyze (python)` **3/3 `success`**。同 SHA 另有 **Dependabot run** [36191504926](https://github.com/Eswink/research-system-new/actions/runs/36191504926)（`npm_and_yarn in / for yaml - Update`，`success`）。轮询日志 `scratch/goal018-c1-ci-poll.log`（`ALL_TERMINAL`）。**外部旁证**：`/dependabot/alerts?state=open` **9 → 8**，剩余**全部**是 `undici`（6 medium + 2 low），留档 `scratch/goal018-gh-alerts-after.json` |
| cycle 2 实施（EC-04 收口） | **收口提交**（记录面 + GOAL `ACTIVE → ACHIEVED`）：**本行由该提交写入** | 依「固定口径」**只在回合汇报记账、不回写文件** | 依「固定口径」其自身 run **只在回合汇报记账**（其余全部推送提交的 run 已在上面两行登账到终态） |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-26 | ACTIVE | 建档：用户会话指令（goal 模式）「**先收尾，然后再甲**」⇒ 本轮做**收尾轮**。授权实施严格限于两项：**`yaml` patch 升级**（`2.8.1 → 2.8.4`）+ **`undici` 前置调研（零升级）**；授权登记三条：**D-06 取 (c) 维持** / **D-05 取 (b) 维持** / **D-04 本 GOAL 拍板为 (c) 维持 + 重启前置 = 先修误报面**。四 EC 设计（yaml 升级 / undici 调研 / 13 项 `D-NN` 结清 / 收口复检）。**明确不授权**：`undici` 升级（含 overrides）、hook 检测层安装、**甲的全部内容**（鉴权 / 中间件 / 路由保护）、D-01(a) / D-02(a) / D-12(a)、`ADR-0031` 的 `Status`、`yaml` 跨 minor。**建档时零代码改动**（只增本文件）。建档提交 `869f815` 的 CI = **八 job 全 success + CodeQL 3/3**（`run_attempt=1`）。 |
| 2026-09-26 | ACTIVE | cycle 1：派生 **PLAN-20260926-186**（EC-01 + EC-02 + EC-03 合并为一个可独立验收的主题面）。**EC-01**：`yaml` `2.8.1 → 2.8.4`（`2.8.x` 最新 patch；首个修复版本 `2.8.3` 被覆盖）——lockfile **只有这一个包**变化，web 六门 + 根 `check` 全绿，**设计基线逐字节未改**（无漂移 ⇒ 未重生成、容差未动），**as-is m0 = 23/23**。**EC-02**：`undici` 三问结论文档在位（**不可在本仓正确升级**，归属方 = `@cursor/sdk` 上游），**零升级**由两条反证钉住。**EC-03**：13 项终态表 + GOAL 侧 13 条同词声明 + 对齐表封闭词汇表，**零「待定」**；判据扩到 **14 passed**，含 **13 条按压**（其中一次「按压打偏」当场修：简报里有**同形状的索引表**）。EC-04 仍 PENDING。 |
| 2026-09-26 | ACHIEVED | cycle 2（收口）：派生 **PLAN-20260926-188**（EC-04 收口复检）。**两树复检**（`scratch/goal018-ec04-recheck.py`，**不含任何进程执行**）：结构半 **14/14 PASS**，工作树 vs 干净 `git worktree`（`D:\rs-goal018-clean`，detached `83b782c`）**判词列 14/14 相同**；**非恒真 6/6 判红**（`yaml-pin` / `undici-upgrade` / `terminal-row` / `terminal-state` / `goal-decl` / `residual`）；判据面两树同结论 = **14 passed** / **1029 passed** / `Cursor 治理验证通过` / `DOCS-CHECK PASS`；**as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`**（`PASS [` = 24、`FAILED` 零命中、退出码 0）。**当场修掉两处同类缺陷**：按压作用域（简报里有**同形状的索引表** ⇒ 整份替换会打偏）与 `_GOAL_SECTION` 的**贪婪**节边界（原会从更早的 `##` 起算，把别处的编号项与声明吸进来）⇒ 后者是**判据加强**。**13 项 `D-NN` 终态齐**（已实施 9 + 部分实施 1 + 已拍板为维持现状 3，**未授权待拍板 0**）。承继残余 `R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` / `W-4` / `W-5` / `W-6` 逐条在人工面登记。**EC-01 / EC-02 / EC-03 / EC-04 全 PASS。** |
