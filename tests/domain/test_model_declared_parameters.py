"""模型**声明参数**（上下文窗口 / 思考强度）的域判据（EC-02）。

这两个值是**声明值**（用户/运维登记），不是探测结果，本版本也不发给 provider——
域层判据只钉住「承载 + 校验 + 词表」，读面与文档的诚实口径在别处判。
"""

from __future__ import annotations

import pytest

from packages.domain.enums import ThinkingIntensity
from packages.domain.models import ModelDefinition

WINDOW = 512000
LEVELS = {"MINIMAL", "LOW", "MEDIUM", "HIGH", "MAX"}


def _model(**overrides: object) -> ModelDefinition:
    payload: dict[str, object] = {
        "id": "model-agnes",
        "endpoint_id": "main",
        "model_name": "agnes-2.5-flash",
    }
    payload.update(overrides)
    return ModelDefinition(**payload)  # type: ignore[arg-type]


def test_declared_parameters_are_carried_verbatim() -> None:
    model = _model(context_window_tokens=WINDOW, thinking_intensity=ThinkingIntensity.MAX)
    assert model.context_window_tokens == WINDOW
    assert model.thinking_intensity is ThinkingIntensity.MAX
    # 序列化后仍是同一对事实（值不因往返变形）
    assert model.thinking_intensity.value == "MAX"


def test_declared_parameters_default_to_absent() -> None:
    """既有构造点不传这两个字段 ⇒ 保持 None（不凭空给默认值）。"""
    model = _model()
    assert model.context_window_tokens is None
    assert model.thinking_intensity is None


@pytest.mark.parametrize("value", [0, -1, -512000])
def test_non_positive_context_window_is_rejected(value: int) -> None:
    with pytest.raises(ValueError) as excinfo:
        _model(context_window_tokens=value)
    assert "context_window_tokens must be >= 1" in str(excinfo.value)


def test_intensity_vocabulary_is_vendor_neutral_levels() -> None:
    """级别是相对词（厂商中立）；`MAX` 承载用户声明的 Max。"""
    assert {member.value for member in ThinkingIntensity} == LEVELS
