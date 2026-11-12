---
id: GOAL-20261111-111
slug: panel-verdicts-that-can-be-refuted
title: 面板判词从「某个模型认为」升级为可核验的结构断言
status: ACHIEVED
created_at: 2026-11-12
updated_at: 2026-11-12
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    用户 2026-11-11 登记序 77…80 五轮程序（与序 76 同一次授权），本轮为序 79：
    「面板判词从『某个模型认为』升级为**可核验的结构断言**」。沿用户 2026-10-29
    全权限预授权；push-to-main-for-CI：只推 main、不 force、不重写历史、不推旁支。
objective: >-
  §7 用 P1–P4 把 `NOT_JUDGED` 五项逐项判过：第 1/2/3 项（引用是否**支持**那句话 /
  论证是否成立 / 方法学是否合适）只能人评；GOAL-107 交付了外部评审面板（advisory、
  `PANEL_UNAVAILABLE` 独立一类）。**但面板判词目前无法被反驳**——模型的 `rationale`
  是自由文本，读者无法核对它指的那句话在不在正文里。本轮把它升级为**可核验**：
  `REFUTED` 的 `rationale` 必须**指向正文里真实存在的句子**（`S<n>` 编号或可被子串
  核验的原文片段）⇒ 判词本身可反驳。**射程仍不充分**：这是「某个模型认为 X 句有问题，
  且那句话在正文里确实存在」——**不是**「论证成立」。
exit_criteria:
  - id: EC-01
    criterion: >-
      **判词引用面**：新建 `packages/application/deliverable/panel_grounding.py`：
      把正文切成**编号句子**（`S1…Sn`，确定性、可复算）并核验一条 `rationale` 是否
      **落在那份正文字节上**（`S<n>` 编号命中 / 引用的原文片段是正文的真实子串）。
      两种「不成立」分得开：**指向不存在的句子** ≠ **rationale 为空**。
    verify: >-
      `tests/application/deliverable/test_panel_grounding.py` ⇒ 正例（`S3` 命中 +
      原文片段是子串）+ 反证（`S99` 不存在 ⇒ 判负并点名）+ 反证（空 rationale ⇒ 判负，
      且与「不存在」**点名不同**）。
    status: PASS
  - id: EC-02
    criterion: >-
      **`REFUTED` 必须被指向**：`manuscript_panel` 的判词在写出前经那道核验——
      `REFUTED` 而 grounding 不成立 ⇒ 该条判词**降级**为 `AMBIGUOUS` 并在判词里
      **点名缺什么**（不静默通过、不静默丢弃）。`SUPPORTED` 不受此约束（它不指句子）。
    verify: >-
      `tests/application/deliverable/test_panel_grounding.py` ⇒ 三条：
      `REFUTED` + 有效引用 ⇒ 保持 `REFUTED`；`REFUTED` + 无效引用 ⇒ `AMBIGUOUS` 并点名；
      `SUPPORTED` + 空 rationale ⇒ **仍** `SUPPORTED`（约束只落在 `REFUTED`）。
    status: PASS
  - id: EC-03
    criterion: >-
      **四条判据（缺一即判空）**：① 正例 rationale 指向真实句子 ⇒ 通过；
      ② **反证** rationale 指向不存在句子 ⇒ 判红；③ **反证** rationale 空 ⇒ 判红；
      ④ 面板仍 **advisory**（不产生 `Decision`、不进验收门）。
    verify: >-
      `tests/application/deliverable/test_panel_grounding.py`（①②③）+ 既有
      `tests/application/test_manuscript_panel.py` 的 advisory 断言（④）仍绿。
    status: PASS
  - id: EC-04
    criterion: >-
      **`NOT_JUDGED` 逐字不动**：五项一个字节都不改，`len(NOT_JUDGED) == 5` 仍绿；
      §7（`docs/architecture/MANUSCRIPT_QUALITY.md`）**补一句**说明面板判词现在可核验、
      但射程仍不充分。判定表**一字不动**。
    verify: >-
      `tests/application/test_manuscript_quality.py` 的 `NOT_JUDGED` 相关判据全绿
      （含 `len == 5`）+ 收口断言集逐字比对五项原文。
    status: PASS
  - id: EC-05
    criterion: >-
      **收口资产与宪章记账**：`tools/verify_goal111_closeout.py` +
      `tools/goal111_closeout_assertions.py`，登记进 `_VERIFIERS` 与 `IN_SCOPE`；
      宪章程序表 / 阶梯 / 进展 / 修订按实际改；GOAL-109 / GOAL-110 台账的 run id 回填顺路完成。
    verify: >-
      收口验证器全 PASS；两处登记判据绿；`tools/credential_audit.py` 四面 `offenders=0`。
    status: PASS
