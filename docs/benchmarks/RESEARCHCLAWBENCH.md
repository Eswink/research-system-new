# ResearchClawBench 接入说明

> 本文档是 GOAL-20261120-116 的调研交付物，记录**如何把本仓接进这个外部基准**，
> 以及接入时必须如实登记的边界。**不记录分数**——分数只进证据 JSON 与 PRD §7.2。
>
> 调研日期 2026-11-20；来源均为公开页面，**未实测**。

## 1. 它是什么

| 项 | 内容 |
| --- | --- |
| 名称 | ResearchClawBench（RCB） |
| 发布方 | InternScience |
| 许可 | **MIT** |
| 规模 | **40 任务 / 10 学科**（每学科 4 个） |
| 论文 | arXiv **2606.07591**（2026-07-03） |
| 仓库 | `github.com/InternScience/ResearchClawBench` |
| 镜像 | Hugging Face `InternScience/ResearchClawBench`（另有 16 个社区任务） |
| 它测什么 | **AI coding agent 能否独立做科研**——从读原始数据到产出发表级报告 |

## 2. 任务结构

```
tasks/Astronomy_000/
  task_info.json        # 指令：问题、输入数据、期望交付物
  data/                 # 原始数据：.csv .h5 .pdb .sdf .xlsx .pt .npy .json .tex .ipynb .yaml .dat
  related_work/         # 参考论文
  target_study/         # 目标论文 + rubric + 图片（判分用，agent 看不到）
```

十个学科：Astronomy · Chemistry · Earth · Energy · Information · Life · Material ·
Math · Neuroscience · Physics。

## 3. 交付物契约

agent **无人干预**地工作，必须产出：

```
<workspace>/report/report.md
```

要求含：图、方法、结果、讨论。**不给思维链提示**。

## 4. 评分语义（必须逐字转述，不得美化）

- 由**多模态 LLM judge** 打分；输入是「指令 + AI 报告 + rubric」，**不含**目标论文。
- rubric 是加权清单（checklist），含文本项与**图像项**、技术关键词、逐项权重；
  每项按 0–100 打。judge 有两种模式：
  - **Mode A（目标优化，定量项）**：41–50 ≈ 与论文相当；51–60 ≈ 略好；91–100 = 突破。
  - **Mode B（诊断分析，定性项）**：41–50 ≈ 深度相当；71–80 ≈ 显著更深；91–100 = 原创洞见。
- **> 50 = 达到论文水平；> 70 = 超越。**
- 主分**没有 Pass@1 阈值**；另有 Pass@5 稳定性榜。
- 归一化：对每个 (task, agent) 取最好分。

### 公开读数（作为标尺，不是我们的成绩）

| 系统 | 分数 | 备注 |
| --- | --- | --- |
| InnoClaw (2.0) | **34.89** | GPT-5.5，公开榜第 2 |
| jiutian-DeepInsight | 28.38 | 33 个保留任务 |
| 其他参赛 | QinShi / Ligase / EvoLab / Open Science / EvoScientist 等 | 分数未在本轮取证中读到 |

README 原话：`every point above 50 is uncharted territory`。
**⇒ 满分不是现实目标；零分是有效读数。**

## 5. 运行方式（harness 侧）

```bash
git clone https://github.com/InternScience/ResearchClawBench
pip install -r evaluation/requirements.txt

# judge（外部付费模型；示例 gpt-5.1）
#   JUDGE_API_KEY / JUDGE_API_BASE / JUDGE_MODEL_NAME 写进 evaluation/.env

python -m evaluation          # 打开 http://localhost:5000
# 或批量：
python3 -m evaluation.cli_eval eval_configs/<your>.yaml
```

关键常量与限制：

| 项 | 值 |
| --- | --- |
| Docker/容器 | 仓库本身是 Flask + vanilla JS，**不含**容器定义；沙盒由 agent 自带 |
| Agent 超时（OpenClaw 预设） | **3600s** |
| 批量依赖的环境变量 | `SERPER_KEY` / `JINA_KEY` / `MINERU_TOKEN`（ResearchHarness 批量用） |
| 结果落点 | `workspaces/cli_runs/cli_<ts>_<rand>/eval_report_<batch>.md` |

