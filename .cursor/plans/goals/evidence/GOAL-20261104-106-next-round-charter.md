# 下一轮 charter 骨架（GOAL-20261103-105 → GOAL-20261104-106）

> 本文件由 `tools/next_round_charter.py` **确定性**产出：零出网、零模型、零时钟。
> 同输入 ⇒ 逐字节相同。**判断面**（objective / EC 的内容）不在这里 —— 见末节，
> 那些位置显式留空（`<待填：判断>`），不由本工具猜。

## 一、输入（内容寻址）

- 上一个 GOAL：`.cursor/plans/goals/GOAL-20261103-105-citation-readings-and-review-driven-revision.md`（`status: ACHIEVED`）
- 上一个复检：`.cursor/plans/rechecks/RECHECK-20261103-105-citation-readings-and-review-driven-revision.md`（`result: PASS`）
- 宪章：`.cursor/plans/goals/MAINLINE.md`
- 摘要：goal `sha256:528cd2be3e0db67f`；recheck `sha256:8520b2734eee0e26`；charter `sha256:1e4561e76b92a916`

## 二、上一轮的残余与未覆盖范围（逐条原文，**不摘要**）

共 5 条（`W-1`…`W-5`）。搬运时**不得删、不得改写**；每一条都要在下一轮里被处置
（做掉 / 明确承接 / 登记为不做并给理由）—— 处置**不是**本工具的事。

- `W-1`｜**三个读数没有阈值，也判不出「充分」**：`MIN_MARKS_PER_SENTENCE` /
  `MIN_CITATIONS_PER_REFERENCE` / `MIN_SUPPORT_PER_SECTION` **全部 `None`**。仓内**零真实
  手稿语料**（`manuscript*.md` 0 命中、`data/e2e.db` 的 `artifacts` 0 行、最大夹具 209 词）
  ⇒ 任何数字都是编造。`uncalibrated_thresholds()` 只保证「填了值必须有标定来源」，它**不**
  保证那个来源是真的够用。
- `W-2`｜**词重叠是必要不充分**：`action_taken` 与 `ReviewPoint.text` 共享一个实词就通过 ——
  「已按 reproducibility 相关意见修改」与一个讲 reproducibility 的评审点重叠，但正文可能
  一个字都没改对。判「解决了那个问题」需要语义蕴含 ⇒ 人评。射程已写进 docstring 与阶梯。
- `W-3`｜**协议相级只有 `retmax` 一个键有解释器**：`run_chain_arguments` 的 schema 是
  **封闭对象**（`additionalProperties: false`，只声明 `retmax`）⇒ 写错键名（如 `topk`）在
  **加载期**被点名拒绝，不会静默无效。缺口收窄为「想表达别的调用参数时，schema 里没有那个
  键」—— 那是**明确的拒绝**，不是静默失效。
- `W-4`｜**靶子 1 第 2 项曾被实现成「第三份正则」**（收口审计抓到，已修）：`citation_sufficiency.py`
  第一版在导入 `_SENTENCE_SPLIT` 的同一文件里又写了 `_CITATION = re.compile(r"\[(\d+)\]")`，
  而**紧接上一行的注释**写着「这里再写一份会变成第四份，所以直接复用」—— 注释与代码自相矛盾，
  且未登记为残余。修法：删掉定义，`_CITATION` 并入既有导入行。
  **判据补了三层，每层都是被上一层的漏洞逼出来的**：
  ① `pattern ==` 是弱判据（复制品同样相等）；
  ② `is` **也不够** —— `re.compile` 对同一 pattern 有模块级缓存，一份
  `re.compile(_SHARED.pattern)` 造出来的副本与原件是**同一个对象**，实测注入后
  10 条判据**全绿**；
  ③ 因此改判**源码 AST**：本模块里不得出现「对引用语法再做一次编译」
  （`_recompiles_the_grammar()` / 收口验证器的 `_recompiled_grammar_lines()` 同一个口径）。
  按压留证：把 `_CITATION = __import__('re').compile(_SHARED.pattern)` 注入 ⇒
  测试与收口验证器**都**判红并逐字点名那段源码。
  **这条残余本身也说明**：字符串标记式判据（`"_CITATION = re.compile" not in src`）
  会被改名写法绕过 —— 本轮实测过一次（副本注入后全绿）。
- `W-5`｜**`design-outline-guard` 的「只改样式不误报」在 CI 上红过一次**（已修）：
  `openProjects` 只等 `projects-page` 可见，而那个 section 在数据到达**之前**就可见
  （骨架 + `loading-state`）⇒ 「抓 before → 改样式 → 抓 styled」两次快照之间页面可能
  自行完成加载。CI 实测形态：`before` 含 `loading-state`、`styled` 含 `projects-list`
  与 `project-switcher`。修法 = 等 `loading-state` 计数归零（页面稳定的定义），
  **判据与阈值未动**。**如实登记**：本机按压 5 次都没复现（时序窗口比 CI 窄），
  因此归因依据是**日志里的结构差异**，不是本机复现。

