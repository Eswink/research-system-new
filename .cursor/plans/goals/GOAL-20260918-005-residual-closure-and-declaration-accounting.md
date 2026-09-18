---
id: GOAL-20260918-005
slug: residual-closure-and-declaration-accounting
title: 残留收口与声明清账：安全审计残留复核、同形补偿入口、未消费声明、时钟风险、读面语义边界、历史行可追溯
status: ACHIEVED
created_at: 2026-09-18
updated_at: 2026-09-18
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-18 用户会话指令（goal 模式）：**新建承接 GOAL-005**，把 GOAL-20260917-004
    收口时如实登记、但未随收口通过的长程项（「终止与收口 · 收口结论（2026-09-17，cycle 9）」
    9 类表 + 「后继入口」①②③ + RECHECK-091/092 的 W 列表）按优先级做成可独立验收的 EC，
    之后由本驱动**自动化循环推进、无需逐轮确认**。承接关系 = GOAL-004 收口结论表的
    「后继 GOAL 的入口」建议优先级：① 安全审计残留的联网复核与干净 checkout 重扫、
    ② 同形未修入口 `resume_after_approval`、③ 声明未消费项清账（`on_validation_failure` /
    `lease_ttl_seconds`），并按同一表补齐 ④ 时钟/时序风险 ⑤ 读面语义边界 ⑥ 历史行可追溯。
    GOAL-004 保持 ACHIEVED、GOAL-003 保持 BLOCKED：**两者只读，本 GOAL 不修改它们**
    （如需指名，只允许在对方文件追加一行事实更正；本 GOAL 当前不需要）。
    push-to-main-for-CI 授权沿用 GOAL-001/002/003/004 的批准口径：**只推 main、不 force、
    不重写历史、不推旁支触发 CI**；push 前 `git pull --ff-only origin main`（必要时
    --rebase，始终不 force）。循环预算与纪律以本文件 frontmatter 为准（客户端自带的
    迭代/重试/超时上限一律让位于此）。
objective: >
  把 GOAL-004 收口时如实登记的长程项从「已登记的缺口」变成「有终态结论的事实」：
  安全审计的两条未决（依赖 advisory 无署名、hook 侧 `scanner_enobufs`）拿到可复核结论或
  可复现配方、并在干净 checkout 上取得新的封印终态；`resume_after_approval` 与
  `resume_paused` 同判据地做失败补偿；`on_validation_failure` 与
  `ClaimRequest.lease_ttl_seconds` 两条「声明了没人读」清账（要么给真实消费者、要么移除并
  写明）；注入时钟的 PG 用例逐个判定「安全（写明为何不依赖墙钟）」或「修复」；
  `dispatch_ownership` 的列表 N+1 与 PG 两读快照一致性至少收口一项、Fake 无过期语义与
  `WORKER_CLAIM` 覆盖范围写进同源文档；旧 run 无冻结正文、旧 `manifest.frozen` 事件无
  `semantic_digest` 两条历史行缺口给出三选一的可追溯处置。**全程不删测试、不改门禁、
  不以「未观测到失败」或「扫描没报问题」充当 PASS。**
exit_criteria:
  - id: EC-01
    criterion: >-
      安全审计残留的可复核复核（收口结论表第 1 项 / RECHECK-091 W-1…W-5）：① 依赖
      advisory 拿到**署名与结论**——密封产物只给了「1 包命中 1 条」，本 EC 要求联网复核后
      记录**哪个包、哪个版本、什么 advisory、结论是什么、来源 URL/查询命令与时间**；
      联网不可用 ⇒ 记录不可用证据（命令 + 原文错误）并如实标「仍不可判定」，
      **不得**读作「无已知漏洞」。② 在**干净 checkout**（`git worktree`/`git archive`
      导出到仓库外目录，只含 tracked 内容）上重跑密封深扫，取得 scanId/seal 与逐条处置，
      使扫描输入不再是「仓库 + gitignored 工作树内容」的混合体。③ hook 侧
      `scanner_enobufs` 先**复现并定位根因**；不可复现 ⇒ 给出**可复现配方 + 人工步骤
      清单**。④ 未覆盖范围（威胁建模/授权面、业务逻辑、动态渗透）必须写明。
    verify: >-
      终态文档（`docs/audits/` 下新记录）：advisory 段含包名/版本/advisory 标识/结论/
      来源；干净 checkout 扫描段含导出命令、扫描根路径、scanId/seal、逐条处置表
      （每条：结论/依据/处置）；enobufs 段含复现命令与原始输出（或人工步骤清单）；
      未覆盖范围段。**反证**：把 advisory 查询换成「复核无问题」的空话 ⇒ 判 FAIL；
      把扫描输入换成含 `scratch/`/`artifacts/` 的路径 ⇒ 判 FAIL（判据落在「扫描根 =
      仅 tracked 导出目录」这一可查事实上，不落在「扫描没报问题」上）。
    status: PASS
  - id: EC-02
    criterion: >-
      `resume_after_approval` 同形未补偿入口（收口结论表第 2 项 / RECHECK-090 W-1）：
      审批通过后的续跑与 `resume_paused` **同判据**——失败即补偿（不放任上下文被 pop 后
      静默丢掉）、补偿可观测（失败原因落到 canonical 事实/事件链，读面能判）、可重入
      （撤掉故障后同一入口能真的续起来）、且两条入口（API 审批端点 / 其它驱动）语义一致
      或在文档写明有意差异。
    verify: >-
      用例（真 SQLite + 注入时钟）：注入 `resume_after_approval` 失败 ⇒ run 不停在
      「上下文已丢但仍声称等待审批」的不一致态，状态与失败原因可从 canonical 读到；
      重入用例：补偿后再次审批续跑成功；**反证：去掉补偿 ⇒ 对应用例变红**；
      受影响套件 + m0 绿。
    status: PASS
  - id: EC-03
    criterion: >-
      声明未消费项清账（收口结论表第 3 项 / RECHECK-086 W-1 + RECHECK-089 W-1）：
      `on_validation_failure` 与 `ClaimRequest.lease_ttl_seconds` **逐条二选一处置**——
      要么给出**真实消费者**（读该声明并按它行事，行为可被用例判定），要么从**契约与文档
      移除并写明**（说明为何不提供该能力）；两条都不得只改注释/文案充数。
    verify: >-
      **反向搜索判据**：处置后全树搜索该名字，命中的每一处要么是「真实读取点 + 用例」，
      要么是「已移除/明确不提供」的说明；`ClaimRequest` 取租路径用例证明请求级 TTL 生效
      （或该字段已不在 port 上）；`on_validation_failure` 要么有消费者用例（声明前后行为
      可判定地不同），要么已从示例契约/文档移除且 `unhonored` 视图不再列它；
      词表/契约快照（OpenAPI）与文档同源收敛；受影响套件 + m0 绿。
    status: PASS
  - id: EC-04
    criterion: >-
      时钟/时序风险收口（收口结论表第 9 项 / RECHECK-084 W-5）：对 `tests/postgres/`
      下**所有注入时钟的用例文件**逐个给出判定——「安全」（写明为何不依赖墙钟：例如该文件
      没有任何时钟敏感列经 SQL 时钟写入、断言只比较注入时钟推进后的相对量）或「修复」
      （夹具改用引擎时钟）；**不得**以「未观测到失败」作为终态判据。
    verify: >-
      判定表（新记录或实例文档）：每文件一行，含**文件路径 / 判定 / 结构依据**；
      结构依据必须是可复核的代码事实（如「该文件不出现 SQL 时钟函数」「该文件不读
      `datetime.now`/`time.time`」），不是「跑过一次没红」；修复项给出反证（改回墙钟 ⇒
      用例红或结构判据红）；枚举脚本可复跑（枚举结果 = 判定表行数）。
    status: PASS
  - id: EC-05
    criterion: >-
      读面语义边界（收口结论表第 4 项 / RECHECK-089 W-2…W-6）：**至少收口一项**——
      ① `GET /projects/{id}/runs` 列表路径的 `dispatch_ownership` **N+1**（每条 run 两次
      SQL）改成批量读面（一次读多 run）；或 ② PG 实现里「重排 + 租约」两次查询**不承诺
      快照一致**，改成单次快照一致的查询（或等价的事务内一致读）。另外两条**写进同源文档**
      （`docs/api/CONTROL_PLANE_API.md`）：Fake 实现**无过期语义**（「活」= 仍在租约表里，
      不是「租约新鲜」）、`WORKER_CLAIM` **也覆盖控制面自持租约**（`worker_id=None`）。
    verify: >-
      结构判据 + 用例：N+1 收口 ⇒ 结构判据（列表路径不再逐 run 调 `dispatch_ownership`）
      + 用例证明批量读面与逐 run 读**同判**（含 `dispatch=None`/三态边界，先钉住读面真的
      答了）；或 PG 快照一致性 ⇒ 结构判据（两读在同一快照/同一语句内）+ 并发用例
      （反证：拆回两次读 ⇒ 用例红）；文档两面同源（`CONTROL_PLANE_API.md` 内含 Fake 与
      `WORKER_CLAIM` 两条边界）；受影响套件（含 PG parity）+ m0 绿。
    status: PASS
  - id: EC-06
    criterion: >-
      历史行可追溯（收口结论表第 6 项 / RECHECK-084 W-2 + RECHECK-087 W-1）：旧 run 无
      冻结正文、旧 `manifest.frozen` 事件无 `semantic_digest` 两条缺口，**三选一**并写明
      后果——a) 迁移/回填（重算可回填的事实）；b) 一等事实 + 读面写明（读面能正面回答
      「这条是历史行、缺哪条事实、此路不通」而不是含糊的 None）；c) 明确记为不可回填并
      给出拒绝路径点名。判据要求「不含糊」：历史行与当前行在**读面可区分**，拒绝原因
      **点名缺的是哪条事实**，且该判定有用例/结构判据支撑。
    verify: >-
      结构判据（读面字段或拒绝原因分支）+ 用例（构造一条历史形态的 run 行/事件 ⇒ 读面
      如实回答、重建拒绝原因点名）；反证：去掉该判定 ⇒ 用例红；文档同源
      （`EVENT_MODEL.md` / `CONTROL_PLANE_API.md` 写明历史行口径）；受影响套件 + m0 绿。
    status: PASS
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
child_plans:
  - .cursor/plans/tasks/PLAN-20260918-093-security-audit-residual-recheck.md
  - .cursor/plans/tasks/PLAN-20260918-094-approval-resume-failure-compensation.md
  - .cursor/plans/tasks/PLAN-20260918-095-declaration-clearing.md
  - .cursor/plans/tasks/PLAN-20260918-096-clock-injection-adjudication.md
  - .cursor/plans/tasks/PLAN-20260918-097-dispatch-list-batch-read.md
  - .cursor/plans/tasks/PLAN-20260918-098-rebuild-readiness-read-surface.md
  - .cursor/plans/tasks/PLAN-20260918-099-goal-005-closeout-recheck.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260918-099-goal-005-closeout-recheck.md
