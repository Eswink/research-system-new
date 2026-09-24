---
id: RECHECK-20260924-161
plan_id: PLAN-20260924-159
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-24
completed_at: 2026-09-24
reviewer: root-agent-goal-014-ec05 + 独立复检脚本（scratch/verify_goal014_c5.py，两棵树各跑一遍）
baseline_ref: 1d2482f（cycle 4 的推送 tip）
checked_head: 当前树（cycle 5 收口记录）+ 干净 checkout（同一 tip 的分离检出）
---

# RECHECK-20260924-161 — GOAL-014 收口复检 + 残余登记（cycle 5）

## 检查范围

① 独立复检脚本在**当前树**与**干净 checkout** 是否**同判据同结论**；② 本地 m0 终局行；
③ 治理与文档门；④ CI 台账是否到终态；⑤ 13 条人工面 + `W` 列表 + 承继残余是否**逐条登记**；
⑥ 收口文件自洽（`latest_recheck` 为仓库相对路径、引用文件都在同一提交内）。

## 检查结果

### 一、独立复检：两棵树同结论

`scratch/verify_goal014_c5.py`（**只读 / 只用标准库 / 不 import 仓库代码**；
`VERIFY_ROOT` 决定复检哪棵树）在**两处**都给出：

```
VERIFY_ROOT = D:\research-system                        checked=42 failures=0
VERIFY_ROOT = C:\…\Temp\g014final（1d2482f，无 scratch）  checked=42 failures=0
```

判据分组：**A** 策略面（`evidence.read` 的 allow + 镜像表同步 + `default_effect: DENY` 仍在
+ 该能力不在 deny/require_approval/allow_with_constraints）／**B** 真实控制面装配边界
（live 判据挂 `requires_live_llm`；支持模块断言 `preflight_override is None` 且**零**
判词面赋值/关键字实参）／**C** 差集审计（表 35 行、终态三选一、零待定、6 + 29 分侧、
判据 7 例、`OUTSIDE_DIFF` 在册）／**D** 记录自洽（GOAL 引用的文件都在、`ALL_PLAN` 收录、
记忆索引收录）／**E** 越权检查（`allow` 段能力集合恰为已知集合）／**F** 残余在册
（≥13 条编号项 + `R-M1`…`R-F3`）／**G** 判据实跑（EC-01/EC-03 判据 + 镜像一致性判据全绿、
且无判据本身出站）。

### 二、本地 m0 终局行（含一次如实的失败）

- **第一次**（`scratch/goal014-c5-m0.log`）：判红 **1 项 = `framework/validate`**，
  根因是**本 cycle 自己的收口记录当时还没写完**（`PLAN-20260924-159` 缺「证据 / 影响报告」
  两节、未进 `ALL_PLAN`）。**不是**产品缺陷，**不是**门禁被改动 —— 是收口流程本身的顺序问题。
- **补齐记录后重跑**（`scratch/goal014-c5-m0-final.log`）：终局行**逐字**
  `PASS: profile=m0; 23 deterministic checks`（未截断；`PASS [` 行 **24** 条 =
  23 项受检 + `release-assets-immutable` 在计数之外，与既有口径一致）；
  `python/tests` = **4429 passed / 19 skipped / 0 failed**（与 cycle 3 同值 —— 本 cycle
  没加删用例）。

### 三、`R-F3` 的代管与还原（口径必须写清）

本机 m0 的 `framework/validate_bundle` 会被**仓库外并发写者**的 gitignored
`scratch/self-governance-bootstrap-prompt.md`（**不是**本 GOAL 的产物）判红
（正文里的路径正则被纯文本链接扫描读成本地链接）。按 GOAL-013 的既有口径：

1. 记录 `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2`、
   `size 69944`、`mtime 1790187424.185179`（落 `scratch/g014-c5-quarantine-record.json`）；
