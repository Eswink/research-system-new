# M13 API Stack Qualification — FastAPI / Uvicorn / Starlette / Pydantic

- 日期：2026-08-25
- 性质：M13（Research Console）Control Plane API 栈选型与供应链登记
- 范围权威：`docs/roadmap/MILESTONES.md` M13 节（唯一权威）；
  `docs/architecture/SYSTEM_ARCHITECTURE.md` §3（`services/*` = inbound entry
  adapter + composition root）

## 结论

采用 **FastAPI 0.141.1 + Uvicorn 0.52.4**（+ 传递 Starlette 1.6.0 / Pydantic 2.13.4）
作为 Research OS Control Plane API 的正式 Python API 栈。不引入第二套 API
stack；M14+ 的 PostgreSQL / Temporal 演进不改变本选型（仅替换 adapter 层）。

## 选型依据

1. **仓库既定方向**：`SYSTEM_ARCHITECTURE.md` §1 明确 `FastAPI API` 为
   Control Plane 组件；M13 是首份落地。
2. **依赖兼容（关键）**：`openhands-sdk==1.42.0`（M5R 冻结）已传递依赖
   `starlette 1.6.0`；fastapi 0.141.1 的 `starlette>=0.46.0` 约束与 1.6.0
   兼容，全仓库共享单一 starlette 版本，无版本分裂。`uv lock --check` 通过。
3. **Pydantic v2** 与 Domain 边界隔离：API DTO 独立于 `packages/domain`
   dataclass，禁止 `__dict__` dump；DTO ↔ Domain 映射在 `services/api/dto/`
   显式完成（`.importlinter.api` 强制 DTO 不 import packages/adapters）。

## 供应链登记（UPSTREAM_COMPONENTS.yaml）

| Component | 版本 | sdist digest (sha256) | License |
| --- | --- | --- | --- |
| fastapi | 0.141.1 | e8822fc40db1e1858054d7a949a888695bc9bdce70139178e33bd2871a453ca1 | MIT |
| uvicorn | 0.52.4 | 73acfee47a0b133c5de13d219492d62d8a31e935f4fe6e41a232451a15379f86 | BSD-3-Clause |
| starlette | 1.6.0 | d4e3ac5e546444960c710297a3c9fc3f7ebae1b7e963f3d36173b49da535be9b | BSD-3-Clause |
| pydantic | 2.13.4 | c40756b57adaa8b1efeeced5c196f3f3b7c435f90e84ea7f443901bec8099ef6 | MIT |

升级门禁：显式批准 + lock_refresh + license_review + control_plane_api_regression；
starlette 额外叠加 openhands_adapter_contract_suite（保护 M6 适配器）。

## 边界与风险

- **DTO 单一真相**：OpenAPI schema 导出 `docs/api/openapi.m13.json`
  （`scripts/gen_openapi.py`），前端 TS 类型由此生成；
  `tests/contracts/test_openapi_snapshot.py` 防漂移。
- **测试栈**：`fastapi.testclient`（httpx 传输）用于 API contract 测试；
  真实网络（relay probe）仅 `requires_live_llm` opt-in。
- **已知注意**：fastapi.testclient 对 httpx 的 deprecation warning 为
  starlette 1.6 上游提示，不阻塞 CI（非错误）。
- M14+：PostgreSQL canonical state 通过同一 Port 接缝替换配置存储；
  Temporal 决策另行 qualification（`MILESTONES.md` M14 节）。