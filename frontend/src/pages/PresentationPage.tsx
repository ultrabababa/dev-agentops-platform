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
    title: "Agent 评测：答对了，就算成功吗？",
    lead: "从一个简单的 CI 失败案例，理解如何设计评测、定位 Badcase，并通过实验验证改进。",
    notes: "开场可以问大家：一道数学题答案写对了，但没有计算过程，能否确信他真的会？Agent 也一样。今天用一个贯穿全场的小例子说明思路；它是教学示例，正式的指标仍来自冻结的 20-Case Suite。",
  },
  {
    section: "01 · SCENARIO",
    title: "一条测试失败日志，Agent 到底要做什么？",
    lead: "先看一个小例子：预期 2 + 3 = 5，测试却得到 6。只说「断言失败」够不够？",
    notes: "展示两份材料：日志告诉我们哪里出错；源代码告诉我们为什么会错。Agent 需要从资料中找证据、作出归类并生成结构化报告。这里的数字和文件内容是讲解用的构造示例，并非正式 Case。",
  },
  {
    section: "02 · BENCHMARK",
    title: "怎样把一个例子做成可重复评测的 Case？",
    lead: "核心不是给模型出一道题，而是把题目、标准答案、判分依据和运行条件都固定下来。",
    notes: "以这个小例子说明 Case 的四部分：可见输入、评测者持有的参考故障类型、Required Evidence、统一 Scorer。真正的 Suite 有 20 个人工审查 Case，每个重复 3 次，因此每次正式运行计划 60 个 Sample。",
  },
  {
    section: "03 · METRICS",
    title: "诊断对了，不代表证据和报告也合格",
    lead: "同一份 Agent 报告至少可以拆成三道独立的判断题。",
    notes: "示例：故障类型答对，分类得分很好；但只引用日志、漏掉代码，Evidence Hit 可能只有 1/2；再假设引用了不存在的 Evidence ID，协议又会失败。三个指标描述不同失败模式，不该混成单个总分。这里的 1/2 是假设这个教学案例有两条必需证据。",
  },
  {
    section: "04 · CONDITIONS",
    title: "同一道题，换一种「查资料」的方法",
    lead: "L1–L4 的区别，可以理解为让模型用不同方式获得材料、决定下一步动作。",
    notes: "不要花太久讲 Runtime 细节：L1 全部材料一次给；L2 固定两阶段；L3 程序先检索；L4 模型自行调用只读工具。Oracle 是评测侧提供关键原始证据的特殊诊断条件，不是 L5。下面两列是代表性正式运行的指标，不是严格因果效应。",
  },
  {
    section: "05 · ATTRIBUTION",
    title: "证据没命中：没找到，还是找到了没用？",
    lead: "这两种 Badcase 看起来都会扣分，但应该采用不同的改进办法。",
    notes: "用教学例子区分：检索只取到 log，叫 acquisition 缺口；两份材料都在上下文中但报告只引用 log，叫 utilization / citation 缺口。再展示 L3 真实结果的三项指标，解释分母不同。Oracle 提供强诊断信号，但不能视为因果估计或理论上限。",
  },
  {
    section: "06 · CONTROLLED REPLAY",
    title: "模型答案没变，为什么评分反而提升？",
    lead: "有些 Badcase 不是模型判断错，而是证据引用格式没有被评测基础设施正确识别。",
    notes: "假设 Agent 说了 raw.log 的某段行号，但评测器要求稳定 Evidence ID。这里不能任意改变模型答案；固定历史输出，只改变确定性的引用规范化步骤，再用原 Validator / Scorer 重放。结果显示 Protocol Validity 改善，但 Failure Type Exact Match 不变，因此可把这部分问题定位到基础设施。",
  },
  {
    section: "07 · OPTIMIZATION",
    title: "改进方案真的有效吗？做一次对照实验",
    lead: "一个容易理解的例子：原来查询日志和代码要反复找模型，现在可在同轮提出独立工具调用、并行执行。",
    notes: "用两个工具查询的例子解释减少模型往返。控制 Suite、模型配置、评分方法、Runtime 家族等主要条件，只改 Tool Policy，做 back-to-back replication。真实结果：Model Decisions 877 到 571，Wall Time 978.27s 到 806.69s。效率趋势复现，但 fresh generation 下的质量差异不等于严格的因果效果。",
  },
  {
    section: "08 · TAKEAWAYS",
    title: "评测真正的价值：告诉我们下一步改哪里",
    lead: "不是拿到一张成绩单，而是把发现问题 → 找原因 → 做实验 → 验证改进连成闭环。",
    notes: "结尾用一句话收束：Agent 评测不仅要判对错，还要解释原因、驱动工程决策。方法可以迁移到金融 Agent、Skill、MCP，但业务任务、标准答案和评分指标要重新定义。",
  },
];

