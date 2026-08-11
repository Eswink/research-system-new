# Artifact Store v0.4.0

## Interface

```python
class ArtifactStore(Protocol):
    put(...)
    get(...)
    verify(...)
    list_refs(...)
    archive(...)
    delete(...)
```

## Content Addressing

主键引用可包含：

```text
sha256
media_type
size
storage_uri
```

## Upload Flow

```text
STAGED
→ digest/size/type validate
→ malware/content policy（按需）
→ VERIFIED/QUARANTINED
→ ACTIVE
```

## Large Tool Results

ToolResult 只保存 summary + Artifact refs。

## Reproducibility Bundle

```text
manifest
source/config snapshots
code/environment
inputs
metrics
figures
claim/evidence map
```
