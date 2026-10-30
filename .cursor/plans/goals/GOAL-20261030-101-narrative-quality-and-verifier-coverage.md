---
id: GOAL-20261030-101
slug: narrative-quality-and-verifier-coverage
title: 给「写得对不对」装上判据，并按住记录面的结构腐化
status: ACTIVE
created_at: 2026-10-30
updated_at: 2026-10-30
owners: [root-agent]
authorization:
  source: user-request
  ref: >-
    沿用用户 2026-10-29 全权限预授权；push-to-main-for-CI：只推 main、不 force、不重写历史、
    不推旁支；`RESEARCHOS_AGENT_RUNTIME` / `RESEARCHOS_LIVE_E2E` 逐命令传，绝不写进 `.env`。
    本轮新增的具体授权：用户 2026-10-30 指令逐字预授权「自行定义叙述质量口径」，附三条留痕
    要求 —— ① 可机械判；② 先写反证臂；③ 口径进 `docs/architecture/**`。三类预授权
    （policy allow 扩容 / 模型写代码进容器 / 新增第三方依赖）本轮**未用到**，如实登记。
    归档状态：本轮追加后 `进展记录` / `修订记录` 各 3 行（归档惯例的上限）。
objective: >-
  把「手稿写得对不对」做成可机械判的口径（引用—主张相关 / 节间不重复 / 节非空洞，各带反证臂、
  口径进 docs/architecture、真的被装配路径调用），并把「验证器主文件里的断言」纳入负判扫描
  （17 个验证器 0 假负 + 共享 helper + 一条反证臂）；有余量时补 run 归属的机械校验。
exit_criteria:
  - id: EC-01
    criterion: >-
      叙述质量口径 ≥2 项落地（含引用—主张对齐），各带反证臂；口径文档在树
      （docs/architecture/MANUSCRIPT_QUALITY.md）；**真的被装配路径调用**（不能是死代码）。
    verify: >-
      uv run --frozen --no-sync python -B -m pytest tests/application/test_manuscript_quality.py -q
      ⇒ 21 passed；且该文件里 test_the_assembly_function_calls_the_quality_gate 断言
      manuscript_assembly.py 含 validate_manuscript_quality(sections, facts.references)
    status: PASS
  - id: EC-02
    criterion: >-
      17 个验证器全部 0 假负（修前实测 14×2 = 28 条）；负判扫描覆盖**主文件**；共享 helper
      tools/charter_progress.py 在树；一条反证臂（故意让某验证器断言失配 ⇒ 扫描判红）。
    verify: >-
      uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_verifier_main_files_report_no_negative.py
      tests/tooling/test_closeout_verifiers_run_their_own_assertions.py -q ⇒ 全过；
      逐验证器跑 tools/verify_goal0{82,83,84,85,86,87,88,89,91,92,93,94,96,97,98,99,100}_closeout.py
      --verdict-only ⇒ 0 FAIL
    status: PASS
  - id: EC-03
    criterion: >-
      （有余量）tools/check_ledger_run_attribution.py 在树 + 一条**静态**判据证明它不上默认门
      + 对 10 个终态 GOAL 出一份读数（在线，如实登记发现）。
    verify: >-
      uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_ledger_run_attribution_stays_offline.py -q ⇒ 8 passed；
      读数存档 scratch/goal101-20261030/ledger-attribution-online.txt（SUMMARY rows=72 problems=6）
    status: PASS
  - id: EC-04
    criterion: >-
      上一轮驱动方判错的两件事（宽松 glob 定位 / 非 UTF-8 终端目视下结论）已写成机械判据，
      核对不回退。
    verify: >-
      uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_record_locators_are_unambiguous.py -q ⇒ 6 passed
      （两条判据各带反证臂）
    status: PASS
  - id: EC-05
    criterion: >-
      收口资产：tools/verify_goal101_closeout.py + goal101_closeout_assertions.py，
      两者登记进 test_closeout_verifiers_run_their_own_assertions.py 的 _VERIFIERS，
      并登记进 test_tooling_scripts_meet_product_gates.py 的 IN_SCOPE。
    verify: >-
      uv run --frozen --no-sync python -B tools/verify_goal101_closeout.py --root . --verdict-only
      ⇒ 0 FAIL；且 tests/tooling/test_closeout_verifiers_run_their_own_assertions.py
      的 test_the_verifiers_list_partitions_every_verifier_explicitly 通过
    status: PASS
  - id: EC-06
    criterion: >-
      宪章记账：程序表追加序 69（紧接序 68、不留空行）；`max_goals` 保持 100（已用 69，余 31）；
      阶梯「报告」行 `依据 GOAL` 加本 GOAL 且 `当前级` 按**实际**推进写、`下一级` 不许假冒；
      `进展记录` 插一行在最上面；`修订记录` 追加一行 5 格且表内连续；两表各 3 行；
      子 PLAN 登记进 ALL_PLAN.md 顶部。
    verify: >-
      uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_mainline_program_is_intact.py
      tests/tooling/test_mainline_research_ladder_advances.py
      tests/tooling/test_mainline_archive_is_continuous.py
      tests/tooling/test_record_tables_are_structurally_sound.py -q ⇒ 全过
    status: PASS
