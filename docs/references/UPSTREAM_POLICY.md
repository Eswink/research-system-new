# Upstream Dependency Policy v0.2.2

## Pin

核心依赖使用 exact version/commit，写入 lockfile 和 Run/Deployment manifest。

## Compatibility Matrix

记录：

```text
Research OS version
upstream version
Python/Node version
supported features
known incompatibilities
contract test result
```

## Upgrade Gate

```text
release notes/security advisory
→ dependency install
→ adapter contract
→ security tests
→ vertical slice regression
→ canary
→ approve
```

## No Type Leakage

Domain/Public API 不暴露上游类型。

## Plugin Pin

Plugin/ToolPack 解析 floating ref 后，必须保存 immutable commit/digest。

## Patch

如必须 patch：

```text
patches/<upstream>/<version>/
PATCHES.md
```

记录 removal condition。

## Security Response

支持：

- revoke version；
- disable ToolPack；
- block model endpoint；
- quarantine artifact；
- emergency policy bundle。
