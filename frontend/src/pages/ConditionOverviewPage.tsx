import { useCallback, useEffect, useState } from "react";

import { getConditions } from "../api/client";
import type { Condition } from "../api/types";
import { MetricVector } from "../components/ConditionShared";
import { TechnicalLabel } from "../components/Primitives";
import { conditionEditorial, ladderDimensions, ladderIds } from "../content/conditions";

export function ConditionOverviewPage() {
  const [conditions, setConditions] = useState<Condition[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    setError(null);
    try { setConditions(await getConditions()); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "未知 API 错误"); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  const byId = new Map(conditions?.map((condition) => [condition.condition, condition]));

  return (
    <main id="main" className="conditions-page">
      <section className="condition-index-hero">
        <p className="eyebrow">Condition Explorer</p>
        <h1>我们怎样一步步改变 Agent 能看到什么、能做什么</h1>
        <p>L1–L4 分别采用四种运行方式：一次给全部上下文、固定两阶段、先自动检索、再到模型自己调用工具。这样可以把“信息怎么给模型”和“谁控制下一步”拆开看，而不是把所有结果压成一个总分。Oracle 另外回答：如果跳过“自己找证据”，模型还能诊断到什么程度。</p>
      </section>

      <section className="ladder-architecture" aria-labelledby="ladder-title">
        <header><p className="eyebrow">Ladder Architecture</p><h2 id="ladder-title">L1–L4：四种运行方式，不是能力排名</h2><p>从左到右，主要变化的是模型拿到多少 Evidence、程序怎么组织调用，以及下一步调查由程序决定还是由模型决定。</p></header>
        <div className="ladder-rungs">
          {ladderIds.map((id, index) => {
            const editorial = conditionEditorial[id];
            return <a href={`/conditions/${id.toLowerCase()}`} key={id}><span>{id}</span><div><strong>{editorial.name}</strong><small>{editorial.runtimeVariant}</small></div>{index < ladderIds.length - 1 ? <i aria-hidden="true" /> : null}</a>;
          })}
        </div>
        <div className="ladder-dimensions" role="table" aria-label="Condition ladder changed boundaries">
          <div className="dimension-header" role="row"><span role="columnheader">主要变化</span>{ladderIds.map((id) => <span role="columnheader" key={id}>{id}</span>)}</div>
          {ladderDimensions.map((dimension) => <div role="row" key={dimension.label}><strong role="rowheader">{dimension.label}</strong>{dimension.values.map((value, index) => <span role="cell" key={`${dimension.label}-${ladderIds[index]}`}>{value}</span>)}</div>)}
        </div>
      </section>

      <section className="condition-comparison" aria-labelledby="condition-comparison-title">
        <header><p className="eyebrow">Condition Comparison</p><h2 id="condition-comparison-title">每个 Condition 到底在测什么？</h2><p>下面每组数字来自对应 Condition 的 representative fresh canonicalized formal Run。它们展示各自方案的正式结果，但不同 fresh Runs 不能直接当成严格的单因素因果对照。</p></header>
        {error ? <div className="overview-api-error" role="status"><strong>代表性实验数据暂不可用</strong><span>{error}</span><button type="button" onClick={() => void load()}>重新读取</button></div> : null}
        <div className="overview-condition-list">
          {ladderIds.map((id) => {
            const editorial = conditionEditorial[id];
            const condition = byId.get(id);
            return (
              <article key={id}>
                <div className="overview-condition-id"><span>{id}</span><small>{editorial.runtimeVariant}</small></div>
                <div className="overview-condition-copy"><h3>{editorial.name}</h3><p>{editorial.question}</p><div><TechnicalLabel>这里改了什么</TechnicalLabel><span>{editorial.change}</span></div><a href={`/conditions/${id.toLowerCase()}`}>查看 {id} 的流程与结果 <span aria-hidden="true">→</span></a></div>
                <MetricVector metrics={condition?.formal_metric_vector ?? null} unavailable={Boolean(error)} />
              </article>
            );
          })}
        </div>
      </section>

      <section className="oracle-overview" aria-labelledby="oracle-overview-title">
        <div><TechnicalLabel tone="signal">独立诊断条件</TechnicalLabel><span>不属于 L1–L4</span></div>
        <div className="oracle-overview-copy"><p className="oracle-index">Oracle</p><h2 id="oracle-overview-title">Selected Source Evidence / One Shot</h2><p>Oracle 不让模型自己找证据。评测侧先用 required_evidence_ids 定位冻结文件里的关键原始片段，再把片段本身交给模型；模型看不到 Expected Answer、Required Evidence 标签或“为什么选这些片段”的理由。</p><a href="/conditions/oracle">查看 Oracle 的流程与结果 <span aria-hidden="true">→</span></a></div>
        <MetricVector metrics={byId.get("Oracle")?.formal_metric_vector ?? null} unavailable={Boolean(error)} />
      </section>
    </main>
  );
}