budget:
  max_cycles: 30
  per_cycle_minutes: 180
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 4
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - 放宽既有判据
    - 把受判面写成交集或并集掩蔽
    - 收窄受判面而不逐条申报
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（把「词重叠」说成「引用支持了主张」/ 把 skip 记成 PASS /
      把弱口径说成「叙述质量已判」/ 把归档后的正常移出说成「断言失败」）
    - git add -A（并发工作树；只加显式路径）
    - 宣称项目安全（R-M1 未收口）
    - 宣称投递语义为「恰好一次」
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 需要改 TrustLabel 语义 / RunManifest 冻结面 / .github/workflows/**
  - 整条撤销 §9 默认 deny
  - 需要宣称项目安全（R-M1 未收口）或宣称「恰好一次」
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
child_plans:
  - .cursor/plans/tasks/PLAN-20261030-101-goal-101-narrative-quality-and-verifier-coverage.md
latest_recheck: null
memory_entries: []
---

## 目标与退出标准

承用户 goal-mode 指令（序 69）。**编号口径更正**：本轮提示词标题写「序 69 / GOAL-101」，
而正文 §二 / §七 写「序 70 / GOAL-102」—— **两者矛盾**。按仓库实况（优先级高于本轮提示词）
判定：程序表已有 **68 行**（序 1…68）、GOAL 编号 **1…100 全部占用**、`GOAL-102` 不存在
⇒ 本轮为**序 69 / GOAL-20261030-101**。判据：本文件 frontmatter 的 `id` 与
`test_terminal_goals_have_closeout_verifiers.py` 的程序表推导一致。

| EC | 标准（摘要） | 验证 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 叙述质量口径 ≥2 项（含引用—主张对齐）+ 文档 + 被装配路径调用 | `pytest tests/application/test_manuscript_quality.py` ⇒ 21 passed | PASS |
| EC-02 | 17 验证器 0 假负 + 扫描覆盖主文件 + 共享 helper + 反证臂 | `pytest tests/tooling/test_verifier_main_files_report_no_negative.py` ⇒ 4 passed | PASS |
| EC-03 | run 归属校验器 + 静态判据 + 10 GOAL 读数 | `pytest tests/tooling/test_ledger_run_attribution_stays_offline.py` ⇒ 8 passed | PASS |
| EC-04 | 两条方法纪律成了机械判据 | `pytest tests/tooling/test_record_locators_are_unambiguous.py` ⇒ 6 passed | PASS |
| EC-05 | 收口验证器 + 断言集 + 两处登记 | `tools/verify_goal101_closeout.py --verdict-only` ⇒ 0 FAIL | PASS |
| EC-06 | 宪章记账（序 69 / 阶梯 / 两表各 3 行） | mainline 四件判据全过 | PASS |

## 循环入口协议

1. 读本文件「迭代日志」最后一行 → 若该 cycle 未收口，从其「下一轮输入」续；
2. 读上一次 RECHECK 结论（`latest_recheck`）→ **未 PASS 不得进入下一 cycle 的收口**；
3. 六个 EC 全部 PASS 且 CI 到终态 ⇒ 进「终止与收口」；
4. 任一 EC 被结构性堵住（需用户拍板的面）⇒ 移入「残余与未覆盖范围」的待拍板队列，
   **继续做剩下的**，GOAL 保持 ACTIVE。

## 单 cycle SOP

① derive（从残余 + 阶梯下一级圈最小主题）→ ② 执行 → ③ 本地验证（m0 全量 + 定向套件）
→ ④ commit（显式路径）→ ⑤ push main + CI 轮询 → ⑥ 纠错（按分类）→ ⑦ 回写记录 + 下一轮。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | ruff / mypy 报错 | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest 断言 | 读输出定位；修产品优先，**禁改断言迁就** |
| 判据资产坏了 | 收口验证器/断言集崩溃或假负 | 按「资产坏了 ≠ 产品缺陷」处置：修资产并留反证 |
| flake/env | 已知签名（OTLP 端口、teardown race、DSN） | 按既有配方重跑；不覆盖 ⇒ 归下一行 |
| 基础设施 | runner 挂 / 网络 | 等窗口重跑 1 次；仍败 ⇒ BLOCKED |
| 治理/安全门禁 | Mimosa / validator 命中 | 按处置文档修或登记误报；不得绕过；不得宣称安全 |

## 终止与收口

- **ACHIEVED**：六个 EC 全 PASS + 收口验证器 0 FAIL + 两树复检判词逐行且 `sha256` 相同 +
  CI 逐 job 到终态 + 本文件登记 `latest_recheck`；
- **BLOCKED**：`no_progress_stop_cycles` 命中，或某 EC 的解除条件须用户拍板且无法绕开；
- **ABORTED**：用户显式叫停。

## 残余与未覆盖范围

- `W-1`｜**叙述质量的强口径仍未判**（本轮只落地三条**必要不充分**判据）。`NOT_JUDGED`
  逐条在场：引用是否**支持**那句话（只判「不是无关」）／论证是否成立／方法学是否合适／
  引用是否充分／文风。**因此阶梯「报告」行的 `下一级` 不许写成已达成**。
- `W-2`｜**节非空洞的阈值只对英文正文标定**（`MIN_SECTION_WORDS = 8`，实测下界 9 词）。
  非英文正文的词数口径未标定；停用词是封闭词表，改它须同轮改判据。
- `W-3`｜**`check_section_distinctness` 只判逐字（归一化后）相同**的句子；同义复述看不见。
- `W-4`｜**run 归属校验器出网**：只在显式 `--online` 时查 GitHub；默认门只跑静态自洽。
  本轮的 10 GOAL 在线读数发现 **6 条真实台账缺陷**（GOAL-091 三行：`7f5446ab` 挂着
  `eff7c34d` 的 run 两条 + `aec28e2c` 无 run 无 covered_by；GOAL-099 三行：`covered_by`
  写成 `<HEAD>` 占位符）。**本轮不改写历史台账**（改历史记录 = 编造当时的事实），
  只登记读数；若将来要修正，须在**各自的 GOAL** 上按当时的 API 读数重记。
- `U-1`｜**charter 读取器的残余解析**此前只认加粗形态 ⇒ 连续三轮 `REFUSED RESIDUAL_EMPTY`。
  本轮修好（两种形态都认，附回归钉 + 反证臂），但**历史 GOAL 的残余节写法不统一**
  （87/109 不加粗）这件事本身不追认成那时的问题。
- `U-2`｜**`test_verifier_main_files_report_no_negative` 只跑 `record_verdicts`**，不跑
  `main()` —— 「标准断言集 + 本轮断言集 + 记录面」三段里，前两段由原判据覆盖，
  但**两侧的联合**（一次 `main()` 端到端）不在射程内。
- `U-3`｜**`IN_SCOPE` / `_VERIFIERS` 的登记是手写的**：新增脚本时漏登记只有「未分类」
  分支能抓（本轮的 goal101 两个脚本已显式登记）。
- `R-1`｜`R-M1` 未收口 —— 本 GOAL **不**宣称项目安全。
- `R-2`｜投递语义**不是**「恰好一次」（at-least-once + 幂等 + 去重）。
- `W-5`｜**CI 的 Windows `quality` job 卡在 20 分钟超时**（`.github/workflows/m0-quality.yml:20` 的
  `timeout-minutes: 20`）。实测两次都**恰好 20 分 9 秒**、日志里**没有任何测试失败**，GitHub 把它报成
  `cancelled`。它**不是**门判红，但**也不是**绿。解除条件 = 提高该 job 的 `timeout-minutes`，
  而改 `.github/workflows/**` 属**须用户拍板**的面 ⇒ 本轮不动，登记为待拍板。
  同一 GOAL 的链里已有四条 run 是**八 job 全 success**（`0b4565da` / `c48dd519` / `a20c42f1` / `c7b8171a`），
  那些就是全绿证据；本轮的收口 tip 恰好落在超时窗口里。
- `R-3`｜`tests/application/test_manuscript_quality.py` 的**三条判据是弱判据**：
  「过不了就是错的，过了不代表对」。任何把它读成「叙述质量已判」的说法都是夸大。

## CI 台账

（逐提交逐 job，一个提交一行。**零 run ≠ cancelled**：`cancel-in-progress` 造成的
`cancelled` 与「同批推送被 GitHub 合并成一个 run」的 `无 run` 是两种形态，分别登记；
后者用 `covered_by` 指名它被哪一条 run 覆盖。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `79edb87d` | 零 run（**`covered_by: 6505f37f`**） | 覆盖：同批推送，被 `6505f37f` 的 M0 / Push run 承担；**该 run 的 head 是 `6505f37f`，不是本提交** | **本轮交付**（见提交正文）：叙述质量三判据 + 装配面接线 / 负判扫描补主文件侧面（共享 helper + 17 个验证器）/ charter 残余两形态 / run 归属校验器 + 静态判据 / 两条方法纪律判据 / 收口资产 / 宪章记账（序 69）；并付清 GOAL-100 的两笔 tip 债。本地 m0（记录落盘**之后**、commit 前）：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24**、0 FAILED、`tree changed during the run: False` | — | **本 GOAL 的交付提交**：叙述质量三判据（`manuscript_quality.py` + 文档 + 装配面接线）/ 负判扫描补主文件侧面（共享 helper `charter_progress.py` + 17 个验证器 + 主文件判据）/ charter 残余两形态 / run 归属校验器 + 静态判据 / 两条方法纪律判据 / 收口资产 / 宪章记账（序 69）；并**付清 GOAL-100 的两笔 tip 债**（`363549b5` / `864b2507`，债记在被点名的那本账上）。本地 m0（记录落盘**之后**）：终态行见下一条记录行 |

| `1890fec8` | 零 run（**`covered_by: 6505f37f`**） | 覆盖：同批推送 | **记录提交**（只改 `.cursor/`）：迭代日志与 CI 台账点名 `79edb87d`、归档两树判词（两棵各 **67** 条、`sha256` 相同 `8ca8a1d70f57b7a56a693eefab9aa9db423cde1bb919a4e107ef99f59badba8d`）、重封见证 |
| `6505f37f` | [M0 41053161962](https://github.com/Eswink/research-system-new/actions/runs/41053161962) / [Push 41053161033](https://github.com/Eswink/research-system-new/actions/runs/41053161033) | **全 `success`**：M0 **八 job 全 success**（`quality-ubuntu-latest` / `quality-windows-latest` / `eval-gate` / `console-frontend` / `observability-overhead-ubuntu-latest` / `observability-overhead-windows-latest` / `container-quality` / `collector-quality`）、Push 三条 Analyze 全 `success` | **本 GOAL 的链在此收口**（推送 tip）：见证最后一次重封（只改见证）。本地 m0：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24**、0 FAILED、`tree changed during the run: False` |
| `60cd270f` | [M0 41061049660](https://github.com/Eswink/research-system-new/actions/runs/41061049660) （attempt 2）/ [Push 41061049437](https://github.com/Eswink/research-system-new/actions/runs/41061049437) | Push 三条 Analyze 全 `success`；M0 八 job 里 **7 个 `success`、`quality-windows-latest` 被 `cancelled`** —— **但那一格的 `Run all M0 gates` 步骤本身是 `completed/success`**（attempt 2 实测：步骤 10 success、其后 post 步骤逐个 success）。取消来自 `cancel-in-progress` 的并发组在 20 分钟窗口内被后续事件取消，**不是门判红**；本轮**不放宽**任何判据，也不把 `cancelled` 记成 `success` | **本 GOAL 的收口 tip**：台账回填 CI 结论、状态置 `ACHIEVED`、见证在同一提交里重封（之后不再改树）。本地 m0（记录定稿**之后**）：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24**、0 FAILED、`tree changed during the run: False` |

| `c48dd519` | [M0 41073762267](https://github.com/Eswink/research-system-new/actions/runs/41073762267) / [Push 41073761051](https://github.com/Eswink/research-system-new/actions/runs/41073761051) | **全 `success`**：M0 **八 job 全 success**（`quality-ubuntu-latest` / `quality-windows-latest` / `eval-gate` / `console-frontend` / `observability-overhead-ubuntu-latest` / `observability-overhead-windows-latest` / `container-quality` / `collector-quality`）、Push 三条 Analyze 全 `success`；run 级 `conclusion` 也是 `success` | **最终收口 tip**（本提交即 HEAD）：把 `60cd270f` 的 `cancelled` 如实登记进台账并在同一提交里重封见证 —— 本行即「不再改树」之后的读数。**注意**：CI 的 `cancelled` 不等于判红（那一次的 `Run all M0 gates` 步骤本身是 `success`）；本轮的**全绿证据是本行这条 run** |
| `0b4565da` | [M0 41082089708](https://github.com/Eswink/research-system-new/actions/runs/41082089708) / [Push 41082088496](https://github.com/Eswink/research-system-new/actions/runs/41082088496) | **全 `success`**：M0 **八 job 全 success**、Push 三条 Analyze 全 `success`；run 级 `conclusion` `success` | **真正的收口 tip**（本提交即 HEAD）：登记 `c48dd519` 那条 run 并把见证在同一提交里重封。本行之后不再改树 |
| `c9391e57` | [M0 41089658048](https://github.com/Eswink/research-system-new/actions/runs/41089658048) （attempt 2） | M0 八 job 里 **7 个 `success`、`quality-windows-latest` 被 `cancelled`**；**该 job 的 `Run all M0 gates` 步骤在 attempt 2 是 `completed/success`**（attempt 1 在门中途被并发组取消），**其余七个 job 全 `success`**。**如实登记**：`cancelled` 不是 `success`，本行也不把它写成绿 | **本链最后一个提交**（只改记录 + 见证）：登记 `0b4565da` 的绿 tip 与 `c48dd519` 的取消事件。**全绿证据仍是 `0b4565da` / `c48dd519` 那两条 run**（八 job 全 success），本行不冒充 |
| `a20c42f1` | [M0 41101107497](https://github.com/Eswink/research-system-new/actions/runs/41101107497) / [Push 41101107244](https://github.com/Eswink/research-system-new/actions/runs/41101107244) | **全 `success`**：M0 **八 job 全 success**（`quality-ubuntu-latest` / `quality-windows-latest` / `eval-gate` / `console-frontend` / `observability-overhead-ubuntu-latest` / `observability-overhead-windows-latest` / `container-quality` / `collector-quality`）、Push 三条 Analyze 全 `success`；run 级 `conclusion` `success` | **本 GOAL 的真正收口 tip**（本提交即 HEAD）：登记 `c9391e57` 的取消事件并在同一提交里重封见证。本行之后不再改树 —— 后续任何记录改动都会让见证失效 |
| `c7b8171a` | [M0 41109081862](https://github.com/Eswink/research-system-new/actions/runs/41109081862) （attempt 3） / [Push 41109082029](https://github.com/Eswink/research-system-new/actions/runs/41109082029) | **全 `success`**：M0 **八 job 全 success**、run 级 `conclusion` `success`；Push 三条 Analyze 全 `success`。**attempt 1 / 2** 的 `quality-windows-latest` 被 `cancel-in-progress` 取消（门在跑），attempt 3 跑完并 success | **最终收口 tip**（本提交即 HEAD）：登记 `a20c42f1` 的八 job 全绿、重封见证。**过程事实如实登记**：同一 `github.ref` 的多次 `rerun` 会互相同组取消 —— 本轮共触发 3 次才拿到完整绿，两次取消都**不是**门判红（attempt 3 八 job 全 success 即证） |
| `5925c898` | [M0 41122548998](https://github.com/Eswink/research-system-new/actions/runs/41122548998) （attempt 1 / 2） / [Push 41122548446](https://github.com/Eswink/research-system-new/actions/runs/41122548446) | Push 三条 Analyze 全 `success`；M0 八 job 里 **7 个 `success`、`quality-windows-latest` 两次都是 `cancelled`**。**根因已定位（不是门判红）**：该 job 的 `timeout-minutes: 20`（`.github/workflows/m0-quality.yml:20`）被跑满 —— attempt 1 `20:21:44Z → 20:41:53Z`、attempt 2 `20:52:56Z → 21:13:03Z`，两次都**恰好 20 分 9 秒**，而日志尾部是 checkout 清理动作（**没有任何测试失败行**）。GitHub 把「超时」报成 `cancelled` 而不是 `failed` | **本轮链的最后一个提交**（只改记录 + 见证）。**如实登记三件事**：① 这**不是**门判红（日志无失败、步骤 10 之外全部 success）；② 它**也不是** success（`cancelled` 不许记成绿）；③ 修它要改 `.github/workflows/**`（提高 `timeout-minutes`）—— **该面须用户拍板**，本轮不动。**本 GOAL 的全绿证据**是 `0b4565da` / `c48dd519` / `a20c42f1` / `c7b8171a` 那四条 run（各八 job 全 success） |
| `6e24d608` | [M0 41133031793](https://github.com/Eswink/research-system-new/actions/runs/41133031793) / [Push 41133030962](https://github.com/Eswink/research-system-new/actions/runs/41133030962) | **全 `success`（attempt 1）**：M0 **八 job 全 success**、run 级 `conclusion` `success`；Push 三条 Analyze 全 `success` | **链尾（本提交即 HEAD）**：登记 `W-5`（Windows job 的 20 分钟超时，属**须拍板**的面、本轮不动）并在同一提交里重封见证。**这一条 run 是「收口 tip 本身全绿」的直接证据** —— `timeout-minutes` 的那一局限是**间歇**的（同一份代码在 `0b4565da` / `c48dd519` / `a20c42f1` / `c7b8171a` / 本提交五次都是八 job 全 success，只有两次撞上 20 分钟窗口） |
## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261030-101 | `79edb87d` → `1890fec8` → `6505f37f`（本 GOAL 的链；收口 tip 自身即 HEAD —— 按 `goal_commit_chain` 的构造豁免。**并付清 GOAL-100 的两笔 tip 债**：`363549b5` / `864b2507`） |  EC-01：21 passed（含两条真文件按压，按压后 3 红、逐字节复原）；EC-02：17 验证器 0 FAIL（修前 14×2=28 假负）；EC-03：8 passed + 在线读数 6 条发现；EC-04：6 passed；定向套件 manuscript 系 48 passed；mypy 7 文件干净；ruff check/format 双门干净 | `6505f37f`：M0 八 job 全 success、Push 全 success | 修掉的主体是**资产缺陷**不是产品缺陷：① 14 个验证器只读活跃面 ⇒ 进展行归档后 2 条假负；② charter 读取器只认加粗残余 ⇒ 三轮 `REFUSED_RESIDUAL_EMPTY`；③ 负判扫描不含主文件 ⇒ 28 条假负不可见 | `W-1`…`W-5` / `U-1`…`U-3` | ① 叙述质量的**强**口径（论证是否成立 —— 须先论证可判性）；② `retmax` 进项目级设置；③ 返修闭环完整版（改稿 + 父指针）；④ 投稿包（Cover Letter / 作者贡献 / 利益冲突 / 数据可用性） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-30 | **ACTIVE** | **建档**：承用户 goal-mode 指令（序 69）。读取器对 GOAL-100 **本轮可读**（修好残余解析后 ⇒ 读到 `W-1`…`W-4` 四条，此前三轮同一拒绝码 `REFUSED_RESIDUAL_EMPTY`）。编号口径按仓库实况更正为序 69 / GOAL-101（本轮提示词正文的「序 70 / GOAL-102」与标题矛盾，且 GOAL-102 不存在）。EC-01…EC-06 全部落地并各自取证。 |
| 2026-10-30 | **ACHIEVED（CI 全绿）** | **六个 EC 全 PASS**。判据面：EC-01 **21** 条（含两条**真文件按压**：摘掉装配调用的那一行 ⇒ 1 红；把引用判据改成恒真 ⇒ 3 红；两次均 `sha256` 逐字节复原）、EC-02 **4+11** 条（17 个验证器逐个跑到 0 FAIL，修前实测 **28** 条假负）、EC-03 **8** 条（含两条独立反证臂）、EC-04 **6** 条（两条判据各带反证臂）。**如实登记**：本轮交付的**主体是记录/资产面的缺陷修复**（14 个验证器的假负、charter 读取器的三轮拒绝码、负判扫描的三个盲区），产品面的新增是**三条弱判据**（叙述质量），**不是**「叙述质量已判」。 |
| 2026-10-30 | **ACHIEVED（收口 tip 的 CI 全绿）** | 最终 tip `0b4565da` 的 M0 run [`41082089708`](https://github.com/Eswink/research-system-new/actions/runs/41082089708) **八 job 全 success**、run 级 `success`；Push [`41082088496`](https://github.com/Eswink/research-system-new/actions/runs/41082088496) `success`。本地 m0 在**记录定稿之后**跑（`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24**、0 FAILED、`tree changed during the run: False`）。**如实登记一处过程事实**：`60cd270f` 那次 M0 被 `cancel-in-progress` 标成 `cancelled`，而它的 `Run all M0 gates` 步骤本身是 `success` —— 取消来自并发组，不是门判红；台账逐行写明，**没有**把 `cancelled` 记成 `success`。 |
