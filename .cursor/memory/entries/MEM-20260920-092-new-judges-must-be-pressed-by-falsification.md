---
id: MEM-20260920-092
title: "新写的判据必须先用反证压一遍：本轮两条「绿」的判据其实是「没看」——跨行反引号配对吞掉变量名、宽判「全文出现过」放行清单漏项"
status: ACTIVE
created_at: 2026-09-20
updated_at: 2026-09-20
scope: repository
confidence: 0.92
review_after: 2027-09-20
source_plans:
  - .cursor/plans/tasks/PLAN-20260920-119-live-model-runbook.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260920-119-live-model-runbook.md
supersedes: []
tags:
  - falsification
  - gate-design
  - markdown-parsing
  - runbook
  - honesty
---

# 判据的「绿」可能只是「没看」（GOAL-20260920-008 / cycle 6）

## 做了什么

EC-06 要求一份真实端点 runbook（登记 / 凭据注入与轮换 / 重启边界 / Fake↔真实切换与回退 /
「哪些面仍是 demo」），并且**判据要判同源**而不是判文笔。落地：

- `docs/integration/LIVE_MODEL_RUNBOOK.md`（五节，全部引用真实符号）；
- `docs/INDEX.md` 的 Integrations 清单加条目行；
- `tests/architecture/python/test_runbook_same_source.py`：文档里的仓库路径必须存在
  （运行期产物逐条白名单 + 理由）、全大写变量名必须在代码里出现、pytest 目标必须存在、
  demo 符号必须存在、五个小节缺一判红。

## 为什么这样做（可复用结论）

1. **反证不是「确认判据有效」，而是「确认判据在看」**。本轮 F1/F3/F5 一次就红，
   但 **F2（变量名改错一个字符）与 F4（索引条目被换掉）第一次跑时判据仍然全绿**——
   两条判据都有洞：
   - **跨行反引号配对**：`re.findall(r"`([^`]+)`", 全文)` 会被 Markdown 代码围栏（```）
     打乱配对，文档里明明用反引号写着的变量名根本没进 token 集合；
   - **宽判「全文出现过」**：索引判据只要求 `docs/INDEX.md` 某处提过该路径，
     于是快捷问答里的一句引用就能满足它，**清单漏项反而放行**。
   两条都按缺陷修判据（`affc063`）：token 按**行**抽（行内代码本来就不跨行，围栏行跳过）、
   索引判**条目行**而不是「某处提过」。
2. **解析是判据最脆的地方**：写「扫文档」的判据时，先问「我的解析器在什么输入下会**少看**」。
   对 Markdown 而言，跨行构造（围栏、表格、嵌套引用）就是那类输入。
3. **同源判据判存在性，不判行为一致**：路径存在 / 变量名出现 / 符号存在，都证明不了
   「文档描述的行为与代码行为一致」。行为要靠**行为判据**（如凭据重启边界那条落在
   `tests/api/test_llm_endpoints_api.py`），两者别互相冒充。
4. **白名单要逐条带理由，并检查它仍然被引用**：运行期产物（gitignored、clean checkout 不存在）
   才进白名单；判据同时检查「白名单条目仍出现在文档里」，避免留下死条目让旧例外长期生效。
5. **「清单」类内容是清点结果，不是穷举证明**：demo 清单判据只保证「列出来的符号存在」，
   不保证「存在的 Fake 都被列出来」——这个射程要写在判据里，别让读者以为它是完备性证明。

## 怎么做与复现

```sh
# 同源判据
uv run --frozen --no-sync pytest -q tests/architecture/python/test_runbook_same_source.py

# 反证（先红后复原；脚本把「复原后仍有 diff」当失败）
uv run --frozen --no-sync python -B scratch/ec06-falsification.py

# 文档一致性（会同时抓「文档引用了不存在的文件」）
uv run --frozen --no-sync python -B tools/docs_consistency_check.py
```

## 适用边界

- 适用于**任何新写的静态判据**（扫文档、扫代码、扫配置）：先造一个「应该红」的注入，
  红了再信它。这与「先红后复原」是同一条纪律，区别是**靶子从实现换成了判据自己**。
- 同源判据的射程：只覆盖存在性；行为一致性、完备性、语义正确性都不在射程内（W-1/W-4）。
- 大写字变量名判据是启发式：全大写 + 至少一个下划线才判，单个大写词不判（避免误伤术语）。
- runbook 里的 live 步骤与 HTTP 片段**未实测**（无凭据；请求体形态没实跑校对）——W-5/W-6。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260920-119-live-model-runbook.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260920-119-live-model-runbook.md`（F1–F5、W-1…W-6）
- 代码：`docs/integration/LIVE_MODEL_RUNBOOK.md`、`docs/INDEX.md`、
  `tests/architecture/python/test_runbook_same_source.py`
- 相关：[[MEM-20260920-091]]（结论口径要落成穷举词表；枚举守卫走运行期）、
  [[MEM-20260920-089]]（读面谎言要用措辞判据钉：判「宣称」而不是判「话题」）
