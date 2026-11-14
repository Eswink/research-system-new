# MAINLINE 进展记录归档 —— 序 78（GOAL-20261111-110）

（自 `MAINLINE.md` 的 `## 进展记录` **原样搬入**；唯一允许的改动是相对链接基准修正：`../rechecks/` → `../../rechecks/`。活跃面保留**最近三条**。）

| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |
| --- | --- | --- | --- | --- |
| 2026-11-12 | GOAL-20261111-110 | **证据矛盾的处置闭环（仲裁策略闭集 + HTTP 路由）**。检测面**不重做**（三种可判形态 / 存量清扫 / 五态处置 / `ConflictResolution` 已在树）；本轮补「谁、依据什么消解」：`memory/arbitration.py` 的三值闭集（`NEWER_WINS` 依据两时间戳、`SOURCE_TRUST_WINS` 依据 `TrustLabel` 读序、`REQUIRE_HUMAN` 显式拒绝），**缺省即 `REQUIRE_HUMAN`**（自动化只能显式声明 + 必须带阈值；`REQUIRE_HUMAN` 不是可声明的策略）；路由 `POST /memory/{id}/conflicts/{other_id}/resolve` 带幂等键，落账走**既有** lifecycle 用例。判据三正例（三策略）+ 两反证（低于阈值拒自动 / 同一对重复消解点名）+ 幂等两向；阶梯只改「证据」一格，**其余六格逐字未动**。 | 复检 | [RECHECK-20261112-110](../../rechecks/RECHECK-20261112-110-conflict-arbitration.md) |
