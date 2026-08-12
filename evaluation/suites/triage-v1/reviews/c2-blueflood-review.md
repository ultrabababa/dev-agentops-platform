# C2 — bugswarm-blueflood-80881330 — construction and Human Review record

> **Layer 1 `PASS`** · **Layer 2 `ADEQUATE`** · constructed and reviewed in the targeted replacement round, awaiting Human disposition.
> **NOT a Formal Freeze and NOT frozen Formal Suite membership.** `Canonicalization Profile v1` is unfrozen, no Suite Manifest exists, and all coordinates and the fingerprint are `provisional-pre-freeze`.

**Failure type:** `config_or_environment_failure`, `acceptable_failure_types: []`.
**Fingerprint:** `c5e566a81cbb8cac12a5cd761ed2d954057628d1f969a553b97af3685b087a36`.
**Slot:** one of two `config_or_environment_failure` replacements.

## 1. The open question that gated construction — resolved in favour of the Case

The discovery ledger recorded that C2 was conditional: *"if the mapping is supplied by the `elasticsearch-test` library rather than the project, the repository contributes nothing necessary and C2 collapses toward `LOW`."*

**It is a repository file.** `blueflood-elasticsearch/src/main/resources/events_mapping.json`, 454 bytes, 27 lines, present at the exact revision. It is loaded by the failing test through `EsSetup.fromClassPath("events_mapping.json")`. The condition is satisfied and the Case is constructed.

## 2. Authenticity and provenance

Source `https://www.bugswarm.org/artifact-logs/80881330/raw/`. **Exact executed revision** `3c1c16bc200b7d0b97b1dc0594d506b53aa51e0d` (rackerlabs/blueflood), verified against the GitHub API; committer date `2015-09-17T16:43:45Z` matches the BugSwarm `committed_at` exactly. Travis push job on branch `rax-prod`, so there is no merge-revision ambiguity.

`raw.log` is 314,411 bytes / 7,930 lines. Sanitization is ANSI/OSC escape removal plus CRLF/CR normalisation, and nothing else — no pruning, no replacement, no added text. All **20 repository members are byte-identical** to the exact revision, verified by SHA-256 against the manifest.

## 3. Physical Universe — 20 members, selected by rule

The bound is stated so it can be checked: **the failing test file, every project-internal type its `@BeforeClass` and `@AfterClass` reference, the classpath resources those methods load together with their sibling resources in the same directory, and the failing job configuration.** Selection is answer-neutral — it was applied before the causal chain was known, and it admits files that argue against the diagnosis as readily as for it.

Repository total 77,760 bytes across 20 files; with the log, 112 canonical units (80 log + 32 repository).

Notably the rule admits `metrics_mapping.json` and `metrics_mapping_v1.json`, whose root key is literally `"metrics"` — the very type name the failing call uses. They are genuine competing evidence, not decoration (§6).

## 4. Independent causal chain

1. `raw.log:7846-7848` — `HttpAnnotationsEndToEndTest` reports `Tests run: 2, Failures: 0, Errors: 2` and `EsSetupRuntimeException: Exception when executing request create index [index='events']`.
2. The stack's throwing frame is `org.elasticsearch.index.mapper.DocumentMapperParser.parse` (`raw.log:7849`), reached via `MapperService.merge` and `MetaDataCreateIndexService`. The failure is therefore in **parsing a mapping**, not in connecting to a cluster and not in parsing index settings.
3. `HttpAnnotationsEndToEndTest.java:74-76` — the only mapping supplied:
   ```java
   esSetup.execute(EsSetup.createIndex(EventElasticSearchIO.EVENT_INDEX)
           .withSettings(EsSetup.fromClassPath("index_settings.json"))
           .withMapping("metrics", EsSetup.fromClassPath("events_mapping.json")));
   ```
   The mapping is registered under type **`"metrics"`**.
4. `events_mapping.json:2` — the document's root object is **`"graphite_event"`**.
5. `EventElasticSearchIO.java:42-43` — `EVENT_INDEX = "events"` and `ES_TYPE = "graphite_event"`. The events index stores `graphite_event` documents, so the mapping document is correct for production and the literal `"metrics"` in the test is the inconsistent element.
6. An Elasticsearch mapping body must be rooted at the type it defines. Registering a `graphite_event` body under type `metrics` leaves an unrecognised root-level object, which `DocumentMapperParser` rejects — matching frame 2 exactly.
7. `raw.log:7862-7863` — `NullPointerException at HttpAnnotationsEndToEndTest.tearDownClass(HttpAnnotationsEndToEndTest.java:157)`. `@BeforeClass` failed before assigning `httpQueryService`, so `@AfterClass` dereferences null. A pure secondary symptom that inflates the error count from one to two.

