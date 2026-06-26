# Support Repeated Runs for Stability Checks

V1 will treat LLM non-determinism as a known evaluation risk. Formal evaluation defaults to a single run per condition for cost control, but selected candidate or unstable conditions may be repeated to estimate metric variance and badcase stability; repeated runs are a targeted stability check, not the default for every evaluation condition.
