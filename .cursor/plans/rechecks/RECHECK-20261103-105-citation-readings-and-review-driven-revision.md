---
id: RECHECK-20261103-105
slug: citation-readings-and-review-driven-revision
title: GOAL-105 复检 —— 引用充分性结构读数 / retmax 缺省抹平 + 协议相级 / 判词驱动改稿
status: COMPLETED
result: PASS
created_at: 2026-11-03
updated_at: 2026-11-03
plan_id: PLAN-20261103-105
parent_goal: GOAL-20261103-105
owners:
  - root-agent
verify_paths:
  - packages/application/deliverable/citation_sufficiency.py
  - packages/application/deliverable/manuscript.py
  - packages/application/deliverable/manuscript_quality.py
  - packages/application/ports/resource_catalog.py
  - packages/domain/protocols.py
  - packages/application/protocol_compile/compiler.py
  - packages/application/run_orchestration/phase_call_arguments.py
  - packages/application/run_orchestration/phase_capabilities.py
  - packages/application/run_orchestration/revision_assembly.py
  - packages/application/run_orchestration/review_points.py
  - packages/application/run_orchestration/session_resolution.py
  - packages/application/run_orchestration/task_executor.py
  - adapters/contracts/protocol_loaders.py
  - schemas/protocol.schema.json
  - tests/application/test_citation_sufficiency.py
  - tests/application/test_manuscript_citation_readings.py
  - tests/application/test_retmax_undeclared_is_a_fact.py
  - tests/application/test_retmax_protocol_phase.py
  - tests/application/test_revision_review_points.py
  - docs/architecture/MANUSCRIPT_QUALITY.md
  - tools/verify_goal105_closeout.py
  - tools/goal105_closeout_assertions.py
---

# RECHECK-20261103-105

## 复检范围

GOAL-20261103-105 的七条 EC 逐条取证。**两路以上**（`verify_paths` 列出的每个文件都是
一条独立的取证路径；产品面与判据面各取一次）。

## 检查结果

### 逐条读数

