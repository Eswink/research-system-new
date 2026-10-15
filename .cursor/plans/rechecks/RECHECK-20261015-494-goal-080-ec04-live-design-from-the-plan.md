---
id: RECHECK-20261015-494
slug: goal-080-ec04-live-design-from-the-plan
title: GOAL-080 cycle 4 复检 — 真实模型写出的设计驱动实验（EC-04）
status: COMPLETED
result: PASS
created_at: 2026-10-15
updated_at: 2026-10-16
plan_id: PLAN-20261015-493
parent_goal: GOAL-20261015-080
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261015-494 — GOAL-080 cycle 4

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | **真实 run 跑通且设计由模型写出** | **PASS** | **1 passed in 75.57s**；run `748a56a6-b051-4ad4-a5e0-1eed38fd2d5e` 终态 `SUCCEEDED`、`failures: []`；计划制品正文 **4240 字符**（`message_count=2`），内含模型写的 `experiment_design` 块 |
| AC-2 | **设计的内容决定实验** | **PASS** | 计划声明 `deduped` / `raw` 两臂 ⇒ 读面**恰两条**实验记录，且各自的 `experiment_run_id` = 该臂的确定性派生（逐条比对通过） |
| AC-3 | **参数逐键真的生效**（本 cycle 补强的判据） | **PASS** | `duplicates_expected` **0 vs 12**、`comparison_reduction_ratio` **0.0 vs 595.0**、`n_items` 120/120、`seed` 42/42 —— 每个臂声明的参数都落在**该臂**的落库指标里 |
| AC-4 | **三处产品缺陷已修且都被钉住** | **PASS** | ① 循环控制豁免（逐字白名单 + 不扩散反证）；② `finish` 投影（含顺序断言 + 非 finish 反证）；③ 正文取自文本而非 repr、交付物不套遥测上限 |
| AC-5 | **判据默认门如实 skip** | **PASS** | 无开关时 `1 skipped`，理由逐字（开关未开 / runtime 未配 / 凭据不可解析） |
| AC-6 | **读数归档进树** | **PASS** | `evidence/GOAL-20261015-080-ec04-blocker.txt`（阻塞点取证）与 `…-design-evidence.txt`（达成读数），均 `CR=0` |
| AC-7 | 既有判据零放宽 | **PASS** | 受影响套件 **148 passed, 1 skipped**；新增判据只**加强**（参数生效 / 豁免面逐字 / 顺序） |
| AC-8 | 规模门 | **PASS** | **1258 passed**（含 `test_python_source_limits.py`；本轮新建/改动的文件均 ≤ 450 行且无超 50 行函数） |

## 警告（如实登记）

- **`W-1`**：**本 cycle 为取证共跑四次真实 run** —— 前三次**都失败**且各自暴露一处产品缺陷
  （如实登记在 GOAL 的 cycle 4 修复记录里）；只有末次达成。**不是**「一次就绿」。
- **`W-2`**：**设计质量无人判** —— 判的是「设计来自产物、参数真的生效」；模型选的臂是否
  **科学上合理**没有判据（承 GOAL `W-2`）。
- **`W-3`**：**参数白名单仍只有三个键**（`seed` / `n_items` / `duplicate_pairs`）——
  设计块的表达力受它约束（承 GOAL `W-3`）。
- **`W-4`**：**臂数 > 2 与择优**不在射程（承 GOAL `W-4`）。
- **`W-5`**：本轮 live 的**证据链覆盖**仍由既有输入面满足（模型自陈「session did **not**
  receive the retrieved literature records」——它**如实说了自己没拿到**，这份诚实本身是好读数，
  但「计划站在真检索之上」仍由既有 `research_report_plan` 的覆盖判据在**别处**承担）。
- **`W-6`**：`R-M1` 未收口 ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」。

## 未覆盖的面

- 设计质量 / 臂数 > 2 / 择优（`W-2` / `W-4`）；
- 自举收口（EC-05）。

## 无可复用事实需要另建工程记忆

本 cycle 的三处缺陷**已并进**既有族谱语境（`MEM-20261014-221` 的「声明但从未构造 = 死缝」
与「先在真路径取证再设计判据」）；无须另立条目。

## 结论

**PASS。** EC-04 成立：**真实模型写出的计划产物驱动了该 run 的实验** ——
模型自写 `experiment_design` 块（`deduped` 0 重复 vs `raw` 12 重复），两个臂各在真容器
跑一次，**每个臂声明的参数逐键生效**（`duplicates_expected` 0 vs 12、比值 0.0 vs 595.0），
run `SUCCEEDED`、`failures` 为空。

**本 cycle 最有价值的读数是三处产品缺陷**（循环控制被当能力拒 / `finish` 答复不投影 /
正文取自 repr 且交付物被遥测上限截断）——它们**只在真实 run 上暴露**：受控夹具不跑
真实 SDK agent loop、也不经交付物信封。这正是「live 取证」不可替代的证明。