2. **代管**到仓库外（`…\Temp\g014-quarantine\`）—— 移出后 `validate_bundle` **exit 0**
   （`scratch/g014-c5-bundle-check.log`）；
3. 跑完整 m0 拿终局行；4. **还原**并逐字节复核：还原后 `sha256` 与 `size` 与代管前**一致**、
   `mtime` 差 < 0.01s（代管目录已删）。

**不得**把「代管后 23/23」读成「本机一直 23/23」；**as-is 的本机 m0 仍是 22/23 形态**
（判红项恒为 `framework/validate_bundle`）。CI 检出无 `scratch/` ⇒ CI 侧不受影响
（cycle 3 / cycle 4 的六 job 全绿即为证）。

### 四、治理与文档门

`validate.py` ⇒ `Cursor 治理验证通过`；`docs_consistency_check.py` ⇒
`DOCS-CHECK PASS: 6 deterministic checks`。

### 五、CI 台账到终态（逐 run 逐 job 实查）

| 推送 | 提交 | M0 | CodeQL |
| --- | --- | --- | --- |
| cycle 3（EC-03） | `bf3ecdc` | [35969958027](https://github.com/Eswink/research-system-new/actions/runs/35969958027) **六 job 全 success** | [35969957120](https://github.com/Eswink/research-system-new/actions/runs/35969957120) **3/3 success** |
| cycle 4（EC-04） | `1d2482f` | [35972496231](https://github.com/Eswink/research-system-new/actions/runs/35972496231) **六 job 全 success** | [35972494660](https://github.com/Eswink/research-system-new/actions/runs/35972494660) **3/3 success** |

（本 GOAL 更早各 cycle 的台账行走 GOAL-014 的 CI 台账表；每个 tip 都到终态、**无未记账 run**。）

### 六、残余逐条登记（本 GOAL 的收口清单）

**EC 终态**：`EC-01 = PASS`、`EC-02 = BLOCKED`、`EC-03 = PASS`、`EC-04 = PASS`、`EC-05 = PASS`。

**13 条人工面（原样保留，按事实标注）**：ADR-0031（Proposed，待拍板）／威胁建模·BOLA-BFLA
（待拍板）／`artifacts/` token 清理（**已完成**，无待办）／450 行纪律的贴线文件（待拍板，
本 GOAL EC-04 只分类：3 个正好 450、10 个 400–449、70 个过软阈值）／依赖 pin 升级
（待拍板；含 `R-D1` 的 23 条告警）／hook 侧 L3 门（待拍板；根因 = `semgrep` 检测层未安装，
本 cycle 现场复现失败开放）／真实 runtime 默认化（**禁止**，默认必须 Fake）／
为 anthropic 形态引入新依赖（需拍板）／把凭据写进 CI（**明文禁止**）／
`ModelCompatibilityProfile` 一等域实体（待拍板）／放宽 `AcceptanceCriteria`（**明文禁止**）／
`secrets/llm_key.txt`（**已完成**，无待办）／30 条非 ASCII 路径（**已登记豁免**，AGENTS §13）。

**`W` 列表**：`W-A`（真实控制面对 `sort_analysis_v1` 的 `evidence.read` 判 `DENY`）与
`W-C`（同协议两套装配结论漂移）—— **本 GOAL 已消灭**（EC-01 PASS：`FAIL` → `WARN`、
策略维度清零、`SAME_STATUS = False → True`、两套装配都可冻结）。

**承继残余**：`R-M1`（Mimosa 钩子侧未得完整结论 ⇒ **不得**宣称项目安全，本 GOAL 未改）／
`R-D1`（23 条告警，EC-04 已分类，**未升级**）／`R-B1`（路径 (B) 已否证，5 条重设计项待拍板）／
`R-N1`（30 条非 ASCII 路径，按 §13 豁免）／`R-F1`（主观面必须先操作化 —— 本 GOAL 的落实 =
EC-01 的「同一判据脚本同求两套装配」）／`R-F2`（真实调用规模不足时如实标注 —— 落实 =
EC-02 的失败形态如实记录）／`R-F3`（并发写者的 gitignored 文件致 as-is 本地 m0 停在
22/23 形态，**本 cycle 代管后拿到 23/23，还原后环境形态不变**）。

**本 GOAL 新登记的拍板项**：
1. **`F-11`（决定性）**：`EvaluationInputs` 缺 `tests` / `policy_decision` 两维 ⇒ 带真实实验的
   run 在产品路径上到不了 `SUCCEEDED`；这正是 GOAL-011 登记的 ①②③。
2. **`F-10`**：出厂组合根是否自己接执行体缝（`tool_providers` / `capabilities` /
   `experiment_task`）。
3. **读类能力是否成类预放行**（EC-03 的 15 条「该登记」）：(a) 成类 / (b) 维持逐条 / (c) 不动。
4. **三项残余的处置**（EC-04）：告警升 pin / L3 检测层安装 / 450 行拆分。

### 七、收口文件自洽

`latest_recheck` = `.cursor/plans/rechecks/RECHECK-20260924-161-goal-014-closeout-recheck.md`
（**仓库相对路径**）；`child_plans` 收录 5 份子 PLAN（155/156/157/158/159）；
`memory_entries` 收录 4 条（MEM-124 / 125 / 126 / 127）；
复检脚本引用到的文件**都在同一提交内**。

## 判据性质披露（必须读的一段）

- **本 GOAL 不是 `ACHIEVED`**：建档时写死「EC-01…EC-05 **全部 PASS**」才是 `ACHIEVED`，
  而 **EC-02 = `BLOCKED`**（判据本体待用户拍板）。本 RECHECK 的 `PASS_WITH_WARNINGS`
  是**收口复检本身**的结论（六项收口条件都达成且可复核），**不是**「目标已达成」。
- **本机 m0 的 23/23 是「代管并发写者文件后」的结论**（第三节）；**as-is 的本机 m0 仍是
  22/23 形态**。CI 侧不受该残余影响。
- 干净 checkout 只用于复检（同一 tip 的分离检出），**不是**发布物，跑完已移除。

## 结论

**`PASS_WITH_WARNINGS`** —— ① 独立复检两树同结论（`checked=42 failures=0` ×2）；
② m0 终局行逐字 `PASS: profile=m0; 23 deterministic checks`（含一次如实登记的失败与根因）；
③ 治理与文档门全绿；④ CI 台账到终态、无未记账 run；⑤ 残余逐条登记（13 条人工面 +
`W` 列表 + 承继残余 + 4 项新拍板项）；⑥ 收口文件自洽。
**WARN**：`EC-02 = BLOCKED` ⇒ **GOAL 收口状态 = `BLOCKED`**（留人工决策，清单见第六节）。

## 仍未处理项

- 第六节的 4 项新拍板项（`F-11` / `F-10` / 读类口径 / 三项残余处置）。
- 13 条人工面中的 9 条待拍板项（ADR-0031 / 威胁建模 / 450 行 / 依赖 pin / L3 门 /
  真实 runtime 默认化 / 新依赖 / `ModelCompatibilityProfile` / 放宽验收门）。
- `R-M1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` / `R-F3` 原样保留。
