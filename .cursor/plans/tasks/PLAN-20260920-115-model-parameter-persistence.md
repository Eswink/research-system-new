---
id: PLAN-20260920-115
slug: model-parameter-persistence
title: 模型参数落库：上下文窗口与思考强度的承载字段 / 契约 / 往返 / 读面 / 快照（EC-02）
status: IN_PROGRESS
created_at: 2026-09-20
updated_at: 2026-09-20
parent_goal: GOAL-20260920-008
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260920-008 cycle 2 = EC-02（模型参数落库）。授权来源：2026-09-20 用户 goal 模式指令（建档 GOAL-008 并自动化循环推进、无需逐轮确认）；模型参数口径（上下文窗口 512000、思考强度 Max）与「如实记录或如实登记为不支持」的要求见 GOAL-20260920-008 frontmatter `authorization.ref` 第 (2) 条。本 PLAN 遵守：厂商中立命名、不引入新依赖、**不新建 PG canonical 表**（那触及 Canonical State 边界 ⇒ escalation）、默认门保持离线。"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260920-115 — 模型参数落库（GOAL-008 cycle 2 = EC-02）

## 目标

把用户声明的两个模型参数——**上下文窗口 512000 tokens**、**思考强度 Max**——从
「只在对话里说过」变成**域里有承载字段、契约里有声明、配置面能往返、读面能看见**的事实：

1. **承载字段**：`ModelDefinition` 增两个可选字段（**厂商中立命名**，AGENTS.md §1）；
2. **契约**：`schemas/model-definition.schema.json` 声明它们（该 schema 是
   `additionalProperties: false` ⇒ 不声明就写不进去，这本身是判据）；
3. **往返**：YAML 契约加载器与 SQLite 配置存储都能写能读，**旧行缺键时解码向后兼容**；
4. **读面**：API DTO/响应可见（含 OpenAPI 快照同步）**且页面有渲染分支**；
5. **不静默丢弃**：**缺字段 ⇒ 用例红**，且「运行期尚未把这两个值发给任何 provider」
   这一事实**必须在读面/文档如实登记**（用户授权 (2) 明确允许"如实登记为不支持"）。

## 先探明再动手（建档时只读勘察已确认的事实）

1. **`ModelDefinition` 现在只有 6 个字段**：`id` / `endpoint_id` / `model_name` /
   `display_name` / `enabled` / `capabilities`（`packages/domain/models.py:82-97`），
   **没有任何字段承载上下文窗口或思考强度**（全仓 `reasoning_effort` / `reasoning_level` /
   `thinking_budget` **零命中**；`context_window` 只存在于前端 mock 与设计参考稿；
   `max_context_tokens` 只存在于 **agent 侧** `AgentContextConfig`）。
2. **配置面是 SQLite JSON blob 的键值行**：`models(model_id, model_json, created_at)`
   （`adapters/sqlite/model_store.py:22-28`，`_encode` `:90-106`、`_decode` `:109-126`）；
   **没有 SQL 列可加**，且 **PG 组合根也用同一配置面**
   （`services/api/pg_composition.py:214-220,263-264`）⇒ 「迁移」的真实含义是
   **旧行缺键时解码走向后兼容**，不是 DDL。**本 PLAN 不新建 PG 表**。
3. **契约 schema 是 `additionalProperties: false`**（`schemas/model-definition.schema.json`），
   `required` 只列 `id/endpoint_id/model_name/capabilities`；
   加载器 `adapters/contracts/models_loaders.py::load_models`（`:52-76`）逐字段显式构造
   ⇒ **schema 不加属性、加载器不读，YAML 里写了也会被判红或丢掉**。
4. **API 三个 DTO 与映射**：`services/api/dto/models.py`（`ModelCreateDto:34-40` /
   `ModelUpdateDto:43-48` / `ModelReadDto:51-58`）、`services/api/mappers/models.py`
   （`model_read_dto:41-85`）、`services/api/routers/models.py`（create `:145-164`、
   patch `:184-210`）。
