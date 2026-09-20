---
id: GOAL-20260920-009
slug: live-sample-and-anthropic-surface-closure
title: live 采样与 anthropic 面收口：把 GOAL-008 如实 skip 的 live 分支推进到有真实样本，并给「run 自身消费哪一面」一个一等终态
status: ACHIEVED
created_at: 2026-09-20
updated_at: 2026-09-20
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-20 用户会话指令（goal 模式）：**建档 GOAL-20260920-009 并授权本驱动自动化循环推进、
    无需逐轮确认**。四段授权原文要点如下：
    (1) **live-gated 真实调用授权**：用户授权在真实端点上做 **live-gated 真实调用**——端点
    `https://apihub.agnes-ai.com`、模型 `agnes-2.5-flash`；**次数取最小必要**，不做压测、批量或
    重复重跑。该凭据为**可弃用的免费额度**，**泄露风险已由用户明示接受**（此声明只降低追责口径，
    **不放松下面的凭据纪律**）。
    (2) **凭据纪律（不得放松）**：键名 `LLM_MAIN_KEY`，**值只存在于本机 gitignored 的 `.env`**
    （`.gitignore:1` 已覆盖，`git ls-files` 不含该文件）。进程内可见性由**导入栈的 dotenv 加载**
    保证（litellm 导入期 `load_dotenv`）——判据是 `EnvCredentialResolver().has('LLM_MAIN_KEY')`
    为 `True`。**值不得写入任何 tracked 文件、DB、记录（PLAN/RECHECK/MEM/GOAL）、日志或命令回显**。
    **不得把 `RESEARCHOS_AGENT_RUNTIME` 写进 `.env`**——它**只作为单条命令的内联前缀**，否则默认门
    会切到真实 runtime、破坏 CI 语义。
    (3) **默认姿态不变**：默认 runtime 保持 Fake、默认 CI 离线（AGENTS.md §11）；live 分支必须
    **显式** `RESEARCHOS_AGENT_RUNTIME=openhands` 才开门（fail-closed 姿态不放松，AGENTS.md §9）。
    (4) **push-to-main-for-CI 授权**：沿用 GOAL-001…008 的批准口径——**只推 main、不 force、不重写
    历史、不推旁支触发 CI**；push 前 `git pull --ff-only origin main`（必要时 `--rebase`，始终不
    force）。循环预算与纪律以本文件 frontmatter 为准（客户端自带的迭代/重试/超时上限一律让位于此）。
    GOAL-001…008 全部**只读**（001/002/004/005/006/007/008 ACHIEVED、003 BLOCKED），本 GOAL 不修改
    它们；如需指名只允许按只追加补一行事实更正（当前不需要）。
objective: >
    把 GOAL-008 里那两条**如实 skip 的 live 分支**（EC-04 首次 live-gated 真实 run / EC-05 漂移
    实测样本）从「没有样本」推进到**有真实样本**——在**显式配置 + policy 允许**的 live-gated 路径上
    跑**最小必要次数**的真实调用，跑出：probe 段 `verified and ok`、run 到**终态**、运行时**指纹可判**、
    usage **真归账**到 BudgetLedger、制品与证据**可读**，结论口径**停在 `REPEATABLE_CONFIGURATION`**
    （AGENTS.md §4：**不得**宣称「完全模型可复现」）；把自己的失败也**如实落终态**（端点/协议/装配
    导致失败即如实归类为缺陷并按 fix_policy 纠错，**不得把失败写成 PASS、不得降低判据**）。
    同时给「**一次 run 自身消费哪一面**」一个**一等终态**：要么改模型→端点绑定让 run 本身走
    ANTHROPIC 协议到终态（含对既有 stub/live e2e、设计基线、前端读面的影响评估），要么把
    「run 走 `main`（OPENAI_COMPATIBLE）、anthropic 面由 probe 段驱动」**写成一等边界**
    （读面/文档同源）并给出改绑步骤、影响面与判据草案——**不得留模糊状态**。漂移可见性的三态
    （一致/漂移/未知）从「未知」变为**实测**；失败路径（无效凭据/端点拒绝/模型不存在）有**可判定**
    的门与记录语义并至少给一条**反证**；凭据生命周期（注入/轮换/撤销/可弃用额度处置）落成 runbook
    的**同源判据**。**全程不删测试、不改门禁、不以「未观测到失败」充当 PASS；不引入新依赖、不改
    上游 pin、不自行修改 Accepted ADR / 核心安全策略 / Canonical State 边界、不把真实 runtime 设为
    默认——触及即 BLOCKED。**
exit_criteria:
  - id: EC-01
    criterion: >-
      **live 采样第一次（首次真实 run 到终态）**：跑 `tests/e2e/test_ec04_live_first_run.py` 的
      **live 分支**（显式 `RESEARCHOS_AGENT_RUNTIME=openhands` 内联前缀开门），四段判据全中：
      (i) probe 段 `verified and ok`；(ii) run **到终态**；(iii) 运行时**指纹可判**（记录里
      `returned_model_identifier` 非空）；(iv) usage **真归账**到 BudgetLedger（`MODEL_TOKENS`
      条目 ≥1 且 `model_tokens > 0`）；(v) 制品与证据**可读**（`artifact_ids` / `evidence_ids`
      非空）。结论口径**必须**停在 `REPEATABLE_CONFIGURATION`（`record.is_verified` 为真），
      **不得**声称「完全模型可复现」。样本**如实登记**进记录（run id、UTC 时间、probe 返回的
      model 名；**不含凭据值、不含凭据片段**）。
      **失败也必须落终态**：若端点/协议/装配导致失败，如实归类为缺陷并按 fix_policy 纠错，
      **不得**把失败写成 PASS、**不得**降低判据；门未开（无凭据/未配置）时**如实记 skip 并停止
      宣称**，**skip 不是 PASS**。
    verify: >-
      `RESEARCHOS_AGENT_RUNTIME=openhands uv run --frozen --no-sync python -B -m pytest
      tests/e2e/test_ec04_live_first_run.py -v` ⇒ `test_live_first_run_reaches_a_terminal_state`
      **PASS（非 skip）**，且落盘的 `live-run-record.json` 的 `verdict` 恰为
      `REPEATABLE_CONFIGURATION`；样本（run id / 时间 / 返回 model 名）写入对应 RECHECK 与
      `docs/integration/LIVE_MODEL_RUNBOOK.md` 的样本条目。跑前自检
      `EnvCredentialResolver().has('LLM_MAIN_KEY') is True`（只问存在性，**不物化值**）。
      反证：把 `RESEARCHOS_AGENT_RUNTIME` 前缀去掉 ⇒ 同一命令必须走 skip 且记录
      `NOT_VERIFIED`（门关着 ⇒ 零出站）。
    status: PASS
  - id: EC-02
    criterion: >-
      **run 自身消费 anthropic 面的口径（二选一终态，不得留模糊状态）**：
      (a) **改模型→端点绑定**（`agnes_flash` → `agnes-anthropic`）使 run **本身**走 ANTHROPIC 协议
      跑到终态——判据：run 的端点协议为 `ANTHROPIC` + run 到终态 + usage 归账；改绑前**必须**评估
      对既有 stub/live e2e、设计基线与前端读面的影响并如实记录；
      (b) **维持现有绑定**，把「run 走 `main`（`OPENAI_COMPATIBLE`）、anthropic 面由 probe 段驱动」
      写成**一等边界**（读面/文档**同源**），并给出**改绑步骤、影响面与判据草案**。
      无论选哪条，**决策与理由必须落记录**，且读面措辞与代码事实一致（**不得**在文档里把未发生的
      事写成已发生）。若选 (a)，回退路径必须写明。
    verify: >-
      (a) 路径：EC-01 的 live run 记录中，run 所用端点的 `protocol` 为 `ANTHROPIC`，且
      `models.yaml` / 读面 DTO 与之一致（结构判据 + 一次 live run 终态）；
      (b) 路径：存在一条**同源判据**（测试或 validator 规则）把「run 面 = `main` / probe 面 =
      `agnes-anthropic`」钉住，且 `docs/integration/LIVE_MODEL_RUNBOOK.md` 含改绑步骤与影响面，
      该文档的仓库路径/变量名/目标判据**全部可解析**（沿用 GOAL-008 EC-06 的同源判据形态）。
      两条路径都要求：**决策记录存在**（RECHECK 里写明选了哪条、为什么）。
    status: PASS
  - id: EC-03
    criterion: >-
      **漂移实测样本（补 EC-05 的 live 缺口）**：把「**实测返回 model 名 vs 声明值**」的**真实样本**
      落到读面/记录——漂移三态（一致/漂移/未知）从「**未知**」变为**实测**。若中转站返回标识与声明
      值**不同**，**如实记为漂移样本**并给出影响面（这正是 AGENTS.md §4 要可见的那种漂移）；若**相同**，
      记为一致样本并写明**它的证明力边界**（单次样本 ≠ 永不漂移）。**不得**把「没观测到漂移」写成
      「无漂移」。
    verify: >-
      记录中含**真实样本**（返回 model 名 + 声明值 + 判定结果 + 时间 + run id），且该样本经既有读面
      （模型详情 DTO / 页面三态渲染）可取；判据含「未知 ≠ 无漂移」的钉住（沿用 EC-05 既有用例）。
      样本本身来自 EC-01 的 live 调用，**不额外发起调用**（次数取最小必要）。
    status: PASS
  - id: EC-04
    criterion: >-
      **失败路径的诚实语义（反证式）**：无效凭据 / 端点拒绝 / 模型不存在三类情形下，门与记录的语义
      **可判定**——要么**不发起调用**（门关着，零出站），要么发起后**明确失败并落记录**（终态 +
      点名理由）。至少给**一条反证**：临时把 key 置空或改无效 ⇒ 行为与登记一致，随后**复原**；
      **全过程不打印值**（含片段）。
    verify: >-
      反证的**先红后绿**证据（改动 → 观察到预期行为 → 复原 → 复绿），且每一次都记录**命令形态与
      结论**而非输出值；三类情形各自的期望语义有明文（记录/读面/文档同源）。复原后必须复跑
      EC-01 的判据确认无残留。
    status: PASS
  - id: EC-05
    criterion: >-
      **凭据生命周期 runbook 落地**：把本机 `.env` 注入、`set -a; . ./.env; set +a` 的加载方式、
      **轮换**（换值即生效、无需重启 API 的边界与不成立的情形）、**撤销**（清空值 ⇒ 门**自动关闭**）
      写成**同源判据**（文档里的仓库路径/变量名/pytest 目标必须可解析，沿用 EC-06 的判据形态）；
      含「**本 key 为免费可弃用额度**」的说明与「值不落任何文件」的纪律复述。
    verify: >-
      同源判据套件 PASS（文档路径/变量名/pytest 目标全部可解析）；轮换与撤销各有一条**实跑**证据
      （先使门关、再使门开，或反之），**全过程无凭据值出现在任何记录/日志/回显**。
    status: PASS
  - id: EC-06
    criterion: >-
      **收口复检 + 残余登记**：独立复检脚本（**当前树 + 干净 checkout 同结论**）+ 本地 m0 全量 +
      治理 `validate.py` 绿；GOAL-008 遗留的**六项人工面**（ADR-0031 仍 Proposed、威胁建模/BOLA-BFLA、
      `artifacts/` 明文 token 清理、450 行纪律、依赖 pin 升级、hook 侧 L3 门）**原样保留**为残余，
      外加本 GOAL 自己新产生的 W 列表。残余**不得**因收口消失。
    verify: >-
      复检脚本三层判据全 PASS 且两棵树同结论；m0 **23/23**；治理 `validate.py` 绿；本文件
      `latest_recheck` 指向 PASS/PASS_WITH_WARNINGS 的 RECHECK；frontmatter 的 EC 状态与
      markdown 状态表**一致**（GOAL-006/007/008 收口时同一类漏改，见 MEM-20260920-093）。
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
  - 新依赖/上游版本 pin 变更（含为判据引入新的解析/传输库——优先用现有依赖实现）
  - 同一失败签名超过 fix_policy 上限
  - 威胁建模/授权面（BOLA/BFLA）覆盖类决策——需用户或 ADR 拍板，本循环不得自行决定
  - 依赖 pin 升级（`undici` / `vite` / `yaml` 等有修复版本的包）——上游 pin 变更，需用户或 ADR 拍板
  - ADR-0031（`tool_pack.*`，Status: Proposed）是否采纳——归用户
  - 把真实 runtime 设为**默认**（默认必须仍是 Fake；本循环只做「显式配置才启用」）
  - 新增依赖或改动既有依赖 pin（含为 anthropic 形态引入 SDK——优先用手写 HTTP）
  - 明文凭据泄露（**即使是可弃用的免费额度**）——立即停止并报告
