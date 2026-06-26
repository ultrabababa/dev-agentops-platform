# Allow Project Knowledge but Not Evaluation Artifacts

V1 triage agents may retrieve project knowledge such as SOPs, troubleshooting runbooks, repository architecture notes, dependency policies, and testing conventions. They must not retrieve expected answers, historical badcase reviews, leaderboard conclusions, debug findings, or previous evaluation reports, because those artifacts leak evaluation feedback rather than representing normal project knowledge.
