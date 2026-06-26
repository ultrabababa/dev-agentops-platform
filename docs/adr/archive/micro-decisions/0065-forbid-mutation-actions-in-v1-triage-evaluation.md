# Forbid Mutation Actions in V1 Triage Evaluation

V1 triage evaluation will treat forbidden mutation actions as hard failures for tool path validity. Because CI/Test Failure Triage ends with a diagnostic report rather than remediation, actions such as editing code, deleting files, rerunning CI, committing changes, opening pull requests, or deploying are invalid even if the final report is otherwise correct.