child_plans:
  - .cursor/plans/tasks/PLAN-20260920-121-first-live-sampling-run.md
  - .cursor/plans/tasks/PLAN-20260920-122-anthropic-surface-boundary-decision.md
  - .cursor/plans/tasks/PLAN-20260920-123-live-drift-sample-as-judged-record.md
  - .cursor/plans/tasks/PLAN-20260920-124-live-failure-path-semantics.md
  - .cursor/plans/tasks/PLAN-20260920-125-credential-lifecycle-runbook.md
  - .cursor/plans/tasks/PLAN-20260920-126-goal-009-closeout-recheck.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20260920-126-goal-009-closeout-recheck.md
memory_entries: MEM-094, MEM-095, MEM-096, MEM-097, MEM-098, MEM-099
---

# GOAL-20260920-009 — live 采样与 anthropic 面收口（自迭代循环）

本 GOAL 承接 GOAL-20260920-008（真实供应链接入，**ACHIEVED**）的**恢复条件**：
GOAL-008 把「anthropic 协议执行路径」「模型参数落库」「供应链登记与凭据纪律」「漂移三态」
「runbook」都做成了有终态的交付，但它的 **EC-04 / EC-05 的 live 分支在收口时如实记为 skip**
——六项候选凭据环境变量当时全部 absent，**那次真实 run 从未发生**。收官结论明文写着：

> **恢复条件**：用户注入凭据（只经环境变量或 Credential boundary）后，按
> `docs/integration/LIVE_MODEL_RUNBOOK.md` 执行首次 live run——它会同时把 EC-04 与 EC-05 的
> live 分支从「如实 skip」推进到「有样本」。

**该条件在 2026-09-20 已满足**：本机 `.env`（gitignored）已含 `LLM_MAIN_KEY`（见「建档时已探明的
现状」）。因此本 GOAL 的存在理由只有一个：**把「如实 skip」变成「有样本」**，并且在这个过程中
**不放松任何一条纪律**。

## 目标与退出标准

| EC | 标准 | 验证命令／证据来源 | 状态 |
| --- | --- | --- | --- |
| EC-01 | live 采样第一次：live 分支四段全中（probe ok / 到终态 / 指纹可判 / usage 归账 / 制品证据可读），口径停在 `REPEATABLE_CONFIGURATION`；样本如实登记 | `RESEARCHOS_AGENT_RUNTIME=openhands … pytest tests/e2e/test_ec04_live_first_run.py -v` ⇒ 该用例 **PASS 非 skip**；落盘 `live-run-record.json` 的 `verdict == REPEATABLE_CONFIGURATION` | **PASS**（**终态 = `FAILED`**，设计内 acceptance-gate 判拒；样本已登记，`RECHECK-20260920-121` = PASS_WITH_WARNINGS） |
| EC-02 | run 自身消费 anthropic 面的口径（二选一终态）：(a) 改绑使 run 走 ANTHROPIC 到终态，或 (b) 把「run=main / probe=anthropic」写成一等边界 + 改绑草案；决策必须落记录 | (a) live run 记录里 run 端点 `protocol == ANTHROPIC` + 终态 + 归账；(b) 同源判据 PASS + runbook 含改绑步骤/影响面；两条都要求 RECHECK 写明选了哪条与为什么 | **PASS**（取 **(b)**：边界已钉成一等**可判**事实 §12 + 改绑步骤/影响面/判据草案；`RECHECK-20260920-122` = PASS_WITH_WARNINGS） |
| EC-03 | 漂移实测样本：实测返回 model 名 vs 声明值，三态从「未知」变「实测」；不同则如实记为漂移并给影响面，相同则写明证明力边界 | 记录含真实样本（返回名/声明值/判定/时间/run id）且经既有读面可取；「未知 ≠ 无漂移」钉住用例仍 PASS；**不额外发起调用** | PASS |
| EC-04 | 失败路径诚实语义（反证式）：无效凭据/端点拒绝/模型不存在三类可判定；至少一条反证先红后复原，全程不打印值 | 反证的先红后绿证据 + 三类期望语义明文；复原后复跑 EC-01 判据确认无残留 | PASS |
| EC-05 | 凭据生命周期 runbook：注入（`set -a; . ./.env; set +a`）/轮换/撤销/可弃用额度说明落成同源判据 | 同源判据套件 PASS；轮换与撤销各有实跑证据；无凭据值出现在任何记录/日志/回显 | PASS |
| EC-06 | 收口复检 + 残余登记：独立复检（当前树 + 干净 checkout 同结论）+ m0 23/23 + 治理 validate 绿；六项人工面原样保留 + 本 GOAL 的 W 列表 | 复检脚本三层判据全 PASS 且两树同结论；m0 23/23；`validate.py` 绿；`latest_recheck` 指向 PASS/PASS_WITH_WARNINGS；frontmatter 与状态表一致 | PASS |

### 建档时已探明的现状（事实类，用于判定起点；不当作验收依据）

以下为 2026-09-20 建档当日**实跑核对**的结论（命令均已执行，非引用历史记录）：

