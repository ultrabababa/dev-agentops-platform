import { useCallback, useEffect, useState } from "react";

import { getHomepageData } from "./api/client";
import type { ConditionId, HomepageData } from "./api/types";
import { ArchitecturePage } from "./pages/ArchitecturePage";
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
  ["实验与归因", "/compare"], ["系统架构", "/architecture"], ["Cases", "/cases"],
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

function formatElapsed(seconds: number) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, "0");
  const remaining = (seconds % 60).toString().padStart(2, "0");
  return `${minutes}:${remaining}`;
}

function LoadingState({ seconds }: { seconds: number }) {
  const phase = seconds >= 50
    ? {
        title: "仍在等待 Evaluation API",
        copy: "冷启动时间较长，但当前请求仍在进行。请保持页面打开；API 返回后会自动进入项目概览。",
      }
    : seconds >= 8
      ? {
          title: "正在唤醒 Evaluation API",
          copy: "Render 免费实例可能正在从休眠中唤醒。首次访问可能需要 50 秒以上，API 就绪后页面会自动继续。",
        }
      : {
          title: "正在连接 Evaluation API",
          copy: "正在请求 Overview · Conditions · Experiment Evolution。",
        };

  return (
    <main className="loading-page" id="main" aria-busy="true" aria-label="正在读取正式评测数据">
      <section className="loading-panel">
        <p className="loading-kicker">PUBLIC EVALUATION EXPLORER</p>
        <h1 aria-live="polite">{phase.title}</h1>
        <p className="loading-copy">{phase.copy}</p>
        <div className="loading-elapsed" aria-label={`已等待 ${seconds} 秒`}>
          <strong>{formatElapsed(seconds)}</strong>
          <span>已等待</span>
        </div>
        <div className="loading-progress" role="progressbar" aria-label="Evaluation API 请求进行中"><i /></div>
        <div className="loading-status" aria-label="当前加载状态">
          <span><b>REQUEST</b> IN FLIGHT</span>
          <span><b>DATA</b> PENDING</span>
        </div>
      </section>
      <aside className="loading-context" aria-hidden="true">
        <span>RUN</span><i /><span>RECORD</span><i /><span>SCORE</span><i /><span>ATTRIBUTE</span><i /><strong>EVOLVE</strong>
      </aside>
    </main>
  );
}

function ErrorState({ message, retry }: { message: string; retry: () => void }) {
  return (
    <main className="error-page" id="main" role="alert">
      <p className="eyebrow">Evaluation data unavailable</p><h1>产品说明仍可阅读，实验事实暂不展示。</h1>
      <p>首页没有用静态值替代失败的 API 响应。请确认 Evaluation API 可用后重试。</p>
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
  const [waitSeconds, setWaitSeconds] = useState(0);
  const load = useCallback(async () => {
    if (path !== "/") return;
    setWaitSeconds(0); setLoading(true); setError(null);
    try { setData(await getHomepageData()); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "未知 API 错误"); }
    finally { setLoading(false); }
  }, [path]);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    if (!loading || data) return;
    const startedAt = Date.now();
    const tick = () => setWaitSeconds(Math.floor((Date.now() - startedAt) / 1000));
    tick();
    const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, [loading, data]);
  let page;
  if (path === "/conditions") page = <ConditionOverviewPage />;
  else if (detailId) page = <ConditionDetailPage id={detailId} />;
  else if (path === "/runs") page = <RunsPage />;
  else if (path === "/compare") page = <ComparePage />;
  else if (path === "/architecture") page = <ArchitecturePage />;
  else if (sampleMatch) page = <SampleDetailPage runId={decodeURIComponent(sampleMatch[1])} caseId={decodeURIComponent(sampleMatch[2])} repeat={Number(sampleMatch[3])} />;
  else if (runDetailMatch) page = <RunDetailPage runId={decodeURIComponent(runDetailMatch[1])} />;
  else if (path === "/cases") page = <CasesPage />;
  else if (caseDetailMatch) page = <CaseDetailPage caseId={decodeURIComponent(caseDetailMatch[1])} />;
  else if (path !== "/") page = <Placeholder path={path} />;
  else if (loading && !data) page = <LoadingState seconds={waitSeconds} />;
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
