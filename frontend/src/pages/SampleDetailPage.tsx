import { useCallback, useEffect, useRef, useState } from "react";

import { getOverview, getRun, getSample, getTrace, getTrajectory } from "../api/client";
import type { Overview, Run, Sample, TraceEvent, TraceResponse, TrajectoryResponse } from "../api/types";
import { ExplorerError, ExplorerLoading, FailureTypeLabel, PageIntro, percent, ProvenanceSheet, runtimeLabels, shortId } from "../components/ExplorerShared";

const tabs = [
  { key: "Structured Report", label: "诊断报告", canonical: "Report" },
  { key: "Evidence", label: "引用证据", canonical: "Evidence" },
  { key: "Trajectory", label: "Agent 过程", canonical: "Trajectory" },
  { key: "Trace", label: "Runtime 事件", canonical: "Trace" },
  { key: "Provenance", label: "实验身份", canonical: "Provenance" },
] as const;
type Tab = typeof tabs[number]["key"];

function DataFields({ value }: { value: Record<string, unknown> }) {
  return <dl className="payload-fields">{Object.entries(value).map(([key, item]) => <div key={key}><dt>{key}</dt><dd>{item == null ? "—" : typeof item === "object" ? <code>{Object.entries(item as Record<string, unknown>).map(([nestedKey, nestedValue]) => `${nestedKey}: ${String(nestedValue)}`).join(" · ")}</code> : typeof item === "boolean" ? String(item) : String(item)}</dd></div>)}</dl>;
}

function CompactContent({ text, label = "完整内容", previewLines = 6 }: { text: string; label?: string; previewLines?: number }) {
  const [expanded, setExpanded] = useState(false);
  const lines = text.split("\n");
  const isLong = lines.length > previewLines + 2 || text.length > 900;
  if (!isLong) return <pre className="visible-content">{text}</pre>;
  const preview = lines.slice(0, previewLines).join("\n");
  return <div className="compact-content"><pre className="visible-content">{expanded ? text : `${preview}\n…`}</pre><button type="button" aria-expanded={expanded} onClick={() => setExpanded((current) => !current)}>{expanded ? `收起${label}` : `展开${label} · ${lines.length} 行`}</button></div>;
}

function StructuredReportView({ sample }: { sample: Sample }) {
  if (!sample.report) return <div className="sample-empty"><h3>这次 Sample 没有生成 Structured Report。</h3><p>{sample.outcome.status === "execution_failed" ? `执行在 ${sample.outcome.failure_stage ?? "unknown stage"} 失败，因此没有报告可评分。` : "公开 Sample 记录中没有报告。"}</p>{sample.outcome.failure_code ? <code>{sample.outcome.failure_code}</code> : null}{sample.outcome.failure_message ? <p>{sample.outcome.failure_message}</p> : null}</div>;
  const report = sample.report;
  return <div className="report-layout"><article className="structured-report"><header><div><span>分类状态</span><strong>{report.classification_status ?? "—"}</strong></div><div><span>故障类型</span><strong>{report.failure_type ? <FailureTypeLabel value={report.failure_type} /> : "—"}</strong></div><div><span>置信度</span><strong>{report.confidence == null ? "—" : percent(report.confidence)}</strong></div><div><span>报告版本</span><strong>v{report.schema_version ?? "—"}</strong></div></header>{report.summary ? <section><h3>现象摘要</h3><p>{report.summary}</p></section> : null}{report.root_cause ? <section><h3>根因判断</h3><p>{report.root_cause}</p></section> : null}{report.recommended_action ? <section><h3>建议动作</h3><p>{report.recommended_action}</p></section> : null}</article><aside className={`validation-card ${sample.validation?.valid ? "valid" : "invalid"}`}><span>REPORT VALIDATION</span><strong>{sample.validation?.valid ? "Valid" : "Invalid"}</strong>{sample.validation?.errors?.length ? <ul>{sample.validation.errors.map((error, index) => <li key={`${error.code}-${index}`}><code>{error.code ?? "validation_error"}</code><span>{[error.field, error.message].filter(Boolean).join(" · ")}</span></li>)}</ul> : <p>{sample.validation ? "报告结构校验通过，没有 validation errors。" : "Validation result unavailable."}</p>}</aside></div>;
}

