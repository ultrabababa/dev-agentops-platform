# Formal Evaluation Methodology：Evidence Universe、Schema V2 与 Access Conditions

本文定义 DevAgentOps Formal Evaluation 中 Case 世界、证据坐标、Trusted Evaluator 边界和 Runtime 访问方式。它解决两个相连的问题：

1. Curator 不得在评测前把 Normal Agent corpus 裁成 minimal required evidence；
2. Physical Investigation Workspace 不得与 Canonical Evidence coordinates 或 Evaluator Ground Truth 混为同一份 Artifact。

本方法论与 Schema V2 三层设计已经接受，Schema V2 Loader、Fingerprint、Doctor、Scorer split 和 public leakage boundary 已实现。Runtime、Retriever、Tool、Index 与 Oracle Runner 仍未实现。Issue #15 的 B04 Schema V2 calibration 已通过 Human Review；在批量构造其余 Formal Cases 前，先校准并 Human-freeze suite-shared `Canonicalization Profile v1`。

## 1. 证据与信任模型

```mermaid
flowchart TD
    A["Physical Artifacts: source of truth"] --> B["Evidence Universe / Investigation Workspace"]
    A --> C["Source-resolved Canonical Evidence Units"]
    D["Trusted Evaluator: Required Evidence"] --> H["Evidence Scorer / Oracle Builder"]
    A --> H
    C --> H
    E["Trusted Evaluator: Expected Answer"] --> F["Diagnosis Scorer"]
    C --> G["Retrieval / Tool Observation / Trace / Citation"]
```

### 1.1 Evidence Universe

Evidence Universe 是一个 Formal Case 中真实存在、可被调查的信息空间。第一版 Formal Suite 的 Case Universe 严格等于：

```text
complete or naturally bounded historical CI/test log
+
bounded repository snapshot derived from the exact failing/relevant revision
```

它必须 authentic、frozen、offline、bounded but realistic，并保留自然邻近信息与 natural distractors。不能因为 Curator 已知答案就只保留 root-cause 附近内容，也不能为制造难度添加 synthetic irrelevant noise。

Universe 不要求整个 upstream repository 或无界 log history。合理 repository 边界可以是相关 module/subtree，以及其中完整的 source、config、test、dependency 和 build files。边界必须从 failure observation 出发，回答“一个合理 Agent 实际可能调查哪些真实文件”，而不是从 curator 已知 root cause 反向只保留答案文件。禁止只保留 root-cause file、只裁取 failure 附近 log、根据答案缩小 Universe、添加 synthetic distractors，或把 passing/fix artifacts 放入 Agent-visible workspace。

Exact revision 固定来源身份与因果上下文，但不要求 Case 中冻结的 bytes 必须与 upstream commit bytes 完全相同：必要时可以先执行 Human-reviewed、semantics-preserving sanitization，前提是不改变 failure causal semantics。Passing revision、fix、PR 与 history 可以供 curator 验证 causal chain，但只能存在于 evaluator/curator-only 流程。

Project Knowledge 仍是 DevAgentOps 的一般 Runtime 能力，但不是 Issue #15 Formal Case 的 Physical Artifact，也不属于当前 Schema V2 Evidence Universe。未来可把 versioned Project Knowledge 作为独立 retrieval/runtime input 或 ablation，不在本设计中加入 Case。

### 1.2 Investigation Workspace

Investigation Workspace 是 Evidence Acquisition Condition 提供给 Runtime 的 Evidence Universe 视图。Normal ReAct 概念上通过工具调查：

```text
physical-artifacts/raw.log
physical-artifacts/repository/*
```

例如：

- `search_log`；
- `open_log_range`；
- `list_files`；
- `search_repo`；
- `open_file`。

Workspace 本身不等于一次性 Prompt Context。Normal ReAct 不应在 episode start 获得完整 Canonical Evidence list、Required Evidence IDs 或 Expected Answer。L1 `full_context_one_shot` 是一个明确的非 Agentic diagnostic condition：它把完整 Agent-visible Evidence Universe 一次性序列化给模型，但仍不得看到 Evaluator artifacts；它不会改变 Workspace、Canonical Evidence 或 Trusted Evaluator 的边界。

