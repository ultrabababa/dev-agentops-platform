import { useCallback, useEffect, useMemo, useState } from "react";

import { getCases } from "../api/client";
import type { CaseMetadata } from "../api/types";
import { ExplorerError, ExplorerLoading, FailureTypeLabel, failureTypeLabels, HashValue, PageIntro } from "../components/ExplorerShared";

export function CasesPage() {
  const [cases, setCases] = useState<CaseMetadata[]>([]);
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try { setCases(await getCases()); }
    catch (e) { setError(e instanceof Error ? e.message : "未知 API 错误"); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  const failureTypes = useMemo(() => [...new Set(cases.map((item) => item.failure_type))], [cases]);
  const visible = filter === "all" ? cases : cases.filter((item) => item.failure_type === filter);

  return <main id="main" className="explorer-page cases-page">
    <PageIntro eyebrow="CASE CATALOG" title="冻结 Cases" description="这 20 个 Case 是所有正式实验共用的 benchmark 输入。这里看输入是什么、属于哪类故障、来源是否可公开；不展示模型答案或隐藏评分目标。" meta={<span className="sr-only">20 个正式实验共享的 frozen benchmark 输入。这里展示输入身份、failure type 与公开 provenance，不展示模型输出或隐藏评分目标。</span>} />
    <section className="explorer-filterbar interview-filterbar cases-filterbar" aria-label="筛选 Cases">
      <div className="filter-explainer"><p><strong>故障类型</strong><span>这是 benchmark 给每个冻结 Case 的分类，用来观察不同类型故障下的表现，不是模型本次预测结果。</span></p></div>
      <fieldset><legend>按故障类型筛选</legend><div className="filter-chips"><button type="button" aria-pressed={filter === "all"} onClick={() => setFilter("all")}>全部</button>{failureTypes.map((item) => <button type="button" key={item} aria-pressed={filter === item} onClick={() => setFilter(item)} title={item}>{failureTypeLabels[item] ?? item}<span className="sr-only">{item}</span></button>)}</div></fieldset>
      <span className="filter-count">显示 {visible.length} / {cases.length} Cases</span>
    </section>
    {loading ? <ExplorerLoading /> : error ? <ExplorerError message={error} retry={() => void load()} /> : <div className="run-table-wrap"><table className="explorer-table cases-table"><thead><tr><th className="case-index-head" scope="col"><span className="sr-only">序号</span></th><th scope="col">Case</th><th scope="col">故障类型</th><th scope="col">Schema / weight</th><th scope="col">公开来源</th><th scope="col">Sanitization</th></tr></thead><tbody>{visible.map((item, index) => <tr key={item.case_id}><td className="case-index-cell" aria-hidden="true"><span className="case-sequence">{String(index + 1).padStart(2, "0")}</span></td><td data-label="Case"><div className="case-primary"><a href={`/cases/${item.case_id}`}>{item.case_id}</a><HashValue value={item.case_fingerprint} /></div></td><td data-label="故障类型"><FailureTypeLabel value={item.failure_type} /><span className="sr-only">{item.failure_type}</span></td><td data-label="Schema / weight"><strong>Schema v{item.case_schema_version}</strong><small>weight {item.weight}</small></td><td data-label="公开来源"><span>{item.provenance.source_type ?? "—"}</span><small>{item.provenance.license_or_permission ?? "—"}</small></td><td data-label="Sanitization"><span className="sanitization-status" title={item.sanitization.status ?? undefined}>{item.sanitization.status?.replaceAll("_", " / ") ?? "—"}</span><a className="row-action" href={`/cases/${item.case_id}`}>打开 Case →</a></td></tr>)}</tbody></table></div>}
  </main>;
}
