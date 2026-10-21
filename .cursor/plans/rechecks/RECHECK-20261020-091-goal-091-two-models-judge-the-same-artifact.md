---
id: RECHECK-20261020-091
slug: goal-091-two-models-judge-the-same-artifact
title: GOAL-091 复检 —— 两个不同评审模型对同一产物各判一次（真跑取证）
status: COMPLETED
result: PASS
created_at: 2026-10-20
updated_at: 2026-10-20
plan_id: PLAN-20261020-091
parent_goal: GOAL-20261020-091
owners:
  - root-agent
verify_paths:
  - tests/application/run_orchestration/test_review_score_reads_the_envelope.py
  - tests/application/run_orchestration/test_review_material_in_prompt.py
  - tests/e2e/test_two_models_judge_the_same_artifact.py
  - tests/e2e/test_two_models_judge_the_same_artifact_live.py
  - tools/run_m0_with_witness.py
memory_entries: []
---

# RECHECK-20261020-091 — GOAL-091

## 检查结果

**PASS**。六条 EC 全部达成；真跑一次取得**有效分歧读数**（`glm-5.3` REJECT 0.45 /
`kimi-k2.6` PASS 0.82，`dissent` 非空、`independent is true`）。过程中剥出并修掉一处
**既有缺陷**：检索段 / 前序段在真实会话里**从未进过提示词**（见「七、既有缺陷」）。

## 一、建档实测的三处缺口（先钉缺口存在）

| # | 缺口 | 实测读数 | 修法 |
| --- | --- | --- | --- |
| 1 | `REVIEW_SCORE` 只读**顶层**点分路径，而真实交付物是**信封**（正文在 `content` 里） | 同一分数 `0.5`：直形态取到 `0.5`、信封形态取到 `None` ⇒ 恒 `review score unknown` ⇒ 恒判负 ⇒ **两个模型无论判什么都只得到一个「不知道」** | `evaluation_gate._unwrap_deliverable`：在**路径每一段**上先看是不是信封，是则用既有 `declared_object` 解包 |
| 2 | 上游产物只以**证据**身份落库，**不进**评审者的提示词 | `compose_prompt` 只有三段（方向 / 前序 / 检索）；被评对象在 `cross_phase_inputs` 里但零提示词消费者 | 新 `review_material.py` + 第四段（并列、有界、截断可见、同源）；只对 `REVIEWER` 挂 |
| 3 | 多评审聚合面已就位但**零真分歧** | GOAL-085/086/087 已补齐「可归因 / 同 phase 成组 / 一位判负不取消同批」，既有判据全用受控执行体 | 新协议 `dual_model_review_v1` + 四条成对判据 + 真跑 |

## 二、既有判据改动逐条申报

基线 `1463a8f2`（本轮起点）。**判定口径**：删除行必须逐条给出「原谓词 → 新谓词 + 为什么不是
放宽」；新增行一律是**收紧或显式登记**。

| 文件 | `numstat`（+/-） | 删除的谓词 / 行 | 现在的谓词 | 性质 |
| --- | --- | --- | --- | --- |
| `packages/application/run_orchestration/phase_input_material.py` | +5 / −2 | `raise InvalidInputError(f"... {{{{'{key}': {{...}}}}}} ...")`（嵌套花括号被当成**格式说明符**） | 形状串用**字面量**拼（`shape = "{'" + str(key) + "': {...}}"`） | **缺陷修复**：原写法在这条 fail-closed 分支**自己抛 `ValueError`**（`Invalid format specifier`），于是「解不出来」被报成一个无关的格式化错误。判据侧无断言被改 |
| `packages/application/run_orchestration/retrieval_prompt.py` | +34 / −8 | `section = render_retrieval_prompt(view)` / `render_prior_knowledge_prompt(view)` 直接调用 | `section = _section_of(view, render)`：**`str` 原样用**，视图才渲染 | **缺陷修复 + 收紧**：见「七、既有缺陷」。零回归有一条判据钉住（`compose_prompt(...) == purpose` 在空串 / `None` 下逐字成立） |
| `packages/application/run_orchestration/evaluation_gate.py` | +41 / −0 | —（纯新增） | `_unwrap_deliverable` + 路径每段解包 | 纯新增（直形态逐字不变，有判据钉住） |