| # | 事实 | 核对方式 | 结论 |
| --- | --- | --- | --- |
| F-1 | `.env` 存在且 **gitignored** | `git check-ignore -v .env` ⇒ `.gitignore:1:.env`；`git ls-files --error-unmatch .env` ⇒ pathspec 不匹配 | **勾住** |
| F-2 | `LLM_MAIN_KEY` **值非空**（只测长度，未打印值） | 逐行解析 `.env`（跳过注释）后比较键名 | **非空** |
| F-3 | 进程内**凭据可解析** | `import tests.e2e.live_run_support` 后 `EnvCredentialResolver().has('LLM_MAIN_KEY')` | **True** |
| F-4 | dotenv 的加载**来自导入栈**，不是仓库代码 | 全仓 `grep -rn "load_dotenv" --include=*.py` ⇒ **0 命中**；裸导入 `adapters.relay.credential_resolver` 时 `has()` 为 **False**，导入 litellm 后为 **True** | **由 litellm 导入期加载**；判据必须跑在完整导入栈里 |
| F-5 | `.env` **不含** `RESEARCHOS_AGENT_RUNTIME` | 对 `.env` 逐行取键名后比对（存在一个**不同**的 `AGENT_RUNTIME` 键，被 `settings.py` 忽略） | **勾住**（默认门不会被动切到真实 runtime） |
| F-6 | 门的**两条**开门条件与默认姿态 | 逐条取键名后调用 `evaluate_live_run_gate(...)`（**无网络**） | 默认下 `open=False`，理由逐字为 *agent runtime is not configured (need 'openhands'; default stays fake); credential 'LLM_MAIN_KEY' is not resolvable* |
| F-7 | 端点协议与绑定现状 | 读 `examples/config/llm_endpoints.yaml` / `models.yaml` | `main` = `OPENAI_COMPATIBLE`（`credential_ref: LLM_MAIN_KEY`）；`agnes-anthropic` = **`ANTHROPIC`**、**已登记**；**`agnes_flash.endpoint == main`** ⇒ EC-02 的 (a) 需要改绑 |
| F-8 | 一次 run 实际用到的模型 | `examples/config/agents.yaml` + `examples/protocols/console_demo_research_v1.yaml` | 协议绑**角色**（`domain_researcher` / `scientific_reviewer`），AgentSpec 绑 **`research_alpha` / `reviewer_gamma` / `coding_beta`** 与 profile `research_strong` —— 这些都走 `main` |
| F-9 | 本 GOAL 建档时**未发起任何真实调用** | —— | 截至建档，`agnes-2.5-flash` 的真实返回标识仍**无样本**（EC-01/EC-03 的起点） |
| F-10 | 一次 run **实际消费哪些模型**（决定 EC-02 (a) 的改绑靶子） | `examples/config/agents.yaml` + `model_profiles.yaml` + `examples/protocols/console_demo_research_v1.yaml` 的角色表，交叉核对 | 协议要 `domain_researcher` / `scientific_reviewer` ⇒ `domain_a` = **`research_alpha`**、`reviewer_a` = **`reviewer_gamma`**（均绑 `main`）；`research_strong` profile 的 primary 也是 `research_alpha`。**`agnes_flash` 只被 probe 段使用** ⇒ 只改绑它**不会**让 run 走 ANTHROPIC |

**结论**：GOAL-008 的恢复条件已满足（F-2/F-3），且默认姿态没有被破坏（F-5/F-6）。EC-01 与 EC-03
的 live 分支**可以真的跑**；EC-02 需要一次**有证据的决策**（F-7/F-8 说明 (a) 不是零成本的）。

### EC-01 判定细则（live 采样第一次）

1. **开门命令**（单条命令的内联前缀，跑完**不得**把开关留在环境或 `.env`）：
   `RESEARCHOS_AGENT_RUNTIME=openhands uv run --frozen --no-sync python -B -m pytest tests/e2e/test_ec04_live_first_run.py -v`
2. **跑前自检**：`EnvCredentialResolver().has('LLM_MAIN_KEY')` 必须为 `True`（**存在性**检查，
   **不物化明文**）。为 `False` ⇒ 门关着 ⇒ **如实 skip 并停止**，不得伪造。
3. **跑后纪律**：确认 `RESEARCHOS_AGENT_RUNTIME` **未**留在 shell 环境、**未**写入 `.env`；
   命令回显与记录里**无凭据值/片段**。
4. **判据**：`test_live_first_run_reaches_a_terminal_state` **PASS（非 skip）**；落盘记录的
   `verdict == REPEATABLE_CONFIGURATION`；四段（终态 / 指纹 / 归账 / 制品与证据）逐条为真。
5. **口径**：结论**只能**停在「可重复配置」（§4）。`system_fingerprint` 缺失是**如实的缺口**，
   **不**降级判定、也**不**用「没看到指纹」冒充「模型可复现」。
6. **失败处理**：失败**也是终态**——如实归类（端点面 / 协议面 / 装配面）并按 fix_policy 纠错；
   **不得**把失败写成 PASS，**不得**降低判据迁就实现。

### EC-02 判定细则（anthropic 面口径）

- **允许的两条终态**见上表；**不允许**的是「两边都提一句、都没做实」的模糊状态。
- 选 (a) 时**必须先评估**（并把评估写进子 PLAN 的影响报告）：既有 stub/live e2e 是否假设
  `agnes_flash → main`；设计基线（前端像素/结构签名）是否随读面文案变化；前端读面是否展示协议。
- 选 (b) 时**必须**给出：改绑步骤、影响面、判据草案——**并**把当前边界写成可判的同源事实，
  而不是散落在注释里。
- **cycle 1 实测补充（F-10，改绑的靶子不是 `agnes_flash`）**：本 GOAL 的 EC-02 (a) 沿用了
  用户指令里的简写「`agnes_flash` → `agnes-anthropic`」。**实测澄清**（读
  `examples/config/agents.yaml` + `model_profiles.yaml` + 协议的角色表）：
  **一次 run 消费的模型不是 `agnes_flash`**——协议的两个 phase 要
  `domain_researcher` 与 `scientific_reviewer`，前者由 `domain_a`（`EXPLICIT_MODEL
  research_alpha`）承担、后者由 `reviewer_a`（`EXPLICIT_MODEL reviewer_gamma`）承担；
  `agnes_flash` **只**被 EC-04 判据的 **probe 段**用到。⇒ 只把 `agnes_flash` 改绑到
  `agnes-anthropic`，**run 本身仍然走 `main`**，**达不成** EC-02 的判据（「run 的端点协议为
  `ANTHROPIC`」）。因此选 (a) 时**改绑的靶子是 run 实际消费的模型**（至少
  `research_alpha` 与 `reviewer_gamma`，必要时 `coding_beta`）；
  **这不是把判据放宽或挪动，而是把靶子读准**——判据一直是「run 的端点协议」。
- 回退路径必须写明（改绑是配置改动，回退同样是配置改动；**不涉及** Domain / Canonical State）。

### EC-03 判定细则（漂移实测样本）

- 样本**复用 EC-01 的同一次 live 调用**（`run_live_probe` 的返回），**不额外发起调用**
  ——「次数取最小必要」是用户授权的硬口径。
- 三态沿用既有实现（`assess_model_drift`）：**一致** / **漂移** / **未知**。本 EC 要消灭的是
  「未知」，**不是**「漂移」——若中转站返回的标识与声明值不同，那是**要如实记录的发现**，
  **不是**要修掉的缺陷（AGENTS.md §4 正是要这种可见性）。
- 单次样本的**证明力边界**必须写明：`一致` 只代表**这一次**一致，**不**等于「永不漂移」。

### EC-04 判定细则（失败路径的诚实语义）

三类情形各自要有**可判定的期望**（先写清楚，再验证）：

| 情形 | 期望语义 |
| --- | --- |
| 无效凭据 | 门**开**（`has()` 只看存在性，不看有效性）⇒ **发起**调用 ⇒ **明确失败**并落记录（点名鉴权失败），**不**静默成功、**不**重试到超时 |
| 端点拒绝 / 不可达 | 同上：**明确失败**并落记录；若 URL 策略先行拒绝（localhost/环回/私有/保留），则**不发起出站**且点名策略 |
| 模型不存在 | **明确失败**并落记录（点名模型标识），**不**回退到别的模型 |

**反证（至少一条）**：临时把 key 置空或改无效 ⇒ 观察行为与上表一致 ⇒ **复原** ⇒ 复跑 EC-01 判据
确认无残留。**全过程不打印值**（含片段）——只记录**命令形态**与**结论**。

### EC-05 判定细则（凭据生命周期 runbook）

- **注入**：`set -a; . ./.env; set +a`（POSIX shell 形态）与「只经环境变量」的纪律复述；
  **必须写明**本机是否自动加载（F-4：由导入栈的 litellm `load_dotenv` 加载 ⇒ 跑 pytest 时**无需**
  手工导出，但**显式导出**是更可移植的形态）。
- **轮换**：换值即生效的**边界**——两个解析器（`EnvCredentialResolver` /
  `RegistryCredentialResolver`）都在**构造时**拷贝 `os.environ`
  （`adapters/relay/credential_resolver.py` / `adapters/relay/registry_credential_resolver.py`）。
  **实测（2026-09-21）：撤销来源后，已构造的同一个实例仍报 `has()=True`；只有新构造的实例才看到变化。**
  ⇒ 「同一进程内改 `os.environ` 即生效」**不成立**；生效边界是「**新构造 resolver 的时机**」
  （新进程 / 每次新建实例的路径）⇒ API 面仍需**重启**（§3）。**RegistryCredentialResolver
  的 `_registry` 副本**（`register()` 注入）**独立于环境变量**：命中注册表时**不**回退环境快照。
- **撤销**：清空值 ⇒ **新构造**的解析器 `has()` 为 `False` ⇒ **门自动关闭**（fail-closed）。
  **判据**：撤销后 `evaluate_live_run_gate` 必须 `open=False` 且理由点名凭据不可解析。
  **边界**：若该 ref 已 `register()` 进注册表，注册表命中**优先于**环境变量 ⇒
  撤销环境变量**不**关闭这个面的门，必须 `unregister()`。
- **可弃用额度**：如实写明本 key 为**免费可弃用额度**（用户明示接受泄露风险）**以及**
  「这**不**降低凭据纪律」——值仍**不得**落任何 tracked 文件/DB/记录/日志/回显。