memory_entries:
  - MEM-20260918-067
  - MEM-20260918-068
  - MEM-20260918-069
  - MEM-20260918-070
  - MEM-20260918-071
  - MEM-20260918-072
---

# GOAL-20260918-005 — 残留收口与声明清账（自迭代循环）

本文件是 **GOAL 记录**（位于 `PLAN-*` 之上的编排层），格式契约见本目录 `README.md`；
工程事实、验收与复检仍由 PLAN/RECHECK/MEM 体系承载（单一流程权威：
`.cursor/rules/20-plan-memory-recheck.mdc`）。GOAL 只做编排与记账。

## 目标与退出标准

GOAL-004 收口时把 9 类「仍未处理的长程项」如实登记进「终止与收口 · 收口结论」，并把
后继入口按优先级排序（① 安全审计残留的联网复核与干净 checkout 重扫；② 同形未修入口
`resume_after_approval`；③ 声明未消费项清账）。本 GOAL 承接其中**可独立验收的六项**，
逐条做成 EC；收口结论表里**依赖人工拍板**的项（威胁建模/授权面覆盖、`artifacts/` 内明文
token 清理、后继入口第 8 项、450 行硬上限的持续搬迁）按契约写进「不进入循环 / 需人工
拍板」节，**不伪装成 EC**。

| EC | 主题 | 来源 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 安全审计残留复核（advisory 署名 + 干净 checkout 重扫 + `scanner_enobufs` 根因/配方） | 收口结论表 1 / RECHECK-091 W-1…W-5 | **PASS**（RECHECK-20260918-093） |
| EC-02 | `resume_after_approval` 同形未补偿入口 | 收口结论表 2 / RECHECK-090 W-1 | **PASS**（RECHECK-20260918-094） |
| EC-03 | 声明未消费项清账（`on_validation_failure` / `ClaimRequest.lease_ttl_seconds`） | 收口结论表 3 / RECHECK-086 W-1 + 089 W-1 | **PASS**（RECHECK-20260918-095） |
| EC-04 | 时钟/时序风险逐个收口（不做「未观测到失败」式收尾） | 收口结论表 9 / RECHECK-084 W-5 | **PASS**（RECHECK-20260918-096） |
| EC-05 | 读面语义边界（列表 N+1 或 PG 两读快照至少一项 + Fake/`WORKER_CLAIM` 同源文档） | 收口结论表 4 / RECHECK-089 W-2…W-6 | **PASS**（RECHECK-20260918-097，做 ①） |
| EC-06 | 历史行可追溯（旧 run 无正文 / 旧事件无 `semantic_digest`，三选一） | 收口结论表 6 / RECHECK-084 W-2 + 087 W-1 | **PASS**（RECHECK-20260918-098，做 (b)） |

**优先级**：EC-01 → EC-02 → EC-03 → EC-04 → EC-05 → EC-06（derive 取 EC 表首个 PENDING；
若某 EC 本轮**部分交付**，其「下一轮输入」优先于表序）。

**不在本 GOAL 的 EC 内**（GOAL-004 收口结论表其余项，登记为背景，不伪装成已收口）：
第 5 项（失败 run 重建后的执行期结局）、第 7 项（补偿的诚实边界：守护线程静默降级、
失败无任务级归因、进程内暂停上下文不复活、API 仍 200）、第 8 项（450 行贴线，见
「不进入循环」节）。这些**不因本 GOAL 存在而被宣称已解决**。

### EC-01 判定细则（安全审计残留复核）

- **禁止的 PASS 依据**：「扫描没报问题」「复核过了没问题」「未发现异常」。PASS 只认
  **可复核的署名与封印**：advisory 的包名/advisory 标识/结论/来源，扫描的 scanId/seal。
- **干净 checkout 的硬判据**：导出目录只含 tracked 内容（`git ls-files` 与导出树一致），
  扫描根 = 该目录；扫描产物里不得出现 `scratch/`、`artifacts/` 等 gitignored 路径。
- **联网不可用**：如实记「仍不可判定」+ 复现命令 + 原始错误输出，EC 保持 PENDING
  （按「未实跑不得记 PASS」）；**不得**因「查不到」而写成「没有已知漏洞」。
- **hook 侧 `scanner_enobufs`**：先在**当前树**复现（同一 commit 前后各一次），命中则给
  根因证据（hook 原始输出、`scratch/goal4-mimosa-enobufs.md` 的历程对照、可复现命令）；
  不可复现 ⇒ 保留「不可复现」的诚实结论并给可复现配方 + 人工步骤清单。
- **未覆盖范围**必须写明：威胁建模、授权面（越权/BOLA/BFLA）、业务逻辑、动态渗透不在
  静态扫描射程；产品测试提供的对应证据不能代表独立审计结论。

### EC-02 判定细则（对标 GOAL-004 EC-06 的判据形态）

GOAL-004 EC-06 的判据形状是：**失败即补偿 + 补偿可观测 + 可重入 + 反证（去掉补偿 ⇒
用例红）**。本 EC 逐字沿用该形状，只换入口（审批通过后的续跑，`resume_after_approval`）。
「补偿」的语义以当前 canonical 状态机允许的落点为准（例如放回 `WAITING_FOR_APPROVAL` 或
等价可判定态），**不新增无需的状态**；若实现上发现必须新增 canonical 状态/字段，先按
`escalation_triggers` 判是否触及 Canonical State 边界。

### EC-03 判定细则（清账，二选一）

两条声明**各自独立判定**（可以一条给消费者、另一条移除）：

