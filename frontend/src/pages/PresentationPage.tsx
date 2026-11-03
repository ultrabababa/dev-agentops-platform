import { useEffect, useState, type ReactNode } from "react";

type Slide = {
  section: string;
  title: string;
  lead: string;
  notes: string;
};

const slides: Slide[] = [
  {
    section: "INTRODUCTION",
    title: "DevAgentOps：从 Agent 评测到实验归因",
    lead: "以 CI / Test Failure Triage 为例，讨论如何把 Agent 的运行结果变成可解释、可复现的工程证据。",
    notes: "开场只交代场景与主线。本次不是 Runtime 功能介绍，重点回答三个问题：怎么评、怎么定位失败、怎么验证改进。",
  },
  {
    section: "01 · PROBLEM & SYSTEM",
    title: "先明确：我们在评测怎样的 Agent？",
    lead: "面对大量日志和代码，Agent 需要读取证据、定位失败原因，并提交可审计的结构化诊断报告。",
    notes: "只讲够理解后续评测的 Agent 背景。V1 只读，不修改代码、不重跑 CI、不自动修复。不要在 Runtime 实现细节上花太多时间。",
  },
  {
    section: "02 · BENCHMARK DESIGN",
    title: "如何构建可复现的评测基准？",
    lead: "固定输入、预先审核的参考答案和统一评分口径，比先挑一个看起来合理的综合分数更重要。",
    notes: "说明 Case、Sample、Formal Run 的不同粒度：20 个经过人工审核的 Case，每个 Case 重复 3 次，每次 Formal Run 计划 60 个 Sample。测试环境、Ground Truth 和 Scorer 要保持冻结。",
  },
  {
    section: "03 · SCORING",
    title: "正确答案只是评测的一个维度",
    lead: "把故障归类、证据覆盖、报告协议和执行过程分开观察，才能知道 Agent 实际可靠在哪里。",
    notes: "强调 Exact Match、Evidence Hit、Protocol Validity 不可互相替代。Trajectory / Trace 是审计与诊断材料，不应声称读取或校验模型不可见的内部思维链。",
  },
  {
    section: "04 · COMPARISON",
    title: "不同条件下，能力差异发生在哪里？",
    lead: "L1–L4 用于拆解能力边界；Oracle 是单独的诊断性证据干预，而不是更高一级的 Agent。",
    notes: "比较代表性正式运行的方向和矛盾：L3 分类准确率更高，但 Evidence Hit 反而偏低；L4 Evidence Hit 较好。不同 fresh generation 的差异不能直接解释为因果效应。",
  },
  {
    section: "05 · FAILURE ATTRIBUTION",
    title: "证据没命中：没找到，还是找到却没用？",
    lead: "把 Evidence pipeline 拆成获取、利用和最终引用，才能提出针对性的系统改进假设。",
    notes: "以 L3 为例：Acquisition Recall 76.56%，已获取证据的 Utilization 66.18%，最终 Evidence Hit 50.67%。注意分母不同。Oracle 85.40% 只是支持证据发现瓶颈的诊断信号，不是理论上限。",
  },
  {
    section: "06 · CONTROLLED REPLAY",
    title: "模型没变，分数却提高了：为什么？",
    lead: "用固定历史输出的 Replay，把模型能力与评测基础设施问题区分开。",
    notes: "引用规范化实验保持历史输出和评分器不变，只改变确定性 Evidence Reference 规范化：L4 Protocol Validity 81.36% 到 96.61%，未知 Evidence ID 12 到 0；分类 Exact Match 88.33% 不变。",
  },
  {
    section: "07 · RUNTIME EXPERIMENT",
    title: "评测也能指导效率优化",
    lead: "对照 Single + Sequential 与 Batch + Parallel Tool Policy，验证减少模型往返是否真的节省时间。",
    notes: "解释 877→571 次 Model Decisions、978.27→806.69 秒 Wall Time、809→775 次 ToolCalls。效率趋势在 replication 中复现，但 fresh generation 下的质量差异不应做强因果结论。",
  },
  {
    section: "08 · TAKEAWAYS",
    title: "评测不是成绩单，而是下一轮工程决策的起点",
    lead: "Frozen Case → Execution Evidence → Scoring → Badcase Attribution → Controlled Experiment → Runtime Evolution",
    notes: "结尾强调可迁移原则，而不是说 CI 场景的 Case 或评分规则能原样迁移到金融 Agent、Skill 或 MCP。开放讨论。",
  },
];

