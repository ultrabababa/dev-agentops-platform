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
  const fullDiagramHref = selected.id === "system"
    ? `${selected.html}?theme=light`
    : `${selected.html}?reader=1&theme=light`;

  return (
    <main className="architecture-page" id="main">
      <section className="architecture-hero">
        <p className="eyebrow">SYSTEM DESIGN · EVIDENCE-BACKED</p>
        <h1>从系统边界到 Agent Runtime，三层展示 DevAgentOps 的工程设计。</h1>
        <p>
          High-Level Architecture 描述系统组件与边界；Formal Evaluation Workflow 描述一次可复现评测的完整生命周期；
          L4 Runtime Sequence 展开单个 Agent sample 内模型、工具、工作区与证据流的真实交互。
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
            <p className="eyebrow">ARCHITECTURE MAPS</p>
            <h2 id="architecture-browser-title">选择一个层级，查看完整系统设计。</h2>
          </div>
          <p>页面内展示完整 SVG 便于快速阅读；“全屏查看交互图” 会以更大的物理比例展示复杂 Workflow / Sequence；较小屏幕允许平移查看，而不是继续缩小文字。</p>
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

          <a
            className="architecture-preview"
            href={fullDiagramHref}
            target="_blank"
            rel="noreferrer"
            aria-label={`打开 ${selected.title} 全屏交互图`}
          >
            <img
              key={selected.id}
              src={selected.svg}
              alt={`${selected.title} 完整静态图`}
            />
          </a>

          <footer>
            <p><span>Evidence</span>{selected.evidence}</p>
            <div className="architecture-actions">
              <a className="button primary" href={fullDiagramHref} target="_blank" rel="noreferrer">打开全屏交互图 ↗</a>
              <a className="button secondary" href={selected.svg} target="_blank" rel="noreferrer">查看 SVG ↗</a>
              <a className="text-link" href={selected.ir} target="_blank" rel="noreferrer">查看 Typed IR ↗</a>
            </div>
          </footer>
        </article>
      </section>

      <section className="architecture-level-map" aria-labelledby="architecture-level-map-title">
        <div className="architecture-level-copy">
          <p className="eyebrow">THREE LEVELS · ONE SYSTEM</p>
          <h2 id="architecture-level-map-title">同一系统，从组件边界到 Runtime 交互逐层展开。</h2>
          <p>High-Level Architecture 展示系统组件、边界与主路径；Formal Evaluation Workflow 展示正式评测的控制流、并发、失败边界与持久化；L4 Runtime Sequence 展示模型、工具、冻结工作区、Trace 与 Trajectory 如何在一次 Agent 执行中协作。</p>
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
                }}>在上方查看完整图 ↑</button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