function EvidenceView({ sample }: { sample: Sample }) {
  const references = sample.report?.evidence_references ?? [];
  return <div className="evidence-view"><header><div><p className="eyebrow">CITED EVIDENCE</p><h2>这份报告引用了哪些证据？</h2></div><p>这里只显示模型最终报告主动引用的公开 Evidence IDs。隐藏的评测目标、参考答案和选择依据不会展示。</p></header>{references.length ? <ol className="evidence-list">{references.map((reference, index) => <li key={`${reference.evidence_id}-${index}`}><span>{String(index + 1).padStart(2, "0")}</span><code>{reference.evidence_id}</code></li>)}</ol> : <div className="sample-empty"><h3>报告没有公开 Evidence references。</h3><p>{sample.report ? "这是有效的空引用状态。" : "本次执行没有生成可引用 Evidence 的报告。"}</p></div>}<section className="score-summary" aria-labelledby="score-summary-title"><h3 id="score-summary-title">这一次 Sample 的评分</h3>{sample.validation ? <div><span>Report validation</span><strong>{sample.validation.valid ? "Valid" : "Invalid"}</strong></div> : null}{sample.score?.failure_type_exact_match != null ? <div><span>Failure Type Exact Match</span><strong>{percent(sample.score.failure_type_exact_match)}</strong></div> : null}{sample.score?.report_evidence_hit_rate != null ? <div><span>Report Evidence Hit Rate</span><strong>{percent(sample.score.report_evidence_hit_rate)}</strong></div> : null}{sample.score?.required_fields_completeness != null ? <div><span>Required Fields Completeness</span><strong>{percent(sample.score.required_fields_completeness)}</strong></div> : null}{!sample.validation && !sample.score ? <p>该 Sample 没有 validation 或公开 score。</p> : null}</section></div>;
}

function TrajectoryView({ data, loading, error, retry }: { data: TrajectoryResponse | null; loading: boolean; error: string | null; retry: () => void }) {
  if (loading) return <ExplorerLoading label="正在读取公开 Trajectory…" />;
  if (error) return <ExplorerError message={error} retry={retry} />;
  if (!data?.messages.length) return <div className="sample-empty"><h3 aria-label="此 Run 没有可公开展示的 Trajectory。">这个 Run 没有保存可公开展示的 Agent 过程。</h3><p>该实验版本没有保存这一层数据。这是有效的历史数据状态，不是 API 错误，也不会用 Trace 拼出一份假的对话。</p></div>;
  const modelDecisions = data.messages.filter((message) => message.role === "assistant").length;
  const toolCalls = data.messages.reduce((count, message) => count + message.tool_calls.length, 0);
  const toolResults = data.messages.filter((message) => message.role === "tool_result").length;
  const totalTokens = data.messages.reduce((sum, message) => sum + (message.usage?.total_tokens ?? 0), 0);

  return <div className="trajectory-view"><div className="timeline-explainer"><strong>Agent 调查过程</strong><span>模型实际看到的交互历史</span><p>Trajectory 只包含模型可见的消息和工具交互。默认收起大段上下文与 ToolResult，需要时再展开。</p></div><div className="journey-summary"><div><span>模型决策</span><strong>{modelDecisions}</strong></div><div><span>ToolCalls</span><strong>{toolCalls}</strong></div><div><span>ToolResults</span><strong>{toolResults}</strong></div><div><span>累计 tokens</span><strong>{totalTokens || "—"}</strong></div></div><ol className="trajectory-list compact-trajectory">{data.messages.map((message) => {
    const label = message.role === "user" ? "初始输入" : message.role === "tool_result" ? `工具结果${message.tool_name ? ` · ${message.tool_name}` : ""}` : message.tool_calls.length ? "模型决定调用工具" : "模型输出";
    return <li key={message.message_index} className={`trajectory-message role-${message.role}`}><div className="timeline-rail"><span>{String(message.message_index).padStart(2, "0")}</span><i /></div><article><header><strong>{label}</strong><div>{message.stop_reason ? <span>stop: {message.stop_reason}</span> : null}{message.response_model ? <span>{message.response_model}</span> : null}{message.usage?.total_tokens != null ? <span>{message.usage.total_tokens} tokens</span> : null}</div></header>{message.visible_content ? <CompactContent text={message.visible_content} label={message.role === "user" ? "初始上下文" : message.role === "tool_result" ? "ToolResult" : "模型输出"} previewLines={message.role === "tool_result" ? 5 : 4} /> : null}{message.tool_calls.map((call) => <section className="tool-block" key={call.tool_call_id}><header><span>调用工具 <b className="canonical-inline">TOOL CALL</b></span><strong>{call.tool_name}</strong><code>{call.tool_call_id}</code></header>{call.arguments ? <DataFields value={call.arguments} /> : <p>没有公开 arguments。</p>}</section>)}{message.role === "tool_result" ? <section className={`tool-block result ${message.is_error ? "is-error" : ""}`}><header><span>{message.is_error ? "工具返回错误" : "工具执行完成"} <b className="canonical-inline">TOOL RESULT</b></span><strong>{message.tool_name ?? "unknown tool"}</strong><code>{message.tool_call_id ?? "—"}</code></header></section> : null}</article></li>;
  })}</ol></div>;
}

