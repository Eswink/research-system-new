---
id: MEM-20260926-144
title: "同源文档要有「一条逐字重复的声明句」；零夸大判据必须自带一个受判的豁免；按压要报「实际判红的集合」"
status: ACTIVE
created_at: 2026-09-26
updated_at: 2026-09-26
scope: repository
confidence: 0.9
review_after: 2027-03-26
source_plans:
  - .cursor/plans/tasks/PLAN-20260926-192-auth-surface-four-doc-same-source.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260926-193-auth-surface-four-doc-same-source-recheck.md
supersedes: []
tags: [documentation-same-source, gate-design, press-test, ast-criterion, allow-list, zero-overclaim, goal-019, ec-04]
---

## 做了什么

把「写面已认证 / 读面未认证 / 多租户与 RBAC 未实现」这一实况**同源**地登记进四处文档
（身份总纲 / 威胁模型 §6 / 接口草图 / live runbook），并新增一条 **11 例**的结构判据
`tests/architecture/python/test_control_plane_auth_same_source.py`（437 行），
再以 **14 条按压**逐条验证它非恒真（13 条按预期判红、1 条"引述禁令不判红"）。

## 为什么这样做

1. **「同源」要落成「一条逐字重复的声明句」，而不是「四处都提过这件事」。**
   后者只能靠人读；前者是**子串计数**，可机械判、可按压（改一处即红）。
   代价是同一句有 5 份副本（四份文档 + 判据常量）——**这个摩擦是有意的**。
2. **"零夸大"不能用"要求面"表达，要用"禁止面"表达，而且禁止面必须配一个受判的豁免。**
   只要求"写了未覆盖范围"⇒ 判据会被文档自己的措辞喂饱（承 `MEM-20260925-141`）。
   但纯禁止面会**误伤引述禁令的句子**：本仓威胁模型里就写着
   「**不得**据此宣称『项目安全』或『授权面已覆盖』」——那是**写作纪律**，不是宣示。
   ⇒ 规则定为"短语**所在句**含否定标记则豁免"，并把豁免**自身**做成断言：
   `_overclaims("本节声称：授权面已覆盖。") == ["授权面已覆盖"]` 与
   `_overclaims("不得…简写成「授权面已覆盖」") == []` 同时成立。**豁免不受判 ⇒ 禁止面必假**。
3. **按压要报「实际判红的**集合**」，不能只报「红没红」。**
   本轮 P5（插入 `已实现 RBAC`）首版把替换文本里的「零夸大」三个字**顺手删掉了**，
   而那是**另一条**判据（AC-2）的必需措辞 ⇒ 一次按压打红两组。
   只看"红了"会把它当成通过；比对集合才看出**按压的替换文本改了别的判据的输入面**。
4. **判据里的 AST 假设必须先探针后写。** 首版四处自红全是"我以为的形状"：
   `frozenset({…})` 是 `ast.Call`（不是 `Set`，`literal_eval` 直接抛）、
   `os.environ` 是 `Attribute`（用属性名**集合相等**判恒不成立）、
   f-string 里的变量名是 `FormattedValue`（不是字面量常量，`.join` 常量拿不到）、
   `async def dispatch` 是 `AsyncFunctionDef`（不是 `FunctionDef`）。
5. **450 行 / 50 行函数门是"顺手多写一行"就会撞上的门。** 新判据首版 **451 行**（越 1 行）被判红。
   可用的压缩手法：逐行 `{"GET", …}` 集合改成 `frozenset("GET …".split())`（8 行→1 行）；
   短元组条目合并成一行（注意 ruff 的 line-length 按**显示宽度**算，CJK 计 2 ⇒ 长条目仍会被展开）。
6. **"期望不红的按压"是**有价值**的证据，但必须标注。** 它证明豁免是**有意的**、不是漏网；
   不标注则会被读成"14/14 条都判红"（RECHECK 里显式写成 W-5 就是为了防这一读）。

## 怎么做与复现

```bash
# 1) 同源句四处各一次（改一处即红）
python -c "import pathlib; s='**认证覆盖**：…'; [print(pathlib.Path(p).read_text(encoding='utf-8').count(s), p) for p in ('docs/security/IDENTITY_AND_ACCESS.md','docs/security/THREAT_MODEL.md','docs/api/CONTROL_PLANE_API.md','docs/integration/LIVE_MODEL_RUNBOOK.md')]"
# 2) 判据
uv run --frozen --no-sync python -B -m pytest tests/architecture/python/test_control_plane_auth_same_source.py -q
# 3) 14 条按压（每条：唯一命中 → 判红 → sha256 逐字节还原）
uv run --frozen --no-sync python -B scratch/goal019-ec04-press.py
# 4) 规模门禁（450 行 / 50 行函数）
uv run --frozen --no-sync python -B -m pytest tests/tooling/test_python_source_limits.py -q
```

## 适用边界

- **禁止面词表是**下限**不是上限**（21 条，只增不减）：未列入的新措辞不会被抓。
  新增一遍辞就要连带加条目 + 加一条按压。
- **文档集合是写死的四元组**：将来新增第五份"对外语义"文档，判据**不会**自动覆盖它。
- **AC-2 的观察窗有界（锚点后 1200 字）**：在锚点后插入大段合法内容可能把必需措辞挤出窗口
  ⇒ **假红**（可调整窗口，但**不得**改成全文搜索——那会让"这一节声明了"退化成"文档里提过"）。
- **本次只覆盖写面认证的文档口径**：部署面（反代 / TLS / 多副本）**仍未验证**，
  文档里如实写了"未验证"，但**没有**实测面。
- 新判据 **437/450 行**（余量 13 行）；再扩就要先压缩，**不得**抬阈值。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260926-192-auth-surface-four-doc-same-source.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260926-193-auth-surface-four-doc-same-source-recheck.md`
- 按压脚本与日志：`scratch/goal019-ec04-press.py` / `scratch/goal019-ec04-press.out`
- 相关记忆：`MEM-20260925-141`（一个开关一个读取点 / 判据自身恒真）、
  `MEM-20260926-142`（按压必须落在判据自己的块内）、
  `MEM-20260926-143`（认证面复用唯一的分类）
