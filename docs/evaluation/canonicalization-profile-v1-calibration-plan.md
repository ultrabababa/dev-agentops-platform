# Canonicalization Profile v1 Calibration Plan

## Status and scope

**Status:** Revised after Human Review; ready for final Human approval before calibration. B04 remains unchanged.

This plan calibrates the shared deterministic coordinate system used by Formal Cases. It does not construct B01/B06/N01 packages, execute upstream projects, search for new Cases, implement Retrieval Runtime, create a Suite Manifest, or freeze any Case/Suite fingerprint.

The calibration question is narrow:

> Does one answer-neutral Canonicalization Profile provide complete, stable, usable coordinates across materially different authentic Evidence Universes without turning Canonical Units into Retrieval chunks?

## Candidate Profile v1

The Profile is versioned independently from Suite, Offline Case, artifact, Suite Manifest, Runtime, and Structured Report schemas. It may contain deterministic subprofiles by artifact class, but every Formal Case must use the same algorithm and parameters for the same artifact class.

### Repository text candidate

For every frozen repository text file:

1. start at line 1;
2. create contiguous, non-overlapping fixed-`N` line windows;
3. allow only the final unit to contain fewer than `N` lines;
4. cover every physical line exactly once;
5. derive answer-neutral IDs from source identity and line range;
6. hash the exact resolved bytes;
7. never adjust a boundary using failure lines, fixes, Required Evidence, or curator judgment.

`N=100` is the current candidate parameter because B04 uses it successfully. It is not Suite-frozen.

### Log text calibration question

B04 currently has 11 deterministic natural build-stage units covering its complete 619-line log. That is a valid case-local calibration result, not yet a suite-shared log rule. The calibration must compare two answer-neutral options without changing the retained Physical log:

- a documented deterministic stage/section parser with a deterministic fallback; or
- the same fixed-line-window family used for repository text.

The selected log subprofile must give complete, gap-free coverage across ecosystems and nontraditional failure artifacts without curator-selected error windows. If no stage parser can be specified without ecosystem-specific curator freedom, the fixed-window option is preferred for coordinates. Runtime Retrieval may still use any separately versioned chunking.

## Recommended calibration Cases

The three Cases below are already Human-selected. Counts are estimates from existing source-research files only; they are not approved Formal snapshot membership and do not authorize package construction.

| Case | Pattern | Existing research shape | Units if every listed text file uses `N=100` | Why it tests B04 |
| --- | --- | --- | ---: | --- |
| B01 — Traccar assertion | Stable test assertion with implementation/test context | 2,632-line CI log; three Java files of 210, 83 and 33 lines | log 27 + repository 5 = **32** | Tests whether a causal call/fixture relationship remains citable when one 210-line test file crosses three neutral windows and the small implementation files each collapse to one unit. |
| B06 — Traccar dependency/install | Dependency/runtime incompatibility with repeated fan-out | 10,452-line CI log; 285-line `pom.xml`; 3-line `.travis.yml` | log 105 + repository 4 = **109** | Stresses very long repetitive logs, error fan-out, small build config, and whether fixed coordinates avoid making difficulty mainly a unit-count artifact. |
| N01 — Cukes order-dependent/flaky | Order-dependent shared-state contamination | six exact-revision Java files of 80, 62, 230, 198, 96 and 47 lines; 37-line iDFlakies failure-record JSON; one unresolved 13-line research order file | repository Java 9 + candidate raw failure artifact 1 = **10 naturally mapped**, plus **1 unresolved artifact** | Tests many short files, cross-file state flow, nontraditional failure evidence, and whether the V2 two-part Physical Universe can represent the authentic observation without silently changing its artifact identity. |

B04 remains the fourth calibration observation: 3,050 repository lines become 33 repository units at `N=100`; its 619-line log would become 7 fixed-line units, compared with the current 11 natural stage units. The calibration does not modify either representation yet.

### Why these three, rather than another discovery round

- B01 adds a stable assertion pattern and moderate multi-stage CI log.
- B06 adds the largest log and dependency fan-out, the strongest stress test for coordinate volume.
- N01 adds order dependence, cross-file causal evidence, many short artifacts, and failure evidence that is not a conventional linear CI failure window.

Together they cover the requested assertion, dependency/install, and order/flaky patterns while remaining structurally distinct from B04 lint/type. A config/environment Case is not necessary for this coordinate-only calibration unless one of these three proves ineligible during later source construction; that event would require a separate Human decision, not automatic discovery here.

### N01 Physical Artifact mapping gate

