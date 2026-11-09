import { useEffect, useState, type ReactNode } from "react";

type Slide = {
  section: string;
  title: string;
  lead: string;
};

const slides: Slide[] = [
  {
    section: "INTRODUCTION",
    title: "Agent 评测与实验归因实践",
    lead: "以 CI 失败诊断为例，分享评测体系、失败归因与工程优化的实践。",
  },
  {
    section: "01 · SCENARIO",
    title: "CI 失败诊断：从错误现象到证据链",
    lead: "示例：测试期望 2 + 3 = 5，实际返回 6；日志与源码提供不同层面的证据。",
  },
  {
    section: "02 · BENCHMARK",
    title: "从失败样例到可复现评测集",
    lead: "冻结输入和运行条件，隔离 Ground Truth，以统一 Scorer 保证评测口径。",
  },
  {
    section: "03 · METRICS",
    title: "诊断对了，不代表证据和报告也合格",
    lead: "对同一份报告分别衡量故障分类、必需证据覆盖与输出协议有效性。",
  },
  {
    section: "04 · CONDITIONS",
    title: "同一道题，换一种「查资料」的方法",
    lead: "L1–L4 改变上下文供给和执行方式，观察诊断质量与证据引用的差异。",
  },
  {
    section: "05 · ATTRIBUTION",
    title: "证据没命中：没找到，还是找到了没用？",
    lead: "相同的 Evidence Hit 失分，可能来自证据获取与证据利用两个不同环节。",
  },
  {
    section: "06 · CONTROLLED REPLAY",
    title: "固定输出重放：区分模型诊断与引用格式问题",
    lead: "保持模型历史输出不变，仅调整确定性引用规范化逻辑，验证基础设施影响。",
  },
  {
    section: "07 · OPTIMIZATION",
    title: "工具并行化：用对照实验验证效率收益",
    lead: "将可独立执行的 ToolCalls 合并到同一轮并行执行，减少模型往返开销。",
  },
  {
    section: "08 · TAKEAWAYS",
    title: "Evaluation-driven Development：评测驱动迭代",
    lead: "将 Badcase 诊断转化为可验证的工程决策，形成持续评测与改进闭环。",
  },
];

