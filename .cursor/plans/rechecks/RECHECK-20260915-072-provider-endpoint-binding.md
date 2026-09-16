---
id: RECHECK-20260915-072
plan_id: PLAN-20260915-072
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-16
completed_at: 2026-09-16
reviewer: root-agent-goal-003-cycle10
baseline_ref: 4bc2f89
checked_head: 4bc2f89+worktree
---

# RECHECK-20260915-072 — provider 端点绑定（GOAL-003 cycle 10）

## 检查范围

PLAN-20260915-072 声称的交付面：`services/api/tool_provider_endpoints.py`（三态解析与
只读投影）、`services/api/preflight_support.py` 的探测门槛、注册面把 `endpoint_env`
从**写入 → 存储 → 读面**打通（域实体 + `spec()` 重建 + SQLite 往返 + 注册/更新 DTO +
注册读面 DTO）、`schemas/tool-provider.schema.json` 的字段说明、示例配置的误用修正、
以及 `tests/api/test_tool_provider_endpoint_binding.py` 与 store 用例。

**同时处置**：cycle 9 收口提交在 CI 上的红项（见文末「随本轮入库的更正」）。

**未覆盖**（见告警）：把解析出的端点**注入 adapter**（需要按 spec 重建 provider 实例）。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 三态解析且只读进程环境（AC-01） | `test_binding_states_read_the_process_environment_only`：未声明 / 未设置（含空白值）/ 已设置三态；**同名值写在文件里不算数**（文件确实存在，解析仍判未设置）；另有 `test_resolver_reads_the_real_process_environment_by_default` 证明默认路径真的读 `os.environ`（否则注入映射会掩盖"其实没接线"） | PASS |
| 不泄漏（AC-02） | 绑定后只有 `sha256:` 指纹；`repr(binding)` / `repr(dto)` / `model_dump()` 三段序列化里都**不含端点明文**也不含主机名；指纹稳定且换值即换指纹（"换没换"可被看见）；探测 detail 同样不含端点 | PASS |
| 读面自洽（AC-02 附加） | `test_endpoint_binding_rejects_inconsistent_states`：只有 `BOUND` 允许带指纹，`NOT_DECLARED` 不许带变量名，未知状态直接拒绝 | PASS |
| 执法而非装饰（AC-03） | `test_declared_but_unset_endpoint_blocks_the_probe`：声明 + 未设置 ⇒ 探测**不执行**、UNKNOWN、detail 点名变量且 `observed_schema_digest=None`；**去掉声明** ⇒ 同一 fixture 回到原路径（HEALTHY，门槛挂在声明上）；NATIVE 不看端点声明；设置变量后回到正常探测 | PASS |
| 可见（AC-04） | `test_registration_read_surface_carries_the_binding`：注册（带声明）→ 读面 `ENV_UNSET`；设置环境变量后**同一份注册**立刻变 `BOUND` + 指纹；未声明的注册是 `NOT_DECLARED`；注册读面字符串里无端点明文 | PASS |
| 存储往返与旧行（AC-04 附加） | `test_endpoint_env_round_trips_and_legacy_rows_stay_undeclared`：声明入库往返一致；**抹掉键的历史行**解码为 `None`（未声明），不抛错也不补假值 | PASS |
| 配置/规格对齐（AC-05） | 示例配置不再把 `NCBI_API_KEY` 写进 `endpoint_env`（并留注释写明凭据不走这里）；schema 增 `description`；`docs/integration/MCP_TOOL_PROVIDERS.md` §6.1 写明 env-only / 凭据边界 / 未设置即不可用 / 只暴露指纹；`test_example_config_keeps_credentials_out_of_endpoint_env` 钉住示例约定 | PASS |
| 定向套件（AC-06） | `tests/adapters/sqlite` **97 passed**；`tests/api` **380 passed**；`tests/contracts + tests/loaders` **398 passed / 56 skipped**；OpenAPI 重生成（+66 行）后快照契约通过 | PASS |
| 全量门禁 + 记录（AC-06） | m0 **PASS: profile=m0; 23 deterministic checks**；ruff/format 干净；mypy 相关模块 clean；RECHECK-072 + MEM-047 + GOAL 记账 + ALL_PLAN | PASS |

## 告警

- **W-1（仍未"用"上解析出的端点）**：本轮把 `endpoint_env` 变成**准入条件 + 可见状态**，
  但 adapter 仍用构造时注入的连接规格。要让解析结果真正参与执行，需要按 spec
  重建 provider 实例（composition 级改动）——如实登记为下一轮候选，**不要把本轮读成
  "端点已经由配置驱动"**。
- **W-2（门槛会让"声明了但没配"的 provider 变红）**：这是有意的诚实化（不是回归），
  已写进 schema description 与文档；示例配置先修好，避免开箱即红。运维若把
  `endpoint_env` 当"可选提示"写进配置，升级后会看到 UNKNOWN。
- **W-3（指纹不是端点）**：读面只给 `sha256` 指纹与变量名，运维要知道具体端点仍需查环境变量；
  另外指纹对**可猜测的 URL** 存在"确认猜测"的理论空间——这是"可观测 vs 不泄漏"的取舍，
  已在模块 docstring 写明。
- **W-4（凭据表达面仍缺）**：`ToolProviderSpec` 无法表达 `credential_ref`
  （示例里被误用的那个名字正说明这个缺口），凭据目前只能由 adapter 的默认值决定。
  这是相邻缺口，不在本 PLAN 判据内。
- **W-5（示例约定的钉子是定点而非通用）**：`endpoint_env` 命名检查只覆盖随仓库发布的
  示例配置（`_KEY/_TOKEN/_SECRET/_PASSWORD` 结尾即判红），**不是**运行时通用门禁——
  避免用启发式规则误伤合法命名。它钉住的是本轮修掉的那次真实漂移。

## 随本轮入库的更正（cycle 9 CI 红项）

cycle 9 收口提交 `cb61f41` 的 CI run **35115260874**：`quality-ubuntu-latest` 在
`python/tests` 判红，其余五个 job success。红的是 cycle 9 的**负载型反证用例**
（2 vCPU runner 上 288 次往返没复现竞态；本地 8+ 核每次 10~20/96）。
处置：该反证改为**结构判据**（产品连接的读结果在锁内取尽 = `MaterializedRows`；
退回语句级串行 = 裸 `sqlite3.Cursor`），确定性、任何机器成立；负载型复现器
（含实测数字与脚本路径）降级为记录，不再当门禁。详见 RECHECK-071 的「更正」段。
**这不是放宽断言**：门禁从"不可移植的症状判据"换成"可移植的结构判据"，
被保护的性质（读结果在锁内取尽）没有改变。

## 结论

一个**声明了却没有任何消费者**的字段（`endpoint_env`，且示例里还被写成了凭据名）
在本轮被接成真实的能力：解析只读进程环境、端点明文不进任何读面、未设置即不可用
（点名变量而非伪装健康）、注册写入/存储往返/读面投影全线打通、旧行按"未声明"解码。
结果为 **PASS_WITH_WARNINGS**：W-1（还没把端点注入 adapter）如实标注为下一轮候选，
W-2/W-3/W-5 是这条"执法 + 可见"路线的代价与边界，W-4 是相邻缺口。