### 1.3 Canonical Evidence Unit

Canonical Evidence Unit 是对 Physical Artifact 中 source span 的确定性稳定坐标。它是 measurement/citation coordinate system，不是 curator-selected evidence corpus，也不是 Retrieval Runtime 的强制 index chunk。它服务于 tool-result identity、trace observation、report citation、Retrieval Evidence Hit、Report Evidence Hit 和 Oracle resolution。

Physical Artifact 是唯一事实源；Canonical Unit 不能成为一份可独立漂移的事实副本。每个 unit 至少需要：

- stable、answer-neutral `evidence_id`；
- controlled physical source path；
- machine-readable source span；
- resolved content SHA-256；
- deterministic、source-faithful resolution。
- 对 Formal text Evidence Universe 的完整 coverage；
- 无 gaps、无 overlaps，且 boundary 不依赖 failure line、fix、Required Evidence 或 curator 判断。

示例方向：

```json
{
  "evidence_id": "log:ci-lines-0572-0601",
  "source": "physical-artifacts/raw.log",
  "start_line": 572,
  "end_line": 601,
  "content_sha256": "<sha256>"
}
```

```json
{
  "evidence_id": "repo:equals-avoid-null-check.java:lines-0401-0500",
  "source": "physical-artifacts/repository/src/main/EqualsAvoidNullCheck.java",
  "start_line": 401,
  "end_line": 500,
  "content_sha256": "<sha256>"
}
```

ID 描述来源或位置，不得编码 Failure Type、Root Cause 或 Fix。B04 calibration 的 repository partition 覆盖全部 6 个 physical files，共 `3050/3050` lines；这说明 Canonical coordinates 可以完整覆盖 realistic workspace，而不是只枚举 curator 选中的高价值 span。

后续 Formal Cases 最终必须使用同一个 versioned `Canonicalization Profile v1`，避免逐 Case 自由选择 50-line、semantic 或 200-line units。当前 candidate repository-text rule 是：从 line 1 开始、连续、无重叠、固定 `N` 行、末 unit 可不足 `N` 行、100% coverage、无 answer-dependent boundary adjustment。B04 的 `N=100` 仍只是待跨 Case calibration 的 candidate parameter，不是已全局冻结的 universal constant。Canonicalization Profile 可以按 artifact class 定义不同但同样确定性的规则；在 Profile freeze 前，不把 B04 的 log-stage partition 或 100-line repository partition 擅自推广为全 Suite 规则。

### 1.4 Canonicalization 与 Runtime Retrieval Chunking

Canonicalization 和 Retrieval Chunking 是两个独立的 version namespace 与实验职责：

```text
Physical Artifacts
    +--> Canonicalization Profile
    |       -> stable coordinates / identity / citation / scoring
    |
    +--> versioned Runtime Retrieval Chunker
            -> index / embedding / top-k / reranking
            -> retrieved physical spans
            -> map to overlapping Canonical Evidence IDs
```

Canonicalization 回答“模型实际观察到了哪一块真实证据”；Retrieval Chunking 回答“Retrieval Runtime 如何组织和搜索 Evidence Universe”。Chunk size、overlap、embedding、index、top-k 和 reranker 都是 Runtime/Evidence Acquisition Condition 参数。Runtime 可以独立切分 Physical Artifacts，但必须在 Trace 中保留实际 retrieved/observed physical spans，并记录其 overlapping Canonical IDs。Overlap mapping 只是 observation attribution 的候选坐标，不自动等价于 Required Evidence Hit；正式 Hit 规则必须在 Canonicalization Profile freeze 前校准。禁止默认 `Canonical Units = Retrieval index chunks` 或 `any overlap = full hit`。

### 1.5 Required Evidence 与 Expected Answer

Schema V2 把两类 Ground Truth 分离：

- `evaluator/required-evidence.json` 是唯一 Evidence Ground Truth，保存 Required/Optional Canonical Evidence IDs；
- `evaluator/expected-answer.json` 是 Diagnosis Ground Truth，保存 Primary/Acceptable Failure Type、Expected Summary、Expected Root Cause 和 Recommended Action 等诊断契约。

