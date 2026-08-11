---
name: system-spec-check
description: 校验 Research OS system specification 的文档、Schema、示例配置、Role/Agent/Model/Protocol 引用和安全架构硬边界。
disable-model-invocation: true
---
# System Specification Check

当 `docs/`、`schemas/`、`examples/`、Research OS 架构契约或版本化 specification 发生变化时显式运行。

```bash
python -B scripts/validate_bundle.py
```

本 Skill 拥有 system-specification 的离线 bundle validator。不要把该脚本重新移动到仓库根 `scripts/`。
