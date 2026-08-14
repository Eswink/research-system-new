# Skill Registry v0.4.0

## 1. 定位

Skill 是纯声明资产（ADR-0005）：可复用方法指令，只声明所需
Capability，**不授予任何权限**。授权面始终由 Role 的
`requested_capabilities` / `forbidden_capabilities` 与 PolicyEvaluator
裁决；Skill Registry 只负责稳定加载、引用校验与能力路由。

```text
Role/Agent
→ Skill Registry（digest/version/lifecycle 校验）
→ Capability 声明并集（纯声明，不产生 CapabilityGrant）
→ ToolResolver（policy + health + trust 求交）
→ ToolProvider
```

## 2. 数据面

`SkillSpec`（`packages/domain/tools.py`）：

```text
id / version（semver）
capabilities（声明所需，非授权）
description
status：ACTIVE → DEPRECATED → RETIRED
digest：内容确定性 digest（不含 digest 与 status 字段本身）
```

- `skill_content_digest` 覆盖 id/version/capabilities/description；
  status 是 registry 生命周期元数据，不参与内容 digest。
- `schemas/skill.schema.json` 为 YAML/JSON 配置契约。

## 3. Registry

`packages/application/skill_registry/registry.py`：

- `build_registry`：稳定加载（key 与 spec.id 一致性检查）。
- `check_skill_refs`：按引用校验
  MISSING / DIGEST_MISMATCH / DEPRECATED / RETIRED。
- `SkillRefIssueKind` 枚举承载四类问题，preflight 映射为
  `SKILL_MISSING / SKILL_DIGEST_MISMATCH / SKILL_DEPRECATED /
  SKILL_RETIRED`（agent 面历史 MISSING 保持
  `AGENT_PERMISSION_DENIED` 向后兼容）。

## 4. 能力路由

`packages/application/skill_registry/routing.py`：

- `capability_union_for_skills`：ACTIVE 且 digest 一致的 skill 的
  capability 声明并集（确定性排序）；MISSING / DIGEST_MISMATCH /
  RETIRED 不参与路由；DEPRECATED 参与路由但带 issue 标记。
- 路由输出是纯声明集合，**不产生 `CapabilityGrant`**——Skill 无法
  自行授权限（负面测试：
  `tests/application/test_skill_registry.py::TestRouting`）。

## 5. 生命周期

`packages/application/skill_registry/lifecycle.py`：

```text
ACTIVE → DEPRECATED → RETIRED
```

- 合法迁移：ACTIVE→{DEPRECATED, RETIRED}、DEPRECATED→{RETIRED}；
  反向与自迁移抛 ValueError。
- 退役不自动撤销 capability（授权面由 Role/Policy 控制），但引用
  RETIRED skill 会被 Registry 拒绝；DEPRECATED 引用产生 warning。

## 6. Role/Agent 集成

- `AgentSpec.skill_refs` / `RoleDefinition.default_skills` 经
  preflight（`packages/application/preflight/role_checks.py`）解析：
  `check_agent_permissions` 把 skill 的 capability 声明并入能力面并
  做 Registry 校验；`check_role_skills` 校验 role 默认 skill 引用。
- 复用：同一 skill id 可被多 Role/Agent 引用，每个引用独立校验
  （多主体引用测试覆盖）。
- loader：`adapters/contracts/roles_loaders.py::load_skills` 支持
  `status` 与 `digest` 字段。

## 7. 测试锚点

- `tests/application/test_skill_registry.py`（digest/生命周期/路由/复用）
- `tests/domain/test_tool_plane_domain.py::TestSkillDigest`
- `tests/integration/test_capability_plane.py::TestSkillCannotGrantPermissions`
- preflight 集成：`tests/application/test_m4_preflight_roles.py`