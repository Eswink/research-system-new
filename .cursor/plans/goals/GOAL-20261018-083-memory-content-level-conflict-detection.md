---
id: GOAL-20261018-083
slug: memory-content-level-conflict-detection
title: 记忆的内容级冲突检测（说法真的相反时要判得出来）
status: ACTIVE
created_at: 2026-10-18
updated_at: 2026-10-18
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    战役宪章（`.cursor/plans/goals/MAINLINE.md`）「科研能力阶梯」的**证据**域 `下一级是什么`
    逐字写的是「**内容级冲突检测**（现只校验声明的完整性，声明本身写的是对是错无人判）」；
    同文件「战役级核算（2026-10-18）」把它列为**第一候选**（「纯判断逻辑改动，不动协议与读面
    契约」）。承用户 2026-10-06 全部权限下放 + 2026-10-14 方向指令（「每一次自动迭代都必须让
    科研能力越来越近」）。授权要点：
    (1) **本 GOAL 必须让阶梯前进**（由 `tests/tooling/test_mainline_research_ladder_advances.py`
    机械强制）。
    (2) **不做**：默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA /
    D 组审批通道 / 部署面验证 / `R-M1` / destructive 能力改 allow / 为凑数扩承接面 /
    宣称项目安全 / 宣称投递语义为「恰好一次」（**明确否认**）/ **不引入任何模型调用做冲突判定**
    （见 `forbidden`）。
    (3) **来源与授权口径**：push-to-main-for-CI（只推 `main`、不 force、不重写历史、不推旁支）；
    默认 runtime 保持 Fake、默认 CI 离线（`RESEARCHOS_AGENT_RUNTIME` / `RESEARCHOS_LIVE_E2E`
    **不进 `.env`**）。

objective: >
    让**两条记忆的说法真的相反**这件事**判得出来**，而不是**只有**提案方主动声明时才看得见：
    在记忆提交门链的 `contradiction` 阶段增加**内容级**判定（确定性、零出网、可复核），
    并让判定结果在**既有读面**（`GET /projects/{id}/memory` 的处置与理由）**可读出**；
    判据成对：**说法相反且无人声明 ⇒ 判出冲突并点名两条 id** + **说法不相反 ⇒ 不判冲突**
    （不 false-positive）。