Required Evidence 是 Human-reviewed、hidden、inclusion-minimal sufficient subset。完整集合包含推导 Expected Diagnosis 所需的来源事实；移除任一项后，至少一个必要事实或消歧依据不可用。Canonical content 不得写入 evaluator-authored answer、scorer label、selection rationale 或 curator reasoning。

通常应满足：

```text
Normal Investigation Workspace >> Hidden Required Evidence subset
```

不要创建第二份 `oracle-evidence.json`。Required Evidence 只有一个 source of truth。

## 2. Offline Case Schema V2 三层目录

已实现的严格布局如下，三层语义不得合并：

```text
<case-id>/
├── case.json
├── physical-artifacts/
│   ├── raw.log
│   ├── repository-manifest.json
│   └── repository/
│       ├── src/...
│       ├── test/...
│       └── config/...
├── canonical-evidence/
│   ├── log-units.json
│   └── repository-units.json
└── evaluator/
    ├── required-evidence.json
    └── expected-answer.json
```

### 2.1 Physical Artifacts

`physical-artifacts/raw.log` 保存 complete or naturally bounded frozen failure log。`physical-artifacts/repository/` 保存来源于 exact failing/relevant upstream revision 的 bounded repository files，并保留真实相对路径。若源 artifact 含 credential、token、private identifier 或其他不允许的数据，可以在进入 Case 前进行 Human-reviewed、semantics-preserving sanitization；sanitization 不得改变 failure causal semantics。

```text
upstream exact revision
        -> if necessary: Human-reviewed semantics-preserving sanitization
        -> frozen Physical Artifact in Case Package
        -> Canonical Evidence source spans / hashes
        -> Case fingerprint
```

Agent/Runtime 实际调查的是 Case Package 中冻结后的 Physical Artifact，而不是重新读取 upstream revision。

`repository-manifest.json` 的职责是：

- 明确 snapshot membership；
- 记录真实 upstream repository identity 与 exact revision identity；
- 记录每个冻结文件在允许的 sanitization 之后的 path、SHA-256 与 byte size；
- 配合 provenance/sanitization metadata 记录发生了哪些允许的转换及其 Human review 状态；
- 进入 deterministic Case fingerprint coverage。

Loader 必须按 Manifest 验证 membership 和冻结后的 content，不得通过目录扫描静默决定 Formal Snapshot 包含哪些文件。Manifest 的 exact revision 字段证明来源，不要求 sanitized frozen artifact 与 upstream commit 逐字节相同。

### 2.2 Canonical Evidence

`canonical-evidence/log-units.json` 与 `repository-units.json` 引用 Case 中冻结后的 Physical Artifact path + source span + resolved content hash；source span 与 `content_sha256` 都针对 sanitization 后的 frozen artifact 计算。Runtime 可以在 Agent 实际检查 physical span 后，把 observation span 与 overlapping Canonical Evidence IDs 一起附到 Tool Result/Trace，供 attribution 与最终报告引用。

```text
Agent investigates physical world
-> Runtime maps observation to canonical coordinates
-> Report cites canonical coordinates
-> Evaluator compares against hidden required evidence
```

Canonical unit 文件不是 Normal ReAct 的 episode-start evidence menu。

Canonical unit 集合必须覆盖 Formal text Physical Universe，而不是只覆盖 Required/Optional Evidence。Runtime 独立产生的 retrieval/tool spans 可以跨越或小于 Canonical Unit；physical overlap mapping 必须与正式 Evidence Hit decision 分开保存/解释，避免只观察到 unit 边缘就获得完整 Required hit。

当前 Schema V2 Loader 验证已声明 unit 的 controlled path、manifest membership、合法 line span、ID/类型、resolved hash，以及 Ground Truth 对已知 ID 的引用。100% coverage、无 gaps/overlaps、answer-neutral boundary 与 shared Profile compliance 目前仍是 Case Construction/Human Review audit；bulk Formal construction 前需要 deterministic Profile generator/validator 或等价 machine validation。本阶段只记录要求，不扩大 Issue #22 或实现该工具。