## 循环入口协议

驱动方（会话或定时自动化）进入时，按迭代日志最后一行 + 工作树/远端实况判定续点：

1. 最后一 cycle 无记录 → 开 cycle 1：执行 ①。
2. 有子 PLAN 但仍在 IN_PROGRESS → 继续该 PLAN 的执行（②）。
3. 本地验证已过、有未推送 commit → 执行 ④⑤（push + CI）。
4. CI 在跑或未记录结论 → 执行 ⑤（等待/判定），**禁止猜测绿**。
5. CI 有失败且修复次数未达上限 → 执行 ⑥（纠错）。
6. 最后一 cycle 的 commit+CI 全绿且 EC 未满足 → 执行 ①（生成下一子 PLAN）。
7. 判定条件按「终止与收口」：ACHIEVED / BLOCKED / 超预算。

**本 GOAL 特有的续点判据**（live 面）：**live 调用是否已发生**以**落盘的记录/样本**为准
（不是以「命令跑过」为准）。任何「已跑过 live」的声称若无样本文件与 RECHECK 条目支撑，
按**未发生**处理。live 调用**次数取最小必要**：同一 EC 不重复跑；EC-03 复用 EC-01 的样本。

## 驱动

- owner：`root-agent`；进入 cycle 时在迭代日志声明 `driver=client-goal / owner=root-agent`。
- 另一驱动已持有未收口的 ACTIVE cycle 时**等待**，不并发双写。
- 客户端自带的迭代/重试/超时上限**一律让位于**本文件 frontmatter 的 budget / fix_policy。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；用 Plan Mode 流程写
  子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 增加 `parent_goal: GOAL-20260920-009` 并投影
  `ALL_PLAN`，同一提交）。GOAL 迭代日志登记子 PLAN 路径。**live 类 EC 的子 PLAN 必须先写清
  「判据 + 失败如何落终态」再跑**。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**显式路径**）。
- **③ 本地验证**：先自查规模门禁（50 行函数 / 450 行文件）与快照类门禁（OpenAPI / 设计基线），
  再跑 `make validate-all`（m0 全量 23 项）+ 受影响定向套件 + web 门（tsc/eslint/unit/build/stub/live e2e）。
  **默认门一律离线**；live 步骤**只以单条命令的内联前缀**开
  （`RESEARCHOS_AGENT_RUNTIME=openhands`），跑前确认 `EnvCredentialResolver().has('LLM_MAIN_KEY')`
  为 `True`、**跑后不得把开关留在环境或 `.env`**。**本地不绿不得 push**。
- **④ commit**：子 PLAN 收口（RECHECK 完成后 DONE），GOAL 记录 commit 列表。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（仅 main）→ 用 GitHub
  REST API 查 main 上 `m0-quality` 最新 run（**head_sha 匹配** + `/jobs` 读六个 job 结论）→
  轮询到终态；失败时取失败 job 日志作为证据。记录 run URL + 真实终态（**禁止推测**）。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤。
  超过 fix_policy 上限或命中 escalation_triggers → `status=BLOCKED`。
- **⑦ 记录 + 下一轮**：更新 EC 状态、迭代日志、child_plans、memory_entries、状态历史；
  未达终态 → 回到 ①（cycle+1）；触顶预算 → BLOCKED。**收尾前必须回写**。

**凭据自检（每轮，硬要求）**：任何记录/日志/回显中都**不得**出现 key 值或片段；发现泄露
（**即使是可弃用的免费额度**）立即**停止并报告**，按 escalation 处置。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；**修产品优先，禁改断言迁就** |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境） | 按 `docs`/记忆中的既有配方重跑；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂/网络/依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | Mimosa/validator 命中新增项 | 按各处置文档修或登记误报；**不得绕过**；**不得宣称安全** |
| **live 面（本 GOAL 特有）** | live 用例在 CI 上 skip 是**预期**（CI 离线、无凭据） | **不**为让 CI「看到 live」而把凭据塞进 CI；live 证据**只在本地实跑产生**并落 RECHECK |

## 终止与收口

- **ACHIEVED**：EC-01…EC-06 全 PASS 且**有实跑证据** + 收口 RECHECK（独立复检，`result: PASS` 或
  `PASS_WITH_WARNINGS`）+ 本文件 `latest_recheck` 指向该 RECHECK + 「终止与收口」写明收口结论
  （含仍未处理项）。**live 样本必须真实存在**——本 GOAL 的存在理由就是消灭「如实 skip」，
  因此**不存在**「live 分支 skip 仍可 ACHIEVED」的退路：若凭据不可用或门未开，
  **停止并记 `BLOCKED`（能力边界）**，**不**把 skip 写成完成。
- **BLOCKED**：`budget.max_cycles` 触顶、或 `no_progress_stop_cycles` 连续命中、或命中
  `escalation_triggers`（含**明文凭据泄露**、把真实 runtime 设为默认、新增依赖、Accepted ADR、
  Canonical State 边界）、或**凭据不可用**导致 live 采样无法发生。写 BLOCKED 记录
  （原因/EC 状态表/收口复检/安全扫描处置/恢复条件/仍未处理的长程项），恢复条件由用户拍板。
- **ABORTED**：用户显式终止本目标。

收口时必须把「仍未处理的长程项」**如实登记**为后继入口（**不隐藏缺口**），并给出恢复条件。


### 收口结论（2026-09-21）

**GOAL-009 = ACHIEVED。** 六条 EC 全部 PASS 且有实跑证据；收口复检
`RECHECK-20260920-126` = **PASS_WITH_WARNINGS**，独立复检脚本
`scratch/verify_goal009_closeout.py` 在**当前树**与**干净 checkout** 上给出**同一结论**。

**本 GOAL 消灭的缺口**：GOAL-008 收口时那两条**如实 skip 的 live 分支**现在都有真实样本——
EC-01 跑出**本仓第一次真实 live run**（run `142f7e77-cd4d-4044-a953-79296509fd54`，probe
`verified and ok`，返回 model 名 `agnes-2.5-flash`，tokens 15219 真归账，口径恰为
`REPEATABLE_CONFIGURATION`；**终态是 `FAILED`**——协议 acceptance gate 的**设计内判拒**，
**没有**写成 SUCCEEDED），EC-04 跑出**第一条失败样本**（无效凭据 ⇒ 1 次出站 ⇒ `401 Unauthorized`
⇒ run `FAILED`、失败记录非空、**tokens 0**、失败文本**不含**凭据值）。

**收口时抓出并处理的三件事**（都由独立复检脚本而非实施叙述发现）：

1. `latest_recheck` 是**裸 ID** 且**过期**（停在 123）⇒ 改为指向本收口 RECHECK 的**仓库相对路径**；
2. `child_plans` **漂了**（只列到 123，缺 124/125）⇒ 补齐到 126；
3. 磁盘上除 `.env` 外还有一份凭据副本 **`secrets/llm_key.txt`**（**gitignored、untracked**，
   早于本 GOAL 存在）⇒ **登记为残余**，**不删除**（不是本循环该动的资产）。
   **被跟踪文件命中数 = 0** ⇒ 不构成 tracked 泄露。

**残余（不因收口消失）**：GOAL-008 的**六项人工面**原样保留（见下一节），外加本 GOAL 的
**W 列表**（`RECHECK-121` W-1…W-7 / `122` W-1…W-6 / `123` W-1…W-6 / `124` W-1…W-7 /
`125` W-1…W-6 / `126` W-1…W-6），逐条写在各 RECHECK 的 W 节。
**仍未处理的长程项**（后继入口）：ADR-0031 仍 `Proposed`；`ANTHROPIC` 的 **run** 路径仍**无 live 样本**
（EC-02 取 (b)，改绑步骤与影响面已备但未实跑）；「模型不存在」只有装配层判据、无 provider 侧样本；
本地门「离线」不是结构保证（W-7 观测到一次真实出站）；前端 drift/设计基线未由判据把守。

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 BLOCKED
（前六项**原样承自 GOAL-008**，作为残余保留）：

1. **ADR-0031（`tool_pack.*` 能力策略，`Status: Proposed`）是否采纳**——归用户拍板。
2. **威胁建模 / 授权面覆盖（BOLA / BFLA）**——需用户或 ADR 拍板。
3. **`artifacts/` 明文 token 清理**——涉及不可变历史资产与凭据面，需人工确认。
4. **450 行纪律的贴线文件**——大重构会放大 diff 风险，需人工决定。
5. **依赖 pin 升级**（`undici` / `vite` / `yaml` 等）——上游 pin 变更，需用户或 ADR 拍板。
6. **hook 侧 L3 门**——治理面，需人工决定。
7. **把真实 runtime 设为默认**——默认必须仍是 Fake；本循环只做「显式配置才启用」。
8. **为 anthropic 形态引入 SDK / 新依赖**——优先用手写 HTTP；需要新依赖即 BLOCKED。
9. **把凭据写进 CI**（哪怕是为了让 CI 里看到 live 分支）——**本循环明文禁止**；CI 必须保持离线。
10. **`ModelCompatibilityProfile` 是否按 AGENTS.md §1 建为一等域实体**——涉及 Domain 面与可能的
    Canonical State 边界，需拍板。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | （见状态历史） | 治理 `validate.py` 绿 + `validate_bundle` / DOCS-CHECK 绿 | （见状态历史） | — | EC-01…EC-06 全 PENDING；凭据**已可用**（F-2/F-3）⇒ live 采样**可以真的跑**（与 GOAL-008 建档时的「六项凭据全 absent」不同） | cycle 1 = derive EC-01 子 PLAN（live 采样第一次） |
