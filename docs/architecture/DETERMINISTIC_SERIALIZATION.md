# Deterministic Serialization — v0.4.0

## 目的

Research OS 需要对 RunManifest、HandoffBundle、Artifact、Event payload 等对象计算可复现的 digest。本文件定义 canonical 序列化规则，保证同一逻辑对象（字段顺序、Decimal 精度、时区表示不同）总是产生相同的字节序列与 `sha256` digest。

实现：`packages/domain/serialization.py`；值对象：`packages/domain/core.py`。

## 适用范围

- RunManifest 快照 digest（不可变语义快照）
- HandoffBundle digest（schema 强制 required）
- Artifact 内容 digest（sha256 内容寻址）
- Event payload_digest
- 任何需要确定性比较或指纹的域对象

## Canonical JSON 编码规则

1. **key 排序**：对象（dict）的 key 递归排序，比较按 `str(key)` 字典序。嵌套 dict、dataclass 展开后的 dict 同样递归处理。
2. **datetime**：必须是 aware datetime；编码为 RFC3339 UTC，尾缀 `Z`。微秒为 0 时省略小数部分（`2026-08-11T12:00:00Z`），否则保留 6 位（`2026-08-11T12:00:00.123456Z`）。非 UTC 时区先归一化到 UTC。
3. **Decimal**：非有限值（NaN/Infinity）拒绝。零统一编码为 `"0"`（含负零与 `0E+3`）。其余调用 `normalize()` 去除尾随零后以无指数形式输出（`Decimal("1E+3")` → `"1000"`）。
4. **UUID**：编码为规范小写字符串（`str(uuid)`）。
5. **dataclass**：递归展开为 dict（等价 `dataclasses.asdict`）。
6. **float 拒绝**：`float` 不允许进入 digest 对象（精度不可复现）。需要数值时使用 `int` 或 `Decimal`。
7. **其他类型**：`str`、`int`、`bool`、`None`、`list`、`tuple` 支持；其余类型抛 `TypeError`。
8. **输出格式**：无多余空白（`separators=(",", ":")`）、`sort_keys=True`、UTF-8、不转义非 ASCII（`ensure_ascii=False`）。

## Digest 表示

- 算法：`sha256`
- 字符串形式：`sha256:<64 位小写 hex>`（如 `sha256:ab...`），参考示例契约中的 `digest: sha256:fixture-only`。
- 值对象：`Digest.hex_value` 保存 hex；`str(digest)` 带前缀；`Digest.parse(text)` 接受带前缀形式。

## 设计约束

- Decimal 尾随零会被 `normalize()` 归一化：`Decimal("0.0100")` 与 `Decimal("0.01")` 产生相同 digest。若某字段需要保留精度语义，应使用 `Money`（整数最小单位）或显式定点类型。
- 本规则不包含浮点类型；任何新增可 digest 对象必须遵守上述类型白名单。
- 规则变更属于契约资产变更，必须同步实现、测试与
  `.cursor/skills/system-spec-check/scripts/validate_bundle.py` 检查后发布。