**零改动声明**：`aggregate_panel` / `PanelVerdict` / `run_panel`（聚合语义**一行未动**）；
`review_panel_judging`（GOAL-087 的组级判定**一行未动**）；`TrustLabel` 与
`count_retrieved_sources`（**一行未动**）；既有三个提示词段的**渲染器**（`render_*_prompt`）
**一行未动** —— 改的是「传进来的值是不是已渲染的字符串」这一层。

## 三、两向按压 / 反证（真装配上改事实）

| 项 | 按压/反证 | 判据读数 |
| --- | --- | --- |
| EC-01 fail-closed 四态 | 正文无 JSON / 分数非数 / 分数是布尔 / 只有 `content` 无 `declared_artifact` | 全部 `None`（**不**回落默认分） |
| EC-01 信封判别 | 直形态 `{"review_decision": {"score": 0.5}}` | `0.5`（既有口径零回归） |
| EC-02 零回归 | 未声明跨相输入 / 非 `REVIEWER` / 未接装配器 | `compose_prompt(...) == purpose`（逐字）；spec **同一对象**返回 |
| EC-02 有界 | `max_chars=50` | `len(shown) == 50`、`truncated is True`、`TRUNCATED_MARK` 在提示词里 |
| EC-02 同源 | 截断前后 | `digest == Digest.of_bytes(shown)`，截断前后是两个不同 digest |
| EC-03 独立性 | `reviewer_b` → `critic_independent` | `targets == ["main/glm-5.3"]`、`independent is False`、note 点名该目标 |
| EC-03 单评审 | `min_instances: 1` | `panels == []`、`panel_count == 0` |
| EC-03 两位读同一件 | 两份提示词的 `UNDER REVIEW` 段 | **逐字相同**（同一份产物、同一摘录） |
| EC-06 第三态 | 见证搬到临时目录 | `verify_only() == 2` 且**不创建**见证 |
| EC-06 纯读 | 见证在位时调用 `verify_only()` | 见证**字节一字不变** |

## 四、真跑读数（EC-04，真实中转站 + 真实 runtime）

**协议**：`dual_model_review_v1.yaml`（`author` 写 `research_plan` → `review` 两位评审者
各判一次，`review_panel: COMPLETE_THEN_JUDGE`）。
**装配**：产品组合根（`preflight_override is None`）+ `RESEARCHOS_AGENT_RUNTIME=openhands`
+ 端点 `main`（`LLM_MAIN_KEY`）。
**run**：`f869322c…`（终态 `FAILED` —— 评审判负是**正当结论**，不是基础设施失败）。

| 评审者 | 解析后的执行目标 | verdict | 分数 | 分数是否过阈值 0.8 |
| --- | --- | --- | --- | --- |
| `reviewer_a` | `main/glm-5.3` | **REJECT** | 0.45 | 否 |
| `reviewer_b` | `main/kimi-k2.6` | **PASS** | 0.82 | 是 |

**面板读面**（`review_read`）：
`{"scope": "PHASE", "voters": 2, "votes": {"PASS": 1, "REJECT": 1}, "advisory": null,
"dissent": ["gate:reviewer_a:REJECT", "gate:reviewer_b:PASS"], "ineligible": [],
"targets": ["main/glm-5.3", "main/kimi-k2.6"], "independent": true}`。

### 两位模型各自的判词全文（逐字）

**`main/glm-5.3` → REJECT 0.45**

