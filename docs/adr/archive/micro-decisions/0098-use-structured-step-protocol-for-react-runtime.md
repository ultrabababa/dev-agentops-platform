# Use Structured Step Protocol for ReAct Runtime

V1 self-built ReAct runtime will use a structured step protocol rather than requiring a literal Thought/Action/Observation text transcript. The runtime should record step index, tool calls, arguments, observations, selected evidence, visible assistant messages when applicable, and final structured report submission, making traces auditable and comparable with function-calling or future framework runtimes without storing hidden reasoning text.
