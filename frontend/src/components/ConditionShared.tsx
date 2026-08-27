import type { ReactNode } from "react";

import type { Condition, FormalMetricVector } from "../api/types";
import { metricLabels } from "../content/home";

const percent = (value: number) => `${(value * 100).toFixed(2)}%`;

export function MetricVector({ metrics, unavailable = false }: { metrics: FormalMetricVector | null; unavailable?: boolean }) {
  if (!metrics) {
    return <p className="condition-data-unavailable">{unavailable ? "Representative experiment data unavailable · 未使用静态指标替代" : "Formal metric vector unavailable"}</p>;
  }
  return (
    <dl className="condition-metric-vector" aria-label="Representative formal metric vector">
      {metricLabels.map(([key, label]) => (
        <div key={key}>
          <dt>{label}</dt>
          <dd>{percent(metrics[key])}</dd>
        </div>
      ))}
    </dl>
  );
}

export function RepresentativeResults({ condition, error, loading }: { condition: Condition | null; error: string | null; loading: boolean }) {
  return (
    <section className="condition-results" aria-labelledby="representative-results-title" aria-busy={loading || undefined}>
      <header>
        <div><p className="eyebrow">Representative Results</p><h2 id="representative-results-title">这次代表性 Run 的结果</h2></div>
        <p>Representative fresh canonicalized formal Run</p>
      </header>
      {loading ? <p className="condition-data-unavailable">正在读取代表 Run 数据…</p> : <MetricVector metrics={condition?.formal_metric_vector ?? null} unavailable={Boolean(error)} />}
      {condition ? (
        <dl className="run-provenance">
          <div><dt>Run</dt><dd title={condition.representative_run.run_id}>{condition.representative_run.run_id.slice(0, 8)}…</dd></div>
          <div><dt>已评分 / 计划</dt><dd>{condition.representative_run.scored_samples} / {condition.representative_run.planned_samples}</dd></div>
          <div><dt>状态</dt><dd>{condition.representative_run.status}</dd></div>
        </dl>
      ) : null}
      {error ? <p className="inline-api-error" role="status">正式实验数据读取失败：{error}</p> : null}
    </section>
  );
}

export function VisibilityBoundary({ visible, runtimeObservability, evaluatorOnly, oracle = false }: { visible: string[]; runtimeObservability?: string[]; evaluatorOnly: string[]; oracle?: boolean }) {
  return (
    <section className={`visibility-boundary ${oracle ? "oracle-visibility" : ""}`} aria-labelledby="visibility-title">
      <header>
        <p className="eyebrow">Information Boundary</p>
        <h2 id="visibility-title">模型到底能看到什么？</h2>
        <p>把模型输入、Runtime 自己记录的信息和只用于评分的隐藏信息分开看，才能知道每个 Condition 真正改变了哪一层。</p>
      </header>
      <div className={`visibility-lanes ${runtimeObservability ? "has-observability" : ""}`}>
        <div className="visibility-lane model-visible">
          <span className="visibility-label">模型可见 · MODEL VISIBLE</span>
          <ul>{visible.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
        {runtimeObservability ? <div className="visibility-lane runtime-observability"><span className="visibility-label">Runtime 自己记录 · RUNTIME OBSERVABILITY</span><ul>{runtimeObservability.map((item) => <li key={item}>{item}</li>)}</ul></div> : null}
        <div className="visibility-lane evaluator-only">
          <span className="visibility-label">模型看不到 / 仅评测侧 · EVALUATOR ONLY</span>
          <ul>{evaluatorOnly.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
      </div>
      {oracle ? <p className="visibility-oracle-note">Oracle 的唯一特殊点：评测侧选中的原始 source spans 会进入模型，但“为什么选这些片段”、Expected Answer 和评分标签仍然不会进入模型。</p> : null}
    </section>
  );
}

export function ArchitectureNode({ label, detail, tone = "default", badge }: { label: string; detail?: string; tone?: "default" | "signal" | "evaluator" | "runtime"; badge?: string }) {
  return (
    <div className={`architecture-node ${tone}`}>
      {badge ? <span>{badge}</span> : null}
      <strong>{label}</strong>
      {detail ? <small>{detail}</small> : null}
    </div>
  );
}

export function ArchitectureEdge({ label, direction = "right" }: { label?: string; direction?: "right" | "down" | "cross" }) {
  return <div className={`architecture-edge ${direction}`} aria-hidden="true"><i />{label ? <small>{label}</small> : null}</div>;
}

export function DiagramFrame({ title, description, children, className = "" }: { title: string; description: string; children: ReactNode; className?: string }) {
  return (
    <figure className={`architecture-frame ${className}`.trim()}>
      <figcaption><span>ARCHITECTURE / PROCESS</span><strong>{title}</strong><p>{description}</p></figcaption>
      <div className="architecture-canvas">{children}</div>
    </figure>
  );
}