- `ClaimRequest.lease_ttl_seconds`：取租路径读请求里的值（默认仍 300），或用例证明
  请求级 TTL 生效；若判定「不提供」，则从 port 与三个实现的构造参数中移除写明。
- `on_validation_failure`：给真实消费者（例如验收门失败后按声明二次处置任务行）**或**
  从示例契约 + 文档移除并写明原因；`unhonored` 视图必须与实际声明面一致。
- **反证**：处置后必须有 **反向搜索**（全树按名字）证据，且**至少有 1 条用例**证明该
  处置不是文案改动（消费者 ⇒ 行为可判定地不同；移除 ⇒ 该名字在声明面消失且用例钉住）。

### EC-04 判定细则（时钟/时序风险）

- 枚举面 = `tests/postgres/` 下**所有注入时钟的用例文件**（以脚本枚举为判据，不靠记忆；
  RECHECK-084 W-5 记的是 12 个文件、当时只修了 1 个）。
- 每个文件的判定只能是「安全」或「修复」，且必须带**结构依据**：例如「该文件不出现
  时钟敏感列由 SQL 时钟写入」「该文件不读墙钟（`datetime.now` / `time.time` /
  `CURRENT_TIMESTAMP`）」。**「跑一次没红」不是依据**。
- 修复项：夹具改用引擎时钟（与 RECHECK-084 的修复同形），并给反证。

### EC-05 判定细则（读面语义边界，至少一项）

① 与 ② **至少完成一项**（完成两项不额外加分，但都完成则都写进验收）：

- ① **N+1**：`GET /projects/{id}/runs` 的列表路径不再对每条 run 各做一次
  `dispatch_ownership`；批量读面与逐 run 读**同判**（含无派发方、`WORKER_CLAIM`、
  `RETRY_DISPATCH` 三态与 `dispatch=None` 边界）。
- ② **PG 两读快照**：重排与租约两次查询落在**同一快照/同一语句**；并发写期间不得出现
  「重排已前移、租约仍是旧值」的撕裂读（反证：拆回两次读 ⇒ 用例红）。
- **文档面**（必做，与上面哪项无关）：`docs/api/CONTROL_PLANE_API.md` 写明 Fake 无过期
  语义、`WORKER_CLAIM` 也覆盖控制面自持租约。

### EC-06 判定细则（历史行可追溯，三选一）

- a) **迁移/回填**（若选此项，注意 `escalation_triggers` 的「破坏性数据迁移」——仅当
  非破坏、可重入、可回退时才在循环内做，否则 BLOCKED）；
- b) **一等事实 + 读面写明**：读面能正面回答「这是历史行、缺的是冻结正文 / 语义 digest、
  重建此路不通」；拒绝原因点名事实；
- c) **明确不可回填**：给出判定与拒绝路径点名，并在同源文档写明。
- 三条都要求：历史行与当前行**在读面可区分**（不是一律 None）、判定有**用例或结构判据**。

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

当前续点：**本 GOAL 已收口**（`status: ACHIEVED`，2026-09-18）。EC-01…EC-06 全 PASS，收口复检 = RECHECK-20260918-099（PASS_WITH_WARNINGS）且 `latest_recheck` 指向它；收口结论见「终止与收口 · 收口结论」。**循环到此为止**：再触发入口协议只在`status != ACTIVE` 分支输出终止摘要，不再做改动。恢复条件 = 用户新建承接 GOAL 或显式变更 budget 并置回 ACTIVE（残余清单见收口结论）。

## 驱动

驱动无关（README「驱动适配」）：本实例由客户端 goal 模式驱动（每轮触发 = 一次入口
协议），亦可换会话/定时驱动；仅当 `status=ACTIVE` 时推进。同一时刻仅一个驱动推进。

## 单 cycle SOP

按 README ①~⑦ 执行。本实例附加约定：

- ① derive 主题顺序：EC 表首个 PENDING；若上一 cycle 部分交付，以其「下一轮输入」为准。
  子 PLAN 必须独立可验收、独立 RECHECK（`.cursor/plans/rechecks/`），frontmatter 带
  `parent_goal: GOAL-20260918-005` 并投影 ALL_PLAN。
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
  或命中 `escalation_triggers`（含威胁建模/授权面与受控出网类决策）。写 BLOCKED 记录
  （原因/EC 状态表/收口复检/安全扫描处置/恢复条件/仍未处理的长程项），恢复条件由用户拍板。
- **ABORTED**：用户显式终止本目标。

收口时必须把「仍未处理的长程项」如实登记为后继入口（不隐藏缺口），并给出恢复条件
（新建承接 GOAL 或显式变更 budget 并置回 ACTIVE）。

### 收口结论（2026-09-18，cycle 7 = 收口）

**ACHIEVED**。六条 EC 全 PASS，每条都有实跑证据与独立复检；收口复检 = RECHECK-20260918-099
（`latest_recheck` 指向它，result `PASS_WITH_WARNINGS`），门禁全绿（m0 **23/23**，全量 pytest
**3932 passed / 10 skipped**；web 六门；规模/治理门禁），收口 head 取得**新的干净 checkout
封印**（`sha256:c0202d05…`，25 条发现逐类处置）。

| EC | 主题 | 终态 | 子 PLAN / RECHECK |
| --- | --- | --- | --- |
| EC-01 | 安全审计残留复核（advisory 署名 + 干净 checkout 重扫 + `scanner_enobufs` 根因/配方） | **PASS** | PLAN-093 / RECHECK-093（PASS_WITH_WARNINGS） |
| EC-02 | `resume_after_approval` 同形未补偿入口 | **PASS** | PLAN-094 / RECHECK-094（PASS） |
| EC-03 | 声明未消费项清账（`on_validation_failure` / `ClaimRequest.lease_ttl_seconds`） | **PASS** | PLAN-095 / RECHECK-095（PASS_WITH_WARNINGS） |
| EC-04 | 时钟/时序风险逐个判定（12 个注入时钟文件） | **PASS** | PLAN-096 / RECHECK-096（PASS_WITH_WARNINGS） |
| EC-05 | 读面语义边界（做 ① 列表 N+1 批量读 + ② 的诚实边界登记） | **PASS** | PLAN-097 / RECHECK-097（PASS_WITH_WARNINGS） |
| EC-06 | 历史行可追溯（做 (b) 一等事实 + 读面点名缺失事实） | **PASS** | PLAN-098 / RECHECK-098（PASS_WITH_WARNINGS） |

**仍未处理的长程项（如实登记，不因收口而消失）**：

1. **人工决策面六项**（本文件「不进入循环 / 需人工拍板」）：威胁建模/授权面（BOLA/BFLA）覆盖、
   `artifacts/` 内未跟踪明文 token 清理、后继入口第 8 项（按声明给 adapter 接线 / `tool_pack.*`
   策略）、450 行硬上限的持续搬迁（现由「随改动搬代码」纪律兜住）、依赖 pin 升级
   （`undici@5.29.0` 12 / `vite@6.3.5` 7 / `yaml@2.8.1` 1，全部有修复版本）、hook 侧 L3 门修复
   （semgrep 检测层未装；装上后 graded 会交互询问）。
2. **EC-05 ②**（PG 两读快照一致性）未做：批量读消掉的是 N+1 不是撕裂读；
   `dispatch_ownership` 的两条 SQL 之间不承诺快照一致（port docstring / `PORTS.md` / RECHECK-097 W-1）。
3. **EC-03 的 `DEAD_LETTER` 消费**未做：验收门跑在 durable `SUCCEEDED` 之后，按声明处置需要
   改写终态行 ⇒ canonical 状态机 + ADR 边界（RECHECK-095 W-2）。
4. **各 cycle 的 W 列表**（RECHECK-093…098）继续有效：依赖 pin 与 hook 门、补偿的诚实边界、
   时钟断言的调度依赖与真墙钟矩阵、批量读无分页上限 / Fake 弱同判、重建读面不预测结果 /
   前端未消费 `rebuild`。
5. **收口扫的覆盖缺口**：`threatModel`/`findingDiscovery` partial ⇒ 静态扫描不给出授权面结论；
   扫描 `verdictEffect=none`，**不得**读作"项目安全"。

