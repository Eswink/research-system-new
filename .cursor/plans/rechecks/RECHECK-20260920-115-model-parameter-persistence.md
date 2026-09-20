---
id: RECHECK-20260920-115
plan_id: PLAN-20260920-115
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-20
completed_at: 2026-09-20
reviewer: root-agent-goal-008-cycle2
baseline_ref: a6c03bc
checked_head: 53f4a26
---

# RECHECK-20260920-115 — 模型参数落库（EC-02 复检）

## 检查范围

不采信实施叙述：按 EC-02 判据在**当前树**上真跑，逐条做**先红后复原**的反证，门禁以
**完整 m0（23 项）**为准而不是「定向套件绿」。检查面：

- 承载：`ModelDefinition` 两字段可判、非法值被拒、既有构造点不受影响；
- 契约：`schemas/model-definition.schema.json` 声明两属性（`additionalProperties: false` 使
  「没声明就写不进去」本身成为判据）；
- 往返：YAML 加载器取值可判 + `SqliteModelStore` 写读往返 + **旧行缺键**解码不抛；
- 装配：两组合根**共用同一个配置面实例**（AST 判据），**PG 组合根运行期读回两值**
  （`build_postgres_assembly` → `build_postgres_apideps`，无事后替换）；
- 读面：API 三 DTO + 映射 + OpenAPI 快照 drift 门 + 页面渲染分支（stub e2e）；
- 诚实：读面文案与 `docs/` 同源（声明值 / 不发送 / 不参与 eligibility）。

## 检查结果

### 判据（实测）

| AC | 判据 | 结果 |
| --- | --- | --- |
| AC-01 域承载 | `tests/domain/test_model_declared_parameters.py`（6 条：原样携带；默认缺省为 `None`；`0 / -1 / -512000` 被拒；词表是厂商中立级别词） | PASS |
| AC-02 契约 | `tests/loaders/test_contract_loaders.py::test_load_models_carries_declared_parameters`（示例模型读出 `512000` / `ThinkingIntensity.MAX`；未声明的模型保持 `None`）+ 既有 `test_load_models_from_fixture` | PASS |
| AC-03a 往返（配置面） | `tests/adapters/sqlite/test_model_store_declared_parameters.py`（3 条：往返；缺省往返为 `None`；**手工构造的旧行**缺键解码为 `None` 且不抛） | PASS |
| AC-03b 两组合根共用配置面 | `tests/architecture/python/test_model_config_face_wiring.py`（AST：`assemble` 只构造 **1** 个 `SqliteModelStore` 并传给两个分支；PG 根不自建、从 `config` 取同一实例交给 `PostgresAssembly`；PG 迁移无 `models` 表） | PASS |
| AC-03c PG 根运行期读面 | `tests/postgres/test_m14_model_declared_parameters_pg_root.py`（2 条：`deps.model_store is model_store`；POST/GET/PATCH 两值可判且 PATCH 后 ETag 变；未声明读回 `null`） | PASS |
| AC-04 读面（API+快照） | `tests/api/test_models_api.py` 新增 6 条（create 读回 / 缺省 `null` / PATCH 改值且 **ETag 变** / probe 后仍保留 / `0` 与非法词表 422）+ `tests/contracts/test_openapi_snapshot.py`（drift 门）+ 快照重生成 **+91 行** | PASS |
| AC-05 读面（页面） | `apps/web/tests/e2e/models-declared-parameters.spec.ts`（3 条：有声明 en/zh 两语言都渲染值 + 诚实文案；无声明渲染「未声明」且不推断默认值）；web `lint` / `typecheck` / `unit(76)` 绿 | PASS |
| AC-06 诚实登记 | 同源四处：`docs/architecture/DOMAIN_MODEL.md` §5、`docs/architecture/MODEL_COMPATIBILITY.md` §4、`docs/integration/MODEL_GATEWAY.md` §4、页面文案（en/zh 两套断言） | PASS |
| AC-07 门禁 | 定向套件 + 规模门 + `ruff`/`format`/`mypy(949 files)` + **m0 全量 23 项** + 治理 `validate.py` | PASS |

### 反证（先红后复原，均在本轮实测）