exit_criteria:
  - id: EC-01
    criterion: >-
      **判定存在且确定性**：门链新增**内容级**冲突判定（纯函数，输入两条 `MemoryRecord` 的
      正文，输出「是否相反 + 判据形态」），**零出网、零模型调用**；同一对输入**逐次同结果**
      （无随机、无时间依赖）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/memory/test_content_conflict_detection.py -q`
      ⇒ 全绿；判据覆盖：正向（相反）/ 反向（同义、无关、互相包含）/ 重复调用同一结果 /
      空正文与超长正文的处理**点名**。
    status: PASS
  - id: EC-02
    criterion: >-
      **接进既有门链，且不放宽既有语义**：`contradiction` 阶段在**保留**原引用完整性校验
      （被引 id 存在、不得自指）的前提下增加内容级判定；**未声明冲突但内容相反 ⇒ 提案被拒
      并点名两条 id**；既有「声明了冲突就落 `CONFLICTED`」的行为**逐字不变**。
    verify: >-
      `tests/application/memory/test_content_conflict_gate.py` ⇒ 全绿；反证：把内容级判定
      关掉 ⇒ 「未声明但相反」的那条**又变回通过**（证明它真的在起作用）；
      既有 `tests/application/memory/**` 全绿（零回归）。
    status: PASS
  - id: EC-03
    criterion: >-
      **读面可读出**：冲突的**来源**（声明 vs 内容判定）在既有读面上**分得开** ——
      `GET /projects/{id}/memory` 的处置理由能点名「是内容判定判出的冲突」，
      而不是与「提案方声明」混成同一句话。
    verify: >-
      e2e `tests/e2e/test_content_conflict_reaches_the_read_face.py` ⇒ 两种来源各自的判词
      **不同且各自点名**；反证：抹掉来源标记 ⇒ 判据红。
    status: PASS
    scope_note: >-
      **改判经过（如实）**：本条原写 e2e「读两种 422 判词」，实测发现
      `MemoryProposalDto` **不接受** `contradictions`（`extra="forbid"`）—— HTTP 写面
      **根本没有「声明冲突」这条路**（只有进程内用例能声明）⇒ 「两种来源在读面分得开」
      在今天的 HTTP 面上**无法成立**（读面只会有内容级一种来源）。⇒ 本条改判**门链层**
      （两种来源唯一共存的层），并**新增一条断言钉住那个 API 缺口**（
      `test_the_http_proposal_dto_does_not_expose_declarations`）—— 将来若补上写面入口，
      那条会红，届时更新判据与残余，而不是让它默默变绿。

  - id: EC-04
    criterion: >-
      **不 false-positive**：一组**真实语料**（仓内既有的记忆夹具 + 至少 8 对同义 / 无关 /
      互相包含的正文）上**零误报**；判据把语料与期望逐条钉住（不是「看起来没问题」）。
      **若某些形态本质上判不了（例如需要世界知识才能判「相反」）⇒ 明确登记为不判**，
      不假装判得了。
    verify: >-
      `tests/application/memory/test_content_conflict_precision.py` ⇒ 全绿；判据逐条列出
      语料与期望；**射程边界**在 GOAL 与判据里**逐条明写**（判不了的形态写清楚）。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口**：验证器进树（复用 `tools/closeout_recheck_assertions` 标准断言集）+
      两树复检（判词归档**进树**、二进制写盘、CR=0）+ as-is m0 23/23
      （**在全部记录写入之后**、**静止工作树**）+ 治理绿 + 凭据审计 + CI 台账**逐提交**
      （`cancelled` 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**；自我指涉边界
      **明写并封闭**）+ 残余与未覆盖范围逐条。**★ 并含阶梯记账（两个面）**：
      向宪章 `进展记录` 追加本行（**能力域 = 证据**）**且**更新阶梯「证据」行的
      `依据 GOAL`，使两个面都收录本 GOAL。
    verify: >-
      验证器本树 `--verdict-only` 全 PASS；`tools/two_tree_recheck.py` 两树判词逐行相同 +
      `sha256` 相同；m0 终态行 `PASS: profile=m0; 23 deterministic checks`；
      `validate.py` = `Cursor 治理验证通过`；台账逐 run 逐 job（含 `run_attempt`）。
    status: PENDING

budget:
  max_cycles: 14
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator / 门禁 / 快照 / 测试断言使其通过
    - 放宽任何既有判据的断言、词表、扫描面或阈值
    - 把受判面写成交集、并集掩蔽或写法清单
    - 收窄既有受判面而不逐条申报（逐条枚举 + `numstat` 删除行读数 + 谓词比对）
    - 改 `default_effect: DENY` / 放宽 §9 / 新增任何 allow
    - >-
      **用模型/网络做冲突判定**：判定必须是**确定性纯函数**（零出网、零模型调用）——
      引入 LLM 判「说法是否相反」会让门链变成不可复现、也不可离线判的东西
    - >-
      把内容级判定做成「总是判冲突」或「总是放行」：前者会把所有记忆写入掐死，
      后者等于没做；两种都算未达成
    - 把 `research_report_plan` 之外**无关**的合约 / 协议改出本轮射程
    - 把 `RESEARCHOS_AGENT_RUNTIME` 或 `RESEARCHOS_LIVE_E2E` 写进 `.env`
    - >-
      把真实凭据（`sk-…` / `cpk-…` 等）写进**任何 tracked 文件**；
      判据自证 = `tools/credential_audit.py` 四面 `offenders=0`
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 新增任何依赖
    - 宣称项目安全（`R-M1` 未收口）；宣称投递语义为「恰好一次」（**明确否认**）

escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - >-
    **真实凭据出现在 tracked 文件里**（含记录）—— **立即 BLOCKED** 并清理
  - >-
    **内容级判定需要世界知识才能判的形态**（例如「A 比 B 好」vs「B 比 A 好」之外的
    语义矛盾）—— 明确**登记为不判**，**不**用启发式硬凑；若某形态的必要性被证明是
    验收前提 ⇒ 记 BLOCKED 留拍板

child_plans:
  - .cursor/plans/tasks/PLAN-20261018-511-goal-083-ec01-content-level-conflict-detection.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-512-goal-083-ec01-content-level-conflict-detection.md
memory_entries: []
---

## 目标与退出标准

**一句话**：让**两条记忆的说法真的相反**这件事**判得出来** —— 阶梯「证据」域的 `下一级`。

**主线归属（宪章要求逐条声明）**：

- **轴** = **质量**（产出的可判定性：结论有来源支持、且**相互矛盾的说法不会被静默当成并存知识**）；
- **能力域** = **证据**（阶梯逐字：`内容级冲突检测`）。

## 为什么这一条更近科研（**建档实测**，逐条带读数）

1. **三个关键函数名全仓零命中**：`detect_content_conflict` / `conflicts_with` /
   `content_conflict` —— `rg` 扫全仓（`packages/` / `services/` / `adapters/`）**都是 0**。
2. **门链的 `contradiction` 阶段只查引用完整性**（`packages/application/memory/gate.py:81`
   `_contradiction_check`）：被引 id **存在** + **不得自指**；**正文一个字都不看**。
3. **读面的 `CONFLICTED` 只来自声明**：`adapters/canonical/memory_read.py` 的
   `conflicted_by` 传的是 `_unresolved_declarers(...)` —— 即「谁在 `contradictions` 里点了它」；
   `MemoryRecord.contradictions` 由**提案方**填写。
4. ⇒ **后果**：两条记忆**说法真的相反**、但**没人声明**时，读面照旧报 `USE`（「照用」）——
   一份自相矛盾的知识库在处置面上与一份一致的知识库**不可区分**。

**本 GOAL 不加新依赖、不引入模型调用、不放宽任何判据。** 内容级判定必须是**确定性纯函数**
（零出网），否则门链会变成不可复现、不可离线判的东西 —— 那是往反方向走。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **确定性纪律**：判定**不得**读时钟、**不得**随机、**不得**出网、**不得**调模型；
- **射程纪律**：判不了的形态**明确登记为不判**（`EC-04`），不用启发式硬凑；
- **不改契约纪律**：读面 DTO 只**追加**字段 / 复用既有处置与理由（不新造第二套读面）；
- **凭据纪律**：每一批提交前跑 `tools/credential_audit.py` 自证 `offenders=0`。

## CI 失败分类与纠错

沿用既有四类（lint/typecheck / 产品测试失败 / flake-env / 基础设施）。基础设施红须三条取证；
时序型 flake 按既有纪律 `rerun-failed-jobs`，**不改阈值**，首轮红如实登记。

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 全 PASS 且有实跑证据 + 独立 RECHECK + 本文件收口
  （`latest_recheck` 为**仓库相对路径**）+ CI 台账到终态 + 残余与未覆盖范围逐条
  + **阶梯记账成立（两个面）**。
- **BLOCKED**：命中任一 `escalation_triggers` / 同一失败签名超过 `fix_policy` 上限 /
  `max_cycles` 触顶 / 连续 `no_progress_stop_cycles` 轮未推进任何 EC。
- **ABORTED**：用户撤销。

## 残余与未覆盖范围（逐条明写）

**建档时已知的残余**（将在各 cycle 如实更新）：

- `W-1` —— **EC-05 本身**在收口复检跑之前仍是待办。
- `W-2` —— **判定只能是「形态级」的**：确定性纯函数判不出需要**世界知识**的矛盾
  （例如「该药有效」vs「该药无效」在字面上毫无重叠）。**射程边界**：本 GOAL 只判
  **可机械判**的形态（否定极性、数值方向、同一主语-谓语的相反断言），其余**登记为不判**。
- `W-3` —— **不做跨 tier 的全库扫描**：判定发生在**写入时**（提案 vs 既有记录），
  不给存量记忆批量补判（那属迁移，需单独设计）。
- `W-4` —— **不改变**既有 `contradictions` 声明面的语义；声明仍由提案方给出。
- `W-5` —— **HTTP 写面没有「声明冲突」入口**（`MemoryProposalDto` 不含 `contradictions`，
  `extra="forbid"`）：本轮实测发现。⇒ 读面上目前**只有内容级**一种冲突来源；
  补这个入口属**写面契约改动**，不在本 GOAL 射程。判据
  `test_the_http_proposal_dto_does_not_expose_declarations` 钉住该事实（补入口时会红）。
- `W-6` —— **无单位数字不判**（实测取舍）：`the metric is 2.0` vs `the metric is 0.5`
  在**没有单位**时**不判** —— 无单位数字既可能是量值也可能是编号（`mem-1` / `内容 1`），
  两者不可区分；把编号当量值会产生误报（`EC-04` 实测三条）。⇒ 数值形态只认**带单位**的度量值。

**未覆盖范围**（逐条明写；本 GOAL **不声称**已解决）：

- **读面认证**、**多租户·RBAC·BOLA·BFLA**、**部署面验证**、**D 组审批通道** —— 均**不做**；
- **用 LLM 判语义矛盾**（与确定性纪律冲突）—— **不做**；
- 默认 runtime 改真（§11）—— 默认仍是 Fake；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」（**明确否认**）。

## 不进入循环 / 需人工拍板

- 默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA / D 组审批通道 /
  部署面验证 —— **均不做**；
- **世界知识级的语义矛盾判定** —— 需人工拍板（本 GOAL 只做确定性形态级）；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 建档提交同批推送 | 见「状态历史」 | 见「CI 台账」 | — | EC-01…EC-05 PENDING | cycle 1 = EC-01（确定性判定 + 射程边界） |

## CI 台账

（逐 run 逐 job；`cancelled` 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | job 结论 |
| --- | --- | --- | --- |

**自我指涉边界（明写并封闭）**：受判的是**代码面**与**收口面**的 CI；只改 `.cursor/plans/**`
的记录提交，其 CI 照实登记但**不再**为它追加新行 —— 边界在「收口时的 tip 那一行」闭合。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | **ACTIVE** | **建档**：承 GOAL-082 收口后的战役级核算（「证据域内容级冲突检测」= 第一候选）。**定位** = 阶梯「证据」域的 `下一级`。**建档实测四条**（逐条带读数）：① 三个关键函数名全仓零命中；② 门链 `contradiction` 阶段只查引用完整性（正文一个字都不看）；③ 读面 `CONFLICTED` 只来自声明（`_unresolved_declarers`）；④ 后果 = 说法真的相反但无人声明时读面报 `USE`。 |