5. **OpenAPI 快照单文件** `docs/api/openapi.m13.json`，由 `tools/gen_openapi.py` 生成，
   drift 门在 `tests/contracts/test_openapi_snapshot.py`；web 类型
   `apps/web/src/api/types.ts`（`ModelReadDto:186-194`）**手工同步**。
6. **已知既存行为（如实登记，不在本 PLAN 修）**：`ModelUpdateDto` 的字段用
   `if payload.x is not None` 构造 ⇒ **显式 `null` 被忽略**，即"清空某字段"今天做不到
   （`types.ts:180` 的注释声称可以——J-1 登记）。本 PLAN 沿用「缺省 = 保持」的既有约定，
   **不顺手改清空语义**（那是独立行为决策）。

## 口径（设计取舍，先写死避免实施时漂移）

- **命名**：`context_window_tokens: int | None`、`thinking_intensity: ThinkingIntensity | None`。
  取值词表用**域枚举** `ThinkingIntensity(StrEnum)` = `MINIMAL | LOW | MEDIUM | HIGH | MAX`
  ——**级别词、厂商中立**（用户声明的 `Max` 落为 `MAX`）。
- **校验**：`context_window_tokens` 设置时必须 `>= 1`（否则 `ValueError`）；
  两个字段**默认 `None`**（既有构造点与既有数据不受影响）。
- **来源口径**：这两个值由**用户/运维声明**（不是探测得来）；因此读面文案必须写明
  「**声明值**，本版本**不向 provider 发送**，也不参与 eligibility 判定」——
  **不得**让读者以为它们已经在生效。这条同样进 `docs/`。
- **不做**：不改 `ModelProfile` / `ModelCapability`（`REASONING` 仍是布尔能力，不升级成强度）；
  不改 eligibility / fallback 语义；不引入新依赖；不改门禁与既有断言强度；
  **不新建 PG 表**（需要即 BLOCKED）。
- **快照同步是流程的一部分**：DTO 变化 ⇒ 用 `tools/gen_openapi.py` 重新生成
  `docs/api/openapi.m13.json` 并同步 `types.ts`（**不是**为过门而改快照——
  drift 门必须仍然存在且绿）。
- **页面改动**：若结构签名/设计基线判红，按既有配方重生成
  （`UPDATE_OUTLINES=1` 单路由 + win32 像素 + 既有容器配方生成 linux 像素 + 跨平台一致性复核），
  **不得**只改期望值让门变绿。

## 验收条件

- **AC-01 域承载**：`ModelDefinition` 两字段存在且可判；设置非法 `context_window_tokens`
  （`0` / 负数）⇒ `ValueError`；**反证**：删掉字段 ⇒ 域用例红。
- **AC-02 契约**：`schemas/model-definition.schema.json` 声明两属性与取值枚举；
  一份带两字段的 YAML 经 `load_models` 读出的值可判；**反证**：从 schema 删属性 ⇒
  该 YAML 判红（`additionalProperties: false` 生效）。
- **AC-03 往返（配置面）**：`SqliteModelStore` 写入 ⇒ 读出两值可判；**旧行缺键**
  （手工构造不含新键的 `model_json`）⇒ 解码得 `None` 且**不抛**；
  判据须证明**两个组合根共用同一配置面**（结构/装配判据，而不是只测 SQLite 一侧）。
- **AC-04 读面（API + 快照）**：三个 DTO 承载两字段；`model_read_dto` 填充；
  API 响应里两值可判；`docs/api/openapi.m13.json` 同步后 **drift 门绿**；
  **反证**：摘掉映射 ⇒ 读面用例红。
- **AC-05 读面（页面）**：web 类型同步 + **页面有渲染分支**（模型详情或目录表），
  stub e2e 断言「有值 / 无值」两种状态**可区分**；**反证**：去掉渲染分支 ⇒ 该 e2e 红；
  web 门（lint / typecheck / unit / build / stub e2e / live e2e）绿。
- **AC-06 诚实登记**：「声明值、本版本不发送给 provider」的口径在**读面文案与文档**同源
  （逐处可判）；`docs/` 有该说明。
