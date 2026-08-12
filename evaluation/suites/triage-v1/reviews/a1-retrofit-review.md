# A1 — bugswarm-retrofit-113047638 — construction and Human Review record

> **Layer 1 `PASS`** · **Layer 2 `ADEQUATE — lower end`** · constructed and reviewed in the targeted replacement round, awaiting Human disposition.
> **NOT a Formal Freeze and NOT frozen Formal Suite membership.** `Canonicalization Profile v1` is unfrozen, no Suite Manifest exists, and all coordinates and the fingerprint are `provisional-pre-freeze`.

**Failure type:** `test_assertion_failure`, `acceptable_failure_types: []`.
**Fingerprint:** `b54adda01eef4534f6322051ba6e661a7f8aae4bf5b8cff27d33103550effc32`.
**Slot:** one of two `test_assertion_failure` replacements.

## 1. Authenticity and provenance

Source `https://www.bugswarm.org/artifact-logs/113047638/raw/`. **Exact executed revision** `323ffc8f00b19dba98873e77a77c25ec7f89f56c` (square/retrofit), verified against the GitHub API; committer date `2016-03-02T06:14:13Z` matches the BugSwarm `committed_at` exactly. Travis push job, so no merge-revision ambiguity. The upstream repository has since been renamed, and the API resolves the redirect — the revision is intact.

`raw.log` is 146,352 bytes / 2,385 lines. Sanitization is ANSI/OSC escape removal plus CRLF/CR normalisation and nothing else. All **22 repository members are byte-identical** to the exact revision.

## 2. The observation withholds the entire comparison

`raw.log:2311` is the complete failure disclosure:

```
Failed tests:   serializeNullThrows(retrofit2.converter.protobuf.ProtoConverterFactoryTest)
Tests run: 6, Failures: 1, Errors: 0, Skipped: 0
```

Measured against the assertion-disclosure screen, this block contains **zero message characters** — one of only three such logs in the entire 741-log discovery pool. There is no expected value, no actual value, no exception text and no line number. One failure out of 307 tests run across the reactor.

## 3. Independent causal chain

1. `ProtoConverterFactoryTest.java:135-142` — the test:
   ```java
   @Test public void serializeNullThrows() {
     try { service.post(null); fail(); }
     catch (IllegalStateException e) { assertThat(e).hasMessage("Unable to serialize null message."); }
   }
   ```
   It expects `service.post(null)` **itself** to throw.
2. `:43` — the service method is declared `@POST("/") Call<Phone> post(@Body(ignoreNull = false) Phone impl);`.
3. `ProtoRequestBodyConverter.java:14-17` — the converter **does** throw exactly `IllegalStateException("Unable to serialize null message.")` on a null value. The naive "the converter lost its null check" hypothesis is dead.
4. `RequestAction.java:261-273` — `Body.perform` with `ignoreNull == false` **does** call `converter.convert(value)` rather than substituting an empty body. The "`ignoreNull` is not wired through" hypothesis is dead.
5. `OkHttpCall.java:180-186` — `createRawCall()` is where `requestFactory.create(args)` runs, and it is invoked only from `request()`, `execute()` and `enqueue()` (`:66`, `:88`, `:165`). **Request construction, and therefore body conversion, is deferred.**
6. Invoking `service.post(null)` only builds a `Call`. Nothing throws, `fail()` runs, and the test fails with an `AssertionError` — consistent with Maven reporting a Failure rather than an Error.

The oracle assumes eager request construction that the call pipeline does not perform. The product behaves as designed; the test's expectation is wrong.

## 4. Required Evidence — 6 units, each removal-tested