| 1 | PLAN-20260920-121（EC-01） | `291224f`（derive + ALL_PLAN）、`dab74b0`（impl：runbook 样本 + MEM-094） | **live 分支真跑 PASS（非 skip）**：`RESEARCHOS_AGENT_RUNTIME=openhands` 内联前缀跑 `tests/e2e/test_ec04_live_first_run.py` ⇒ **1 passed / 1 skipped in 28.69s**（run id `142f7e77-cd4d-4044-a953-79296509fd54`，**终态 `FAILED`** = 设计内 acceptance-gate 判拒，`verdict = REPEATABLE_CONFIGURATION`，tokens 15219，制品 1 / 证据 1，缺项 2 已声明）；离线基线 + 反证：默认门 **1 passed / 1 skipped**、内联前缀 `-k closed` ⇒ **SKIPPED（gate is open）**、去前缀复跑回到 **1 passed / 1 skipped**（无残留）；同源判据 **10 passed**；离线同路径套件 **2 passed / 1 skipped**（独立复现「判拒是链在正常工作」）；独立复检脚本 `scratch/verify_goal009_cycle1.py` **22 checks PASS**（凭据面扫描 tracked 文件 `hits=0`，**未打印值**）；治理 `validate.py` / `validate_bundle` / DOCS-CHECK 绿 | **run 35514493092 = success**（`47c50d2` 建档推送；六 job 全 success：`quality-ubuntu-latest` / `quality-windows-latest` / `console-frontend` / `collector-quality` / `container-quality` / `eval-gate`，逐 job 实查，terminal `status=completed conclusion=success`）；cycle 1 自身的推送 run 在回合汇报里给出终态 | **m0 三轮，全部如实登记，最终 23/23**：第 1 轮 22/23（红：`python/tests` 的单条 `test_start_run_unprovisioned_control_plane_reports_actionable_failure`）、第 2 轮（空 DSN）**同一个红** ⇒ **推翻**了我第一轮的 DSN 归因、第 3 轮（`LLM_MAIN_KEY=""` 复现 CI 的「无凭据」条件）**PASS：profile=m0; 23 deterministic checks（4201 passed / 12 skipped，557.61s）**。**真根因**经反证定位：该用例对**凭据是否可解析**不封闭——前序 import 过 openhands-sdk 后 `.env` 凭据入进程 ⇒ `main` 端点（`discovery.enabled: true`）**真的做端点发现** ⇒ run 走到 `FAILED` 却不再产出 `run.failed` ⇒ 断言空集。**最小复现** `pytest tests/adapters/openhands <该用例>` ⇒ **1 failed / 83 passed** 且日志含 `GET https://apihub.agnes-ai.com/v1/models` **200 OK**；**决定性反证** 同命令加 `LLM_MAIN_KEY=""` ⇒ **84 passed** 且**零出站** ⇒ **红 ⇔ 凭据可得**，而 **CI 无 `.env`、无凭据** ⇒ **CI 不可复现**。**一次真实出站已被捕获**——「本地门离线」**不是**结构保证，作为残余登记（W-7 / MEM-20260920-095）。**未改任何断言/门禁/快照**，只改环境输入且被阻断的正是 CI 不具备的输入 | EC-01 **PASS**；EC-02…EC-06 PENDING。EC-01 的 W：W-1 终态是 `FAILED` 非 `SUCCEEDED`（设计内，须写明）、W-2 逐条失败消息未捕获、W-3 litellm 无该模型价格映射、W-4 「一致」是单次样本、W-5 缺 `system_fingerprint`、W-6 anthropic 面问题归 EC-02、W-7 全量 m0 时序 | cycle 2 = derive **EC-02**（run 自身消费 anthropic 面的二选一终态） |
| 2 | PLAN-20260920-122（EC-02） | `dcbd313`（derive + ALL_PLAN）、`2785e68`（判据 + 文档）、`86e77d8`（**CI 红修复**：MEM-094 改写进暂存） | 判据 `test_anthropic_surface_boundary.py` **10 passed** 且**被压过**（改绑 `research_alpha` ⇒ **RED**，定位精确到 run 腿那一条；复原 ⇒ **GREEN**；`git diff examples/config/models.yaml` **空**）；定向 `tests/architecture tests/loaders tests/e2e/test_ec04_*` ⇒ **145 passed / 1 skipped**；`ruff`/`format`/`mypy` 绿；治理 `validate.py` 绿；m0 两轮如实登记：第 1 轮 **stale**（在我修完行宽/类型之前启动，读旧文件 ⇒ `python/product-lint` + `python/typecheck` 红，两条都指向已修好的行；其余 **24 项 PASS**）、第 2 轮干净树 ⇒ **PASS：profile=m0; 23 deterministic checks（4212 passed / 12 skipped，592.81s）** | **run 35517481162 = failure**（`e16e458`；`quality-ubuntu-latest` / `quality-windows-latest` 红 —— `framework/validate` 报 `MEM-20260920-094` 缺章节；其余四 job success）。**CI 是对的**：本地把该条目改好了但**改写未进暂存区**，提交进去的仍是旧形态，而本地门读的是**未提交**的工作树 ⇒ **本地绿而提交红**。处置：`86e77d8` **修记录**（**不放宽 validator**），沉淀 `MEM-20260920-096`。**cycle 2 自身的推送 `86e77d8` → run 35519644853 = success（六 job 全 success），上条失败已随修复转绿** | — （**未改任何门禁/断言强度**；判据的 `::symbol` 路径处理是**让判据更对**，不是放宽） | EC-02 **PASS（取 (b)）**；EC-03…EC-06 PENDING。残余 W-1…W-6（W-1 run 腿仍走 OPENAI_COMPATIBLE、W-2「会打到 OpenAI 形态 mock」是**强推断非实跑**、W-3 判据**有意过严**、W-4 判据不覆盖执行正确性、W-5 前端列无判据把守、W-6 = 上述 CI 红已修） | cycle 3 = derive **EC-03**（漂移实测样本落到读面/记录；样本已由 cycle 1 的同一次 probe 带出：实测返回标识 == 声明值 ⇒ **一致**，不另发调用） |
| 3 | PLAN-20260920-123（EC-03） | 见回合汇报（derive + 判据 + 文档 + 收口） | 新判据 `test_live_drift_sample_same_source.py` **8 passed**，与既有 runbook 判据同跑 **18 passed in 0.95s**；**被压过（两条路径）**：①改坏 runbook §6 的返回标识 ⇒ **RED**（`1 failed, 7 passed`，消息把 `declared/returned/两态` 全打出来，定位精确到重算那一条）、复原 ⇒ **GREEN**、`git diff` 只剩意图内改动；②查**不存在的标签** ⇒ 抛错并**点名**（`… no longer has a row labelled '不存在的标签'`），**不静默返回空串**（否则「判据没在看」会伪装成「判据通过」）；定向套件（两道同源判据 + `test_protocol_vocabulary` + `tests/domain/test_model_drift.py` + `tests/api/test_models_api.py`）⇒ **47 passed in 2.03s**；`ruff check` / `format --check` / `mypy` 绿；全量 m0（**CI 同形配置**：`LLM_MAIN_KEY=""` + 测试 DSN pin）⇒ **`PASS: profile=m0; 23 deterministic checks`（4221 passed / 12 skipped，589.50s，FAIL 0 条）**，**一次跑完无 stale、无红**；治理 `validate.py` 绿 | 见回合汇报（**未跑到终态不记账**） | — （**未改任何门禁或断言强度**；**未新增 live 调用**：样本复用 cycle 1 的同一次 probe） | EC-03 **PASS**；EC-04…EC-06 PENDING。残余 W-1…W-6（W-1 单次样本 ≠ 永不漂移、W-2 反证**发现不了自洽的假样本**（由 run id 交叉引用兜住）、W-3 判据与标签行**耦合**（改标签必须同改判据）、W-4「漂移未持久化」只有文档口径无判据把守、W-5 前端 drift 渲染不在判据射程、W-6 CI 台账填写规则） | cycle 4 = derive **EC-04**（失败路径诚实语义 + 至少一条反证） |
| 4 | PLAN-20260920-124（EC-04） | `d3b8f0f`（derive + ALL_PLAN + cycle 3 CI 台账）、见回合汇报（impl + 收口） | 新判据 `test_live_failure_paths_same_source.py` **16 passed** 且**被压过**（把 §7 行标签「端点拒绝」改成「端点被拒」⇒ **RED**：`2 failed, 14 passed`，消息点名 `§7 no longer has a row labelled '端点拒绝'`；复原 ⇒ **GREEN**，`git diff` 只剩新增 26 insertions / 0 deletions）；**实跑反证（live，出站 2 次，均被拒）**：`RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_FAILURE_CASE=invalid-credential LLM_MAIN_KEY=<故意无效>` 跑 `tests/e2e/test_live_failure_paths.py` ⇒ **`1 passed`**、**1 次出站** `POST https://apihub.agnes-ai.com/v1/chat/completions` ⇒ **`HTTP/1.1 401 Unauthorized`**、观察文件 `{"run_state":"FAILED","failure_count":1,"usage_entries":0,"credential_leaked":false}`；**先断言门开再发起**（否则失败可能来自门关，语义完全不同）；预置条件式反证：默认门 ⇒ **`1 skipped`**（点名开关），带预置条件 ⇒ **`1 passed`**；离线门套件 **22 passed**；`ruff`/`format`/`mypy` 绿；全量 m0 **两轮**：第 1 轮 **`FAILED: 1 check(s): python/tests=1`**（新增用例函数 **58 行** > 本仓 **50 行**上限）⇒ **拆函数**（**不放宽门禁**）⇒ 第 2 轮 **`PASS: profile=m0; 23 deterministic checks`（4239 passed / 13 skipped，558.84s，FAIL 0）**；治理 `validate.py` 绿 | **run 35522167112 = success**（`d3b8f0f` 的 derive 推送；六 job 全 success）；cycle 4 收口推送的 run 在回合汇报里给出终态 | ①**50 行函数上限对 `tests/**` 同样生效**——新增 live 用例写成了长流水线，m0 抓出；处置是**拆函数**（`_assert_gate_is_open` / `_run_with` / `_Reads`），**不是**调阈值。②拆完**重跑**了 live 反证（让证据对应**提交形态**）⇒ 出站共 **2 次**，均被拒、均零计费（如实登记，未凑成「1 次」） | EC-04 **PASS**；EC-05/EC-06 PENDING。残余 W-1…W-7（W-1 端点拒绝那一格是**指向**既有判据而非本 cycle 重测、W-2「模型不存在」只有**装配层**判据、**无** provider 侧实跑样本、W-3 失败消息**未按内容**断言（provider 文案是外部契约）、W-4 预置条件开关是新环境变量、W-5「门开 ≠ 凭据有效」是**设计内**语义、改它是行为变更超出授权、W-6 CI 台账、W-7 出站 2 次） | cycle 5 = derive **EC-05**（凭据生命周期 runbook：注入/轮换/撤销/可弃用额度） |
| 5 | PLAN-20260920-125（EC-05） | `8d443ad`（derive + **GOAL EC-05 更正** + ALL_PLAN）、见回合汇报（runbook §8 + 判据 + 收口） | 新判据 `test_live_credential_lifecycle_same_source.py` **20 passed**（与既有 runbook 判据同跑 **30 passed in 1.26s**）；**被压过两次**：①第一次压测**发现判据自己太松**——把 §8 撤销行改写成「每次调用都读一次环境，所以立即生效」，判据**仍全绿**（当时只断言「§8 里出现过『快照』」，而别处还有这个词）⇒ 处置是**收紧判据**（`assert "新构造" in _row(label)`，**逐行**判），**不是**放过改写；②收紧后同一处改写 ⇒ **RED**（消息点名「§8 的 '撤销' 行必须写明生效边界是「新构造」」），复原 ⇒ **GREEN**，`git diff` = **59 insertions / 0 deletions**；**判据自身两次返工也如实登记**：第一版把「传 `environment=` 也是快照」写错（实测**按引用**持有）⇒ 语义按**构造方式**拆三种；且第一版用小写变量名查环境（Windows 上 `os.environ` 大小写不敏感、拷贝后的普通 dict **敏感**）⇒ 直接红，遂补成一条断言。两次返工都是**让判据更对**，未放宽断言；`ruff`/`format`/`mypy` 绿；全量 m0：首轮 **`FAILED: 1 check(s): framework/validate=1`**——治理报 `工程记忆来源不存在: MEM-20260920-099: …RECHECK-20260920-125`（**引用先于记录**），处置是**把 RECHECK 写出来**（**不是**删字段或放宽 validator），`python/tests` 同轮 **4260 passed / 13 skipped**（无红）；补记录后治理 `validate.py` **绿** | **run 35525365307 = success**（`8d443ad` 的 derive 推送；六 job 全 success）；cycle 5 收口推送的 run 在回合汇报里给出终态 | — （**未改任何门禁或断言强度**；第一次压测的处置是**收紧**判据） | EC-05 **PASS**；EC-06 PENDING。残余 W-1…W-6（W-1 判据把构造语义当**契约**钉住、改它须三处同步、W-2「按引用」只成立于测试/注入路径、W-3 大小写那条只钉住「拷贝后敏感」这一半、W-4 本 cycle **未读/未打印/未写入任何真实凭据值**、代价是不覆盖真实 `.env` 注入链路、W-5 额度声明只判在场、W-6 CI 台账） | cycle 6 = derive **EC-06**（收口复检：当前树 + 干净 checkout 同结论、m0、治理、六项人工面原样保留 + 本 GOAL 的 W 列表） |
| 6 | PLAN-20260920-126（EC-06） | 见回合汇报（收口 + 复检 + 残余登记） | 独立复检脚本 `scratch/verify_goal009_closeout.py` **四层**（A 交付物 21 / B 判据用例 8 / C 登记面 / D 凭据面），**当前树 90 checks** 与**干净 checkout 88 checks** 跑出**同一组 3 个失败**（`EC-06` 仍 PENDING、`latest_recheck` 是裸 ID 且过期）⇒ **真问题**，本收口已修；同一比对还抓出 `child_plans` 漂了（缺 124/125）与磁盘第二份凭据副本；修后复跑 + 治理 `validate.py` 绿；全量 m0 见回合汇报 | 见回合汇报（**未跑到终态不记账**） | — | **EC-06 PASS ⇒ GOAL ACHIEVED**；残余 = GOAL-008 六项人工面 + 本 GOAL W 列表（121/122/123/124/125/126 各自 W-1…W-n） | —（本 GOAL 收口） |

