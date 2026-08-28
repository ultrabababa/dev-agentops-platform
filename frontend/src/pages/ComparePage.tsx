import { useCallback, useEffect, useState } from "react";

import { compareRuns, getComparisons, getConditions, getOverview } from "../api/client";
import type { ComparisonCompatibility, Condition, Overview, RunComparison, RuntimeMetricComparison } from "../api/types";
import { ExplorerError, ExplorerLoading, metricEntries, percent, shortId } from "../components/ExplorerShared";

type CuratedExperimentData = { overview: Overview; conditions: Condition[]; comparison: RunComparison };

const runtimeMetrics: Array<[keyof NonNullable<RunComparison["runtime_optimization"]>["metrics"], string, "integer" | "seconds"]> = [
  ["model_decisions", "Model Decisions", "integer"], ["executed_tool_calls", "executed ToolCalls", "integer"],
  ["input_tokens", "Input Tokens", "integer"], ["output_tokens", "Output Tokens", "integer"], ["total_tokens", "Total Tokens", "integer"],
  ["run_wall_time_seconds", "Run Wall Time", "seconds"], ["mean_sample_latency_seconds", "Mean Sample Latency", "seconds"],
  ["p50_sample_latency_seconds", "P50 Sample Latency", "seconds"], ["p95_sample_latency_seconds", "P95 Sample Latency", "seconds"],
];

const compatibilityRows: Array<[keyof ComparisonCompatibility, string]> = [
  ["same_suite", "同一 frozen benchmark / Suite"], ["same_suite_fingerprint", "同一 Suite fingerprint"],
  ["same_model_configuration", "同一模型配置"], ["same_evaluation_method", "同一评分方法"],
  ["same_output_contract", "同一输出合同"], ["same_code_revision", "同一代码版本"],
  ["same_runtime_variant", "同一 L4 Runtime"], ["same_treatment", "同一工具执行策略"],
];

const conditionOrder = ["L1", "L2", "L3", "L4", "Oracle"] as const;
const number = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const integer = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