budget:
  max_cycles: 40
  per_cycle_minutes: 180
  no_progress_stop_cycles: 2
fix_policy:
  allowed:
    - 按判据点名修产品缺陷（判据先红后绿，逐条留证）
    - 新增判据文件与两向按压
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 把真实 key 写进任何被跟踪文件（只进 gitignored `.env`）
    - 改 TrustLabel 语义 / 动 RunManifest / 改 `.github/workflows/**`
    - 改 `NOT_JUDGED` 五项任何一个字（射程声明不是本轮的面）
    - 让面板产生 `Decision` 或参与验收门（advisory 边界）
    - 把「判词可核验」写成「叙述质量已判」
  same_signature_retries: 3
  cycle_fix_retries: 6
escalation_triggers:
  - 改 TrustLabel 语义 / 动 RunManifest 冻结面 / 改 .github/workflows/**（须用户拍板）
  - 需要提高「引用充分性」阈值才能继续 ⇒ 停下登记待拍板（阈值仍全 `None`）
  - 同一失败签名超过 fix_policy 上限
child_plans:
  - .cursor/plans/tasks/PLAN-20261112-111-panel-grounding.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261112-111-panel-grounding.md
memory_entries: []
---

# GOAL-20261111-111 —— 面板判词从「某个模型认为」升级为可核验的结构断言

## 目标与退出标准

承序 78。§7 的 `NOT_JUDGED` 第 1/2/3 项**仍然不判**（那要人评或独立模型）；
本轮做的是让**独立模型已经给出的判词**变得**可核验**。

### 判词为什么现在不可核验

`PanelVerdict.rationale` 是模型写的自由文本。读者拿到「REFUTED: the Results section
overstates what the measurements show」这句话时**无法核对**它指的是正文哪一句 ——
它可能指着一句不存在的话，也可能什么都没指。面板因此停在「某个模型认为」。

### 本轮把它变成什么

- 正文切成**编号句子**（`S1…Sn`）；
- `REFUTED` 的判词必须**落在正文的字节上**：要么点名 `S<n>`（且 `n` 在范围内），
  要么引用一段**正文的真实子串**；
- 核验不成立 ⇒ 该条判词**降级** `AMBIGUOUS` 并**点名缺什么**（不静默通过、不静默丢弃）。

**射程（写死）**：「某个模型认为 X 句有问题，且那句话确实在正文里」——**不是**
「论证成立」，**不是**「叙述质量已判」。`NOT_JUDGED` 五项逐字不动。

## 循环入口协议

1. 读本文件「迭代日志」最后一行 → 若该 cycle 未收口，从其「下一轮输入」续；
2. 读 `latest_recheck`（若非 null）→ **未 PASS 不得进入收口**；
3. 五条 EC 全部 PASS 且 CI 到终态 ⇒ 进「终止与收口」；
4. 任一 EC 被结构性堵住 ⇒ 移入「残余与未覆盖范围」，**继续做剩下的**，GOAL 保持 ACTIVE；
5. 工作树上有**别人**的未提交改动 ⇒ 只 add 本 cycle 的显式路径，绝不 `add -A`。

## 单 cycle SOP

① derive → ② 执行 → ③ 本地验证（定向套件 + 全量 m0 见证）→ ④ commit（显式路径）
→ ⑤ push main + CI 轮询 → ⑥ 纠错 → ⑦ 回写记录 + 下一轮。

**记录顺序**：写全部记录 → `git add` 全部受判文件 → 记录面判据
→ **最后**跑 `tools/run_m0_with_witness.py` → 之后不再改树 → 提交推送。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | ruff / mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest 断言 | 读失败输出定位；**修产品优先，禁改断言迁就** |
| 台账为空 | `test_goal_ledger_covers_every_commit`：CI 台账没有提交 | 首推后**先补台账行再推下一笔**（序 78 实测） |
| 行尾漂移 | 一条 LF 锚点判据突然红 | 检查是不是自己把文件写成 CRLF |
| flake/env | 已知签名（observability OTLP 端口、teardown race） | 按既有配方重跑 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 ⇒ BLOCKED |

## 终止与收口

- **ACHIEVED**：五条 EC 全 PASS + RECHECK（PASS / PASS_WITH_WARNINGS）+ 全量 m0 见证
  终态行 + CI 到终态 + 两树复检 + 本文件收口。
- **BLOCKED**：命中 `escalation_triggers`，或同一失败签名超过上限，或 `max_cycles` 触顶。
- **ABORTED**：用户撤销目标。
- 三个终态都必须把「残余与未覆盖范围」写实，不得留空。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261112-111 | 见台账 | 引用面判据 19 + 质量/面板 36 + 阶梯射程 5；收口验证器 **69 PASS / 0 FAIL**；ruff/format/mypy 三道绿 | 与收口提交同一次 push（无独立 run；不冒领） | 两处（引用子串命中未计数 ⇒ 真引用被判 NOT_GROUNDED；切句同源判据按变量名匹配 ⇒ 改按正则字面量） | `W-1`/`W-2` 残余、`U-1`/`U-2` 未覆盖 | 序 80（实验生成级） |

## 残余与未覆盖范围

### 残余（本轮已交付里仍然存在的缺口）

- `W-1` **句子编号只在整份正文上一次给出**：`number_sentences` 对**全文**切句，
  而面板实际看的是**按 rubric 切出的有界摘录**（`manuscript_excerpts`，4000 字符上限）。
  于是 `S<n>` 在「摘录内的第 n 句」与「全文的第 n 句」之间**可能错位**——本轮的核验在
  **全文**上做（判词引用的句子必须真的在稿件里），但**不**保证「模型看到的摘录里
  `S<n>` 指的是同一句」。给摘录也编号是另一个设计问题（要决定编号是全文的还是局部的），
  本轮未做。
- `W-2` **子串核验依赖模型的引号用法**：`panel_grounding` 只认 `"…"` / `“…”` 包起来的
  片段（≥12 字符）。模型若用单引号或不加引号直接抄原句，会被判 `NOT_GROUNDED`
  ——这是**保守**的方向（宁可降级也不假绿），但会漏掉一些本来可核验的判词。

### 未覆盖范围（本轮**没有**触及的面）

- `U-1` **未用真实模型跑过一次降级**：四条判据全部离线（`ground_verdict` 是纯函数，
  判据用构造的 `PanelVerdict`）。真实会话里模型**会不会**主动写 `S<n>`、写了之后
  **降级率多高**，本轮没有读数——那是 live 门后的事（CI 无凭据）。
- `U-2` **提示词没有要求模型写 `S<n>`**：`panel_prompt` 逐字未改（仍是「一行判词 +
  一句话理由」）。模型不知道要引用编号 ⇒ 真实路径上**大多数 `REFUTED` 会被降级**。
  加提示词约束会改**提问面**（等同改口径），本轮不做；这是 `U-1` 的下一个自然步骤。

### 声称边界（**不得宣称**的事）

- `R-1` **判词可核验 ≠ 叙述质量已判**：核验只证明「那句话确实在正文里，且判词指着它」。
  「论证是否成立」「引用是否真的支持那句话」仍然**不可机械判**——这正是 `NOT_JUDGED`
  第 1/2/3 项继续存在的原因。**判定表一字未动，五项逐字未动。**
- `R-2` **面板仍 advisory**：判词落 `ReviewFinding`（`review_type = manuscript_panel`），
  **不**产生 `Decision`、**不**参与验收门、**不**改变任何 run 的终态。可核验化改变的是
  「读者能不能核对这句话指哪」，**不是**「面板的意见有没有约束力」。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-12 | ACTIVE | 建档：序 79；五条 EC；`NOT_JUDGED` 五项不动 |
| 2026-11-12 | ACHIEVED | 五条 EC 逐条落地；判词可核验 ≠ 叙述质量已判（`R-1`）；摘录编号/引号形态/live 降级率未做（`W-1` / `W-2` / `U-1` / `U-2`） |

## CI 台账

（逐提交逐 job。**零 run ≠ cancelled**；判红也如实登记。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
