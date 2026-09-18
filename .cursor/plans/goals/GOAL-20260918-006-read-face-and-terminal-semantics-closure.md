---
id: GOAL-20260918-006
slug: read-face-and-terminal-semantics-closure
title: 读面与终态语义收口：PG 快照一致读、DEAD_LETTER 消费、前端消费重建读面、时钟断言去调度依赖、批量读上限与 Fake 同判、失败诚实边界
status: ACTIVE
created_at: 2026-09-18
updated_at: 2026-09-18
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-18 用户会话指令（goal 模式）：**新建承接 GOAL-006**，把 GOAL-20260918-005
    收口时如实登记、但未随收口通过的长程项（「终止与收口 · 收口结论（2026-09-18）」第 2…4 项
    与 RECHECK-20260918-093…099 的 W 列表）按优先级做成可独立验收的 EC，之后由本驱动
    **自动化循环推进、无需逐轮确认**。承接关系 = GOAL-005 收口结论表：① PG 两读快照
    一致性（EC-05 ② 未做 / RECHECK-097 W-1）、② `DEAD_LETTER` 消费（EC-03 余项 /
    RECHECK-095 W-2）、③ 前端未消费 `rebuild` 读面（RECHECK-098 W-3）、④ 时钟断言的
    调度依赖与真墙钟矩阵（RECHECK-096 W-1/W-4）、⑤ 批量读无上限 + Fake 弱同判
    （RECHECK-097 W-2/W-3）、⑥ 失败的诚实边界余项（RECHECK-090 W-2…W-5）。
    GOAL-005（ACHIEVED）、GOAL-004（ACHIEVED）、GOAL-003（BLOCKED）保持只读，
    **本 GOAL 不修改它们**（如需指名，只允许在对方文件追加一行事实更正；本 GOAL 当前不需要）。
    push-to-main-for-CI 授权沿用 GOAL-001…005 的批准口径：**只推 main、不 force、
    不重写历史、不推旁支触发 CI**；push 前 `git pull --ff-only origin main`（必要时
    --rebase，始终不 force）。循环预算与纪律以本文件 frontmatter 为准（客户端自带的
    迭代/重试/超时上限一律让位于此）。
objective: >
  把 GOAL-005 收口时如实登记的残留从「已登记的边界」变成「有终态结论的事实」：
  `dispatch_ownership` 的 PG 两读拿到快照一致性结论（实现一致读，或 ADR 级论证 + 契约
  收敛到该论证）；`DEAD_LETTER` 拿到按声明处置的终态（在既有 canonical 边界内实现，
  或 ADR 草案 + 权威登记 + 声明/文档同源）；控制台页面真的消费 `rebuild` 读面（三态 +
  `missing`）且「读面不预测结果」在 UI 与文档同源；时钟断言去掉对调度时序的依赖并给出
  真墙钟覆盖口径；批量读加显式上限语义、Fake 的弱同判与真引擎对齐或写成显式边界；
  失败原因给出结构化任务级归因或登记为一等边界且守护线程补偿失败的降级读面可见。
  **全程不删测试、不改门禁、不以「未观测到失败」或「扫描没报问题」充当 PASS；
  触及 canonical 状态机 / Accepted ADR / 核心安全策略即 BLOCKED，不自行扩大边界。**