> **Verdict: REJECT as written (revision needed).**
>
> **What the plan gets right.** All three required components are present and coherent. The
> question is concrete and answerable; the hypothesis is directional (explicit structured
> planning > direct generation on unit-test pass rate); and the falsification test points the
> right way — it names the outcome that would kill the hypothesis (planning condition failing
> to beat the baseline on a matched benchmark), so it is not tautological or unfalsifiable in
> spirit.
>
> **Why it still fails the "could actually refute" bar.** The refutation test is not a
> decision procedure as written:
>
> 1. **"Significantly higher" is undefined.** No statistical test (per-task paired comparison?
>    two-proportion z-test?), no α level, no minimum effect size. With a small sample a real
>    effect will never reach significance; with a huge one a trivial effect will. The verdict is
>    thus left to unstated free parameters chosen post hoc by the implementer — a
>    garden-of-forking-paths risk.
> 2. **"A matched benchmark" is unnamed and un-matched in any defined sense.** Whether explicit
>    planning helps is plausibly benchmark-dependent (HumanEval-style function synthesis vs.
>    SWE-bench-style repository repair); the test harness, the metric (pass@1 averaged over
>    tasks? per-task binary outcomes?), and flaky-test handling are all unspecified.
> 3. **No experimental design.** Number of tasks, which model(s) (the hypothesis says "an LLM
>    coding agent" — singular, unspecified, and generalizing from one model would over-claim),
>    repeat runs/temperature/seed variance, and no equal-compute or equal-token control.
>    Planning consumes context and tokens, so an unmatched baseline confounds the comparison.
> 4. **The intervention itself is unoperationalized.** "Structured plan" could mean a fixed
>    template, free-form prose, or pseudocode — each a different intervention, so the study is
>    neither reproducible nor well-posed. The baseline is also suspect: modern models plan
>    implicitly in their reasoning, so "direct generation" is not a clean no-planning condition.
>
> **Weakest link.** The refutation test's decisive term — "significantly higher" — has no
> statistical definition (no test, threshold, or effect size), and the benchmark and sample size
> are unspecified, so two competent experimenters following the plan as written could reach
> opposite verdicts; no stated procedure genuinely puts the hypothesis at risk.
>
> This is a sound research seed with nothing wrong in what it says — but everything that
> determines the refutation outcome is missing, so I would not execute it as written without
> first pinning down the benchmark, sample size, statistical decision rule, model(s), and the
> operational definition of "structured plan".
>
> ```json
> {"review_decision": {"verdict": "REJECT", "score": 0.45, "weakest_link": "The refutation test hinges on 'significantly higher' with no specified statistical test, significance/effect-size threshold, benchmark, or sample size, so no stated procedure can decisively refute the hypothesis."}}
> ```

**`main/kimi-k2.6` → PASS 0.82**

> The plan clearly states a focused research question, a directional hypothesis, and a
> falsification test that logically could refute the hypothesis: if the planning condition does
> not outperform direct generation, the claim that planning yields higher pass rates is
> undermined. The weakest link is the refutation test’s failure to operationalize what counts as
> “significantly higher.” Without specifying a statistical test, significance threshold, or
> minimum effect size, the criterion for falsification remains vague, meaning different
> researchers could disagree on whether the results actually refute the hypothesis once data are
> collected.
>
> ```json
> {"review_decision": {"verdict": "ACCEPT", "score": 0.82, "weakest_link": "The refutation test does not operationalize 'significantly higher,' leaving the falsification criterion undefined and open to interpretation."}}
> ```

**读数说明（重要）**：两位模型指出的是**同一个弱点**（“significantly higher” 未被操作化），
但**严重程度判断不同** —— `glm-5.3` 认为「没有决策程序 ⇒ 不算可反驳 ⇒ 不可执行」，
`kimi-k2.6` 认为「逻辑上可反驳 ⇒ 弱点但可接受」。这正是本 GOAL 要的读数形态：
**分歧来自判断标准，而不是来自「有没有看到同一份东西」**（后者是修缺口前两位判负的成因）。

全文归档：`scratch/goal091-ec04-verdict-bodies.txt`（gitignored；正文已逐字抄入本节）。

## 五、判据清单与读数

| 判据文件 | 条数 | 读数 |
| --- | --- | --- |
| `tests/application/run_orchestration/test_review_score_reads_the_envelope.py` | 4 | 4 passed |
| `tests/application/run_orchestration/test_review_material_in_prompt.py` | 12 | 12 passed |
| `tests/e2e/test_two_models_judge_the_same_artifact.py` | 4 | 4 passed |
| `tests/e2e/test_two_models_judge_the_same_artifact_live.py` | 1 | 门关 ⇒ 如实 skip；门开 ⇒ **1 passed** |
| `tests/tooling/test_m0_witness_matches_the_tree.py` | 8 | 7 passed（新增 1 条；`test_the_witness_is_for_the_tree…` 在正式见证重跑前如实判红） |

## 六、零回归

受影响套件（顺序执行）：**4013 passed / 92 skipped**（`tests/e2e tests/architecture tests/tooling
tests/application tests/contracts`；三条判红全部由本轮改动引起并已修：① 新增 live 模块需进
`LIVE_MODULES` / `LITERAL_MENTIONS` 两张显式清单 —— 那是判据的设计意图，登记后 14 passed；
② 见证在正式重跑前如实判红）。补跑面：`tests/architecture tests/tooling tests/loaders
tests/contracts` = **2428 passed / 72 skipped**（1 红 = 见证，同一条）。
`tests/tooling/test_python_source_limits.py` = **1313 passed**（`composition.py` 曾在 452 行，
按 450 硬上限压到 450：把 `review_material_builder` 改为收 `ports` 聚合并压掉一条注释）。
定向套件逐条：

- `tests/application/run_orchestration`：**298 passed**；
- `tests/application/test_retrieval_prompt_renderer.py` + `test_prior_knowledge_in_prompt.py`
  + `tests/api/test_project_direction.py` + 新判据：**47 passed**；
- 既有评审链（`test_review_score_linkage_on_the_run_path.py` /
  `test_reviewers_on_one_phase_form_a_panel.py` /
  `test_a_rejecting_reviewer_does_not_cancel_the_panel.py` /
  `test_review_panel_aggregation.py`）：**282 passed**。

## 七、既有缺陷（本轮实测剥出并修掉）：三段提示词在真实会话里从未生效

**现象**：真跑时两位模型都报告「UNDER REVIEW 段不存在」，而我们在 `compose_prompt`
显式传了它。

**剥法**（逐层取证，不靠猜）：

1. 在装配器处打点：`with_review_material` **确实**挂上了 `ReviewMaterialView`（内容是被评
   对象正文）⇒ 缺口不在装配；
2. 在 `SessionBuilder.build_session` 处打点 `compose_prompt` 的**入参**：`review_material`
   是**已渲染的 `str`**（长度 1028、`"UNDER REVIEW" in text == True`）⇒ 四段都在；
3. 在 `LocalConversation.send_message` 处打点**实际发出的字符串**：`len=1082`、尾部是合约
   文本 —— **被评对象段整个不见**。

**根因**：`task_executor._run_session` 把 `session_prompts.*_prompt(spec_context)` 的返回
（**已渲染的 `str`**）放进 `AgentSessionSpec`，而 `SessionBuilder` 又把它交给
`compose_prompt`；`compose_prompt` 的 `prompt_with_*` 按**视图对象**调用
`render_*_prompt(view)`，对字符串取 `getattr(view, "entries", ())` ⇒ 空元组 ⇒ **返回空串**
⇒ 那一段被**静默丢弃**。

**这意味着**：GOAL-081 的「检索摘录进提示词」与 GOAL-082 的「前序知识进提示词」在
**真实会话**上一直没生效（它们的判据测的是渲染器与 `compose_prompt` 的**纯函数**行为，
而缺陷在「谁把什么交给谁」这一层 —— 这正是「判据绑错了对象」的又一例）。

**修法**：`_section_of(value, render)` —— `str` 原样用，视图才渲染。零回归由
`test_a_rendered_section_string_survives_the_composer` 与既有 `== purpose` 判据两侧钉住。

## 八、收口读数

见 GOAL 的「迭代日志」与「CI 台账」。

## 结论

**PASS**。六条 EC 全部达成，且**真跑取证成立**：

- **不同模型**：`main/glm-5.3` 与 `main/kimi-k2.6` 各落一条判词，`reviewer_model` 互不相同、
  可归因到解析后的执行目标；
- **同一被评对象**：两位读的是**同一份**上游产物（跨相输入逐字同一份、提示词段逐字相同）；
- **分歧可读**：`votes {"REJECT": 1, "PASS": 1}`、`advisory null`、`dissent` 两条逐字点名、
  `independent is true`；
- **两条反证**都判红：同模型 ⇒ `independent is False` 并点名；单评审 ⇒ `panels == []`；
- **顺带修掉一处既有缺陷**：检索段 / 前序段在真实会话里从未进过提示词。

**未触发停止条件**：两位模型**没有**同判（0.45 判负 vs 0.82 判过），因此不需要把阶梯
`下一级` 改写为「用第三方模型打破同质化」。

## 八之二、见证的第二个盲区（本轮实测）：新增文件在被跟踪之前不在受判面里

**现象**：m0 全绿（24 条 `PASS [`、终态行正确、`--verify-only` 报「覆盖成立」），提交后
`--verify-only` 立刻报**覆盖不成立**，差的 **13 项全部是本轮新增的文件**（判据、协议、
装配器、记录……），且方向单一（「内容变了/新增 13 项；见证里有而当前没有 0 项」）。

**根因**：`tree_fingerprint` 的受判面取自 **`git ls-files`**（已跟踪文件）。新增文件在
`git add` **之前**不在其中 ⇒ 门跑它们（pytest 会收集未跟踪的测试文件）而见证**不记录**
它们 ⇒ 「门看到的树」与「提交后的树」在内容上不一致，而见证**看不出来**。

**为什么这比 GOAL-090 的三次判红更隐蔽**：那三次是**绑错了对象**（脏清单 / 平台字节 /
HEAD），每一版都在 CI 上立刻红；这一次**本地全绿、`--verify-only` 也报成立** —— 因为
不一致只在「提交之后」才显现，而那一步正是 `--verify-only` 想替你省掉的那一步。

**处置（本轮）**：提交后**重跑**全量 m0，让新增文件进入受判面，取得覆盖成立的正式见证。
**这是顺序纪律的正确形态**：先提交（让新文件被跟踪）→ 再跑门 → 之后不再改树。

**未修的部分（如实登记）**：本判据**不会**在提交前提醒「你有未跟踪的受判面文件」。
可选的收口是让 `tree_fingerprint` 同时记录**未跟踪**的受判面文件（用 `ls-files --others
--exclude-standard`），但那会改变 GOAL-090 定下的口径（且 `--verify-only` 的语义随之变化）
—— 属下一轮，不在本轮范围。

## 八之三、正式见证与 CI 读数

- **正式见证**（提交后重跑，覆盖成立）：`terminal_line` = `PASS: profile=m0; 23 deterministic checks`，
  `green: true`，`tree_changed_during_the_run: false`，受判面 **4540** 个文件；
  `--verify-only` 退出码 `0`（「覆盖成立」）。
- **m0 计数**：`PASS [` **24** 行、`FAILED:` **0** 行（23 项 deterministic checks +
  `release-assets-immutable` 在计数之外）。
- **CI**（逐提交）：`7f5446ab` / `eff7c34d` → [M0 39486782767](https://github.com/Eswink/research-system-new/actions/runs/39486782767)
  **八 job 全 `success`**、[CodeQL 39486782251](https://github.com/Eswink/research-system-new/actions/runs/39486782251)
  **三 job 全 `success`**；最终树 `5e949122` → [M0 39494047272](https://github.com/Eswink/research-system-new/actions/runs/39494047272)
  **八 job 全 `success`**、[CodeQL 39494047688](https://github.com/Eswink/research-system-new/actions/runs/39494047688)
  **三 job 全 `success`** —— **零判红、零 cancelled**（`aec28e2c` 是记录提交，与 `5e949122`
  一起推，run 覆盖后者）。

## 八之四、两树复检（收口面）

```
TREE current=D:
esearch-system exit=0 verdicts=65 sha256=b947d020939c926e568783358893c647f1914e88176e754c60c37d98610f32ee
TREE clean=D:
esearch-system-clean-tree exit=0 verdicts=65 sha256=b947d020939c926e568783358893c647f1914e88176e754c60c37d98610f32ee
COMPARE identical=True
TWO-TREE PASS
```

**口径说明（如实登记）**：本轮用 `--script-mode shared`（两树共用**主树**的复检脚本）。
原因是 `tree` 模式按**字节**比对两棵树的脚本，而本仓 `.gitattributes` 是
`* text=auto eol=lf`，Windows 主树检出 CRLF、干净 worktree 由 git 归一化 ⇒ 同一份脚本
两处字节不同（`SETUP 入口失败：两树的复检脚本字节不同`）。这与 GOAL-090 的见证指纹
（工作树字节 vs `git hash-object`）是**同一个坑**的第二次现身。

**收口脚本**：`tools/verify_goal091_closeout.py`（标准断言集 + `tools/goal091_closeout_assertions.py`
的本轮特有断言 + 记录面），**65 条判词全 PASS、零 FAIL**。

## 八之五、收口后又抓到一处（本轮第二次「判据文件自身的缺陷」）

**现象**：把本轮两个收口脚本登记进 `IN_SCOPE`（四道门的显式清单）之后，**全量 m0 判红**
一处：`test_python_source_size_limits` 说 `tests/tooling/test_tooling_scripts_meet_product_gates.py`
自己超了 450 行硬顶。定向套件（`test_tooling_scripts_meet_product_gates.py`）当时是绿的 ——
因为该文件自己受 `tests/` 的规模门约束，而定向跑不经过那个参数化测试。

**这与 GOAL-090 记下的形态同族**：新判据文件自身的三类缺陷（可选类型未收窄 / 显式清单未
登记 / 函数或文件超限）**只有全量 m0 抓得到**。本轮第二次撞上同一个坑的第三个分支（文件
行数）。

**修法（纯位移，不改判据语义）**：把该文件顶部的射程说明散文压缩一行（三条 bullet 合成
两行），腾出被两条新登记项占用的体积，回到恰好 **450** 行；`ruff format --check` /
`ruff check` / 规模门 / mypy 四道门重跑全绿（1330 passed）。

**如实说明**：这不是「为了绿而改判据」——判据的逻辑一字未改，改的是该文件自己的散文排版。

## 八之六、收口读数（第二次全量 m0，覆盖成立）

- `PASS [` **24** 行、`FAILED:` **0** 行、终态行 `PASS: profile=m0; 23 deterministic checks`。
- 见证：`--verify-only` 退出码 `0`（「覆盖成立：见证覆盖的就是当前这棵树（**4542** 个受判面
  文件）」）；`tree_changed_during_the_run: false`。
- 受判面从 4540 涨到 4542 = 本轮收口脚本两件（提交后才进入受判面，故第二次重跑）。

## 九、未覆盖范围（如实登记）

- **`W-1`：`REVIEW_SCORE` 的分数仍是「评审者自述」**。本轮只让它的**来源**（信封里的正文）
  能被读到，**没有**判它是否与判词一致（低分却写 ACCEPT 这类矛盾仍不可判）。
- **`W-2`：分歧的「质量」无人判**。判据只证明两位**判出了不同结论**，不证明谁的判断更对。
- **`W-3`：只有一个协议、一份被评对象**。`dual_model_review_v1` 的 `author` 格是**单次会话**，
  被评对象的内容质量不在任何判据面上（与 `real_research_deliverable` 同一条诚实边界）。
- **`W-4`：中转站侧瞬时失败会打掉一位评审者**。实测一次 `glm-5.3` 的
  `retry budget exhausted` ⇒ 该位判词为 `UNKNOWN`、面板仍报「1 of 2 rejected」。这是
  **设施失败**，不是评审判负；读面已按 `UNKNOWN` 如实点名（不冒充 REJECT）。
- **`W-5`：`--verify-only` 只覆盖本地树**；CI 覆盖推送后的树，两者对象不同。
- **`W-6`：见证不记录未跟踪的受判面文件**（本轮实测的第二盲区）。提交前新增的文件在
  `git add` 之前不在 `git ls-files` 里 ⇒ 「门看到的树」与「提交后的树」内容不一致而见证
  看不出来。本轮的处置是「提交后重跑」，**判据本身未修**（收口要改 GOAL-090 定下的口径）。
