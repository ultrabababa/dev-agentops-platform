# F6 — odrepair-remoting-abf0455a — construction and Human Review record

> **Layer 1 `PASS`** · **Layer 2 `ADEQUATE`** · constructed from a Human-validated candidate and a Human-supplied immutable ODRepair artifact. Awaiting Human disposition.
> **NOT a Formal Freeze and NOT frozen Formal Suite membership.** `Canonicalization Profile v1` is unfrozen, no Suite Manifest exists, and all coordinates and the fingerprint are `provisional-pre-freeze`.

**Failure type:** `timeout_or_flaky_failure`, `acceptable_failure_types: []`. **Slot:** the 20th Case.
**Fingerprint:** `5f335a33e447df8f2014ce1ff89554e5a8c8845fac5c354182f3b5e104e79c34`.

## 1. Correction of record

A previous pass declared this candidate **blocked at Layer 1** for want of a fix-free record naming the polluter. That
conclusion was wrong: it searched IDoFT and `UT-SE-Research/iDFlakies` but **not `UT-SE-Research/ODRepair`**, which is
where the detector's raw per-victim output lives. The artifact exists, is immutable, and is fix-free.
`jenkins-remoting-blocked-record.md` is superseded by this record.

## 2. Authenticity and provenance — Layer 1 clears

**Observation.** `UT-SE-Research/ODRepair` @ `f1c38c319246bae3f5b946fc066cf21ec8a0723e`,
`experiments/jsonFiles_0/hudson.remoting.ClassFilterTest.userRequest/flaky-lists.json`. **357 bytes, one line, frozen
byte-identical — no transformation of any kind.** It contains no ANSI or control sequences, no carriage returns, and
already ends with a newline, so unlike every other Case in the suite there is nothing to strip and nothing to select.

```json
{"dts":[{"name":"hudson.remoting.ClassFilterTest.userRequest",
  "intended":{"order":[],"result":"PASS","testRunId":"2569292575248-…"},
  "revealed":{"order":["hudson.remoting.DefaultClassFilterTest.testDefaultsAreUsedIfOverridesAreGarbage"],
              "result":"ERROR","testRunId":"2550350212668-…"}}]}
```

This is **stronger than the dubbo observation**, which encoded the outcome only in an `OD-test-type` label: here the two
outcomes are stated explicitly, each with a historical `testRunId`.

**Revision.** Exact revision `abf0455a68ad6c52a57e912bb89d51f883f77542`, verified upstream — committer date
`2020-11-02T17:36:12Z`. The same ODRepair commit binds this victim to that revision in `experiments/data/victim.csv:139`
(`jenkinsci/remoting,abf0455a…,.,hudson.remoting.ClassFilterTest.userRequest`) — a **curator-side** check. All **5
repository members are byte-identical** to the exact revision.

**Answer-key exclusion.** `jenkinsci/remoting` PR #706 and ODRepair `experiments/data/results.csv` are curator-side
corroboration only. Verified by scan: `pull/706`, `706` and `results.csv` occur **zero times** across the observation and
all 5 members. `NoClassDefFoundError` — the term PR #706's title uses — also occurs **zero times** anywhere in the
package.

## 3. Independent causal chain

1. **The polluter writes a deliberately invalid regex.** `DefaultClassFilterTest.testDefaultsAreUsedIfOverridesAreGarbage:100-117`
   is `@Test(expected=Error.class)` and builds an overrides file whose sole line is `"Z{100,0}"` — the source's own
   comment reads `/* min > max for repetition */` — then points
   `ClassFilter.FILE_OVERRIDE_LOCATION_PROPERTY` at it.
2. **`ClassFilter` initialises from a static initializer.** `ClassFilter.java:147-154` — `static { STANDARD =
   createDefaultInstance(); … CURRENT_DEFAULT = STANDARD; }`.
3. **That initialisation throws.** `createDefaultInstance():205-225` reads the property and compiles each line;
   `Pattern.compile(line)` on an invalid expression raises `PatternSyntaxException`, which `:225` rethrows as
   `new Error("Error compiling blacklist expressions - '…' is not a valid regular expression.", pex)`.
4. **The class is now permanently unusable.** An `Error` escaping a static initializer marks the class erroneous for the
   life of that classloader; the initializer is never retried.
5. **The polluter's cleanup cannot undo it.** `@After clearProperty():62-65` only unsets the system property. Nothing
   re-runs a static initializer, so the poisoned state survives into every later test in the same JVM.
6. **The victim touches the poisoned class.** `ClassFilterTest.userRequest:124-128` calls `setUp()`, which at `:59-67`
   builds a channel `.withClassFilter(new TestFilter())`; `TestFilter` is declared at `:49` as
   `private static class TestFilter extends ClassFilter`. Merely instantiating the subclass requires the failed
   superclass, so the test **errors rather than failing an assertion** — matching the record's `"result":"ERROR"`
   exactly.

The victim's own code is correct. The failure exists only for orders in which the polluter runs first in the same JVM.

