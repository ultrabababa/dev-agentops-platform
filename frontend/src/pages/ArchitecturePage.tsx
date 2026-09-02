import { useState } from "react";

type DiagramId = "system" | "evaluation-workflow" | "l4-runtime";

type Diagram = {
  id: DiagramId;
  index: string;
  title: string;
  question: string;
  description: string;
  html: string;
  svg: string;
  ir: string;
  evidence: string;
};

const diagrams: Diagram[] = [
  {
    id: "system",
    index: "01",
    title: "High-Level System Architecture",
    question: "系统由什么组成？",
    description: "从 CLI、Formal Preflight、Orchestrator、Condition Executors 到 scoring、evidence persistence 与只读 Explorer，展示 DevAgentOps 的静态系统边界与主执行路径。",
    html: "/architecture-assets/system.html",
    svg: "/architecture-assets/system.svg",
    ir: "https://github.com/ultrabababa/dev-agentops-platform/blob/main/docs/architecture/system.architecture.json",
    evidence: "32 个源码引用，固定到生成时的 Git revision",
  },
  {
    id: "evaluation-workflow",
    index: "02",
    title: "Formal Evaluation Execution Workflow",
    question: "一次正式 Eval 怎么跑完？",
    description: "展开 Matrix v2 从 preflight、frozen contracts、sample planning、Case-level scheduling、condition execution、scoring/aggregation 到 SQLite finalization 与 JSON/Markdown artifacts 的完整生命周期。",
    html: "/architecture-assets/evaluation-workflow.html",
    svg: "/architecture-assets/evaluation-workflow.svg",
    ir: "https://github.com/ultrabababa/dev-agentops-platform/blob/main/docs/architecture/evaluation-workflow.workflow.json",
    evidence: "Workflow IR；按当前 Matrix v2 实现逐段核对",
  },
  {
    id: "l4-runtime",
    index: "03",
    title: "L4 ReAct Runtime Sequence",
    question: "Agent Runtime 内部怎么循环？",
    description: "聚焦一个 L4 sample：typed trajectory、MiniMax provider、same-request retry、ToolCall dispatch、冻结 workspace、bounded observations、termination、Trace 与 deterministic scoring。",
    html: "/architecture-assets/l4-runtime.html",
    svg: "/architecture-assets/l4-runtime.svg",
    ir: "https://github.com/ultrabababa/dev-agentops-platform/blob/main/docs/architecture/l4-runtime.sequence.json",
    evidence: "Sequence IR；按 L4 Runtime / Tool / Workspace 实现逐段核对",
  },
];

export function ArchitecturePage() {
  const [selectedId, setSelectedId] = useState<DiagramId>("system");
  const selected = diagrams.find((diagram) => diagram.id === selectedId) ?? diagrams[0];

  return (
    <main className="architecture-page" id="main">
      <section className="architecture-hero">
        <p className="eyebrow">SYSTEM DESIGN · EVIDENCE-BACKED</p>
        <h1>从系统边界到 Agent loop，三层看清 DevAgentOps。</h1>
        <p>
          这不是三张重复的流程图。Architecture 解释系统组成，Workflow 解释正式评测生命周期，Sequence
          解释 L4 Agent Runtime 的真实交互。三层都来自当前实现，并保留可版本化的 Archify IR。
        </p>
        <div className="architecture-hero-meta" aria-label="架构文档属性">
          <span>3 views</span>
          <span>interactive HTML</span>
          <span>versioned IR</span>
          <span>static SVG export</span>
        </div>
      </section>

      <section className="architecture-browser" aria-labelledby="architecture-browser-title">
        <div className="architecture-browser-heading">
          <div>
            <p className="eyebrow">INTERACTIVE ARCHITECTURE</p>
            <h2 id="architecture-browser-title">选择一个层级，直接检查系统关系。</h2>
          </div>
          <p>交互图与 Evaluation API 解耦；即使只读 API 冷启动，这些静态架构资料也可以独立浏览。</p>
        </div>

        <div className="architecture-tabs" role="tablist" aria-label="架构图层级">
          {diagrams.map((diagram) => (
            <button
              key={diagram.id}
              type="button"
              role="tab"
              aria-selected={selected.id === diagram.id}
              aria-controls="architecture-viewer"
              className={selected.id === diagram.id ? "active" : undefined}
              onClick={() => setSelectedId(diagram.id)}
            >
              <span>{diagram.index}</span>
              <strong>{diagram.question}</strong>
              <small>{diagram.title}</small>
            </button>
          ))}
        </div>

        <article className="architecture-viewer" id="architecture-viewer" role="tabpanel">
          <header>
            <div>
              <span>{selected.index}</span>
              <p>{selected.question}</p>
            </div>
            <div>
              <h3>{selected.title}</h3>
              <p>{selected.description}</p>
            </div>
          </header>

          <div className="architecture-frame">
            <iframe
              key={selected.id}
              src={`${selected.html}?embed=1&theme=light`}
              title={`${selected.title} interactive diagram`}
              loading="lazy"
            />
          </div>

          <footer>
            <p><span>Evidence</span>{selected.evidence}</p>
            <div className="architecture-actions">
              <a className="button primary" href={selected.html} target="_blank" rel="noreferrer">打开完整交互图 ↗</a>
              <a className="button secondary" href={selected.svg} target="_blank" rel="noreferrer">查看 SVG ↗</a>
              <a className="text-link" href={selected.ir} target="_blank" rel="noreferrer">查看 Typed IR ↗</a>
            </div>
          </footer>
        </article>
      </section>

      <section className="architecture-level-map" aria-labelledby="architecture-level-map-title">
        <div className="architecture-level-copy">
          <p className="eyebrow">THREE LEVELS · ONE SYSTEM</p>
          <h2 id="architecture-level-map-title">面试时按“结构 → 生命周期 → Runtime”逐层下钻。</h2>
          <p>先用高层架构建立共同语言，再用正式 Evaluation Workflow 解释可靠执行，最后进入 L4 Sequence 讨论 Harness、Tool boundary、retry、trajectory 与 termination。</p>
        </div>
        <div className="architecture-level-cards">
          {diagrams.map((diagram) => (
            <article key={diagram.id}>
              <div className="architecture-level-index">{diagram.index}</div>
              <img src={diagram.svg} alt={`${diagram.title} 静态预览`} loading="lazy" />
              <div>
                <p>{diagram.question}</p>
                <h3>{diagram.title}</h3>
                <button type="button" className="architecture-select" onClick={() => {
                  setSelectedId(diagram.id);
                  document.getElementById("architecture-browser-title")?.scrollIntoView({ behavior: "smooth", block: "start" });
                }}>在上方交互查看 ↑</button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
