---
id: MEM-20260926-146
title: "记录面缺陷是**时刻**不是扫描面：门要在记录写完之后跑，并由判据把「记录面在受判集合内」变成机械事实"
status: ACTIVE
created_at: 2026-09-26
updated_at: 2026-09-26
scope: repository
confidence: 0.9
review_after: 2027-03-26
source_plans:
  - .cursor/plans/tasks/PLAN-20260926-196-record-face-is-covered-by-the-gate.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260926-197-record-face-coverage-recheck.md
supersedes: []
tags: [gate-ordering, record-face, goal-020, ec-02, pressable-criterion, mechanical-guarantee]
---

## 做了什么

把 GOAL-019 遗留的「记录面未被本地门覆盖」从**叙述纪律**改成**机械事实**（GOAL-020 EC-02）。
交付两件东西：

1. **新判据** `tests/architecture/python/test_record_face_is_covered_by_the_gate.py`（215 行 / 8 例），
   它读**符号值**与**行为**，断言记录面在受判集合内；
2. **SOP 条款**（`docs/architecture/LOCAL_GATE_PROTOCOL.md` 的
   `### 记录面覆盖（GOAL-020 EC-02）` 节）写明 canonical 顺序
   **写记录 → 记录面判据 → 全量门**，并被上面那条判据**按小节**绑定（改名即判红）。

## 为什么这样做

**缺陷的真实形状是时刻，不是扫描面**（本条最要紧的更正）。记录面**并非从未被扫**：
`.cursor/plans` 早就在 `test_reproducibility_wording.py` 的 `_SCAN_ROOTS` 里，
`tools/credential_audit.py` 的 `RECORDS_DIR` 也是它。**实测取证**：
往 `.cursor/plans/rechecks/` 临时写一条含禁用形态的记录 ⇒ 该判据**当场判红**
（`test_no_affirmative_fully_reproducible_claim`）⇒ 证明「若记录在门之前就位，门会红」。

⇒ 用户判词给的三选一里，**选项①「全量门包含记录面判据」在字面上已经成立，却不足以修复缺陷**：
门**已经**扫记录面，只是本地 SOP 把门跑在**记录写入之前** ⇒ 那次结论只覆盖**当时还不存在**的
记录内容。修复必须把**结论**与**记录面内容状态**绑定，所以落在 ②/③ 的实质：
一条**可按压**的覆盖判据 + 一条**被判据绑定**的 SOP 顺序条款。

## 怎么做与复现

```bash
# 1) 修前对照：扫描面取证（临时探针 ⇒ 单独判红 ⇒ 复原 ⇒ 绿）
uv run --frozen --no-sync python -B scratch/goal020-ec02-wp-a-red-before.py
# 2) 覆盖判据本身
uv run --frozen --no-sync python -B -m pytest \
  tests/architecture/python/test_record_face_is_covered_by_the_gate.py -q
# 3) 按压矩阵（6 条期望红 + 1 条期望不红；逐字节 sha256 还原）
uv run --frozen --no-sync python -B scratch/goal020-ec02-wp-c-press.py
```

## 判据为什么长这样（三条可复用的形状结论）

1. **「在受判集合内」必须按符号 / 行为取证，不能按文档句子取证。** 本判据读的是
   `_SCAN_ROOTS` 的**符号值**、`_scan_files()` 的**实际产出**、`credential_audit.RECORDS_DIR`、
   治理 `iter_cursor_text_files()` 的**实际产出**、runner 的收集面常量。
   只断「某文档里写了这句话」= 被文档字面量喂饱的恒真判据（承 `MEM` 的判据自身恒真纪律）。
2. **「按小节」而不是「按整篇」判条款履行。** 第一次按压 P6 **没红**——因为判据名在
   文档里出现**两次**（第 1 节的跑法表 + 新节），删一处仍满足整篇子串断言。
   改成**取小节文本**（到下一个 `##` 为止）后判红。**教训**：条款类判据要限定在
   **承载条款的那一节**内，否则"别处提过"会冒充"条款履行"。
3. **按压矩阵要允许声明命中次数。** 按压器默认要求 `old` **唯一命中**（防打偏），
   但「同一名字出现两次、必须全改」是一个**合法**的按压 ⇒ 加 `hits` 参数声明期望次数；
   并且**打偏必须记为失败**（否则按压矩阵会被空转糊过去）。

## 适用边界

- **判据绑的是"记录面在受判集合内"，不是"每次门都跑在记录之后"。** 后者是**人的顺序**，
  判据能保证的是：任何人删扫描根 / 换 walker / 把判据挪出门的收集面 / 让 SOP 条款悬空，
  都会**判红**。顺序本身仍靠 SOP 条款 + 这条判据的绑定来维持。
- **未覆盖面已如实登记**：`.cursor/memory/entries` **不在**话术判据与凭据审计的记录面里
  （它只由治理的 `.cursor/**` 文本扫描与版本 / 链接扫描覆盖）。判据里
  `test_the_recorded_uncovered_ranges_are_still_accurate` **断言这个未覆盖事实**——
  将来若有人补上覆盖，该用例会红并提示更新记录（**登记不是待办，是防夸大**）。
- **`credential_audit` 不扫 `.cursor/memory/entries`** ⇒ 那一片的**凭据形态**今天只有治理侧
  `SECRET_PATTERNS` 覆盖，两边的模式表**不完全同源**（凭据审计的 `assigned-secret` 有意更严）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260926-196-record-face-is-covered-by-the-gate-receipt.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260926-197-record-face-coverage-recheck.md`
- 脚本：`scratch/goal020-ec02-wp-a-red-before.py`（修前对照）、
  `scratch/goal020-ec02-wp-c-press.py`（按压矩阵）
- 相关记忆：`MEM-20260926-145`（本条的**前一条**：记录本身会被判据扫到 ⇒ 门压在记录之前）、
  `MEM-20260926-144`（同源文档要有逐字声明句 / 按压要报实际判红的集合）、
  `MEM-20260925-141`（判据自身恒真）