| # | 注入的缺陷 | 观察到的红 | 复原后 |
| --- | --- | --- | --- |
| F1 | 从 `ModelDefinition` 摘掉两个字段 | `tests/domain/test_model_declared_parameters.py` **5 failed**（`unexpected keyword argument 'context_window_tokens'`） | 绿 |
| F2 | 从 `schemas/model-definition.schema.json` 摘掉两个属性 | `tests/loaders/test_contract_loaders.py` **2 failed**（`Additional properties are not allowed ('context_window_tokens', 'thinking_intensity' were unexpected)`）——`additionalProperties: false` 判定确实在咬 | 绿 |
| F3 | 去掉 `create_model` 构造里的两字段 | `tests/api/test_models_api.py` **2 failed**（`assert None == 512000`） | 绿 |
| F4 | 去掉 `_merge_probed` 重建时的两字段 | 同文件 **1 failed**（probe 后声明被丢） | 绿 |
| F5 | 从 `model_version` canonical dict 去掉两键 | 同文件 **1 failed**（PATCH 后 ETag 不变——If-Match 保护对声明字段失效） | 绿 |
| F6 | 从 `apps/web/src/api/types.ts` 的 `ModelReadDto` 摘掉两字段 | `tsc --noEmit` **11 处**（`ModelDetails` / `ModelCatalogTable` / `apiFixtures`） | 绿 |
| F7 | 去掉 `<DeclaredParameters/>` 挂载 | 新 e2e spec **3 failed** | 绿 |
| F8 | PG 分支各建一个 `SqliteModelStore` | 装配判据 **1 failed**（"构造了 2 个"） | 绿 |
| F9 | `PostgresAssembly` 不带 `model_store` | 装配判据 **1 failed** + PG 运行期用例 **2 failed**（`TypeError: missing 1 required positional argument`） | 绿 |
| F10 | `PostgresAssembly(model_store=None)` | PG 运行期用例 **2 failed**（身份断言失败 + `save_model` on `None`） | 绿 |
| F11 | 往 `adapters/postgres/migrations/` 放一个 `CREATE TABLE models` | 装配判据 **1 failed**（点名该文件）；探针文件已删除，`git status` 复查干净 | 绿 |

复原后：`tests/domain + tests/loaders + tests/architecture/python/test_model_config_face_wiring.py`
**33 passed**；`tests/postgres/test_m14_model_declared_parameters_pg_root.py` +
装配判据 **5 passed**。

### 设计对照门（**零 diff** 的结论必须说清射程）

`pnpm --dir apps/web exec playwright test design-fidelity`（34 路由像素 + DOM 结构签名）
**2 passed**，且 `design-fidelity.spec.ts-snapshots/` 与 `design-outlines.json` **零 diff**。
**原因不是"页面没改"，而是该路由在替身下不渲染数据**：默认 `stubApi` 的路由表没有
`GET /models`，`library-model-registry` 基线渲染的是错误态，表格/详情组件未挂载。
⇒ 新渲染分支由**自带的 stub spec**（F7 可咬）覆盖；设计基线**无需**按配方重生成
（重生成反而会引入无意义的跨平台像素 diff）。已登记为 MEM-20260920-088。

### 复检**实测出的门禁失败**

本轮无 m0 门禁失败（无 G 项）：`ruff format` / `ruff check` / `mypy` / 规模门在提交前就地跑过，
首次 m0 全量即 **23/23 PASS**。这与 cycle 1（G1–G4 四处）不同，原因如实说明：本轮先按
**受影响面**跑过格式化与类型门，再进全量 m0；不是门禁变弱。

### 门禁

- `python/format-check` / `python/product-lint` / `python/typecheck`（**949 files**）：PASS。
- 定向：`tests/domain/test_model_declared_parameters.py` + `tests/adapters/sqlite/test_model_store_declared_parameters.py`
  + `tests/loaders/test_contract_loaders.py` + `tests/api/test_models_api.py`
  + `tests/architecture/python/test_protocol_vocabulary.py` + `tests/contracts/test_openapi_snapshot.py`
  **56 passed**；PG 根用例 + 装配判据 **5 passed**；web unit **76 passed**。
