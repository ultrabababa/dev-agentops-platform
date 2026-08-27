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
    { index: "01", label: "Frozen Case" },
    { index: "02", label: "Agent Runtime" },
    { index: "03", label: "Execution Evidence", detail: "Trace / Trajectory" },
    { index: "04", label: "Structured Report" },
    { index: "05", label: "Deterministic Scoring" },
    { index: "06", label: "Case-first Aggregation" },
    { index: "07", label: "Failure Attribution" },
  ];
  return (
    <Section index="01" eyebrow="Evaluation Loop" title="把一次 Agent 运行变成可复现的工程证据" intro="从冻结输入到确定性评分，再通过 badcase attribution（坏样本归因）决定下一次 Runtime 改什么。">
      <div className="evaluation-flow" aria-label={nodes.map((node) => node.label).join(" 到 ")}>
        {nodes.map((node, position) => (
          <div className="flow-segment" key={node.label}>
            <div className="flow-node"><span>{node.index}</span><strong>{node.label}</strong><small>{node.detail ?? ""}</small></div>
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
            <TechnicalLabel>BASELINE · SAME FROZEN SUITE</TechnicalLabel>
            <h3>建立第一组可比较的诊断基线</h3>
            <p>我们先在同一套冻结的 20 个 CI / Test Failure Cases 上，让几种不同的诊断条件完成同一诊断任务，同时记录报告质量、Evidence 引用和执行结果。</p>
            <div className="stage-annotation"><b>发现</b><span>一些失败不只是模型判断错了故障类型。部分报告包含有价值的信息，但 Evidence Reference 的写法无法按 frozen schema 解析，因此在 validator / scorer 处失分。</span></div>
          </div>
          <div className="baseline-map" aria-label="L1、L2、L4 平行基线与独立 Oracle 诊断条件">
            <span className="suite-spine">SAME FROZEN 20-CASE SUITE</span>
            <div className="baseline-lane"><code>L1</code><code>L2</code><code>L4</code></div>
            <div className="baseline-oracle"><div><span>独立诊断条件</span><b>不属于 L1–L4</b></div><code>Oracle</code><p>直接提供 Required Evidence</p></div>
            <small>同一 Ground Truth · 同一 Deterministic Scorer</small>
          </div>
        </article>

        <article className="evolution-stage stage-canonicalization">
          <div className="stage-index"><span>02</span><i /></div>
          <div className="stage-copy">
            <TechnicalLabel tone="signal">FIXED-OUTPUT OFFLINE REPLAY</TechnicalLabel>
            <h3>修复 Evidence Reference 的表示错误</h3>
            <p>为了判断问题来自模型还是基础设施，我们不重新调用模型，而是把历史模型输出完全固定。只在报告进入 validator 前加入 deterministic normalization，把能够确定解析的 line-range reference 映射到 frozen canonical evidence ID。</p>
            <div className="stage-annotation"><b>验证</b><span>完全相同的历史输出依次经过 normalization、原 validator 和未改变的 scorer。唯一变化是 Evidence Reference 的解析步骤。</span></div>
          </div>
          <div className="stage-evidence">
            <MechanismFlow items={["Model Output", "Deterministic Canonicalization", "Validator", "Scorer"]} />
            <div className="pair-stack">
              <MetricPair label="Protocol Validity" before={percent(canonical.l4.protocol_validity_before)} after={percent(canonical.l4.protocol_validity_after)} />
              <MetricPair label="Unknown Evidence IDs" before={canonical.l4.unknown_evidence_ids_before} after={canonical.l4.unknown_evidence_ids_after} />
              <MetricPair label="Failure Type Exact Match" before={percent(canonical.l4.failure_type_exact_match_before)} after={percent(canonical.l4.failure_type_exact_match_after)} />
            </div>
            <p className="stage-conclusion">Failure Type 判断没有变化，但协议有效率和 Evidence Reference 解析明显改善。这里修复的是机器可验证的输出表示，而不是通过重新生成答案让模型答得更好。</p>
            <small className="evidence-caption">Provenance · fixed historical model outputs</small>
          </div>
        </article>

        <article className="evolution-stage stage-runtime">
          <div className="stage-index"><span>03</span><i /></div>
          <div className="stage-copy">
            <TechnicalLabel tone="verified">BACK-TO-BACK L4 REPLICATION</TechnicalLabel>
            <h3>减少不必要的 Model Decision 轮次</h3>
            <p>旧 Runtime 一轮只接受一个 ToolCall，无法直接利用模型在同一轮给出的多个独立工具请求，因此会产生额外的 Model Decision 和模型往返。</p>
            <div className="stage-annotation"><b>改动</b><span>同一轮接受多个合法、相互独立的 ToolCalls 并行执行；全部完成后，再按原始 ToolCall 顺序返回 ToolResults。</span></div>
          </div>
          <div className="stage-evidence runtime-evidence">
            <div className="runtime-mechanism">
              <div><small>REFERENCE</small><strong>Single</strong><span>+</span><strong>Sequential</strong></div>
              <FlowArrow label="change one Runtime boundary" />
              <div className="active"><small>TREATMENT</small><strong>Batch</strong><span>+</span><strong>Parallel</strong></div>
            </div>
            <div className="runtime-metrics">
              <MetricPair label="Model Decisions" before={runtime.model_decisions[0]} after={runtime.model_decisions[1]} />
              <MetricPair label="ToolCalls" before={runtime.executed_tool_calls[0]} after={runtime.executed_tool_calls[1]} />
              <MetricPair label="Wall Time" before={seconds(runtime.run_wall_seconds[0])} after={seconds(runtime.run_wall_seconds[1])} />
            </div>
            <p className="stage-conclusion">ToolCalls 只小幅减少，但 Model Decisions 明显减少：主要收益来自减少模型往返与 decision overhead，而不是大幅减少调查。</p>
            <div className="stage-verdict"><b>结论</b><span>效率改进复现；未证明存在可复现的实质质量回退。</span></div>
            <small className="evidence-caption">Provenance · fresh back-to-back replication</small>
          </div>
        </article>

        <article className="evolution-stage stage-retrieval">
          <div className="stage-index"><span>04</span></div>
          <div className="stage-copy">
            <TechnicalLabel>FORMAL L3 ATTRIBUTION RUN</TechnicalLabel>
            <h3>拆开“没找到”与“找到但没用好”</h3>
            <p>最后加入 deterministic Static Retrieval，专门分析 Evidence 到底在哪一步丢失。我们分别测量 Required Evidence 是否进入模型上下文，以及进入后是否最终在报告中被正确引用。</p>
            <div className="stage-annotation"><b>理解</b><span>“找不到证据”和“找到了但没用好”是两个不同的问题，需要不同的 Runtime / Retrieval 改进。</span></div>
          </div>
          <div className="stage-evidence retrieval-attribution">
            <div><span>Required Evidence 被检索到</span><strong>{percent(retrieval.retrieval_acquisition_recall)}</strong><small>分母：全部 Required Evidence</small></div>
            <div><span>已检索到的 Required Evidence 最终被报告引用</span><strong>{percent(retrieval.acquired_required_evidence_utilization)}</strong><small>分母：已经成功检索到的 Required Evidence</small></div>
            <div><span>最终整体 Report Evidence Hit</span><strong>{percent(retrieval.report_evidence_hit_rate)}</strong><small>分母：全部 Required Evidence，按正式 Case-first 方法聚合</small></div>
            <p>这是一项 failure attribution 诊断；正式结果没有证明 L3 相对 L1 / L2 提升了 Evidence Hit。</p>
            <small className="evidence-caption">Provenance · formal Static Retrieval Run + evaluator-side acquisition diagnostic</small>
          </div>
        </article>
      </div>
    </Section>
  );
}

function RepresentativeFindings({ data }: { data: HomepageData }) {
  const { canonicalization: canonical, runtime_optimization: runtime, retrieval_attribution: retrieval } = data.overview.featured_findings;
  return (
    <Section index="03" eyebrow="Representative Findings" title="三项最重要的实验发现" intro="每项实验都围绕一个明确的系统边界设计，再根据对应的实验结果判断这个改动是否值得保留。" className="findings-section">
      <div className="finding-list">
        <article><span>A</span><div><h3>Evidence Reference Canonicalization</h3><p>修复机器可验证的 Evidence Reference 表示问题 · Fixed-output replay</p></div><MetricPair label="Protocol Validity" before={percent(canonical.l4.protocol_validity_before)} after={percent(canonical.l4.protocol_validity_after)} /></article>
        <article><span>B</span><div><h3>Batch + Parallel Runtime</h3><p>减少不必要的 Model Decision 和运行时间 · Back-to-back replication</p></div><MetricPair label="Model Decisions" before={runtime.model_decisions[0]} after={runtime.model_decisions[1]} /></article>
        <article><span>C</span><div><h3>Static Retrieval Attribution</h3><p>把“没找到 Evidence”和“找到但没用好”分开观察 · Formal L3 Run</p></div><Metric label="Acquisition / Final Hit" value={`${percent(retrieval.retrieval_acquisition_recall)} / ${percent(retrieval.report_evidence_hit_rate)}`} /></article>
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
    <Section id="conditions" index="04" eyebrow="Conditions" title="不同 Runtime 条件，分别回答不同问题" intro="从 L1 到 L4，逐步改变模型能看到的 Evidence、程序如何组织模型调用，以及 Runtime 控制是否由模型自适应决定。Oracle 是独立的诊断干预，不是下一等级。">
      <p className="conditions-provenance">下方指标来自各 Condition 的 representative fresh canonicalized formal Run；与上方 fixed-output replay 和 L4 replication 属于不同实验上下文。</p>
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
            <div className="oracle-heading"><TechnicalLabel tone="signal">独立诊断条件</TechnicalLabel><span>不属于 L1–L4</span></div>
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
    <Section index="05" eyebrow="Evaluation Principles" title="为什么这些实验结果可以复现和追溯">
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
          <p className="eyebrow">Public Evaluation Explorer</p>
          <h1><span>面向 CI / Test Failure Triage 的</span><span><em>Agent Runtime</em> 与 <em>Formal Evaluation</em> 平台</span></h1>
          <p className="hero-english">Evaluation-driven runtime engineering for reproducible agent failure triage.</p>
          <p className="hero-copy">冻结 benchmark 输入，记录 Runtime 执行证据，对 Structured Report 做确定性评分，再用正式评测结果驱动受控的 Runtime 演进。</p>
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
