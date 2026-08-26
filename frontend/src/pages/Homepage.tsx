import type {
  CanonicalizationFinding,
  Condition,
  Evolution,
  HomepageData,
  RetrievalAttributionFinding,
  RuntimeOptimizationFinding,
} from "../api/types";
import { conditionCopy, evaluationPrinciples, metricLabels } from "../content/home";
import { FlowArrow, Metric, MetricPair, Section, TechnicalLabel } from "../components/Primitives";

const percent = (value: number) => `${(value * 100).toFixed(2)}%`;
const seconds = (value: number) => `${value.toFixed(2)}s`;

function BenchmarkFacts({ data }: { data: HomepageData }) {
  const benchmark = data.overview.benchmark;
  return (
    <dl className="benchmark-facts" aria-label="冻结 benchmark 概览">
      <div><dt>Frozen Cases</dt><dd>{benchmark.case_count}</dd></div>
      <div><dt>Repeats / Case</dt><dd>{benchmark.repeats_per_case}</dd></div>
      <div><dt>Samples / Formal Run</dt><dd>{benchmark.samples_per_formal_run}</dd></div>
      <div><dt>Failure Types</dt><dd>{benchmark.failure_type_count}</dd></div>
    </dl>
  );
}

function EvaluationLoop() {
  const nodes = [
    ["01", "Frozen Case"], ["02", "Agent Runtime"], ["03", "Trace + Trajectory"],
    ["04", "Structured Report"], ["05", "Deterministic Scoring"],
    ["06", "Case-first Aggregation"], ["07", "Failure Attribution"],
  ];
  return (
    <Section index="01" eyebrow="Evaluation Loop" title="把一次 Agent 输出变成可复现的工程证据" intro="从冻结输入到可复现评分，再用 badcase attribution 驱动 Runtime 演进。">
      <div className="evaluation-flow" aria-label={nodes.map((node) => node[1]).join(" 到 ")}>
        {nodes.map(([index, label], position) => (
          <div className="flow-segment" key={label}>
            <div className="flow-node"><span>{index}</span><strong>{label}</strong></div>
            {position < nodes.length - 1 ? <FlowArrow /> : null}
          </div>
        ))}
      </div>
      <div className="loop-return" aria-hidden="true"><span>controlled Runtime evolution</span><i /></div>
    </Section>
  );
}

function MechanismFlow({ items }: { items: string[] }) {
  return (
    <div className="mechanism-flow">
      {items.map((item, index) => (
        <div className="mechanism-segment" key={item}>
          <code>{item}</code>
          {index < items.length - 1 ? <FlowArrow /> : null}
        </div>
      ))}
    </div>
  );
}