exit_criteria:
  - id: EC-01
    criterion: >-
      PG 两读快照一致性（GOAL-005 收口结论第 2 项 / RECHECK-097 W-1，承接该 GOAL 的
      EC-05 ②）：`dispatch_ownership` 的「重排投影 + 租约」两条 SQL 拿到**二选一终态**——
      (a) 实现一致读：两读落在**同一语句**（单语句 CTE / `UNION ALL` + 判别列）或
      **同一快照**（同一事务 + 明写的隔离级别，并说明该级别由何保证）；或
      (b) **ADR 级论证不做**：给出一等事实（为何在同一语句/快照内不可表达，或代价与收益
      的技术依据）并把契约（port docstring / `PORTS.md` / `docs/api/CONTROL_PLANE_API.md`）
      **收敛到与该论证一致**。仅「文档已写明非快照」**不算**交付（GOAL-005 已做完登记）。
    verify: >-
      结构判据（可复核的代码事实：一次 `dispatch_ownership` 调用内的语句数 = 1，或 = 2 但
      同一事务且隔离级别在代码/文档可查）+ 并发用例（在两次读之间插入外部写 ⇒ 选 (a) 时
      不得出现「重排已前移、租约仍旧值」的撕裂读；**反证：拆回两次独立读 ⇒ 用例红**）+
      **PG parity**（SQLite/Fake 与 PG 在快照语义上的同判形态写明；不一致处点名为显式边界）+
      受影响套件（含 `tests/postgres`）+ m0 绿。选 (b) 时：ADR 草案/一等事实文档在树 +
      三处契约逐处一致（反向搜索快照相关措辞）。
    status: PENDING
  - id: EC-02
    criterion: >-
      `DEAD_LETTER` 消费（GOAL-005 收口结论第 3 项 / RECHECK-095 W-2，承接其 EC-03 余项）：
      验收门拒收一条已 durable `SUCCEEDED` 的任务行后，按 `failure_policy` 声明处置拿到
      **二选一终态**——(a) **实现**：在**既有 canonical 状态机边界内**落终态（`DEAD_LETTER`
      已是既有状态；不得新增 canonical 状态或迁移）；或 (b) **ADR 草案 + 权威登记 + 同源
      收敛**：写明为何不在本循环做（属产品语义/canonical 决策），把声明面（示例契约、
      `failure_policy.py`、`TASK_HANDOFF` §2.1、port docstring）与文档**同源收敛**到一处口径。
      **触及 canonical 状态机与 Accepted ADR 边界时按 escalation 立即 BLOCKED，不自行扩大边界。**
    verify: >-
      二选一：(a) 用例（拒绝 ⇒ 任务行落 `DEAD_LETTER` 或既有等价终态，事件链可读；
      **反证：去掉处置 ⇒ 用例红**）+ 事件 payload schema + 读面可判；
      (b) ADR 草案文件在树（`docs/adr/`）+ 权威登记（`docs/INDEX.md` 或既有 ADR 的未决段）
      + `on_validation_failure` 反向搜索每处命中要么是「真实消费者 + 用例」要么是
      「不提供/待决」说明 + 四处文档逐处一致。两条都要求：**不得只改注释/文案充数**。
    status: PENDING
  - id: EC-03
    criterion: >-
      前端消费重建读面（RECHECK-098 W-3）：控制台页面**真的展示** `RunDetailDto.rebuild`
      （三态 `SELF_CONTAINED`/`SOURCE_DEPENDENT`/`REFUSED` + `missing` 点名），接入 +
      **stub e2e 一条链 + live e2e 一条链**；「读面不预测结果」口径在 UI 文案与文档
      **同源**（`SELF_CONTAINED` 不得渲染成「重建必过」，`REFUSED` **不得**渲染成
      「不可回填」——RECHECK-098 W-1/W-2）。
    verify: >-
      结构判据（`rebuild` 字段在页面有渲染分支，不是「只在 `types.ts` 里存在」）+
      stub e2e 与 live e2e 各一条（断言三态在页面上可区分；**反证：去掉渲染分支 ⇒
      对应 e2e 红**）+ web 六门（lint / typecheck / unit / build / stub e2e / live e2e）+
      页面改动的设计基线/结构签名按既有流程重生成（跨平台一致性用既有容器配方复核）+
      文档同源（`CONTROL_PLANE_API.md` / 页面文案同一口径）。
    status: PENDING
  - id: EC-04
    criterion: >-
      时钟断言的调度依赖收口（RECHECK-096 W-1 + W-4）：① 把**依赖调度时序**的断言
      （`tests/postgres/test_claim_concurrency_pg.py` 的「并发是真的」`>= 2`）改成
      **不依赖调度**的形式（例如「进入领循环的线程计数」/显式相位判据），**不得**删掉它
      （它保护的是「测试真的在并发」这一前提）；② 真墙钟对照矩阵给出一等口径：要么建立
      `tests/postgres/test_cross_process_real.py` 的覆盖矩阵（用例 × 覆盖的时序 × 等待有界
      判定方式），要么给出为何不可行的一等事实 + 结构判据。**不得以「未观测到失败」收尾。**
    verify: >-
      结构判据（改后的断言不读取调度产物——不依赖「谁先跑完」，改为可复核的相位/计数事实）+
      反证（把断言替换回调度依赖形态 ⇒ 判据可识破；或注入调度扰动 ⇒ 新断言仍不红）+
      真墙钟矩阵：文件级覆盖表（或不可行论证 + 结构判据）+ 受影响套件（`tests/postgres`）+
      m0 绿。矩阵口径须写明**等待有界**（有界轮询，非固定 sleep）。
    status: PENDING
  - id: EC-05
    criterion: >-
      批量读上限与 Fake 同判（RECHECK-097 W-2 + W-3）：① `dispatch_ownership_many` 加
      **显式上限语义**——超限行为可判定（明确 raise / 分块 / 契约上限），且上限值写在
      契约（port docstring + `PORTS.md` / `CONTROL_PLANE_API.md`）而不是隐含；② Fake 的
      **弱同判**（「活」= 仍在租约表里，无过期语义）要么与 SQLite/PG **对齐**（Fake 实现
      过期语义并有用例证明同判），要么在契约里把**弱化写成显式边界**（同判用例只断言可
      同判部分，不一致处逐条点名）。
    verify: >-
      ① 上限用例（超限 ⇒ 可判定行为；**反证：把上限去掉/放宽 ⇒ 用例红**）+ 三实现一致
      （SQLite / PG / Fake 同判据覆盖超限与边界，含空入参、未知 run ⇒ `NONE` 条目）；
      ② 对齐 ⇒ Fake 过期用例与真引擎**同判**（同一断言形态跑三实现）；显式边界 ⇒
      结构判据（契约写明弱化 + 用例只断言可同判部分，且不一致处点名）+ 文档同源；
      受影响套件（含 `tests/adapters/sqlite`、`tests/postgres`、`tests/api`）+ m0 绿。
    status: PENDING
  - id: EC-06
    criterion: >-
      失败的诚实边界（GOAL-005 收口结论第 4 项 / RECHECK-090 W-3/W-4/W-5）：**二选一终态**——
      (a) **结构化任务级归因**：续跑失败的 `run.resume_failed` payload 从「异常类型 + 文本」
      升级为**结构化任务级归因**（失败任务/phase 可判），且读面能判；或 (b) **一等边界 +
      降级可见**：把「哪一步炸的仍需读事件链上下文」登记为一等边界（文档同源），**并**把
      守护线程补偿失败的静默降级（`_compensate_failed_resume` 的 `except: pass`）做成
      **读面可见**（canonical 痕迹或读面字段），不得只留在遥测/log。
      （W-5「响应仍 200」的传输层信号属产品决策，只作如实登记，不改。）
    verify: >-
      (a) 事件 payload schema + 用例（失败 ⇒ 归因字段点名任务/phase；**反证：去掉归因 ⇒
      用例红**）+ 读面字段 + 文档同源；(b) 文档同源（写明读面**不承诺**任务级归因）+
      补偿失败可见性用例（store 不可用 ⇒ 补偿失败在 canonical/读面可见，而非静默 pass）+
      反证（把补偿失败改回静默 ⇒ 用例红）。两条都要求：受影响套件 + m0 绿，
      **未实跑不得记 PASS**。
    status: PENDING
