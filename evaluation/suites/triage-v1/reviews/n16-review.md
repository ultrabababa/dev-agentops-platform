# N16 — github-gptme-pr-1968 — REJECTED case record

> **FINAL DISPOSITION: `REJECTED — INVALID_FAILURE_ARTIFACT_AND_LOW_DISCRIMINATIVE_VALUE`.**
> **N16 is NOT a Formal Suite member and must never be frozen as one.**
> Retained solely as a rejection record and a negative calibration example.

**Layer 1 — Scientific Validity:** `FAIL / BLOCKED` — and **not repairable**.
**Layer 2 — Runtime Discriminative Value:** `LOW`.
**Route:** lightweight Measurement-Value Screening. Full Human Review was **deliberately not performed**, because the Layer 1 defect cannot be repaired and no full-review outcome could change the disposition.
**Failure type as drafted:** `timeout_or_flaky_failure` (not the reason for rejection).
**Fingerprint:** `80345301a60c04f71210d5719c481edc024bdb70af06c7c4185a2fcb251539df` (`provisional-pre-freeze`, rejected package; supersedes `8b1f851c…`).

## How N16 differs from N17

These two rejections must not be collapsed into one lesson. They are different failure modes.

| | N17 (`github-node-issue-61762`) | N16 (this Case) |
|---|---|---|
| Layer 1 Scientific Validity | `PASS` after repair | **`FAIL / BLOCKED`, unrepairable** |
| Layer 2 Runtime Discriminative Value | `FAIL` | `LOW` |
| Raw failure artifact | Authentic GitHub Check Run failure annotation, recovered from upstream | **Fix-PR prose written after the diagnosis was known** |
| Was salvage possible? | Yes — a test-level Check Run annotation survived and replaced the bad artifact | **No — no test-level historical artifact survives** |
| Root defect | Source chain wrongly assembled from three unrelated histories | The failure observation was never a failure observation |
| Reusable lesson | Verify the run/job that actually produced the artifact; screen for contemporaneous same-family fixes | **Never use fix-PR / fix-commit narrative as the Agent-visible raw failure artifact** |

## A. Layer 1 blocker — the raw failure artifact is fix-PR narrative

`physical-artifacts/raw.log` is one sentence, 213 bytes:

> Master CI run `23841222952` failed on `tests/test_tools_subagent.py::test_subagent_with_profile_and_model` with `TypeError: 'NoneType' object is not subscriptable` while reading `mock_create_thread.call_args[1]`.

That sentence is quoted **verbatim from the body of https://github.com/gptme/gptme/pull/1968**, whose title is `fix(test): join subagent threads before mock assertions` and which is **merged**. It is therefore the fix author's post-hoc summary of a failure, composed inside the fix PR after the diagnosis was already reached — not a historical CI observation. Under ADR 0125, fix artifacts are curator-only causal-verification inputs and must not enter the Agent-visible workspace.

The distillation matters as much as the provenance: the sentence already names the test file, the test function, the exception type, and the exact failing expression `mock_create_thread.call_args[1]`. A genuine CI artifact would not be pre-localized like that. And the very next sentence of the same PR body reads *"the failure is the test racing the background thread. Waiting for the spawned thread(s) makes the assertion deterministic"* — root cause plus recommended action, in the same paragraph the artifact was cut from.

### Salvage was attempted and is impossible

The underlying historical failure is real, and the declared revision is sound — this is not a fabricated Case:

| Check | Result |
|---|---|
| `actions/runs/23841222952` | Exists; workflow `Test`; `conclusion: failure`; `created_at 2026-04-01T09:13:55Z` |
| Run `head_sha` | `f48de363aa956caae8789a9b751d7631fd44fe3c` — **identical to the declared revision** |
| Declared revision vs fix | `compare bf9d05ce (PR #1968 head)...f48de363` → `status: behind`, `behind_by: 2`, `ahead_by: 0`, so the declared revision is a genuine **pre-fix ancestor**. PR #1968 merged at `09:47:17Z`, 34 minutes after that commit. |
| Job log | **HTTP 410** — retention expired |
| Check Run annotations | **One only**: `path: .github`, `annotation_level: failure`, `message: "Process completed with exit code 2."` — generic exit code, **no test-level failure detail** |

N17 was rescued because its Check Run retained a full test-level annotation carrying the stack, the captured output and the victim's identity. N16 has no such artifact. Nothing authentic survives to replace the fix-PR sentence, and reconstructing one would be invention. **Layer 1 is blocked, not merely defective.**

## B. Layer 2 — low discriminative value independently of Layer 1