function runtimeValue(value: number, kind: "integer" | "seconds") { return kind === "seconds" ? `${number.format(value)}s` : integer.format(value); }
function relativeDelta(metric: RuntimeMetricComparison) { if (metric.a === 0) return "—"; const value = ((metric.b - metric.a) / metric.a) * 100; return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`; }
function deltaPp(value: number) { return `${value > 0 ? "+" : ""}${value.toFixed(2)} pp`; }

function DecisionChain({ children }: { children: string[] }) {
  return <ol className="decision-chain" aria-label="从问题到工程决策">{children.map((item) => <li key={item}>{item}</li>)}</ol>;
}

function ExperimentHeader({ id, index, title, canonical, method, summary }: { id: string; index: string; title: string; canonical: string; method: string; summary: string }) {
  return <header className="experiment-header"><span className="experiment-index" aria-hidden="true">{index}</span><div><p className="method-badge">{method}</p><h2 id={id}>{title}</h2><p className="canonical-name">{canonical}</p><p>{summary}</p></div></header>;
}

function EvidenceLinks({ links }: { links: Array<[string, string]> }) {
  return <nav className="evidence-links" aria-label="实验依据下钻">{links.map(([label, href]) => <a key={`${label}-${href}`} href={href}>{label} →</a>)}</nav>;
}

function EddLoop() {
  const stages = [
    ["正式评测", "Formal Evaluation", "先找出 badcase，而不是只看一个总分。"],
    ["失败归因", "Failure Attribution", "把失败拆到具体环节，再提出可以验证的 hypothesis。"],
    ["控制实验", "Controlled Experiment / Ablation", "根据问题选择 fixed-output replay、ablation、replication 或 diagnostic intervention。"],
    ["证据驱动迭代", "Evidence → Runtime Evolution", "证据支持哪一层有问题，就改哪一层，然后回到下一轮 Evaluation。"],
  ];
  return <section className="edd-overview" aria-labelledby="edd-title"><header><p className="eyebrow">EVALUATION-DRIVEN DEVELOPMENT</p><h2 id="edd-title">Evaluation 不是收尾报告，而是下一次工程决策的起点。</h2><p>这套闭环的重点不是“跑完 benchmark”，而是从 badcase 出发做 failure attribution：先定位失败发生在哪一层，再提出可验证假设，用合适的控制实验验证，最后依据 evidence 决定 Runtime 下一步改什么。</p></header><ol className="edd-loop" aria-label="Evaluation-driven development 闭环">{stages.map(([title, term, explanation]) => <li key={term}><strong>{title}</strong><small>{term}</small><span>{explanation}</span></li>)}</ol><div className="edd-return"><span>下一轮 Evaluation</span><i aria-hidden="true">↩</i><p>Runtime Evolution 不是终点；改完以后必须重新进入正式评测，看 badcase 是否真的减少。</p></div></section>;
}

function CanonicalizationCase({ overview }: { overview: Overview }) {
  const finding = overview.featured_findings.canonicalization; const l4 = finding.l4;
  return <article className="experiment-case" id="canonicalization" aria-labelledby="canonicalization-title">
    <ExperimentHeader id="canonicalization-title" index="01" title="Evidence 引用规范化" canonical="Evidence Reference Canonicalization" method="FIXED-OUTPUT REPLAY · CAUSAL ISOLATION" summary="模型输出保持不变，只改 Evidence 引用的规范化与校验规则，判断这批 Protocol badcase 是否有一部分来自评测基础设施，而不是模型诊断本身。" />
    <div className="story-pair"><section><h3>问题</h3><p>评测里出现了一批 Evidence / Protocol badcase。模型是真的诊断错了，还是它已经找对证据，只是引用格式没有被基础设施正确识别？</p></section><section><h3>待验证假设</h3><p>我们怀疑其中一部分 badcase 并非模型诊断错误，而是 Evidence 引用在进入 validator / scorer 前没有被稳定规范化和识别。这个基础设施步骤就是 <code>evidence-reference canonicalization</code>。</p></section></div>
    <section className="case-design"><h3>实验设计</h3><p className="important-sentence">我们没有重新调用模型。同一份历史模型输出前后各评一次，唯一改变的是 Evidence 引用如何被规范化和识别。</p><ol className="replay-flow"><li><strong>同一份历史模型原始输出</strong><small>same model output</small></li><li><strong>模型输出完全不变</strong><small>no regeneration</small></li><li><strong>只改 Evidence 引用规范化</strong><small>deterministic canonicalization</small></li><li><strong>重新校验与评分</strong><small>validation / scoring</small></li></ol></section>
    <section className="case-results"><h3>结果</h3><div className="metric-rails three"><div><span>Protocol Validity</span><strong>{percent(l4.protocol_validity_before)} <i>→</i> {percent(l4.protocol_validity_after)}</strong></div><div><span>unknown Evidence IDs</span><strong>{l4.unknown_evidence_ids_before} <i>→</i> {l4.unknown_evidence_ids_after}</strong></div><div><span>Failure Type Exact Match</span><strong>{percent(l4.failure_type_exact_match_before)} <i>→</i> {percent(l4.failure_type_exact_match_after)}</strong><small>unchanged</small></div></div></section>
    <div className="conclusion-decision"><section><h3>结论</h3><h4>模型的 Failure Type 判断没变，变的是基础设施能否正确识别 Evidence 引用。</h4><p>Failure Type Exact Match 保持不变，但 Protocol Validity 明显恢复，unknown Evidence IDs 从 12 降到 0。这支持我们把这部分 badcase 定位到 Evidence 引用规范化 / validation infrastructure，而不是把改善归因成“模型重新推理得更好”。</p></section><section><h3>EDD 决策</h3><p>因此这一轮优先修复基础设施，而不是先改 prompt 或换模型。</p><DecisionChain>{["发现 Protocol badcase", "归因到 infrastructure", "做 deterministic fix", "固定输出 replay", "验证修复影响"]}</DecisionChain></section></div>
    <details className="experiment-details"><summary>查看实验依据与 provenance</summary><p><code>{finding.authority}</code> · <code>{finding.artifact_id}</code></p></details>
  </article>;
}

function ToolPolicyCase({ comparison }: { comparison: RunComparison }) {
  const runtime = comparison.runtime_optimization;
  return <article className="experiment-case" id="tool-policy" aria-labelledby="tool-policy-title">
    <ExperimentHeader id="tool-policy-title" index="02" title="L4 工具执行策略" canonical="L4 Tool Policy" method="CONTROLLED ABLATION · REPLICATION" summary="保持关键实验身份一致，只改变 ToolCall 的接收与执行策略，观察效率收益能否在 replication 中再次出现。" />
    <div className="story-pair"><section><h3>问题</h3><p>L4 ReAct Runtime 能自主调用工具，但基线策略每轮最多执行一个 ToolCall，工具调用按顺序执行；如果模型一次生成多个调用，基线策略会拒绝这组调用。这会不会让 Agent 付出本来不必要的模型决策、token 和等待时间？</p></section><section><h3>待验证假设</h3><p>我们怀疑一部分开销不是任务本身必须付出的，而是 Tool Policy 让 Agent 额外经历了更多轮模型决策。</p></section></div>
    <section className="case-design"><h3>实验设计</h3><div className="ablation-rail"><div><span>A · 原策略</span><strong>Single + Sequential</strong><p>每轮最多执行 1 个 ToolCall；多调用会被基线策略拒绝，工具按顺序执行。</p></div><div className="intervention"><span>唯一主要 intervention</span><strong>工具执行策略</strong><small>Tool Policy</small></div><div><span>B · 新策略</span><strong>Batch + Parallel</strong><p>同一轮可接受多个 ToolCall；互不依赖的调用允许并行执行。</p></div></div></section>
    <section className="control-summary"><div><h3>控制变量 · 保持不变</h3><ul><li>同一 frozen benchmark / Suite</li><li>同一模型配置</li><li>同一评分方法与输出合同</li><li>同一代码版本</li><li>同一 L4 Runtime</li></ul></div><div><h3>真正改变</h3><p>工具执行策略 / Tool Policy</p></div></section>
    <section className="case-results"><h3>结果</h3>{runtime ? <><div className="metric-rails three">{([runtimeMetrics[0], runtimeMetrics[5], runtimeMetrics[1]]).map(([key, label, kind]) => { const metric = runtime.metrics[key]; return <div key={key}><span>{label}</span><strong>{runtimeValue(metric.a, kind)} <i>→</i> {runtimeValue(metric.b, kind)}</strong><small>{relativeDelta(metric)}</small></div>; })}</div><details className="experiment-details"><summary>查看完整 Runtime 指标</summary><dl className="secondary-metrics">{runtimeMetrics.map(([key, label, kind]) => { const metric = runtime.metrics[key]; return <div key={key}><dt>{label}</dt><dd>{runtimeValue(metric.a, kind)} → {runtimeValue(metric.b, kind)} <small>{relativeDelta(metric)}</small></dd></div>; })}</dl></details></> : <p className="data-unavailable">Runtime milestone 数据暂不可用；页面不会从 Trajectory 或 Trace 重算。</p>}</section>
    <section className="quality-block"><h3>正式质量指标</h3><p>正负只表示观测差值，不自动代表好坏、显著性或因果。</p><dl className="quality-comparison">{metricEntries.map(([key, label]) => { const metric = comparison.formal_metrics[key]; return <div key={key}><dt>{label}</dt><dd><span>{percent(metric.a)}</span><i>→</i><strong>{percent(metric.b)}</strong><small>{deltaPp(metric.delta_pp)}</small></dd></div>; })}</dl></section>
    <div className="conclusion-decision"><section><h3>结论</h3><h4>效率收益在 replication 中再次出现；没有观察到可复现的实质质量回退。</h4><p>Operational metrics 的效率趋势在 replication 中再次出现，因此我们保留 Batch + Parallel 作为 Runtime 优化方向；质量指标的小幅差异只作为观测结果，不作为 Tool Policy 改变诊断质量的因果证据。</p><p className="causal-note">两边都是 fresh generation。即使关键配置保持一致，托管模型重新生成时仍有生成方差，所以质量指标的小幅变化不能直接归因于 Tool Policy。<code>causal_claim_supported = {String(comparison.causal_claim_supported)}</code></p></section><section><h3>EDD 决策</h3><p>保留这个效率优化，同时在下一轮正式评测中继续监测质量。</p><DecisionChain>{["发现 Runtime 开销", "提出 Tool Policy 假设", "控制变量 ablation", "Replication", "保留效率优化", "继续监测质量"]}</DecisionChain></section></div>
    <details className="experiment-details"><summary>查看控制条件、Run IDs 与 fingerprints</summary><dl className="provenance-list">{compatibilityRows.map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{comparison.compatibility[key] ? "相同" : "不同"}</dd></div>)}</dl><EvidenceLinks links={[[`查看原策略 Run ${shortId(comparison.run_a.run_id)}`, `/runs/${comparison.run_a.run_id}`], [`查看新策略 Run ${shortId(comparison.run_b.run_id)}`, `/runs/${comparison.run_b.run_id}`]]} /></details>
  </article>;
}

function RetrievalCase({ overview, conditions }: { overview: Overview; conditions: Condition[] }) {
  const finding = overview.featured_findings.retrieval_attribution;
  const evidenceRate = (id: "L1" | "L2" | "L3") => conditions.find((item) => item.condition === id)?.formal_metric_vector?.report_evidence_hit_rate;
  const representatives = (["L1", "L2", "L3"] as const).map((id) => [id, evidenceRate(id)] as const);
  return <article className="experiment-case" id="retrieval" aria-labelledby="retrieval-title">
    <ExperimentHeader id="retrieval-title" index="03" title="L3 静态检索归因" canonical="L3 Static Retrieval" method="BADCASE ATTRIBUTION" summary="L3 最终 Evidence 指标没有提升后，我们继续拆解损失发生在哪一层：Retrieval 没拿到，还是 Agent 拿到后没有用进最终报告。" />
    <div className="story-pair"><section><h3>问题</h3><p>我们加入 Static Retrieval（先用固定检索逻辑提供候选 Evidence），希望更容易把关键 Evidence 提供给模型。但正式结果中，L3 的 Report Evidence Hit Rate 并没有比 L1 / L2 更高。</p><div className="inline-comparison">{representatives.map(([id, value]) => <span key={id}><b>{id}</b>{value === undefined ? "—" : percent(value)}</span>)}</div><strong className="negative-finding">正式结果没有显示出 L3 的 Evidence Hit 提升。</strong></section><section><h3>待验证假设</h3><p>只看最终分数，无法判断 Retrieval 是没有找到证据，还是 Agent 拿到证据后没有真正利用。我们需要把 Evidence pipeline 拆开。</p></section></div>
    <section className="case-design"><h3>实验设计 · 拆解 Evidence pipeline</h3><ol className="evidence-funnel"><li><strong>应该找到的证据</strong><small>Required Evidence</small></li><li><strong>Retrieval 实际拿到多少</strong><small>Acquisition</small></li><li><strong>拿到后真正利用多少</strong><small>Utilization</small></li><li><strong>最终报告实际引用多少</strong><small>Final Report Citation</small></li></ol></section>
    <section className="case-results"><h3>归因结果</h3><div className="metric-rails three attribution-metrics"><div><span>Retrieval Acquisition Recall</span><strong>{percent(finding.retrieval_acquisition_recall)}</strong><p>所有应该找到的 Required Evidence 中，Retrieval 实际拿到了多少。</p></div><div><span>Acquired Required Evidence Utilization</span><strong>{percent(finding.acquired_required_evidence_utilization)}</strong><p>已经拿到的 Required Evidence 中，最终报告真正利用 / 引用了多少。</p></div><div><span>Report Evidence Hit Rate</span><strong>{percent(finding.report_evidence_hit_rate)}</strong><p>经过两层损失后，最终报告命中的 Evidence 比例。</p></div></div></section>
    <div className="conclusion-decision"><section><h3>结论</h3><h4>Evidence 的损失不只发生在 Retrieval，也发生在拿到证据后的利用 / 引用阶段。</h4><p>问题不是简单的“Retrieval 没找到证据”：一部分 Required Evidence 没被拿到；即使已经拿到，Agent 也没有全部利用或引用进最终报告。</p></section><section><h3>EDD 决策</h3><p>下一轮不能只追 retrieval recall；要分别验证 acquisition / ranking 和 utilization / citation 两类假设，确认问题究竟出在“没拿到”还是“拿到了但没用进报告”。</p><DecisionChain>{["发现最终指标没有 uplift", "拆 Evidence pipeline", "定位 acquisition loss", "定位 utilization loss", "形成针对性假设"]}</DecisionChain></section></div>
    <details className="experiment-details"><summary>查看 L3 artifact 与正式 Run</summary><p><code>{finding.authority}</code> · <code>{finding.artifact_id}</code></p><EvidenceLinks links={[[`查看 L3 正式 Run ${shortId(finding.run_id)}`, `/runs/${finding.run_id}`]]} /></details>
  </article>;
}

function OracleCase({ conditions }: { conditions: Condition[] }) {
  const condition = conditions.find((item) => item.condition === "Oracle");
  return <article className="experiment-case" id="oracle" aria-labelledby="oracle-title">
    <ExperimentHeader id="oracle-title" index="04" title="Oracle 证据干预" canonical="Oracle Evidence Intervention" method="DIAGNOSTIC ABLATION" summary="暂时绕过普通 Evidence discovery，由 evaluator 定位关键原始 source evidence，观察 Evidence 瓶颈是否明显缓解。" />
    <div className="oracle-boundary" role="note"><strong>Oracle 不是 L5</strong><strong>不是产品 Runtime</strong><strong>不是理论上限</strong></div>
    <div className="story-pair"><section><h3>问题</h3><p>如果暂时绕过普通 Evidence discovery，直接把 evaluator 已定位到的关键原始证据片段提供给模型，Evidence 相关表现会发生什么？</p></section><section><h3>待验证假设</h3><p>如果表现明显提高，就支持把 Evidence discovery / acquisition 列为重点瓶颈候选；这个结果只用于 diagnosis 和 hypothesis formation。</p></section></div>
    <section className="oracle-input"><div><h3>模型看到什么</h3><p>evaluator 只从 frozen Physical Artifacts 中定位关键原始 source evidence，模型看到的仍是原始证据片段。</p></div><div><h3>模型不会看到</h3><ul><li>Required Evidence 标签</li><li>隐藏参考答案</li><li>scorer label / selection rationale</li><li>fix information</li></ul></div></section>
    <section className="case-results"><h3>诊断结果 · Report Evidence Hit Rate</h3><p className="diagnostic-caption">这里横向看 representative Conditions，只用于 diagnosis / hypothesis formation；它们是 fresh generation，不是严格的因果对比。</p><div className="condition-bars">{conditionOrder.map((id) => { const value = conditions.find((item) => item.condition === id)?.formal_metric_vector?.report_evidence_hit_rate; return <div key={id}><strong>{id}</strong><span><i style={{ width: value === undefined ? "0%" : `${value * 100}%` }} /></span><b>{value === undefined ? "—" : percent(value)}</b></div>; })}</div></section>
    <div className="conclusion-decision"><section><h3>结论</h3><h4>绕过普通 Evidence discovery 后，Evidence 相关表现明显更高。</h4><p>这给出一个强诊断信号，支持把 Evidence discovery / acquisition 列为重点瓶颈候选。但这些 representative Runs 仍是 fresh generation，因此不是严格的 Run-level causal estimate，更不能把 Oracle 称为上界。</p></section><section><h3>EDD 决策</h3><p>围绕 retrieval、evidence acquisition 和 utilization 形成下一轮假设，再回到正式 Evaluation 验证。</p><DecisionChain>{["发现 Evidence gap", "做 Oracle intervention", "得到 bottleneck signal", "形成 retrieval 假设", "回到下一轮 Evaluation"]}</DecisionChain></section></div>
    <details className="experiment-details"><summary>查看 Oracle 正式 Run 与语义边界</summary><p>这是 orthogonal diagnostic intervention，不属于 Runtime capability ladder。</p>{condition ? <EvidenceLinks links={[[`查看 Oracle 正式 Run ${shortId(condition.representative_run.run_id)}`, `/runs/${condition.representative_run.run_id}`]]} /> : null}</details>
  </article>;
}

function MethodSummary() {
  const experiments = [["Evidence 引用规范化", "定位 Protocol / Evidence badcase 是否来自基础设施层"], ["L4 工具执行策略", "判断 Runtime 优化是否真的减少执行成本"], ["L3 静态检索归因", "判断 Evidence loss 具体发生在哪一层"], ["Oracle 证据干预", "判断绕过 Evidence discovery 后瓶颈是否明显缓解"]];
  const methods = [["固定输出 Replay", "Fixed-output replay：模型输出保持不变，只改 deterministic infrastructure 逻辑，适合隔离基础设施改动的影响。"], ["控制变量 Ablation", "Controlled ablation：其余关键条件不变，只改变一个主要变量，观察系统行为如何变化。"], ["Replication", "把同一优化再跑一轮，确认观察到的趋势能不能再次出现。"], ["Badcase attribution", "把最终指标拆成多个 failure stage，定位损失发生在哪一层。"], ["Diagnostic intervention", "暂时绕过一个环节，判断它是不是重要瓶颈。"]];
  return <section className="method-summary" aria-labelledby="method-summary-title"><header><p className="eyebrow">METHOD SUMMARY</p><h2 id="method-summary-title">四个实验，不是四次“比谁分数高”。</h2><p>它们分别回答不同的工程问题，但共同服务于同一条 Evaluation-driven development 证据链。</p></header><dl className="experiment-map">{experiments.map(([name, purpose]) => <div key={name}><dt>{name}</dt><dd>{purpose}</dd></div>)}</dl><div className="page-conclusion"><strong>先用正式评测暴露 badcase，再做 failure attribution 缩小问题范围，最后选择合适的实验方法验证 hypothesis。</strong><p>证据支持哪一层有问题，就改哪一层；改完以后再回到正式 Evaluation 验证。</p></div><details className="methods-disclosure"><summary>为什么不同问题要用不同实验方法？</summary><dl>{methods.map(([name, use]) => <div key={name}><dt>{name}</dt><dd>{use}</dd></div>)}</dl></details></section>;
}

export function ComparePage() {
  const [data, setData] = useState<CuratedExperimentData | null>(null); const [error, setError] = useState<string | null>(null); const [loading, setLoading] = useState(true);
  const load = useCallback(async () => { setLoading(true); setError(null); try { const [overview, conditions, presets] = await Promise.all([getOverview(), getConditions(), getComparisons()]); const preset = presets.find((item) => item.id === "l4-replication" || item.category === "controlled_fresh_generation_comparison"); if (!preset) throw new Error("推荐的 L4 replication experiment 暂不可用"); const comparison = await compareRuns(preset.run_a, preset.run_b); setData({ overview, conditions, comparison }); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "实验数据读取失败"); } finally { setLoading(false); } }, []);
  useEffect(() => { void load(); }, [load]);
  if (loading && !data) return <main id="main" className="explorer-page compare-page"><ExplorerLoading label="正在读取真实实验与归因数据…" /></main>;
  if (error || !data) return <main id="main" className="explorer-page compare-page"><ExplorerError message={error ?? "实验数据未返回"} retry={() => void load()} /></main>;
  return <main id="main" className="explorer-page compare-page"><header className="attribution-intro"><p className="eyebrow">EXPERIMENTS &amp; ATTRIBUTION</p><h1>实验与归因</h1><p>DevAgentOps 不把 Evaluation 当成最后一张成绩单。我们用正式评测发现 badcase，再做归因、设计控制实验，让证据决定下一次 Runtime 应该改什么。</p></header><EddLoop /><div className="case-study-sequence" aria-label="四个真实实验案例"><CanonicalizationCase overview={data.overview} /><ToolPolicyCase comparison={data.comparison} /><RetrievalCase overview={data.overview} conditions={data.conditions} /><OracleCase conditions={data.conditions} /></div><MethodSummary /><nav className="compare-next-links" aria-label="继续核查真实评测证据"><a href="/runs">查看全部正式 Runs →</a><a href="/cases">查看 Cases / Samples →</a><a href={`/runs/${data.comparison.run_b.run_id}`}>从正式 Run 下钻 Agent Trajectory / Runtime Trace →</a></nav></main>;
}
