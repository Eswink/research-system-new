---
name: layered-default-resolution
description: Use when a value has more than one source of truth — explicit argument, protocol-phase declaration, project setting, environment variable, or default constant — or when a setting seems to be ignored at runtime. Covers making "undeclared" a first-class fact instead of collapsing it into a default, and checking that a declared field is actually wired through store, DTO, and every construction site. Not for single-level config or for changing a product default.
---

# Layered Default Resolution

多层配置里最贵的缺陷不是「哪一层优先」，而是**默认值把「未声明」吃掉**：构造期读到的显式值在运行期被静默压回默认，而构造期与运行期两条路径各自都能通过自己的判据。

## 缺陷形态（实测）

```text
ProjectSettings.retmax: int = 3        # 缺省即 3
构造期 RESEARCHOS_RETMAX=9            → fixed_arguments = {"retmax": 9}
运行期 retrieval_calls(7)             → {"retmax": 3}     # 被压平
```

两条判据都绿：构造期那条只看 `configured_retmax`，运行期那条只看缺省路径。「未声明」与「声明了 3」在值上不可区分 ⇒ 缺陷无判据可抓。

## 硬规则

1. **缺省即 `None`**：字段写成 `int | None = None`，让「未声明」是一阶事实。
2. **不施加时必须返回同一对象**：`apply_x(calls, None)` 返回**入参本身**（`is` 相同），不是等值副本。等值副本会让「未声明」重新变成「施加了默认值」。
3. **只改自己那一种调用**：`apply_x` 只改带该键的调用，不得给不带键的调用新增键。
4. **有效性校验放在唯一同时看见两层的点**：越界 / 非整数 / 布尔（`bool` 是 `int` 子类，必须显式排除）在那一处点名拒绝，判词要点名**是哪一层**给的坏值。
5. **措辞分级要说清**：`configured_x` 内是四级回落（显式 > 项目声明 > env > 默认常量）；加上协议相级后整体是五级取值。两处口径在源码里都存在，混说会让人按字面执行出错。

## 断链检查清单（这层最容易被忽略）

字段在 Domain 里存在 **≠** 产品路径接通。逐点核对：

- [ ] store 的 `get` 与 `save` payload 都含该字段（缺一即恒回落到下层）
- [ ] DTO / OpenAPI 快照含该字段（或**显式**决定不进 DTO 并记录理由）
- [ ] 每一处 `XxxSettings(...)` 构造点都传了它 —— `rg -n "XxxSettings\("`
- [ ] 配置样例能表达它；同时确认没有「看起来像配置但产品不读」的死字段
- [ ] schema 是 **closed**（`additionalProperties: false`），未知键在加载期点名（开放的 schema 会让拼错的键静默失效）

## 判据

- 「声明 3」与「未声明」必须可区分（同一断言里跑两条输入，输出不同）。
- 未声明时，运行期值**不得**被压回默认（这是缺省抹平的直接反证）。
- 每一层各一臂：显式 > 协议相级 > 项目声明（仅在已声明时）> env > 默认。
- 非法值（越界 / 非整数 / `True`）点名拒绝，判词含层级名。
- 端到端读**出站参数**（如检索请求里的 `pageSize`），不读内部字段——内部字段一致而线上不同是另一类缺陷。

## 陷阱

- **协议相级与显式参数同时在场**：若显式值在构造期就短路了配置面，「显式最高」是由构造期保证的，不是运行期比较出来的 ⇒ 这一臂要么补，要么在记录里写明未覆盖。
- **`replace()` 出来的新对象仍可能是等值副本**：判「未声明」用 `is`，不用 `==`。
- **项目级字段可能只在 `from_mapping` 一条路上被读出**：store / REST 全无该字段时，产品上项目级恒 `None`——这是缺口，不是「默认行为」。