- **本地 m0（profile=m0）**：**PASS: profile=m0; 23 deterministic checks**，测试计数器
  **4097 passed / 11 skipped**（冻结树 `40fe55d` 上的一次全量运行，耗时 461.72s）。
- 其后仅新增一段文档（`MODEL_COMPATIBILITY.md` §4，提交 `53f4a26`）：已单独复跑
  `framework/validate_bundle`、`framework/docs_consistency_check`（`DOCS-CHECK PASS: 6 deterministic checks`）、
  治理 `validate.py`（`Cursor 治理验证通过`）三门绿；**未**重跑全量 m0，
  故 m0 的 23/23 对应 `40fe55d`，这一点如实登记。

## Warnings（不阻断，如实登记）

- **W-1 声明值不生效**：`context_window_tokens` / `thinking_intensity` 只是**声明**，
  既不发送给 provider，也不参与 eligibility / capability 匹配 / 预算折算。用户授权 (2)
  要求「如实记录到读面或如实登记为不支持」——本轮走的是**前者 + 明写不生效**；
  若要让 `thinking_intensity=MAX` 真正生效，需要执行侧映射（OpenHands/litellm 的
  `reasoning_effort` 一类参数）与新的供应商差异面，**本轮未做也不声称可做**。
- **W-2 OpenHands 侧未接线**：agent 真实运行走 OpenHands SDK，不读这两个声明字段；
  本轮的读面在配置面与控制台，**不在运行时**。
- **W-3 web 类型与 OpenAPI 快照没有自动比对门**：`types.ts` 仍是**手工同步**
  （`tests/contracts/test_openapi_snapshot.py` 只守 Python 侧快照 drift）。
  本轮的耦合判据是 `tsc`（F6 证明它真的会红），不是「有生成器/有 drift 门」。
- **W-4 「迁移」的语义**：配置面是 SQLite 的 JSON blob 键值行，**没有列可加**，
  也没有新建 PG 表；EC-02 的迁移面 = **旧行缺键时的解码向后兼容**（F1 之外的
  `test_legacy_row_without_the_new_keys_decodes` 钉住）。**不得**被读成「模型参数已在 PG 持久化」。
- **W-5 设计对照门对本分支不可见**：见上节；新分支靠自带 spec 覆盖，
  像素/结构基线零 diff 是**射程**问题而不是"新分支已被设计门覆盖"。
- **W-6 PLAN-115 建档时登记的两条既存行为未改**：`ModelUpdateDto` 的**显式 `null` 被忽略**
  （"清空某字段"仍做不到）、`RUNTIME_OBSERVED` 等既有语义未动——本轮按口径「缺省 = 保持」，
  不做顺手的行为变更。
- **W-7 示例契约的注释是唯一「配置侧」的诚实提示**：`examples/config/models.yaml` 里
  `agnes_flash` 带两值并有注释说明；`examples/config/models.yaml` 之外没有别的示例模型声明它们。

## 结论

**PASS_WITH_WARNINGS**。EC-02 的可判部分全部成立，且每条关键判据都有独立反证（F1–F11）：

1. **承载字段**在域上存在、可判、可拒非法值；词表是厂商中立的级别词（AGENTS.md §1 未破）；
2. **契约 + 加载器**两侧同时改（少了任一侧即红：schema 侧 F2、加载器侧 F3/F4 同源）；
3. **往返**覆盖新值与旧行缺键两条路径，且**两组合根共用同一配置面**既有 AST 判据
   （F8/F9/F11）又有 PG 根**运行期**判据（F10）；
4. **读面**三 DTO + 快照 + 页面渲染分支都在，且 PATCH 改声明值会让 **ETag 变**（F5）
   ——不会出现"改了值但版本号不动"的静默；
5. **诚实登记**在读面文案（en/zh）与三份文档四处同源，并明确写下「不发送、不参与
   eligibility」；
6. 全量 m0 在冻结树 **23/23 PASS**（4097 passed / 11 skipped）。

**未完成即未声称完成**：W-1（声明不生效，需执行侧映射）、W-2（OpenHands 未接线）、
W-3（web 类型无自动 drift 门）、W-5（设计门射程）都是**真实边界**，已逐条登记；
EC-04 / EC-05 的 live 分支仍受**无凭据**限制（cycle 1 的 W-1 不变）。
