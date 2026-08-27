import type { ReactNode } from "react";

import { ArchitectureEdge, ArchitectureNode, DiagramFrame } from "./ConditionShared";

function EvaluatorRail({ children }: { children: ReactNode }) {
  return <div className="diagram-evaluator-rail"><span>模型看不到 / 仅评测侧</span>{children}</div>;
}

export function L1Diagram() {
  return (
    <DiagramFrame title="一次把全部上下文交给模型" description="L1 是最简单的基线：程序把冻结 Case 的日志、代码快照和引用坐标整理成一个请求，模型只调用一次并直接生成最终报告。" className="linear-diagram">
      <div className="diagram-lane-label">主流程</div>
      <div className="architecture-flow six-step">
        <ArchitectureNode badge="SOURCE" label="冻结 Case" detail="raw.log + frozen repository snapshot" />
        <ArchitectureEdge />
        <ArchitectureNode badge="INPUT" label="完整上下文" detail="日志、代码与引用坐标一次性进入模型" tone="runtime" />
        <ArchitectureEdge />
        <ArchitectureNode badge="MODEL" label="单次模型调用" detail="不调用工具，也没有多轮 Agent 调查" tone="signal" />
        <ArchitectureEdge />
        <ArchitectureNode badge="OUTPUT" label="Structured Report" detail="模型生成最终结构化诊断报告" />
        <ArchitectureEdge />
        <ArchitectureNode badge="EVAL" label="Validator / Scorer" detail="用同一套确定性规则校验和评分" tone="evaluator" />
      </div>
      <EvaluatorRail><span>Expected Answer</span><span>Required Evidence 标签 / selection</span><span>scorer ground truth</span></EvaluatorRail>
    </DiagramFrame>
  );
}

export function L2Diagram() {
  return (
    <DiagramFrame title="同一份完整上下文，固定分成两次模型调用" description="程序先让模型做 Evidence 分析，再把这一步的可见输出作为 handoff，连同完整 Evidence 一起交给第二次调用生成最终报告。模型不能自己改变这条流程。" className="linear-diagram l2-diagram">
      <div className="diagram-lane-label">程序固定流程</div>
      <div className="architecture-flow l2-flow">
        <ArchitectureNode badge="INPUT" label="完整 Evidence" detail="两个阶段都会收到同一冻结 Case 的完整上下文" />
        <ArchitectureEdge />
        <ArchitectureNode badge="STAGE 1" label="先分析 Evidence" detail="evidence_analysis · 生成工作备忘" tone="runtime" />
        <ArchitectureEdge />
        <ArchitectureNode badge="STAGE 2" label="再生成最终报告" detail="report_synthesis · handoff + 完整 Evidence" tone="signal" />
        <ArchitectureEdge />
        <ArchitectureNode badge="OUTPUT" label="Structured Report" detail="最终结构化诊断报告" />
        <ArchitectureEdge />
        <ArchitectureNode badge="EVAL" label="Validator / Scorer" detail="确定性校验与评分" tone="evaluator" />
      </div>
      <div className="program-stop-rail"><span>程序不提供工具或 Retrieval，也没有额外的 verifier / repair stage；模型不能增加、跳过或重排这两个阶段</span><code>evidence_analysis → report_synthesis → stop</code></div>
      <EvaluatorRail><span>Expected Answer</span><span>Required Evidence 标签 / selection</span><span>scorer ground truth</span></EvaluatorRail>
    </DiagramFrame>
  );
}

export function L3Diagram() {
  return (
    <DiagramFrame title="程序先自动找证据，再让模型诊断一次" description="L3 不把全部上下文交给模型。Static Retriever 按冻结规则从日志和代码快照里选出一部分原始片段；模型的 Evidence context 只包含这些检索结果。Required Evidence 只在运行结束后用于检查“哪里丢了证据”。" className="l3-diagram">
      <div className="diagram-lane-label">模型输入怎么产生</div>
      <div className="architecture-flow l3-main-flow">
        <ArchitectureNode badge="SOURCE" label="冻结日志和代码" detail="raw.log + frozen repository snapshot" />
        <ArchitectureEdge />
        <ArchitectureNode badge="PROGRAM" label="Static Retriever 自动检索" detail="固定规则选片段、排序并 packing" tone="runtime" />
        <ArchitectureEdge />
        <ArchitectureNode badge="VISIBLE" label="Evidence context 只含检索片段" detail="source / span / content + answer-neutral 引用坐标" tone="signal" />
        <ArchitectureEdge />
        <ArchitectureNode badge="MODEL" label="单次模型调用" detail="模型不会自己生成 query 或追加搜索" />
        <ArchitectureEdge />
        <ArchitectureNode badge="OUTPUT" label="Structured Report" detail="最终结构化诊断报告" />
        <ArchitectureEdge />
        <ArchitectureNode badge="EVAL" label="Validator / Scorer" detail="确定性校验与评分" tone="evaluator" />
      </div>
      <div className="attribution-flow" aria-label="evaluator-side Evidence loss attribution">
        <span>运行结束后，再检查证据到底丢在哪一步</span>
        <div><ArchitectureNode label="评测侧 Required Evidence" tone="evaluator" /><ArchitectureEdge /><ArchitectureNode label="Retriever 找到了吗？" tone="evaluator" /><ArchitectureEdge /><ArchitectureNode label="最终报告正确引用了吗？" tone="evaluator" /></div>
        <p>Required Evidence 只用于事后对照：先看 Retriever 有没有把需要的证据找出来，再看找到的证据有没有进入最终报告。它不会参与 retrieval query，也不会进入模型输入。</p>
      </div>
    </DiagramFrame>
  );
}