**恢复条件**：用户新建承接 GOAL（把上表第 1-3 项按优先级做成 EC），或显式变更本文件
`budget` 并置回 `ACTIVE`。本文件保持 ACHIEVED，**只读**（如需事实更正，按 README 追加）。

## 不进入循环 / 需人工拍板

以下项**不在本 GOAL 的 EC 内**，循环内不得自行决定；一旦 EC 的实现必须改动它们才能继续，
按 `escalation_triggers` 立即置 `status: BLOCKED` 并留人工决策（可选动作只限「如实登记 +
给出选项与影响面」，不含实现）：

1. **威胁建模/授权面覆盖**（收口结论表第 1 项的一部分）：越权、BOLA/BFLA、业务逻辑风险
   需要独立审计射程与决策面，本循环只负责在 EC-01 里**如实写明未覆盖**，不自行开展。
2. **`artifacts/` 内未跟踪明文 token 文件的清理**（RECHECK-091 W-4）：文件从未提交
   （`git ls-files artifacts/` = 0），清理属操作者决策；本循环只登记事实。
3. **后继入口第 8 项：按声明给 adapter 接线 / `tool_pack.*` 策略**：组合根仍注入
   FakeAgentRuntime、OpenHands adapter 已建未接线，方向是「runtime 可配置」；`tool_pack.*`
   与脚本策略涉及受控出网与产品决策，可能触及 Accepted ADR 与核心安全策略。
4. **450 行硬上限贴线的持续重构**：`packages/application/run_orchestration/service.py`
   450/450 属「下一行就会红」的状态；**随改动搬代码**（每个 cycle 的 ③ 自查），
   **不单独成 EC**。需要改门禁时即 BLOCKED。
5. **依赖 pin 升级**（cycle 1 新登记，RECHECK-20260918-093 W-1）：`undici@5.29.0`（12 条）、
   `vite@6.3.5`（7 条）、`yaml@2.8.1`（1 条）全部有修复版本，但都在 **devDependency 链**上，
   升级属上游 pin 变更 ⇒ 命中 `escalation_triggers`，由用户/ADR 拍板。**不得**读作
   「依赖面无风险」。
6. **hook 侧 L3 门修复**（cycle 1 新登记，W-2）：根因是插件检测层（semgrep 1.136.0）未安装，
   修复命令见 `docs/audits/MIMOSA_POST_CLOSURE_AUDIT_20260918.md §3.3`；但装上后
   `MIMOSA_GIT_GATE_MODE=graded` 的 medium 会**交互式询问**，可能挡住无人值守提交 ⇒
   修与不修都是**安全策略决定**，留人工。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 建档（本文件；driver=client-goal / owner=root-agent） | `6007b01` | `.cursor/skills/governance-check/scripts/validate.py` 绿（本机实跑） | run **35308775303**（#151，`6007b01`）：**failure**——仅 `quality-windows-latest` 红，`python/tests` 里 1 条**既有**并发用例 `OperationalError: database is locked`（12 线程并发写，4/96 次写越过 5 s 预算；其余五 job success） | 该签名此前从未出现（非已知 flake 配方）⇒ 按「产品测试失败」处置：定位为**控制面 SQLite 的 busy_timeout 预算不足**（实测：同一把锁被持 8 s 时，旧预算 5.53 s 即失败、新预算等待 8.02 s 成功）；修复提交 `ef0d722`（`adapters/sqlite/db.py` 的 `BUSY_TIMEOUT_MS` 5 s → 30 s，**断言未改**）→ run **35311496737 六个 job 全 success** | EC-01…EC-06 全 PENDING | cycle 1 = EC-01（安全审计残留复核） |
