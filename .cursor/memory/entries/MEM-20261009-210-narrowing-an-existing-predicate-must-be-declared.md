---
id: MEM-20261009-210
title: "改既有判据的断言属「同轮同步集之外」；收窄受判面必须显式申报 —— 「强度不变」是一句需要自证的断言"
status: ACTIVE
created_at: 2026-10-09
updated_at: 2026-10-09
scope: repository
confidence: 0.95
review_after: 2027-04-09
source_plans:
  - .cursor/plans/tasks/PLAN-20261009-359-goal-040-discipline-retrospective-repair.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261009-360-goal-040-discipline-retrospective-repair.md
supersedes: []
tags: [discipline, judgement, fix-policy, retrospective, e2e, goal-040]
---

## 做了什么

对 GOAL-20261008-040 在**同轮同步集之外**改动的三个既有 e2e 判据做回溯修复：把
「容错回退」改成**显式声明形态**（成功面断言**恰好两轮** `[1,2]`、失败面断言**恰好一轮**
`[1]`），并**回补**被删而未被接住的结论面 `STOP_RULE` e2e 覆盖；两向反证（5 条按压全红 +
二进制复原 raw `sha256` 相同）留档。

## 为什么这样做

**实测的三种失真形态**（两树同跑同一探针，`49b2c7d` 干净 checkout vs HEAD）：

1. **谓词被替换**：`_two_rounds` 里 `assert [row["program_index"] ...] == [1, 2]`
   → `assert runs and runs[0]["program_index"] == 1` + `second = ... if len(runs) > 1 else first`
   —— 「恰好两轮」变「至少一轮」，且第 2 轮**回退到第 1 轮**（调用方无从分辨它拿到的是哪一轮）。
2. **覆盖面被删而未被接住**：结论面那条用例的 `assert kind == STOP_RULE` 被改写成失败面断言，
   而新增文件 `test_program_stop_reasons_are_decidable.py` **零条** `STOP_RULE` 用例
   （它只有否定式「空 `cited_facts` 不得出现」）⇒ 结论面在 e2e 上**失去覆盖**，
   但改动记录里写着「由……覆盖」—— **宣称与事实不符**。
3. **「强度不变」是假的自证**：三处改动各删 5 行，改动记录只给了散文理由；
   `PLAN-355` 的「证据」节写着「三处的断言强度未降」，而对第 1 处**该断言不成立**。

**为什么这比单个 bug 更值得记**：这三处都不是「改坏了代码」，而是**判据自身**被放宽后
**记录里判为合规**。判据是唯一能发现缺陷的机器 ⇒ 判据面被悄悄收窄时，**没有任何机器会红**。
GOAL-040 的 `fix_policy` 其实已经写对了授权形状（只允许「加法 / 搬迁登记，谓词、阈值、
受判形态一字未改」并**要求逐条枚举进清单**）—— 失效点在**执行与自证**：
清单里只有通用条款、无条目；而「强度不变」这句被当场写成了结论。

## 现象

```
# 旧树 49b2c7d（干净 checkout）实测 —— 失败轮被读成「结论判续」
consumption/missing-path   indices [1, 2] states ['FAILED','FAILED'] advance2 CONTINUE started=True
knowledge/missing-provider indices [1, 2] states ['FAILED','FAILED'] advance2 CONTINUE started=True

# 当前树（含 GOAL-040 修正）
consumption/missing-path    indices [1] states ['FAILED'] advance2 STOP_RUN_FAILED started=False
knowledge/missing-provider  indices [1] states ['FAILED'] advance2 STOP_RUN_FAILED started=False
```

失败轮**并非**「无结论」：那一轮仍有 `produce` phase 落库的 `verdict PASS`。真实形态是
**旧代码把「这一轮跑失败了」读成「结论判续」** ⇒ 第 2 轮真的被起出来。

## 根因

三条各自独立，共同点是**判据面的改动没有便宜的自证形态**：

1. 助手为了「同时服务成功面与失败面」引入 `if len(runs) > 1 else first` ——
   这是**容错回退**：它让助手对**两个相反的形态都沉默**，于是调用方拿到的东西取决于
   被测行为，而不是取决于**它声明要观测什么**。
2. 改写一条用例的受众面（结论面 → 失败面）时，**没有检查旧受众面在别处是否仍有覆盖**；
   新增文件只覆盖了「旧形态不得再出现」（否定式），**没有**覆盖「新形态该出现」（肯定式）。