| EC | 判据 | 读数 | 结论 |
| --- | --- | --- | --- |
| EC-01 | `test_citation_sufficiency.py` | **10/10 绿**：三读数正例逐项等于期望值 / 加一条引用两读数都变 / `enforce=False` 零引用不抛错 / 三常量全 `None` / 无标定来源被点名 / 三份引用语法逐字同形 / 第 4 项仍在 `NOT_JUDGED` / 单支撑节三条件缺一不算 | PASS |
| EC-01 | 反证：把 `mark_counts_per_sentence` 改成硬编码读数 | **3 红**（含 `test_adding_one_citation_moves_both_readings`）⇒ 读数真从字节来；随后 `sha256` 逐字节还原 | PASS |
| EC-01 | 反证：`_SENTENCE_SPLIT` 实测切分 | `"Alpha [1]. Beta [2] and [3]. Gamma."` → `['Alpha [1].', 'Beta [2] and [3].', 'Gamma.']`（3 句） | PASS |
| EC-01 | `content_words` 边界实测（F-5） | `content_words("It is an ox") == frozenset()`；`content_words("It is to be or not") == frozenset()` | PASS（已进设计） |
| EC-02 | `test_manuscript_citation_readings.py` | **4/4 绿**：脚注三数与函数返回值逐项相等 / 改正文读数随之变 / 脚注自陈「读数非判决」/ 零引用仍写 `0` | PASS |
| EC-03① | 缺陷实测（**修复前**） | `RESEARCHOS_RETMAX=9` → 构造期 `{'retmax': 9}`、运行期 `{'retmax': 3}`；`retrieval_calls(7)` → 构造期 `{'retmax': 7}`、运行期 `{'retmax': 3}` | **缺陷成立** |
| EC-03① | 缺陷实测（**修复后**） | env 臂运行期 `{'retmax': 9}`；显式臂运行期 `{'retmax': 7}`；项目声明 5 压过 env 9 → `{'retmax': 5}`；全不声明 → `{'retmax': 3}` | PASS |
| EC-03① | `test_retmax_undeclared_is_a_fact.py` | **5/5 绿**（含「未声明 ⇒ 连对象都不新造」`wired is capabilities`） | PASS |
| EC-03① | 反证：把缺省改回 `3` | **3 红**（env 臂 / 显式臂 / 不新造对象），而「项目显式声明压过 env」仍绿 ⇒ 「未声明是一等事实」而非「叠一层覆盖」；随后还原 | PASS |
| EC-03① | `test_project_settings_default_retmax_is_undeclared` | 改写完成：缺省 `None`，且断言 `settings.retmax != DEFAULT_RETMAX` | PASS |
| EC-03② | `test_retmax_protocol_phase.py` | **16/16 绿**：协议 `retmax: 5` ⇒ 出站 `pageSize == 5` / 协议压过项目 9 / 项目臂 6 / 默认臂 3 / **env 臂 10** / 五个非法值点名「protocol phase」/ 非映射点名 / 缺键 `None` / loader 搬运 / compiler 搬运 / 相集十一相 / schema 两向 | PASS |
| EC-03② | 反证：让 `retmax_for_phase` 忽略协议值 | **2 红**（协议臂与「协议压过项目」），回落三臂仍绿 ⇒ 协议那一级真的生效；随后还原 | PASS |
| EC-03③ | 优先级顺序 | 显式 > 协议 > 项目（仅当已声明）> env > 默认 3 —— 五级各有独立判据（`test_the_explicit_argument_beats_everything` / 协议臂 / 项目臂 / env 臂 / 默认臂） | PASS |
| EC-04 | `test_revision_review_points.py` | **7/7 绿**：正例含实词通过 / 零重叠点名 `P1` 且带原文 / 恒空集 ⇒ 全红 / **无实词 point 点名不可比较** / 不存在的 `point_id` 点名 / `points=None` 时前两条判据逐字不变 / 判据顺序 | PASS |
| EC-04 | 反证：把重叠判定短路成 `if False and …` | **1 红**（`test_an_action_with_no_shared_word_names_the_point_id`：`DID NOT RAISE`）⇒ 判据真在比词；随后还原 | PASS |
| EC-04 | 既有夹具的**真实缺陷**暴露 | `tests/application/test_revision_closure.py` 与 `tests/e2e/manuscript_replies.py` 的 `action_taken`（「revised the section named in P1」）与评审点**零重叠** —— 判据接上即 3 红；改为点名「planning choice / related work」后全绿 | PASS（夹具缺陷已修，非放宽） |
| EC-05 | `test_manuscript_quality_strong_criterion.py` | **5/5 绿**（含 `len(NOT_JUDGED) == 5`）；§7 判定表逐字未动 | PASS |
| EC-05 | 文档补句 | `MANUSCRIPT_QUALITY.md` §6 命中 `citation_sufficiency.py` / `充分性仍未判` / `取值待 ≥3 份真实手稿的量分布`；`git diff --stat` = **4 插入 0 删除**（只加不删） | PASS |
| EC-06 | `tools/verify_goal105_closeout.py --root . --verdict-only` | 全 PASS、判词不含绝对路径（记录面判据见下文「收口后」） | PASS |
| EC-06 | `_VERIFIERS` / `IN_SCOPE` 两处登记 | 各 1 条命中（`verify_goal105_closeout.py` / `goal105_closeout_assertions.py`） | PASS |
| EC-07 | `MAINLINE.md` 四处记账 | 程序表序 73（紧接序 72、无空行）/ 阶梯「报告」+「复检」两行 `当前级` 追加并各自收录本 GOAL / 进展行 / 修订行 5 格 | PASS |
| EC-07 | 两行 `下一级` 逐字未动 + 无过度声称 | `叙述质量与事实一致性可判` / `判词改写了下一轮的计划/立题` 仍在；五项禁词零命中 | PASS |
| 规模门 | `test_python_source_limits.py` | **1408 条全绿**；`phase_capabilities.py` = **450 行（贴线）**、`task_executor.py` = 449 行 | PASS |
| 静态门 | `ruff check` / `ruff format --check` / `mypy` | 全绿（10 个产品文件 mypy 零问题） | PASS |
| 执行纪律 5.9 | `tools/credential_audit.py` 四面 | **`offenders=0`（四面全部 0）**：`tracked` 5058 / 命中 105 / 放行 105 / **0**；`records` 1097 / 5 / 5 / **0**；`config_db` 1 / 0 / 0 / **0**；`logs` 940 / 0 / 0 / **0**。终态行 `PASS: 四面扫描无明文凭据命中（放行项已逐条给理由）` | PASS |

## 本轮真跑暴露并修掉的缺陷