function EvolutionSection({ evolution }: { evolution: Evolution }) {
  const canonical = evolution.stages.find((stage) => stage.stage === "canonicalization")?.key_observation as CanonicalizationFinding | undefined;
  const runtime = evolution.stages.find((stage) => stage.stage === "runtime_optimization")?.key_observation as RuntimeOptimizationFinding | undefined;
  const retrieval = evolution.stages.find((stage) => stage.stage === "retrieval_attribution")?.key_observation as RetrievalAttributionFinding | undefined;
  if (!canonical || !runtime || !retrieval) throw new Error("实验演进 API 缺少必要 stage 数据");

  return (
    <Section id="experiments" index="02" eyebrow="Experiment Evolution" title="评测不是终点，而是 Runtime 的变更依据" intro="Observe → Attribute → Change one boundary → Freeze → Evaluate → Decide" className="evolution-section">
      <div className="evolution-rail">
        <article className="evolution-stage stage-baseline">
          <div className="stage-index"><span>01</span><i /></div>
          <div className="stage-copy">
            <TechnicalLabel>BASELINE · OBSERVE</TechnicalLabel>
            <h3>建立可比较的 Runtime 基线</h3>
            <p>在同一 frozen Suite 上运行 L1 / L2 / Oracle / L4，建立 Evidence delivery、fixed workflow 与 adaptive Runtime 的正式基线。</p>
            <div className="stage-annotation"><b>发现</b><span>部分失败并非 Failure Type 判断错误，而是 Evidence Reference 的机械性 realization failure。</span></div>
          </div>
          <div className="baseline-map" aria-label="同一冻结套件上的四个基线条件">
            <span className="suite-spine">frozen Suite</span>
            <div><code>L1</code><code>L2</code><code>Oracle</code><code>L4</code></div>
            <small>同一 Ground Truth · 同一 Scorer</small>
          </div>
        </article>

        <article className="evolution-stage stage-canonicalization">
          <div className="stage-index"><span>02</span><i /></div>
          <div className="stage-copy">
            <TechnicalLabel tone="signal">CANONICALIZATION · ISOLATE</TechnicalLabel>
            <h3>修复 Evidence Reference 的表示错误</h3>
            <p>固定历史模型输出，只改变 deterministic normalization，通过 offline replay 隔离基础设施改动。</p>
            <div className="stage-annotation"><b>验证</b><span>fixed-output replay 是 causal isolation experiment；fresh hosted generations 不是因果估计。</span></div>
          </div>
          <div className="stage-evidence">
            <MechanismFlow items={["Model Output", "Deterministic Canonicalization", "Validator", "Scorer"]} />
            <div className="pair-stack">
              <MetricPair label="Protocol Validity" before={percent(canonical.l4.protocol_validity_before)} after={percent(canonical.l4.protocol_validity_after)} />
              <MetricPair label="Unknown Evidence IDs" before={canonical.l4.unknown_evidence_ids_before} after={canonical.l4.unknown_evidence_ids_after} />
              <MetricPair label="Failure Type Exact Match" before={percent(canonical.l4.failure_type_exact_match_before)} after={percent(canonical.l4.failure_type_exact_match_after)} />
            </div>
            <p className="stage-conclusion">改进来自 deterministic output infrastructure，而不是重新生成模型答案。</p>
          </div>
        </article>

        <article className="evolution-stage stage-runtime">
          <div className="stage-index"><span>03</span><i /></div>
          <div className="stage-copy">
            <TechnicalLabel tone="verified">RUNTIME · REPLICATE</TechnicalLabel>
            <h3>减少不必要的 Model Decision 轮次</h3>
            <p>模型可在一次 Decision 产生多个独立 ToolCalls；Runtime 并行执行有效 sibling calls，在 barrier 后按 authored order 回填 ToolResults。</p>
            <div className="stage-annotation"><b>结论</b><span>效率改进复现；未证明存在可复现的实质质量回退。</span></div>
          </div>
          <div className="stage-evidence runtime-evidence">
            <div className="runtime-mechanism">
              <div><small>REFERENCE</small><strong>Single</strong><span>+</span><strong>Sequential</strong></div>
              <FlowArrow label="one Tool Policy boundary" />
              <div className="active"><small>TREATMENT</small><strong>Batch</strong><span>+</span><strong>Parallel</strong></div>
            </div>
            <div className="runtime-metrics">
              <MetricPair label="Model Decisions" before={runtime.model_decisions[0]} after={runtime.model_decisions[1]} />
              <MetricPair label="ToolCalls" before={runtime.executed_tool_calls[0]} after={runtime.executed_tool_calls[1]} />
              <MetricPair label="Wall Time" before={seconds(runtime.run_wall_seconds[0])} after={seconds(runtime.run_wall_seconds[1])} />
            </div>
            <small className="evidence-caption">Representative result · fresh back-to-back replication</small>
          </div>
        </article>

        <article className="evolution-stage stage-retrieval">
          <div className="stage-index"><span>04</span></div>
          <div className="stage-copy">
            <TechnicalLabel>RETRIEVAL · ATTRIBUTE</TechnicalLabel>
            <h3>拆开 Evidence Acquisition 与 Utilization</h3>
            <p>最终 Evidence Hit 之前至少有两个可分离的 failure stage：需要的 Evidence 是否被检索到，以及模型是否使用并引用了已获得的 Evidence。</p>
            <div className="stage-annotation"><b>理解</b><span>Evidence Acquisition 与最终 Evidence 使用是两个不同的 failure stage。</span></div>
          </div>
          <div className="stage-evidence retrieval-funnel">
            <div className="funnel-step"><span>Required Evidence</span></div>
            <div className="funnel-step"><span>Acquired Evidence</span><strong>{percent(retrieval.retrieval_acquisition_recall)}</strong></div>
            <div className="funnel-step"><span>Used / Cited Evidence</span><strong>{percent(retrieval.acquired_required_evidence_utilization)}</strong></div>
            <div className="funnel-step"><span>Final Report Evidence Hit</span><strong>{percent(retrieval.report_evidence_hit_rate)}</strong></div>
            <small>Diagnostic attribution · not a simple quality uplift claim</small>
          </div>
        </article>
      </div>
    </Section>
  );
}

