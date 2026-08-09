# Evaluation loader fixture

This tiny Schema V2 suite exists only to test the Offline Case Package loader,
Suite Manifest validator, fingerprint chain, scorer, and `eval doctor` CLI boundary.
It is deliberately too small to be a Formal Evaluation Suite and must not be used
for runtime comparisons, leaderboards, or claims about triage quality.

The future Formal Evaluation Suite will use separately reviewed immutable V2 Cases
with the balanced V1 Failure Type distribution defined by the evaluation policy.
