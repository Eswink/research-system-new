---
id: MEM-20260920-099
title: "凭据解析器按构造方式分三种语义：无参 EnvCredentialResolver 拷贝 os.environ（快照），传 environment= 的按引用持有，RegistryCredentialResolver 一律 dict() 拷贝"
status: ACTIVE
created_at: 2026-09-21
updated_at: 2026-09-21
scope: repository
confidence: 0.9
review_after: 2027-09-21
source_plans:
  - .cursor/plans/tasks/PLAN-20260920-125-credential-lifecycle-runbook.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260920-125-credential-lifecycle-runbook.md
supersedes: []
tags:
  - credentials
  - resolver
  - env
  - windows
  - goal-009
---

# 凭据解析器的构造语义（GOAL-009 cycle 5 实测）

## 做了什么

为 GOAL-009 EC-05（凭据生命周期 runbook）在**不读真实凭据**的前提下（用虚构值）实测了解析器语义，
发现 **GOAL-009 的 EC-05 判定细则原文是错的**（原文写「`EnvCredentialResolver` 每次读
`os.environ` ⇒ 同一进程内改 `os.environ` 即生效」）。实测结论按**构造方式**分三种：

| 构造方式 | 来源之后变化时 | 机制 |
| --- | --- | --- |
| `EnvCredentialResolver()`（**生产路径**，无参） | **看不到** —— 已构造的实例是**快照** | `dict(os.environ)` |
| `EnvCredentialResolver(environment=…)` | **看得到** —— 映射**按引用**持有 | 直接赋值 `self._environment = environment` |
| `RegistryCredentialResolver(environment=…)` | **看不到** —— 快照 | `dict(environment)` |

另有第二条边界（原文也没写）：**注册表命中优先于环境变量** ⇒ 已 `register()` 的 ref
**不会**因环境变量被清空而变成不可解析，撤销这个面必须 `unregister()`。

## 为什么这样做

- 这三条是**读代码容易看漏**的：`self._environment = environment if environment is not None
  else dict(os.environ)` 一行里**同时**有两种语义（传引用 / 拷贝），不实测很容易把
  「传映射的测试行为」当成「生产行为」，写出一个**验证不了生产**的判据。
- 它直接决定 runbook 与门的行为口径：**生效边界是「新构造 resolver 的时机」**，
  所以「轮换/撤销 ⇒ 重启生效」（§3）是对的，而「进程内改环境变量即生效」是错的。
- 附带一条**平台**事实：`os.environ` 在 Windows 上查找**大小写不敏感**，但解析器拷贝出来的是
  **普通 dict**（大小写敏感）⇒ `credential_ref` 与环境变量名必须**逐字**一致，
  写错大小写会**静默**变成「凭据不可解析」（门关、不报错）。

## 怎么做与复现

```bash
# 语义（不读真实值：用虚构值）
uv run --frozen --no-sync python -B -c "
import os
from adapters.relay.credential_resolver import EnvCredentialResolver
ref='LLM_MAIN_KEY'
inst = EnvCredentialResolver()          # 生产路径
os.environ.pop(ref, None)               # 撤销来源
print(inst.has(ref))                    # True  ⇒ 快照（旧实例看不到撤销）
print(EnvCredentialResolver().has(ref)) # False ⇒ 新构造的才看到
"
```

- **判据**：`tests/architecture/python/test_live_credential_lifecycle_same_source.py`
  （20 用例，含上面三条 + 注册表面 + 名字大小写两条边界）。
- **文档**：`docs/integration/LIVE_MODEL_RUNBOOK.md` §8 的三行表格是这一节的同源版本。

## 适用边界

- **适用于**：任何构造 `EnvCredentialResolver` / `RegistryCredentialResolver` 的地方——
  长生命周期实例（API 进程、装配好的 deps）**不会**跟随环境变化；要「换值即生效」必须
  走**新实例**（新进程、或每次新建）。
- **不适用于**：`resolve()` 的值语义与错误模型（那是另一回事，本条目不讲）。
- **不要**据此认为「凭据会持久化」：注册表是**内存**字典，进程结束即消失（§3）。
  相关：[[MEM-20260920-098]]。

## 来源

- 实测：2026-09-21，用虚构值（`fabricated-value-for-semantics-only`）驱动，**未读真实凭据**
- 更正对象：`.cursor/plans/goals/GOAL-20260920-009-live-sample-and-anthropic-surface-closure.md`
  的 EC-05 判定细则「轮换 / 撤销」两条
- 复检：`.cursor/plans/rechecks/RECHECK-20260920-125-credential-lifecycle-runbook.md`
- 计划：`.cursor/plans/tasks/PLAN-20260920-125-credential-lifecycle-runbook.md`
