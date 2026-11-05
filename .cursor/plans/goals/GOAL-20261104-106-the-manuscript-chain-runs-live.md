---
id: GOAL-20261104-106
slug: the-manuscript-chain-runs-live
title: 十一相链首次真实成立
status: ACTIVE
created_at: 2026-11-04
updated_at: 2026-11-05
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    沿用用户 2026-10-29 全权限预授权；
    push-to-main-for-CI：只推 main、不 force、不重写历史、不推旁支；
    RESEARCHOS_AGENT_RUNTIME / RESEARCHOS_LIVE_E2E 逐命令传，绝不写进 .env。
objective: >-
  `examples/protocols/direction_to_manuscript_v1.yaml`（十一相：question → retrieval →
  novelty → plan → experiment → review → manuscript → editorial → revision → submission →
  report）**在真实模型 + 真实中转站下跑到一次 `SUCCEEDED`**，十一件产物全部落 canonical
  且可从读面取回字节；并把 GOAL-105 的两件机制（引用结构读数 / 应答实词重叠）在**真实手稿**
  上取证，全过程失败形态逐条归类入台账。
exit_criteria:
  - id: EC-01
    criterion: >-
      建 live 判据 `tests/e2e/test_the_manuscript_chain_runs_live.py`：以
      `direction_to_manuscript_v1.yaml` 为协议、**产品组合根** `assemble()`（一律不补缝）、
      真实 runtime、`preflight_override` 只做运维上下文。断言 ① 终态 `SUCCEEDED`；
      ② **十一件产物全部落库**且可从读面取回字节（九个会话产物 + `manuscript.md` /
      `research_report.md` + 投稿五件 + 改稿两件）；③ 读数**先写盘再断言**（失败路径也落盘）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_the_manuscript_chain_runs_live.py
      -q -rs`（凭据 + live 开关 + runtime 三者齐备时真跑；缺一如实 skip）。
      取证文件 `.cursor/plans/goals/evidence/GOAL-20261104-106-manuscript-chain-live.json` 在场。
    status: PASS
  - id: EC-02
    criterion: >-
      真实 run 收敛 `SUCCEEDED`：修掉所有阻塞（产品缺陷 / 合约措辞 / 配置 / 前置条件）。
      **每个失败形态落盘并归类**（真缺陷 / 环境 / 配额 / 中转站瞬时），不许用「重跑就绿」
      掩盖未归因的失败。
    verify: >-
      EC-01 的判据两条用例真跑通过（不是 skip）；取证文件里 `state == "SUCCEEDED"` 且
      `phase_states` 十一相全 `SUCCEEDED`。
    status: PENDING
  - id: EC-03
    criterion: >-
      GOAL-105 的两件机制在真实手稿上生效：① `manuscript.md` 脚注里三个引用读数可解析，
      且与**从正文重算**的结果逐项相等（同一份字节、同一个函数）；② `response_letter.md`
      里每条 `**Action taken.**` 与对应 `ReviewPoint.text` 有实词重叠
      （`validate_action_references` 在真实 run 上真的跑过）。
    verify: >-
      `tests/e2e/test_the_manuscript_chain_runs_live.py::test_the_goal105_readings_hold_on_the_real_manuscript`
      真跑通过；取证文件含 `citation_readings` / `readings_match_body` / `action_overlap`。
    status: PENDING
  - id: EC-04
    criterion: >-
      RECHECK 里有一节 `## 真实 run 的失败形态台账`，把 EC-02 过程中出现的**每一个**失败
      形态写成一条：现象 / 读面证据 / 归类 / 修法 / 是否修好。**零归因的失败不许留在台账外**。
    verify: >-
      `RECHECK-20261104-106` 含该二级标题且每条含五列；`verify_goal106_closeout.py` 断言它存在
      且条目数 ≥ 实际记录的失败形态数。
    status: PASS
  - id: EC-05
    criterion: >-
      文档同步：`docs/architecture/MANUSCRIPT_QUALITY.md` 补一句「十一相链于 YYYY-MM-DD 首次
      真实 `SUCCEEDED`（run id / protocol），此前只有 mock e2e」。**§7 判定表逐字不动**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_manuscript_quality_strong_criterion.py -q`
      全绿（含 `len(NOT_JUDGED) == 5`）；文档 grep 命中新句。
    status: PASS
  - id: EC-06
    criterion: >-
      收口资产 `tools/verify_goal106_closeout.py` + `tools/goal106_closeout_assertions.py`，
      登记进 `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的 `_VERIFIERS`。
      验证器必须断言「真实 run 的读数文件在树」（不是「散文说跑过」）。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal106_closeout.py --root . --verdict-only`
      全 PASS、判词不含绝对路径；脚本过 ruff / mypy / 规模门。
    status: PENDING
  - id: EC-07
    criterion: >-
      宪章记账：程序表追加序 74（紧接序 73、**不留空行**）；阶梯「报告」/「实验」/「复检」行
      按**实际**推进写；进展/修订各追加一行（5 格、表内连续）后各 4 行 ⇒ **归档最旧一行**
      （进展序 71 = `GOAL-20261101-103`，修订序 71）。
    verify: >-
      `tests/tooling/test_mainline_program_is_intact.py`、`test_mainline_research_ladder_advances.py`、
      `test_mainline_archive_is_continuous.py`、`test_short_archive_revision_rows_are_registered.py`
      全绿；两表各 2 行 + 归档指针在末个数据行之后。
    status: PASS
budget:
  max_cycles: 40
  per_cycle_minutes: 180
  no_progress_stop_cycles: 2
fix_policy:
  allowed:
    - 按判据点名修产品缺陷（判据先红后绿，逐条留证）
    - 新增判据文件与两向按压（每条新判据都有反证臂）
    - 修记录缺陷（如 `PHASES` 元组已是 11 项而注释仍写「十个相」—— GOAL-102 漏改计数）
    - 改合约措辞 / 配置 / 前置条件，只要判据不降级
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - "不得为了绿而减相 / 减产物 / 放宽判据（真跑证明不可达 ⇒ 登记 BLOCKED，不删）"
    - "不得把「重跑就绿」当作失败归因（每个失败形态必须归类并落盘）"
    - "不得在无 Docker 的环境下把实验相失败判成产品缺陷"
    - "不得对外部评审面板做任何实现（它在长期路线，需用户拍板模型调用）"
    - 改 `.github/workflows/**`（本轮关闭，任何改动停 BLOCKED）
    - 改 `TrustLabel` 语义 / 动 `RunManifest` 冻结面
    - 改十一相相集 / 新增角色或能力（角色 27、能力词表 47 钉死）
    - 改 §7 判定表 / `NOT_JUDGED` 五项
  same_signature_retries: 3
  cycle_fix_retries: 6
escalation_triggers:
  - 改 TrustLabel 语义 / 动 RunManifest 冻结面 / 改 .github/workflows/**（须用户拍板）
  - 整条撤销 §9 默认 deny（§9 姿态只放开点名项）
  - 同一失败签名超过 fix_policy 上限（连续 3 次同一失败签名 ⇒ 停下分析）
  - 新增第三方依赖
  - 实现外部评审面板（引入模型调用判叙述质量 ⇒ 须用户拍板）
child_plans:
  - .cursor/plans/tasks/PLAN-20261104-106-manuscript-chain-live.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261104-106-manuscript-chain-live.md
memory_entries: []
---

# GOAL-20261104-106 —— 十一相链首次真实成立

## 目标与退出标准

承用户 goal-mode 指令（序 74）。本轮只有**一个靶子**：`direction_to_manuscript_v1.yaml`
（十一相）在**真实模型 + 真实中转站**下跑到一次 `SUCCEEDED`，十一件产物全部落 canonical
且可从读面取回字节。

**为什么这是本轮**（2026-11-04 全仓 115 个 SQLite 文件逐一普查的实测读数）：

```text
console_demo_research_v1    FAILED 2
direction_to_question_v1    FAILED 30 / SUCCEEDED 5
direction_to_report_v1      FAILED 1  / SUCCEEDED 1
direction_to_report_v2      FAILED 3  / SUCCEEDED 2
dual_model_review_v1        FAILED 24 / SUCCEEDED 0     ← 正确行为，见 F-1
direction_to_manuscript_v1  合计: 0                      ← 本轮的靶子
```

**零次**。它只被两种东西验证过：① `tests/e2e/test_direction_to_manuscript_product_path.py`
（**mock 中转站** + 离线 Europe PMC + 真容器实验）；②
`test_productive_entry_runs_the_whole_chain.py`，而那条跑的是 `direction_to_report_v2`
（七相）、不是十一相。GOAL-099/100/101/102/105 五轮交付的全部机制（IMRaD 手稿 / 编辑四值
决定 / 逐条应答 / 投稿包五件 / 引用结构读数）**全部落在这条从未真跑的链上**。

**本轮不做的事**：不实现「外部评审面板」。它在长期路线 1，要评的是**手稿**；手稿链本身
从未真跑过 ⇒ 在未验证的地基上加「谁来评」的第二层，等于让新机制也只被 Fake 验证。
先让链真跑，再谈谁来评。

## 循环入口协议

1. 读本文件「迭代日志」最后一行 → 若该 cycle 未收口，从其「下一轮输入」续；
2. 读 `latest_recheck`（若非 null）→ **未 PASS 不得进入收口**；
3. 七个 EC 全部 PASS 且 CI 到终态 ⇒ 进「终止与收口」；
4. 任一 EC 被结构性堵住（需用户拍板的面 / 上游不可用）⇒ 移入「残余与未覆盖范围」的
   待拍板队列，**继续做剩下的**，GOAL 保持 ACTIVE；
5. 工作树上有**别人**的未提交改动（并发驱动）⇒ 只 add 本 cycle 的显式路径，绝不 `add -A`。

## 单 cycle SOP

① derive（从剩余 EC + 上一轮「剩余差距」圈最小主题）→ ② 执行（WP 逐条 commit）
→ ③ 本地验证（定向套件 + 全量 m0 见证）→ ④ commit（显式路径）
→ ⑤ push main + CI 轮询 → ⑥ 纠错（按分类）→ ⑦ 回写记录 + 下一轮。

**记录顺序（GOAL-019 的教训）**：写全部记录 → `git add` 全部受判文件 → 记录面判据
→ **最后**跑 `tools/run_m0_with_witness.py`（`.cursor/plans` 在
`test_reproducibility_wording.py` 的扫描面内 ⇒ 先跑门后写记录 = 记录从未被门覆盖）。

**顺序纪律（本轮）**：**先探针真跑**（不做任何修改）看十一相链卡在哪里，再决定修什么 ——
这是 EC-02 的起点，也是唯一能告诉你「该修什么」的读数。不要先读代码猜。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff / eslint / tsc / mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest / playwright 断言 | 读失败输出定位缺陷（产品 vs 测试各半）；**修产品优先，禁改断言迁就** |
| live 判据在 CI 上 skip | `requires_live_llm` 无凭据 | **这是预期**：live 判据只在操作者本地跑；skip 不是 PASS，如实记 |
| 视觉基线漂移 | `design-fidelity` / outline 判红 | 本轮不动前端 ⇒ 若红即真缺陷或环境漂移，逐类登记 |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境） | 按既有配方重跑；配方不覆盖 ⇒ 归类下一行 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 ⇒ BLOCKED（infra 非代码缺陷） |
| 上游文献源不可用 | Europe PMC `503` / NCBI esearch `500` | **不是产品缺陷**：落盘取证 + 轮询等窗口；判据不得因此放宽 |
| 治理/安全门禁 | Mimosa / validator 命中新增项 | 按各处置文档修或登记误报；不得绕过；不得宣称安全 |

## 终止与收口

- **ACHIEVED**：七个 EC 全 PASS + 独立 RECHECK（PASS / PASS_WITH_WARNINGS）+ 全量 m0 见证
  终态行 + CI 到终态 + 两树复检（`tools/two_tree_recheck.py --script-mode shared`，两树逐行
  \+ `sha256` 相同）+ 本文件收口。
- **BLOCKED**：命中 `escalation_triggers`，或同一失败签名超过 `fix_policy` 上限，
  或 `budget.max_cycles` 触顶。
- **ABORTED**：用户撤销目标。
- 三个终态都必须把「残余与未覆盖范围」写实（含**没做到**的那部分），不得留空。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261104-106 | （见 CI 台账） | 探针真跑 1 次（`scratch/goal106-probe-p1.json`）；mock e2e 9 passed；判据取数自检绿 | 见台账 | F-5 注释计数修（`PHASES` 11 项 vs 注释「十个」） | EC-02 等上游窗口 | 上游恢复后重跑探针 |

## 影响报告

（**实测**，非预判。）

- **Domain/API/schema**：**零变化**。本轮不改相集（十一相仍钉在
  `tests/contracts/test_direction_to_manuscript_protocol.py:44-62`）、不改角色数（27）、
  不改能力词表（47）、不改任何 DTO ⇒ `docs/api/openapi.m13.json` 零 diff、`types.ts` 零改动、
  零 migration。
- **产品代码**：**零改动**。本轮交付的是**判据**（`tests/e2e/test_the_manuscript_chain_runs_live.py`）、
  **收口资产**（`tools/verify_goal106_closeout.py` + `tools/goal106_closeout_assertions.py`）、
  **记录**（GOAL / PLAN / RECHECK / 宪章 / 文档）与一处**记录缺陷修正**
  （`tests/e2e/direction_to_manuscript_support.py` 的「十个相」→ 十一相注释）。
  真跑暴露的阻塞全部归**上游**（见 RECHECK 的失败形态台账 `F-1` / `F-7`）。
- **安全/凭据**：零变化（无新凭据、无新出网面、无新工具面）。真跑沿用既有运维路径
  （`LLM_MAIN_KEY` 注入 + 显式 `preflight_override`），凭据值不读、不回显、不落盘。
  `tools/credential_audit.py` 四面 `offenders=0`（收口时以实测数为准）。
- **兼容性/迁移**：零 migration、零协议改动。
- **上游版本**：零依赖变化。
- **上游可用性（本轮的真实读数，必须登记）**：2026-11-05 约 12:59→13:43（UTC+8）之间，
  **Europe PMC 搜索后端**连续 `503`（`scratch/goal106-upstream-poll.log` 逐分钟 48+ 次，
  最大同一状态码），**NCBI esearch** 同时坏且**两种形态并存**（`500`，以及 `200` 但正文为
  `{"esearchresult": {"ERROR": "Search Backend failed…"}}`）。同一主机上 EPMC 的其它路由与
  NCBI 的 `einfo` 都正常 ⇒ 坏的是**搜索引擎后端**，不是网络、不是我们的调用形态。

## 残余与未覆盖范围

（**没做到**的那部分，逐条明写。空着等于宣称「没有缺口」，那是伪造验证证据。）

### 残余（本轮已交付里仍然存在的缺口）

- `W-1`｜**EC-02 / EC-03 未达成（本轮结束时仍在等上游窗口）**：十一相链**尚未**在真实模型
  + 真实中转站下跑到 `SUCCEEDED`。两次真跑都停在同一个相（`retrieval`），失败原因是
  **第三方文献源不可用**（EPMC `503` / NCBI 搜索后端 `500` 与「200 带 ERROR」并存），
  不是产品缺陷。判据、收口资产、记录、宪章记账已全部就位；**只剩真跑**。
  这不是「重跑就绿」—— 每一次尝试的读数与归类都在 RECHECK 的台账里（`F-1` / `F-7`）。
- `W-2`｜**相级进度读面不把 run 级汇编制品挂到 `report` 相**：`manuscript.md` / 投稿五件 /
  改稿两件的 id 是 `{run_id}:<name>`（没有任务段），因此 `RunDetailDto.phases` 只把
  `research_report.md` 挂在 `report` 相。本轮的判据据此分两面取证（会话产物按相归属判、
  汇编制品按在场 + 字节判），**没有**改产品读面 —— 「run 级制品的相归属该不该可读」是
  一个独立的产品决策，本轮不动。
- `W-3`｜**判据的取数函数只用 mock 链自检过，还没有在真跑上跑过一次**：
  `scratch/goal106_judge_selfcheck.py` 证明的是「取数正确」（同一份装配产出的同形状字节），
  不是「真实模型产物上的取数正确」。真实模型的产物形状可能多出夹具没有的边角。
- `W-4`｜**诊断变体不是 EC-02 的通过条件**：把检索 provider 实例换成 NCBI 的那次运行
  （`scratch/goal106-ncbiprobe-n1.json`）属**运维替代**，只用来把「阻塞点在检索出口」与
  「其余十相能走」分开；产品的出厂装配只造 `europe_pmc`。把它当成「链跑通了」属于伪造。

### 未覆盖范围（本轮**没有**触及的面）

- `U-1`｜**外部评审面板未做**（刻意不做）：它是长期路线 1，要评的是**手稿**，且引入模型调用
  判叙述质量 ⇒ 需用户拍板。前提是链真跑通 —— 而链本轮**还没**跑通。
- `U-2`｜**手稿的叙述质量与事实一致性仍未判**：本轮只取证「链成立」与「两个结构读数可读」，
  `NOT_JUDGED` 五项逐字未动，§7 的判定表一字未改。

### 声称边界（**不得宣称**的事）

- `R-1`｜**不得宣称「十一相链已经真实成立」** —— 只要 `W-1` 还在，这条就是假的。
  已交付的是**判据 + 收口资产 + 一次性归因**，不是那条链的成功读数。
- `R-2`｜**不得把上游不可用说成产品缺陷**，也不得把「判据在 CI 上 skip」说成 PASS。
- `R-3`｜**不得宣称手稿写得好**：本轮判的是结构（产物在场、字节可读、读数可解析、
  实词重叠），不是叙述质量。

## 状态历史

- 2026-11-04：建档（ACTIVE）。序 74。
- 2026-11-05：cycle 1 —— charter 读取、前置检查（Docker + 镜像 + 凭据 + 端点）全过；
  探针真跑第一次：`question` 相成功、`retrieval` 相在 Europe PMC `503` 上失败
  （`run-chain capability step failed: europe pmc temporarily unavailable`）⇒ 归**上游**
  基础设施，不是产品缺陷。EC-01 判据建成并自检。
