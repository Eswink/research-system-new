---
id: MEM-20261112-242
title: "全量 m0 的见证只覆盖**已跟踪**文件：新建的受判文件必须先 `git add` 再跑 m0"
status: ACTIVE
created_at: 2026-11-12
updated_at: 2026-11-12
scope: repository
confidence: 0.97
review_after: 2027-05-12
source_plans:
  - .cursor/plans/tasks/PLAN-20261112-112-authored-enablement.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261112-112-authored-enablement.md
supersedes: []
tags: [witness, m0, git, evidence, closeout, rule-8-1]
---

# 见证只覆盖已跟踪文件

## 做了什么

序 80 的第三个 CI 轮：新建了 EC-06 点名的程序完成报告
`docs/roadmap/ROUNDS_76_80_PROGRAMME_COMPLETION.md`，本地跑全量 m0 得
`PASS: profile=m0; 23 deterministic checks`（24 条 `PASS [`、0 FAILED、
`tree changed during the run: False`），提交推送后 CI 的 `quality-ubuntu-latest` 与
`quality-windows-latest` 仍然红，**唯一判负是** `test_m0_witness_matches_the_tree`。

## 为什么这样做

`tools/run_m0_with_witness.py` 的 `tree_fingerprint()` 用
`git ls-files` 取**受判面文件清单**，再用 `git hash-object` 逐份取**归一化 blob 哈希**
（这条口径本身是对的：与平台行尾、与工作树是否干净无关）。

`git ls-files` 只列**已跟踪**文件 ⇒ 新建但未 `git add` 的文件**不在清单里**，
于是：

- 本地：见证与"当前树"都不含它 ⇒ 判据绿；
- CI：那笔提交把它变成 tracked ⇒ 见证少一条 ⇒ **判红**，判词逐字给出
  「内容变了/新增（1 项）：[('docs/roadmap/…', '<blob>')]」。

**已经跟踪、只被修改**的文件不受影响：`hash-object` 读的是**工作树内容**，
所以「记录改了但没 `git add`」在见证里是**被看见**的。缺口只在**新文件**。

## 怎么做与复现

1. 写完全部记录（含**新建**文件）；
2. **`git add` 全部受判文件**——重点是新建文件，否则它不进 `git ls-files`；
3. 再跑 `uv run --frozen --no-sync python -B tools/run_m0_with_witness.py`；
4. 判终态行 + 24 条 `PASS [` + `tree changed during the run: False`；
5. 之后不再改树，提交（见证文件本身在 `SELF_REFERENTIAL` 里，不参与描述）。

**取证命令**（本地即可复现这条缺口）：

```bash
# 见证里的受判面清单里有几个文件；新建文件若不在其中 ⇒ 那一次 m0 没覆盖它
uv run --frozen --no-sync python -B -c "
import json,pathlib
d=json.loads(pathlib.Path('.cursor/plans/goals/evidence/M0-WITNESS.json').read_text(encoding='utf-8'))
paths={item['path'] for item in d['fingerprint_after']['files']}
print('docs/roadmap/ROUNDS_76_80_PROGRAMME_COMPLETION.md' in paths)
"
```

**按压方式**：拿任意一个新建且未 `git add` 的受判面文件跑一次见证入口，
`files` 清单里必然没有它；`git add` 之后同一命令为 `True`。

## 适用边界

- 只对**见证入口**（`tools/run_m0_with_witness.py`）成立：其他门不看这份清单。
- 与 `SELF_REFERENTIAL` 无关：那是**见证文件自己**不参与描述，这里是**未跟踪文件**
  压根不在清单里——两种「不在」的成因不同，判词也不同（前者静默、后者在 CI 上判红）。
- 该缺口的**信号形态是"本地全绿 / CI 单条红"**：若 CI 红的那一条正是见证，
  先查「这次有没有新建受判文件而没 add」，再怀疑产品缺陷。

## 失效与复核触发器

- 见证入口改为「工作树扫描」（如 `git ls-files --others --exclude-standard` 也纳入）
  ⇒ 本条失效，需重判。
- `WATCHED_PREFIXES` 变更 ⇒ 复核本条的前提（受判面范围变了）。
- 复核日期到达（2027-05-12）或 `.cursor` 记录顺序纪律（8.1）被改写。

## 来源

- `.cursor/plans/goals/GOAL-20261111-112-experiment-generation-enablement-surface.md`
  的 `## CI 台账`（`ab97a4b9` 那一行）+ `## 迭代日志` 第 3 行。
- CI run [43228489710](https://github.com/Eswink/research-system-new/actions/runs/43228489710)
  的 `quality-ubuntu-latest` 日志（唯一判负 + 逐文件点名）。
- `tools/run_m0_with_witness.py` 的 `tree_fingerprint` / `SELF_REFERENTIAL` / `_watched`。

## 相关

- `MEM-20261112-241`（换站轮的两条：`verify:` 点名文件可能不存在；门判可解析不判有效）
- `MEM-20261020-090` 一族（见证口径的三次定稿：脏清单 → 工作树 sha → `hash-object`）