| 1 | PLAN-20260918-093（EC-01：安全审计残留复核；driver=client-goal / owner=root-agent） | `3eaa19a`（OSV 探针 + 证据 JSON）、`07fab27`（AST 判据探针）、`04e8c54`（终态记录 + `docs/INDEX.md`）、`e3f0ee4`（PLAN/RECHECK/MEM/ALL_PLAN）、`ef0d722`（CI 修复：SQLite busy timeout） | 治理 validate 绿；定向：`tests/adapters/sqlite` **161 passed**（3.12，含并发池用例）、`tests/tooling/test_python_source_limits.py` **930 passed**、`tests/application/protocol_authoring/test_draft_service.py` **13 passed**；探针自证 `probe_dynamic_sql_forms.py --selftest` **8/8 ok**；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3896 passed / 10 skipped**，561.60s） | run **35311496737**（#152，`ef0d722`）：**六个 job 全 success**（collector-quality / container-quality / quality-windows-latest / quality-ubuntu-latest / eval-gate / console-frontend，runner_id 非 0，无重跑） | 首跑 CI 红 1 条（并发池用例）⇒ **修产品**（busy timeout）而非改断言；**方法学更正**：上一轮「产品树动态 SQL 零命中（grep）」被 AST 判据更正为「22 处构造、逐处核对为常量/固定记号」（结论未变、依据升级） | EC-01 **PASS**（RECHECK-20260918-093 = PASS_WITH_WARNINGS，W-1…W-5）；EC-02…EC-06 PENDING | cycle 2 = EC-02（`resume_after_approval` 同形未补偿入口） |
| 2 | PLAN-20260918-094（EC-02：审批通过后续跑失败的补偿；driver=client-goal / owner=root-agent） | `55757a3`（补偿接线 + 4 条用例 + `CONTROL_PLANE_API.md`）、`9af9c18`（PLAN/RECHECK/MEM/ALL_PLAN + 新文件 ruff format） | 治理 validate 绿；**新用例「先纠正了上游告警的错描述」**：W-1 说失败停在 `WAITING_FOR_APPROVAL`，实测 `decide` 先落 `RUNNING` ⇒ 真实缺口是**悬空 RUNNING**；定向（DSN pin）`tests/api+application+contracts+domain+e2e` **1997 passed / 4 skipped**（271.89s）；新用例 **4 passed**、与既有补偿/审批用例合并 **18 passed**；**反证**：补偿换成 `raise exc` ⇒ **2 failed / 2 passed**（红的正是断言补偿的两条）；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3901 passed / 10 skipped**，558.25s；首跑红 1 处 = 新增测试文件 ruff format ⇒ 格式化后复跑全绿，未改断言） | run **35314730222**（#155，`9af9c18`）：**六个 job 全 success**（collector-quality / console-frontend / quality-windows-latest / eval-gate / container-quality / quality-ubuntu-latest，无重跑） | m0 首跑 `python/format-check` 红（新文件未格式化）⇒ `ruff format` 后全绿；补偿走**既有域迁移**（`RUNNING --PAUSE--> PAUSED`）⇒ 未新增 canonical 状态，不触 ADR 边界 | EC-02 **PASS**（RECHECK-20260918-094 = **PASS**，W-1…W-4 为沿用 EC-06 的诚实边界）；EC-03…EC-06 PENDING | cycle 3 = EC-03（声明未消费项清账：`on_validation_failure` / `ClaimRequest.lease_ttl_seconds`） |
| 3 | PLAN-20260918-095（EC-03：声明未消费项清账；driver=client-goal / owner=root-agent） | `053301a`（port 移除请求级 TTL + 示例契约清账 + 两件判据用例 + 四处文档同源）、本次回写提交（PLAN/RECHECK/MEM/ALL_PLAN/INDEX + 本文件） | 治理 validate 绿；**反向搜索（判据）**：`lease_ttl_seconds` 读者 0（三实现只读引擎级 `self._lease_ttl`）、19 个 `ClaimRequest(...)` 构造点无一传它；`on_validation_failure` 只进 `unhonored`；定向（DSN pin）`tests/api+adapters+e2e+contracts+application+domain+loaders` **2474 passed / 7 skipped**（355.46s）；**反证两跑**：① 把 `lease_ttl_seconds` 放回 `ClaimRequest` ⇒ **1 failed / 18 passed / 9 skipped**、② 把 `on_validation_failure` 放回示例契约 ⇒ **1 failed / 21 passed**（各只红对应的钉住用例）；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3903 passed / 10 skipped**，479.83s；首跑红 1 处 = RECHECK 缺 `## 结论` 章节 ⇒ 补齐后复跑全绿） | run **35321234815**（#157，`43933a1`）：**六个 job 全 success**（runner_id 非 0、无重跑） | m0 首跑 `framework/validate` 红（RECHECK 缺章节，记录未写完的中间态）⇒ 补章节后 23/23；EC-03 原文「从 port 与三个实现的构造参数中移除写明」按「移除**请求级**声明 + 写明**引擎级**位置」判读——引擎级 `lease_ttl_seconds` **是被读的**（claim/`renew_lease`/回收共用），删它会砍真实能力（RECHECK W-2） | EC-03 **PASS**（RECHECK-20260918-095 = PASS_WITH_WARNINGS，W-1…W-4）；EC-04…EC-06 PENDING | cycle 4 = EC-04（时钟/时序风险逐个判定；枚举面 = 12 个注入时钟的 PG 用例文件） |
| 4 | PLAN-20260918-096（EC-04：时钟/时序风险逐个判定；driver=client-goal / owner=root-agent） | 本次回写提交（只读探针 + `PORTS.md` 时钟纪律段 + PLAN/RECHECK/MEM/ALL_PLAN/GOAL） | 治理 validate 绿；**枚举以脚本为判据**（`tools/probes/enumerate_clock_injected_pg_tests.py`，AST + 行扫描，只读）：27 个 PG 用例文件 / **12 个注入时钟** / **0 处墙钟读** / 6 个含"无时钟构造点"（逐用例核对）；**逐文件判定 12/12「安全」**，依据 = 写入路径（`db_time_expr`/`server_now` 是写时钟敏感列与做比较的**同一个源**；全树唯一无条件 `now()` 的 SQL 是 `outbox_events.created_at`，断言只按事件类型成员）；`grep now() tests/postgres/*.py` 只剩一行文档字符串（与 W-5「修复后为零」一致）；定向 `tests/postgres` **91 passed**（27.92s）；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3903 passed / 10 skipped**，505.98s） | run **35322946077**（#158，`3358b2e`）：**六个 job 全 success**（runner_id 非 0、无重跑） | 无「修复」项 ⇒ 无"去掉修复"式反证；判定的判别力来自**结构可复核**（如 `next_retry_at == START+3600` ← `projections.retry_schedule(server_now)`，改回 SQL `now()` 该断言即红） | EC-04 **PASS**（RECHECK-20260918-096 = PASS_WITH_WARNINGS，W-1…W-4：并发条数断言的调度依赖、parity 无时钟分支无调用点、WorkerRegistry 生产用 DB 时钟、真墙钟矩阵有意在外）；EC-05/EC-06 PENDING | cycle 5 = EC-05（读面语义边界：N+1 或 PG 两读快照至少一项 + Fake/`WORKER_CLAIM` 同源文档） |
| 5 | PLAN-20260918-097（EC-05 ①：列表路径的批量派发读面；driver=client-goal / owner=root-agent） | `5fce188`（port `dispatch_ownership_many` + 三实现共用装配 + 控制面列表改批量读 + 用例与反证 + 两处文档 + OpenAPI 快照再生成）、本次回写提交（PLAN/RECHECK/MEM/ALL_PLAN/INDEX + 本文件） | 治理 validate 绿；**先确认 N+1 真实存在**（`list_runs` → `_detail_dto` → 每条一次 `dispatch_ownership`，每次两条 SQL ⇒ `2N`）；**同判是结构性的**：单 run 读改成"批量读的一条"（三实现共用 `_dispatch_ownerships`/`_ownership_of`），契约用例三实现断言"逐字相等"（含未知 run ⇒ `NONE` 条目、空入参 ⇒ 空 dict）；**N+1 哨兵**用 adapter call log（列表后批量 +1、逐 run 零次）；**反证实跑**：列表路径改回逐 run 读 ⇒ `-k list` **1 failed / 3 passed / 7 deselected**（`assert 0 == (0 + 1)`）；定向（DSN pin）`tests/api+contracts+adapters/sqlite+postgres+adapters` **1425 passed / 5 skipped**（235.04s）；返工后复跑 `tests/api+contracts+adapters/sqlite` **1053 passed / 2 skipped**；规模门禁 `test_python_source_limits` **932 passed**（PG 引擎 459 → 447 行）；过滤全走绑定参数（`json_each(?)` / `= ANY(%s)`）；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3914 passed / 10 skipped**，468.62s） | run **35330877315**（#159，`3c49638`）：**六个 job 全 success**（collector-quality / container-quality / quality-windows-latest / eval-gate / quality-ubuntu-latest / console-frontend，runner_id 非 0、无重跑） | 首轮改动后引擎里 `retry_schedule` 仍调旧别名 ⇒ 10 条红（`NameError`）⇒ **改产品代码**（改用批量投影的单条取值），**未改断言**，复跑全绿；收口门禁返工两处：① `python/product-lint` 红（新 import 未排序）⇒ 合并既有 import；② PG 引擎 459 > 450 行（规模门禁红）⇒ **搬代码**到新模块 `adapters/postgres/workflow_dispatch.py`（447 行），**未动门禁**；EC-05 ② （PG 两读快照）本轮**不做**（EC-05 允许至少一项），边界留在 port docstring / `PORTS.md` / RECHECK W-1 | EC-05 **PASS**（RECHECK-20260918-097 = PASS_WITH_WARNINGS，W-1…W-4）；EC-06 PENDING | cycle 6 = EC-06（历史行可追溯，三选一） |
| 6 | PLAN-20260918-098（EC-06 (b)：重建能力读面点名缺失事实；driver=client-goal / owner=root-agent） | `813e93c`（分类器 + 读面字段 + `/resume` 同源 + 用例与反证 + 两处文档 + OpenAPI/web 类型与夹具）、本次回写提交（PLAN/RECHECK/MEM/ALL_PLAN/INDEX + 本文件） | 治理 validate 绿；**先探明再动手**（只读勘察）：正文不入库、两种 `None` 混用、拒绝文案分散在 `run_resume`/`convergence`、`snapshot_migrate` 是 opt-in、旧事件回填分支**无用例**；交付：`rebuild_readiness.py`（纯函数分类器：四字段 ⇒ `SELF_CONTAINED`/`SOURCE_DEPENDENT`/`REFUSED` + 按**行字段名**排序的 `missing`）+ `RunDetailDto.rebuild` + `run_rebuild_view.py`；`/resume` 的两条早退与异常前缀改从分类器取（**条件与文案逐字不变**）；**反证实跑**：去掉 `manifest_semantic_digest` 判定 ⇒ **6 failed / 25 passed**，还原 ⇒ **31 passed**；**首轮踩坑并修正**：把"缺正文"前缀绑在 `SOURCE_DEPENDENT` 上会让"同时缺语义 digest"的行丢前缀（既有用例红）⇒ 分类器显式带出 `body_frozen`（**未改断言**）；定向（DSN pin）`tests/api+contracts+application+adapters+e2e` **2053 passed / 7 skipped**（322.87s）；web 六门：lint/typecheck/unit **76 passed**/build/stub e2e **83 passed**/live e2e **36 passed**；规模门禁 **935 passed**；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3932 passed / 10 skipped**，491.81s） | run **35335429653**（#161，`0cb68db`）：**六个 job 全 success**（collector-quality / quality-ubuntu-latest / console-frontend / container-quality / quality-windows-latest / eval-gate，runner_id 非 0、无重跑） | 分类器输出必须把**判过的每个事实**都带出来（`body_frozen` 是第三条不变量）；新增必填 DTO 字段会牵动三处（OpenAPI 快照 / `types.ts` / e2e 夹具）——漏夹具 typecheck 即红；`REFUSED` **不裁决**"不可回填"（opt-in 运营工具仍在） | EC-06 **PASS**（RECHECK-20260918-098 = PASS_WITH_WARNINGS，W-1…W-4）；**EC-01…EC-06 全 PASS** | GOAL 收口（独立复检 + 收口结论 + 后继入口登记） |
| 7 | PLAN-20260918-099（EC-06 之后的**收口复检**；driver=client-goal / owner=root-agent） | 本次回写提交（PLAN-20260918-099 / RECHECK-20260918-099 / ALL_PLAN + 本文件收口结论） | 治理 validate 绿（**首跑两红**：① RECHECK 的 `plan_id` 指向 GOAL ⇒ 改为指向本轮收口 PLAN；② frontmatter 的 `exit_criteria[].status` 仍 PENDING ⇒ 六条逐条改 PASS——**正文表早已 PASS、frontmatter 漏改，验证器抓住了**）；收口复检脚本 `scratch/verify_goal005_closeout.py` **56 checks 全 PASS**（交付物在树 / 判据用例在树 / 登记面一致三层）；六条 EC 判据用例合并复跑 **130 passed**（17.71s）；**干净 checkout 深扫**（`git archive HEAD` 3053 == `git ls-files` 3053，无 `scratch/`/`artifacts/`）：seal `sha256:c0202d05…`、**25 条**（1 high / 19 medium / 5 low）逐类处置，工作树对照 34 条（1/28/5）差集 = gitignored `scratch/` 探针 ⇒ **输入边界改变剖面**（与 EC-01 同一结论）；m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3932 passed / 10 skipped**，484.00s） | run **35336969637**（#162，`177b34a`）：**六个 job 全 success**（collector-quality / eval-gate / quality-ubuntu-latest / console-frontend / quality-windows-latest / container-quality，runner_id 非 0、无重跑） | ① high「不安全反序列化」= **误报**（`yaml.load(Loader=_StrictLoader)`，`_StrictLoader` 继承 `yaml.SafeLoader`，行内 `# noqa: S506` 说明理由）；② 5 low「不安全随机数」= **误报**（带种子的演示词表生成，无安全用途）；③ 19 medium「跨文件污点」= **运维诊断脚本**（`tools/probes/*`、`tools/PA1R运行演练v1.py`）与 **operator 环境变量**（`RESEARCHOS_WORKER_GPU_IMAGE` → worker GPU 镜像，部署域配置）；④ 离线 advisory 通道两次输入答案不同（工作树 1 包 / 干净 0 包）⇒ **不作依赖结论**，以 EC-01 联网查询（3 包 20 条）为准 | **EC-01…EC-06 全 PASS；GOAL 置 ACHIEVED**；残余如实登记（人工决策面六项 + EC-05 ② + `DEAD_LETTER` 消费 + 各 cycle 的 W 列表） | 无（本 GOAL 收口；恢复条件 = 用户新建承接 GOAL 或显式变更 budget 并置回 ACTIVE） |


