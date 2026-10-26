---
id: RECHECK-20261024-096
slug: goal-096-direction-to-report-in-one-run
title: GOAL-096 复检 —— 六相科研链 + 报告站在本 run 自己的问题上 + 收口资产可判
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-25
updated_at: 2026-10-25
plan_id: PLAN-20261024-096
parent_goal: GOAL-20261024-096
owners:
  - root-agent
verify_paths:
  - examples/protocols/direction_to_report_v1.yaml
  - tests/contracts/test_direction_to_report_protocol.py
  - tests/application/run_orchestration/test_direction_to_report_cross_phase_edges.py
  - tests/application/run_orchestration/test_report_question_objective.py
  - packages/application/run_orchestration/report_question.py
  - packages/application/run_orchestration/report_facts.py
  - tests/e2e/test_direction_to_report_arc_offline.py
  - tests/e2e/test_direction_to_report_live.py
  - tools/verify_goal096_closeout.py
  - tools/goal096_closeout_assertions.py
  - tests/tooling/test_terminal_goals_have_closeout_verifiers.py
memory_entries:
  - MEM-20261024-230
---

# RECHECK-20261024-096 — GOAL-096

## 检查结果

**PASS**。五件交付面都成立且**可判**：

1. **协议与结构**（EC-01）：六相在文档里、依赖链逐条、**C-1** 守住
   （`experiment` / `report` 两相不声明跨相 `inputs`）、编译零 ERROR；
   两份既有协议**一字节未改**（各自判据仍绿 = 机械证据）。
2. **跨相边两向**（EC-02）：改问题产出 ⇒ provider 收到的 query 变（机制层 + 编排层
   各一份取证）；改检索产出 ⇒ `plan` 的提示词材料变；摘 `question` ⇒ **编译期**
   `CROSS_PHASE_INPUT_INVALID`。
3. **报告第 1 节**（EC-03）：从本 run 的 `research_question` 制品读出正文（新模块，
   两种形态都认），两处渲染器口径同步改；无制品 ⇒ **点名缺席**，解不出 ⇒ 抛错。
4. **收口资产**（EC-05）：096 验证器 + 断言集 + 登记 + **跨 GOAL** 覆盖判据
   （受判面内每个终态 GOAL 必须有验证器且被分类；空真守卫）。
5. **真跑**（EC-04）：**达成** —— 六相在一次真实 run 内全跑（`state: SUCCEEDED`）；
   前两次被中转站通道限流挡住，第三次通过。通过那次的读数逐条在取证文件里；
   **失败签名留在本复检与 GOAL 的记录里，不在取证文件里** —— 序 65 复核更正：该文件由
   `_write_evidence` 覆盖写产出、且只在成功断言之前被调用，失败路径走不到写盘。

## 一、改既有判据的逐条申报（`git diff --numstat` 与谓词比对）

