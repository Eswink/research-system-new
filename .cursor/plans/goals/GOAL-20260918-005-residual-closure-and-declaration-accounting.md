---
id: GOAL-20260918-005
slug: residual-closure-and-declaration-accounting
title: 残留收口与声明清账：安全审计残留复核、同形补偿入口、未消费声明、时钟风险、读面语义边界、历史行可追溯
status: ACTIVE
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
    status: PENDING
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
    status: PENDING
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
    status: PENDING
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
child_plans:
  - .cursor/plans/tasks/PLAN-20260918-093-security-audit-residual-recheck.md
  - .cursor/plans/tasks/PLAN-20260918-094-approval-resume-failure-compensation.md
latest_recheck: null
memory_entries:
  - MEM-20260918-067
  - MEM-20260918-068
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
| EC-03 | 声明未消费项清账（`on_validation_failure` / `ClaimRequest.lease_ttl_seconds`） | 收口结论表 3 / RECHECK-086 W-1 + 089 W-1 | PENDING |
| EC-04 | 时钟/时序风险逐个收口（不做「未观测到失败」式收尾） | 收口结论表 9 / RECHECK-084 W-5 | PENDING |
| EC-05 | 读面语义边界（列表 N+1 或 PG 两读快照至少一项 + Fake/`WORKER_CLAIM` 同源文档） | 收口结论表 4 / RECHECK-089 W-2…W-6 | PENDING |
| EC-06 | 历史行可追溯（旧 run 无正文 / 旧事件无 `semantic_digest`，三选一） | 收口结论表 6 / RECHECK-084 W-2 + 087 W-1 | PENDING |

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

当前续点：**cycle 2 已收口**（EC-02 PASS + RECHECK-20260918-094 + run 35314730222 六 job 全绿），
下一条 = **cycle 3 = EC-03**（声明未消费项清账）：先反向搜索 `on_validation_failure` 与
`ClaimRequest.lease_ttl_seconds` 的全树命中，逐条判定「给真实消费者」还是「从契约/文档
移除并写明」，两条各自独立处置。

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

### 收口结论

（待收口时填写；当前 `status: ACTIVE`，无收口结论。）

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
