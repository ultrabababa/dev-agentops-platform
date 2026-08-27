import { useCallback, useEffect, useState } from "react";

import { getOverview, getRun, getRunCases } from "../api/client";
import type { Overview, Run, RunCaseAggregate } from "../api/types";
import { dateTime, ExplorerError, ExplorerLoading, FailureTypeLabel, FormalMetrics, MetricGuide, PageIntro, percent, ProvenanceSheet, roleLabels, RunStatus, runtimeLabels, shortId, stageLabels } from "../components/ExplorerShared";

export function RunDetailPage({ runId }: { runId: string }) {
  const [run, setRun] = useState<Run | null>(null);
  const [cases, setCases] = useState<RunCaseAggregate[]>([]);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [nextRun, nextCases, nextOverview] = await Promise.all([getRun(runId), getRunCases(runId), getOverview()]);
      setRun(nextRun); setCases(nextCases); setOverview(nextOverview);
    } catch (e) { setError(e instanceof Error ? e.message : "未知 API 错误"); }
    finally { setLoading(false); }
  }, [runId]);
  useEffect(() => { void load(); }, [load]);
  if (loading) return <main id="main" className="explorer-page"><ExplorerLoading label="正在读取 Run 与 Case 聚合…" /></main>;
  if (error || !run) return <main id="main" className="explorer-page"><ExplorerError message={error ?? "Run API 未返回数据"} retry={() => void load()} /></main>;
  const repeats = overview?.benchmark.repeats_per_case ?? 0;

  return <main id="main" className="explorer-page run-detail-page">
    <nav className="breadcrumb" aria-label="Breadcrumb"><a href="/runs">Runs</a><span>/</span><span aria-current="page">{shortId(run.run_id)}</span></nav>
    <PageIntro eyebrow={`${stageLabels[run.catalog.stage]} · ${roleLabels[run.catalog.role] ?? run.catalog.role}`} title={`${run.catalog.condition_family} · ${runtimeLabels[run.runtime_variant] ?? run.runtime_variant}`} description="这是一整次正式实验：下面先看是否完整跑完、五项正式指标，再下钻到 20 个 Case 和每次 Repeat。" meta={<><code title={run.run_id}>{shortId(run.run_id)}</code>{run.catalog.representative ? <span className="representative-badge">代表 Run</span> : null}</>} />

    <section className="run-identity-grid" aria-labelledby="run-identity-title"><div><p className="eyebrow">RUN STATUS</p><h2 id="run-identity-title">这次实验跑完整了吗？</h2><RunStatus run={run} /></div><dl><div><dt>Condition</dt><dd>{run.catalog.condition_family}</dd></div><div><dt>Runtime</dt><dd>{runtimeLabels[run.runtime_variant] ?? run.runtime_variant}</dd></div><div><dt>实验阶段</dt><dd>{stageLabels[run.catalog.stage]}</dd></div><div><dt>这次 Run 的角色</dt><dd>{roleLabels[run.catalog.role] ?? run.catalog.role}</dd></div><div><dt>Started</dt><dd>{dateTime(run.started_at)}</dd></div><div><dt>Completed</dt><dd>{dateTime(run.completed_at)}</dd></div><div><dt>已评分 / 计划</dt><dd>{run.scored_samples} / {run.planned_samples}</dd></div><div><dt>执行失败</dt><dd>{run.failed_samples}</dd></div></dl></section>

    <section className="explorer-section" aria-labelledby="metric-title"><header><p className="eyebrow">FORMAL METRICS</p><h2 id="metric-title">正式评测结果</h2><p>五项指标分别回答“有没有跑完、故障类型对不对、证据有没有命中、报告字段是否完整、输出协议是否有效”，不合成一个总分。</p></header><FormalMetrics metrics={run.suite_aggregate?.formal_metric_vector ?? null} /><MetricGuide /></section>

    <section className="explorer-section" aria-labelledby="provenance-title"><header><p className="eyebrow">EXPERIMENT IDENTITY</p><h2 id="provenance-title">这次结果是怎么产生的？</h2><p>这里记录这次 Run 使用的模型、Suite、Runtime 和各类 fingerprint。它们的作用是证明“这组结果到底来自哪套实验配置”。</p></header><ProvenanceSheet run={run} /></section>

    {run.failure_type_aggregates.length ? <section className="explorer-section" aria-labelledby="failure-types-title"><header><p className="eyebrow">BY FAILURE TYPE</p><h2 id="failure-types-title">不同类型故障下表现一样吗？</h2><p>把 60 个 Sample 按 5 类冻结故障标签拆开，快速看哪些类型更容易、哪些类型更难。</p></header><div className="aggregate-grid">{run.failure_type_aggregates.map((item) => <article key={item.failure_type}><h3><FailureTypeLabel value={item.failure_type} showCanonical /></h3><strong>{item.scored_sample_count} / {item.requested_sample_count}</strong><span>已评分 / 计划</span><dl><div><dt>Execution Coverage</dt><dd>{percent(item.formal_metric_vector.execution_coverage)}</dd></div><div><dt>Failure Type Exact Match</dt><dd>{percent(item.formal_metric_vector.failure_type_exact_match)}</dd></div></dl></article>)}</div></section> : null}

    <section className="explorer-section run-cases-section" aria-labelledby="run-cases-title"><header><p className="eyebrow">20 FROZEN CASES</p><h2 id="run-cases-title" aria-label="Frozen Cases">继续下钻到具体 Case</h2><p>每个冻结 Case 重复 3 次，共组成 60 个 Sample。点任意 Repeat 就能看到那一次真实报告、Agent 过程和 Runtime 记录。</p></header><div className="run-table-wrap"><table className="explorer-table case-aggregate-table"><thead><tr><th scope="col">Case</th><th scope="col">故障类型</th><th scope="col">3 次 Repeat 的结果</th><th scope="col">打开 Sample</th></tr></thead><tbody>{cases.map((item) => <tr key={item.case_id}><td data-label="Case"><span className="case-sequence">{String(item.case_sequence).padStart(2, "0")}</span><a href={`/cases/${item.case_id}`}>{item.case_id}</a></td><td data-label="故障类型"><FailureTypeLabel value={item.failure_type} showCanonical /></td><td data-label="3 次 Repeat 的结果"><strong>{item.scored_sample_count} / {item.requested_sample_count} 已评分</strong>{item.execution_failed_sample_count ? <small>{item.execution_failed_sample_count} 次执行失败</small> : <small>全部完成</small>}</td><td data-label="打开 Sample"><div className="repeat-links">{Array.from({ length: repeats }, (_, repeat) => <a key={repeat} href={`/runs/${run.run_id}/cases/${item.case_id}/${repeat}`}>Repeat {repeat}</a>)}</div></td></tr>)}</tbody></table></div></section>
  </main>;
}
