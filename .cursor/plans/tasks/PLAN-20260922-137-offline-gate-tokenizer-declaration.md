---
id: PLAN-20260922-137
slug: offline-gate-tokenizer-declaration
title: 「默认 CI 离线」的措辞与判据同源：把 tokenizer 预热做成受判的声明（GOAL-011 EC-05）
status: IN_PROGRESS
created_at: 2026-09-22
updated_at: 2026-09-22
parent_goal: GOAL-20260922-011
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    GOAL-20260922-011 cycle 8 = EC-05（`R-6` 词表固化，可选）。授权来源：2026-09-22 用户 goal 模式
    指令 frontmatter `authorization.ref`——(1) push-to-main-for-CI（只推 main、不 force、不重写历史）；
    (2) 默认 runtime 保持 Fake、默认 CI 离线；(3) **不得为了跑通而放宽出站判据**
    （`tests/egress_guard.py` 是结构判据，一行不改）、不得放宽放行面；(4) 凭据纪律不放松（本 PLAN
    不需要凭据，不发起任何真实出站）；(5) `git pull --ff-only` 后只推 main。
    **本 PLAN 明文不做**：改 validator/门禁/快照/测试断言使其通过；skip/删除测试、降低断言强度；
    `git add -A`；伪造或夸大验证证据；放宽验收门凑成功；新增依赖或改上游 pin；
    **引入未 pin 的外部二进制资产**（固化词表的代价见「定案」）。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260922-137 — 「默认 CI 离线」的措辞与判据同源（GOAL-011 EC-05）

## 目标

EC-05（`R-6`）：让「**默认 CI 离线**」这条声明**要么成立、要么如实降级措辞**；
判据 = **断网（或阻断该单一目的地）跑默认门 ⇒ 行为可判定**，且**措辞与事实同源**。

起点实测（derive，只读）：

- **判据已经存在且是结构性的**：`tests/egress_guard.py` 在**任何数据包之前**拦，
  并在会话收尾按记录整轮判红；放行面只有 `requires_live_llm` marker；自证用例在
  `tests/architecture/python/test_default_egress_guard.py`（本 PLAN 实跑：**190 passed**，
  其中 8 条阻断是判据对**文档保留地址** `198.51.100.1` 的故意探测）。
- **下载已被挪到判据进程之外**：`.github/workflows/m0-quality.yml` 在 4 个跑门的作业里
  各有一个 `Prewarm the offline tokenizer cache` 步骤（`uv run --frozen --no-sync python -c "import litellm"`），
  位于 `uv sync` 之后、跑门之前。
- **措辞已经诚实**：`docs/architecture/AGENT_RUNTIME.md:184-190` 逐字写着
  「预热门只是把这次下载挪到**判据进程之外**，CI 每轮仍有一次对外请求（要连这句也消掉，
  得把词表固化进镜像或私有源）——所以「默认 CI 完全离线」**不声称成立**」。
- **缺口（本 PLAN 要补的那一半）**：这条声明**没有任何判据在守**——谁删掉一个作业的预热门，
  默认门在**热缓存**的本机上仍然全绿，只有 CI 的干净安装才会炸；「每轮一次受控外部下载」
  这句也只活在散文里，**没有机器可复核的同源点**。

## 验收条件

- **AC-1 定案写明并落地**：在 (A) 固化词表 / (B) 降级措辞 + 判据 之间选定一条，**写明理由**
  （含代价与不做的原因）。
- **AC-2 声明受判**：新增**离线**判据：**每个跑 Python 门的 CI 作业**都必须在跑门**之前**
  有一个 tokenizer 预热步骤（命令形态受判）；删掉任一预热门 ⇒ 判据**红**（按压）。
- **AC-3 措辞同源且可复核**：`CI 每轮有一次受控外部下载` 这句在**判据自身的文档**与
  **架构文档**里**逐字同源**，并由判据机器校验（不是靠人读）。
- **AC-4 行为可判定**：给出「冷缓存 ⇒ 判据能判红」或「该子集不触及该路径 ⇒ 如实登记」
  的**实跑结论**（不臆测）；`tests/egress_guard.py` **一行不改**。