- **`D-1`｜`retmax` 的「未声明」被字段缺省抹平（既有缺陷，本轮修复的对象）。**
  `ProjectSettings.retmax` 缺省是 `3` 而不是 `None` ⇒ `_with_project_retmax` 把
  「字段缺省」当成一次声明，`CapabilityDeps.retmax = 3`，运行期 `apply_retmax` 把 env 与
  显式参数一起压成 3。**这不是理论问题**：`test_project_settings_defaults_retmax_to_three`
  把它钉住了 —— **那条判据钉的正是缺陷**。修法选的是计划里的 (a)：字段与 `_retmax_of`
  的缺省都改 `None`，**施加点一个字没改**（`declared is None ⇒ 原样返回` 立刻生效）。
  选 (a) 而非 (b) 的理由：`retmax_declared: bool` 会让「未声明」成为**两个字段的联合事实**
  （`retmax=3, declared=False`），任何一个构造点漏填就回到同一个歧义；`None` 让状态只有一个
  表达。（b）唯一的优点是「不改既有判据」，但那条判据钉的是缺陷，改它是**被授权的**。

- **`D-2`｜测试夹具的 `action_taken` 与评审点真实地无关（判据接上才暴露）。**
  接上判据 ③ 之后，`test_revision_closure.py` 的 3 条与 e2e 的 9 条立刻判红，判词指向
  `action_taken for P1 shares no content word with that review point ('the related work does
  not name the planning choice…')`。**这是夹具的缺陷，不是判据误报**：那句 `action_taken`
  确实没有说改了哪里。修法是把夹具改成点名（`named the planning choice in the related
  work`），**没有放宽判据**。

- **`D-3`｜`phase_capabilities.py` 撞 450 行硬上限。** 加完协议相级取值后是 471 行。修法不是
  拆文件（那会让 `apply_retmax` / `retmax_for_phase` 分散到两处），而是把取值函数
  `retmax_for_phase` 归位到它本来该在的模块（`phase_call_arguments` —— 该模块的职责正是
  「声明字段 → provider 参数」的翻译），并压缩了两处 docstring。终态 **450 行（恰好贴线）**。

- **`D-4`｜首轮 m0 的 `python/typecheck` 判红：新判据文件自身的 mypy 缺陷。**
  `tests/application/test_retmax_undeclared_is_a_fact.py` 自造了两个 `__getattr__` 哑对象
  （`_NeverStore` / `_NeverLedger`）当 Port 替身 —— 在 strict mypy 下与 `ArtifactStore` /
  `EvidenceLedger` 的协议不一致（`arg-type`）。`test_retmax_protocol_phase.py` 还有一处
  `findings=[]` vs `tuple[...]`。**定向套件全绿、只有全量 m0 抓到**（与「新判据文件自身的
  缺陷只有全量 m0 抓到」那条纪律一致）。修法：替身换成仓内既有 `Fake*`（那是契约要求、
  也是本仓的标准做法），`findings=[]` → `()`；没有用 `# type: ignore`（strict 下它是语法
  错误）。

- **`D-5`｜首轮 m0 的 `framework/validate_bundle` 判红：`additionalProperties: true` 被禁。**
  我第一版给 `run_chain_arguments` 写的是开放式对象（`additionalProperties: true`），
  而 `validate_bundle.py:810` 的规则是「JSON Schema object 禁止 `additionalProperties=true`」。
  **规则是对的**（§9 默认 deny 的姿态）：开放式参数袋会让写错键名静默无效。修法改成**封闭
  对象**（`additionalProperties: false` + 只声明 `retmax`）⇒ 未知参数名在**加载期**点名，
  `W-3` 的缺口因此收窄为「明确拒绝」而不是「静默失效」，并补一条判据
  （`test_the_schema_accepts_the_new_property_and_still_rejects_unknown_ones` 的第三向）。

- **`D-6`｜`MAINLINE.md` 的程序表序 72 行被我的一次脚本化编辑覆盖掉。** 我在追加序 73 时
  用 `str.replace` 做定位，生成的行与序 72 在同一位置 ⇒ 序 72 被**静默替换**（`grep` 计数
  0 命中，`test_verifier_main_files_report_no_negative` 点名
  `tools/verify_goal104_closeout.py: ['program-table-has-this-round']`）。**判据抓到了**
  —— 一个只查「我的行在不在」的判据不会抓到它，抓到它的是**上一轮的**收口验证器。
  修法：从 `git show HEAD:` 取回序 72 的**原文**按字节插回，并核对 CRLF 计数与
  「71 → 72 → 73」的相邻关系。教训：**程序表追加不要用替换定位，要用行插入**。