## 状态历史

- 2026-09-18 建档：由 GOAL-20260917-004 收口结论表的「后继 GOAL 的入口」建立（用户
  goal 模式指令：新建承接 GOAL-005 并自动化循环推进、无需逐轮确认）；`status: ACTIVE`；
  EC-01…EC-06 全 PENDING；GOAL-004（ACHIEVED）与 GOAL-003（BLOCKED）保持只读。
- 2026-09-18 建档 CI（run **35308775303** = #151，head `6007b01`）：**failure**——仅
  `quality-windows-latest` 的 `python/tests` 里 1 条**既有**并发用例
  （`tests/adapters/sqlite/test_thread_local_connection.py::test_twelve_threads_write_without_lost_rows_or_interface_errors`）
  报 4 次 `OperationalError: database is locked`。该签名此前从未出现（不在已知 flake 配方里）
  ⇒ 按「产品测试失败」处置。定位过程与判据：① 本机隔离复跑 3/3 绿 + 6 CPU 压力下 6/6 绿
  （**不足以判 flake**）；② 实测 busy handler **是被遵守的**（持锁 8 s 时等待 5.53 s 后失败）
  ⇒ 缺陷边界是「5 s 预算在 12 写者并发下不够」，不是「handler 被绕过」；③ 3.12 下复跑
  同判据。修复 = 产品常量 `BUSY_TIMEOUT_MS` 5 s → 30 s（`adapters/sqlite/db.py`，PRAGMA
  字面量同步；既有用例按常量对账 ⇒ **未改任何断言**）。修复提交 `ef0d722` → 本地 m0 23/23
  （全量 pytest **3896 passed / 10 skipped**）→ run **35311496737**（#152）**六个 job 全 success**。
- 2026-09-18 cycle 1 收口：EC-01 **PASS**（PLAN-20260918-093 / RECHECK-20260918-093 =
  PASS_WITH_WARNINGS，W-1…W-5）。交付：① 干净 checkout 重扫（`git archive` 导出
  **3025 == `git ls-files` 3025**，树内无 `scratch/`/`artifacts/`；新封印
  `sha256:1e549272…`，剖面 **25** = 1/19/5，三件产物摘要逐件 OK；工作树 36 条里 19 条
  非仓库内容 findings 在干净输入上归零 ⇒ 输入边界会改变结论）；② 依赖 advisory **署名**
  （413 锁定包 ⇒ **3 包 20 条**：`undici@5.29.0` 12 / `vite@6.3.5` 7 / `yaml@2.8.1` 1，
  全在 devDependency 链，带 CVE/CVSS/修复版本；扫描器自报 182/1 与 11/0 互相矛盾 ⇒ 不作依据）；
  ③ hook 侧 `scanner_enobufs` **复现 + 根因**（2/2 次 `scanner_no_output` 790/767 ms；
  `cli.js semgrep status --json` ⇒ `installed:false` / `install_metadata_missing` ⇒ L3 门检测层
  未装）；④ 25 条 findings 逐条处置（无产品代码真实缺陷）；⑤ 方法学更正（grep → AST 结构判据）。
  **无产品代码变更**（唯一产品改动是本 cycle 的 CI 修复 `ef0d722`）；`child_plans` 增
  PLAN-20260918-093、`memory_entries` 增 MEM-20260918-067。
- 2026-09-18 cycle 1 收口提交 CI 记录：head `299ef55` → run **35312655449**（#153）
  **六个 job 全 success**（记录提交只改 `.cursor/**` 同样触发六 job，按同口径等到终态）。
- 2026-09-18 cycle 2 收口：EC-02 **PASS**（PLAN-20260918-094 / RECHECK-20260918-094 =
  **PASS**）。**先纠正上游告警描述再动手**：RECHECK-090 W-1 写「失败后 run 停在
  `WAITING_FOR_APPROVAL`」，实测 `decide` 端点先按状态机把 run 落成 `RUNNING`
  （`WAITING_FOR_APPROVAL --APPROVAL_GRANTED--> RUNNING`），`_resume_after_approval` 只捕
  `InvalidInputError` ⇒ 失败后的真实事实是**悬空 `RUNNING`**（没有执行者、`_waiting` 已被
  pop、连重入的 `PAUSED → RUNNING` 迁移也走不到）。修复 = 该分支捕获其余异常并调用
  **与 `resume_paused` 共用的** `compensate_failed_resume`（既有域迁移 `RUNNING --PAUSE-->
  PAUSED` + `run.resume_failed` 事件），**未新增 canonical 状态/迁移/事件类型**。
  判据：新用例 4 条（失败 ⇒ store 里是 `PAUSED`；事件三个键；补偿后可重入
  `continuation=RESUMED`；正常路径与竞态 no-op 不变）；**反证** 2 红（把补偿换成 `raise`
  ⇒ 只有断言补偿的两条红）；定向 **1997 passed / 4 skipped**；m0 首跑 `python/format-check`
  红（新文件未格式化）⇒ `ruff format` 后 **23/23**（全量 pytest **3901 passed / 10 skipped**）；
  CI run **35314730222**（#155，head `9af9c18`）**六个 job 全 success**。产品改动一处
  （`services/api/routers/approvals.py`）+ 新增测试文件 + 文档段；`child_plans` 增
  PLAN-20260918-094、`memory_entries` 增 MEM-20260918-068。
- 2026-09-18 cycle 2 收口提交 CI 记录：head `dbe4f1f` → run **35316180470**（#156）
  **六个 job 全 success**（collector-quality / console-frontend / quality-windows-latest /
  eval-gate / container-quality / quality-ubuntu-latest，无重跑）。
