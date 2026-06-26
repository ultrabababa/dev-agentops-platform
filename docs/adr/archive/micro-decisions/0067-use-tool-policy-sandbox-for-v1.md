# Use Tool Policy Sandbox for V1

V1 will implement sandboxing as a tool-level policy boundary with allowlists, risk levels, and optional human confirmation rather than OS-level isolation such as containers, seccomp, or microVMs. This matches the local offline CI/Test Failure Triage scope while making read-only triage tools, report submission, and forbidden mutation tools explicit in traces, policies, and evaluation.