budget:
  max_cycles: 20
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更（含为判据引入新的图像/解析库——优先用现有依赖实现）
  - 同一失败签名超过 fix_policy 上限
  - 「按声明给 adapter 接线」与 `tool_pack.*`/脚本策略（GOAL-004 后继入口第 8 项）——受控出网与产品决策，需用户或 ADR 拍板
  - 威胁建模/授权面（BOLA/BFLA）覆盖与受控出网类决策——需用户或 ADR 拍板，本循环不得自行决定
  - 依赖 pin 升级（`undici` / `vite` / `yaml` 等有修复版本的包）——上游 pin 变更，需用户或 ADR 拍板
child_plans: []
latest_recheck: null
memory_entries: []
---

# GOAL-20260918-006 — 读面与终态语义收口（自迭代循环）

本文件是 **GOAL 记录**（位于 `PLAN-*` 之上的编排层），格式契约见本目录 `README.md`；
工程事实、验收与复检仍由 PLAN/RECHECK/MEM 体系承载（单一流程权威：
`.cursor/rules/20-plan-memory-recheck.mdc`）。GOAL 只做编排与记账。

## 目标与退出标准

GOAL-005 收口（ACHIEVED）时把「仍未处理的长程项」如实登记进「终止与收口 · 收口结论」，
并给出恢复条件「用户新建承接 GOAL」。本 GOAL 承接其中**可独立验收的六项**，逐条做成 EC；
收口结论里**依赖人工拍板**的六项按契约照抄进「不进入循环 / 需人工拍板」节，
**不伪装成 EC**。