## 4. Physical Universe — 5 members, selected by rule

**The bound:** the two test classes the detector record names, the class whose static initialisation fails, and the
failing job's build configuration. Repository 51,556 bytes across 5 files; 17 canonical units (1 log + 16 repository).

| Member | Bytes | Clause |
|---|---:|---|
| `src/test/java/hudson/remoting/ClassFilterTest.java` | 10,142 | (a) victim, named in the observation |
| `src/test/java/hudson/remoting/DefaultClassFilterTest.java` | 6,765 | (a) polluter, named in the observation |
| `src/main/java/hudson/remoting/ClassFilter.java` | 13,559 | (b) the class whose initialisation fails |
| `pom.xml` | 19,788 | (d) build and surefire configuration — bears on JVM reuse across test classes |
| `Jenkinsfile` | 1,302 | (d) job configuration |

## 5. Required Evidence — 7 units, each removal-tested

| Required unit | What only it supplies | Removal test |
|---|---|---|
| `log:raw-log:lines-0001-0001` | The observation: victim, intended `[]` → `PASS`, revealed `[polluter]` → `ERROR` | Remove: no failure and no ordering relation |
| `repo:defaultclassfiltertest-java:lines-0101-0163` | The invalid pattern `"Z{100,0}"` and the property being pointed at it | Remove: the trigger cannot be established |
| `repo:defaultclassfiltertest-java:lines-0001-0100` | `@After clearProperty()`, i.e. that the polluter *does* attempt cleanup | Remove: "the polluter tidied up, so something else is at fault" cannot be addressed |
| `repo:classfilter-java:lines-0101-0200` | That the defaults are built from a **static initializer** | Remove: the permanence of the damage is unsupported — the crux of the whole diagnosis |
| `repo:classfilter-java:lines-0201-0300` | That `Pattern.compile` on a bad line throws `Error` | Remove: nothing shows initialisation can fail at all |
| `repo:classfiltertest-java:lines-0001-0100` | `TestFilter extends ClassFilter` and its use in `setUp()` | Remove: the victim's dependence on the poisoned class is unknown |
| `repo:classfiltertest-java:lines-0101-0200` | That `userRequest` is the test that calls `setUp()` | Remove: the named victim is not connected to that path |

Two units settle direction rather than merely establish the mismatch: `defaultclassfiltertest:0001-0100` defeats the
"cleanup happened" reading, and `classfilter:0101-0200` is what makes the damage permanent rather than transient. Five
units remain Optional.

## 6. Shortcut and leakage review

- **No fix material.** `pull/706`, `706`, `results.csv` and `NoClassDefFoundError` — all zero across every artifact.
- **The observation contains no mechanism at all.** 357 bytes with no stack, no exception type, no message; every
  diagnostic token (`Z{100,0}`, `static {`, `clearProperty`, `TestFilter`) occurs **only** in the repository.
- **The polluter is disclosed by the observation.** Inherent to the detector format, and the Case's main limitation —
  polluter identification is not measured here (§7).
- **A genuine domain-knowledge bridge is required and is nowhere stated.** That an `Error` escaping a static initializer
  permanently poisons a class is a JVM fact; no artifact says it. This is also what explains `ERROR` rather than
  `FAILURE`, a discrimination the observation hands over but does not explain.
- Answer-prose scan clean: the `should be` hits are ordinary domain prose about class filtering, and the `TODO` /
  `workaround` hits are in `pom.xml` build comments. None concerns ordering, initialisation or a remedy.

## 7. Runtime Discriminative Value — `ADEQUATE`

| Metric (diagnostic only) | Value |
|---|---:|
| Observation | 1 line / 357 bytes |
| Repository | 5 files / 51,556 bytes |
| Canonical units | 17 (1 log + 16 repo) |
| Required / Optional | 7 / 5 |

**What it measures.** Mechanism reconstruction with a real domain bridge. The Agent must explain three things the
evidence does not state: why clearing the property does not help, why the victim is affected at all when it never
touches the override, and why the outcome is an error rather than an assertion failure. Two natural first readings must
be refused — that the polluter's `@After` cleaned up, and that the victim's own code is at fault.

**Why `ADEQUATE` and not lower.** Unlike the dubbo Case, the hard step here is not mechanical composition but a single
non-obvious JVM semantics fact that no artifact supplies. **Why not higher:** as with dubbo, the detector record names
the polluter, so the discrimination N01 measures is absent. If the Human prefers strict parity with
`odrepair-dubbo-737f7a7e`, reading this as `ADEQUATE — lower end` is defensible; the two differ mainly in where the
difficulty sits.

**Taxonomy fit is clean.** The V1 taxonomy names *"order-dependent test"* directly, and the observation states the
order-conditioned outcomes explicitly.

## 8. Disposition

**Recommended `HUMAN REVIEW PASS`**, Layer 1 `PASS`, Layer 2 `ADEQUATE`. Not a Formal Freeze; Formal Suite membership is
not frozen.