const conditions = [
  { name: "L1", control: "完整上下文 · 单轮", exact: 80.0, evidence: 52.16 },
  { name: "L2", control: "固定多阶段流程", exact: 83.33, evidence: 54.15 },
  { name: "L3", control: "静态检索", exact: 88.33, evidence: 50.67 },
  { name: "L4", control: "自研 ReAct + Tools", exact: 81.67, evidence: 71.83 },
  { name: "Oracle", control: "诊断性证据干预", exact: 83.33, evidence: 85.4 },
];

function Stat({ value, label, detail }: { value: string; label: string; detail?: string }) {
  return <div className="pres-stat"><strong>{value}</strong><span>{label}</span>{detail && <small>{detail}</small>}</div>;
}

function Eyebrow({ children }: { children: ReactNode }) {
  return <p className="pres-eyebrow">{children}</p>;
}

function Flow({ items }: { items: string[] }) {
  return <div className="pres-flow">{items.map((item, i) => <div className="pres-flow-item" key={item}><span>{item}</span>{i < items.length - 1 && <b aria-hidden="true">→</b>}</div>)}</div>;
}

function LinkRow({ links }: { links: Array<{ name: string; url: string }> }) {
  return <div className="pres-link-row">{links.map((link) => <a key={link.url} href={link.url} target="_blank" rel="noreferrer">{link.name}<span aria-hidden="true">↗</span></a>)}</div>;
}

function Panel({ className = "", children }: { className?: string; children: ReactNode }) {
  return <div className={"pres-panel " + className}>{children}</div>;
}