| EC | 主题 | 来源 | 状态 |
| --- | --- | --- | --- |
| EC-01 | PG 两读快照一致性（实现一致读 或 ADR 级论证 + 契约收敛） | GOAL-005 收口结论 2 / RECHECK-097 W-1 | PENDING |
| EC-02 | `DEAD_LETTER` 消费（既有边界内实现 或 ADR 草案 + 权威登记 + 同源收敛） | GOAL-005 收口结论 3 / RECHECK-095 W-2 | PENDING |
| EC-03 | 前端消费重建读面（页面接入 + stub/live e2e + 「不预测结果」同源） | GOAL-005 收口结论 4 / RECHECK-098 W-3 | PENDING |
| EC-04 | 时钟断言去调度依赖 + 真墙钟对照矩阵（或一等事实 + 结构判据） | GOAL-005 收口结论 4 / RECHECK-096 W-1 + W-4 | PENDING |
| EC-05 | 批量读显式上限 + Fake 弱同判对齐或写成显式边界 | GOAL-005 收口结论 4 / RECHECK-097 W-2 + W-3 | PENDING |
| EC-06 | 失败的诚实边界（结构化任务级归因 或 一等边界 + 补偿失败降级可见） | GOAL-005 收口结论 4 / RECHECK-090 W-3…W-5 | PENDING |

**优先级**：EC-01 → EC-02 → EC-03 → EC-04 → EC-05 → EC-06（derive 取 EC 表首个 PENDING；
若某 EC 本轮**部分交付**，其「下一轮输入」优先于表序）。

**不在本 GOAL 的 EC 内**（登记为背景，不伪装成已收口）：GOAL-005 收口结论第 1、5 项
（人工决策面六项、扫描 coverage 口径）见「不进入循环 / 需人工拍板」节；
RECHECK-098 W-2（历史行要不要 re-freeze/fork）与 RECHECK-090 W-5（响应仍 200）
是运营/产品决策，只作如实登记。这些**不因本 GOAL 存在而被宣称已解决**。

### EC-01 判定细则（PG 两读快照，二选一）

- **禁止的 PASS 依据**：「文档已写明了」「跑一次没撕裂」。PASS 只认**结构判据**
  （一次调用内的语句数 / 事务与隔离级别）**加**并发用例**加**反证。
- 选 (a) 实现时，优先**单语句 CTE**（`WITH` 内两次投影 + 判别列），因为它把一致性
  交给语句快照本身；退而求其次用同一事务（隔离级别须写明由何保证，且不得为此降级
  PG 默认隔离级别）。
- 选 (b) 论证时，必须回答：为什么不做的技术依据是什么、代价落在哪、契约如何收敛
  （三处文档逐处一致），以及**并发撕裂读的后果**是什么（谁在读、读到什么）。
- **反证必须实跑**：拆回两次独立读（或去掉事务）⇒ 至少 1 条用例变红。

