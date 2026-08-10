# Plugin / Tool Supply-chain Governance

## 1. ToolPackManifest

```yaml
id:
version:
source:
resolved_revision:
digest:
license:
tools:
skills:
requested_capabilities:
network_domains:
credentials:
compatibility:
```

## 2. Trust Level

```text
BUILT_IN
VERIFIED
USER_APPROVED
UNTRUSTED
REVOKED
```

## 3. Install Flow

```text
Discover
→ Fetch metadata
→ Resolve immutable revision
→ Verify digest/signature
→ License/policy scan
→ Capability diff
→ Sandbox test
→ Approval
→ Install
```

## 4. Update

工具升级不是静默操作。

必须显示：

- schema diff；
- permission diff；
- network/credential diff；
- removed/added tools；
- migration impact。

## 5. MCP Versioning

记录：

```text
transport
protocol version
server capabilities
tool schema hashes
auth mode
```

Remote 默认采用当前推荐的 Streamable HTTP；旧 transport 仅兼容模式。

## 6. Revocation

ToolPack 可被禁用/撤销。

已运行 Run 保留历史 manifest，但新 Task 不再解析到已撤销版本。