const traceEventLabels: Record<string, string> = {
  sample_started: "Sample 开始", l4_execution_started: "Runtime 开始", model_call_started: "模型调用开始", model_call_completed: "模型调用完成", tool_call_started: "工具调用开始", tool_call_completed: "工具调用完成", report_submitted: "报告已提交", agent_terminal: "Agent 结束", evaluation_completed: "评测完成", sample_completed: "Sample 完成",
};

function TraceView({ data, loading, error, retry }: { data: TraceResponse | null; loading: boolean; error: string | null; retry: () => void }) {
  const [showAll, setShowAll] = useState(false);
  if (loading) return <ExplorerLoading label="正在读取公开 Trace…" />;
  if (error) return <ExplorerError message={error} retry={retry} />;
  if (!data?.events.length) return <div className="sample-empty"><h3>此 Sample 没有可公开展示的 Trace。</h3><p>Trace API 返回了有效空事件列表。</p></div>;
  const modelCalls = data.events.filter((event) => event.event_type === "model_call_completed");
  const toolCalls = data.events.filter((event) => event.event_type === "tool_call_completed");
  const totalLatency = modelCalls.reduce((sum, event) => sum + (typeof event.payload.latency_ms === "number" ? event.payload.latency_ms : 0), 0);
  const compactTypes = new Set(["sample_started", "model_call_completed", "tool_call_completed", "report_submitted", "agent_terminal", "sample_completed"]);
  const visibleEvents = showAll ? data.events : data.events.filter((event) => compactTypes.has(event.event_type));
  return <div className="trace-view"><div className="timeline-explainer"><strong>Runtime 执行摘要</strong><span>Runtime 另外记录的执行事件，不是对话</span><p>默认只看关键节点；需要排查执行细节时再展开完整 Trace。</p></div><div className="journey-summary"><div><span>模型调用</span><strong>{modelCalls.length}</strong></div><div><span>工具调用</span><strong>{toolCalls.length}</strong></div><div><span>模型调用耗时</span><strong>{totalLatency ? `${(totalLatency / 1000).toFixed(1)}s` : "—"}</strong></div><div><span>完整 Trace</span><strong>{data.events.length} events</strong></div></div><div className="trace-mode"><button type="button" aria-pressed={showAll} onClick={() => setShowAll((current) => !current)}>{showAll ? "只看关键事件" : `查看完整 Trace · ${data.events.length} events`}</button></div><ol className="trace-list compact-trace">{visibleEvents.map((event) => <TraceEventRow event={event} key={`${event.sequence}-${event.event_type}`} />)}</ol></div>;
}

