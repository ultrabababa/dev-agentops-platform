import { useCallback, useEffect, useMemo, useState } from "react";

import { getCase, getOverview, getRuns } from "../api/client";
import type { CaseMetadata, Overview, Run } from "../api/types";
import { ExplorerError, ExplorerLoading, FailureTypeLabel, HashValue, PageIntro, runtimeLabels } from "../components/ExplorerShared";

export function CaseDetailPage({ caseId }: { caseId: string }) {
  const [item, setItem] = useState<CaseMetadata | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [runId, setRunId] = useState("");
  const [repeat, setRepeat] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [nextCase, nextRuns, nextOverview] = await Promise.all([getCase(caseId), getRuns(), getOverview()]);
      setItem(nextCase); setRuns(nextRuns); setOverview(nextOverview);
      setRunId((current) => current || nextRuns.find((run) => run.catalog.representative)?.run_id || nextRuns[0]?.run_id || "");
    } catch (e) { setError(e instanceof Error ? e.message : "未知 API 错误"); }
    finally { setLoading(false); }
  }, [caseId]);
  useEffect(() => { void load(); }, [load]);
  const representativeRuns = useMemo(() => {
    const preferred = runs.filter((run) => run.catalog.representative);
    return preferred.length ? preferred : runs;
  }, [runs]);
  if (loading) return <main id="main" className="explorer-page"><ExplorerLoading label="正在读取冻结 Case…" /></main>;
  if (error || !item) return <main id="main" className="explorer-page"><ExplorerError message={error ?? "Case API 未返回数据"} retry={() => void load()} /></main>;
  const selectedRun = runs.find((run) => run.run_id === runId);

  return <main id="main" className="explorer-page case-detail-page">
    <nav className="breadcrumb" aria-label="Breadcrumb"><a href="/cases">Cases</a><span>/</span><span aria-current="page">{item.case_id}</span></nav>
    <PageIntro eyebrow={`${item.failure_type} · schema v${item.case_schema_version}`} title="Case" identity={<code>{item.case_id}</code>} description="这是所有正式实验反复使用的同一个冻结 benchmark 输入。下面只展示公开身份、来源和 sanitization 状态。" />
    <section className="case-fingerprint-band" aria-label="Case fingerprint"><span>CASE FINGERPRINT</span><code>{item.case_fingerprint}</code></section>

    <section className="explorer-section case-facts" aria-labelledby="case-facts-title"><header><p className="eyebrow">CASE IDENTITY</p><h2 id="case-facts-title">这个 Case 从哪里来？</h2><p>这里说明输入来源、许可、fingerprint 和 sanitization；不展示隐藏的参考答案或评分目标。</p></header><dl className="provenance-sheet"><div><dt>Case ID</dt><dd><code>{item.case_id}</code></dd></div><div><dt>故障类型</dt><dd><FailureTypeLabel value={item.failure_type} showCanonical /></dd></div><div><dt>Weight</dt><dd>{item.weight}</dd></div><div><dt>Case schema</dt><dd>v{item.case_schema_version}</dd></div><div><dt>Fingerprint</dt><dd><HashValue value={item.case_fingerprint} /></dd></div><div><dt>Source type</dt><dd>{item.provenance.source_type ?? "—"}</dd></div><div className="wide"><dt>Source / construction note</dt><dd>{item.provenance.source_url_or_construction_note ?? "—"}</dd></div><div className="wide"><dt>License / permission</dt><dd>{item.provenance.license_or_permission ?? "—"}</dd></div><div><dt>Sanitization</dt><dd><span className="sanitization-status" title={item.sanitization.status ?? undefined}>{item.sanitization.status?.replaceAll("_", " / ") ?? "—"}</span></dd></div></dl></section>

    <section className="explorer-section cross-run-entry" aria-labelledby="cross-run-title"><header><p className="eyebrow">SAME CASE · DIFFERENT CONDITIONS</p><h2 id="cross-run-title" aria-label="在不同 Run 中查看这个 Case">同一个 Case，在不同运行方式下发生了什么？</h2><p>先选一个代表 Condition，再选 Repeat 0 / 1 / 2，就能打开那一次真实 Sample。其他历史和优化实验仍可在 Runs 页面查看。</p></header>
      <div className="sample-picker interview-sample-picker">
        <fieldset><legend>代表 Condition</legend><div className="run-choice-grid">{representativeRuns.map((run) => <button type="button" key={run.run_id} aria-pressed={runId === run.run_id} onClick={() => setRunId(run.run_id)}><strong>{run.catalog.condition_family}</strong><span>{runtimeLabels[run.runtime_variant] ?? run.runtime_variant}</span></button>)}</div></fieldset>
        <fieldset><legend>Repeat · 同一 Case 的第几次重复</legend><div className="segmented-control">{Array.from({ length: overview?.benchmark.repeats_per_case ?? 0 }, (_, index) => <button type="button" aria-pressed={repeat === index} onClick={() => setRepeat(index)} key={index}>{index}</button>)}</div></fieldset>
        {selectedRun ? <a className="button primary" href={`/runs/${selectedRun.run_id}/cases/${item.case_id}/${repeat}`}>打开 Sample →</a> : null}
        <a className="secondary-link" href="/runs">查看全部 12 次正式 Run →</a>
      </div>
    </section>
  </main>;
}