export function L4Diagram() {
  return (
    <DiagramFrame title="模型自己决定下一步查什么" description="L4 把调查控制权交给模型：每一轮模型选择一个只读工具，或者直接提交报告。Runtime 负责检查请求、执行工具、把 ToolResult 返回模型，并记录整个运行过程。" className="l4-diagram">
      <div className="l4-context-row">
        <ArchitectureNode badge="WORKSPACE" label="只读 Workspace" detail="冻结 raw.log + repository snapshot" />
        <p>整个 episode 都在同一个冻结 Case 上运行；模型只能通过只读工具逐步查看 workspace 内容。</p>
      </div>
      <div className="diagram-lane-label">每一轮 Model Decision</div>
      <div className="architecture-flow l4-main-flow">
        <ArchitectureNode badge="MODEL" label="模型决定下一步" detail="继续查证据，或提交最终报告" tone="signal" />
        <ArchitectureEdge />
        <ArchitectureNode badge="REQUEST" label="Runtime 每轮最多接受 1 个 ToolCall" detail="read · grep · find · ls" />
        <ArchitectureEdge />
        <ArchitectureNode badge="RUNTIME" label="Runtime 执行工具" detail="校验请求 · 顺序执行 · 限制输出" tone="runtime" />
        <ArchitectureEdge />
        <ArchitectureNode badge="RESULT" label="ToolResult 返回模型" detail="成为下一轮模型可见上下文" />
      </div>
      <div className="l4-cycle-note">↺ ToolResult 返回后，模型继续下一轮 Model Decision</div>
      <div className="baseline-policy-error"><span>如果同一轮给出多个 ToolCall</span><strong>全部不执行；每个调用收到 policy-error ToolResult，然后模型重新决策。</strong></div>
      <div className="diagram-lane-label terminal-label">如果模型选择结束调查</div>
      <div className="architecture-flow l4-terminal-flow">
        <ArchitectureNode badge="TERMINAL" label="提交 Structured Report" detail="没有自动 repair / rescue call" tone="signal" />
        <ArchitectureEdge />
        <ArchitectureNode badge="EVAL" label="Validator / Scorer" detail="确定性校验与评分" tone="evaluator" />
      </div>
      <div className="observation-channels">
        <div><span>TRAJECTORY · 模型交互轨迹</span><strong>模型真正看到的对话历史</strong><small>User / Assistant / ToolResult 按顺序组成下一轮上下文</small></div>
        <div><span>TRACE · Runtime 运行记录</span><strong>系统另外记录的执行日志</strong><small>工具执行、延迟、预算、终止原因等；Trace ≠ Trajectory，也不会作为对话发回模型</small></div>
      </div>
    </DiagramFrame>
  );
}

export function OracleDiagram() {
  return (
    <DiagramFrame title="评测侧先定位关键证据，模型只看到证据内容" description="Oracle 跳过普通的“自己找证据”过程。评测侧用 required_evidence_ids 找到冻结文件里的原始片段；在 evidence context 这一部分，模型只拿到这些片段，不会看到 Expected Answer，也不知道为什么选中了它们。" className="oracle-diagram">
      <div className="oracle-lane evaluator-path">
        <div className="diagram-lane-label">仅评测侧：先确定要给哪段原始证据</div>
        <ArchitectureNode badge="SELECTOR" label="required_evidence_ids" detail="人工复核后确定，只在评测侧使用" tone="evaluator" />
        <ArchitectureEdge />
        <ArchitectureNode badge="RESOLVER" label="找到原始位置" detail="根据 Evidence ID 定位冻结文件里的 source coordinates" tone="evaluator" />
        <ArchitectureEdge />
        <ArchitectureNode badge="SOURCE" label="取出原始证据片段" detail="source-faithful Physical Artifact content" tone="evaluator" />
        <div className="oracle-hidden"><span>这些信息始终不发送给模型</span><small>Expected Answer · Required-Evidence selection semantics · curator rationale · scorer labels · fix information</small></div>
      </div>
      <div className="oracle-transfer" aria-label="visibility boundary transfer"><span>可见性边界</span><strong>只有原始证据片段通过</strong><i aria-hidden="true">→</i><small>不会附带“这是 Required Evidence”或为什么选择它的标签</small></div>
      <div className="oracle-lane model-path">
        <div className="diagram-lane-label">模型可见：只拿到选中的原始证据</div>
        <ArchitectureNode badge="INPUT" label="选中的原始 Source Evidence" detail="evidence_id / source / span / content" tone="signal" />
        <ArchitectureEdge />
        <ArchitectureNode badge="MODEL" label="单次模型调用" detail="模型不知道这些片段来自 Oracle selection" />
        <ArchitectureEdge />
        <ArchitectureNode badge="OUTPUT" label="Structured Report" detail="生成与其他 Conditions 同格式的最终报告" />
        <ArchitectureEdge />
        <ArchitectureNode badge="EVAL" label="同一 Validator / Scorer" detail="仍用同一套确定性评分合同" tone="runtime" />
      </div>
      <p className="oracle-anonymity-note">模型输入仍然是 answer-neutral：它可以看到并引用 source spans，但看不到 Required Evidence 标签、Expected Answer、选择理由或评分标签。</p>
    </DiagramFrame>
  );
}