function TraceEventRow({ event }: { event: TraceEvent }) {
  const [expanded, setExpanded] = useState(false);
  const primaryKeys = ["step", "attempt_index", "latency_ms", "status", "terminal_reason", "tool_name", "tool_call_id", "truncated", "usage"];
  const primary = Object.fromEntries(Object.entries(event.payload).filter(([key]) => primaryKeys.includes(key)));
  const secondary = Object.fromEntries(Object.entries(event.payload).filter(([key]) => !primaryKeys.includes(key)));
  const detailId = `trace-detail-${event.sequence}`;
  const time = event.occurred_at.includes("T") ? event.occurred_at.split("T")[1]?.replace("Z", "") : event.occurred_at;
  return <li><div className="timeline-rail"><span>{String(event.sequence).padStart(3, "0")}</span><i /></div><article><header><div><strong>{traceEventLabels[event.event_type] ?? event.event_type}</strong><code>{event.event_type}</code><time dateTime={event.occurred_at}>{time}</time></div></header>{Object.keys(primary).length ? <DataFields value={primary} /> : null}{Object.keys(secondary).length ? <div className="trace-disclosure"><button type="button" aria-label={expanded ? "收起公开 event fields" : "更多公开 event fields"} aria-expanded={expanded} aria-controls={detailId} onClick={() => setExpanded((current) => !current)}>{expanded ? "收起详细字段" : "查看详细字段"}</button>{expanded ? <div id={detailId}><DataFields value={secondary} /></div> : null}</div> : null}</article></li>;
}

