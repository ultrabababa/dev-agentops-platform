import { useCallback, useEffect, useState } from "react";

import { getCondition, getEvolution } from "../api/client";
import type { Condition, ConditionId, RetrievalAttributionFinding } from "../api/types";
import { L1Diagram, L2Diagram, L3Diagram, L4Diagram, OracleDiagram } from "../components/ConditionDiagrams";
import { RepresentativeResults, VisibilityBoundary } from "../components/ConditionShared";
import { TechnicalLabel } from "../components/Primitives";
import { conditionEditorial, ladderIds } from "../content/conditions";

const diagrams = { L1: L1Diagram, L2: L2Diagram, L3: L3Diagram, L4: L4Diagram, Oracle: OracleDiagram };

function L3Attribution({ finding, unavailable }: { finding: RetrievalAttributionFinding | null; unavailable: boolean }) {
  const percent = (value: number) => `${(value * 100).toFixed(2)}%`;
  return (
    <section className="l3-attribution" aria-labelledby="l3-attribution-title">
      <header><p className="eyebrow">Evidence Loss Attribution</p><h2 id="l3-attribution-title">证据到底丢在哪一步？</h2><p>先看 Retriever 有没有把需要的证据找出来，再看已经找出来的证据有没有在最终报告中被正确引用。</p></header>
      {finding ? (
        <div className="attribution-metrics">
          <div><span>需要的证据被 Retriever 找到</span><strong>{percent(finding.retrieval_acquisition_recall)}</strong><small>Retrieval Acquisition Recall · 分母：全部 Required Evidence</small></div>
          <div><span>已找到的证据最终被报告引用</span><strong>{percent(finding.acquired_required_evidence_utilization)}</strong><small>Acquired Required Evidence Utilization · 分母：已被 Retrieval 获取的 Required Evidence</small></div>
          <div><span>最终整体 Evidence Hit</span><strong>{percent(finding.report_evidence_hit_rate)}</strong><small>Report Evidence Hit Rate · 分母：全部 Required Evidence；正式 Case-first 聚合</small></div>
        </div>
      ) : <p className="condition-data-unavailable">{unavailable ? "L3 attribution data unavailable · 未使用静态值替代" : "正在读取 L3 attribution…"}</p>}
      <p>这三项是事后评测指标，不会把 hidden Required Evidence 暴露给模型。结果说明“没检索到”和“检索到了但没在最终报告里正确引用”是两个不同问题；同时也没有证明 L3 的 Report Evidence Hit 高于 L1 / L2。</p>
    </section>
  );
}

function L4PolicyNote() {
  return (
    <aside className="l4-policy-note">
      <div><TechnicalLabel>后续运行优化实验</TechnicalLabel><span>仍属于同一个 L4 Runtime family</span></div>
      <div><code>Single + Sequential</code><i aria-hidden="true">→</i><code>Batch + Parallel</code></div>
      <p>这是后来单独做的 Tool Policy 优化：允许同一轮批量接收并并行执行多个工具调用。它仍然属于 L4，不是新的 capability level；上面的代表性指标也不是这次优化实验的结果。</p>
    </aside>
  );
}

function ConditionNavigation({ id }: { id: ConditionId }) {
  if (id === "Oracle") {
    return <nav className="condition-navigation" aria-label="Condition navigation"><a href="/conditions">← 返回 Condition overview</a><div><span>PRIMARY LADDER</span>{ladderIds.map((ladderId) => <a href={`/conditions/${ladderId.toLowerCase()}`} key={ladderId}>{ladderId}</a>)}</div></nav>;
  }
  const index = ladderIds.indexOf(id);
  const previous = ladderIds[index - 1];
  const next = ladderIds[index + 1];
  return (
    <nav className="condition-navigation" aria-label="Condition navigation">
      <div>{previous ? <a href={`/conditions/${previous.toLowerCase()}`}>← 上一个：{previous}</a> : <a href="/conditions">← Condition overview</a>}</div>
      <a className="oracle-nav-link" href="/conditions/oracle">独立诊断条件：Oracle</a>
      <div>{next ? <a href={`/conditions/${next.toLowerCase()}`}>下一个：{next} →</a> : <a href="/conditions">返回 overview →</a>}</div>
    </nav>
  );
}

export function ConditionDetailPage({ id }: { id: ConditionId }) {
  const editorial = conditionEditorial[id];
  const Diagram = diagrams[id];
  const [condition, setCondition] = useState<Condition | null>(null);
  const [attribution, setAttribution] = useState<RetrievalAttributionFinding | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attributionError, setAttributionError] = useState(false);
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true); setError(null); setAttributionError(false);
    try { setCondition(await getCondition(id)); }
    catch (requestError) { setCondition(null); setError(requestError instanceof Error ? requestError.message : "未知 API 错误"); }
    if (id === "L3") {
      try {
        const evolution = await getEvolution();
        const stage = evolution.stages.find((item) => item.stage === "retrieval_attribution");
        const finding = stage?.key_observation;
        if (!finding || !("retrieval_acquisition_recall" in finding)) throw new Error("L3 attribution stage missing");
        setAttribution(finding);
      } catch { setAttribution(null); setAttributionError(true); }
    }
    setLoading(false);
  }, [id]);
  useEffect(() => { void load(); }, [load]);

  return (
    <main id="main" className={`condition-detail-page condition-${id.toLowerCase()}`}>
      <section className="condition-hero">
        <div className="condition-hero-id"><span>{id}</span>{id === "Oracle" ? <small>独立诊断条件 · 不属于 L1–L4</small> : <small>CAPABILITY / RUNTIME LADDER</small>}</div>
        <div className="condition-hero-copy"><p className="eyebrow">Condition Explorer</p><h1>{editorial.name}</h1><code>{condition?.runtime_variant ?? editorial.runtimeVariant}</code><p>{editorial.explanation}</p></div>
        <div className="research-question"><span>这个条件想回答什么？</span><p>{editorial.question}</p></div>
      </section>

      <section className="detail-question" aria-labelledby="detail-question-title">
        <div><p className="eyebrow">What Changes Here</p><h2 id="detail-question-title">这里具体改变了什么？</h2></div>
        <p>{editorial.change}</p>
      </section>

      <Diagram />
      {id === "L4" ? <L4PolicyNote /> : null}
      <VisibilityBoundary visible={editorial.modelVisible} runtimeObservability={editorial.runtimeObservability} evaluatorOnly={editorial.evaluatorOnly} oracle={id === "Oracle"} />
      {id === "L3" ? <L3Attribution finding={attribution} unavailable={attributionError} /> : null}
      <RepresentativeResults condition={condition} error={error} loading={loading} />

      <section className="result-interpretation" aria-labelledby="result-interpretation-title">
        <div><p className="eyebrow">How To Read This Result</p><h2 id="result-interpretation-title">这些数字该怎么理解？</h2></div>
        <p>{editorial.interpretation}</p>
      </section>
      <ConditionNavigation id={id} />
    </main>
  );
}
