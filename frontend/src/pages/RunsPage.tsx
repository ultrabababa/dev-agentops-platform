import { useCallback, useEffect, useMemo, useState } from "react";

import { getRuns } from "../api/client";
import type { ExplorerStage, FormalMetricVector, Run } from "../api/types";
import { dateTime, ExplorerError, ExplorerLoading, percent, PageIntro, roleLabels, RunStatus, runtimeLabels, shortId, stageLabels } from "../components/ExplorerShared";

const conditions = ["L1", "L2", "L3", "L4", "Oracle"] as const;
const stageOrder: ExplorerStage[] = ["baseline", "canonicalization", "runtime_optimization", "retrieval_attribution"];

function KeyMetrics({ metrics }: { metrics: FormalMetricVector | null }) {
  if (!metrics) return <span className="empty-inline">指标不可用</span>;
  return <div className="run-key-metrics" aria-label="Run 关键指标">
    <span title="Failure Type Exact Match"><small>故障类型</small><strong>{percent(metrics.failure_type_exact_match)}</strong></span>
    <span title="Report Evidence Hit Rate"><small>证据命中</small><strong>{percent(metrics.report_evidence_hit_rate)}</strong></span>
    <span title="Protocol Validity"><small>协议有效</small><strong>{percent(metrics.protocol_validity_rate)}</strong></span>
    <span className="sr-only">Execution Coverage</span><span className="sr-only">Failure Type Exact Match</span><span className="sr-only">Report Evidence Hit Rate</span><span className="sr-only">Required Fields Completeness</span><span className="sr-only">Protocol Validity</span>
  </div>;
}

export function RunsPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [condition, setCondition] = useState("all");
  const [stage, setStage] = useState("all");
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try { setRuns(await getRuns()); }
    catch (e) { setError(e instanceof Error ? e.message : "未知 API 错误"); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  const filtered = useMemo(() => runs.filter((run) => (condition === "all" || run.catalog.condition_family === condition) && (stage === "all" || run.catalog.stage === stage)), [runs, condition, stage]);
  const groups = useMemo(() => stageOrder.map((key) => ({ key, label: stageLabels[key], runs: filtered.filter((run) => run.catalog.stage === key) })).filter((group) => group.runs.length), [filtered]);

  return <main id="main" className="explorer-page runs-page">
    <PageIntro eyebrow="RUN EXPLORER" title="正式实验 Runs" description="这里汇总项目的 12 次正式 Run。先看 Agent 用哪种运行方式、这次实验为什么要跑，再继续下钻到 Case 与单次 Sample。" meta={<span>Run → Case → Sample → Evidence</span>} />

    <section className="explorer-filterbar interview-filterbar" aria-label="筛选 Runs">
      <div className="filter-explainer">
        <p><strong>Condition</strong><span>Agent 用哪种运行方式。L1–L4 是四种 Runtime / Evidence 条件，Oracle 是独立诊断条件。</span></p>
        <p><strong>实验阶段</strong><span>这次 Run 在开发过程中的目的：建立基线、验证规范化、优化 Runtime，或定位 Retrieval 的证据损失。</span></p>
      </div>
      <fieldset><legend>Condition · 运行方式</legend><div className="filter-chips"><button type="button" aria-pressed={condition === "all"} onClick={() => setCondition("all")}>全部</button>{conditions.map((item) => <button type="button" key={item} aria-pressed={condition === item} onClick={() => setCondition(item)}>{item}</button>)}</div></fieldset>
      <fieldset><legend>实验阶段 · 为什么跑</legend><div className="filter-chips"><button type="button" aria-pressed={stage === "all"} onClick={() => setStage("all")}>全部</button>{stageOrder.map((item) => <button type="button" key={item} aria-pressed={stage === item} onClick={() => setStage(item)}>{stageLabels[item]}</button>)}</div></fieldset>
      <span className="filter-count">显示 {filtered.length} / {runs.length} Runs</span>
    </section>

    {loading ? <ExplorerLoading /> : error ? <ExplorerError message={error} retry={() => void load()} /> : groups.length === 0 ? <div className="explorer-state"><span className="state-index">0</span><div><h2>没有符合筛选条件的 Run</h2><p>换一个运行方式或实验阶段即可。</p></div></div> : groups.map((group) => <section className="run-stage" key={group.key} aria-labelledby={`stage-${group.key}`}>
      <header><p>{group.label}</p><h2 id={`stage-${group.key}`}>{group.key === "baseline" ? "最早的可比较基线" : group.key === "canonicalization" ? "规范化后的正式代表结果" : group.key === "runtime_optimization" ? "Runtime 执行策略优化" : "Retrieval 证据获取与引用归因"}</h2><span>{group.runs.length} Runs</span></header>
      <div className="run-table-wrap"><table className="explorer-table runs-table"><thead><tr><th scope="col">Run</th><th scope="col">这次 Run 的角色</th><th scope="col">Samples</th><th scope="col">关键结果</th><th scope="col">时间 / 入口</th></tr></thead><tbody>{group.runs.map((run) => <tr key={run.run_id} className={run.catalog.representative ? "representative-row" : ""}>
        <td data-label="Run"><div className="run-primary"><span className="condition-stamp">{run.catalog.condition_family}</span><div><a href={`/runs/${run.run_id}`}>{runtimeLabels[run.runtime_variant] ?? run.runtime_variant}</a><code title={run.run_id}>{shortId(run.run_id)}</code></div></div></td>
        <td data-label="这次 Run 的角色"><div className="run-role">{run.catalog.representative ? <span className="representative-badge">代表 Run<span className="sr-only">Representative</span></span> : null}<span>{roleLabels[run.catalog.role] ?? run.catalog.role}</span><RunStatus run={run} /></div></td>
        <td data-label="Samples"><strong className="sample-count">{run.scored_samples} / {run.planned_samples}</strong><small>已评分 / 计划</small></td>
        <td data-label="关键结果"><KeyMetrics metrics={run.suite_aggregate?.formal_metric_vector ?? null} /></td>
        <td data-label="时间 / 入口" className="run-start-cell"><time dateTime={run.started_at}>{dateTime(run.started_at)}</time><a className="row-action" href={`/runs/${run.run_id}`}>打开 Run →</a></td>
      </tr>)}</tbody></table></div>
    </section>)}
  </main>;
}
