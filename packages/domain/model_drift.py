"""模型漂移判定（GOAL-20260920-008 EC-05 / AGENTS.md §4）。

中转站可能在**同一个 Model ID 之后替换真实模型**，所以「我配的是 `X`」与「provider 说
回来的是 `Y`」必须逐次对比，并把结论如实送上读面。本模块只做**纯判定**：

- 无 IO、无 provider 分支、无策略：输入两个字符串，输出三态 + 人读 detail；
- 比较规则**只有一处**（`assess_model_drift`），调用方一律取它的结论，不各自 `==` 一遍。

三态与「未知 ≠ 无漂移」的完整口径见 `ModelDriftState`（`packages/domain/enums.py`）。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.domain.enums import ModelDriftState


@dataclass(frozen=True, slots=True)
class ModelDriftAssessment:
    """一次对比的结论：三态 + 参与比较的两个原值 + 人读说明。

    `detail` 只包含两个模型标识（配置面与响应里的非敏感值），**不含**凭据、
    不含 provider 原始响应体、不含任何 header。
    """

    state: ModelDriftState
    declared_model_name: str
    returned_model_name: str | None
    detail: str

    @property
    def is_drift(self) -> bool:
        """**只有** `DRIFT` 为真——`UNKNOWN` 不是漂移，也不是「无漂移」。"""
        return self.state is ModelDriftState.DRIFT


def _clean(value: str | None) -> str | None:
    """只去首尾空白；不做大小写折叠、不做后缀/别名归一（见模块 docstring）。"""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def assess_model_drift(
    declared_model_name: str, returned_model_name: str | None
) -> ModelDriftAssessment:
    """对比登记的模型名与 probe 返回的模型标识，给出三态结论。

    - `returned` 为 `None` 或全空白 ⇒ `UNKNOWN`（未探到，**不是**一致）；
    - 去空白后精确相等 ⇒ `MATCH`；
    - 其余一切差异（含只差大小写）⇒ `DRIFT`，`detail` 同时点名两个原值。
    """
    clean_declared = _clean(declared_model_name)
    if clean_declared is None:
        raise ValueError("declared_model_name must not be blank")
    clean_returned = _clean(returned_model_name)

    if clean_returned is None:
        return ModelDriftAssessment(
            state=ModelDriftState.UNKNOWN,
            declared_model_name=clean_declared,
            returned_model_name=None,
            detail=(
                f"declared {clean_declared!r}; provider did not return a model identifier "
                "(unknown is not the same as no drift)"
            ),
        )
    if clean_returned == clean_declared:
        return ModelDriftAssessment(
            state=ModelDriftState.MATCH,
            declared_model_name=clean_declared,
            returned_model_name=clean_returned,
            detail=f"declared and returned agree on {clean_declared!r}",
        )
    return ModelDriftAssessment(
        state=ModelDriftState.DRIFT,
        declared_model_name=clean_declared,
        returned_model_name=clean_returned,
        detail=f"declared {clean_declared!r} but provider returned {clean_returned!r}",
    )
