---
id: GOAL-20261031-102
slug: submission-package-and-revision-closure
title: 投稿包 + 改稿闭环 —— 把「能投出去的稿」变成「投出去的包」
status: ACHIEVED
created_at: 2026-10-31
updated_at: 2026-11-01
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    沿用用户 2026-10-29 的全权限预授权（GOAL-20261029-100 的 authorization.ref；policy allow
    扩容 / 模型写代码进容器 / 新增第三方依赖 / 叙述质量口径，四类已预授权、各带留痕义务）；
    push-to-main-for-CI：只推 main、不 force、不重写历史、不推旁支；
    RESEARCHOS_AGENT_RUNTIME / RESEARCHOS_LIVE_E2E 逐命令传，绝不写进 .env。
objective: >-
  让「同一篇论文的下一版」在结构上存在（`Artifact.supersedes` 父指针 + 改稿正文 + 应答引用
  真实制品），并把投稿包五件制品（cover letter / CRediT 分工 / 冲突声明 / 数据可得性 /
  补充材料索引）经产品装配路径落到 canonical，外加期刊选择的闭集声明面。
exit_criteria:
  - id: EC-01
    criterion: >-
      Artifact `supersedes` 字段落地：域（缺省 None + 自指拒绝 + `validate_supersedes`
      链校验：目标缺席 / 跨 run / 成环各自点名）+ SQLite（SCHEMA_SQL 列 + insert/update/
      读回）+ Postgres（`030_artifact_supersedes.sql` + insert/update/读回）；
      digest 不受父指针影响。
    verify: >-
      tests/domain/test_artifacts.py::TestSupersedes（链通过 / 缺席 / 跨 run / 二环 / 三环）
      + tests/adapters/sqlite/test_artifact_store.py::TestSupersedesRoundTrip
      + tests/postgres/test_artifact_supersedes_pg.py（无 DSN 按标记跳过）。
    status: PASS
  - id: EC-02
    criterion: >-
      改稿闭环：应答会话回复携带第二块 `revised_manuscript`，报告相装配 `manuscript_v2.md`
      （supersedes → v1，链校验通过才落库）；每条 `action_taken` 必须引用
      `manuscript_v2.md` 且引用的名字必须在本 run 制品名集合里；三条反证各判红
      （无指针的 v2 / 编造引用 / 空谈不引用）。
    verify: >-
      tests/application/test_revision_closure.py（8 条：闭环成立 / 读面拒无指针 v2 /
      读面拒成环 / 编造引用 FAILED / 空谈 FAILED / 旧形状零回归 / 改稿不降硬规则门槛 /
      引用判据直臂）+ tests/e2e/test_goal102_product_path.py（产品入口 v2 + supersedes
      + 正文真的改了）。
    status: PASS
  - id: EC-03
    criterion: >-
      投稿包：协议新增 `submission` 会话相（十一相，申报过的扩展）+ 合约
      `submission_package`；报告相装配五件制品（cover_letter.md /
      author_contributions.md / conflicts_of_interest.md / data_availability.md /
      supplementary.md）；CRediT 角色与本 run 分派对齐（27 角色闭集映射）；digest 与
      本 run 制品对齐；COI 是结构化字段；三条反证各判红。
    verify: >-
      tests/application/test_submission_package.py（11 条，含 invented CRediT / 编造
      digest / 非布尔 has_conflict 三条反证）+ tests/e2e/test_goal102_product_path.py
      （五件经读面可见 / 分派对齐 / digest 用读面字节重算 / COI 按字段读）+
      tests/contracts/test_direction_to_manuscript_protocol.py（十一相 + 七产物 + 两条新边）。
    status: PASS
  - id: EC-04
    criterion: >-
      期刊选择面：`examples/config/journals.yaml` 闭集（name + ISSN + scope keywords，
      无任何评分/排名字段）；`editorial_decision` 决定块可带 `target_journal` +
      `selection_rationale`（同进同出）；选中名 ∈ 闭集；依据引用该刊 scope 关键词 ≥ 1；
      闭集与合约 purpose 镜像；两条反证判红（越闭集 / 空依据）。
    verify: >-
      tests/application/test_journal_selection.py（9 条，四向反证 + 镜像 + 评分字段禁入）
      + tests/e2e/test_goal102_product_path.py（产品路径的选择经闭集校验）。
    status: PASS
  - id: EC-05
    criterion: >-
      收口资产：`tools/verify_goal102_closeout.py` + `tools/goal102_closeout_assertions.py`
      （公共面一行不重写），登记进 `_VERIFIERS` 与 `IN_SCOPE`。
    verify: >-
      tests/tooling/test_closeout_verifiers_run_their_own_assertions.py（清单登记）
      + tests/tooling/test_tooling_scripts_meet_product_gates.py（四道门射程）
      + 本验证器 --root . --verdict-only 全绿。
    status: PASS
  - id: EC-06
    criterion: >-
      宪章记账：程序表序 70（紧接序 69、不留空行）；阶梯「复检」行收录本 GOAL 且
      `当前级` 加「改稿闭环（artifact 父指针）」（`下一级` 不许声称判词内容驱动已判）；
      进展记录插最上面；修订记录追加一行（5 格、表内连续）；两表各 3 行；子 PLAN
      登记进 ALL_PLAN.md。
    verify: >-
      tests/tooling/test_mainline_research_ladder_advances.py（最新轮被阶梯收录）
      + tools/verify_goal102_closeout.py 的记录面判词（阶梯 / 进展 / 修订 / 子计划在位）。
    status: PASS
