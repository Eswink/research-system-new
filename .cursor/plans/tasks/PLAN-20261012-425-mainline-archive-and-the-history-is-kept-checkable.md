---
id: PLAN-20261012-425
slug: mainline-archive-and-the-history-is-kept-checkable
title: MAINLINE 活跃面归档 — 三段累积物瘦身 + 归档连续性判据（不漏 / 不重 / 可解析）
status: DONE
created_at: 2026-10-12
updated_at: 2026-10-12
parent_goal: null
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261012-426-mainline-archive-and-the-history-is-kept-checkable.md
memory_entries:
  - .cursor/memory/entries/MEM-20261012-217-archiving-is-a-move-not-a-deletion-and-it-needs-a-judge.md
---

# PLAN-20261012-425 — MAINLINE 活跃面归档

## 验收条件

- [x] 区间归档在树且非空（`archive/MAINLINE-2026-10-12-through-26.md`）
- [x] **不漏**：原文 26 条 = 活跃面保留 3 + 归档 23；未覆盖集合 ∅
- [x] **不重**：保留集合 ∩ 归档集合 = ∅
- [x] 搬运保真：归档实质行逐字命中原文（链接基准还原后）
- [x] 链接全部可解析（归档 23/23、宪章 6/6）
- [x] 档案惯例写进宪章抬头并挂判据
- [x] 两条按压在**真文件**上实测红 + 逐字节复原
- [x] 既有宪章判据与新增判据全绿（12 passed）

## 实施清单

1. 侦察：MAINLINE 消费者（52 处均为存在性 / 绑定断言，**无行数断言**）、
   `goals/` 无子目录、`validate.py` 用非递归 glob ⇒ 落点定为 `goals/archive/`。
2. 搬运脚本 `scratch/mainline_archive_carve.py`（二进制读写、原样搬运、
   链接基准 `../rechecks/` → `../../rechecks/`）。
3. 宪章瘦身：三段各留最近 3 条 + 表外指针。
4. 新增判据 `tests/tooling/test_mainline_archive_is_continuous.py`（4 例）。
5. 按压两条（`scratch/mainline_archive_press.py`）。
6. 记录面：本 PLAN + RECHECK + MEM + ALL_PLAN + INDEX。

## 证据

| 面 | 读数 |
| --- | --- |
| 连续性 | 26 = 3（保留最新三条）+ 23（归档）；交集 ∅；未覆盖 ∅ |
| 保真 | 归档 77 行实质内容逐字命中原文，未命中 0 |
| 行尾 | 两文件 CR=0（LF） |
| 链接 | 归档 23/23；宪章 6/6 |
| 判据 | 宪章 8 passed + 归档 4 passed = 12 passed |
| 按压 | P1 `进展记录少了 1 行（…）`；P2 点名 `GOAL-20261012-058`；`FINAL_MATCHES_BASELINE True` |
| 门 | 治理绿 / bundle 绿 / 话术 11 passed / `tests/tooling` 1447 passed |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-12 | IN_PROGRESS | 侦察 + 搬运 + 判据 + 按压；两处判据自伤与一处脚本取错端由按压 / 判据当场抓住并修 |
| 2026-10-12 | DONE | 归档落地、判据全绿、按压逐字节复原、记录面齐备 |

## 影响报告

- **产品代码零改动**；新增 1 判据文件 + 1 归档文件；改 `MAINLINE.md`（瘦身 + 惯例）、
  `ALL_PLAN.md`、`memory/INDEX.md`。
- **无 schema / API / 依赖变化**；无安全面或凭据面变化。
- **兼容性**：宪章小节标题逐字保留（判据按标题匹配）；`goals/archive/` 不在
  `validate.py` 的非递归 glob 面内 ⇒ GOAL 结构判据不受影响。

## 背景与缺口（实测，非推测）

战役跑了序 1…26，`MAINLINE.md` 的**两段只追加累积物**膨胀到 **182 行 / 84 KB**：
进展记录 **26 行**（每行一段长结论）、修订记录 **55 行**（含 **3 大块**预算核算）。
「只追加」保证了历史不被改写，但**没有任何机制**把「较早的历史」从活跃面移出
⇒ 每轮触发都会让活跃面更长，读者的第一屏越来越难看到**当前该做什么**（漂移的载体）。

实测另三条事实（决定落点与判据形态）：

1. `.cursor/plans/goals/` 下**没有**子目录；58 个 GOAL 文件平铺；
2. `validate.py::load_goals` 用 `goals_root.glob("GOAL-*.md")`（**非递归**）
   ⇒ 新建 `goals/archive/` **不会**被 GOAL 结构判据扫到；
3. `closeout_recheck_assertions.py` 同样 `glob("GOAL-*.md")`；`_REQUIRED_SECTIONS`
   与各收口验证器对宪章只做**存在性 / 小节标题 / 绑定**断言（**无行数断言**）
   ⇒ 瘦身不会造成假红。

## 做了什么

1. **新建区间归档** `.cursor/plans/goals/archive/MAINLINE-2026-10-12-through-26.md`
   （112 行 / 58 628 B，CR=0）：收录**移出部分**——进展记录 23 条 + 修订记录早期条目
   + 2 块早期预算核算。**原样搬运**，唯一修正是相对链接基准（`../rechecks/` →
   `../../rechecks/`，落点深了一层；**23 处**）。