The current V2 Physical Universe remains exactly one `raw.log` plus a bounded exact-revision repository snapshot. Existing N01 research inputs map as follows:

| Input | Current classification | V2 implication |
| --- | --- | --- |
| six Cukes Java files | exact-revision repository members | Natural repository snapshot candidates; final bounded membership still requires Human approval. |
| committed iDFlakies `flaky-list` JSON | authentic benchmark failure observation, not a Cukes repository member | Natural candidate for the single `raw.log`, preserving its JSON bytes/semantics as the bounded failure artifact rather than pretending it is repository content. |
| 13-line observed/original-order file | separate research/order artifact; not established as an exact-revision Cukes repository member | It must not be silently placed in the repository. The current envelope cannot preserve it as a second independent failure artifact alongside the JSON without an explicit representation decision. |

Before N01 calibration, Human Review must decide whether the committed JSON alone is a sufficient authentic failure observation. If yes, the separate order file stays outside the Physical Universe and the `N=100` estimate is 10 units over the naturally mapped inputs. If the order file is necessary, N01 exposes a current Schema V2 limitation; calibration must report that limitation instead of concatenating artifacts, changing the Evidence Universe definition, or inventing a repository membership.

## Granularity risks to inspect

| Risk | B01 | B06 | N01 | Human-review question |
| --- | --- | --- | --- | --- |
| Necessary context split across adjacent units | test setup/call boundary | XML dependency/plugin block | cross-file state lifecycle | Can Required Evidence cite a minimal set without encoding the answer or requiring arbitrary neighboring units? |
| Unit too broad | small source file becomes one unit | 100 log lines may contain many repeated errors | short files become whole-file units | Does one hit over-credit observation of facts the Runtime did not meaningfully inspect? |
| Unit too narrow | assertion and fixture may separate | fan-out creates many near-duplicate units | causal flow spans several small files | Does evidence scoring become fragmentation-sensitive? |
| Corpus/unit-count distortion | moderate | acute: about 109 units under uniform 100-line text windows | low count but many files | Is comparison dominated by meaningless coordinate volume rather than investigation ability? |
| Artifact-class mismatch | Maven stages are available | huge CI stages and repeated summaries | no reliable CI-stage grammar | Can the log rule be deterministic across all three without curator judgment? |
| Line-based hash stability | ordinary Java | XML plus long CI output | JSON/order records may contain long semantic lines | Are byte spans resolvable and exact-hash verified after allowed normalization? |

Calibration evaluates coordinate quality only. Retrieval chunk size, overlap, embeddings, index, top-k, and reranking are not evaluated or inferred from Canonical Unit counts.

## Observation-to-Canonical Attribution / Evidence Hit Semantics

Canonical overlap mapping and Evidence Hit are separate measurements:

```text
Runtime observation
  -> record physical source + exact observed span
  -> derive all overlapping Canonical IDs
  -> apply a separately frozen V1 attribution rule
  -> decide Required Evidence Hit
```

The calibration must not assume `any overlap = full hit`. For each of `N=50`, `N=100`, and `N=200`, it must evaluate:

- partial-overlap over-credit, such as observing only lines 498–510 of a Required unit at 401–500;
- fragmentation when a necessary causal fact crosses a Canonical boundary;
- whether Runtime traces can retain physical observation spans as well as mapped Canonical IDs;
- whether overlap mapping should remain an attribution record distinct from the formal Retrieval Evidence Hit decision;
- whether Required-ID-only Ground Truth can stably express that the necessary fact was actually observed, rather than merely that some bytes in a broad unit overlapped.
- how attribution propagates into Report Evidence Hit: a partial-overlap mapping must not hand the Runtime a Required ID that can then receive unconditional full report credit when the underlying observation was insufficient under the attribution rule.

The calibration output must recommend one explicit V1 attribution rule and document its false-credit/false-miss tradeoff. It must also state whether an overlap-mapped ID is merely trace metadata or is eligible for Retrieval Evidence Hit, report citation, and Report Evidence Hit, so insufficient observations cannot be promoted through reporting into full Required-ID credit. Candidate rules may be compared conceptually (for example complete Required-unit observation, a documented coverage threshold, or a fact-level anchor), but this plan does not add fields or choose a complex schema. If no rule is unambiguous with the existing Required-ID-only Ground Truth, trace contract, and current report-scoring contract, the result must be an explicit limitation/follow-up design decision before Evidence Hit implementation, not an implicit overlap rule.

## Calibration procedure

