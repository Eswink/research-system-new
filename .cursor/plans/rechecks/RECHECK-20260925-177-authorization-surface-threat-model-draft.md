---
id: RECHECK-20260925-177
plan_id: PLAN-20260925-176
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-25
completed_at: 2026-09-25
reviewer: root-agent-goal-016-cycle5 + 只读勘察子代理（授权面事实清单，55 次只读工具调用）
baseline_ref: cycle 4 推送 tip `d67f324`
checked_head: 当前树（2 个 docs 文件；**无代码 / 门禁 / 判据改动**）
---

# RECHECK-20260925-177 — D-12(b) 授权面威胁模型草案（GOAL-016 cycle 5）

## 检查范围

① 结构（「未覆盖范围」/ BOLA / BFLA / M18）（AC-1）；② 纯增量（删除数 0）（AC-2）；
③ diff 只含 docs（AC-3）；④ 事实可复核（AC-4）；⑤ 口径不越界（AC-5）；⑥ 门与记录（AC-6）；
⑦ 并发写者文件未被卷入。

## 检查结果

### 一、AC-1｜结构齐备

- `docs/security/THREAT_MODEL.md`（106 行 → **252 行**）新增 `## 6. 授权面威胁建模
  （BOLA / BFLA）—— 文档级草案`，含：
  - `### 6.1 术语`（BOLA / BFLA 的定义）；
  - `### 6.2 覆盖了什么（本节实际论证到的范围）`（7 条实况，每条带出处）；
  - **`### 6.3 未覆盖范围（明确不覆盖什么）`**（8 条，`:166` 起）；
  - **`### 6.4 与 M18 边界的关系`**（`:194` 起）；
  - `### 6.5 若取 (a)：范围与代价`；
  - `### 6.6 引用约束（写作纪律）`。
- `BOLA` / `BFLA` 字样命中 **6** 处；`M18` 在关系节内多处命中。

### 二、AC-2｜纯增量（既有内容一字未删）

- `git diff --numstat docs/security/THREAT_MODEL.md`
  ⇒ **`146  0  docs/security/THREAT_MODEL.md`**（**146 增 / 0 删**）。
- ⇒ 第 1–5 节（保护资产 / 信任边界 / 威胁与控制 / Data Classification /
  Security Invariants，共 106 行）**原样在位**。

### 三、AC-3｜diff 只含 docs

本 cycle 的改动集**恰好**两项：

| 文件 | 性质 |
| --- | --- |
| `docs/security/THREAT_MODEL.md` | 增第 6 节（纯增量） |
| `docs/INDEX.md` | Security 节该行加注 |

**不含**：任何 `.py` / `.ts` / `.tsx` / `.yaml` / `.json`、任何门禁脚本、任何测试、
任何阈值、任何 `allow`、`FRAMEWORK_MANIFEST.json`。
（AC-3 的取证方式：`git status --porcelain` 逐条核对改动集；三个并发写者文件不在内。）

### 四、AC-4｜事实可复核（逐条抽查）

子代理以**只读**方式勘察了授权面（55 次工具调用、零写操作），本节事实均带出处。
抽查到的关键事实与其出处：

- **124 条路由、逐条零授权依赖**：`create_app()` 在 `services/api/app.py:261`；
  全仓 `Depends(` / `Security(` / `currentUser` / `HTTPBearer` / `APIKeyHeader` **零命中**。
- **控制面无调用方认证**：唯一请求级强制项是 `Idempotency-Key`
  （`services/api/middleware.py:40`），是幂等而非身份。
- **策略是能力级不是对象级**：`packages/domain/policy.py:29`（`matches` 只比
  capability / action / scope）；`packages/application/policy/native.py:17`、`:47`
  （不读 `actor` / `resource` / `context`，未命中落 `default_effect`）；
  `examples/config/policy.yaml:2` = `default_effect: DENY`。
- **无归属概念**：`packages/domain/run.py:37`（`ResearchRun` 无 owner）；
  `packages/domain/projects.py:5`（明说不是租户边界）；
  `packages/domain/artifacts.py:90`（`created_by` 仅溯源）。
- **M18 = DEFERRED**：`docs/roadmap/MILESTONES.md:971`（定义）、
  `:973`（「不标记部分完成」）、`:980`（触发条件）；
  `docs/adr/ADR-0028-personal-scale-rebaseline.md:44`。
- **唯一有认证的面是 worker 网关**：`services/api/worker_gateway/auth.py:21`、`:58`。

### 五、AC-5｜口径不越界