## 三、阶梯：收录本 GOAL 的域，以及那些域的「下一级是什么」

| 域 | 下一级是什么（原文） |
| --- | --- |
| 复检 | → 评审者与作者分开：novelty 相的作者角色从 novelty_reviewer 拆成新增的 novelty_author（agent novelty_writer / deepseek-v4-pro-0813）⇒ 角色 id、agent id、(endpoint, model_name) 三者都不同；判据跨 28 份出厂协议遍历「评审者不得评自己写的产物」（此前缺陷与 v2 无关，换协议同样能写出该形状）。这属独立性，不是「评审者是否真的判得对」。 → 改稿与评审点有可判连接（GOAL-20261103-105）：每条 action_taken 必须与它回应的那条 ReviewPoint.text 共享至少一个实词（点表与提示词同一个派生函数）；point 无实词 ⇒ 点名不可比较（空真不算通过）。判的是「不是无关」，不是「解决了那个问题」 判词改写了下一轮的计划/立题（现判到「上一轮的判词在下一轮的会话里可见、可归因、分歧不丢」；「模型据此真的改了立题或计划」仍无判据 —— 与 GOAL-082 EC-04 的未决取舍同源：模型对内容采纳不可判，子串判据会假绿） |
| 报告 | 叙述质量与事实一致性可判（现判到「谁写的 + 数字在哪」两件结构事实；「这段写得好不好」与「叙述与事实是否一致」仍无判据 —— 需人评或把叙述拆成可核对断言） |

- 收录本 GOAL 的域：复检、报告
- 这些「下一级」是本轮的**候选靶子**；做哪一个、做几个，**是判断**，不是提取。
- 若某域的「下一级」为空串 ⇒ 该域已到头（宪章口径），不要凭空造下一格。

## 四、CI 台账结论（机械读数，不是独立取证）

- 结论：**有判红（1 行）**
- 行数：32（全 success 13 / 无 run 0 / 判红 1）
- 最后一条：5ef78e38 ⇒ M0 success（8/8 job success）；Push 全 success（3/3）
- 未识别行：8a31ced6 ⇒ 未跑 CI
- 未识别行：b712a989 ⇒ 该推送的读数见本表 f9883a2e 行；本行不冒领
- 未识别行：9c3a0186 ⇒ 读数见本表 f9883a2e 行；本行不冒领
- 未识别行：73a45692 ⇒ 读数见本表 f9883a2e 行；本行不冒领
- 未识别行：38b92a7b ⇒ 读数见本表 f9883a2e 行；本行不冒领
- 未识别行：cc010ce3 ⇒ 读数见本表 f9883a2e 行；本行不冒领
- 未识别行：a9c845f2 ⇒ 读数见本表 f9883a2e 行；本行不冒领
- 未识别行：33017ab8 ⇒ 读数见本表 f9883a2e 行；本行不冒领
- 未识别行：1803b066 ⇒ 读数见本表 f9883a2e 行；本行不冒领
- 未识别行：15f9fb5b ⇒ 读数见本表 f9883a2e 行；本行不冒领
- 未识别行：be35838a ⇒ 读数见本表 5d48703c 行；本行不冒领
- 未识别行：bfa8b84a ⇒ 读数见本表 5d48703c 行；本行不冒领
- 未识别行：f15f190f ⇒ 读数见本表 5d48703c 行；本行不冒领
- 未识别行：f5610f18 ⇒ 与 87f4eb92 同一次 push（无独立 run），读数见本表 87f4eb92 行；本行不冒领
- 未识别行：3a1073cf ⇒ 与 87f4eb92 同一次 push（无独立 run），读数见本表 87f4eb92 行；本行不冒领
- 未识别行：2ef2b1ef ⇒ 读数见本表 46578970 行；本行不冒领
- 未识别行：4e5428e7 ⇒ 读数见本表 46578970 行；本行不冒领
- 未识别行：82321968 ⇒ 读数见本表 46578970 行；本行不冒领

## 五、下一轮 GOAL 的骨架（可由提取得到的那部分）

```yaml
id: GOAL-20261104-106
status: DRAFT
created_at: 2026-11-04
updated_at: 2026-11-04
objective: <待填：判断>
exit_criteria: <待填：判断（每条自带 verify 与反证臂）>
budget:
  max_cycles: <待填：判断>
  per_cycle_minutes: <待填：判断>
  no_progress_stop_cycles: <待填：判断>
authorization:
  source: user-request
  ref: <待填：本轮授权的原文要点>
latest_recheck: null
```

## 六、不可自动推导的部分（**判断**，本工具不猜）

- `objective`：本轮要达成的**一句话目标**；
- `exit_criteria`：每条可机检（命令 + 期望值），且**自带反证臂**（改事实 ⇒ 判据翻向）；
- 靶子选择：第三节里挑哪一个「下一级」，为什么是它而不是别的（写清依赖与代价）；
- 预算与授权：`max_cycles` / 授权要点 / 是否需要停下登记。
