# Version Policy — v0.4.0

本仓库采用**单一工程版本**。

唯一版本源：

```text
VERSION
```

当前值：`0.4.0`。

所有 Research OS system specification、Cursor Engineering Framework、示例 Protocol、开发入口和发布 Manifest 都使用同一个版本号。

## 规则

- 不再维护 “Research OS baseline version” 与 “Cursor Framework version” 两套并行版本。
- 文档标题、示例文件名和配置中的项目版本必须与根 `VERSION` 一致。
- 上游软件自身版本（例如 Python、Cursor、OpenHands）不受本规则影响。
- 历史版本信息属于外部发行记录，不作为当前主包中的活动约束。
- 升级版本时先修改 `VERSION`，再运行统一版本 validator；禁止只修改部分文档。