### 2.3 Trusted Evaluator Artifacts

整个 `evaluator/` 目录属于 Trusted Evaluator boundary。Normal model-backed ladder conditions 和 ReAct model 不得直接读取它。Directory layout 是强物理约定；真正可见性仍由 Evidence Acquisition Condition 和 Runtime 强制执行并进入 fingerprint。

`required-evidence.json` 同时服务 Retrieval Evidence Hit、Report Evidence Hit、Oracle construction 和 Human evidence review。`expected-answer.json` 只服务 diagnosis ground truth 与 Scorer。

## 3. Runtime Visibility Matrix

| Artifact | ReAct model | Retrieval internals | Oracle builder | Trusted Evaluator |
| --- | --- | --- | --- | --- |
| `physical-artifacts/*` | through allowed tools | may read as configured | yes | yes |
| `canonical-evidence/*` | not exposed as complete list at episode start | used for identity/mapping；不要求作为 index chunks | yes | yes |
| `evaluator/required-evidence.json` | no | no | yes | yes |
| `evaluator/expected-answer.json` | no | no | no | yes |

Not every runtime gets identical access. Whether a condition has fixed selection, retrieval, search/open tools, or an adaptive loop is an experimental variable, not a Case-construction responsibility.

## 4. Runtime Capability 与 Evidence Acquisition Conditions

所有受控条件尽量固定 same Case、same Physical Evidence Universe、same Expected Answer、same scorer，以及 Agent/System ablation 使用的 same base model。主要差异是 evidence acquisition 与 runtime scaffold。

| Level / condition | Evidence access | 控制流 | 定位与主要问题 |
| --- | --- | --- | --- |
| L0 deterministic Pipeline | frozen deterministic access/selection | 程序固定，无模型 | Product Runtime baseline；无模型时固定流程能做到什么？ |
| L1 Full-context One-shot | 完整 Agent-visible Universe 一次性进入固定 Prompt | exactly one model call，无循环 | diagnostic；单次模型 reasoning 能做到什么？ |
| L2 Fixed Model Workflow | 固定、显式的 evidence/input flow | 程序决定多阶段调用、next stage 与 stop | diagnostic；fixed orchestration 带来什么？ |
| L3 Static Retrieval | versioned Runtime Chunker/index 返回 selected physical spans，并映射到 overlapping Canonical IDs | 程序固定，无 adaptive Agent loop | evidence-acquisition diagnostic；static retrieval 带来什么？ |
| L4 self-built ReAct | search/open/list 工具调查 Physical Investigation Workspace | adaptive decision/tool/observation/stop loop | 第一个 Agentic Product Runtime；adaptive control 带来什么？ |
| Oracle Evidence | Trusted Builder 直接解析 Required Evidence，绕过 normal discovery | 固定 diagnostic intervention | 正交于 ladder；关键证据已知时模型能否完成诊断？ |

L0–L5+ 是 capability-attribution ladder，不是强制 implementation order；L3 是否必须先于 L4 实现不冻结。V1 Product Runtime 仍只有 Fixed Pipeline 与 self-built ReAct，L1/L2/L3 只是 diagnostic/comparison conditions。L1 不得 silent truncation：如果完整 Agent-visible Universe 超出固定 context budget，截断后的 run 不能继续宣称为 full-context condition；具体 eligibility/preflight/alternative policy 由未来 L1 implementation Issue 决定。

当前 Matrix Schema 尚无可执行的通用 Evidence Acquisition/Delivery 字段。这些语义是未来 Condition 与 Run Manifest 必须显式 version 和 fingerprint 的 accepted design；本次文档决策不修改 Matrix/Registry schema，也不冻结未来字段名。Offline Case Schema V2 与 L0 `pipeline_baseline` tracer bullet 已实现；L1/L2/L3/L4 与 Oracle execution 尚未实现。

