"""实验事实 → 验收门输入（GOAL-014 EC-02 / F-11 的四维接线：**实验侧唯一生产者**）。

用户判词（取 A）要求四项的数据来源必须是**产品路径上已经真实产生的事实**，
**禁止编排层凭空构造**。本模块是实验那一侧的三个事实到门输入的**唯一**转换点：

- `metrics`  ← 域实体字段 `ExperimentRunResult.metrics`（实验**自报**的真实指标）；
- `tests`   ← **实验产物字节**（`experiment_result.json` / `stderr.log`），逐项算出；
- `policy_decision` ← 执行期 `GovernedExperimentExecutor._enforce_policy` **真的求值并执行**
  过的那组决定（**记录已发生的事实**，本模块不做第二次裁决）。

三条取样纪律（与 PLAN-20260924-160 的 D-1 / D-2 / D-5 同文）：

1. **只搬运**：任何一项都不得在这里被赋值成常量（例如 `{"pass": True}`）；
2. **缺维即 fail-closed**：取不到 ⇒ 返回空映射 / `None`，让域求值器给出它既有的恒判词
   （`metric … missing` / `no test results provided` / `policy decision unknown`）；
3. **每个布尔都带出处**：测试项的**名字**就是它的出处（哪件产物、哪个字段、什么取值），
   失败时点名到具体那一项，而不是一个含糊的 False。
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from packages.application.experiments.types import ExperimentExecutionOutcome
from packages.application.ports.artifact_store import ArtifactStore
from packages.domain.enums import PolicyDecision
from packages.domain.experiments import ExperimentRunResult

#: 自报结论里表示「实验科学上跑成了」的取值（与 `experiment_run_output_v1` 的闭集一致）。
_SUCCEEDED = "SUCCEEDED"
#: 执行期逐能力决定 → 门要的单一取值的**保守**合成序（越靠前越不宽松，先说先算）。
_LEAST_PERMISSIVE_FIRST = (
    PolicyDecision.DENY,
    PolicyDecision.REQUIRE_APPROVAL,
    PolicyDecision.ALLOW_WITH_CONSTRAINTS,
    PolicyDecision.ALLOW,
)


def metric_inputs(result: ExperimentRunResult | None) -> dict[str, Decimal]:
    """实验自报的**数值**指标 → `CriterionInputs.metrics`。

    只收 NUMBER 类（域实体已把它归一成 `Decimal`）：`METRIC_THRESHOLD` 比较的是数值，
    把字符串/布尔塞进去只会得到一个「类型不对的比较」；它们不是缺数据，而是**不适用**，
    因此在这里被如实排除，而不是被折算成 0 或 True。
    """
    if result is None:
        return {}
    values: dict[str, Decimal] = {}
    for metric_value in result.metrics:
        value = metric_value.value
        if isinstance(value, Decimal):
            values[metric_value.metric.name] = value
    return values


def recorded_policy_decision(
    decisions: Mapping[str, PolicyDecision],
) -> PolicyDecision | None:
    """执行期**已经发生**的那组逐能力决定 → 门要的单一取值（保守合成）。

    合成规则写死为「最不宽松的那一个说了算」：任一能力带约束 ⇒ 报带约束；全放行 ⇒ 放行。
    这不是第二次裁决——执行期已经按逐能力决定**强制**过（`DENY` / `REQUIRE_APPROVAL`
    会当场抛错、根本走不到验收门），这里只是把那次结果如实汇报成一个门认得的取值。
    空映射 = 治理包装没有运行 ⇒ `None` ⇒ 该判据维持 `policy decision unknown`。
    """
    if not decisions:
        return None
    for candidate in _LEAST_PERMISSIVE_FIRST:
        if candidate in decisions.values():
            return candidate
    return None


def reported_tests(
    outcome: ExperimentExecutionOutcome,
    artifacts: ArtifactStore | None,
) -> dict[str, bool]:
    """实验**自报产物** → `CriterionInputs.tests`（逐项带出处）。

    出处表（每项的名字就是出处，失败时逐字进判词）：

    | 项名 | 出处 |
    | --- | --- |
    | `experiment_result.json:declared_status_SUCCEEDED` | 该产物的 `status` 字段 == `SUCCEEDED` |
    | `experiment_result.json:metrics_declared` | 该产物的 `metrics` 是非空对象 |
    | `stderr.log:empty` | 该产物除空白外无内容（无错误输出） |

    **读不到报告本身**（没跑成 / 产物被拿掉）⇒ 返回**空映射**：这时的诚实结论是
    「没有自报结果可判」（域求值器给 `no test results provided`），而不是伪造一组
    「跑了但失败」的布尔。报告读得到时，每一项都由它的字节算出——`metrics` 缺失、
    状态非 `SUCCEEDED`、stderr 有输出都会**具名**判否。

    如实披露：本项是**实验自报**，**不是**独立跑测框架的结果；名字里带出处就是为了
    让读到判词的人一眼看到这一点。
    """
    report = _declared_report(outcome, artifacts)
    if report is None:
        return {}
    checks = {
        f"{_RESULT_NAME}:declared_status_{_SUCCEEDED}": report.get("status") == _SUCCEEDED,
        f"{_RESULT_NAME}:metrics_declared": bool(report.get("metrics")),
    }
    stderr = _artifact_text(outcome.stderr_artifact_id, artifacts)
    if stderr is not None:
        checks[f"{_STDERR_NAME}:empty"] = stderr.strip() == ""
    return checks


#: 产物名的字面量（与 `packages.application.experiments.types` 的常量同值；判词里要读得懂）。
_RESULT_NAME = "experiment_result.json"
_STDERR_NAME = "stderr.log"


def _declared_report(
    outcome: ExperimentExecutionOutcome,
    artifacts: ArtifactStore | None,
) -> Mapping[str, Any] | None:
    """读实验自报的报告对象；产物不在场 / 不是 JSON 对象 ⇒ `None`（= 没有可判的自报）。"""
    text = _artifact_text(outcome.result_artifact_id, artifacts)
    if text is None:
        return None
    try:
        parsed: Any = json.loads(text)
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _artifact_text(artifact_id: str | None, artifacts: ArtifactStore | None) -> str | None:
    """取产物文本；未配置制品店 / 没有该 id / 内容不在场 ⇒ `None`（缺件不是崩溃）。"""
    if artifacts is None or artifact_id is None:
        return None
    if artifacts.meta(artifact_id) is None:
        return None
    return artifacts.get(artifact_id).decode("utf-8", errors="replace")


__all__ = [
    "metric_inputs",
    "recorded_policy_decision",
    "reported_tests",
]