| Required unit | What only it supplies | Removal test |
|---|---|---|
| `log:raw-log:lines-2301-2385` | The observation and the failing test's identity | Remove: nothing identifies the failure |
| `repo:protoconverterfactorytest-java:lines-0101-0143` | The test body — that it expects an immediate throw and calls `fail()` | Remove: the expectation is unknown |
| `repo:protoconverterfactorytest-java:lines-0001-0100` | `@Body(ignoreNull = false)` on the service method | Remove: it is unknown whether the converter should be invoked for null at all |
| `repo:protorequestbodyconverter-java:lines-0001-0034` | That the converter does throw the exact expected message | Remove: "the converter is missing its null check" stays alive, inverting the diagnosis |
| `repo:requestaction-java:lines-0201-0275` | That `ignoreNull = false` genuinely reaches the converter | Remove: "the framework ignores `ignoreNull`" stays alive, again inverting the fix |
| `repo:okhttpcall-java:lines-0101-0200` | That the request is built in `createRawCall`, reached only from `request`/`execute`/`enqueue` | Remove: the actual mechanism is unavailable |

The last three exist to settle **direction**, not merely to establish the mismatch — the recorded N22 hazard. Seven further units are Optional.

## 5. Shortcut and leakage review — including the branch-name leak

The discovery ledger required this to be preserved and assessed rather than removed. It is preserved.

**The leak.** `jw/pass-null-to-converters` occurs twice in the authentic Travis output — the `git clone --depth=50 --branch=…` line and a cache-archive filename. It is real contemporaneous CI output and has not been altered.

**Assessed impact: weak, and partly misleading.** The branch name announces the feature under development — nulls are now passed to converters. That is a true statement about the change, and it points an Agent toward the converter and the `ignoreNull` wiring. Both of those are **exactly the two hypotheses the evidence refutes**. The actual defect is the timing of request construction, which the branch name says nothing about. The leak therefore costs some search effort but pushes toward the wrong answer as readily as the right one.

**A stronger, unavoidable hint sits inside the failing test file.** `.execute()` appears three times in `ProtoConverterFactoryTest.java` — `serializeAndDeserialize`, `deserializeEmpty` and `deserializeWrongValue` all drive the call — while `serializeNullThrows` does not. An attentive Agent can reach the *remedy* from the Required test unit alone. It cannot reach the *root cause* that way; explaining why the omission matters still requires `OkHttpCall`.

**A note on the workspace bound, recorded because it is a judgement.** Seven sibling converter modules exist in the same reactor, and four of them (`gson`, `jackson`, `moshi`, `scalars`) call `.execute()` in their null-body tests. Those modules are outside this Case's Physical Universe because the stated bound is the failing module plus the request-construction path it exercises plus the job configuration — the same rule applied to C2, and consistent with how earlier Cases were bounded. **This bound was not chosen to hide the hint:** the equivalent contrast is already present inside the Required test unit, so widening the workspace would not disclose anything materially new. The situation is recorded here so the Human can widen it if they disagree.

Answer-prose scan otherwise clean: the only `TODO` / `should be` hits are in `Retrofit.java` and concern unrelated matters. `createRawCall` occurs zero times in the log.

## 6. Runtime Discriminative Value — `ADEQUATE — lower end`

| Metric (diagnostic only) | Value |
|---|---:|
| `raw.log` | 2,385 lines / 146,352 bytes |
| Repository | 22 files / 131,479 bytes |
| Canonical units | 71 (24 log + 47 repo) |
| Required / Optional | 6 / 7 |

Localisation is genuinely hard: one named test among 307, with no message of any kind. The diagnosis then requires refuting two plausible hypotheses across two files before the real mechanism can be found in a third. Both refuted hypotheses are the ones the branch name encourages.

It is rated at the **lower end** rather than plainly `ADEQUATE` because the remedy — drive the call — is reachable from the failing test file alone by noticing the `.execute()` contrast. The Case still separates runtimes that pattern-match from runtimes that explain, since `root_cause` and Evidence Hit both require the three direction-settling units. The rating must not be rewritten upward.

## 7. Disposition

**Recommended `HUMAN REVIEW PASS`** as one `test_assertion_failure` replacement, Layer 1 `PASS`, Layer 2 `ADEQUATE — lower end`. Not a Formal Freeze; Formal Suite membership is not frozen.