实验比较以 paired per-Case comparison 为基础：固定 same Case、same Physical Universe、same base model（适用时）、same Expected Answer 和 same scorer，只改变目标 Runtime/Evidence Acquisition Condition，再跨 Case aggregate。每个 Case Human Review 都必须检查各 ladder condition 与 Oracle 实际获得什么，以及 Case construction 是否给任一 condition 带来 curator-derived advantage，尤其是 search-space size、signal density、chunk granularity 或 answer exposure 的变化。

## 5. Oracle Evidence 是 Derived Runtime Input

Case 中不永久保存 pre-materialized Oracle content pack。Oracle Builder 执行：

```text
evaluator/required-evidence.json
        -> canonical-evidence/*
        -> physical-artifacts/*
        -> deterministic Oracle Pack Builder output
        -> fixed model
```

Oracle model 可以看到 resolved source-faithful content 与 normal Stable Evidence IDs，但不能看到：

- `required`/`optional` 标签或 `required-evidence.json`；
- `expected-answer.json`；
- Failure Type、Summary、Root Cause 或 Recommended Action ground truth；
- scorer label、curator reasoning 或 selection rationale。

## 6. Retrieval Evidence Hit 与 Report Evidence Hit

| Signal | 命中条件 | 回答的问题 |
| --- | --- | --- |
| Retrieval Evidence Hit | Run Trace 的 physical observation span 按已冻结 attribution rule 证明 Runtime/Agent 实际观察了 Required causal fact；不能只凭任意 overlap | 找到了吗？ |
| Report Evidence Hit | 最终 Structured Triage Report 合法引用 Required Canonical Unit | 报告使用了吗？ |

这可以区分没找到、找到但未使用、找到并引用。当前代码已让 `report_evidence_hit_rate` 从 V2 `EvidenceGroundTruth.required_evidence_ids` 读取分母，评分公式保持不变；Retrieval Evidence Hit 尚未实现。当前 Required-ID-only Ground Truth 是否足以无歧义判断“真正观察到必要事实”仍是 calibration question：若 partial overlap、跨 unit causal fact 或 unit breadth 使其不稳定，应记录为明确 limitation/follow-up design decision，而不是默认 any overlap 为 hit。

## 7. 条件结果解释

| 对比结果 | 优先解释与检查 |
| --- | --- |
| Oracle PASS + ReAct FAIL | 模型在关键证据已知时能诊断，但 Agent/System 没有成功获得、管理或使用证据；检查 retrieval、tool use、context、planning、report synthesis 与 stopping。 |
| L3 FAIL + L4 PASS | static/top-k retrieval 或 fixed flow 不足，多步 adaptive investigation 提供了额外价值。 |
| L2 FAIL + L3 PASS | 主要 uplift 与 static evidence acquisition 相关；不能据此归因于 Agent loop。 |
| L1 FAIL + L2 PASS | fixed multi-stage orchestration 提供了额外价值；仍不是 Agentic control 的证据。 |
| Oracle FAIL | 先审计 Oracle evidence completeness/minimality、prompt、report contract、scorer、truncation 与 variance；成立后才视为可能的 model reasoning bottleneck。 |

目标不是预设 ReAct 一定优于 Pipeline，而是在受控条件下区分 model reasoning、fixed orchestration、evidence acquisition 与 adaptive Agent control。Ladder 编号不要求实现或实验严格按序；跨越多个 level 的比较只能解释组合差异。完整 ladder 语义见 [Runtime Capability Ladder 与 Model-backed Diagnostic Conditions](runtime-capability-ladder.md)，Oracle Pairing 与 Realization Gap 解释见 [Oracle Evidence Diagnostic Condition 与 Agent-System Realization Gap](oracle-evidence-diagnostic-condition.md)。

## 8. Schema V2 与 Issue #15

Offline Case Loader 现在只支持 Schema V2。Schema V1 已有意识地退役，不保留 backward-compatible loader、mixed-schema Suite 或 migration framework；tiny fixture 已迁移到 V2。V2 把 repository Physical Artifact 与 Canonical Repository Evidence 分开，并把 Required Evidence 从 Diagnosis Ground Truth 中拆出。

Issue #15 的后续顺序更新为：