- **AC-5 规模门禁**：50 行函数 / 450 行文件两道门绿；贴线文件零增长。

## 计划开始前的定案（写死，执行中不得回退）

- **D-1 取 (B) 降级措辞 + 判据，不固化词表**。理由（代价面逐条）：
  (a) tiktoken 的 `cl100k_base` 是一个**外部二进制资产**，固化进仓库/镜像需要引入
  **pin + digest + 更新策略**（AGENTS §12 的上游策略、§5 的「来源必须 pin 到版本/commit/digest」），
  这本身就是一件需要独立记录的工作，远超 EC-05 自称的「成本小」；
  (b) 收益只有**每轮 CI 少一次请求**，而**判据进程内离线**这条真正的性质**今天已经成立且受判**；
  (c) EC-05 原文允许二选一，且明确要求「措辞与事实同源」——把**已经存在的事实**（一次受控下载
  在环境准备阶段发生）**做成受判声明**，是收益/代价比更高的一侧。
  **本 PLAN 不新增依赖、不引入二进制资产、不改 `.github/workflows/m0-quality.yml` 的任何一步。**
- **D-2 判据读的是**workflow 的**结构**，不是注释散文**：按作业切分步骤，按「步骤是否跑 Python 门」
  判定谁需要预热门，要求预热门出现在**同一作业内、跑门步骤之前**。命令形态受判的最小面 =
  含 `import litellm` 且含 `--frozen`（pin 纪律同源）。
- **D-3 同源句写死为**：`CI 每轮有一次受控外部下载`。它同时出现在
  `tests/egress_guard.py` 的模块 docstring（判据自己的家）与 `docs/architecture/AGENT_RUNTIME.md`
  （架构文档）里，由判据逐字校验；**不**把散文整段纳入判据（只锁这一句）。

## 实施清单

- [ ] **WP1** 定案 + 判据：`tests/tooling/test_offline_gate_prewarm_contract.py`
  （作业级预热门位置 + 命令形态 + 同源句两处逐字在场）。
- [ ] **WP2** 按压：摘掉一个作业的预热门 ⇒ 红；复原 ⇒ 绿。把两次输出逐字记录。
- [ ] **WP3** 冷缓存实验：`TIKTOKEN_CACHE_DIR=<空目录>` 跑**含 SDK 导入**的子集，
  记录「判据是否判红 / 是否出现该目的地」，如实写结论（不臆测）。
- [ ] **WP4** GOAL 回写（EC-05 状态 / 迭代日志 / 台账）+ 本轮记录。

## 证据

| # | 事实 | 取数方式 |
| --- | --- | --- |
| E-1 | 判据是结构性整轮判据、放行面唯一 | `tests/egress_guard.py` 的模块 docstring（拦 + 判两条机制、fail-closed、环回放行） |
| E-2 | 判据自证 | `pytest tests/architecture -q` ⇒ **190 passed**（其中 8 条为其对 `198.51.100.1` 的故意阻断） |
| E-3 | 预热门在 4 个跑门作业里 | `rg -n "Prewarm\|import litellm" .github/workflows/m0-quality.yml` ⇒ 4 处 |
| E-4 | 措辞已诚实但不被判 | `docs/architecture/AGENT_RUNTIME.md:184-190` |
| E-5 | 冷缓存实跑 | 本 PLAN 的 WP3 输出（逐字记录） |
| E-6 | 新判据按压 | 本 PLAN 的 WP2 输出（先红后绿） |

## 影响报告

- **Domain / API / schema**：零改动。
- **CI / workflow**：**不改**任何步骤；只新增一条读它的判据。
- **兼容性 / 迁移**：无。
- **安全 / 凭据**：不新增凭据面；本 PLAN **不发起任何真实出站**（冷缓存实验的目标是让判据拦下尝试）。
- **上游版本影响**：无。
- **下一项任务**：EC-06（收口复检：133/134/135/136/137 一并收口 + 两树 + W 列表）。

## 状态历史

- 2026-09-22：derive（WP0）。只读勘察判据、workflow 预热门、架构文档措辞与缺口；定案 D-1…D-3；
  未改任何文件、未发起任何出站。