budget:
  max_cycles: 30
  per_cycle_minutes: 180
  no_progress_stop_cycles: 2
fix_policy:
  allowed:
    - 按判据点名修产品缺陷（本 GOAL 实测修掉 FakeArtifactStore.mark 丢 supersedes 一处）
    - 新增判据文件与两向按压（每条新判据都有反证臂）
    - 扩既有判据的受判面（十相 → 十一相等），逐条申报为什么不是放宽
  forbidden:
    - 改 validator/门禁/快照/断言使其通过
    - 放宽既有判据（相集判据只增不改形状；逐条申报）
    - 把受判面写成交集或并集掩蔽
    - 收窄受判面而不逐条申报
    - git push --force / 重写历史 / 推非 main
    - 伪造或夸大验证证据（尤其：把「写了应答信」说成「手稿真的改了」、把 skip 记成
      PASS、补造 CRediT 角色/digest）
    - git add -A
    - 宣称项目安全（R-M1 未收口）
    - 宣称投递语义为「恰好一次」（at-least-once + 幂等 + 去重）
escalation_triggers:
  - 改 TrustLabel 语义 / 动 RunManifest 冻结面 / 改 .github/workflows/**（须用户拍板，本轮未动）
  - 整条撤销 §9 默认 deny（本轮未动；§9 姿态只放开点名项）
  - migration 撞冻结面（预案：EC-01/02 的 Postgres 侧移到序 71 —— 未触发，030 已落）
child_plans:
  - .cursor/plans/tasks/PLAN-20261031-102-submission-package-and-revision-closure.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261031-102-submission-package-and-revision-closure.md
memory_entries: []
---

# GOAL-20261031-102 —— 投稿包 + 改稿闭环

## 目标与退出标准

承用户 goal-mode 指令（序 70）。序 69（GOAL-101）收口后，手稿已经「能投出去」（八键
IMRaD + 引用闭合 + 编辑决定 + 逐条应答），但两件事在结构上**不存在**（建档实测，不
重新推导）：① **「同一篇论文的下一版」**——`Artifact` 没有 `parent` / `version` /
`supersedes` 字段（全文件 grep = 0 命中）⇒ v2 无法指回 v1，`AuthorResponse.action_taken`
是自报字符串，没有任何东西验证手稿真的变了；② **「投出去的包」**——`cover letter` /
`author contribution` / `CRediT` / `conflict of interest` / `data availability` /
`supplementary` / `target journal` / `journal selection` 在产品三根全部 0 命中。
三个靶子：改稿闭环（EC-01/02）、投稿包五件制品（EC-03）、期刊选择闭集（EC-04）。

方法与边界（继承的三条纪律 + 本轮三条）：判断文件结构用 Python
`read_bytes().decode('utf-8')`、定位用精确路径、「在不在」用 `grep -c` 拿计数；
序列化两侧同步（SQLite `SCHEMA_SQL` 单一来源 + Postgres 追加式 migration `030`）；
会话相/确定性相分工不动摇（模型写正文与信，汇编器写数字/编号/清单/登记）；期刊闭集
是**声明面**不是评分（无影响因子、无排名，判据钉住）。

| EC | 标准（摘要） | 验证 | 状态 |
| --- | --- | --- | --- |
| EC-01 | `Artifact.supersedes` 落地（域 + 两侧序列化 + 链校验三反证；digest 不变） | `tests/domain/test_artifacts.py` 19 passed + sqlite 13 passed + `tests/postgres/test_artifact_supersedes_pg.py` 在树 | PASS |
| EC-02 | 改稿闭环：v2（supersedes → v1）+ `action_taken` 引用真实制品 + 三反证 | `tests/application/test_revision_closure.py` 8 passed + 产品入口判据 | PASS |
| EC-03 | 投稿包五件制品 + CRediT/digest/COI 三判据 + 三反证 | `tests/application/test_submission_package.py` 11 passed + 产品入口 4 条 + 协议判据 39 passed | PASS |
| EC-04 | 期刊闭集 + 两字段 + 三判据 + 镜像 | `tests/application/test_journal_selection.py` 9 passed | PASS |
| EC-05 | 收口验证器 + 断言集 + 两处登记 | `tools/verify_goal102_closeout.py --verdict-only` ⇒ 0 FAIL | PASS |
| EC-06 | 宪章记账（序 70 / 阶梯两行 / 两表各 3 行 / ALL_PLAN） | mainline 判据 + 记录面判据全过 | PASS |

## 循环入口协议

1. 读本文件「迭代日志」最后一行 → 若该 cycle 未收口，从其「下一轮输入」续；
2. 读上一次 RECHECK 结论（`latest_recheck`）→ **未 PASS 不得进入下一 cycle 的收口**；
3. 六个 EC 全部 PASS 且 CI 到终态 ⇒ 进「终止与收口」；
4. 任一 EC 被结构性堵住（需用户拍板的面）⇒ 移入「残余与未覆盖范围」的待拍板队列，
   **继续做剩下的**，GOAL 保持 ACTIVE。

## 单 cycle SOP

① derive（从残余 + 阶梯下一级圈最小主题）→ ② 执行 → ③ 本地验证（m0 全量 + 定向套件）
→ ④ commit（显式路径）→ ⑤ push main + CI 轮询 → ⑥ 纠错（按分类）→ ⑦ 回写记录 + 下一轮。

## CI 台账

（逐提交逐 job。**零 run ≠ cancelled**；`covered_by` 只写真实覆盖者哈希。首行先记本地
见证证据；CI run 的链接与结论由其后的记录提交回填 —— 回填提交用中性主题（只改
`.cursor/`），不进本 GOAL 的链。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `9a313685` | 本地 m0 见证（`evidence/M0-WITNESS.json`；首次运行为诚实红：product-lint/format/typecheck/tests/framework-validate 各 1，按「CI 失败分类与纠错」逐类修复后复跑） | 修复后复跑全绿（终态行见迭代日志） | 交付提交（38 文件）：supersedes 域+两侧序列化 / 改稿闭环 / 投稿包五件制品 / 期刊闭集 / 收口资产 / 宪章记账；**零 run（`covered_by: 910dd745`）** —— 同批推送，被 tip 的 run 承担 |
| `910dd745` | [M0 41238101258](https://github.com/Eswink/research-system-new/actions/runs/41238101258) / [Push 41238100825](https://github.com/Eswink/research-system-new/actions/runs/41238100825) | **M0 `cancelled`（7/8 job success，`quality-windows-latest` 撞 20 分钟超时窗口 —— GOAL-101 `W-5` 的同一形态，待拍板面）**；**Push 全 success** | **交付 tip**（含见证；两树复检 83 判词逐行相同、sha256 `50b174dd…`，归档 `scratch/goal102-20261101/`）。超时不是门判红（日志无测试失败），但也**不是绿**——如实登记，不冒充全绿 |

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

处置上一轮（GOAL-101）的残余：**逐条处置，不删不改写**：

- `W-1`｜**叙述质量的强口径仍未判** —— 承接为长期路线 3（本轮不做：靶子是投稿包与
  改稿闭环；强口径需先论证可判性）。`NOT_JUDGED` 逐条仍不在场。
- `W-2`｜**节非空洞阈值只对英文正文标定** —— 承接（本轮不改 `MIN_SECTION_WORDS`；
  改停用词须同轮改判据）。
- `W-3`｜**distinctness 只判逐字相同** —— 承接（同义复述看不见，仍是真的）。
- `W-4`｜**run 归属校验器出网面** —— 承接；历史台账缺陷（GOAL-091/099）仍在各自
  GOAL 上等按当时读数重记，本轮不改写历史。
- `W-5`｜**CI Windows `quality` job 的 20 分钟超时** —— 待拍板（改
  `.github/workflows/**` 须用户拍板）；本轮 CI 若再现超时窗口，按既有口径登记。
- `W-6`｜**历史台账不改写** —— 承接；本轮只**补记**了上一轮 tip 链的两行
  （`3cd63a4f` / `66177f39`，按 2026-11-01 的 API 读数），不动任何既有行。
- `W-7`｜**（本轮新发现并已修）charter 读取器对 GOAL-101 拒读**：
  `next_round_charter.py` 以 `REFUSED RESIDUAL_GAP` 点名 W 编号顺序为
  `[1,2,3,4,6,5]` —— GOAL-101 的残余节把 W-6 写在 W-5 之前（连续性纪律 violation，
  疑似 2026-10-31 的编辑顺序事故）。**处置**：对 GOAL-101 做纯**重排**（W-5 块与
  W-6 块互换、零内容改动），读取器随即可读。本轮残余节以此为戒：编号连续且按序。

- `U-1`｜**期刊选择的「语义匹配好坏」不可判**：本轮只判「在闭集内 + 依据引用了
  scope 关键词」；「这个期刊真的合适」是人评，声明面不冒充评价面。
- `U-2`｜**Postgres 侧 supersedes 判据在无 DSN 环境跳过**：m0 的既定形态；migration
  文件存在性/顺序有判据，行的往返在有 DSN 时才真跑。
- `U-3`｜**data_availability 清单的时点边界**：清单是「投稿包装配时点」本 run 已
  产出的制品（应答信与五件投稿制品自身不在自己的清单里 —— 鸡生蛋边界，如实登记）。

- `R-1`｜`R-M1` 未收口 —— 本 GOAL **不**宣称项目安全。
- `R-2`｜投递语义**不是**「恰好一次」。

## 结论

**ACHIEVED**。六个 EC 全部达成（EC-01…EC-06 各自 PASS，证据见 RECHECK 记录）。改稿闭环成为结构事实：`manuscript_v2.md` 带 `supersedes` 指回 v1，每条 `action_taken` 的引用可判；投稿包五件制品经产品装配路径落到 canonical 并可从读面取回；期刊闭集是声明面（无评分字段）。**不**宣称：叙述质量强口径已判（W-1 承接）、项目安全（R-M1）、恰好一次（R-2）。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261031-102 | `9a313685` → `910dd745` | 单元 154 passed（域 19 / sqlite 13 / 改稿 8 / 投稿 11 / 期刊 9 / 协议 39 / 手稿装配与编辑等 32）；产品入口 e2e 15 passed（真容器实验）；两树复检 **PASS**（83 判词逐行相同 + sha256 相同） | [M0 41238101258](https://github.com/Eswink/research-system-new/actions/runs/41238101258) / [Push 41238100825](https://github.com/Eswink/research-system-new/actions/runs/41238100825)：Push success；M0 7/8 success + `quality-windows-latest` cancelled（W-5 超时窗口，待拍板） | `FakeArtifactStore.mark` 重建白名单丢 `supersedes`（判据先红后绿）；GOAL-101 残余节 W 编号乱序（charter 读取器拒读，纯重排修复）；上一轮 tip 链两行台账欠账（`3cd63a4f` / `66177f39`）按 API 读数补记 | W-1…W-6 逐条处置（见残余节）；期刊选择的语义匹配不可判（U-1） | 判词内容驱动改稿（复检域下一级）；叙述质量强口径（需先论证可判性）；Postgres 行往返在无 DSN 环境仍只跑文件面判据 |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-31 | **ACTIVE** | **建档**：承用户 goal-mode 指令（序 70）。charter 读取器先以 `REFUSED RESIDUAL_GAP` 拒读 GOAL-101（W-6 在 W-5 前）；纯重排后可读，读到 W-1…W-6 六条残余。 |
| 2026-11-01 | **ACHIEVED** | **六个 EC 全 PASS**。收口证据链：本地 m0 第四次全绿（前三次的诚实红逐类修复：治理必需章节 / 规模门 450 行 / mypy 再出口 / 链台账）；两树复检 `TWO-TREE PASS`（83 判词逐行相同，sha256 `50b174dd…`，归档 scratch）；CI Push success、M0 7/8（`quality-windows-latest` 撞 W-5 超时窗口 ⇒ cancelled，如实登记不冒充全绿）。产品面：`supersedes` 域+两侧序列化+链校验（缺席/跨 run/成环各点名）；改稿闭环（v2 + 引用判据 + 三反证）；投稿包五件制品（CRediT 27 角色闭集映射 / COI 结构化字段 / digest 读面字节可重算）；期刊闭集（无评分字段 + 镜像判漂移）。实测修掉 `FakeArtifactStore.mark` 丢字段一处。记录面：验证器 + 断言集登记进 `_VERIFIERS` 与 `IN_SCOPE`；宪章程序表序 70 + 阶梯两行 + 两表各 3 行。 |