- 当前 5 个 Batch-1 Schema V1 Packages 只作为 calibration drafts；
- 不 Human-freeze 这些 V1 Packages；
- 不按 V1 继续构造剩余 15 个 Packages；
- B04 已用 V2 重建并通过 Human Review；
- 用 2–3 个已选且结构不同的 Case 校准 `Canonicalization Profile v1`，但不在本阶段构造它们；
- Profile Human-freeze 后，若最终参数改变则统一重建 B04 coordinates，再扩展到其余 Cases。

Issue #22 不修改任何 Issue #15 Package；现有五个 V1 drafts 根据既有 research/provenance/root-cause knowledge 重新构建，而不是自动转换。

## 9. V2 Formal Case Review Checklist

- Physical log/repository Universe 是否 authentic、frozen、offline、bounded but realistic？
- Repository Manifest 是否同时固定真实 upstream repository/revision identity，以及 frozen artifact 的 membership、path、size 与 file hash？
- 如有 sanitization，metadata 是否记录允许的转换与 Human review，且没有改变 failure causal semantics？
- Physical content 是否保留自然邻近信息且无 synthetic irrelevant noise？
- Repository boundary 是否从 plausible investigation neighborhood 出发，而不是从已知答案反向裁剪？
- Passing/fix/PR/history 是否仅用于 curator causal verification，没有进入 Agent-visible workspace？
- Canonical Units 是否 deterministic、source-faithful、answer-neutral，并能解析到受控 source span？
- Formal text Physical Universe 是否 100% 被 Canonical Units 覆盖，且无 gaps/overlaps？
- Canonical boundaries/IDs 是否遵循已冻结 Profile，而非按 failure/Required Evidence 调整？
- Resolved content hash 是否与 Case 中冻结后的 Physical Artifact 一致？
- `required-evidence.json` 是否是唯一 Evidence Ground Truth，且 hidden/minimal sufficient？
- Required 集合删除任意一项后是否确实失去必要 causal/disambiguation fact，而不只是“有帮助”？
- `expected-answer.json` 是否只保存 Diagnosis Ground Truth？
- Expected Diagnosis 是否由 authentic failure + failing/relevant revision 支持，并按 root cause 而非 surface symptom 分类？
- Visibility Condition 是否阻止 Normal Runtime 读取 `evaluator/`？
- Normal Workspace 是否明显大于 Required Evidence subset？
- Retrieval 是否用独立 versioned chunker，并把 physical observations 映射回 Canonical IDs，而非继承 curator-defined search space？
- paired comparison 是否保持 Case、Universe、model、Expected Answer 和 scorer 不变，仅改变目标 acquisition/runtime condition？
- Case、Provenance、Sanitization、Reviewer 与完整 Fingerprint Chain 是否一起冻结？

## 10. 相关决策

- [ADR 0115: Evaluation Suite and Case Artifacts](../adr/0115-evaluation-suite-and-case-artifacts.md)
- [ADR 0118: Retrieval Corpus and Evidence Scope](../adr/0118-retrieval-corpus-and-evidence-scope.md)
- [ADR 0122: Structured Report and Evidence Contract](../adr/0122-structured-report-and-evidence-contract.md)
- [ADR 0124: Oracle Evidence Diagnostic Condition](../adr/0124-oracle-evidence-diagnostic-condition.md)
- [ADR 0125: Formal Evaluation Evidence Universe and Access](../adr/0125-formal-evaluation-evidence-universe-and-access.md)
- [ADR 0126: Offline Case Schema V2 Physical Artifacts and Canonical Evidence](../adr/0126-offline-case-schema-v2-physical-artifacts-and-canonical-evidence.md)
- [ADR 0127: Staged Runtime Capability Ladder and Reference Boundary](../adr/0127-staged-runtime-capability-ladder-and-reference-boundary.md)
- [Runtime Capability Ladder 与 Model-backed Diagnostic Conditions](runtime-capability-ladder.md)
- [Structured Triage Report 校验与单 Case 确定性评分](structured-triage-report-and-per-case-scoring.md)
- [V1 Failure Type Taxonomy 与 Offline Case Policy](v1-failure-type-taxonomy-and-case-policy.md)
