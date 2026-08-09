# Oracle Evidence Diagnostic Condition 与 Agent-System Realization Gap

本文定义 DevAgentOps V1 Evaluation Methodology 中的 Oracle Evidence Diagnostic Condition（简称 Oracle Evidence Condition）。它回答一个受控问题：

> 当经过 Human Review 的正确证据已经放到固定模型面前时，这个模型能否按相同的诊断与报告契约完成当前 Case？

该设计已经接受，但当前仓库尚未实现 Oracle Runner、Matrix Schema、配对校验或 Gap Report。它属于未来独立的 [Issue #19](https://github.com/ultrabababa/dev-agentops-platform/issues/19)，不增加第三个 V1 Product Runtime。Issue #15 仍不承担 Oracle Runtime，但其 Formal Case construction/freeze 必须先等待 Offline Case Schema V2 实现。

## 1. 研究问题与能力边界

正常 Agent 的诊断结果同时受两段链路影响：

```text
Evidence acquisition
→ Evidence selection and context construction
→ Diagnostic reasoning and report synthesis
```

Fixed Pipeline、ReAct、Retrieval、Prompt、Tool Policy 与 Model Ablation 可以比较完整系统，但一次失败仍可能混合：

- 模型已经具备条件化诊断能力，但 Agent 没有找到、筛选、组织或使用关键 Evidence；
- Evidence 已经充分，模型仍无法形成正确诊断；
- Prompt、Report Contract、Scorer 或 Case 本身存在问题。

Oracle Evidence Condition 只移除普通 Evidence Discovery 的难度。它估计的是固定模型在特定 Prompt、Report Contract 和 reviewed evidence packaging 下的条件化诊断上界，不证明模型具有脱离这些条件的普遍推理能力。

## 2. Oracle Evidence Condition 契约

### 2.1 应保持一致的变量

Oracle 与每个被配对的正常 Agent Condition 应保持：

- 相同 Evaluation Suite Version、Case Version 与 Case Weight；
- 相同 Model Provider、Model/Snapshot 与上下文上限；
- 相同 Temperature、Top-p、Seed（若支持）、停止条件和其他 Inference Settings；
- 相同诊断任务 Prompt、Structured Triage Report Schema 和输出 Token Budget；
- 相同 Evaluation Method、确定性诊断 Scorer 与 Report Validation；
- 相同 Evidence 内容版本、Context Truncation Policy 和重复运行策略。

唯一计划内干预是 Evidence Delivery：Oracle 绕过普通 Agent 的检索、工具选择与证据发现，直接提供由可信 Evaluator 在运行时派生的 reviewed evidence input。由于 Runtime Wrapper 或 Tool Loop 无法完全相同，任何不可避免的差异都必须进入 Effective Condition、Condition Fingerprint 和 Run Manifest。除 Evidence Delivery/Discovery 外仍存在行为差异时，结果可以保留为实验观察，但不得计算正式 Realization Gap。

### 2.2 可以提供的内容

Oracle 输入只包含从 `evaluator/required-evidence.json` 的 `required_evidence_ids` 经 Canonical Evidence coordinates 解析回 Physical Artifacts 的 Evidence Item：

- Stable Evidence ID；
- 对应 `physical-artifacts/raw.log` source span 的 resolved content；
- 对应 manifest-declared repository file source span 的 Path 与 resolved content；
- 将来若允许 Derived Evidence，必须保留到稳定来源或 Source Span 的 Provenance，且不能含 Evaluator 总结。

Evidence 使用确定性顺序和固定 Envelope。Stable Evidence ID 可以保留，因为候选报告仍需按正常 Schema 引用证据；模型不得看到“这是 required 标签”或选择理由。Oracle 输入是确定性的运行时派生结果，不冻结成 `oracle-evidence.json`，也不维护另一份可能与 Physical Artifacts 漂移的 copied pack。

### 2.3 绝对禁止提供的内容

- Evidence Ground Truth、Expected Answer 文件或任一答案字段；
- Primary/Acceptable Failure Type；
- Expected Summary、Root Cause 或 Recommended Action；
- `required`/`optional` 标签、未命中 ID、Scorer Label 或 Quality Gate 答案；
- Curator/Reviewer Reasoning、Evidence Selection Rationale 或人工摘要；
- Fix Commit、Passing Revision 或已验证修复内容；
- Reasonable Tool Path、参考轨迹、Badcase Reason 或历史 Eval 结果。

“被选中的内容天然更相关”是 Oracle 干预本身；额外的排序暗示、标题、重点标注、解释或答案式重写不是该干预的一部分，属于 Leakage。

## 3. Minimal Sufficient Evidence Set

每个 Oracle-eligible Case 的 `required_evidence_ids` 所解析出的 Evidence Item 应形成经过 Human Review 的 Minimal Sufficient Evidence Set。

### 3.1 Sufficiency

在固定 Model、Diagnosis Prompt、Report Contract 和 Inference Settings 下，该集合必须包含推导 Expected Diagnosis 所需的事实信息。Reviewer 应能把 Expected Failure Type、关键 Root Cause 事实和最低 Recommended Action 依据追溯到集合中的来源内容；不能依赖 Expected Answer 文本、隐藏仓库状态、Passing Revision 或 Reviewer 的额外解释。

Sufficiency 是数据设计与人工审阅结论，不以“某次模型成功输出答案”作为循环补证标准。否则 Oracle 结果会反向污染 Evidence Curation。

### 3.2 Minimality

Reviewer 应执行删除检查：集合中每一项至少支持一个不可替代的关键事实或必要消歧；移除任一项后，剩余集合不再被审阅为足以推导 Expected Diagnosis。若多个 Evidence Item 完全等价，应只保留一个，或记录为什么它们分别不可替代。

Minimal 不等于越短越好，也不要求删除诊断所需的上下文。目标是避免把无关上下文、重复证据或答案式摘要包装成“Oracle”。

### 3.3 Answer non-encoding

Required Evidence 必须是 source-faithful 的日志、配置、源码或测试内容，并通过 Canonical Evidence source span 与 resolved hash 保留到 Physical Artifact 的 Provenance。Project Knowledge 不属于当前 Formal Case V2 Evidence Universe；未来若作为独立 Runtime/Retrieval ablation 输入，不自动成为 Case Required Evidence。Evidence 文本不能由 Curator 改写为 Failure Type、Root Cause 或 Fix 结论；文件名、Envelope、排序和注释也不能传递这些结论。

一旦 Required Evidence 集合或内容被修正，必须创建新的 Case/Suite Version 并更新 Fingerprint，不能静默修改已冻结 Formal Suite。

## 4. 实验条件

| 条件 | Evidence Acquisition | 主要回答的问题 |
|------|----------------------|----------------|
| A. Oracle Evidence | 直接提供 Human-reviewed Minimal Sufficient Evidence Set | 移除发现难度后，固定模型能否完成诊断？ |
| B. Fixed Pipeline | Deterministic fixed flow、heuristic 或 fixed selection | 固定 Workflow 能兑现多少诊断能力？ |
| C. Retrieval | 在 Canonical Evidence corpus 上 static query/top-k augmentation | Retrieval 本身带来多少 uplift？ |
| D. ReAct Agent | Agent 自主 adaptive search/open、选择 Tool 与 Evidence | Agentic Investigation 能否超过 static retrieval？ |
| E. Improved Agent | Retrieval、Context、Tool Policy、Verifier 或 Planning 等明确版本化的受控改进 | Agent-system Engineering 带来哪些按 Case 可解释的增益？ |

E 不是一个永久、可变的“最佳系统”标签。每个 Improved Agent 必须是 Matrix 中明确版本化、可复现的 Candidate 或 Ablation Condition。各条件共享的 Evidence Universe、Canonical Evidence coordinates 与 access semantics 由 [Formal Evaluation Methodology：Evidence Universe 与 Access Conditions](formal-evaluation-methodology.md) 定义。

## 5. Agent-System Realization Gap

V1 不定义 Composite Score，因此 Gap 也是 Metric Vector。对任一 higher-is-better 诊断指标 `m`：

```text
realization_gap(case, m)
  = oracle_score(case, m) - agent_score(case, m)
```

必须至少输出：

- 每个 Case、每个诊断指标的 Oracle/Agent 值与差值；
- 每个 Failure Type、每个指标的配对聚合；
- 全 Suite、每个指标的配对聚合；
- Pairing Key、Condition Fingerprint、Canonical Run 或 Stability Sample 身份；
- 不可配对原因与所有非计划内条件差异。

Gap 不应把 Retrieval Evidence Hit、Tool Path Validity、Step/Tool Call Count、Cost 或 Latency 合入“模型诊断能力”。这些指标仍应单独报告，用来解释正常 Agent 为什么没有兑现 Oracle 条件下显示的诊断表现。

在当前四项单 Case Scorer 中，Classification 与 Report Evidence Citation 可以提供早期诊断信号，Required Fields Completeness 只能说明结构完整性。正式实现前还需要版本化的 Diagnosis Pass Predicate；不能把当前任意单项分数自行称为 Case PASS。

## 6. Case-level 结果解释

| Oracle | Agent | 解释与后续检查 |
|--------|-------|----------------|
| PASS | FAIL | 强烈提示 Agent-system Opportunity；检查 Retrieval、Context Construction、Tool Use、Planning、Verification、Report Synthesis 与 Stopping。 |
| PASS | PASS | 模型在 Oracle 条件下表现出诊断能力，且当前 Agent Condition 成功兑现。继续查看成本、稳定性和是否存在多余路径。 |
| FAIL | FAIL | 可能是 Model Capability Bottleneck；先审计 Oracle Evidence 完整性/最小性、Prompt/Report Constraint、Scorer、Truncation 与 Variance。 |
| FAIL | PASS | Evaluation Audit Signal；优先检查 Run Variance、Evidence Construction、Prompt/Wrapper Difference、Context Truncation、Pairing 与 Scorer Consistency。 |

PASS/FAIL 必须来自相同 Evaluation Method 中版本化的 Diagnosis Pass Predicate。上述四象限是分析辅助，不是独立评分方法，也不能把相关性表述为确定因果。

## 7. 与现有契约的关系

- 与 ADR 0112 一致：Oracle 是 Diagnostic Condition，不是第三个 Product Runtime。
- 与 ADR 0113 一致：它是受控配对实验；因为 Condition Fingerprint 必然不同，所以属于专门的 Pair Analysis，而不是普通 Direct Leaderboard Ranking。
- 与 ADR 0115/0123/0126 一致：Physical Artifacts、Canonical Coordinates、Evidence/Diagnosis Ground Truth、Provenance、Sanitization 和 Reviewer 状态随 Case/Suite 冻结。
- 与 ADR 0116 一致：输出 Metric Vector，并按 Failure Type 分析，不生成单一综合 Gap。
- 与 ADR 0118/0122 一致：正常 Agent 仍不能检索 Expected Answer；Oracle 只获得来源 Evidence Content，不获得 Evaluator Label、Answer Text 或 Reasoning。

## 8. 当前边界与未来实现

当前仅完成方法与文档决策，尚未实现：

- Matrix 中的 Oracle Evidence Delivery Schema；
- Oracle Pack Builder/Resolver 与 Leakage Guard；
- Minimal/Sufficient Human Review Metadata 与 Doctor Validation；
- Model Runner、Pair Validator、Diagnosis Pass Predicate；
- Per-Case/Per-Failure-Type Gap Report 与 Variance Audit。

未来 Oracle Runtime 实现由 [Issue #19](https://github.com/ultrabababa/dev-agentops-platform/issues/19) 承担，并在 Formal Runner 与真实 Model Condition 具备后接入。Issue #15 仍只负责平衡 Formal Suite 的 Case/Evidence Ground Truth/Expected Answer/Provenance/Sanitization Curation，但必须等 Schema V2 Loader 与验证契约落地后再继续构建和 Human-freeze：现有五个 Batch-1 V1 packages 仅是 calibration drafts，剩余十五个不得按 V1 扩展，V2 落地后先重建 B04。Issue #16 继续只负责 deterministic Pipeline Baseline tracer bullet；它们都不承担 Oracle Runtime 或 Gap Analysis。

## 9. 相关来源

- [ADR 0124: Oracle Evidence Diagnostic Condition](../adr/0124-oracle-evidence-diagnostic-condition.md)
- [ADR 0113: Evaluation Comparison Model](../adr/0113-evaluation-comparison-model.md)
- [ADR 0115: Evaluation Suite and Case Artifacts](../adr/0115-evaluation-suite-and-case-artifacts.md)
- [ADR 0116: Metrics, Quality Gate, and Leaderboard](../adr/0116-metrics-quality-gate-and-leaderboard.md)
- [ADR 0118: Retrieval Corpus and Evidence Scope](../adr/0118-retrieval-corpus-and-evidence-scope.md)
- [ADR 0122: Structured Report and Evidence Contract](../adr/0122-structured-report-and-evidence-contract.md)
- [ADR 0125: Formal Evaluation Evidence Universe and Access](../adr/0125-formal-evaluation-evidence-universe-and-access.md)
- [ADR 0126: Offline Case Schema V2 Physical Artifacts and Canonical Evidence](../adr/0126-offline-case-schema-v2-physical-artifacts-and-canonical-evidence.md)
- [Formal Evaluation Methodology：Evidence Universe 与 Access Conditions](formal-evaluation-methodology.md)
- [Structured Triage Report 校验与单 Case 确定性评分](structured-triage-report-and-per-case-scoring.md)
- [Evaluation Matrix、Component Registry 与 Offline Evaluation Suite](evaluation-matrix-and-component-registry.md)