- 2026-09-18 cycle 3 收口：EC-03 **PASS**（PLAN-20260918-095 / RECHECK-20260918-095 =
  PASS_WITH_WARNINGS，W-1…W-4）。**先反向搜索再处置**（两条各自独立判定）：
  ① `ClaimRequest.lease_ttl_seconds` 读者 0（三实现的取租路径只读引擎级 `self._lease_ttl`）、
  19 个构造点（含生产 `worker_gateway/jobs.py`）**无一传它** ⇒ **移除字段**（不给一个没有
  需求方的字段发明语义：初始租约按请求给、续租按引擎给会让同一租约有两个 TTL）；TTL 仍是
  引擎级配置（PORTS.md + port docstring 写明）。② 示例契约的 `on_validation_failure`
  （连同同类 `allow_partial_evidence`）只有 `unhonored` 点名、没有消费者（验收门跑在任务行
  **durable `SUCCEEDED` 之后**，门拒收时任务行已是终态，按 `DEAD_LETTER` 处置需要把
  `SUCCEEDED` 行改写回去 ⇒ canonical 状态机 + ADR 边界，登记为后继入口） ⇒ **从示例移除**，
  只留被消费的 `on_task_failure: FAIL_RUN`；`unhonored` 机制与"用户键仍被点名"的既有用例
  **未削弱**。判据两件：`fields(ClaimRequest)` 钉住用例、示例契约不变量
  （`failure_policy_view().unhonored == ()`）；**反证两跑**：① 字段放回 ⇒ 1 failed
  （18 passed / 9 skipped）、② 键放回示例 ⇒ 1 failed（21 passed）——各只红对应用例。
  定向（DSN pin）**2474 passed / 7 skipped**；m0 首跑 `framework/validate` 红（RECHECK 缺
  `## 结论` 章节，记录未写完的中间态）⇒ 补齐后 **PASS: profile=m0; 23 deterministic checks**
  （全量 pytest **3903 passed / 10 skipped**，479.83s）。产品改动 5 文件 + 2 测试文件 +
  文档 4 处；`child_plans` 增 PLAN-20260918-095、`memory_entries` 增 MEM-20260918-069。
- 2026-09-18 cycle 3 收口提交 CI 记录：head `43933a1` → run **35321234815**（#157）
  **六个 job 全 success**（eval-gate / console-frontend / collector-quality /
  container-quality / quality-ubuntu-latest / quality-windows-latest，runner_id 非 0、无重跑）。
- 2026-09-18 cycle 4 收口：EC-04 **PASS**（PLAN-20260918-096 / RECHECK-20260918-096 =
  PASS_WITH_WARNINGS，W-1…W-4）。**先把枚举做成脚本判据**（不靠记忆）：
  `tools/probes/enumerate_clock_injected_pg_tests.py`（只读，AST + 行扫描）实跑 ⇒
  27 个 PG 用例文件里 **12 个注入时钟**、**0 处墙钟读**、6 个含"无时钟构造点"。
  逐文件判定 **12/12「安全」**，每条依据都落在**写入路径**上而不是"没跑红"：
  ① 时钟敏感列（`leases.expires_at` / `heartbeat_at`、`tasks.retry_at`）由
  `server_now(conn, now)` 算好**绑定写入**，判据比较也走同一个源（`db_time_expr`），
  生产取数据库时钟、测试注入 ⇒ 写入与比较不会各算各的；② 全树唯一**无条件** `now()`
  的 SQL 是 `outbox_events.created_at`，且没有用例断言它的取值或排序（断言形态是
  `EventType.X in kinds`）；③ 6 个含无时钟构造点的文件逐个看用例断言：
  `test_cross_process`/`test_lease_fencing`/`test_workflow_engine_pg` 的 DB 时钟用例断言
  dedup/状态/异常、`test_experiment_queue_pg` 的时钟是**方法参数**、
  `test_workflow_engine_parity` 的无时钟分支**没有调用点**、
  `test_dispatch_ownership_pg` 的 WorkerRegistry 只被断言状态与 `kind`。
  `grep -rn "now()" tests/postgres/*.py` 只剩一行文档字符串（与 RECHECK-084 W-5 的修复一致）。
  无「修复」项 ⇒ 没有"去掉修复 ⇒ 用例红"式反证，取而代之的是**结构可复核性**
  （如 `next_retry_at == START + 3600` 由 `projections.retry_schedule(server_now)` 产生，
  改回 SQL `now()` 该断言即红）。定向 `tests/postgres` **91 passed**（27.92s）；m0
  一次通过 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3903 passed /
  10 skipped**，505.98s）。产品代码未改（新增 1 个只读探针 + `docs/architecture/PORTS.md`
  的「时钟注入纪律」段）；`child_plans` 增 PLAN-20260918-096、`memory_entries` 增
  MEM-20260918-070。**未宣称"时序风险已清空"**：真墙钟矩阵
  `test_cross_process_real.py`（`timing_sensitive`）有意不在枚举面内（W-4）。
- 2026-09-18 cycle 4 收口提交 CI 记录：head `3358b2e` → run **35322946077**（#158）
  **六个 job 全 success**（console-frontend / container-quality / collector-quality /
  quality-windows-latest / eval-gate / quality-ubuntu-latest，runner_id 非 0、无重跑）。
- 2026-09-18 cycle 5 收口：EC-05 **PASS**（PLAN-20260918-097 / RECHECK-20260918-097 =
  PASS_WITH_WARNINGS，W-1…W-4），做的是 **①（列表 N+1）**。**先确认 N+1 真实存在**：
  `GET /projects/{id}/runs` 对每条 run 各调一次 `dispatch_ownership`（每次内部两条读）
  ⇒ 查询数 `2N`。交付：port 新增 `dispatch_ownership_many(run_ids)`；三实现的单 run 读
  改成"批量读的**一条**"（SQLite/PG 共用 `_dispatch_ownerships`、Fake 共用 `_ownership_of`）
  ⇒ 同判是**结构性**的而不是两边各写一套；投影层新增批量查询（SQLite `json_each(?)`、
  PG `= ANY(%s)`，**全绑定参数**，`retry_schedules`/`live_lease_holders_many` 供单 run 版
  复用）；控制面列表一次批量读 + 逐行装配。判据三件：① 契约用例三实现断言"批量 == 逐 run"
  （含未知 run 是 `NONE` 条目、空入参空 dict）；② **N+1 哨兵**用 adapter call log
  （整页后批量 +1、逐 run **零次**）；③ **反证实跑**：把列表路径改回逐 run 读 ⇒ `-k list`
  **1 failed / 3 passed**（`assert 0 == (0 + 1)`）。EC-05 的**文档面**（必做）写进
  `CONTROL_PLANE_API.md`：Fake **无租约过期语义**（"活"= 仍在租约表里）、
  `WORKER_CLAIM` **也覆盖控制面自持租约**（`worker_id=null`）。
  **收口门禁返工（如实记）**：① m0 首跑 `python/product-lint` 红（新 import 未排序）；
  ② 复跑规模门禁红（`adapters/postgres/workflow_engine.py` 459 > 450 行）⇒ **搬代码**
  （不碰门禁）：把派发读面的装配与记账移到新模块 `adapters/postgres/workflow_dispatch.py`
  （与既有 `workflow_claim`/`workflow_ops`/`workflow_submit` 同形），引擎方法只留
  `_ensure_open` + 错误边界，文件 **447 行**；③ 列表路由 docstring 改成**消费者可读**的
  说明（不含 cycle/EC 编号）并**重新生成** `docs/api/openapi.m13.json`（1 处 `description`
  变化，随本轮提交——**不是"快照没变"**）。定向（DSN pin）**1425 passed / 5 skipped**，
  返工后复跑 **1053 passed / 2 skipped**；m0 **PASS: profile=m0; 23 deterministic checks**
  （全量 pytest **3914 passed / 10 skipped**，468.62s）。产品改动 + 文档 3 处 + 快照 1 处 +
  2 个测试文件；`child_plans` 增 PLAN-20260918-097、`memory_entries` 增 MEM-20260918-071。
  EC-05 ② （PG 两读快照一致性）**未做**（EC-05 允许"至少一项"）：批量读消掉的是 N+1，
  不是撕裂读；诚实边界仍在 port docstring 与 `PORTS.md`（W-1）。
- 2026-09-18 cycle 5 收口提交 CI 记录：head `3c49638`（产品 `5fce188` + 记录 `3c49638`）
  → run **35330877315**（#159）**六个 job 全 success**（collector-quality /
  container-quality / quality-windows-latest / eval-gate / quality-ubuntu-latest /
  console-frontend，runner_id 非 0、无重跑）。
