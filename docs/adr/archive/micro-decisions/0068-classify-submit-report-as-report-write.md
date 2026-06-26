# Classify Submit Report as Report Write

V1 will classify `submit_report` as a report-write tool rather than a read-only tool or an external mutation tool. It writes the structured triage report into DevAgentOps state and is required to complete triage, but it does not mutate the repository, CI system, pull requests, deployments, or other external development workflow resources.