### EC-02 判定细则（`DEAD_LETTER` 消费，二选一）

- (a) **实现**的硬边界：**只允许既有 canonical 状态**（`DEAD_LETTER` 已在状态机内）
  与**既有迁移**；若实现需要新增状态、新增迁移或改写 Accepted ADR ⇒ **立即 BLOCKED**。
- (b) **ADR 草案**必须给出：问题陈述、候选方案与代价、为何本轮不做、触发条件（何时
  必须做）、影响面（谁在读这条任务行）。
- 两条共同要求：`on_validation_failure` 的**反向搜索**每处命中可解释（消费者或说明），
  且**至少有 1 条用例**证明处置不是文案改动。

### EC-03 判定细则（前端消费重建读面）

- 「接入」的定义是**页面可区分三态**：`SELF_CONTAINED`、`SOURCE_DEPENDENT`（并列出
  `missing` 字段名）、`REFUSED`；三者文案不同且不预测结果。
- 页面改动必须走既有设计基线流程（结构签名判红 ⇒ `UPDATE_OUTLINES=1` 重生成 ⇒
  跨平台一致性复核），否则 web 门会红。
- live e2e 的夹具必须由域代码生成（内容寻址 digest 不可手写），spec 要幂等。

### EC-04 判定细则（时钟断言的调度依赖）

- 改后的断言**不得**读取调度产物（谁先跑完、谁领了几条）；应读取**相位事实**
  （如「有多少线程进入了领循环」）。
- 真墙钟矩阵的口径必须包含**等待有界**（有界轮询，非固定 sleep）与**覆盖声明**
  （覆盖哪些时序、不覆盖哪些）。
- 若判定「矩阵不可行」，必须给一等事实 + 结构判据，且**不得**因此宣称时序风险已清空。

### EC-05 判定细则（批量读上限与 Fake 同判）

- 上限语义的三选一必须**明说**：raise（点名异常类型）/ 分块（点名分块大小与顺序保证）/
  契约上限（写明调用方义务）。隐含上限不算。
- Fake 分支：若选「显式边界」，则同判用例必须**逐条点名**哪些断言只在真引擎上成立
  以及为什么（不能只是"Fake 上也跑一遍"）。

### EC-06 判定细则（失败的诚实边界）

- (a) 的「任务级归因」指：失败事件能回答**哪个任务/phase 失败**，而不是把异常文本
  塞进 payload 就算。
- (b) 的「降级可见」指：补偿失败后**读面能判**（canonical 事件或读面字段），
  不是遥测/log 里有。
- **W-5（响应仍 200）不改**：传输层信号属产品决策，只作如实登记。

## 循环入口协议

按 README 的 7 步判定执行，一切状态以「文件 + 工作树 + 远端实况」为准：

1. 本文件 `status != ACTIVE` → 只输出终止摘要（ACHIEVED/BLOCKED/ABORTED + 依据），本轮不做改动。
2. 迭代日志最后一行判定续点：无记录 → 开 cycle 1（执行 ①）；有子 PLAN 在
   IN_PROGRESS → 继续 ②；本地验证已过、有未推送 commit → ④⑤；CI 未记录结论 →
   ⑤（等待/判定，禁止猜测绿）；CI 有失败且未达上限 → ⑥。
3. 每 cycle 收口必须：CI 终态已记录 + 本文件（迭代日志/EC 状态/child_plans/
   latest_recheck/状态历史）已回写；未收口不得开新 cycle。
4. 进入 cycle 时在迭代日志声明 `driver=client-goal` / `owner=root-agent`；另一驱动
   持有未收口 ACTIVE cycle 时等待，不并发双写。

当前续点：**建档完成即进入 cycle 1 = EC-01（PG 两读快照一致性）**。状态以本文件
「迭代日志」末行 + 工作树实况为准；不凭记忆假设上一轮状态。

## 驱动

驱动无关（README「驱动适配」）：本实例由客户端 goal 模式驱动（每轮触发 = 一次入口
协议），亦可换会话/定时驱动；仅当 `status=ACTIVE` 时推进。同一时刻仅一个驱动推进。