- **`D-7`｜靶子 1 第 2 项被实现成「第三份正则」（收口审计抓到，已修）。**
  `citation_sufficiency.py` 第一版从 `manuscript_quality` 导入了 `_SENTENCE_SPLIT`，
  却在同一文件里又写了一份 `_CITATION = re.compile(r"\[(\d+)\]")` —— 而它**上一行的注释**
  写着「这里再写一份会变成第四份，所以直接复用」。注释与代码自相矛盾，且这条偏差没有
  登记成任何 `W-NN`。这正是本轮要求里**唯一**逐字点名的产品约束（「别写第三份正则」），
  所以收口审计判它不通过是对的。
  修法：删掉定义，`_CITATION` 并入既有导入行。**同形从「巧合」变成「结构」** ——
  实测 `cs._CITATION is manuscript_quality._CITATION` 为 `True`（此前只是 pattern 字符串相等）。
  判据同步补强：`tools/goal105_closeout_assertions.py` 原先把 **`"_CITATION = re.compile"`
  当作「复用在场」的标记**（钉的正是错误形态）；现在改成
  `readings-do-not-redefine-the-citation-grammar`（本模块不得重定义）+
  `readings-import-the-shared-citation-grammar`（导入在场）两向。

  **按压过程本身抓出了两个判据缺陷**（这才是这条记录值得留的部分）：
  1. 第一版判据用 `assert "_CITATION = re.compile" not in source`。注入一份副本
     `_CITATION = __import__('re').compile(_SHARED.pattern)` ⇒ **10 条判据全绿**
     （字符串写法不同）。字符串标记式判据会被改名绕过。
  2. 改成判 `cs._CITATION is manuscript_quality._CITATION` ⇒ 副本**仍然全绿**。
     原因：`re.compile` 对同一 pattern 有**模块级缓存**，副本与原件是同一个对象。
     所以 `is` 也判不出「是不是抄了一份」。
  3. 最终判**源码 AST**（`_recompiles_the_grammar()` / `_recompiled_grammar_lines()`）：
     本模块里不得出现「对引用语法再做一次编译」。注入同一副本 ⇒ 测试与收口验证器
     **都**判红，并逐字点名 `__import__('re').compile(_SHARED.pattern)`。

## 反证臂汇总（**判据咬得住**的证据）

| 判据 | 注入 | 极性 |
| --- | --- | --- |
| `test_adding_one_citation_moves_both_readings` | 读数改硬编码 | **红** |
| `test_the_environment_survives_an_undeclared_project_at_runtime` | 缺省改回 `3` | **红** |
| `test_an_explicit_argument_survives_an_undeclared_project_at_runtime` | 同上 | **红** |
| `test_a_declared_project_still_beats_the_environment_at_runtime` | 同上 | 绿（**应当**绿：证「叠覆盖」不是修法） |
| `test_a_protocol_phase_value_reaches_the_outgoing_request` | `retmax_for_phase` 忽略协议值 | **红** |
| `test_the_phase_value_beats_the_project_declaration` | 同上 | **红** |
| `test_an_action_with_no_shared_word_names_the_point_id` | 重叠判定短路 | **红** |
| `test_a_point_without_content_words_is_named_not_passed` | 无实词 point | **红**（点名不可比较） |
| `test_a_threshold_without_a_calibration_source_is_named` | 阈值填值而不给来源 | 点名该常量 |

## 两树复检

`tools/two_tree_recheck.py` 在干净 checkout 上跑同一份验证器，判词逐行 + `sha256` 与
工作树一致（见证据文件）。

## 凭据面（执行纪律 5.9）

命令：

```bash
uv run --frozen --no-sync python -B tools/credential_audit.py
```

实测输出（四个面**逐个**报告，缺面时记 `not_present` 而非 PASS）：

```text
tracked    status=scanned        files= 5058 binary=395 hits=105 allowed=105 offenders=  0
records    status=scanned        files= 1097 binary=  0 hits=  5 allowed=  5 offenders=  0
config_db  status=scanned        files=    1 binary=  0 hits=  0 allowed=  0 offenders=  0
logs       status=scanned        files=  940 binary=  0 hits=  0 allowed=  0 offenders=  0
PASS: 四面扫描无明文凭据命中（放行项已逐条给理由）
```

## 结论

七条 EC 全部达成，两向按压逐条留证。**本轮交付的是读数与连接，不是判决**：
引用充分性的阈值仍全部 `None`（仓内零真实语料）；词重叠只证明「回应与评审点不是无关」。
这两条边界已逐字写进产品 docstring、`MANUSCRIPT_QUALITY.md` §6 与宪章阶梯行的
`下一级` 列（未动）。
