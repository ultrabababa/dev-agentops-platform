# `timeout_or_flaky_failure` — second replacement slot — UNFILLED

> **No Case was constructed for this slot.** Two candidates were examined against their real failure-era
> repositories and **both were rejected before package construction**, on the same material ground.
> The slot remains open. Nothing here is frozen.

## The criterion that both candidates failed

`timeout_or_flaky_failure` is defined by *nondeterminism, excessive duration, race behaviour, or intermittent behaviour
without a stable product-code root cause*. A Case can only measure that if the **nondeterminism is established by the
frozen evidence** — otherwise the Expected Answer asserts a causal character its own artifacts do not support, which is
the recorded N22 hazard applied to the taxonomy label rather than to a fix direction.

Both candidates turned out to have **fully deterministic mechanisms**.

## F2 — `orbit/orbit` job `361637862` — REJECTED, deterministic

Screened at `ADEQUATE` on the strength of actor-lifecycle timing and BugSwarm `stability 2/5`. The real mechanism is a
plain coding defect in `DefaultResponseCachingExtension.generateParameterHash`:

```java
final MessageDigest md = messageDigest.newDigest();
md.digest(messageSerializer.serializeMessage(runtime, new Message().withPayload(params)));   // :208 — result DISCARDED
return String.format("%032X", new BigInteger(1, md.digest()));                                // :209 — digest of EMPTY input
```

`MessageDigest.digest(byte[])` completes **and resets** the digest. Its return value is thrown away, and the second
`md.digest()` then hashes nothing. The method therefore returns **the same constant for every non-empty parameter list**,
so all arguments collide on one response-cache key. That deterministically explains both failures:

- `testMultipleInputs` — `getNow("1")` is served from the entry cached for `getNow("0")`, the actor is never invoked, and
  `assertEquals(i + 1, accessCount)` fails as `expected:<2> but was:<1>`.
- `testCacheFlushWithMultipleInputs` — two distinct inputs return one cached `System.nanoTime()` value, so
  `assertNotEquals` fails with `Values should be different`.

There is no race, no ordering dependence and no timing sensitivity. The static `accessCount` is reset by an `@Before`
method, closing the one order-dependence route that looked plausible at screening.

**F2 would make a good `test_assertion_failure` Case** — the observation gives `expected:<2> but was:<1>` and the cause is
a two-line digest misuse three modules away. Both assertion slots are already filled by A1 and A2, so it is recorded here
rather than salvaged into the wrong taxonomy.

## F3 — `ocpsoft/rewrite` job `118490282` — REJECTED, deterministic

The recorded reserve, screened at `MEDIUM–ADEQUATE` on a truncated message and `stability 3/4`. The mechanism:
`WebClassesFinderTest` injects a mock `ClassLoader` stubbed with
`Mockito.when(classLoader.loadClass("package.TestClass")).thenReturn(ClassFinderTestBean.class)`, but the stack shows the
production path never uses it — `AbstractClassFinder.processClass:199` calls `Class.forName(...)`, which fails on every
run because no class named `package.TestClass` exists. Deterministic, and the same on both failing test methods.

## The generalisable finding

**BugSwarm's `reproducibility_status: Flaky` and `stability` fields describe how reliably the *artifact reproduces*, not
whether the *test* is nondeterministic.** Reproduction variance can come from infrastructure, network or container
scheduling. Screening the flaky category on that metadata — as this discovery round did for F2, F3 and F4 — selects for
the wrong property.

The correct screen is **artifact-visible nondeterminism**, and F1 `apache/lucene` shows what it looks like:

- the log carries a seed line, `__randomizedtesting.SeedInfo.seed([6603B3B1AF668E36:…])`; and
- the source contains an explicit randomiser on the failing path,
  `context = LuceneTestCase.newIOContext(randomState, context)`.

Both are in the Physical Universe, so an Agent can establish the failure's nondeterministic character from the evidence
rather than being told.

## Recommendation for the open slot

Search for candidates carrying an **explicit nondeterminism marker in the observation or on the causal path** — a
randomized-testing seed, a retry that succeeds, an explicit `Thread.sleep`/await/poll timeout, a shared mutable static
without reset, or a documented ordering dependence between tests. Reproduction-stability metadata may be used to *rank*
such candidates but must not be used to *identify* them.

`iDFlakies`-style records remain the natural second source here, since that benchmark selects specifically for
order-dependent tests — the property this slot needs. N01 was drawn from exactly that pool and is already admitted, so
the precedent and the provenance handling both exist.

**Neither F2 nor F3 was salvaged, and neither was constructed.** The slot is reported open rather than filled with a Case
whose taxonomy label its own evidence would not support.