## 单 cycle SOP

按 README ①~⑦ 执行。本实例附加约定：

- ① derive 主题顺序：EC 表首个 PENDING；若上一 cycle 部分交付，以其「下一轮输入」为准。
  子 PLAN 必须独立可验收、独立 RECHECK（`.cursor/plans/rechecks/`），frontmatter 带
  `parent_goal: GOAL-20260918-006` 并投影 ALL_PLAN。
- ② 按子 PLAN 的 WP 推进，**每 WP 独立 commit**（显式路径；并发工作树，禁 `git add -A`）。
- ③ 本地验证：`make validate-all` 全量 23 项（DSN 固化配方）+ 受影响定向套件 + web 门
  （lint/typecheck/unit/build/stub e2e/live e2e）；页面改动时按既有流程重生成设计基线
  与结构签名（`UPDATE_OUTLINES=1 pnpm exec playwright test design-fidelity -g 结构签名`，
  跨平台一致性用既有容器配方复核）。实现完成后**先自查规模门禁**（50 行函数 / 450 行文件）
  与快照类门禁（OpenAPI / 设计基线），再跑 m0。本地不绿不得 push。
- ④ 子 PLAN 收口（RECHECK DONE）后 GOAL 记录 commit 列表。
- ⑤ `git pull --ff-only origin main`（必要时 --rebase，不 force）→ `git push origin main`
  → 按本机口径查 m0-quality 最新 run（无 gh CLI：`git credential fill` 取已存令牌走
  GitHub REST API，按 head_sha 匹配 + `/jobs` 读六个 job 结论）→ 轮询到终态并记录
  run 链接与结论。只改 `.cursor/**` 的记录提交同样触发六 job CI，按同口径等待。
- ⑥ 按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤。
- ⑦ 回写本文件：迭代日志（含 driver/owner 声明行）、EC 状态、child_plans、
  latest_recheck、状态历史；未达终态且未触顶 → 直接进入下一 cycle ①。
- **未实跑不得记 PASS**；本机无法验证记 PENDING 并停止推进，不猜测绿。
- **CI 台账闭合约定**（沿用 GOAL-005）：逐条记录每个推送提交触发的 run 到终态；
  写下本条的这个提交自身触发的 run 在回合汇报里给出终态、不再回写文件。

## CI 失败分类与纠错

按 README 分类表执行；本仓已知 flake/env 签名（重跑不修，先排除环境干扰）：
observability OTLP teardown race（stopped receiver 端口）、m0 全量单跑在负载下的 timing
用例（隔离复跑对照）、DSN 注入（需固化配方：`RESEARCHOS_POSTGRES_DSN` 指向 test DSN、
其余 DSN 键清空，防 litellm `load_dotenv` 注入 operator `.env`）、
`framework/run_cursor_framework_evals` 在 Windows 上偶发文件占用（复跑对照）、
**kill 后台 m0 会留孤儿 pytest**（复跑前先确认无残留进程/容器，否则污染下一轮）。

`.github/workflows/m0-quality.yml` 属治理面：循环内不修改；需要改动即 BLOCKED 提请人工。
账户级计费阻断（runner_id=0、无 step、2 秒结束）非代码缺陷：不推进 cycle，恢复后先复核
`runner_id != 0` 再回填结论（GOAL-003 cycle 1 的处置模板）。

## 终止与收口

- **ACHIEVED**：EC-01…EC-06 全 PASS 且有实跑证据 + 收口 RECHECK（独立复检，
  `result: PASS` 或 `PASS_WITH_WARNINGS`）+ 本文件 `latest_recheck` 指向该 RECHECK +
  「终止与收口」写明收口结论（含仍未处理项，如有）。
- **BLOCKED**：`budget.max_cycles` 触顶、或 `no_progress_stop_cycles` 连续命中、
  或命中 `escalation_triggers`（含威胁建模/授权面、canonical 边界与依赖 pin 决策）。
  写 BLOCKED 记录（原因/EC 状态表/收口复检/安全扫描处置/恢复条件/仍未处理的长程项），
  恢复条件由用户拍板。