function SlideBody({ index }: { index: number }) {
  switch (index) {
    case 0:
      return <div className="pres-cover">
        <div className="pres-cover-main">
          <div className="pres-tag">TECHNICAL SHARING · AGENT EVALUATION</div>
          <h1>从 <em>Agent 评测</em><br />到 <em>实验归因</em></h1>
          <p>DevAgentOps · CI / Test Failure Triage</p>
          <p className="pres-cover-desc">不只回答「Agent 做对了吗」，更要回答「为什么失败，以及下一步该改哪里」。</p>
        </div>
        <div className="pres-cover-bottom">
          <Stat value="20 × 3" label="Frozen Cases × Repeats" />
          <Stat value="L1–L4" label="Runtime / Condition Ladder" />
          <Stat value="4" label="代表性实验研究" />
        </div>
      </div>;
    case 1:
      return <div className="pres-content-grid pres-two">
        <Panel>
          <Eyebrow>SCENARIO</Eyebrow>
          <h2>大规模 CI 失败，人工排查链路长</h2>
          <p>输入可能包含失败日志、仓库代码及关联上下文。真正的任务不是生成一段流畅解释，而是找到<strong>可引用的证据</strong>并完成可信归因。</p>
          <div className="pres-callout">V1 范围：只读诊断，不改代码、不执行测试、不提交修复。</div>
        </Panel>
        <Panel className="pres-panel-dark">
          <Eyebrow>MINIMAL AGENT LOOP</Eyebrow>
          <div className="pres-vertical-flow">
            <div>模型决定下一步动作</div><span>↓</span>
            <div>Runtime 校验动作与权限</div><span>↓</span>
            <div>read / grep / find / ls</div><span>↓</span>
            <div>Observation → 下一轮决策</div><span>↓</span>
            <div>Structured Triage Report</div>
          </div>
        </Panel>
      </div>;
    case 2:
      return <div className="pres-stack">
        <div className="pres-stat-row pres-stat-row-3">
          <Stat value="20" label="Human-reviewed Cases" detail="同一冻结 Suite" />
          <Stat value="3" label="Repeats / Case" detail="观察运行波动" />
          <Stat value="60" label="Samples / Formal Run" detail="先聚合 Case，再看整体" />
        </div>
        <div className="pres-content-grid pres-three">
          <Panel><Eyebrow>INPUT</Eyebrow><h3>Frozen Environment</h3><p>固定日志、仓库片段和可见工作区；避免 Case 在不同实验中漂移。</p></Panel>
          <Panel><Eyebrow>GROUND TRUTH</Eyebrow><h3>Reference & Evidence</h3><p>人工审核故障类型与所需证据，作为可检验的参考标准。</p></Panel>
          <Panel><Eyebrow>SCORING</Eyebrow><h3>Shared Deterministic Scorer</h3><p>统一报告 Schema、Validator 与 Scorer，确保结果可对比、可追溯。</p></Panel>
        </div>
        <Flow items={["Frozen Case", "Agent Execution", "Trace / Trajectory", "Validation & Scoring", "Case-first Aggregation"]} />
      </div>;
    case 3:
      return <div className="pres-stack">
        <div className="pres-content-grid pres-three pres-metrics">
          <Panel><Eyebrow>RESULT QUALITY</Eyebrow><h3>Failure Type Exact Match</h3><p>最终故障归类是否与参考答案一致。</p><div className="pres-small-point">只回答「分类对不对」</div></Panel>
          <Panel><Eyebrow>EVIDENCE QUALITY</Eyebrow><h3>Report Evidence Hit</h3><p>最终报告是否引用了需要的关键证据。</p><div className="pres-small-point">避免「猜对结论、证据不足」</div></Panel>
          <Panel><Eyebrow>PROTOCOL QUALITY</Eyebrow><h3>Protocol Validity</h3><p>输出是否符合结构化协议、引用是否有效。</p><div className="pres-small-point">保障下游系统可以消费</div></Panel>
        </div>
        <Panel className="pres-wide-panel">
          <Eyebrow>AUDITABILITY ≠ HIDDEN REASONING</Eyebrow>
          <div className="pres-split"><p>同时保留可观察的工具调用、Agent Trajectory 与 Runtime Trace，用于故障分析和复盘。</p><strong>报告评分 + 执行证据<br />两条线并行</strong></div>
        </Panel>
      </div>;
    case 4:
      return <div className="pres-stack pres-comparison">
        <div className="pres-legend"><span>Failure Type Exact Match</span><span>Report Evidence Hit Rate</span></div>
        <div className="pres-chart-table">
          <div className="pres-chart-head"><span>Condition</span><span>控制方式</span><span>分类准确</span><span>证据命中</span></div>
          {conditions.map((c) => <div key={c.name} className={"pres-chart-row" + (c.name === "L4" ? " pres-highlight" : "")}>
            <strong>{c.name}</strong><span>{c.control}</span>
            <div><span className="pres-bar pres-bar-muted" style={{ width: String(c.exact) + "%" }} /><b>{c.exact.toFixed(2)}%</b></div>
            <div><span className="pres-bar pres-bar-strong" style={{ width: String(c.evidence) + "%" }} /><b>{c.evidence.toFixed(2)}%</b></div>
          </div>)}
        </div>
        <div className="pres-bottom-note"><strong>观察：</strong>L3 分类准确率高，但 Evidence Hit 没有提升；L4 Evidence Hit 较高。<strong>边界：</strong>代表性 fresh runs 不是严格的单变量因果实验，Oracle 也不是 L5。</div>
      </div>;
    case 5:
      return <div className="pres-stack">
        <div className="pres-content-grid pres-three pres-attribution">
          <Panel><Eyebrow>STEP 01 · ACQUISITION</Eyebrow><h3>找得到吗？</h3><strong>76.56%</strong><p>Retrieval Acquisition Recall</p><small>分母：全部 Required Evidence</small></Panel>
          <Panel><Eyebrow>STEP 02 · UTILIZATION</Eyebrow><h3>找到后用了吗？</h3><strong>66.18%</strong><p>Acquired Required Evidence Utilization</p><small>分母：已获得的 Required Evidence</small></Panel>
          <Panel><Eyebrow>OUTCOME · CITATION</Eyebrow><h3>最后引用了吗？</h3><strong>50.67%</strong><p>Report Evidence Hit Rate</p><small>正式 Case-first 聚合指标</small></Panel>
        </div>
        <div className="pres-content-grid pres-two pres-attribution-bottom">
          <Panel><Eyebrow>DIAGNOSTIC INTERVENTION</Eyebrow><h3>Oracle Evidence</h3><div className="pres-inline-numbers"><span>L4 <b>71.83%</b></span><span>Oracle <b>85.40%</b></span></div><p>绕过普通证据发现过程后，Evidence Hit 更高，支持继续调查证据获取瓶颈。</p></Panel>
          <Panel className="pres-panel-tint"><Eyebrow>ENGINEERING QUESTION</Eyebrow><h3>两个不同的优化方向</h3><p><strong>没找到：</strong>改善检索、候选覆盖与定位。</p><p><strong>找到却没用：</strong>改善上下文组织、证据利用与报告引用。</p></Panel>
        </div>
      </div>;
    case 6:
      return <div className="pres-stack">
        <div className="pres-experiment-path">
          <div><small>HYPOTHESIS</small><strong>部分 Badcase 来自引用格式，而非模型诊断</strong></div>
          <div><small>CONTROL</small><strong>固定历史模型输出，只改变规范化步骤</strong></div>
          <div><small>REPLAY</small><strong>原 Validator / Scorer 重新评分</strong></div>
        </div>
        <div className="pres-content-grid pres-three pres-result-cards">
          <Panel><Eyebrow>PROTOCOL VALIDITY</Eyebrow><div>81.36% <span>→</span> <strong>96.61%</strong></div><p>协议有效率提升</p></Panel>
          <Panel><Eyebrow>UNKNOWN EVIDENCE IDs</Eyebrow><div>12 <span>→</span> <strong>0</strong></div><p>引用解析错误消失</p></Panel>
          <Panel><Eyebrow>FAILURE TYPE EXACT MATCH</Eyebrow><div>88.33% <span>→</span> <strong>88.33%</strong></div><p>诊断分类保持不变</p></Panel>
        </div>
        <div className="pres-bottom-note"><strong>结论：</strong>这次改善发生在 Evidence Reference Canonicalization / Validation 基础设施，并非模型「重新想对了」。</div>
      </div>;
    case 7:
      return <div className="pres-stack">
        <div className="pres-content-grid pres-two pres-policy">
          <Panel><Eyebrow>BASELINE</Eyebrow><h3>Single + Sequential</h3><p>每次模型决策最多执行一个工具调用；多步独立检索需要反复模型往返。</p></Panel>
          <Panel className="pres-panel-tint"><Eyebrow>TREATMENT</Eyebrow><h3>Batch + Parallel</h3><p>同轮接受多个合法、独立 ToolCalls，并行执行，再按调用顺序返回结果。</p></Panel>
        </div>
        <div className="pres-stat-row pres-stat-row-3 pres-efficiency">
          <Stat value="877 → 571" label="Model Decisions" detail="−34.89%" />
          <Stat value="978 → 807s" label="Run Wall Time" detail="−17.54%" />
          <Stat value="809 → 775" label="Executed ToolCalls" detail="−4.20%" />
        </div>
        <div className="pres-bottom-note"><strong>决策：</strong>效率收益在重复实验中再次出现，可以保留该优化；fresh generation 下的小幅质量差异不等于 Tool Policy 的因果效应。</div>
      </div>;
    default:
      return <div className="pres-conclusion">
        <div className="pres-conclusion-lead">Observe → Attribute → Experiment → Decide</div>
        <div className="pres-content-grid pres-three">
          <Panel><span className="pres-step-number">01</span><h3>评得可靠</h3><p>冻结 Case 与 Scorer，拆开正确性、证据与输出协议。</p></Panel>
          <Panel><span className="pres-step-number">02</span><h3>解释失败</h3><p>从 Badcase 找到损失环节，而不是只看聚合分数。</p></Panel>
          <Panel><span className="pres-step-number">03</span><h3>验证改进</h3><p>匹配实验方法与因果主张，再决定修改哪层系统。</p></Panel>
        </div>
        <div className="pres-transfer"><strong>可以迁移的原则</strong><span>Agent / Skill / MCP 评测都需要任务成功标准、可审计证据和归因闭环；具体数据集与指标仍应按业务重新定义。</span></div>
        <LinkRow links={[{ name: "打开完整 Evaluation Explorer", url: "/" }, { name: "查看实验与归因", url: "/compare" }, { name: "查看系统架构", url: "/architecture" }]} />
      </div>;
  }
}