### CI 台账（逐 run 逐 job 实查；全部落在 main）

| 推送 | 提交 | run | 六 job 结论 |
| --- | --- | --- | --- |
| 建档 | `47c50d2` | [35514493092](https://github.com/Eswink/research-system-new/actions/runs/35514493092) | 六 job 全 **success**（`quality-ubuntu-latest` / `quality-windows-latest` / `console-frontend` / `collector-quality` / `container-quality` / `eval-gate`；terminal `status=completed conclusion=success`） |
| cycle 1 收口 | `e16e458` | [35517481162](https://github.com/Eswink/research-system-new/actions/runs/35517481162) | **failure** —— `quality-ubuntu-latest` / `quality-windows-latest` **红**（`framework/validate`：`MEM-20260920-094` 缺章节），其余四 job **success**。**归类：治理/安全门禁 → 修记录**（`86e77d8`），**不放宽 validator** |
| cycle 2（含上条修复） | `86e77d8` | [35519644853](https://github.com/Eswink/research-system-new/actions/runs/35519644853) | 六 job 全 **success**（`eval-gate` / `container-quality` / `collector-quality` / `quality-windows-latest` / `quality-ubuntu-latest` / `console-frontend`；terminal `status=completed conclusion=success`）—— **cycle 1 那条失败已随修复转绿** |
| cycle 3 | `3de73d1` | [35521188002](https://github.com/Eswink/research-system-new/actions/runs/35521188002) | 六 job 全 **success**（`collector-quality` / `console-frontend` / `quality-ubuntu-latest` / `container-quality` / `quality-windows-latest` / `eval-gate`；terminal `status=completed conclusion=success`） |
| cycle 4 derive | `d3b8f0f` | [35522167112](https://github.com/Eswink/research-system-new/actions/runs/35522167112) | 六 job 全 **success**（`eval-gate` / `quality-windows-latest` / `collector-quality` / `container-quality` / `quality-ubuntu-latest` / `console-frontend`；terminal `status=completed conclusion=success`） |
| cycle 4 收口 | `3b27bac` | [35524463053](https://github.com/Eswink/research-system-new/actions/runs/35524463053) | 六 job 全 **success**（`eval-gate` / `container-quality` / `collector-quality` / `console-frontend` / `quality-windows-latest` / `quality-ubuntu-latest`；terminal `status=completed conclusion=success`） |
| cycle 5 derive | `8d443ad` | [35525365307](https://github.com/Eswink/research-system-new/actions/runs/35525365307) | 六 job 全 **success**（`collector-quality` / `container-quality` / `eval-gate` / `quality-ubuntu-latest` / `quality-windows-latest` / `console-frontend`；terminal `status=completed conclusion=success`） |
| cycle 5 收口 | `337a2ae` | [35527501482](https://github.com/Eswink/research-system-new/actions/runs/35527501482) | 六 job 全 **success**（`collector-quality` / `quality-windows-latest` / `container-quality` / `console-frontend` / `quality-ubuntu-latest` / `eval-gate`；terminal `status=completed conclusion=success`） |
| cycle 6 收口（GOAL 收官） | 见回合汇报（**台账尾巴口径**：本条自身触发的 run 不再回写文件） | |

**台账尾巴口径**（沿用 GOAL-005…008，写死在此）：写下**本条**「CI 台账回写」提交自身触发的 run
**只在回合汇报里给出终态、不再回写文件**——否则每轮都要为回写再推一次、无限追加。
**CI 保持离线**：本 GOAL **明文禁止**把凭据写进 CI（哪怕是为了让 CI 里看到 live 分支），
live 证据只在本地产生并落 RECHECK。

## 状态历史

- 2026-09-20 cycle 1（`driver=client-goal / owner=root-agent`）：**EC-01 PASS**
  （PLAN-20260920-121 / RECHECK-20260920-121 = PASS_WITH_WARNINGS，W-1…W-7）。
  **本轮最大的事实变化：本仓第一次真实 live run 真的发生了**——GOAL-008 收口时那条
  「live 分支如实 skip」的缺口，由 GOAL-009 用**一次**真实调用序列（probe + run，次数取最小必要）
  补上：`test_live_first_run_reaches_a_terminal_state` **PASS（非 skip）**，
  run id `142f7e77-cd4d-4044-a953-79296509fd54`，probe `verified and ok`，返回 model 名
  `agnes-2.5-flash`，tokens 15219 真归账，制品与证据各 1 条可读，口径恰为
  `REPEATABLE_CONFIGURATION`。
  **本轮最要紧的诚实记录**：该 run 的**终态是 `FAILED`**——**没有**写成 SUCCEEDED。
  归类结论是**协议设计内的 acceptance-gate 判拒**（合约要 `analysis_report`、真实会话给
  `session_message`；制品 id 后缀正是 `:session_message`），依据是三条收敛证据 + 离线同路径判据
  `_assert_deliverable_adjudicated` 的既有期望（该套件本轮真跑 **2 passed / 1 skipped**
  独立复现）。**未捕获项**（逐条失败消息只活在 in-memory 事件库）已**逐字登记**，
  归类是**收敛证据**而非直读——runbook 与 RECHECK 都写明了这一点。
  **独立复检**：`scratch/verify_goal009_cycle1.py` **22 checks PASS**，四面（记录 / 同源 / 判据 /
  凭据），其中凭据面是**扫描全部 tracked 文件找凭据值、只输出命中数**（`hits=0`，**未打印值**）。
  反证：默认门 **1 passed / 1 skipped** → 内联前缀 `-k closed` **SKIPPED（gate is open）** →
  去前缀复跑回到 **1 passed / 1 skipped**（**无残留**，开关未留在环境或 `.env`）。
  **顺带带出 EC-03 的漂移原始样本**（同一次 probe，未另发调用）：实测返回标识 == 声明值 ⇒
  **一致**；**边界**：单次一致 ≠ 永不漂移，口径仍只能停在「可重复配置」。
  **CI 台账**：建档推送 `47c50d2` → **run 35514493092 = success**（六 job 全 success）。
  **未改任何判据、未改门禁、未新增依赖、未改 pin、未改默认 runtime、未把凭据写进 CI。**

- 2026-09-20 cycle 2（`driver=client-goal / owner=root-agent`）：**EC-02 PASS，取 (b)**
  （PLAN-20260920-122 / RECHECK-20260920-122 = PASS_WITH_WARNINGS，W-1…W-6）。
  **决策过程本身就是本轮的交付**：EC-02 的 (a)（改绑让 run 走 ANTHROPIC）一开始看起来更强，
  但**把影响量出来**之后结论反了——run 腿消费的是 `research_alpha` / `reviewer_gamma`
  （**不是** `agnes_flash`，它只被 probe 腿用到），而两处耦合挡在路上：
  `tests/loaders/test_contract_loaders.py` 断言 `research_alpha.endpoint_id == "main"`，
  且离线链用例的 mock **自称「最小 OpenAI-compatible 端点」**而
  `tests/e2e/live_run_support.py` 的 `point_catalog_at` **只换 `base_url`、保留 `protocol`**
  ⇒ 改绑会把 **Messages 形态**请求打到 OpenAI 形态的 mock 上，修它落在「测试与门禁」的射程内，
  正是本 GOAL fix_policy 画红线的地方。加之 `ANTHROPIC` 的 **run** 路径**从未真跑**
  （cycle 1 被 live 消费的是 probe 腿），(a) **无法不花真实调用就验证**。
  **交付**：`tests/architecture/python/test_anthropic_surface_boundary.py`（**10 checks**，
  解析链 roles → agents → binding → models → endpoints → protocol；run 腿必须落在
  `OPENAI_COMPATIBLE`；probe 腿必须指向 `agnes-anthropic`；读面必须仍暴露
  `protocol` / `endpoint_id`）+ `docs/integration/LLM_ENDPOINTS.md` **§12**
  （12.1 现在走哪一面 / 12.2 改绑步骤 / 12.3 **实测**影响面 / 12.4 判据草案）。
  **判据被压过**：改绑 `research_alpha` ⇒ **RED**（定位精确到 run 腿那一条），复原 ⇒ **GREEN**，
  `git diff` 空 ⇒ 不是恒绿、不是恒红。**判据有意过严**（改绑是架构决策，应该撞门）。
  **CI 抓到我漏掉的一条（本轮最有价值的反馈）**：cycle 1 的推送 `e16e458` 让
  **run 35517481162 = failure**——`framework/validate` 报 `MEM-20260920-094` 缺章节。
  **CI 是对的**：该条目我在本地修好了，但**改写没进暂存区**，提交进去的仍是旧形态，
  而本地门绿是因为它读了**未提交**的工作树 ⇒ **本地绿而提交红**。处置是 `86e77d8` **修记录**，
  **没有**放宽 validator；沉淀为 `MEM-20260920-096`。
  **未改任何门禁或断言强度；未新增依赖；未改 pin；未发起真实调用**（取 (b)，判据全部离线可判）。
  **CI 台账**：收口推送 `86e77d8` → **run 35519644853 = success**（六 job 全 success），
  cycle 1 的那条失败**已随修复转绿**。


- 2026-09-21 cycle 5（`driver=client-goal / owner=root-agent`）：**EC-05 PASS**
  （PLAN-20260920-125 / RECHECK-20260920-125 = PASS_WITH_WARNINGS，W-1…W-6）。
  **本轮把 GOAL 自己的一条错假设改掉了（这是本轮最要紧的事）**：EC-05 判定细则原文写
  「`EnvCredentialResolver` **每次读** `os.environ` ⇒ 同一进程内改 `os.environ` 即生效」。
  **实测证伪**（用虚构值，**不读真实凭据**）：两个解析器都在**构造时**决定来源语义，
  撤销来源后**已构造的实例仍报 `has()=True`**，只有**新构造**的实例看到变化。
  精确到**构造方式**有三种：无参 `EnvCredentialResolver()`（**生产路径**）拷贝环境 ⇒ **快照**；
  传 `environment=` 的**按引用**持有 ⇒ 看得到改动；`RegistryCredentialResolver` 一律 `dict()` 拷贝。
  处置是**改 GOAL 正文**并照实测写判据——**不是**照错假设写一条会红的判据。
  同时补上原文**漏掉**的边界：**注册表命中优先于环境变量** ⇒ 撤销环境变量**不**关这个面的门，
  必须 `unregister()`（少这条，读者会把「清空环境变量」当成万能撤销）。
  **交付**：`docs/integration/LIVE_MODEL_RUNBOOK.md` **§8 凭据生命周期**（四行固定标签表 +
  三种构造方式表 + `set -a; . ./.env; set +a` 逐字给出 + 「名字必须逐字一致」的大小写边界 +
  撤销两条边界 + 可弃用额度与纪律声明；**59 insertions / 0 deletions**，§1–§7 未动）+ 判据
  `tests/architecture/python/test_live_credential_lifecycle_same_source.py`（**20 checks**）。
  **第一次压测发现了判据自己的漏洞（本轮最有价值的一步）**：把 §8 的撤销行改写成
  「每次调用都读一次环境，所以立即生效」⇒ 判据**仍然全绿**——因为当时只断言「§8 里出现过『快照』」，
  而 §8 别处还有这个词 ⇒ **「整节在场」证明不了「这一行是对的」**。
  处置是**收紧判据**（逐行断言）后重压：同一处改写 ⇒ **RED**，复原 ⇒ **GREEN**。
  **判据自身还有两次返工**（都如实登记，且都是**让判据更对**）：①把「传 `environment=` 也是快照」写错
  （实测按引用持有）；②用小写变量名查环境变量——Windows 上 `os.environ` 大小写**不敏感**，
  但解析器拷贝出来的是**普通 dict**（**敏感**）⇒ 直接红，遂补成一条断言。
  **m0 首轮红也是对的**：`framework/validate` 报 `工程记忆来源不存在: MEM-20260920-099: …RECHECK-20260920-125`
  ——`MEM-099` 的先 `source_rechecks` 指向了**还没写**的 RECHECK（**引用先于记录**）。
  处置是**把 RECHECK 写出来**，**不是**删来源字段或放宽 validator；`python/tests` 同轮 4260 passed / 13 skipped。
  **本轮不发起任何真实调用**，且**未读 / 未打印 / 未写入任何真实凭据值**（全部用虚构值驱动）。
  **未改任何门禁或断言强度、未新增依赖、未改 pin、未改 Policy、未改默认 runtime。**
  沉淀 `MEM-20260920-099`（构造语义）+ 扩写 `MEM-20260920-097`（文档取值型判据必须**逐行**断言）。
  **CI 台账**：derive 推送 `8d443ad` → **run 35525365307 = success**（六 job 全 success）；
  收口推送的 run 在回合汇报里给出终态（**台账尾巴口径**）。

- 2026-09-20 cycle 4（`driver=client-goal / owner=root-agent`）：**EC-04 PASS**
  （PLAN-20260920-124 / RECHECK-20260920-124 = PASS_WITH_WARNINGS，W-1…W-7）。
  **本轮把「失败时该发生什么」从散文变成可判事实**，并给出本 GOAL 的**第一条真正的失败样本**。
  **先探明**（只读勘察）发现两件事：EC-04 三类情形里**有两类已有强离线判据**——
  端点拒绝由 `tests/api/test_runtime_egress_gate.py` 管（URL 策略是门链第一环、**零出站**、
  链短路、逐条点名，且带**反证不空转**），门关时的零出站由 `tests/e2e/test_ec04_live_gate_offline.py` 管
  ⇒ 本 cycle **不重复实现**，只把**指针**钉住（判据核对那两条关键用例**仍在**、套件**未被禁用**）。
  **新交付**：runbook **§7** 三类情形的**固定标签**表 + 判据
  `tests/architecture/python/test_live_failure_paths_same_source.py`（**16 checks**），钉住三条
  **最容易被误读**的语义：①**「门开」≠「凭据有效」**（门只问 `has()` 存在性 ⇒ **非空但无效也开门**；
  与「空值 ⇒ 关门」**配对**断言，两条一起才钉住）；②**run 腿不消费 fallback**
  （`build_llm` 只收**一个** `ModelDefinition`、`session_llm_factory` 不查候选——这一点**必须判**，
  因为本仓**确实有** `ModelProfile.fallback` 与 `plan_fallback`，「没有 fallback」是错的，
  正确的是「**这条路径**不消费它」）；③**重试有界**（`num_retries=endpoint.max_retries`，示例配置 = `2`）。
  **判据被压过**：把 §7 的行标签「端点拒绝」改成「端点被拒」⇒ **RED**（`2 failed, 14 passed`，
  消息点名缺哪个标签），复原 ⇒ **GREEN**（`16 passed`），`git diff` 只剩新增。
  **第一条失败样本（live，出站 2 次，均被拒 ⇒ 零额度消耗）**：用**故意无效**的凭据值（内联前缀，
  **不落任何文件**）跑新增 live 用例 ⇒ **1 次出站** `POST …/chat/completions` ⇒
  **`HTTP/1.1 401 Unauthorized`** ⇒ run **`FAILED` 终态**、失败记录 **1 条**（非空 ⇒ 不是静默失败）、
  **tokens 0**、失败消息**不含注入值**（由**断言**得出）。用例**先断言门开再发起**——
  否则「失败」可能来自**门关**，那是完全不同的语义。
  **预置条件式反证**（本用例期望就是失败，「先红后绿」不适用）：默认门 ⇒ **`1 skipped`** 并点名开关；
  带预置条件 ⇒ **`1 passed`**；离线判据另断言「带 `requires_live_llm`」「未声明即 skip 并点名」
  ⇒ 「恒过的失败测试」这条腐坏路径被堵住。
  **m0 抓出一条真缺陷（本轮最有价值的门禁反馈）**：新增 live 用例的**函数 58 行**，超过本仓
  **50 行**函数上限 ⇒ m0 第 1 轮 `FAILED: 1 check(s): python/tests=1`。处置是**拆函数**
  （`_assert_gate_is_open` / `_run_with` / `_Reads`），**不是**放宽
  `test_python_source_size_limits.py`；拆完第 2 轮 **`PASS: profile=m0; 23 deterministic checks`**
  （4239 passed / 13 skipped，FAIL 0）。因为观测必须对应**提交的形态**，拆完**重跑**了 live 反证
  ⇒ 出站共 **2 次**（如实登记，未凑成「1 次」）。沉淀 `MEM-20260920-098`。
  **复原无残留**：`.env` 未被写、产品代码与配置**无**改动、离线门套件 **22 passed**、EC-01 样本未动。
  **未改任何门禁或断言强度、未新增依赖、未改 pin、未改 Policy、未改默认 runtime。**
  **CI 台账**：derive 推送 `d3b8f0f` → **run 35522167112 = success**（六 job 全 success）；
  收口推送的 run 在回合汇报里给出终态（**台账尾巴口径**）。

- 2026-09-20 cycle 3（`driver=client-goal / owner=root-agent`）：**EC-03 PASS**
  （PLAN-20260920-123 / RECHECK-20260920-123 = PASS_WITH_WARNINGS，W-1…W-6）。
  **本轮把漂移样本从「散文」变成「判据能重算的事实」**：cycle 1 那次 probe 的原始观测
  （返回标识 `agnes-2.5-flash` == 声明值 `agnes-2.5-flash` ⇒ **一致**）此前只活在 runbook §6 的表格
  与 RECHECK-121 的叙述里——**没有任何东西**会在样本被改错时变红。本轮补上判据
  `tests/architecture/python/test_live_drift_sample_same_source.py`：从 §6 按**固定标签**解析
  （声明值 / 返回标识 / 判定 / run id），代入 `assess_model_drift` **重算**并断言相等。
  **判据被压过两次（这是本轮最要紧的证据）**：①改坏返回标识 ⇒ **RED**（`1 failed, 7 passed`，
  消息 `the runbook says 'MATCH' but re-deriving from declared='agnes-2.5-flash' /
  returned='agnes-2.5-flash-drifted' gives 'DRIFT'`），复原 ⇒ **GREEN**（`18 passed`），
  `git diff` 无残留；②压**解析路径本身**：查不存在的标签 ⇒ 抛错并**点名缺哪个标签**，
  **不静默返回空串**——这条堵的是「判据没在看」伪装成「判据通过」的腐坏路径。
  **读面同源被钉住**：`services/api/routers/models.py:151` 的读面 drift **就是**
  `assess_model_drift(model.model_name, result.returned_model_name)` 的输出（全仓该函数定义**只有一处**），
  DTO 字面量 `Literal["MATCH","DRIFT","UNKNOWN"]` 与域枚举**逐字一致**，且 `UNKNOWN` **不算**漂移
  （`is_drift` 只为 `DRIFT` 为真）——三条都由判据断言。
  **两条证明力边界写在样本旁边**：单次一致 **≠** 永不漂移；以及**漂移判定不持久化**
  （读面只在**探测过的那个进程**里显示它）。**反证自身的边界也如实登记**：改**一个**值会红，
  把**两个值同时**改成一对**自洽**的假样本**不会**红——兜住它的是 run id 必须同时出现在
  `RECHECK-20260920-121` 的交叉引用（判据已断言），**这条仍是「同一 run 的记录」而非新证据**。
  **本地门禁**：定向 **47 passed**；全量 m0（CI 同形配置）⇒ **23/23**（4221 passed / 12 skipped，
  FAIL 0），**一次跑完无 stale、无红**。
  **本轮未发起任何真实调用**（样本复用 cycle 1 的同一次 probe，次数取最小必要）、
  **未改任何门禁或断言强度、未新增依赖、未改 pin、未改默认 runtime**。
  沉淀 `MEM-20260920-097`（文档取值型判据的解析契约）。
  **CI 台账**：收口推送 `3de73d1` → **run 35521188002 = success**（六 job 全 success）。

- 2026-09-20 cycle 1 派生（`driver=client-goal / owner=root-agent`）：derive
  `PLAN-20260920-121-first-live-sampling-run`（EC-01，投影 ALL_PLAN）。**派生前的离线实跑**
  （**无网络**，两次）：默认门下 `tests/e2e/test_ec04_live_first_run.py` ⇒ **1 passed / 1 skipped**；
  以 `RESEARCHOS_AGENT_RUNTIME=openhands` 内联前缀跑 `-k closed` ⇒ 该用例 **SKIPPED**
  （跳过理由即「gate is open on this machine」）⇒ **两条开门条件在 pytest 进程内同时成立**，
  且内联前缀**没有被**导入栈的 dotenv 覆盖。据此确认 GOAL-008 的恢复条件**已满足**、
  EC-01 的 live 采样**可以真的跑**。**本步未发起任何真实调用**（判据只读门，门不自带网络面）。

- 2026-09-20 建档：GOAL **ACTIVE**（`driver=client-goal / owner=root-agent`）。承接 GOAL-008 的
  **恢复条件**——用户已注入凭据 ⇒ 本 GOAL 把 EC-04 / EC-05 的 live 分支从「如实 skip」推进到
  「有样本」。**建档前的实跑核对**（见「建档时已探明的现状」F-1…F-9）：`.env` gitignored 且含
  `LLM_MAIN_KEY`（**只测长度与存在性，未打印值**）；`EnvCredentialResolver().has('LLM_MAIN_KEY')`
  在完整导入栈里为 `True`（裸导入 `adapters.relay.credential_resolver` 为 `False` ⇒ dotenv 来自
  **litellm 导入期**，全仓 `load_dotenv` 零命中）；`.env` **不含** `RESEARCHOS_AGENT_RUNTIME`
  （`.env` 里另有一个键 `AGENT_RUNTIME`——它只是名字**以其结尾**，是**完全不同**的键，
`settings.py` 只读 `RESEARCHOS_AGENT_RUNTIME`，因此不会被它触发）；默认门下
  `evaluate_live_run_gate` 逐字返回未满足条件，**未发起任何真实调用**。**端点面**：
  `main` = `OPENAI_COMPATIBLE`、`agnes-anthropic` = `ANTHROPIC`（**均已登记**）；
  `agnes_flash.endpoint == main` ⇒ EC-02 的 (a) 需要改绑（不是零成本）。**本 GOAL 明文禁止**
  把凭据写进 CI（CI 保持离线，live 证据只在本地产生）。**未新增依赖、未改 pin、未改 Policy、
  未改默认 runtime、未改任何门禁或断言强度。**