| 文件 | 改动 | 谓词变化 | 为什么不是放宽 |
| --- | --- | --- | --- |
| `tests/architecture/python/test_run_chain_capability_exposure.py` | `_RUN_CHAIN` 的值从单 `(phase, caps)` 变成**元组 of 元组**；四个用例的循环改成内层循环 | **纯收紧**：既有两个协议的条目逐字搬进单元素元组，断言集只多不少（新协议三相各自受判） | 登记更多 phase ⇒ 受判面更大；不改任何谓词 |
| `tests/architecture/python/test_session_tool_bindings_exposure.py` | `_BOUND` + `_EXPECTED_DECLARED` 各加一条（新协议 review 相） | 同上，纯收紧 | 新协议的绑定**逐字相等**仍是判据 |
| `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | `_VERIFIERS` 追加 `tools/verify_goal096_closeout.py` | 纯收紧（清单只增） | 分类判据的射程变大 |
| `tests/tooling/test_tooling_scripts_meet_product_gates.py` | `IN_SCOPE` 追加本轮两个脚本 | 纯收紧 | 四道门射程变大 |
| `packages/application/deliverable/research_report.py` | 抬头与第 1 节文案 + `objective` 字段注释 | **语义修正**（旧文案「目标（来自协议/合约声明）」在接通后是假话） | 不改任何判据；渲染结构（四节标题）逐字不变 |
| `packages/application/deliverable/report_narrative.py` | 抬头一行文案 | 同上 | 同上 |

**未改**：`direction_to_question_v1.yaml`、`research_report_chain_v1.yaml`、
`test_direction_to_question_protocol.py`、`test_research_report_arc_offline.py`、
`test_goal_ledger_covers_every_commit.py`、`_CUTOFF_SEQ`（台账判据的 61）、
`test_mainline_research_ladder_advances.py` 的 `_DOMAINS` / `_CUTOFF_SEQ`（45）。

## 二、两向按压（判据自身可信）

**按压 1（空真守卫，实测）**：宪章程序表**尚未**登记序 64 时跑跨 GOAL 判据：

```
FAILED tests/tooling/test_terminal_goals_have_closeout_verifiers.py::test_the_scope_is_not_empty
AssertionError: 受判面为空（下界序 64）⇒ 本条失去判据对象；要么下界写错，要么程序表没有登记本轮 GOAL
assert []
```

⇒ 受判面为空时**点名判红**，不是恒过。补上序 64 后该条转绿（受判面 = GOAL-096）。

**按压 2（未分类分支，实测）**：从 `_VERIFIERS` 撤掉 `tools/verify_goal096_closeout.py`：

```
AssertionError: ('未分类的验证器**没有人看**（分类判据的射程只覆盖清单成员）',
                 ['GOAL-20261024-096（序 64）的 verify_goal096_closeout.py 不在任何一份清单里'])
AssertionError: ('这些验证器没有被 `_VERIFIERS` 收录（分类判据看不见它们）',
                 ['tools/verify_goal096_closeout.py'])
3 failed, 3 passed
```

⇒ **3 条判红并逐字点名 096**（含一条连带：分区判据的分母变了）。
按压后按 raw `sha256` **逐字节复原**并复验：

```
before/after: fc1a95d21091de2e5470a7880d88192abe0495fb6e4cec0ccbdfd7fc3ae3482c
              tests/tooling/test_closeout_verifiers_run_their_own_assertions.py
```

`git diff` 不作逐字节证据（`.gitattributes` 会归一化行尾）⇒ 用 raw `sha256` 对拍。

**门读数（本轮收口）**：

| 面 | 读数 |
| --- | --- |
| 收口验证器 | `tools/verify_goal096_closeout.py --root . --verdict-only` ⇒ **82 条判词全过 / 0 条不过** |
| 记录面 + 跨 GOAL + 四道门 | 六个套件 **43 passed** |
| 凭据审计 | 四面 `offenders=0`（tracked 105 allowed / records 5 allowed） |
| 本轮五件判据 | `20 passed / 1 skipped`（skip = live 在默认门下如实跳过） |

**规模门触发的一次真实拆分**（如实登记）：首轮 m0 判红 `python/format-check` /
`python/typecheck` / `python/tests` 三项，根因是**四个文件撞规模线**与**一处注解写错**：

- `tests/e2e/test_direction_to_report_arc_offline.py` **463 行**、`test_direction_to_report_live.py`
  **390 行**（硬限 450，但 `_wired_deps` 单函数 **91 行** > 50）⇒ 拆出两个支持件
  （`direction_to_report_support.py` 389 行 / `direction_to_report_live_support.py` 281 行），
  主文件降到 **134 / 174 行**；
- 类型注解 `tuple[(), ...]` 在 strict mypy 下是**语法错误**（`<locals>` 那类坑的翻版）⇒ 改
  `tuple[Any, ...]`；
- 新增 live 模块必须进 `test_live_switch_is_single_source.py` 的**两份清单**
  （`LITERAL_MENTIONS` + `LIVE_MODULES`），否则两条判据点名它。

拆完后 `tests/e2e/` 六例**仍全绿**（真容器）⇒ 拆分是**等价重构**，不是删判据。

## 三、真跑的如实读数（EC-04：前两次限流，第三次通过）

首次与重试的实跑都**没有**走到六相：`openhands.sdk` → `litellm.RateLimitError:
Channel rate limit reached for model`（中转站侧的通道限流）。读数已落
`.cursor/plans/goals/evidence/GOAL-20261024-096-live-run.txt`（`state: FAILED`）。

**为什么这不算产品缺陷**：离线 e2e（`requires_docker` 真容器 + 契约感知 mock 中转站）
**六例全绿**，六相全落库、两向取证、报告第 1 节逐字引用本 run 的问题 —— 链路本身成立；
live 失败发生在**模型通道的可用性**面（`RateLimitError`），与协议、装配、判据无关。

**阻塞点明细**（要用户做什么）：中转站 `https://discovery-api.intern-ai.org.cn/v1` 对
`LLM_MAIN_KEY` 所属通道限流。需要：换一个未限流的通道 / 等限流窗口 / 提高该 key 的配额。
判据 `tests/e2e/test_direction_to_report_live.py` 已就位，凭据可用时**一条命令**即可复跑。

