---
id: GOAL-20260920-009
slug: live-sample-and-anthropic-surface-closure
title: live 采样与 anthropic 面收口：把 GOAL-008 如实 skip 的 live 分支推进到有真实样本，并给「run 自身消费哪一面」一个一等终态
status: ACTIVE
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
  - id: EC-05
    criterion: >-
      **凭据生命周期 runbook 落地**：把本机 `.env` 注入、`set -a; . ./.env; set +a` 的加载方式、
      **轮换**（换值即生效、无需重启 API 的边界与不成立的情形）、**撤销**（清空值 ⇒ 门**自动关闭**）
      写成**同源判据**（文档里的仓库路径/变量名/pytest 目标必须可解析，沿用 EC-06 的判据形态）；
      含「**本 key 为免费可弃用额度**」的说明与「值不落任何文件」的纪律复述。
    verify: >-
      同源判据套件 PASS（文档路径/变量名/pytest 目标全部可解析）；轮换与撤销各有一条**实跑**证据
      （先使门关、再使门开，或反之），**全过程无凭据值出现在任何记录/日志/回显**。
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
child_plans: []
latest_recheck: null
memory_entries: []
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
| EC-01 | live 采样第一次：live 分支四段全中（probe ok / 到终态 / 指纹可判 / usage 归账 / 制品证据可读），口径停在 `REPEATABLE_CONFIGURATION`；样本如实登记 | `RESEARCHOS_AGENT_RUNTIME=openhands … pytest tests/e2e/test_ec04_live_first_run.py -v` ⇒ 该用例 **PASS 非 skip**；落盘 `live-run-record.json` 的 `verdict == REPEATABLE_CONFIGURATION` | PENDING |
| EC-02 | run 自身消费 anthropic 面的口径（二选一终态）：(a) 改绑使 run 走 ANTHROPIC 到终态，或 (b) 把「run=main / probe=anthropic」写成一等边界 + 改绑草案；决策必须落记录 | (a) live run 记录里 run 端点 `protocol == ANTHROPIC` + 终态 + 归账；(b) 同源判据 PASS + runbook 含改绑步骤/影响面；两条都要求 RECHECK 写明选了哪条与为什么 | PENDING |
| EC-03 | 漂移实测样本：实测返回 model 名 vs 声明值，三态从「未知」变「实测」；不同则如实记为漂移并给影响面，相同则写明证明力边界 | 记录含真实样本（返回名/声明值/判定/时间/run id）且经既有读面可取；「未知 ≠ 无漂移」钉住用例仍 PASS；**不额外发起调用** | PENDING |
| EC-04 | 失败路径诚实语义（反证式）：无效凭据/端点拒绝/模型不存在三类可判定；至少一条反证先红后复原，全程不打印值 | 反证的先红后绿证据 + 三类期望语义明文；复原后复跑 EC-01 判据确认无残留 | PENDING |
| EC-05 | 凭据生命周期 runbook：注入（`set -a; . ./.env; set +a`）/轮换/撤销/可弃用额度说明落成同源判据 | 同源判据套件 PASS；轮换与撤销各有实跑证据；无凭据值出现在任何记录/日志/回显 | PENDING |
| EC-06 | 收口复检 + 残余登记：独立复检（当前树 + 干净 checkout 同结论）+ m0 23/23 + 治理 validate 绿；六项人工面原样保留 + 本 GOAL 的 W 列表 | 复检脚本三层判据全 PASS 且两树同结论；m0 23/23；`validate.py` 绿；`latest_recheck` 指向 PASS/PASS_WITH_WARNINGS；frontmatter 与状态表一致 | PENDING |

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
- **轮换**：换值即生效的**边界**——`EnvCredentialResolver` 每次读 `os.environ` ⇒ 同一进程内
  改 `os.environ` 即生效；**但**已注入 `RegistryCredentialResolver._registry` 的内存副本
  **不会**随环境变量变化（GOAL-008 runbook §3 的机制）⇒ 写明「哪些面不需要重启、哪些面需要」。
- **撤销**：清空值 ⇒ `has()` 为 `False` ⇒ **门自动关闭**（fail-closed）。**判据**：撤销后
  `evaluate_live_run_gate` 必须 `open=False` 且理由点名凭据不可解析。
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

## 状态历史

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
