# Enforce Forbidden Actions in Policy and Evaluation

V1 will enforce forbidden triage actions both before and after execution. Sandbox or tool policy should prevent mutation actions from being available or approved for CI/Test Failure Triage, while evaluation scoring will still inspect run traces and hard-fail tool path validity if forbidden actions appear, making governance violations visible even when prevention fails.