Even setting the artifact problem aside, the bounded 4-file workspace contains the answer in two independent places, both **contemporaneous** and therefore not removable:

**1. The implementation states the mechanism in a comment.**

```
gptme/tools/subagent/api.py:417-419
  # Register Subagent BEFORE starting thread to avoid race condition:
  # run_subagent closure looks up agent_id in _subagents, which would
  # return None if the thread runs before _subagents.append(sa).
```

The drafted `root_cause` is *"The implementation publishes the subagent in the shared list before starting its background thread… Scheduler interleaving can leave call_args as None."* The comment states that structure, names the race, and explains the `None`. A second instance sits at `api.py:316`: `# (avoids race condition where fast completion can't locate sa in _subagents)`. Line 316 falls inside the Required unit `repo:gptme-tools-subagent-api-py:lines-0301-0400`, so the Required evidence itself is answer-bearing prose rather than the structural fact.

**2. Sibling tests in the same file already demonstrate the remediation.**

`tests/test_tools_subagent.py:1277` `# Wait for the thread to finish`, `:1365` `# Wait for both ACP threads to complete`, `:115` `# Sequential mode blocks with t.join(), so we need threads to complete instantly`. The drafted `recommended_action` is *"Synchronize the test with completion of the spawned subagent thread before inspecting mock call arguments"* — which those siblings already show.

**Shortcut test.** Over 4 files, `grep race` or `grep thread` reaches `api.py`; `grep join` reaches both `api.py` and the sibling patterns in the test file; and the observation has already performed victim localization. A weak workflow — read observation, list files, grep obvious terms, open top hits — very likely completes the diagnosis. Pipeline, Retrieval and ReAct would converge on the same path, so the acquisition gap the Formal Suite measures does not exist.

Per the standing principle, these contemporaneous repository facts **must not be hidden to make the Case harder**. The correct response is to lower the rating, which is what this record does.

## Metrics at rejection

| Metric | Value |
|---|---|
| Physical repo files | 4 |
| Physical repository | 2,752 lines / 92,050 bytes |
| Raw failure artifact | **1 line / 213 bytes** |
| Canonical units | 30 (1 log + 29 repo) |
| Required / Optional | 3 (10 %) / 0 |
| Units in files holding no Required evidence | 9 / 30 (30 %) |

The raw artifact is by far the thinnest in the suite, and the Required set includes a unit whose relevance rests on an explanatory comment rather than on structure.

## Package changes made for rejection-record integrity

The package was **not** rebuilt. Only statements that actively asserted authenticity were corrected, because leaving them would have kept describing N16 as a valid candidate:

- `provenance.source_url_or_construction_note` — now states plainly that `raw.log` is fix-PR prose, records the confirmed run/revision facts, and records why salvage is impossible.
- `sanitization.transformations[0].description` — the previous text claimed *"Removed ANSI/control noise only; retained the complete or naturally bounded authentic historical failure observation"*. **Both claims were false**: no ANSI or control bytes were ever present, and the file is not a historical failure observation. Corrected to describe what actually happened — transcription of fix-PR prose — and recorded as the Layer 1 defect rather than repaired.
- `curation.reviewed_by` — now records the rejection. `review_status` remains the literal `human_reviewed` because Schema V2's loader accepts no other value; it records that review concluded, not that the Case was admitted.
- `case_fingerprint` recomputed accordingly.

Physical Artifacts, Canonical Evidence, Required Evidence and Expected Answer were left untouched. The package remains loader-valid so this rejection record stays inspectable; validity is not admission.

## Recorded Candidate-Discovery rule produced by N16

> The Agent-visible raw failure artifact must come from the **failure side** — a CI job log, a Check Run failure annotation, or a failure-reporting issue body. **Never** use narrative text from a fix PR, fix commit message, or post-mortem write-up, however verbatim the quotation. Such text is authored after the diagnosis is known, is pre-localized, and usually sits adjacent to the root cause and the fix in the same paragraph.

Corollary for screening: when a candidate's only surviving failure text lives in a fix PR, check first whether an authentic failure-side artifact still exists (job log, Check Run annotation, issue body). If none does, drop the candidate at discovery instead of constructing a package.

## Scope boundary

Only the N16 `case.json` metadata corrections above, this record, and the N16 material in `BULK-DRAFT-REVIEW.md` were changed. No Physical Artifact, Canonical Evidence, Required Evidence or Expected Answer was modified; no other Case, the suite manifest, runtime code, Schema V2, or the Canonicalization Profile documents were touched. No full Human Review was performed, and no replacement candidate discovery was started.