## 5. Required Evidence — 4 units, each removal-tested

| Required unit | What only it supplies | Removal test |
|---|---|---|
| `log:raw-log:lines-7801-7900` | The observation, and the `DocumentMapperParser` frame that localises the failure to mapping parsing | Remove: no observation at all, and no basis to prefer mapping parsing over cluster readiness |
| `repo:httpannotationsendtoendtest-java:lines-0001-0100` | That the mapping is registered under type `"metrics"`, and which resource is loaded | Remove: neither the type name nor the resource is knowable |
| `repo:events-mapping-json:lines-0001-0027` | That the document's root type is `graphite_event` | Remove: the mismatch cannot be established |
| `repo:eventelasticsearchio-java:lines-0001-0100` | `ES_TYPE = "graphite_event"` — which side of the mismatch is correct | Remove: the mismatch is still visible, but the **direction** is not. "Change the mapping's root key to metrics" becomes equally defensible |

The fourth unit is included specifically because of the recorded N22 hazard: a Required set can establish a mismatch without entailing the direction its Expected Answer asserts. Here the direction is carried by an explicit Required unit.

Six units are Optional, including both sibling mapping resources and `index_settings.json`.

## 6. Shortcut and leakage review

- **`graphite_event` occurs zero times in the log.** The decisive token exists only in the repository, in exactly the two files that establish the mismatch and its direction. There is no grep from the observation to the answer.
- The log's only structural hint is `DocumentMapperParser`, four occurrences, all stack frames.
- **A real competing hypothesis survives into the workspace.** `metrics_mapping.json` is rooted at `"metrics"`, so "the test loaded the wrong file — it should have loaded `metrics_mapping.json`" is a coherent reading that the evidence must defeat. Only `ES_TYPE` settles it, because the index under construction is the events index.
- **A second competing hypothesis is endorsed by the source itself.** BugSwarm classifies this artifact `Flaky` with stability 4/5, i.e. the dataset's own metadata suggests an unreliable Elasticsearch. The stack frame is what refutes it.
- The `blueflood-elasticsearch` module ran no tests in this job (`raw.log:6802-6805` goes straight from surefire to jar), so the readiness hypothesis is **not** eliminated by a passing sibling. It is eliminated by the throwing frame and by structural comparison with the production mapping — which is why both sibling mappings are retained as Optional evidence.
- Answer-prose scan: the two `TODO` / `should be` hits in the workspace are in `ScheduleContext.java`, `CoreConfig.java` and `HttpMetricsIngestionServer.java` and concern thread-safety, a Riemann host comment and a configurable timeout. None mentions Elasticsearch, mappings or types.

## 7. Runtime Discriminative Value — `ADEQUATE`

| Metric (diagnostic only) | Value |
|---|---:|
| `raw.log` | 7,930 lines / 314,411 bytes |
| Repository | 20 files / 77,760 bytes |
| Canonical units | 112 (80 log + 32 repo) |
| Required / Optional | 4 / 6 |

The observation states that creating an index failed and gives one library frame. It does not name the mapping, the type, the resource file or the inconsistency. Reaching the diagnosis requires composing three repository files, eliminating two live competing hypotheses — one of which the dataset's own metadata asserts — and deciding the direction of a two-sided mismatch. That is what the category is supposed to measure, and it is the property `config_or_environment_failure` candidates almost always lack.

**Residual, recorded honestly.** That an ES mapping body must be rooted at its type is domain knowledge, not an artifact fact; the frozen evidence supports the diagnosis but does not prove it in isolation. The structural identity between `events_mapping.json` and the production `metrics_mapping.json` — same `_routing.required`, same not-analyzed string properties — is what makes "the mapping style is invalid for this ES version" unattractive, and that comparison is available in the workspace.

## 8. Disposition

**Recommended `HUMAN REVIEW PASS`** as one `config_or_environment_failure` replacement, Layer 1 `PASS`, Layer 2 `ADEQUATE`. Not a Formal Freeze; Formal Suite membership is not frozen.
