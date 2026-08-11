# B06 — bugswarm-traccar-221926468 — Human Review PASS record

**Layer 1 — Scientific Validity:** `PASS`. **Layer 2 — Runtime Discriminative Value:** **`ADEQUATE`**.
**Status:** **`HUMAN REVIEW PASS`** — retained in the Formal Suite candidate set. **NOT a Formal Freeze**: `Canonicalization Profile v1` is unfrozen and no Suite Manifest exists.
**Failure type:** `dependency_or_install_failure`. **Fingerprint:** `fee1ea1e2378ba5c00dd77d5ca7a7597c99a26c6b3f54415e02609afd142f6b5`.

## 1. Layer 1
Source `bugswarm.org/artifact-logs/221926468/raw/`; exact revision `15f3258905e964ab3b23d9c11fde4a1946ef10b0` (traccar/traccar). `raw.log` is the largest artifact in the suite at **10,452 lines / 954,023 bytes**, and was **verified byte-exact** (upstream 955,046 B / ANSI stripped). All **5 members byte-identical**. Nothing to repair.

## 2. Independent causal chain
1. `raw.log:~3707` — `java.lang.UnsupportedClassVersionError: org/asynchttpclient/AsyncHttpClient : Unsupported major.minor version 52.0`, first surfacing in `WatchProtocolEncoderTest`.
2. Major version **52 is Java 8**. The log never says so — this is domain knowledge the Agent must supply.
3. `.travis.yml` (3 lines) pins `openjdk7`.
4. `pom.xml:72-74` declares `org.asynchttpclient:async-http-client:2.0.31`.
5. **`Context.java:159`** — `private static final AsyncHttpClient ASYNC_HTTP_CLIENT = new DefaultAsyncHttpClient();`. A class-load-time static: any test that touches `Context` triggers class initialisation, loads the Java 8 class file under a Java 7 VM, and errors.
6. Consequence: `Tests run: 237, Failures: 0, Errors: 196` — **196 of 237 tests error**, almost all in unrelated protocol decoders, and the build fails at `:~10431`.

## 3. Required Evidence — corrected 3 → 4
Added `repo:src-org-traccar-context-java:lines-0101-0200`. The Ground Truth asserts *"the incompatible dependency poisons shared initialization"*, and line 159 is the only evidence for it — without it there is no explanation for why 196 unrelated tests failed rather than one. The other three pass removal tests.

## 4. Shortcut analysis
No answer-prose in the workspace. The discriminative properties are unusually strong:

- **Massive misleading fan-out.** 196 errors across unrelated protocol decoders read as broad breakage, not one bad dependency. Picking the right one of 196 is the work.
- **A domain-knowledge decode step.** `major.minor version 52.0` → Java 8 is not stated anywhere in the artifacts.
- **Cause-to-terminal distance ~6,700 lines** in a 10,452-line log; the terminal message is only the generic Maven `BUILD FAILURE … There are test failures`.
- **The fan-out requires a specific line.** Explaining 196 failures needs `Context.java:159`, which no grep on the log will suggest.

## 5. Layer 2 — `ADEQUATE`
116 units (105 log + 11 repo), Required 4 (**3.4 %**), 5 files / 29,475 repository bytes. Four artifacts must be composed — log, `.travis.yml`, `pom.xml`, `Context.java` — plus one external domain fact. This is the strongest structure reviewed to date: it is the only Case combining large-scale misleading fan-out, an unstated domain decode, and a static-initialisation explanation.
