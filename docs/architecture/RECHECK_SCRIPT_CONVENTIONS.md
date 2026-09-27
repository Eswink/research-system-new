# 复检脚本编写规范（Recheck Script Conventions）

**GOAL-20260928-022 EC-01 / EC-03 的交付物**。本页把 GOAL-020 / GOAL-021 两次**手工补跑**
两树对照时踩过的环境坑固化成条款，并给每条挂上**判据或可复跑检查**——
**规范不得只是散文**：一条没有被任何东西检查的「规范」，等于没有。

落点约定：**可复用入口进 `tools/`**（`scratch/` 在 `.gitignore` 里 ⇒ 放那里的东西
**不算交付**，只能当判词归档，且**必须在记录里引用**）。判据进 `tests/tooling/`
或 `tests/architecture/python/`（两者都落在 m0 的 `python/tests` 收集面内 ⇒ m0 条数不变）。

## 收口复检必须两树

**条款**：任何**收口复检**（GOAL 的收口 cycle）**必须**对「**当前树** + **干净 checkout**」
各跑一次**同一组断言**，并把两路判词**逐行比对**。只跑一路、或跑了一路而结论「看起来一样」，
**都不成立**——第二路证明的是「**提交后的树**也成立」，即排除「结论依赖工作树里的未提交产物 /
本地残留」这类可能。

**入口**：`tools/two_tree_recheck.py` —— 它只认两棵树，**没有单树模式**；
拿不到干净树就非 0 退出，**绝不**降级成「只跑当前树的 PASS」。
**判据**：`tests/tooling/test_two_tree_recheck_entry.py`。

**为什么写成条款而不是一次性的手工操作**：GOAL-021 的 EC-05 条款①**写明了**两路，
首轮却**只跑了一路**、既未登记也未在「未复核的面」里说明，却随该 EC 记了 PASS ⇒
被完成核验判负（`RECHECK-20260927-210` 的 `W-0`）。缺陷不在**有没有跑**，
而在**没有任何东西保证它下次会被跑**。

## 六条环境口径

| # | 口径 | 要求（坑的形态） | 检查 |
| --- | --- | --- | --- |
| ① | **共用解释器** | 两棵树都用**主树**的解释器（等价 `uv run --frozen --no-sync`）。干净 checkout **没有**自己的 `.venv`；现场建会超时，而且那等于在比**两套环境**。 | 判据：`test_both_trees_use_the_same_interpreter`（两树记录到的解释器相同且等于调用方） |
| ② | **`--verdict-only` 纯度** | 只比**判词行**。整份输出含耗时与路径 ⇒ 两棵树天然不同。出现非判词行即**拒绝服务**，**不得**静默过滤——静默过滤会把真差异一起丢掉。 | 判据：`test_impure_output_is_refused_not_filtered` |
| ③ | **文本 vs 二进制读写** | 做**按压 / 复原**的脚本必须用 `read_bytes` / `write_bytes`。`pathlib.write_text` 在 Windows 会把 LF 写成 CRLF ⇒ raw `sha256` 变了，「逐字节复原」复核（正确地）判不一致；而 `git diff` 会因 `.gitattributes` 归一化**静默吞掉**该差异 ⇒ **`git diff` 不足以**充当逐字节证据。 | 可复跑检查（见下） |
| ④ | **落点断言（`--root` 参数化）** | 脚本**不得**硬编码仓库根；树由 `--root` 给定。否则「两棵树」就退化成「同一棵树跑两次」。 | 判据：`test_both_trees_agree_when_assertions_agree`（以**任意** `tmp_path` 目录为树跑通 ⇒ 未硬编码仓库根） |
| ⑤ | **进程卫生** | 起子进程的脚本 teardown **必须连整棵树**（Windows 用 `taskkill /T /F`）。GOAL-020 实测过一次留下 **96 个孤儿** python 进程并导致假红。 | 可复跑检查（见下） |
| ⑥ | **路径无关输出** | 判词行**不得**嵌入本树的绝对路径。两棵树的路径必然不同 ⇒ 这类判词不是「结论」而是「现场坐标」。**规范化成占位符会掩盖真差异**，所以选择**拒绝**而不是**改写**。 | 判据：`test_path_dependent_verdict_is_refused_not_normalized` |

### ③ 的可复跑检查

在 **临时文件**上复现行尾危害（**不得**拿仓库里的文件做这件事——那会把工作树写脏）：

```bash
uv run --frozen --no-sync python -B -c "import pathlib,tempfile; p=pathlib.Path(tempfile.mkdtemp())/'probe.txt'; p.write_bytes(b'a\nb\n'); before=p.read_bytes(); p.write_text(p.read_text(encoding='utf-8')); print('byte-identical', before==p.read_bytes())"
```

Windows 上输出 `byte-identical False` 即证实：**文本模式读写会改字节**
（`\n` 被写成 `\r\n`）⇒ 按压 / 复原必须走二进制。非 Windows 上若输出 `True`，
说明该危害在本平台不出现——**但规范仍然适用**（复检脚本要跨平台可比）。

### ⑤ 的可复跑检查

复检脚本跑完后确认**零泄漏**（Windows）：

```bash
tasklist | grep -i python || echo "no python processes"
```

判据侧的对应要求：入口在**超时**路径上必须连整棵树杀，而不是只 kill 直接子进程。

## 与既有门禁的关系

- 本页的条款**不改动**任何既有判据、门禁、阈值或放行面；它只**新增**过程要求与判据。
- 记录面的顺序条款仍以 `docs/architecture/LOCAL_GATE_PROTOCOL.md` 的
  「记录面覆盖」一节为准（该节由
  `tests/architecture/python/test_record_face_is_covered_by_the_gate.py` 钉住）。
- `tools/` **不在** `PRODUCT_ROOTS` 内 ⇒ 落在 `tools/` 的脚本**不被**
  ruff / mypy / 规模门禁覆盖。因此入口的**行为**必须由 `tests/tooling/` 的判据钉住，
  并且入口**自愿**遵守同样的规模与风格约束（无人检查不代表可以放松）。
