---
id: MEM-20260927-149
title: "枚举式判据必须从代码枚举（不是手写清单），且按压要能指出「谁被移出保护」——两口径互证 + 三轮按压实测"
status: ACTIVE
created_at: 2026-09-27
updated_at: 2026-09-27
scope: repository
confidence: 0.9
review_after: 2027-03-27
source_plans:
  - .cursor/plans/tasks/PLAN-20260927-201-auth-cannot-be-bypassed-on-the-write-face.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260927-202-auth-cannot-be-bypassed-recheck.md
supersedes: []
tags: [adversarial-self-check, enumeration-from-code, pressable-criterion, write-face-auth, goal-021, ec-01]
---

## 做了什么

对 GOAL-019/020 的写面认证做**对抗性自检**（GOAL-021 EC-01），交付
`tests/api/test_write_face_cannot_be_bypassed.py`（274 行 / 18 例）与
`RECHECK-20260927-202`。三条事实被实测：

1. **枚举来自代码**：判据内调用 `create_app()` 读 OpenAPI `paths` 取得写面端点，
   **不用**手写清单；`_MEASURED_MUTATING_COUNT = 60` 是**漂移告警线**而非保护面定义。
2. **两口径互证 = 60**：AST 扫 `@router.<m>` 装饰器（含 `ast.AsyncFunctionDef`）= 60，
   OpenAPI mutating 操作 = 60，覆盖 **17** 个 router 文件。
3. **按压 3/3 红**（逐字节复原，sha256 `ca03dac3…`）：
   PRESS-1 删 `DELETE` ⇒ **3 failed**；PRESS-2 加 `GET` ⇒ **4 failed**；
   PRESS-3 继承 `_is_analysis_post` 豁免 ⇒ **10 failed**（8 个分析类路径逐个红）。

## 为什么这样做

- **手写清单有两个真实失效模式**：**漏网**（新增端点没人补清单）与**过期**（删了端点后
  清单还在断言不存在的路径）。从**被守护对象自己的声明**枚举，这两类失效都不可能出现。
- **按压要挑「能点名的形态」**：只按总量变化判，无法区分「保护面被破坏」与「枚举算错了」。
  AST 口径能**按文件定位**（`team_protocol.py: 7` / `ops_control.py: 6` …）⇒ 按压可点名。
- **PRESS-3 是最承重的一轮**：它判的是**推理关系**为假——
  「幂等面放行 ⟹ 认证面放行」被**结构**（AST 不引用例外集）与**行为**（8 个端点逐个 401）
  **双重**否定，而不是靠一句注释声明。
- **必须含 `ast.AsyncFunctionDef`**：本仓路由几乎都是 `async def`，只扫 `FunctionDef`
  会得到 **6**（而不是 60）——一次实打实的漏枚举（建档期首版即如此）。

## 怎么做与复现

```bash
# 枚举两口径对账（只读）
PYTHONPATH=. uv run --frozen --no-sync python -B scratch/goal021-ec01-probe-enumeration.py

# 按压的可证伪性（先于判据写；按压①⇒404、按压②⇒422、基线 401、复原 401）
PYTHONPATH=. uv run --frozen --no-sync python -B scratch/goal021-ec01-probe-press-shape.py

# 判据本体
uv run --frozen --no-sync python -B -m pytest tests/api/test_write_face_cannot_be_bypassed.py -q
```

**按压形态（内存态，改后即复原；须 `sha256` + `git diff` 复核）**：
①`_MUTATING_METHODS` 去掉 `DELETE`；②加入 `GET`；③认证面加
`if request.method == "POST" and _is_analysis_post(request.url.path): return await call_next(request)`。
**逐轮必须报「实际判红集合」**（哪些用例红了），不能只报红没红。

## 适用边界

- 覆盖范围**只限控制面 app**：worker 网关是独立 app（`create_worker_app`），
  实测控制面 app 的 35 条路由里**零** worker 路由。本判据**不**覆盖 worker 面。
- 枚举覆盖的是 **app 声明过的端点**：绕过 FastAPI 路由的写（SSE 内副作用、
  后台调度器触发的写）**不在**枚举面内 ⇒ **不覆盖**这类路径。
- 按压是**内存态**破坏，证明「判据对这类破坏敏感」；**不**证明「CI 会拦住这类提交」——
  后者由判据本身常驻 CI 覆盖。
- 判据中的 token 是**合成假值** ⇒ **不**验证真实 token 的熵 / 长度 / 轮换行为。
- **本判据证明「已声明的边界成立」，不能证明「不存在未声明的缺口」。**

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260927-201-auth-cannot-be-bypassed-on-the-write-face.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260927-202-auth-cannot-be-bypassed-recheck.md`
  （`PASS_WITH_WARNINGS`，`W-1`…`W-5`）
- 取证脚本：`scratch/goal021-ec01-probe-enumeration.py`、
  `scratch/goal021-ec01-probe-press-shape.py`
- 相关：`MEM-20260926-143`（认证面复用分类）、`MEM-20260926-141`（判据自身恒真）