- 2026-09-18 cycle 5 记录提交（CI 记账）的 CI 记录：head `1189336` → run **35332314096**
  （#160）**六个 job 全 success**（container-quality / quality-windows-latest /
  console-frontend / collector-quality / eval-gate / quality-ubuntu-latest，runner_id 非 0）。
- 2026-09-18 cycle 6 收口提交 CI 记录：head `0cb68db`（产品 `813e93c` + 记录 `0cb68db`） → run **35335429653**（#161）**六个 job 全 success**（collector-quality / quality-ubuntu-latest / console-frontend / container-quality / quality-windows-latest / eval-gate，runner_id 非 0、无重跑）。
- 2026-09-18 cycle 6 收口：EC-06 **PASS**（PLAN-20260918-098 / RECHECK-20260918-098 =
  PASS_WITH_WARNINGS，W-1…W-4），做的是 **(b) 一等事实 + 读面写明**。**先只读勘察再动手**：
  ① 控制面 run 行只持久化两个 digest 与 `protocol_body`（**manifest 正文从不入库**）；
  ② `manifest_semantic_digest` / `protocol_body_digest` 的 `None` **混着三种处境**（功能前
  历史行 / 起步时冻结失败 / 还没冻结）；③ 拒绝文案分散在 `run_resume`（两条早退 +
  `body is None` 前缀）与 `convergence`（语义 digest 守卫）；④ `tools/snapshot_migrate.py`
  是**显式 opt-in** 的运营动作（`keep`/`re-freeze`/`fork`），非自动 backfill；
  ⑤ 旧 `manifest.frozen` payload（只有 `digest`）的 from-event 回填分支**没有任何用例**。
  交付：`packages/application/run_orchestration/rebuild_readiness.py`（纯函数分类器：
  四字段 ⇒ `SELF_CONTAINED`/`SOURCE_DEPENDENT`/`REFUSED` + **按行字段名确定性排序**的
  `missing`）+ `RunDetailDto.rebuild`（任何状态都给）+ `services/api/run_rebuild_view.py`；
  `/resume` 的两条早退与异常前缀改从分类器取（**条件与文案逐字不变**）⇒ 读面与拒绝
  **同源**。判据三件：① 分类器矩阵 10 用例 + 值对象三条不变量 + `missing` 取值 ⊆
  `dataclasses.fields(ResearchRun)`（结构判据）；② 读面用例：旧事件形态点名
  `manifest_semantic_digest`、旧 run 形态点名 `protocol_body`+`protocol_source`、
  自足行 `missing == []`（**历史行与当前行可区分**）；③ 旧事件回填分支补覆盖
  （`from_payload({"digest": …})` ⇒ None，不伪造）。**反证实跑**：去掉
  `manifest_semantic_digest` 判定 ⇒ **6 failed / 25 passed**，还原 ⇒ **31 passed**。
  **首轮踩坑并修正（如实记）**：把"没有冻结正文"前缀绑在 `status=SOURCE_DEPENDENT` 上，
  会让"既缺正文又缺语义 digest"的行丢前缀 ⇒ 既有用例
  `test_a_run_without_a_frozen_body_names_both_missing_facts` 红；修正 = 分类器显式带出
  `body_frozen`（**未改断言**）。定向（DSN pin）`tests/api+contracts+application+adapters+e2e`
  **2053 passed / 7 skipped**（322.87s）；web 六门绿（lint / typecheck / unit **76** /
  build / stub e2e **83** / live e2e **36**）；规模门禁 **935 passed**；m0
  **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3932 passed / 10 skipped**，
  491.81s）。文档同源两处（`CONTROL_PLANE_API.md` 读面三态与诚实边界、`EVENT_MODEL.md`
  旧 payload 形态）；OpenAPI 快照 + web `types.ts` + e2e 夹具同步。
  `child_plans` 增 PLAN-20260918-098、`memory_entries` 增 MEM-20260918-072，
  `latest_recheck` 指向 RECHECK-20260918-098。**EC-01…EC-06 全 PASS** ⇒ 下一条 = 收口。
  **未宣称**：读面不预测重建结果（W-1）、不裁决"不可回填"（W-2）、前端未消费 `rebuild`
  （W-3）、`missing` 未做 UI 文案映射（W-4）。

- 2026-09-18 cycle 7 = **收口**（GOAL-005 达成）：`status: ACTIVE` → **`ACHIEVED`**，
  `latest_recheck` 指向 RECHECK-20260918-099（PASS_WITH_WARNINGS）。**独立复检**（不看历史
  RECHECK 结论文本）：① 复检脚本 `scratch/verify_goal005_closeout.py` **56 checks 全 PASS**
  （交付物在树 / 判据用例在树 / 登记面一致三层，含六条 EC 表逐条 PASS、ALL_PLAN 七行 DONE）；
  ② 六条 EC 的判据用例合并复跑 **130 passed**（17.71s）；③ EC-04 的枚举探针在收口 head **重跑
  逐数一致**（27 / 12 / 0 / 6）；④ **干净 checkout 深扫**取得新封印
  `sha256:c0202d05a57e3919139a80416e16d6e02e4350ebfbf196b614248c9d28c52f89`
  （25 条：1 high / 19 medium / 5 low）并**逐类处置**（high = `yaml.load(_StrictLoader)` 子类
  `SafeLoader` 的误报，有行内证据；low = 演示脚本的带种子随机；medium = 运维诊断脚本与
  operator 环境变量），工作树对照扫 34 条（1/28/5）差集 = gitignored `scratch/` 探针
  ⇒ 与 EC-01 同一结论（输入边界改变剖面）；**离线 advisory 通道两次输入答案不同 ⇒ 不作
  依赖结论**，以 EC-01 的联网查询为准；扫描 `verdictEffect=none` / coverage `inconclusive`
  ⇒ **不宣称"项目安全"**；⑤ 门禁全绿（m0 **PASS: profile=m0; 23 deterministic checks**，全量 pytest **3932 passed / 10 skipped**，484.00s；web 六门 cycle 6 内实跑；
  规模门禁 935 passed；治理 validate 绿）。**收口不等于残余消失**：人工决策面六项、
  EC-05 ②（PG 两读快照）、EC-03 的 `DEAD_LETTER` 消费、各 cycle 的 W 列表、扫描覆盖缺口
  全部写进「收口结论」；恢复条件 = 用户新建承接 GOAL 或显式变更 budget 并置回 ACTIVE。
- 2026-09-18 收口提交 CI 记录：head `177b34a` → run **35336969637**（#162）**六个 job 全 success**
  （collector-quality / eval-gate / quality-ubuntu-latest / console-frontend /
  quality-windows-latest / container-quality，runner_id 非 0、无重跑）。**GOAL-005 至此收口**：
  `status: ACHIEVED`，不再有新 cycle；本条之后的记录提交只做 CI 记账（同 GOAL-004 收口口径）。
- 2026-09-18 收口记录提交的 CI 记录：head `2bddf4f` → run **35338050399**（#163）**六个 job 全 success**
  （console-frontend / collector-quality / eval-gate / quality-ubuntu-latest /
  quality-windows-latest / container-quality，runner_id 非 0、无重跑）。**这是本 GOAL 的最后一条
  记账**：其后不再有内容提交（`status: ACHIEVED`，循环终止）。
- 2026-09-18 终态记账：head `cf09efc` → run **35339327745**（#164）**六个 job 全 success**
  （collector-quality / eval-gate / container-quality / quality-ubuntu-latest /
  quality-windows-latest / console-frontend）。
- 2026-09-18 台账闭合提交自身的 CI 记录：head `8535fb6` → run **35340409693**（#165）
  **六个 job 全 success**（collector-quality / eval-gate / container-quality /
  quality-ubuntu-latest / quality-windows-latest / console-frontend，runner_id 非 0）。
  **CI 台账闭合口径（写死在这里，避免"记录—提交—再记录"的无限递归）**：台账逐条记录**每个
  推送提交**触发的 run 到终态；**本轮记账提交自身**（即写下本条的这个提交）触发的 run 在
  **回合汇报**里给出终态（run id + 六 job 结论），**不再回写本文件**——因为回写又会产生一个
  新提交与新 run，递归没有终点。据此：`#165` 是最后一个**被文件记录**的 run，
  其后仅剩"记录本条的那个提交"的 run（回合报告口径），**本 GOAL 不再新增内容提交**。