const conditions = [
  { name: "L1", control: "一次看全部材料", exact: 80.0, evidence: 52.16 },
  { name: "L2", control: "固定先分析、再报告", exact: 83.33, evidence: 54.15 },
  { name: "L3", control: "程序先帮它检索", exact: 88.33, evidence: 50.67 },
  { name: "L4", control: "模型自己调用工具", exact: 81.67, evidence: 71.83 },
  { name: "Oracle", control: "评测侧直接给关键证据", exact: 83.33, evidence: 85.4 },
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

function TeachingTag() {
  return <span className="pres-demo-label">简化教学示例 · 非正式评测 Case</span>;
}

function SlideBody({ index }: { index: number }) {
  switch (index) {
    case 0:
      return <div className="pres-cover">
        <div className="pres-cover-main">
          <div className="pres-tag">DEVAGENTOPS · AGENT EVALUATION</div>
          <h1>Agent 评测：<br /><em>答对了</em>，就算成功吗？</h1>
          <p>从一次 CI 测试失败，讲清评测设计、失败归因和实验优化。</p>
          <p className="pres-cover-desc">比「分数是多少」更重要的是：为什么失分？下一步该改哪里？</p>
        </div>
        <div className="pres-cover-bottom">
          <Stat value="20 × 3" label="正式评测 Case × 重复次数" />
          <Stat value="L1–L4" label="不同执行条件" />
          <Stat value="4" label="代表性实验研究" />
        </div>
      </div>;
    case 1:
      return <div className="pres-stack">
        <div className="pres-example-heading"><TeachingTag /><span>目标：找出失败原因，并提供能核查的证据</span></div>
        <div className="pres-content-grid pres-two">
          <Panel>
            <Eyebrow>01 / 测试日志告诉我们「哪里错了」</Eyebrow>
            <div className="pres-code">
              <span className="pres-code-label">tests/test_calculate.py</span>
              <code>assert calculate_total(2, 3) == 5</code>
              <code className="pres-code-error">AssertionError: expected 5, got 6</code>
            </div>
            <p className="pres-example-caption">日志只说明结果不符合预期，还没解释根因。</p>
          </Panel>
          <Panel>
            <Eyebrow>02 / 源代码告诉我们「为什么错了」</Eyebrow>
            <div className="pres-code">
              <span className="pres-code-label">repository/calculator.py</span>
              <code>def calculate_total(a, b):</code>
              <code className="pres-code-error">    return a * b  # 本应相加</code>
            </div>
            <p className="pres-example-caption">真正的原因是实现写成乘法，而不是加法。</p>
          </Panel>
        </div>
        <div className="pres-example-answer"><strong>理想的 Agent 报告</strong><span>故障类型：<b>测试断言失败</b></span><span>根因：<b>代码使用乘法</b></span><span>证据：<b>日志 + 源代码</b></span></div>
        <div className="pres-bottom-note">关键问题：Agent 只说「断言失败」也许猜对了；但只有找到并引用代码证据，我们才更有理由信任它的诊断。</div>
      </div>;
    case 2:
      return <div className="pres-stack">
        <div className="pres-stat-row pres-stat-row-3">
          <Stat value="20" label="人工审核的 Cases" detail="固定题目与材料" />
          <Stat value="3" label="每个 Case 重复 3 次" detail="观察结果波动" />
          <Stat value="60" label="每次 Formal Run 的 Samples" detail="先按 Case 聚合" />
        </div>
        <div className="pres-content-grid pres-two">
          <Panel>
            <Eyebrow>AGENT 能看到的题目</Eyebrow>
            <h3>输入材料（Frozen）</h3>
            <div className="pres-example-lines"><span>失败日志：expected 5, got 6</span><span>仓库代码：return a * b</span><span>允许使用的工具 / 报告格式</span></div>
            <p>一旦冻结，同一 Case 换条件时题目不能悄悄变。</p>
          </Panel>
          <Panel className="pres-panel-tint">
            <Eyebrow>仅评测器持有的参考标准</Eyebrow>
            <h3>Ground Truth + Scorer</h3>
            <div className="pres-example-lines"><span>正确类别：test_assertion_failure</span><span>必需证据：日志 + 代码片段</span><span>按相同规则判定对错与引用</span></div>
            <p>不能把参考答案或「哪些证据必需」透露给被测 Agent。</p>
          </Panel>
        </div>
        <Flow items={["固定题目", "运行 Agent", "拿到报告", "对照标准答案", "聚合并分析"]} />
        <div className="pres-example-smallprint">上面两栏是教学示例；20 × 3 是 DevAgentOps 真实正式评测规模。</div>
      </div>;
    case 3:
      return <div className="pres-stack">
        <div className="pres-example-heading"><TeachingTag /><span>假设本例的两条必需证据是「失败日志」和「相关代码」</span></div>
        <div className="pres-content-grid pres-three pres-metrics pres-simple-metrics">
          <Panel>
            <Eyebrow>01 / 结论</Eyebrow>
            <h3>Failure Type Exact Match</h3>
            <div className="pres-big-example">答对类别 <strong>✓</strong></div>
            <p>Agent 输出「测试断言失败」，与参考类别一致。</p>
            <span className="pres-plain-language">问的是：<b>诊断方向对不对？</b></span>
          </Panel>
          <Panel>
            <Eyebrow>02 / 证据</Eyebrow>
            <h3>Report Evidence Hit</h3>
            <div className="pres-big-example">只引用日志 <strong>1 / 2</strong></div>
            <p>虽然猜中类别，但缺少证明代码写错的证据。</p>
            <span className="pres-plain-language">问的是：<b>有没有拿出依据？</b></span>
          </Panel>
          <Panel>
            <Eyebrow>03 / 规范</Eyebrow>
            <h3>Protocol Validity</h3>
            <div className="pres-big-example">引用 ID 不存在 <strong>✕</strong></div>
            <p>即使分析方向正确，报告仍可能无法通过校验。</p>
            <span className="pres-plain-language">问的是：<b>系统能不能可靠读取？</b></span>
          </Panel>
        </div>
        <div className="pres-bottom-note"><strong>所以：</strong>「结论正确、证据不全、报告格式有错」完全可能同时发生。三个指标各有含义，不宜只汇总一个成功率。</div>
      </div>;
    case 4:
      return <div className="pres-stack pres-comparison">
        <div className="pres-example-heading"><span className="pres-demo-label pres-demo-neutral">通俗理解</span><span>就像同一道开卷题，区别在于资料是一次给全、系统帮你查，还是自己决定查什么。</span></div>
        <div className="pres-legend"><span>故障类别判断正确率</span><span>报告证据命中率</span></div>
        <div className="pres-chart-table">
          <div className="pres-chart-head"><span>Condition</span><span>查资料的方式</span><span>类别正确</span><span>证据命中</span></div>
          {conditions.map((c) => <div key={c.name} className={"pres-chart-row" + (c.name === "L4" ? " pres-highlight" : "")}>
            <strong>{c.name}</strong><span>{c.control}</span>
            <div><span className="pres-bar pres-bar-muted" style={{ width: String(c.exact) + "%" }} /><b>{c.exact.toFixed(2)}%</b></div>
            <div><span className="pres-bar pres-bar-strong" style={{ width: String(c.evidence) + "%" }} /><b>{c.evidence.toFixed(2)}%</b></div>
          </div>)}
        </div>
        <div className="pres-bottom-note"><strong>值得追问：</strong>L3 分类准确率达到 88.33%，但证据命中只有 50.67%。是检索没找到，还是 Agent 没把找到的证据用起来？<br /><small>这些是代表性正式运行的观测差异；Oracle 属于独立诊断干预，不是 L5，也不是因果上限。</small></div>
      </div>;
    case 5:
      return <div className="pres-stack">
        <div className="pres-content-grid pres-two pres-badcases">
          <Panel>
            <Eyebrow>BADCASE A · 没找到</Eyebrow>
            <h3>Evidence Acquisition 问题</h3>
            <div className="pres-evidence-list"><span className="pres-evidence-ok">✓ 找到了失败日志</span><span className="pres-evidence-miss">✕ 没找到相关代码</span></div>
            <p>模型根本没拿到关键材料；优先检查检索与证据覆盖。</p>
          </Panel>
          <Panel>
            <Eyebrow>BADCASE B · 找到了没用</Eyebrow>
            <h3>Evidence Utilization 问题</h3>
            <div className="pres-evidence-list"><span className="pres-evidence-ok">✓ 日志和代码都找到了</span><span className="pres-evidence-miss">✕ 报告只引用失败日志</span></div>
            <p>模型拿到了材料，却没把证据写进最终报告；需要检查利用与引用。</p>
          </Panel>
        </div>
        <div className="pres-stat-row pres-stat-row-3 pres-attribution-compact">
          <Stat value="76.56%" label="L3 获取到必需证据" detail="Acquisition Recall" />
          <Stat value="66.18%" label="已获取证据最终被引用" detail="Utilization（条件分母）" />
          <Stat value="50.67%" label="最终整体证据命中" detail="Case-first Evidence Hit" />
        </div>
        <div className="pres-bottom-note"><strong>诊断验证：</strong>Oracle 绕过普通检索、直接提供关键原始证据后，代表性 Evidence Hit 为 <b>85.40%</b>（L4 为 <b>71.83%</b>）。支持调查证据发现瓶颈，但不构成严格因果证明。</div>
        <div className="pres-example-smallprint">上方 A / B 是教学示例；百分比来自 L3 正式归因实验，三项指标的分母与聚合口径不同。</div>
      </div>;
    case 6:
      return <div className="pres-stack">
        <div className="pres-example-heading"><TeachingTag /><span>Agent 找到了位置，却没有按系统认可的 Evidence ID 来引用</span></div>
        <div className="pres-content-grid pres-two pres-reference-example">
          <Panel>
            <Eyebrow>原始输出（保持不变）</Eyebrow>
            <h3>「证据在 raw.log 的第 42–43 行」</h3>
            <p>人看得懂，但如果校验器只接受稳定的 Evidence ID，行号描述就可能无法正确计分。</p>
          </Panel>
          <Panel className="pres-panel-tint">
            <Eyebrow>加一层确定性规范化</Eyebrow>
            <h3>映射为可验证的 Evidence ID</h3>
            <div className="pres-code pres-small-code"><code>log:assertion-mismatch</code></div>
            <p>源内容和模型判断都没变，只把能确定解析的位置引用转换为规范 ID。</p>
          </Panel>
        </div>
        <div className="pres-stat-row pres-stat-row-3 pres-attribution-compact">
          <Stat value="81.36 → 96.61%" label="Protocol Validity" detail="更少引用格式问题" />
          <Stat value="12 → 0" label="Unknown Evidence IDs" detail="无法识别的引用归零" />
          <Stat value="88.33% 不变" label="Failure Type Exact Match" detail="模型分类没有改善" />
        </div>
        <div className="pres-bottom-note"><strong>结论：</strong>固定历史模型输出，仅改变引用规范化，再使用相同 Validator / Scorer 重放。提升来自评测基础设施，而不是模型重新推理了一遍。</div>
      </div>;
    case 7:
      return <div className="pres-stack">
        <div className="pres-content-grid pres-two pres-policy pres-policy-simple">
          <Panel>
            <Eyebrow>BEFORE · SINGLE / SEQUENTIAL</Eyebrow>
            <h3>一次查一份材料</h3>
            <Flow items={["问模型", "查日志", "再问模型", "查代码"]} />
            <p>多次模型往返会带来额外等待。</p>
          </Panel>
          <Panel className="pres-panel-tint">
            <Eyebrow>AFTER · BATCH / PARALLEL</Eyebrow>
            <h3>一次决定，多路并行查询</h3>
            <div className="pres-parallel-demo"><span>模型一次提出独立工具调用</span><div><b>查日志</b><b>查代码</b></div><span>统一返回工具结果</span></div>
            <p>并不是少看了很多资料，而是减少不必要的决策往返。</p>
          </Panel>
        </div>
        <div className="pres-stat-row pres-stat-row-3 pres-efficiency pres-attribution-compact">
          <Stat value="877 → 571" label="Model Decisions" detail="−34.89%" />
          <Stat value="978 → 807s" label="Run Wall Time" detail="−17.54%" />
          <Stat value="809 → 775" label="Executed ToolCalls" detail="−4.20%" />
        </div>
        <div className="pres-bottom-note"><strong>实验判断：</strong>在主要配置一致的对照与重复实验中，效率收益再次出现；质量指标的小幅差异仍需谨慎解释，不能直接当作 Tool Policy 的因果影响。</div>
      </div>;
    default:
      return <div className="pres-conclusion">
        <div className="pres-conclusion-lead">发现 Badcase → 区分原因 → 设计实验 → 验证改进</div>
        <div className="pres-content-grid pres-three">
          <Panel><span className="pres-step-number">01</span><h3>先把尺子做对</h3><p>冻结输入与 Ground Truth，分别衡量分类、证据和输出协议。</p></Panel>
          <Panel><span className="pres-step-number">02</span><h3>分数低，要问为什么</h3><p>没找到证据？找到了没引用？还是评测器没识别？不能一概归咎于模型。</p></Panel>
          <Panel><span className="pres-step-number">03</span><h3>改进靠实验验证</h3><p>固定输出 Replay、诊断干预、控制实验，各自回答不同的问题。</p></Panel>
        </div>
        <div className="pres-transfer"><strong>迁移到 Agent / Skill / MCP 评测</strong><span>通用的是「定义成功、保留证据、分析失败、实验验证」；具体的测试集和指标需要贴合业务重新设计。</span></div>
        <LinkRow links={[{ name: "查看完整评测平台", url: "/" }, { name: "查看实验与归因", url: "/compare" }, { name: "查看真实 Case", url: "/cases" }]} />
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