export function SampleDetailPage({ runId, caseId, repeat }: { runId: string; caseId: string; repeat: number }) {
  const [sample, setSample] = useState<Sample | null>(null);
  const [run, setRun] = useState<Run | null>(null);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("Structured Report");
  const [trajectory, setTrajectory] = useState<TrajectoryResponse | null>(null);
  const [trajectoryError, setTrajectoryError] = useState<string | null>(null);
  const [trajectoryLoading, setTrajectoryLoading] = useState(false);
  const [trace, setTrace] = useState<TraceResponse | null>(null);
  const [traceError, setTraceError] = useState<string | null>(null);
  const [traceLoading, setTraceLoading] = useState(false);
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const load = useCallback(async () => { setLoading(true); setError(null); try { const [nextSample, nextRun, nextOverview] = await Promise.all([getSample(runId, caseId, repeat), getRun(runId), getOverview()]); setSample(nextSample); setRun(nextRun); setOverview(nextOverview); } catch (e) { setError(e instanceof Error ? e.message : "未知 API 错误"); } finally { setLoading(false); } }, [runId, caseId, repeat]);
  const loadTrajectory = useCallback(async () => { if (trajectory || trajectoryLoading) return; setTrajectoryLoading(true); setTrajectoryError(null); try { setTrajectory(await getTrajectory(runId, caseId, repeat)); } catch (e) { setTrajectoryError(e instanceof Error ? e.message : "未知 API 错误"); } finally { setTrajectoryLoading(false); } }, [trajectory, trajectoryLoading, runId, caseId, repeat]);
  const loadTrace = useCallback(async () => { if (trace || traceLoading) return; setTraceLoading(true); setTraceError(null); try { setTrace(await getTrace(runId, caseId, repeat)); } catch (e) { setTraceError(e instanceof Error ? e.message : "未知 API 错误"); } finally { setTraceLoading(false); } }, [trace, traceLoading, runId, caseId, repeat]);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => { if (tab === "Trajectory") void loadTrajectory(); if (tab === "Trace") void loadTrace(); }, [tab, loadTrajectory, loadTrace]);
  const selectTab = (next: Tab) => setTab(next);
  const onTabKeyDown = (event: React.KeyboardEvent, index: number) => { if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return; event.preventDefault(); const nextIndex = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length; selectTab(tabs[nextIndex].key); tabRefs.current[nextIndex]?.focus(); };
  if (loading) return <main id="main" className="explorer-page"><ExplorerLoading label="正在读取 Sample evidence…" /></main>;
  if (error || !sample || !run) return <main id="main" className="explorer-page"><ExplorerError message={error ?? "Sample API 未返回数据"} retry={() => void load()} /></main>;
  const repeatCount = overview?.benchmark.repeats_per_case ?? 0;
  const activeTabIndex = tabs.findIndex((item) => item.key === tab);

  return <main id="main" className="explorer-page sample-page"><nav className="breadcrumb" aria-label="Breadcrumb"><a href="/runs">Runs</a><span>/</span><a href={`/runs/${run.run_id}`}>{shortId(run.run_id)}</a><span>/</span><a href={`/cases/${caseId}`}>{caseId}</a><span>/</span><span aria-current="page">Repeat {repeat}</span></nav><PageIntro eyebrow={`${run.catalog.condition_family} · ${runtimeLabels[run.runtime_variant] ?? run.runtime_variant}`} title={`Sample · Repeat ${repeat}`} identity={<code>{caseId}</code>} description="查看这一次真实 Sample 的诊断报告、引用证据、Agent 调查过程、Runtime 执行记录和实验身份。" meta={<><span className={`sample-status status-${sample.outcome.status}`}>{sample.outcome.status}</span><span>{sample.trajectory_available ? "有 Agent 过程" : "无 Trajectory"}</span><span>{sample.trace_available ? "有 Runtime Trace" : "无 Trace"}</span></>} />
    <div className="sample-context-bar"><div><span>故障类型</span><FailureTypeLabel value={sample.outcome.evaluation_failure_type} /></div><nav aria-label="相邻 repeats">{Array.from({ length: repeatCount }, (_, index) => <a key={index} aria-current={repeat === index ? "page" : undefined} href={`/runs/${runId}/cases/${caseId}/${index}`}>Repeat {index}</a>)}</nav><div><a href={`/runs/${runId}`}>← 返回 Run</a><a href={`/cases/${caseId}`}>返回 Case</a></div></div>
    <section className="sample-evidence-viewer" aria-label="Sample evidence viewer"><div className="sample-tabs" role="tablist" aria-label="Sample public views">{tabs.map((item, index) => <button key={item.key} ref={(node) => { tabRefs.current[index] = node; }} type="button" role="tab" aria-label={item.key} aria-selected={tab === item.key} aria-controls={`panel-${index}`} id={`tab-${index}`} tabIndex={tab === item.key ? 0 : -1} onClick={() => selectTab(item.key)} onKeyDown={(event) => onTabKeyDown(event, index)}><span>{item.label}</span><small>{item.canonical}</small></button>)}</div><div className="sample-tab-panel" role="tabpanel" id={`panel-${activeTabIndex}`} aria-labelledby={`tab-${activeTabIndex}`} tabIndex={0}>{tab === "Structured Report" ? <StructuredReportView sample={sample} /> : tab === "Evidence" ? <EvidenceView sample={sample} /> : tab === "Trajectory" ? <TrajectoryView data={trajectory} loading={trajectoryLoading} error={trajectoryError} retry={() => { setTrajectory(null); void loadTrajectory(); }} /> : tab === "Trace" ? <TraceView data={trace} loading={traceLoading} error={traceError} retry={() => { setTrace(null); void loadTrace(); }} /> : <div className="provenance-tab"><header><p className="eyebrow">SAMPLE PROVENANCE</p><h2 aria-label="这份报告来自哪一套输入、Runtime 和评分合同？">这份 Sample 是怎么产生的？</h2><p>下面的 Run、模型、Suite、Runtime 和 fingerprint 共同标识这一次实验配置，方便复现和核对结果来源。</p></header><ProvenanceSheet run={run} sampleIdentity={{ case_id: caseId, repeat_index: repeat }} /></div>}</div></section>
  </main>;
}