- 6.6 明写两条约束：① 事实以当前树为准、行号会漂移（复核以**符号名**为准）；
  ② **不得**引作「已做威胁建模」「授权面已覆盖」或任何安全结论，
  唯一可引用口径是「实况与空白已登记在第 6 节（D-12(b) 草案）」。
- 6.3 第 8 条把「依赖告警未清」与「授权面缺口」**显式并列且互不顶替**
  （`R-D1` 与本节是**两个不同**的缺口）。
- 6.5 明写 (a) 的前置是**主体模型**，且「没有第二个主体可测」——
  **未**把 (a) 缩权或改判。

### 六、AC-6｜门与记录

- **doc 一致性门**：`DOCS-CHECK PASS: 6 deterministic checks`（首跑即过；
  反引号引用全部可解析——`file:line` 形态含 `:` 被门禁跳过，纯路径均为真实对象）。
- **治理门**：`validate.py` ⇒ `Cursor 治理验证通过`。
- **m0**：见「附：m0 终态行」。
- 本 PLAN / 本 RECHECK / `MEM-20260925-138` 与 GOAL-016 的回写同轮完成。

### 七、并发写者文件未被卷入

- 工作树里三处**他人**的未提交条目（`apps/web/src/features/models/ModelDetails.tsx`、
  `packages/domain/model_drift.py`、`services/api/dto/models.py`）**不在**本 cycle 的改动集里
  ⇒ **未**被 `git add`、**未**被提交。

## 附：m0 终态行

- **代管后的树**（`R-3` 的文件 `scratch/self-governance-bootstrap-prompt.md` 临时移出）：
  **`PASS: profile=m0; 23 deterministic checks`**（退出码 **0**，**首次即通过**；
  `PASS [` = **24** 行 = 23 项 + 计数外的 `release-assets-immutable`；`FAIL` 行数 = **0**）。
  逐字节复核**一致**：`size=69944` / `mtime_ns=1790187424185178900` /
  `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2`。
  日志：`scratch/goal016-c5-m0-quarantined.log`；
  轮次输出：`scratch/goal016-c5-m0-quarantine-run.txt`。
- **as-is 的树**：唯一预置红 = `framework/validate_bundle`（`R-3`），与本 cycle 改动无关。
- **口径**：代管后的终态行**不得**读成「as-is 本机全绿」。
- **记录时序声明**：本轮 m0 在**冻结树**上跑，且已包含本 cycle 的全部产物
  （2 个 docs 文件 + PLAN / RECHECK / MEM / `ALL_PLAN` / `INDEX` / GOAL-016 的 EC-05 段）；
  该跑之后的写入**只有**记录面（台账回填），**不改**判据 / 产品代码 / 门禁 / 文档正文。

## 结论

- **AC-1…AC-6 全部成立** ⇒ **GOAL-016 EC-05 = PASS**。
- **PASS_WITH_WARNINGS 的五条警告**：
  - **W-1｜本节不是安全性，只是可见性**：它**没有**提高任何访问控制强度。
    控制面「无认证、无逐路由授权、无对象级归属」的**事实仍在**，
    △ 交付物只让这个事实变成**可引用**的。**不得**读成「授权面已处理」。
  - **W-2｜本节会过期且不会自己红**：(b) 的固有代价——树变了它不报警。
    要「防漂移」必须先有 (a) 的判据，而 (a) 的前置是**主体模型**（M18 或等价授权）。
  - **W-3｜(a) 的最小形态也可能立刻全红**：若把「每条路由必须有授权状态」写成判据，
    今天 124 条路由**全部**不合规 ⇒ 只能写成「现状白名单快照」（只防漂移、不提供安全），
    而白名单**本身就是待还的债**。这一点已写进 6.5，但**没有**被解决。
  - **W-4｜`FRAMEWORK_MANIFEST.json` 该条快照未刷新**：该文件是发布快照
    （`docs/operations/REPOSITORY_HYGIENE.md:21`），刷新属**发布动作**；
    本 cycle 若刷新会带进非 docs 文件（违反 AC-3）。实测该快照**本就已过期**
    （220 条中 **131** 条 hash 与现树不符）⇒ 非本 cycle 引入。
  - **W-5｜`R-3` / `R-M1` / `R-D1` 原样保留**：as-is 本机 m0 的预置红、
    hook 面安全结论、依赖告警未清部分，三者均**不在**本 EC 范围，**未**被本 EC 收口。
- **未改动**：产品代码、策略面（`policy.yaml` / `_CAPABILITY_SCOPE`）、门禁、阈值、判据、
  测试、运行时默认值、依赖。
