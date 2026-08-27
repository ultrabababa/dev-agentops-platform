import { useCallback, useEffect, useState } from "react";

import { getHomepageData } from "./api/client";
import type { ConditionId, HomepageData } from "./api/types";
import { ConditionDetailPage } from "./pages/ConditionDetailPage";
import { ConditionOverviewPage } from "./pages/ConditionOverviewPage";
import { Homepage } from "./pages/Homepage";

const navigation = [
  ["项目概览", "/"], ["实验条件", "/conditions"], ["正式实验", "/runs"],
  ["实验对比", "/compare"], ["Cases", "/cases"],
] as const;

const placeholderCopy: Record<string, [string, string]> = {
  "/runs": ["正式实验", "Runs Explorer 将在后续阶段开放。"],
  "/compare": ["实验对比", "完整 comparison page 将在后续阶段开放。"],
  "/cases": ["Cases", "Case drill-down 将在后续阶段开放。"],
};

function SiteHeader({ path }: { path: string }) {
  return (
    <header className="site-header">
      <a className="brand" href="/" aria-label="DevAgentOps 项目概览">
        <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
        <span><strong>DevAgentOps</strong><small>Evaluation Explorer</small></span>
      </a>
      <nav aria-label="主导航">
        {navigation.map(([label, href]) => {
          const active = path === href || (href === "/conditions" && path.startsWith("/conditions/"));
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
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">跳到主要内容</a><SiteHeader path={path} />
      {path === "/conditions" ? <ConditionOverviewPage /> : detailId ? <ConditionDetailPage id={detailId} /> : path !== "/" ? <Placeholder path={path} /> : loading && !data ? <LoadingState /> : error || !data ? <ErrorState message={error ?? "API 未返回数据"} retry={() => void load()} /> : <main id="main"><Homepage data={data} /></main>}
      <SiteFooter />
    </div>
  );
}

export default App;