2. **宪章瘦身** 182 → **116 行**（27 389 B → 加归档惯例后略增）：三段各保留**最近 3 条**
   + 一段**表外指针**指向归档（表内不放指针：`_bad_recheck_links` 只查最后一格，
   放表内会被判「缺链接行」——实测确认）。
3. **新增判据** `tests/tooling/test_mainline_archive_is_continuous.py`（4 例）：
   归档文件存在且非空 / **不漏**（活跃面 + 归档 ≥ 原文行数，基线取 `git show HEAD:` 版）/
   **不重**（同一条记录不得两处并存）/ 辅助函数非空真。
4. **归档惯例写进宪章抬头**（使得「下一轮触发时执行一次检查」有据可依）。

## 关键实测（逐条，可复核）

| 观察 | 读数 |
| --- | --- |
| 连续性 | 原文 **26** = 活跃面保留 **3**（最新三条：`058` / `057` / `056`）+ 归档 **23**；**零未覆盖、零重复** |
| 保真 | 归档 **77** 行实质内容（数据行 47 + 修订条目 30）逐字命中原文，**零未命中** |
| 行尾 | 两文件均 **CR=0**（LF） |
| 链接 | 归档 23 条链接**全部可解析**；宪章 6 条**全部可解析** |
| 既有判据 | 宪章判据 **8 passed**；新增判据 → 合计 **12 passed** |
| 判据面 | 治理 `validate.py` 绿；`validate_bundle` 绿；话术两道 **11 passed**；`tests/tooling` **1447 passed** |

## 按压（两条，均在**真文件**上，实测红 + 逐字节复原）

| 轮 | 按压 | 红形态 | 复原 |
| --- | --- | --- | --- |
| P1 | 从归档删 1 条进展记录 | `exit=1`，判词逐字：`进展记录少了 1 行（原文 26 / 活跃面保留 3 / 归档 22）` | 复跑 `4 passed` |
| P2 | 把活跃面保留的一条复制进归档 | `exit=1`，判词逐字点名：`与宪章同时收录了同一条进展记录：[('2026-10-12','GOAL-20261012-058')]` | 复跑 `4 passed` |
| — | 两次复原后 | `FINAL_MATCHES_BASELINE True`（raw `sha256` 逐字节一致） | — |

## 判据自身抓到的两处缺陷（如实登记，均为**本轮新判据 / 新脚本**的错）

1. **归档路径重复计数 ⇒ 「不漏」上界虚高**：三段指针各提同一归档文件一次，`_archive_paths`
   返回 3 个同一路径 ⇒ 21 行被算成 63 行 ⇒ **删一行也不会判红**（P1 首跑假绿，按压当场抓住）。
   修法 = 按相对路径**去重**（并在 docstring 写明这是判据正确性的一部分）。
2. **进展行正则要求 id 后紧跟 `|`**：漏判修复 cycle 的既有形态
   （`| 2026-10-09 | GOAL-20261008-040（收口后纪律回溯修复 cycle） | … |`）⇒ 一条真实记录
   被判成「谁也没收录」。修法 = 去掉尾部 `|` 要求。
3. **搬运脚本保留端取错**：表格**最新在前**，脚本却取 `rows[-3:]`（末 3 行 = **最旧** 3 条）
   ⇒ 把 23 条较新的搬走、留下最旧 3 条。**由新判据当场报出**（`GOAL-20261012-058`
   既不在活跃面也不在归档）⇒ 修正为 `rows[:3]` 后重跑。预算核算块同向修正
   （块也是最新在前）。

## 残余与未覆盖（如实登记）

- **`W-1`**：「不漏」用的是**行数上界**而非逐行集合相等（同一天同一 GOAL 可能有多行，
  修复 cycle 就是这种形态）⇒ 它能抓「少搬」与「搬重」，**抓不住「搬错行」**；
  那一面由搬运脚本的 `sha256` 留档承担（引用在本记录）。
- **`W-2`**：58 个 GOAL 文件**仍在活跃面**（`goals/` 平铺）。它们有 3 处外部入链
  与两处 glob 消费者，移动它们的收益（目录更短）小于风险（三个判据 + 三条入链同改）
  ⇒ **本轮不做**，如实登记为未覆盖面。
- **`W-3`**：归档只按「区间」分片，**没有**判据约束「下一片从哪里起」
  （即：两次归档之间的区间是否连续）。本轮只有一片，该面未取证。
- **`W-4`**：`R-M1` 未收口、投递语义**不是**「恰好一次」（口径只能是
  at-least-once + idempotency + deduplication）——本记录**不**作任何安全结论。

## 复核命令

```bash
# 连续性三读数（原文 / 保留 / 归档）
uv run --frozen --no-sync python -B -c "
import importlib.util
spec = importlib.util.spec_from_file_location('j','tests/tooling/test_mainline_archive_is_continuous.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
charter, orig = m._charter_text(), m._original_charter_text()
paths = m._archive_paths(charter)
arch = sum(len(m._progress_keys(p.read_text(encoding='utf-8'))) for p in paths)
print('baseline', len(m._progress_keys(orig)), '| kept', len(m._progress_keys(charter)), '| archived', arch)
"

# 两条按压 + 逐字节复原
uv run --frozen --no-sync python -B scratch/mainline_archive_press.py
```