## 6. 接入契约（本仓要满足的）

`evaluation/agents.json` 里每个 agent 是一条带占位的命令：

```json
{
  "name": "research-os",
  "command": ["python", "-m", "tools.rcb_agent", "--workspace", "<WORKSPACE>", "--prompt-file", "<PROMPT>"]
}
```

（占位符字面量是 `<PROMPT>` 与 `<WORKSPACE>`；以上形态以仓库 `agents.json` 为准，
接入时**必须**先读该文件确认字段名。）

### 6.1 本仓的适配器设计（GOAL-116 EC-02）

`tools/rcb_agent.py`：

1. 读 `<PROMPT>`（RCB 指令）→ 转成一次研究方向；
2. 用**产品组合根** `assemble(ApiSettings(db_path=...))` 启动（复用
   `tests/e2e/manuscript_chain_live_support.py:149` 的形态，**不补缝**）；
3. 跑完一次 run 后，把 canonical 里的 `research_report.md`（或 `manuscript.md`）
   **导出**到 `<WORKSPACE>/report/report.md`；
4. 退出码：产出成功 = 0；未产出 = 非 0（让 harness 如实记失败，而不是伪造空报告）。

**为什么必须走产品组合根**：绕过它直接调模型就不是评测本系统，而是评测某个模型。
这条是本仓「可审计」定位与基准的接缝。

## 7. 与现有能力的结构冲突（必须提前知道）

| 冲突 | 现状 | 影响 |
| --- | --- | --- |
| 任意分析代码 | `AUTHORED_ALLOWED_BY_DEFAULT = False`，实验相是**三个白名单脚本** | 任务要求自己写分析代码 ⇒ 不放开几乎必然零分 |
| 科学计算栈 | 沙盒镜像 `research-os-sandbox:m9-test` = `python:3.12-slim`，**无 numpy/pandas/scipy/matplotlib/h5py** | 连 `.h5/.npy` 都读不了 |
| 容器网络 | `network none` | **无法运行期 pip install** ⇒ 依赖必须烘进镜像 |
| 视觉 | `models.yaml` 零 `VISION` 声明 | 判分侧要图，但**我们的模型不需要看图**（图由脚本产出） |
| 运行时长 | 十一相真实 run 约 **29 分钟** | 3600s 够单任务，但没有余量 |

## 8. 数据与成本纪律

1. **数据不入库**：`.h5` / `.pt` 等可能很大（仓库自带 `rcb-clear` 回收空间 ⇒ 说明
   可回收量大）。按任务单独下载到 **gitignored** 目录，并记录文件 digest。
2. **judge 是付费调用**：每次评分一次。本轮总调用 = **1（基线）+ 1（能力后）+ 3（扩量）
   = 5 次**，不是 40 次。
3. **judge 凭据只在本机环境变量**：`JUDGE_*` **不得**进 `examples/config/**`、
   不得进 `.env` 之外的被跟踪文件。判据：`tests/loaders/test_free_model_only_policy.py`
   必须保持绿（`models.yaml` 只允许零价模型）。
4. **judge 模型名必须写进证据**：不同 judge 的分数不可直接比。

## 9. 声称边界

- 本文档的 RCB 细节全部来自**公开 README 与检索结果**，未 clone、未跑通。
- 榜单分数是**他人成绩**，不是本仓读数。
- 即使本轮拿到非零分，也**不宣称**「达到论文水平」（> 50 才是）。
- RCB 的 judge 是 LLM，不是人工评审；它的分数**不等于**论文录用结果。
- 任务的 `data/` 与 `target_study/` 有各自许可，**再分发前需单独确认**。

## 10. 引用

- InternScience. *ResearchClawBench* (2026). arXiv:2606.07591. MIT License.
- 仓库：`https://github.com/InternScience/ResearchClawBench`
- 数据集：`https://huggingface.co/datasets/InternScience/ResearchClawBench`
