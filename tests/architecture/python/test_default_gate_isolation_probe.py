"""默认门凭据隔离探针。

只被 `tests/architecture/python/test_default_gate_credential_isolation.py` 以**子进程**方式
执行：子进程带着凭据键启动，而本用例（未标记 `requires_live_llm`）必须**看不到**它们。
放在独立文件里是为了让「注入」严格限定在子进程内——父进程不得为了制造泄漏而污染自己会话的
进程环境（那样会把 `requires_live_llm` 的 live 用例的 skip 条件掀掉）。

**本用例也会被常规收集**（`tests/` 下的模块必须叫 `test_<subject>.py`，见
`tests/architecture/test_module_file_naming.py`）；两种跑法都成立：

- 常规跑（根 `conftest.py` 生效）⇒ 自动夹具抹掉未标记用例的凭据键 ⇒ 绿；
- `--noconftest` 跑（判据的按压）⇒ 夹具不存在 ⇒ 凭据键可见 ⇒ 红。
"""

from __future__ import annotations

import os

from tests.default_gate_credentials import LIVE_CREDENTIAL_KEYS


def test_default_gate_cannot_see_live_credentials() -> None:
    visible = [key for key in LIVE_CREDENTIAL_KEYS if os.environ.get(key) is not None]
    assert visible == [], f"默认门凭据隔离失效：{visible} 在未标记 live 的用例里仍可见"