- **ABORTED**：用户显式终止本目标。

收口时必须把「仍未处理的长程项」如实登记为后继入口（不隐藏缺口），并给出恢复条件
（新建承接 GOAL 或显式变更 budget 并置回 ACTIVE）。

### 收口结论

（未收口；收口时填写。）

## 不进入循环 / 需人工拍板

以下项**不在本 GOAL 的 EC 内**，循环内不得自行决定；一旦 EC 的实现必须改动它们才能继续，
按 `escalation_triggers` 立即置 `status: BLOCKED` 并留人工决策（可选动作只限「如实登记 +
给出选项与影响面」，不含实现）：

1. **威胁建模/授权面覆盖**（GOAL-005 收口结论表第 1 项的一部分）：越权、BOLA/BFLA、业务逻辑风险
   需要独立审计射程与决策面，本循环只负责在 EC-01 里**如实写明未覆盖**，不自行开展。
2. **`artifacts/` 内未跟踪明文 token 文件的清理**（RECHECK-091 W-4）：文件从未提交
   （`git ls-files artifacts/` = 0），清理属操作者决策；本循环只登记事实。
3. **后继入口第 8 项：按声明给 adapter 接线 / `tool_pack.*` 策略**：组合根仍注入
   FakeAgentRuntime、OpenHands adapter 已建未接线，方向是「runtime 可配置」；`tool_pack.*`
   与脚本策略涉及受控出网与产品决策，可能触及 Accepted ADR 与核心安全策略。
4. **450 行硬上限贴线的持续重构**：`packages/application/run_orchestration/service.py`
   450/450 属「下一行就会红」的状态；**随改动搬代码**（每个 cycle 的 ③ 自查），
   **不单独成 EC**。需要改门禁时即 BLOCKED。
5. **依赖 pin 升级**（RECHECK-20260918-093 W-1）：`undici@5.29.0`（12 条）、
   `vite@6.3.5`（7 条）、`yaml@2.8.1`（1 条）全部有修复版本，但都在 **devDependency 链**上，
   升级属上游 pin 变更 ⇒ 命中 `escalation_triggers`，由用户/ADR 拍板。**不得**读作
   「依赖面无风险」。
6. **hook 侧 L3 门修复**（RECHECK-20260918-093 W-2）：根因是插件检测层（semgrep 1.136.0）未安装，
   修复命令见 `docs/audits/MIMOSA_POST_CLOSURE_AUDIT_20260918.md §3.3`；但装上后
   `MIMOSA_GIT_GATE_MODE=graded` 的 medium 会**交互式询问**，可能挡住无人值守提交 ⇒
   修与不修都是**安全策略决定**，留人工。

**既有口径（照抄 GOAL-005 收口结论第 5 项）**：收口扫的覆盖缺口
（`threatModel`/`findingDiscovery` partial）⇒ 静态扫描不给出授权面结论；扫描
`verdictEffect=none`，**不得**读作「项目安全」；扫描 coverage inconclusive 同样
**不得**读作项目安全。本 GOAL 的任何 EC PASS 也不构成整体安全结论。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 建档（本文件；driver=client-goal / owner=root-agent） | 本次建档提交 | 待记（governance validate 绿 + m0 + 建档 CI） | 待记 | — | EC-01…EC-06 全 PENDING | cycle 1 = EC-01（PG 两读快照一致性） |

## 状态历史

- 2026-09-18 建档：由 GOAL-20260918-005「终止与收口 · 收口结论（2026-09-18）」的
  恢复条件（用户新建承接 GOAL）建立（用户 goal 模式指令：承接 GOAL-005 收口登记的残留项
  并自动化循环推进、无需逐轮确认）；`status: ACTIVE`；EC-01…EC-06 全 PENDING；
  GOAL-005 / GOAL-004（ACHIEVED）与 GOAL-003（BLOCKED）保持只读。