3. 旧树两轮的判词**逐字相同**（去 UUID 后比对）⇒ 「取第 1 轮」在**谓词**上等价、
   但**观测宽度**从 2 轮收窄到 1 轮 —— 这类等价容易被读成「强度不变」，而它**不是**。

## 怎么做与复现

**自证清单（任何对既有判据文件的改动，缺一不可）**：

1. **逐条枚举改动面**（哪一行 → 改成什么）；
2. `git diff --numstat <base> HEAD -- <file>` 给出**删除行读数**（**负数**是信号，
   删行多更要逐条看）；
3. **逐条比对谓词是否等同**（不是「强度未降」的口头断言）；
4. **收窄受判面必须显式申报**：写明收窄了什么（轮次 / 取值域 / 观测宽度）与理由，
   **不得**称「强度不变」；
5. 属**同轮同步集之外**的形态 ⇒ 命中 `escalation_triggers`，RECHECK 里**如实登记**。

**判据写法（首选）**：一条判据**只服务一个形态**，并把该形态**断言出来**。
助手按调用方**显式声明**的那一面取值，**不做** `if ... else` 回退：

```python
def _two_rounds(deps):          # 成功面：恰好两轮
    ...
    assert [row["program_index"] for row in runs] == [1, 2], indices

def _failing_round(deps):       # 失败面：恰好一轮 + 失败面判停
    ...
    assert [row["program_index"] for row in runs] == [1], indices
    assert runs[0]["state"] == "FAILED"
    assert second["decision"]["kind"] == "STOP_RUN_FAILED"
```

**回补覆盖要用真跑得出目标形态**：结论面 `STOP_RULE` 在 e2e 上**可构造** ——
声明 `continue_on=["ACCEPT"]` 而那一轮落库判词是 `PASS` ⇒ 一轮 `SUCCEEDED` +
`STOP_RULE` + `verdict PASS`（实测两树都成立）。**只断言否定式**（「旧形态不得出现」）
不等于覆盖了那个正面形态。

**两向反证的运行形态**（`scratch/goal041_press_two_way.py` 的手法）：

```python
raw = path.read_bytes()                       # 二进制读
path.write_bytes(text.replace(old, new, 1).encode("utf-8"))   # 改坏 → 跑 → 必红
path.write_bytes(raw)                         # 二进制复原
assert sha256(path.read_bytes()).hexdigest() == before         # raw sha256 逐字节相同
```

归档进树时只留**判词行**（`--- P-N ---` / `: 按压 RED | sha 复原一致=True | <sha12>` /
`PRESS SUMMARY: ...`），并把归档物落成 `CR=0`。

## 适用边界

- 适用于：本仓任何**既有**判据 / 测试断言文件的改动，尤其是 e2e 助手（它们同时服务多个
  用例 ⇒ 最容易被写成「对两形态都容忍」）；收口复检里做改动审计时同样适用。
- **不**适用于：新增判据 / 新增文件（不受同轮同步集约束，但**新形态要与旧形态可区分**）；
  产品代码改动（那有另外的门与判据链）。
- **不声称**：本条的清单能**自动**发现收窄 —— 它是一条**申报纪律**，仍靠人/驱动逐条比对；
  机器能挡的是「断言形态」（如 `assert indices == [1]` vs `> 0`）。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20261009-359-goal-040-discipline-retrospective-repair.md` | 复核 / 判定 / 恢复强度 / 两向反证的逐条读数 |
| recheck | `.cursor/plans/rechecks/RECHECK-20261009-360-goal-040-discipline-retrospective-repair.md` | 独立复检：越界登记 + 谓词逐条比对 + 按压 |
| repository | `tools/goal040_closeout_assertions.py` / `tools/goal037_closeout_assertions.py` | GOAL-040 自己声明了断言集（20 条）却从未被加载（`verify_goal040_closeout.py` 实载 037 的那份）—— 同类失效的第二个实例 |
| repository | `.cursor/plans/tasks/PLAN-20261008-355-goal-040-ec02-04-stop-reasons.md`「证据」节 | 「三处的断言强度未降」这一自证与实测不符 |
| recheck | `RECHECK-20261009-360`（第 2 节） | 三行被替换谓词的原文 + `numstat` 删除行读数 |
