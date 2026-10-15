# MAINLINE 归档 — 序 42 的进展记录（原文搬运）

> 依据宪章「归档惯例」：活跃面只保留**最近 3 条**进展记录；本条按原文搬运，
> 唯一改动是链接基准（`../rechecks/` → `../../rechecks/`）。

| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |
| --- | --- | --- | --- | --- |
| 2026-10-13 | GOAL-20261013-074 | 序 42 **质量轴**落地：**标量声明的查询参数重复出现不再被静默折叠** —— 序 37/40/41 接通三面（未知 / 未声明读面 / 写面）后，**同名参数重复**这一形态**从未被量过**：实测 `?limit=1&limit=2` ⇒ **200**（框架静默取末值，无披露）、`?endpoint_id=a&endpoint_id=b` ⇒ 200、序 38 的 `?cursor=a&cursor=b` ⇒ 200。本轮新增**重复臂**：标量重复 ⇒ 422 + 逐个点名 + 明写「只接受一个值」（措辞与「未知参数」分辨）。**射程按声明类型导出**（签名注解判 `list[...]`）：`/evaluations/trend?expected_digests` 是 `list[str]` 且 web 客户端**合法循环追加** ⇒ 一字不动（射程边界有真实用法支撑）。**★ 实测更正**：Starlette 的 `QueryParams.keys()` **去重** ⇒ 计数必须用 `multi_items()`（首版实现即此误）；一次 mypy 真红（`staticmethod` 类型面）同轮修。api 672 / contracts+tooling 2001 / e2e 307 / **live 53** 全绿；快照零 diff；四向按压 W5-1…W5-4 **首跑即全红**；验证器 61 条判词全过；两树判词一致。 | — | [RECHECK-458](../../rechecks/RECHECK-20261013-458-goal-074-ec01-04-duplicated-scalar-query-params-are-not-silently-collapsed.md) |