function RepresentativeFindings({ data }: { data: HomepageData }) {
  const { canonicalization: canonical, runtime_optimization: runtime, retrieval_attribution: retrieval } = data.overview.featured_findings;
  return (
    <Section index="03" eyebrow="Representative Findings" title="三个数字切面，三个不同的系统边界" className="findings-section">
      <div className="finding-list">
        <article><span>A</span><div><h3>Deterministic Evidence Canonicalization</h3><p>representation correctness · fixed-output causal replay</p></div><MetricPair label="Protocol Validity" before={percent(canonical.l4.protocol_validity_before)} after={percent(canonical.l4.protocol_validity_after)} /></article>
        <article><span>B</span><div><h3>Batch + Parallel Runtime</h3><p>fewer Model Decisions · lower runtime latency</p></div><MetricPair label="Model Decisions" before={runtime.model_decisions[0]} after={runtime.model_decisions[1]} /></article>
        <article><span>C</span><div><h3>Static Retrieval Attribution</h3><p>acquisition vs utilization failure decomposition</p></div><Metric label="Acquisition / Final Hit" value={`${percent(retrieval.retrieval_acquisition_recall)} / ${percent(retrieval.report_evidence_hit_rate)}`} /></article>
      </div>
    </Section>
  );
}

function MetricVector({ condition }: { condition: Condition }) {
  if (!condition.formal_metric_vector) return <p className="metric-unavailable">Formal metric vector unavailable</p>;
  return (
    <dl className="metric-vector">
      {metricLabels.map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{percent(condition.formal_metric_vector![key])}</dd></div>)}
    </dl>
  );
}

function ConditionsOverview({ conditions }: { conditions: Condition[] }) {
  const ladder = conditions.filter((item) => item.condition !== "Oracle");
  const oracle = conditions.find((item) => item.condition === "Oracle");
  return (
    <Section id="conditions" index="04" eyebrow="Conditions" title="用 capability ladder 做归因，而不是合成一个总分" intro="L1 → L2 → L3 → L4 表示 Runtime / evidence acquisition 能力演进；Oracle 与 ladder 正交。">
      <div className="condition-layout">
        <div className="condition-ladder">
          {ladder.map((condition, index) => (
            <article className="condition-row" key={condition.condition}>
              <div className="condition-id"><span>{condition.condition}</span>{index < ladder.length - 1 ? <i aria-hidden="true" /> : null}</div>
              <div className="condition-summary"><TechnicalLabel>{condition.runtime_variant}</TechnicalLabel><h3>{conditionCopy[condition.condition].name}</h3><p>{conditionCopy[condition.condition].question}</p><a href={`/conditions/${condition.condition.toLowerCase()}`}>查看 Condition <span aria-hidden="true">→</span></a></div>
              <MetricVector condition={condition} />
            </article>
          ))}
        </div>
        {oracle ? (
          <aside className="oracle-condition">
            <div className="oracle-heading"><TechnicalLabel tone="signal">Diagnostic Condition</TechnicalLabel><span>ORTHOGONAL</span></div>
            <div className="condition-summary"><span className="oracle-id">Oracle</span><TechnicalLabel>{oracle.runtime_variant}</TechnicalLabel><h3>{conditionCopy.Oracle.name}</h3><p>{conditionCopy.Oracle.question}</p><a href="/conditions/oracle">查看 Condition <span aria-hidden="true">→</span></a></div>
            <MetricVector condition={oracle} />
          </aside>
        ) : null}
      </div>
    </Section>
  );
}

function EvaluationPrinciples() {
  return (
    <Section index="05" eyebrow="Evaluation Principles" title="结论可信，先要求实验身份可信">
      <dl className="principles-list">
        {evaluationPrinciples.map(([title, description], index) => <div key={title}><dt><span>0{index + 1}</span>{title}</dt><dd>{description}</dd></div>)}
      </dl>
    </Section>
  );
}

export function Homepage({ data }: { data: HomepageData }) {
  return (
    <>
      <section className="hero" id="overview">
        <div className="hero-thesis">
          <p className="eyebrow">Public Evaluation Explorer · Phase 2A</p>
          <h1>面向 CI / Test Failure Triage 的<br /><em>Agent Runtime</em> 与 <em>Formal Evaluation</em> 平台</h1>
          <p className="hero-english">Evaluation-driven runtime engineering for reproducible agent failure triage.</p>
          <p className="hero-copy">冻结 benchmark 输入，记录 Runtime 执行证据，确定性评分 Structured Reports，再用正式评测结果驱动受控的 Runtime 演进。</p>
          <div className="hero-actions"><a className="button primary" href="#experiments">查看实验结果</a><a className="button secondary" href="https://github.com/ultrabababa/dev-agentops-platform" target="_blank" rel="noreferrer">GitHub ↗</a></div>
        </div>
        <div className="hero-loop" aria-label="DevAgentOps 核心闭环"><span>RUN</span><i /><span>RECORD</span><i /><span>SCORE</span><i /><span>ATTRIBUTE</span><i /><strong>EVOLVE</strong></div>
        <BenchmarkFacts data={data} />
      </section>
      <EvaluationLoop />
      <EvolutionSection evolution={data.evolution} />
      <RepresentativeFindings data={data} />
      <ConditionsOverview conditions={data.conditions} />
      <EvaluationPrinciples />
    </>
  );
}
