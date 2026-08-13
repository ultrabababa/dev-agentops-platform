# L1 Case Subset Debug Runs

Case Subset Debug Run 用于在冻结的 `triage-suite-v1` 中显式选择少量 Case，执行 L1 `full_context_one_shot` 诊断并预览 Case Metric Vector。它是探索性调试入口，不是 Formal Evaluation、Quality Gate qualification、Leaderboard、Badcase 或 regression 结论。

仓库提供了一个受版本控制的 Debug condition：

- Matrix：`evaluation/matrices/l1-case-subset-debug-v1.json`
- Condition：`l1-case-subset-debug-v1`
- Runtime：`full_context_one_shot`
- Suite：`triage-suite-v1`
- Model：`siliconflow / Qwen/Qwen3.5-4B`
- Prompt：`structured-triage-task-contract-v1`

## 运行命令

先配置 `SILICONFLOW_API_KEY`，再显式重复 `--case`：

```bash
.venv/bin/devagentops eval debug \
  --matrix evaluation/matrices/l1-case-subset-debug-v1.json \
  --registry components/registry.json \
  --suite evaluation/suites/triage-v1/suite.json \
  --condition l1-case-subset-debug-v1 \
  --case bugswarm-traccar-170287308 \
  --case bugswarm-apache-struts-190697114 \
  --database .devagentops/devagentops.db \
  --artifacts-dir .devagentops/evaluation-artifacts
```

完整 eval doctor 在 provider 初始化、SQLite 初始化和 artifact 写入之前执行。Case 选择不能为空，不能重复，也不能包含 Suite 外 ID。即使 `--case` 的输入顺序不同，实际执行与输出仍按 Suite Manifest 顺序排列。

## 结果语义

每个选择的 Case 都会得到一个独立 outcome：

- `scored`：provider 返回了结果；即使 Structured Triage Report 无效，仍保留验证结果和 Case Metric Vector，作为模型质量观察。
- `execution_failed`：context、provider、transport、protocol 或 Runtime 执行失败；该 Case 没有报告和分数，后续选择的 Case 继续执行。

全部 Case 可评分时，Run 状态是 `completed`，CLI 返回 `0`。只要存在 Case 执行失败，Run 状态是 `completed_with_case_failures`，CLI 返回 `1`，但 stdout、SQLite、JSON 和 Markdown 中仍保留完整结果。输入、预检或 Run 级失败返回 `2`。

SQLite 的 `evaluation_case_outcomes` 表可查询全部 Case outcome；只有 `scored` Case 会进入 `evaluation_reports` 和 `evaluation_case_scores`。

## Metric Vector Preview

JSON 与 Markdown artifact 都包含：

- overall Metric Vector preview；
- per-Failure-Type Metric Vector preview；
- selected/scored/failed Case 数和 Suite weight；
- `complete` 或 `incomplete` coverage。

聚合只使用 `scored` Case 的 Suite weight。执行失败不会被隐式当作质量 `0`。Debug Run 不计算 composite score，也不产生 Quality Gate 结果。

## 信任边界

Runtime 输入仍由 `PublicCaseView` 和 Agent-visible Physical Evidence 构造。Expected Answer、required/optional Evidence Ground Truth、scorer labels 和 curator reasoning 不进入 provider 请求。Evaluator-only 数据仅用于模型返回后的确定性评分与 preview 分组。
