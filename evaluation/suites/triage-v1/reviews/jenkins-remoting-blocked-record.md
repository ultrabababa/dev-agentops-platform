# Jenkins `remoting` order-dependent case — BLOCKED at Layer 1 (observation not sourceable)

> **No Case Package was constructed.** The mechanism is verified and sound; the blocker is that **no authentic,
> retrievable, fix-free historical artifact records the victim–polluter pairing**. Every route to an observation
> requires something this instruction forbids. Reported rather than worked around.

**Target:** `jenkinsci/remoting` @ `abf0455a68ad6c52a57e912bb89d51f883f77542` (verified upstream; committer date
`2020-11-02T17:36:12Z`, subject *"[maven-release-plugin] prepare for next development iteration"*).
Victim `hudson.remoting.ClassFilterTest.userRequest`, polluter
`hudson.remoting.DefaultClassFilterTest.testDefaultsAreUsedIfOverridesAreGarbage`.

## 1. The mechanism is verified — this is not why it is blocked

Confirmed against the exact revision:

- `DefaultClassFilterTest.java:100-101` — `@Test(expected=Error.class) public void
  testDefaultsAreUsedIfOverridesAreGarbage()`, with `:127-129` setting
  `ClassFilter.FILE_OVERRIDE_LOCATION_PROPERTY` to a file of garbage patterns, and an `@After clearProperty()` at
  `:62-63`.
- `ClassFilter.java:147-154` — a **static initializer** runs `STANDARD = createDefaultInstance(); CURRENT_DEFAULT =
  STANDARD;`.
- `ClassFilter.java:205-225` — `createDefaultInstance()` reads that system property and, at `:222-225`,
  `Pattern.compile(line)` throws `new Error("Error compiling blacklist expressions - '…' is not a valid regular
  expression.", pex)`.
- An `Error` escaping a static initializer leaves the class permanently in a failed-initialization state for that
  classloader; later access yields `NoClassDefFoundError`. The polluter's `@After` clears the property, but **clearing
  a property cannot re-run a static initializer**, so the failed state persists and the later victim, which reuses
  `ClassFilter`, errors.

That matches the supplied mechanism exactly. Layer 1 would be sound on the repository side.

## 2. Why it is blocked — the observation cannot be sourced

Exhaustive search for an authentic record pairing this victim with this polluter:

| Source | Result |
|---|---|
| `idoft/odr-tests.csv` (ODRepair — the fix-free dataset used for the dubbo Case) | **No `jenkinsci/remoting` rows at all** |
| `idoft/pr-data.csv` | Has the victim at the exact revision as `OD`, but has **no polluter column**, and our victim's row carries `PR Link = https://github.com/jenkinsci/remoting/pull/706` |
| `testDefaultsAreUsedIfOverridesAreGarbage` across `pr-data.csv`, `odr-tests.csv`, `gr-data.csv`, `py-data.csv` | **Zero occurrences** — the polluter is in no IDoFT dataset |
| `TestingResearchIllinois/flaky-test-dataset` issue #82 (the `Notes` link on every remoting row) | Repository returns **HTTP 404 — deleted**. Unretrievable |
| `UT-SE-Research/iDFlakies` committed `flaky-lists-files` | Only 5 projects (`cukes-http`, `elastic-job-lite-core`, `lib`, `marine-api`, `naming`) — no remoting |
| `jenkinsci/remoting` issues | No failure-reporting issue. The **only** artifact naming both test classes is **PR #706** itself |

**The only surviving source that pairs victim and polluter is PR #706** — which this instruction designates
curator-side corroboration only.

## 3. Why each workaround was refused

- **Freeze the `pr-data.csv` remoting slice as-is.** Imports `pull/706` into an Agent-visible artifact. Forbidden by the
  instruction. Worse, the PR title alone — *"Address `java.lang.NoClassDefFoundError` in `DefaultClassFilterTest`"* —
  states the symptom and localises the cause.
- **Freeze that slice with the `PR Link` / `Notes` columns stripped.** This is **excision** of authentic record content,
  against the standing "replace, do not excise" rule, and it would still not name the polluter — so the Expected
  Answer's ordering claim would be underdetermined by its own observation (the recorded N22 hazard).
- **Author a detector-style record stating "victim alone: PASS; after polluter: ERROR".** That is a synthetic log
  presented as historical, forbidden by this instruction and by the standing methodology.

## 4. Options for the Human

1. **Point at the specific ODRepair artifact.** If the validated pairing came from an ODRepair paper appendix, Zenodo
   bundle, or a local detector run that is publicly retrievable, freezing it resolves the blocker immediately — the
   dubbo Case shows the pattern works.
2. **Substitute a candidate that `odr-tests.csv` already covers.** That file is fix-free by construction and contains
   **1,447 victim rows with a named polluter**, of which **19 repositories are not yet used by this suite**. Strongest
   by volume and independence:

   | Repository | Victims | Example |
   |---|---:|---|
   | `kevinsawicki/http-request` | 25 | `HttpRequestTest.basicProxyAuthentication` |
   | `wildfly/wildfly` | 20 | `InitialContextFactoryTestCase.testInitialFactory` |
   | `Activiti/Activiti` | 17 | `TaskRuntimeClaimReleaseTest.aCreateStandaloneTaskForGroup` |
   | `spring-projects/spring-boot` | 8 | `Log4J2LoggingSystemTests.loggingThatUsesJulIsCaptured` |

   *(`ktuukkan/marine-api` also appears with 12 victims but overlaps the iDFlakies list set; `Apache/Struts` is
   excluded as a repository already used.)*
3. **Accept the remoting Case with a relaxed observation rule**, explicitly recording that the observation carries the
   fix-PR link. **Not recommended** — the PR title localises the diagnosis, which is precisely the N16/N17 leakage
   profile the suite already rejects.

**Nothing was built, nothing was frozen, and no artifact was authored.** The failed-static-initialisation mechanism is a
genuinely good order-dependent case; only its observation is unsourceable under the stated constraints.