function clampIndex(index: number) {
  return Math.min(slides.length - 1, Math.max(0, index));
}

function initialIndex() {
  const number = Number(new URLSearchParams(window.location.search).get("slide"));
  return Number.isInteger(number) && number >= 1 ? clampIndex(number - 1) : 0;
}

export function PresentationPage() {
  const [index, setIndex] = useState(initialIndex);
  const [notesOpen, setNotesOpen] = useState(false);
  const slide = slides[index];
  useEffect(() => {
    const url = new URL(window.location.href);
    url.searchParams.set("slide", String(index + 1));
    window.history.replaceState(null, "", url.toString());
    document.title = "DevAgentOps · 技术分享 · " + (index + 1) + "/" + slides.length;
  }, [index]);
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.closest("input, textarea, select, [contenteditable=true]")) return;
      if (["ArrowRight", "PageDown", " ", "ArrowDown"].includes(event.key)) {
        event.preventDefault();
        setIndex((i) => clampIndex(i + 1));
      } else if (["ArrowLeft", "PageUp", "ArrowUp"].includes(event.key)) {
        event.preventDefault();
        setIndex((i) => clampIndex(i - 1));
      } else if (event.key === "Home") {
        setIndex(0);
      } else if (event.key === "End") {
        setIndex(slides.length - 1);
      } else if (event.key.toLowerCase() === "n") {
        setNotesOpen((value) => !value);
      } else if (event.key.toLowerCase() === "f") {
        if (document.fullscreenElement) void document.exitFullscreen();
        else void document.documentElement.requestFullscreen().catch(() => {});
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return <main className="pres-root" id="main">
    <div className="pres-stage">
      <header className="pres-topbar">
        <div className="pres-brand"><span className="pres-brand-mark">D</span><span>DevAgentOps <i>/</i> Technical Sharing</span></div>
        <span>{slide.section}</span>
      </header>
      <section className={"pres-slide pres-slide-" + index} aria-label={"第 " + (index + 1) + " 页：" + slide.title} key={index}>
        {index !== 0 && <div className="pres-slide-intro"><Eyebrow>{String(index).padStart(2, "0")} / 08</Eyebrow><h1>{slide.title}</h1><p>{slide.lead}</p></div>}
        <SlideBody index={index} />
      </section>
      {notesOpen && <aside className="pres-speaker-notes"><strong>讲者备注（按 N 关闭）</strong><p>{slide.notes}</p></aside>}
      <footer className="pres-footer">
        <div className="pres-footer-links"><a href="/" target="_blank" rel="noreferrer">Explorer ↗</a><a href="/compare" target="_blank" rel="noreferrer">Experiments ↗</a><a href="/architecture" target="_blank" rel="noreferrer">Architecture ↗</a></div>
        <div className="pres-controls"><button type="button" onClick={() => setNotesOpen((value) => !value)} title="N：讲者备注" aria-pressed={notesOpen}>Notes</button><button type="button" onClick={() => setIndex((i) => clampIndex(i - 1))} disabled={index === 0} aria-label="上一页">←</button><span>{String(index + 1).padStart(2, "0")} / {String(slides.length).padStart(2, "0")}</span><button type="button" onClick={() => setIndex((i) => clampIndex(i + 1))} disabled={index === slides.length - 1} aria-label="下一页">→</button></div>
      </footer>
      <div className="pres-progress" role="progressbar" aria-label="演讲进度" aria-valuenow={index + 1} aria-valuemin={1} aria-valuemax={slides.length}><span style={{ width: String(((index + 1) / slides.length) * 100) + "%" }} /></div>
    </div>
    <div className="pres-help">方向键 / 空格翻页 · N 讲者备注 · F 全屏</div>
  </main>;
}