- **AC-07 门禁**：受影响定向套件 + 规模门 + `ruff`/`format`/`mypy` + **m0 全量 23 项** +
  治理 `validate.py` 绿。

## 实施清单

### WP-A — 域字段与词表

- `packages/domain/enums.py`：新增 `ThinkingIntensity`。
- `packages/domain/models.py`：`ModelDefinition` 增两字段 + `__post_init__` 校验。
- 用例：字段可判 / 非法值拒绝 / 既有构造点不受影响。
- 提交：`feat(domain): carry declared context window and thinking intensity on the model`

### WP-B — 契约 schema 与 YAML 加载器

- `schemas/model-definition.schema.json`：声明 `context_window_tokens` /
  `thinking_intensity`（含枚举与最小值）。
- `adapters/contracts/models_loaders.py::load_models`：读取两字段。
- `examples/` 的模型示例按需补一行（不新增示例端点）。
- 提交：`feat(contracts): declare the two model parameters in schema and loader`

### WP-C — 配置面往返（含旧行兼容）

- `adapters/sqlite/model_store.py`：`_encode` / `_decode` 承载两字段，**解码对缺键向后兼容**。
- 用例：往返 + 旧行缺键 + 越界值拒绝；结构判据证明两个组合根共用该存储。
- 提交：`feat(sqlite): round-trip the declared model parameters with legacy-row tolerance`

### WP-D — API 读面与快照

- `services/api/dto/models.py`（create/update/read）+ `mappers/models.py` +
  `routers/models.py`（create/patch 构造与重建）。
- `tools/gen_openapi.py` 重生成 `docs/api/openapi.m13.json`；drift 门绿。
- 用例：POST 带两值 ⇒ GET 读回；PATCH 改值 ⇒ 读回新值；**缺映射反证**。
- 提交：`feat(api): surface the declared model parameters on the model read face`

### WP-E — web 类型与页面渲染

- `apps/web/src/api/types.ts` 同步；模型详情/目录表加**渲染分支**。
- 夹具与 stub e2e（有值/无值两态可区分）；设计基线/结构签名按既有配方重生成。
- 提交：`feat(web): render the declared model parameters with their honest status`

### WP-F — 反证、文档与记录

- 逐条反证（先红后复原）并登记前后对照。
- `docs/` 说明（声明值 / 不发送 / 不参与 eligibility）+ 读面文案同源。
- 子 PLAN 收口 + RECHECK；GOAL-008 回写（EC-02、迭代日志、child_plans）。
- 提交：`docs(architecture): say what the declared model parameters do and do not affect`

## 证据

（实施中登记：每条 AC 的命令 + 实测输出摘要 + 反证的前后对照。）

## 状态历史

- 2026-09-20 建档（GOAL-008 cycle 2 = EC-02）：`status: IN_PROGRESS`。
  只读勘察确认 6 条事实（无字段承载 → schema `additionalProperties: false` → 加载器显式构造
  → 配置面是 SQLite JSON blob 且 PG 路径共用 → 快照/web 类型手工同步 → PATCH 显式 null 被忽略）。

## 影响报告

- **Domain/API/schema 变化**：`ModelDefinition` 增两个**可选**字段（默认 None ⇒ 既有构造点
  与既有数据不变）；`ThinkingIntensity` 新枚举；model DTO 三处增字段 ⇒
  **OpenAPI 快照更新**（同步流程的一部分）+ `types.ts` 同步。
- **安全/凭据变化**：无（不触碰凭据面、不新增出网面）。
- **兼容性/迁移风险**：**无 DDL**；旧行缺键走向后兼容解码。风险点是「声明 ≠ 生效」被误读 ⇒
  以读面文案 + 文档同源化解（AC-06）。「清空字段」的既存缺口（显式 null 被忽略）**不在本
  PLAN 修**，如实登记。
- **上游版本影响**：无（不引入依赖、不改 pin）。
- **下一项任务**：EC-05（漂移可见性）或 EC-03（供应链登记与凭据纪律）——按 EC 表序，
  下一轮取 EC-03；EC-02 若部分交付，以「下一轮输入」为准。
