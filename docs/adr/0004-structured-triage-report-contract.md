# Use Structured Triage Reports as the Runtime Contract

V1 will require the agent to submit triage reports as schema-validated structured data, with Markdown treated only as a rendering format. This makes report completeness, failure type accuracy, evidence matching, trace review, and regression evaluation reliable; free-form Markdown would be easier to read initially but too brittle as the source of truth for AgentOps metrics.