const conditions = [
  { name: "L1", control: "完整上下文 / 单轮", exact: 80.0, evidence: 52.16 },
  { name: "L2", control: "完整上下文 / 两阶段", exact: 83.33, evidence: 54.15 },
  { name: "L3", control: "静态检索 / 单轮", exact: 88.33, evidence: 50.67 },
  { name: "L4", control: "自主工具调用 / 多轮", exact: 81.67, evidence: 71.83 },
  { name: "Oracle", control: "评测侧提供关键证据", exact: 83.33, evidence: 85.4 },
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
          <p className="pres-cover-desc">评测基准 · 失败归因 · 实验验证 · 工程优化</p>
        </div>
        <div className="pres-cover-bottom">
          <Stat value="20 × 3" label="正式评测 Case × 重复次数" />
          <Stat value="L1–L4" label="不同执行条件" />
          <Stat value="4" label="代表性实验研究" />
        </div>
      </div>;
    case 1:
      return <div className="pres-stack">
        <div className="pres-example-heading"><TeachingTag /><span>任务输出：故障分类 · 根因定位 · 可核查的证据引用</span></div>
        <div className="pres-content-grid pres-two">
          <Panel>
            <Eyebrow>01 / 测试日志：识别失败现象</Eyebrow>
            <div className="pres-code">
              <span className="pres-code-label">tests/test_calculate.py</span>
              <code>assert calculate_total(2, 3) == 5</code>
              <code className="pres-code-error">AssertionError: expected 5, got 6</code>
            </div>
            <p className="pres-example-caption">日志只说明结果不符合预期，还没解释根因。</p>
          </Panel>
          <Panel>
            <Eyebrow>02 / 源代码：定位实现错误</Eyebrow>
            <div className="pres-code">
              <span className="pres-code-label">repository/calculator.py</span>
              <code>def calculate_total(a, b):</code>
              <code className="pres-code-error">    return a * b  # 本应相加</code>
            </div>
            <p className="pres-example-caption">真正的原因是实现写成乘法，而不是加法。</p>
          </Panel>
        </div>
        <div className="pres-example-answer"><strong>目标诊断报告（示意）</strong><span>分类：<b>断言失败</b></span><span>根因：<b>加法写成乘法</b></span><span>引用：<b>日志 + 代码</b></span></div>
        <div className="pres-bottom-note"><strong>评测重点：</strong>仅识别「测试断言失败」属于故障分类；结合源码定位根因，并引用日志与代码，才能形成可核查的诊断依据。</div>
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
            <Eyebrow>被测 Agent 可见（输入）</Eyebrow>
            <h3>冻结的案例材料</h3>
            <div className="pres-example-lines"><span>失败日志：expected 5, got 6</span><span>仓库代码：return a * b</span><span>允许使用的工具 / 报告格式</span></div>
            <p>不同执行条件使用同一 Case 快照，保证输入可追溯。</p>
          </Panel>
          <Panel className="pres-panel-tint">
            <Eyebrow>评测器专有（参考标准）</Eyebrow>
            <h3>Ground Truth + Scorer</h3>
            <div className="pres-example-lines"><span>正确类别：test_assertion_failure</span><span>Required Evidence：日志 + 代码</span><span>统一报告 Schema、Validator / Scorer</span></div>
            <p><strong>信任边界：</strong>标准答案和 Required Evidence 标签只能留在评测侧。</p>
          </Panel>
        </div>
        <Flow items={["冻结 Case", "执行 Agent", "结构化报告", "校验与评分", "Case-first 聚合"]} />
        <div className="pres-example-smallprint">示例中的日志与代码是构造材料；20 个 Case × 3 次重复是正式评测规模，覆盖 5 类 CI 失败。</div>
      </div>;
    case 3:
      return <div className="pres-stack">
        <div className="pres-example-heading"><TeachingTag /><span>假设本例的两条必需证据是「失败日志」和「相关代码」</span></div>
        <div className="pres-content-grid pres-three pres-metrics pres-simple-metrics">
          <Panel>
            <Eyebrow>01 / 结论</Eyebrow>
            <h3>Failure Type Exact Match</h3>
            <div className="pres-big-example">类别匹配 <strong>✓</strong></div>
            <p>Agent 输出「测试断言失败」，与参考类别一致。</p>
            <span className="pres-plain-language">判断维度：<b>故障类型匹配</b></span>
          </Panel>
          <Panel>
            <Eyebrow>02 / 证据</Eyebrow>
            <h3>Report Evidence Hit</h3>
            <div className="pres-big-example">只引用日志 <strong>1 / 2</strong></div>
            <p>分类结果正确，但缺少定位根因所需的代码引用。</p>
            <span className="pres-plain-language">判断维度：<b>必需证据覆盖</b></span>
          </Panel>
          <Panel>
            <Eyebrow>03 / 规范</Eyebrow>
            <h3>Protocol Validity</h3>
            <div className="pres-big-example">引用 ID 不存在 <strong>✕</strong></div>
            <p>即使分析方向正确，报告仍可能无法通过校验。</p>
            <span className="pres-plain-language">判断维度：<b>输出与引用是否合法</b></span>
          </Panel>
        </div>
        <div className="pres-bottom-note"><strong>三个维度，三类问题：</strong>分类正确 ≠ 证据充分 ≠ 输出合法。分别保留指标，便于后续针对 Badcase 进行归因分析。</div>
      </div>;
    case 4:
      return <div className="pres-stack pres-comparison">
        <div className="pres-example-heading"><span className="pres-demo-label pres-demo-neutral">相同评测基准</span><span>比较不同上下文供给与执行条件下的分类和证据指标。</span></div>
        <div className="pres-legend"><span>故障类型 Exact Match</span><span>报告证据 Evidence Hit</span></div>
        <div className="pres-chart-table">
          <div className="pres-chart-head"><span>条件</span><span>资料从哪里来</span><span>分类准确</span><span>证据命中</span></div>
          {conditions.map((c) => <div key={c.name} className={"pres-chart-row" + (c.name === "L3" ? " pres-highlight" : "") + (c.name === "Oracle" ? " pres-oracle-row" : "")}>
            <strong>{c.name}</strong><span>{c.control}</span>
            <div className="pres-metric-cell"><span className="pres-bar pres-bar-muted" style={{ width: String(c.exact) + "%" }} /><b>{c.exact.toFixed(2)}%</b></div>
            <div className="pres-metric-cell"><span className="pres-bar pres-bar-strong" style={{ width: String(c.evidence) + "%" }} /><b>{c.evidence.toFixed(2)}%</b></div>
          </div>)}
        </div>
        <div className="pres-bottom-note"><strong>关键观察：</strong>L3 分类准确率 <b>88.33%</b>，证据命中仅 <b>50.67%</b>。<strong>归因方向：</strong>区分检索未获取与获取后未引用。<small>Oracle ≠ L5：评测侧提供关键原始证据的诊断干预，并非产品 Runtime；跨 fresh Run 的差异不能直接视为单变量因果效应。</small></div>
      </div>;
    case 5:
      return <div className="pres-stack">
        <div className="pres-content-grid pres-two pres-badcases">
          <Panel>
            <Eyebrow>BADCASE A · 获取缺失</Eyebrow>
            <h3>Evidence Acquisition 问题</h3>
            <div className="pres-evidence-list"><span className="pres-evidence-ok">✓ 找到了失败日志</span><span className="pres-evidence-miss">✕ 没找到相关代码</span></div>
            <p>关键代码未进入模型上下文，应优先检查检索召回与覆盖。</p>
          </Panel>
          <Panel>
            <Eyebrow>BADCASE B · 引用缺失</Eyebrow>
            <h3>Evidence Utilization 问题</h3>
            <div className="pres-evidence-list"><span className="pres-evidence-ok">✓ 日志和代码都找到了</span><span className="pres-evidence-miss">✕ 报告只引用失败日志</span></div>
            <p>证据已进入上下文，但最终报告未引用，需要检查证据利用与引用环节。</p>
          </Panel>
        </div>
        <div className="pres-stat-row pres-stat-row-3 pres-attribution-compact">
          <Stat value="76.56%" label="L3 获取到必需证据" detail="Acquisition Recall" />
          <Stat value="66.18%" label="已获取必需证据被引用" detail="Utilization（条件分母）" />
          <Stat value="50.67%" label="最终整体证据命中" detail="Case-first Evidence Hit" />
        </div>
        <div className="pres-bottom-note"><strong>Oracle 诊断干预：</strong>直接提供关键原始证据的条件下，代表性 Evidence Hit 为 <b>85.40%</b>，支持继续调查证据获取瓶颈，但不是理论上限或严格因果估计。</div>
        <div className="pres-example-smallprint">上方 A / B 是教学示例；百分比来自 L3 正式归因实验，三项指标的分母与聚合口径不同。</div>
      </div>;
    case 6:
      return <div className="pres-stack">
        <div className="pres-example-heading"><TeachingTag /><span>模型找到了证据，但引用表示方式没有被校验器识别。</span></div>
        <div className="pres-content-grid pres-two pres-reference-example">
          <Panel>
            <Eyebrow>原始输出（保持不变）</Eyebrow>
            <h3>「证据在 raw.log 的第 42–43 行」</h3>
            <p>当报告 Schema 要求稳定 Evidence ID 时，单纯的行号引用可能无法通过验证。</p>
          </Panel>
          <Panel className="pres-panel-tint">
            <Eyebrow>确定性 Evidence Reference 规范化</Eyebrow>
            <h3>映射为可验证的 Evidence ID</h3>
            <div className="pres-code pres-small-code"><code>log:assertion-mismatch</code></div>
            <p>模型输出保持不变；仅将可确定映射的位置引用规范化为稳定 ID。</p>
          </Panel>
        </div>
        <div className="pres-control-strip"><span><b>保持不变</b> 历史模型输出</span><span><b>只改一处</b> 引用规范化</span><span><b>重新验证</b> 同一 Validator / Scorer</span></div>
        <div className="pres-stat-row pres-stat-row-3 pres-attribution-compact">
          <Stat value="81.36 → 96.61%" label="Protocol Validity" detail="更少引用格式问题" />
          <Stat value="12 → 0" label="Unknown Evidence IDs" detail="无法识别的引用归零" />
          <Stat value="88.33% 不变" label="Failure Type Exact Match" detail="模型分类没有改善" />
        </div>
        <div className="pres-bottom-note"><strong>实验结论：</strong>Protocol Validity 提升，Failure Type Exact Match 保持不变；改善来自引用规范化与校验环节。<small>本页为历史 L4 fixed-output Replay，和上一页 L4 代表性正式运行不是同一组结果。</small></div>
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
            <p>并行处理独立工具请求，减少重复模型决策往返。</p>
          </Panel>
        </div>
        <div className="pres-stat-row pres-stat-row-3 pres-efficiency pres-attribution-compact">
          <Stat value="877 → 571" label="Model Decisions" detail="−34.89%" />
          <Stat value="978 → 807s" label="Run Wall Time" detail="−17.54%" />
          <Stat value="809 → 775" label="Executed ToolCalls" detail="−4.20%" />
        </div>
        <div className="pres-bottom-note"><strong>实验结论：</strong>重复实验中模型决策次数与 Wall Time 均下降，而 ToolCalls 数量变化较小；效率收益主要来自减少模型往返。<small>Fresh generation 下的质量指标差异，不作为 Tool Policy 的严格因果证据。</small></div>
      </div>;
    default:
      return <div className="pres-conclusion">
        <div className="pres-conclusion-lead">评测 → Badcase 归因 → 实验验证 → 工程改进 → 再评测</div>
        <div className="pres-content-grid pres-three">
          <Panel><span className="pres-step-number">01</span><h3>统一评测基准</h3><p>冻结输入与 Ground Truth，分别衡量分类、证据和输出协议。</p></Panel>
          <Panel><span className="pres-step-number">02</span><h3>拆解失败环节</h3><p>区分证据获取、证据利用和协议校验的不同失效模式。</p></Panel>
          <Panel><span className="pres-step-number">03</span><h3>受控验证改进</h3><p>固定输出 Replay、诊断干预与 Tool Policy 对照，各自提供不同强度的证据。</p></Panel>
        </div>
        <div className="pres-transfer"><strong>方法论复用</strong><span>评测闭环可扩展到 Agent / Skill / MCP；具体的成功标准、Case 与指标仍需按业务重设。</span></div>
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
      <footer className="pres-footer">
        <div className="pres-footer-links"><a href="/" target="_blank" rel="noreferrer">Explorer ↗</a><a href="/compare" target="_blank" rel="noreferrer">Experiments ↗</a><a href="/architecture" target="_blank" rel="noreferrer">Architecture ↗</a></div>
        <div className="pres-controls"><button type="button" onClick={() => setIndex((i) => clampIndex(i - 1))} disabled={index === 0} aria-label="上一页">←</button><span>{String(index + 1).padStart(2, "0")} / {String(slides.length).padStart(2, "0")}</span><button type="button" onClick={() => setIndex((i) => clampIndex(i + 1))} disabled={index === slides.length - 1} aria-label="下一页">→</button></div>
      </footer>
      <div className="pres-progress" role="progressbar" aria-label="演讲进度" aria-valuenow={index + 1} aria-valuemin={1} aria-valuemax={slides.length}><span style={{ width: String(((index + 1) / slides.length) * 100) + "%" }} /></div>
    </div>
    <div className="pres-help">方向键 / 空格翻页 · F 全屏</div>
  </main>;
}
