---
name: framework-release
description: 显式发布 Cursor Engineering Framework；从根 VERSION 读取版本，运行确定性 validators/evals，生成 release evidence、SHA-256 manifest 与复验后的 ZIP。
disable-model-invocation: true
---
# Framework Release

先读取仓库根 `VERSION`，将其值作为下面命令的 `<VERSION>`：

```bash
python -B scripts/release_cursor_framework.py --version <VERSION>
python -B scripts/verify_cursor_framework_release.py --version <VERSION>
python -B scripts/package_cursor_framework.py --version <VERSION> --output ../system-specification-cursor-framework-v<VERSION>.zip
```

以上路径均从本 Skill root 解析；本 Skill 的公开脚本位于 `scripts/`。

Release 必须：
- `VERSION`、framework metadata、主文档版本一致；
- system-spec/governance/framework/learning validators 全部通过；
- Hook/Framework/Learning evals 全部通过；
- 根目录不存在泛化 `scripts/`；工程自动化脚本由对应 Skill 所有；
- 发布包不包含 runtime 瞬态状态、`__pycache__`、`.pyc` 或 `.git/`；
- ZIP 在全新目录解压后再次运行 release verification 与回归检查。

Reviewer 仅按风险选择，不设置固定轮数、固定人数或数值评分阈值。