1. Human-approve the bounded Physical Artifact membership for each calibration Case using the plausible investigation-neighborhood rule. Do not use the expected root cause to select files.
2. Apply candidate Profile parameters mechanically to the retained text artifacts. Generate only comparative coordinate inventories during calibration; do not treat them as Formal Packages or fingerprints.
3. Verify 100% line/byte coverage, no gaps, no overlaps, answer-neutral IDs, deterministic regeneration, and exact resolved-content hashes. This is a calibration/construction audit today, not a claim about current Loader enforcement.
4. Map the already reviewed causal facts to overlapping candidate coordinates. Reassess whether Required Evidence can remain inclusion-minimal sufficient; do not move boundaries to improve the mapping.
5. Compare at least `N=50`, `N=100`, and `N=200` for repository text using these four observations. Record per-Case unit counts, required-set cardinality, adjacent-unit dependence, over-credit risk, and coordinate/tool token overhead.
6. Compare the log subprofile alternatives against B04/B01/B06/N01 for complete coverage, determinism, ecosystem neutrality, fan-out behavior, and nontraditional artifacts.
7. Run the Observation-to-Canonical Attribution analysis above and produce a recommended V1 Evidence Hit rule or an explicit schema/trace limitation.
8. Audit experimental fairness: Canonical coordinates must not reduce Retrieval's search space relative to ReAct, and Runtime retrieval chunks must remain independent inputs whose physical spans can map back to the coordinates.
9. Human-freeze the selected algorithms, parameters, normalization assumptions, ID grammar, byte/line resolution rule, attribution decision, and Profile identifier before bulk Case construction.
10. Before bulk construction, provide a deterministic Canonicalization Profile generator/validator or equivalent machine validation that checks complete coverage, no gaps/overlaps, exact hashes, deterministic IDs/order, and Profile compliance. Do not rely on repeated manual auditing, and do not implement that tooling in this documentation-only phase.

No upstream execution or Runtime experiment is required for these checks.

## Freeze criteria

`Canonicalization Profile v1` is ready to freeze only when all of the following hold:

- one shared deterministic subprofile is selected for repository text and one for retained log/failure text;
- all four calibration observations achieve complete, gap-free, overlap-free exact-hash coverage;
- regeneration produces identical IDs, spans, hashes, and unit ordering;
- no boundary or ID depends on Expected Answer, failure location, fix history, or Required/Optional labels;
- Required Evidence remains inclusion-minimal sufficient at the chosen coordinate granularity;
- unit breadth does not systematically over-credit evidence observation, while fragmentation does not make scoring depend mainly on arbitrary adjacent windows;
- physical observation spans, overlap mappings, Retrieval Evidence Hit, report-citation eligibility, and Report Evidence Hit have a documented relationship, including a recommended V1 attribution rule or an explicitly accepted follow-up limitation;
- Required-ID-only Ground Truth has been shown sufficient for that rule, or its insufficiency is explicitly recorded rather than hidden behind `any overlap`;
- long-log unit count and tool/context overhead remain bounded enough that difficulty is not primarily meaningless token volume;
- Pipeline, Retrieval, ReAct, and Oracle retain the same Physical Universe, and Canonical coordinates give no condition curator-derived search-space advantage;
- Human Review explicitly accepts the profile identifier and parameters;
- deterministic generator/validator requirements are specified for implementation before bulk Formal Case construction.

## If `N=100` is rejected

B04's Physical Package remains unchanged. Before Suite freeze:

1. regenerate B04 `repository-units.json` mechanically from all six unchanged Physical files using the frozen repository-text subprofile;
2. regenerate `log-units.json` only if the frozen log subprofile differs from B04's current 11-unit rule;
3. remap Required and Optional Evidence IDs to coordinates overlapping the same unchanged physical facts;
4. repeat inclusion-minimality and answer-leakage Human Review;
5. validate full coverage, gaps/overlaps, exact hashes, loader behavior, and focused tests;
6. recalculate the B04 Case fingerprint;
7. apply the same frozen Profile to every subsequent Formal Case.

This is a coordinate rebuild, not replay, source reconstruction, evidence-window editing, Expected Answer revision, or change to B04's authentic Physical Universe.

## Human decision requested

Approve or revise:

- B01, B06, and N01 as the three calibration observations;
- `N in {50, 100, 200}` as the repository-text comparison set;
- explicit calibration of a suite-shared log subprofile rather than silently inheriting B04's 11 stage units;
- the N01 artifact mapping gate and Schema-limitation handling;
- the Observation-to-Canonical Attribution study and mandatory V1 rule/limitation output;
- the pre-bulk deterministic generator/validator requirement;
- the freeze criteria and the B04 coordinate-rebuild procedure above.
