import { useCallback, useEffect, useState } from "react";

import { getHomepageData } from "./api/client";
import type { ConditionId, HomepageData } from "./api/types";
import { ConditionDetailPage } from "./pages/ConditionDetailPage";
import { ConditionOverviewPage } from "./pages/ConditionOverviewPage";
import { Homepage } from "./pages/Homepage";
import { RunsPage } from "./pages/RunsPage";
import { RunDetailPage } from "./pages/RunDetailPage";
import { CasesPage } from "./pages/CasesPage";
import { CaseDetailPage } from "./pages/CaseDetailPage";
import { SampleDetailPage } from "./pages/SampleDetailPage";
import { ComparePage } from "./pages/ComparePage";

const navigation = [
  ["项目概览", "/"], ["实验条件", "/conditions"], ["正式实验", "/runs"],
  ["实验与归因", "/compare"], ["Cases", "/cases"],
] as const;

const placeholderCopy: Record<string, [string, string]> = {};

function SiteHeader({ path }: { path: string }) {
  return (
    <header className="site-header">
      <a className="brand" href="/" aria-label="DevAgentOps 项目概览">
        <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
        <span><strong>DevAgentOps</strong><small>Evaluation Explorer</small></span>
      </a>
      <nav aria-label="主导航">
        {navigation.map(([label, href]) => {
          const active = path === href || (href !== "/" && path.startsWith(`${href}/`));
          return <a key={href} href={href} aria-current={active ? "page" : undefined}>{label}</a>;
        })}
        <a href="https://github.com/ultrabababa/dev-agentops-platform" target="_blank" rel="noreferrer">GitHub ↗</a>
      </nav>
    </header>
  );
}

function LoadingState() {
  return <div className="loading-page" aria-busy="true" aria-label="正在读取正式评测数据"><div><span>PUBLIC EVALUATION EXPLORER</span><h1>正在读取冻结实验数据</h1><p>Overview · Conditions · Experiment Evolution</p></div><i /></div>;
}

function ErrorState({ message, retry }: { message: string; retry: () => void }) {
  return (
    <main className="error-page" id="main" role="alert">
      <p className="eyebrow">Evaluation data unavailable</p><h1>产品说明仍可阅读，实验事实暂不展示。</h1>
      <p>首页没有用静态值替代失败的 API 响应。请确认 FastAPI 与 Phase 1 showcase data 可用后重试。</p>
      <code>{message}</code><button type="button" onClick={retry}>重新读取</button>
    </main>
  );
}

function Placeholder({ path }: { path: string }) {
  const [title, description] = placeholderCopy[path] ?? ["页面不存在", "返回项目概览继续浏览。"];
  return <main className="placeholder-page" id="main"><p className="eyebrow">Phase 2A · Route prepared</p><h1>{title}</h1><p>{description}</p><a className="text-link" href="/">← 返回项目概览</a></main>;
}

function SiteFooter() {
  return <footer className="site-footer"><div><strong>DevAgentOps</strong><p>Evaluation-driven runtime engineering for reproducible agent failure triage.</p></div><div><span>Frozen inputs</span><span>Deterministic scoring</span><span>Reproducible provenance</span></div></footer>;
}

function App() {
  const path = window.location.pathname.replace(/\/$/, "") || "/";
  const detailMatch = path.match(/^\/conditions\/(l1|l2|l3|l4|oracle)$/);
  const detailId = detailMatch ? (detailMatch[1] === "oracle" ? "Oracle" : detailMatch[1].toUpperCase()) as ConditionId : null;
  const runDetailMatch = path.match(/^\/runs\/([^/]+)$/);
  const sampleMatch = path.match(/^\/runs\/([^/]+)\/cases\/([^/]+)\/(\d+)$/);
  const caseDetailMatch = path.match(/^\/cases\/([^/]+)$/);
  const [data, setData] = useState<HomepageData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(path === "/");
  const load = useCallback(async () => {
    if (path !== "/") return;
    setLoading(true); setError(null);
    try { setData(await getHomepageData()); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "未知 API 错误"); }
    finally { setLoading(false); }
  }, [path]);
  useEffect(() => { void load(); }, [load]);
  let page;
  if (path === "/conditions") page = <ConditionOverviewPage />;
  else if (detailId) page = <ConditionDetailPage id={detailId} />;
  else if (path === "/runs") page = <RunsPage />;
  else if (path === "/compare") page = <ComparePage />;
  else if (sampleMatch) page = <SampleDetailPage runId={decodeURIComponent(sampleMatch[1])} caseId={decodeURIComponent(sampleMatch[2])} repeat={Number(sampleMatch[3])} />;
  else if (runDetailMatch) page = <RunDetailPage runId={decodeURIComponent(runDetailMatch[1])} />;
  else if (path === "/cases") page = <CasesPage />;
  else if (caseDetailMatch) page = <CaseDetailPage caseId={decodeURIComponent(caseDetailMatch[1])} />;
  else if (path !== "/") page = <Placeholder path={path} />;
  else if (loading && !data) page = <LoadingState />;
  else if (error || !data) page = <ErrorState message={error ?? "API 未返回数据"} retry={() => void load()} />;
  else page = <main id="main"><Homepage data={data} /></main>;
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">跳到主要内容</a><SiteHeader path={path} />
      {page}
      <SiteFooter />
    </div>
  );
}

export default App;