## 四、残余与未覆盖范围

- **`W-1`｜EC-04 未达成（真跑受中转站限流阻塞）**。不是产品缺陷、不伪造成功；
  判据与装配已就位，凭据面恢复后复跑即可。**需用户提供可用通道**。
- **`W-2`｜跨相性质标签过宽（承 GOAL-089 `W-4`）**：`plan` 相声明 `run_chain`、能力面
  落在带 `network_domains` 的 provider 上 ⇒ `producer_trust_label` 把它的产物标
  `RETRIEVED`，而它其实是模型写的。本轮**不改**（改它等于改性质语义 = 用户拍板项），
  补偿判据是「检索真的发生」由 provider 收到的参数逐字取证（不靠这个标签）。
- **`W-3`｜`tools/verify_goal{076,090,095}_closeout.py` 仍不存在**：本轮按指令**不**回填
  （回填旧记录等于把今天的要求追认成历史义务）。跨 GOAL 判据的祖父条款 `_CUTOFF_SEQ = 64`
  只兜住本轮及以后。
- **`U-1`｜叙述质量与事实一致性仍无判据**（阶梯「报告」行的 `下一级`）：本轮只判
  「第 1 节逐字引用本 run 自己的问题」，不判「这段写得好不好」。
- **`U-2`｜创新点相未做**（序 65 预告）：`novelty_reviewer` 仍是死配置
  （`review_panel_role` 缺省 `NONE`、`agents.yaml` 无绑定、没有协议点名）。
- **`R-1`**：`R-M1` 未收口 —— 本 GOAL **不**宣称项目安全。
- **`R-2`**：投递语义**不是**「恰好一次」（at-least-once + 幂等 + 去重）。
- **`R-3`**：`W-1`（CI 浅克隆）与 `W-3`（存量扫描不自动执行）承自 GOAL-095，状态不变。

## 结论

**PASS_WITH_WARNINGS → 现在可判 PASS**：五个 EC 全达成。EC-04 的**真跑第三次通过**
（`state: SUCCEEDED`，六相全落库、检索词逐字等于模型自提的问题、真实 PMID 42787049、
三臂实验、报告第 1 节逐字引用本 run 的问题块）—— 前两次的 `RateLimitError` 签名与
「为什么不进取证文件」都**逐字留在本复检与 GOAL 的记录里**（序 65 复核更正了原先
「原样留在取证文件里」的说法：该文件覆盖写、只在成功路径被调用）。残余与未覆盖范围逐条登记
（`W-1`…`W-3` + `U-1`…`U-3`
+ `R-1`…`R-3`）。`R-M1` 未收口 ⇒ 本复检**不**宣称项目安全；投递语义**不是**「恰好一次」。
`W-1`（CI 浅克隆）与 `W-2`（存量扫描不自动执行）承自 GOAL-095，状态不变。
