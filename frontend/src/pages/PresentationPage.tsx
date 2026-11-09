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
    title: "Agent 评测与实验归因实践",
    lead: "以 CI 失败诊断为例，分享评测体系、失败归因与工程优化的实践。",
    notes: "大家好，今天分享之前做过的 DevAgentOps。它的场景是 CI / Test Failure Triage，但今天不主要讲 Agent 怎么实现，而是重点讲三个问题：怎么设计一套可信的评测、评测不理想时怎么归因、怎么通过实验验证改进。我会用一个简单的小例子贯穿其中。这个例子只用于解释方法，正式指标来自冻结的 20-Case Suite。",
  },
  {
    section: "01 · SCENARIO",
    title: "一条测试失败日志，Agent 到底要做什么？",
    lead: "先看一个小例子：预期 2 + 3 = 5，测试却得到 6。只说「断言失败」够不够？",
    notes: "先看一个很简单的 CI 失败：预期 2 + 3 是 5，实际却得到 6。日志只能告诉我们测试断言失败；读到代码后才发现乘法代替了加法。Agent 最少得判断故障类型、定位原因、引用日志和代码并生成结构化报告。真实场景资料更大，Runtime 用只读工具搜索，但本次不展开其内部实现。",
  },
  {
    section: "02 · BENCHMARK",
    title: "怎样把一个例子做成可重复评测的 Case？",
    lead: "核心不是给模型出一道题，而是把题目、标准答案、判分依据和运行条件都固定下来。",
    notes: "评测的第一步是固定尺子。Case 分成 Agent 可见的日志、代码、工具和报告格式，以及只有 Evaluator 可见的故障类型、Required Evidence 和评分规则。要强调参考答案绝不能给被测 Agent。我们的正式 Suite 有 20 个 Human-reviewed Case，覆盖五类失败；每个重复三次，按 Case 聚合后再看整个 Suite。",
  },
  {
    section: "03 · METRICS",
    title: "诊断对了，不代表证据和报告也合格",
    lead: "同一份 Agent 报告至少可以拆成三道独立的判断题。",
    notes: "为什么不能只看分类准确率？举例来说，Agent 识别为测试断言失败，分类是对的；但假设此 Case 要求两条证据，最后只引用日志，没有引用代码，Evidence Hit 就只有 1/2；如果证据 ID 格式或内容违反 Schema，Protocol Validity 还可能失败。这里的 1/2 是说明用的算例，不是正式样本评分。三项指标分别回答结论对不对、有没有证据、机器能不能消费报告。",
  },
  {
    section: "04 · CONDITIONS",
    title: "同一道题，换一种「查资料」的方法",
    lead: "L1–L4 的区别，可以理解为让模型用不同方式获得材料、决定下一步动作。",
    notes: "这里不要细讲 Runtime。把 L1–L4 理解为同一道开卷题的四种查资料方式：L1 一次看全，L2 固定两阶段，L3 程序预先检索，L4 让模型使用只读工具自主调查。代表性结果里 L3 类别准确达到 88.33%，但是 Evidence Hit 只有 50.67%，引出后面的问题：是没找到证据，还是拿到了没用？Oracle 单独作为诊断干预，不是 L5。不同 fresh Run 不能直接解释为因果。",
  },
  {
    section: "05 · ATTRIBUTION",
    title: "证据没命中：没找到，还是找到了没用？",
    lead: "这两种 Badcase 看起来都会扣分，但应该采用不同的改进办法。",
    notes: "这页是重点。先用刚才的例子对比两种 Badcase：A 只检索到日志，没拿到代码；B 日志和代码都拿到了，最后只引用日志。两个都导致 Evidence Hit 低，却应该优化不同环节。L3 的 Acquisition Recall 为 76.56%，已获取证据被最终引用比例为 66.18%，最终 Case-first Evidence Hit 是 50.67%。注意三项分母与聚合口径不等同，不能机械相乘。Oracle 把关键原始证据提供给模型，代表性 Evidence Hit 为 85.40%，只说明值得继续研究证据发现，不是严格因果或上限。",
  },
  {
    section: "06 · CONTROLLED REPLAY",
    title: "模型答案没变，为什么评分反而提升？",
    lead: "有些 Badcase 不是模型判断错，而是证据引用格式没有被评测基础设施正确识别。",
    notes: "第二个重点实验：有些 Badcase 模型已找到证据，但引用的 raw.log 行号没被按规范识别。怎样确认不是模型本身判断错？把历史模型输出完全固定，不重新生成，只对可确定映射的 Evidence Reference 做 Canonicalization，再用相同 Validator / Scorer 重放。Protocol Validity 81.36% 到 96.61%，Unknown Evidence IDs 12 到 0，但分类 Exact Match 保持 88.33%。所以这里修复的是校验与引用基础设施，而不是模型重新变聪明。",
  },
  {
    section: "07 · OPTIMIZATION",
    title: "改进方案真的有效吗？做一次对照实验",
    lead: "一个容易理解的例子：原来查询日志和代码要反复找模型，现在可在同轮提出独立工具调用、并行执行。",
    notes: "最后讲一次效率优化。过去每轮最多执行一个工具调用，查日志再查代码要多次模型往返。现在允许同轮提出多个相互独立的工具请求并行执行。对照实验保持 Suite、模型配置、评分口径、Runtime 家族等主要条件一致，改变 Tool Policy，并做重复实验。Model Decisions 877 到 571，Wall Time 978.27 秒到 806.69 秒，工具调用次数却只下降约 4%。因此主要收益是模型往返变少；质量上小幅差异不宜做强因果解释。",
  },
  {
    section: "08 · TAKEAWAYS",
    title: "评测真正的价值：告诉我们下一步改哪里",
    lead: "不是拿到一张成绩单，而是把发现问题 → 找原因 → 做实验 → 验证改进连成闭环。",
    notes: "最后收束为三点。第一，评测先把尺子做对：冻结 Case、Ground Truth、Scorer。第二，不能只看分数，要区分证据未获取、已获取未引用和评测协议本身的问题。第三，找到问题后，要选合适的实验验证改进，并区分观察与因果结论。对其他 Agent、Skill、MCP 的评测也有方法论参考，但必须重新定义业务目标、样本和指标。谢谢大家。",
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
          <h1>Agent 评测与<br /><em>实验归因实践</em></h1>
          <p>以 DevAgentOps 的 CI 失败诊断场景为例</p>
          <p className="pres-cover-desc">怎么评、怎么归因、怎么用实验证明改进有效。</p>
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
        <div className="pres-example-answer"><strong>一份可信的诊断报告</strong><span>分类：<b>断言失败</b></span><span>根因：<b>加法写成乘法</b></span><span>引用：<b>日志 + 代码</b></span></div>
        <div className="pres-bottom-note"><strong>为什么不能只看答案：</strong>说出「断言失败」只完成分类；定位错误代码并引用证据，才有可核查的诊断依据。</div>
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
            <div className="pres-example-lines"><span>正确类别：test_assertion_failure</span><span>Required Evidence：日志 + 代码</span><span>统一报告格式、Validator / Scorer</span></div>
            <p><strong>信任边界：</strong>标准答案和 Required Evidence 标签只能留在评测侧。</p>
          </Panel>
        </div>
        <Flow items={["固定题目", "运行 Agent", "拿到报告", "对照标准答案", "聚合并分析"]} />
        <div className="pres-example-smallprint">示例中的日志与代码是构造材料；20 个 Case × 3 次重复是正式评测规模，覆盖 5 类 CI 失败。</div>
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
        <div className="pres-bottom-note"><strong>三个维度，三类问题：</strong>分类正确 ≠ 证据充分 ≠ 输出合法。保留指标向量，才能判断该改模型、检索还是报告协议。</div>
      </div>;
    case 4:
      return <div className="pres-stack pres-comparison">
        <div className="pres-example-heading"><span className="pres-demo-label pres-demo-neutral">开卷考试类比</span><span>同一套题，改变资料获取方式；观察分类和证据两类结果。</span></div>
        <div className="pres-legend"><span>故障类型 Exact Match</span><span>报告证据 Evidence Hit</span></div>
        <div className="pres-chart-table">
          <div className="pres-chart-head"><span>条件</span><span>资料从哪里来</span><span>分类准确</span><span>证据命中</span></div>
          {conditions.map((c) => <div key={c.name} className={"pres-chart-row" + (c.name === "L3" ? " pres-highlight" : "") + (c.name === "Oracle" ? " pres-oracle-row" : "")}>
            <strong>{c.name}</strong><span>{c.control}</span>
            <div className="pres-metric-cell"><span className="pres-bar pres-bar-muted" style={{ width: String(c.exact) + "%" }} /><b>{c.exact.toFixed(2)}%</b></div>
            <div className="pres-metric-cell"><span className="pres-bar pres-bar-strong" style={{ width: String(c.evidence) + "%" }} /><b>{c.evidence.toFixed(2)}%</b></div>
          </div>)}
        </div>
        <div className="pres-bottom-note"><strong>关键观察：</strong>L3 分类准确率 <b>88.33%</b>，证据命中只有 <b>50.67%</b>。问题究竟出在「没找到」，还是「找到了没用」？<small>Oracle ≠ L5：它是评测侧提供关键原始证据的诊断干预，不是产品 Runtime。跨 fresh Run 的观测差异不能直接当成单变量因果效应。</small></div>
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
        <div className="pres-bottom-note"><strong>Oracle 诊断干预：</strong>跳过普通证据发现，模型看到关键原始片段后，代表性 Evidence Hit 为 <b>85.40%</b>。这是瓶颈线索，不是理论上限或严格因果估计。</div>
        <div className="pres-example-smallprint">上方 A / B 是教学示例；百分比来自 L3 正式归因实验，三项指标的分母与聚合口径不同。</div>
      </div>;
    case 6:
      return <div className="pres-stack">
        <div className="pres-example-heading"><TeachingTag /><span>模型找到了证据，但引用表示方式没有被校验器识别。</span></div>
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
        <div className="pres-control-strip"><span><b>保持不变</b> 历史模型输出</span><span><b>只改一处</b> 引用规范化</span><span><b>重新验证</b> 同一 Validator / Scorer</span></div>
        <div className="pres-stat-row pres-stat-row-3 pres-attribution-compact">
          <Stat value="81.36 → 96.61%" label="Protocol Validity" detail="更少引用格式问题" />
          <Stat value="12 → 0" label="Unknown Evidence IDs" detail="无法识别的引用归零" />
          <Stat value="88.33% 不变" label="Failure Type Exact Match" detail="模型分类没有改善" />
        </div>
        <div className="pres-bottom-note"><strong>实验支持的结论：</strong>协议有效性改善，但分类判断没有变化。修复的是 Evidence Reference 的规范化与验证环节，不是模型重新推理得更好。</div>
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
        <div className="pres-bottom-note"><strong>实验结论：</strong>效率收益在重复实验中再次出现；主要减少的是模型决策往返，而不是大幅减少取证。fresh generation 的小幅质量差异不等于因果结论。</div>
      </div>;
    default:
      return <div className="pres-conclusion">
        <div className="pres-conclusion-lead">评测 → 归因 → 实验 → 工程改进 → 再评测</div>
        <div className="pres-content-grid pres-three">
          <Panel><span className="pres-step-number">01</span><h3>先把尺子做对</h3><p>冻结输入与 Ground Truth，分别衡量分类、证据和输出协议。</p></Panel>
          <Panel><span className="pres-step-number">02</span><h3>分数低，要问为什么</h3><p>没找到证据？找到了没引用？还是评测器没识别？不能一概归咎于模型。</p></Panel>
          <Panel><span className="pres-step-number">03</span><h3>改进靠实验验证</h3><p>固定输出 Replay、诊断干预、控制实验，各自回答不同的问题。</p></Panel>
        </div>
        <div className="pres-transfer"><strong>面向 Agent / Skill / MCP</strong><span>通用的是评测闭环；业务成功标准、Case 和评分指标必须按真实任务重新设计。</span></div>
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
