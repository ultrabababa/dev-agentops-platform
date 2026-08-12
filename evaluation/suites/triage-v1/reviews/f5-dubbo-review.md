# F5 — odrepair-dubbo-737f7a7e — construction and Human Review record

> **FINAL DISPOSITION: `HUMAN REVIEW PASS`.** Layer 1 `PASS`, taxonomy fit `PASS`, Layer 2 **`ADEQUATE — lower end`**, which must not be rewritten upward.
> **NOT a Formal Freeze and NOT frozen Formal Suite membership.** `Canonicalization Profile v1` is unfrozen, no Suite Manifest exists, and all coordinates and the fingerprint are `provisional-pre-freeze`.

**Failure type:** `timeout_or_flaky_failure`, `acceptable_failure_types: []`. **Slot:** the second `timeout_or_flaky_failure` replacement — the last open slot.
**Fingerprint:** `97c5550b6098739d1061206970551a4f0e1290b7e7c01eee959222773d9a8b62` (supersedes `881762db…` after the Required promotions in §4).

## 1. Authenticity and provenance

**Observation.** The committed ODRepair order-dependent-test record in
`TestingResearchIllinois/idoft/odr-tests.csv`. Rows were selected by `SHA Detected == 737f7a7ea67832d7f17517326fb2491d0a086dd7`,
the original header retained, and **every selected row kept byte-for-byte**. No field was rewritten, redacted or
reordered and nothing was added. The frozen artifact is 68,140 bytes / 186 lines and covers **11 distinct OD-tests across
several modules**, of which our victim is one.

The record's columns are `Project URL, SHA Detected, Module Path, OD-test, Relevant-test(if it is VP/BSS),
Relevant-test(if it is VPC), OD-test-type`. For the victim they read:

```
https://github.com/apache/incubator-dubbo,737f7a7e…,dubbo-rpc/dubbo-rpc-api,
org.apache.dubbo.rpc.proxy.javassist.JavassistProxyFactoryTest.testGetInvoker,
org.apache.dubbo.rpc.RpcContextTest.testAsync,<VPC test>,victim
```

`OD-test-type = victim` is ODRepair's encoding of *passes in its original order, fails when run after the relevant test*.

**Revision.** Exact executed revision `737f7a7ea67832d7f17517326fb2491d0a086dd7`, verified against the GitHub API —
committer date `2018-09-14T16:32:11Z`, subject *"add jdk11 to travis ci (#2487)"*. The repository has since been renamed
`apache/incubator-dubbo` → `apache/dubbo`; the API resolves the redirect and the revision is intact. All **15 repository
members are byte-identical** to that revision.

**Answer-key exclusion — the point of the exercise.** IDoFT's `pr-data.csv` carries `PR Link` and `Status` columns, and
for this victim they name the fix PR. That file is **curator-side validation only and is not present in any Physical
Artifact**. `odr-tests.csv` has no fix column at all, which is why it, and not `pr-data.csv`, is the frozen observation.
Verified by scan: `pull/6314`, `6314` and `Accepted` occur **zero times** across the log and all 15 members. This applies
the recorded N01 rule — a benchmark's own answer key must never enter the Physical Universe.

**Precedent for a non-log observation.** N01 was admitted on a committed iDFlakies record with no exception, stack or
assertion output. This record likewise carries no exception text. It is materially richer than N06 — which was
**replaced** for having an empty revealed order — because it names both the victim and the test whose prior execution
reveals it.

## 2. Independent causal chain

1. **The victim's body is inherited.** `JavassistProxyFactoryTest` is an 11-line shell that only sets
   `factory = new JavassistProxyFactory()`; the test method lives in `AbstractProxyTest.testGetInvoker:59-71`, which
   asserts `invoker.invoke(new RpcInvocation("echo", …, new Object[]{"aa"})).getValue()` equals `origin.echo("aa")`.
2. **The polluter leaks thread state.** `RpcContextTest.testAsync:143-162` installs an `AsyncContextImpl`, calls
   `RpcContext.startAsync()`, completes the future, then calls `rpcContext.stopAsync()` — and at `:161` **asserts that
   `isAsyncStarted()` is still true afterwards**. It never calls `RpcContext.removeContext()`, which the sibling
   `testGetContext` at `:35` does call.
3. **The state is thread-scoped and survives the test.** `RpcContext.java:53` declares the context field as an
   `InternalThreadLocal`; `:126-127` `getContext()` returns `LOCAL.get()` and `:139-140` `removeContext()` calls
   `LOCAL.remove()`, the only clearing path. In the observed ordered execution the subsequent test inherits the same
   thread-local context, so the started `AsyncContext` is still installed.
4. **The invoker changes its return type because of that state.** `AbstractProxyInvoker.invoke:82-91` reads
   `RpcContext.getContext()` and, because `isAsyncStarted()` is true, takes `:89`
   `return new AsyncRpcResult(rpcContext.getAsyncContext().getInternalFuture());` instead of `:91`
   `return new RpcResult(obj)`.
5. **The future is the very one the polluter completed.** `AsyncContextImpl`'s constructor stores the
   `CompletableFuture` handed to it by `testAsync`, `write(Object)` calls `future.complete(value)` on that same field,
   and `getInternalFuture()` returns it. The identity the diagnosis relies on is therefore established, not assumed.
6. **The returned value comes from that future.** `AsyncRpcResult`'s constructor at `:66-79` registers
   `future.whenComplete((v, t) -> … rFuture.complete(new RpcResult(v)))`, and `getValue():87-88` reads that result. The
   value therefore originates in the future the polluter already completed, not in this invocation's own return value,
   so the comparison against `origin.echo("aa")` no longer sees `"aa"`.

   `AsyncContextImpl` also shows why the leak is not self-healing: `stop()` flips the `stoped` flag while
   `isAsyncStarted()` reads `started`, so `RpcContext.stopAsync()` cannot clear the started state.

The victim's own code is correct. The failure exists only for orders in which the polluter runs first.

**Deliberately not claimed.** The frozen record encodes the outcome as `victim`; it does not distinguish a JUnit
*failure* from an *error*, and no exception text exists in the Physical Universe. The Expected Answer therefore states
that the assertion no longer sees `"aa"` and stops there, rather than asserting a particular JUnit outcome category. This
is the N22 discipline applied to an outcome label.

## 3. Physical Universe — 15 members, selected by rule

**The bound:** the detector-named victim and polluter test classes, the abstract test class that actually holds the
victim method, the project-internal types the victim's invocation path traverses, the support types that fix the
expected value, and the failing module's job configuration. Answer-neutral, and it admits `JdkProxyFactoryTest` — the
co-victim the record lists with the same relevant test — as authentic corroborating context.

Repository 58,140 bytes across 15 files; 28 canonical units total (2 log + 26 repository).

## 4. Required Evidence — 9 units, each removal-tested

| Required unit | What only it supplies | Removal test |
|---|---|---|
| `log:raw-log:lines-0101-0186` | The observation: this victim, its relevant test, and `OD-test-type = victim` | Remove: no failure and no ordering relation |
| `repo:abstractproxytest-java:lines-0001-0073` | The victim method and the `"aa"` comparison | Remove: what the victim asserts is unknown |
| `repo:rpccontexttest-java:lines-0101-0164` | That `testAsync` starts async, keeps `isAsyncStarted()` true past `stopAsync()`, and never removes the context | Remove: the leak cannot be established |
| `repo:rpccontext-java:lines-0001-0100` | That the context field is declared as an `InternalThreadLocal` | Remove: the state's thread scope is unsupported |
| `repo:rpccontext-java:lines-0101-0200` | The actual linkage `getContext() -> LOCAL.get()` and `removeContext() -> LOCAL.remove()` | Remove: that the leaked state is read from, and cleared only via, that thread-local is not entailed — the declaration alone does not show how it is accessed |
| `repo:rpccontext-java:lines-0701-0733` | That `stopAsync()` does not clear the started state | Remove: "the polluter cleaned up, so something else is at fault" survives, **inverting** the diagnosis |
| `repo:abstractproxyinvoker-java:lines-0001-0100` | The `isAsyncStarted()` branch that returns the stale async future instead of `RpcResult(obj)` | Remove: the mechanism linking leaked state to a wrong result is unavailable |
| `repo:asynccontextimpl-java:lines-0001-0084` | That the stored `CompletableFuture` is the one `testAsync` passed, that `write()` completes that same field, and that `getInternalFuture()` returns it — plus that `stop()` flips `stoped`, not `started` | Remove: the future-identity the Ground Truth depends on is assumed rather than shown, and the "the polluter stopped it" reading revives |
| `repo:asyncrpcresult-java:lines-0001-0100` | That the returned value is derived from that completed future | Remove: the claim that the comparison stops seeing `"aa"` is not entailed |

Two promotions were applied at Human review (`rpccontext-java:lines-0101-0200` and `asynccontextimpl-java:lines-0001-0084`), taking Required from 7 to 9. **The Physical Universe was not expanded** — both were already canonical units of existing members.

Re-running strict removal tests over the enlarged set confirms **inclusion-minimality holds**: `rpccontext-java:lines-0001-0100` is still necessary because only it shows the field is an `InternalThreadLocal` — `0101-0200` uses `LOCAL` without revealing its type — and `rpccontext-java:lines-0701-0733` is still necessary because only it connects the `RpcContext`-level `stopAsync()` and `isAsyncStarted()` calls to the `AsyncContextImpl` state. Eight units remain Optional.

## 5. Shortcut and leakage review

- **No fix material of any kind.** `pull/6314`, `6314`, `Accepted` — zero occurrences across every artifact.
- **The polluter is disclosed by the observation.** This is inherent to the ODRepair record and is the Case's main
  limitation: unlike N01, polluter identification is **not** measured here (§6).
- **The observation still requires localisation.** It lists 11 OD-tests and 30 distinct relevant tests across several
  modules; `testAsync` appears 8 times in it, attached to two different victims.
- **Three authentic comments are thematically adjacent and are retained unaltered.** `AbstractProxyInvoker.java:88`
  carries the inline `// ignore obj in case of RpcContext.startAsync()? always rely on user to write back.`, which
  explains the branch's intent and sits inside a Required unit; `:94` has `// TODO async throw exception before async
  thread write back, should stop asyncContext`; and `AsyncRpcResult.java:32` observes that *"RpcContext can be changed,
  because thread may have been used by other thread."* None names the polluter, the ordering, or the remedy, but the
  third in particular gestures at thread reuse. Recorded rather than removed, per the standing rule.
- Other `TODO`/`FIXME` hits (`RpcContextTest:73` `//TODO fix npe`, `RpcContext:692`) are unrelated.

## 6. Runtime Discriminative Value — `ADEQUATE — lower end`

| Metric (diagnostic only) | Value |
|---|---:|
| Observation | 186 lines / 68,140 bytes, 11 OD-tests |
| Repository | 15 files / 58,140 bytes |
| Canonical units | 28 (2 log + 26 repo) |
| Required / Optional | 9 / 8 |

**What it measures.** Mechanism reconstruction for an order-dependent failure with **no exception text anywhere**: the
Agent must connect a leaked thread-local, an assertion in the polluter that documents the leak rather than preventing it,
a branch in production code that changes the *type* of the returned result, and the construction of that result from the
polluter's own future. That is a five-file chain crossing the test/main boundary, and the two hypotheses it must refuse —
that `stopAsync()` cleaned up, and that the victim's own code is wrong — are both natural first readings.

**Why the lower end, and not plainly `ADEQUATE`.** The ODRepair record names the polluter, so the hardest step of a
classic order-dependent case — identifying which earlier test is responsible among many candidates — is handed over.
N01 measures exactly that step and this Case does not. The rating must not be rewritten upward on the strength of the
mechanism alone.

**Taxonomy fit is clean**, unlike F1's. The V1 taxonomy names *"order-dependent test"* directly under
`timeout_or_flaky_failure`, and here the nondeterminism is the execution order itself — established by the detector
record, not inferred from reproduction metadata.

## 7. Disposition — decided

**`HUMAN REVIEW PASS`** as the second `timeout_or_flaky_failure` replacement. Layer 1 `PASS`, taxonomy fit `PASS`,
Layer 2 **`ADEQUATE — lower end`**, which must not be rewritten upward.

One Evidence/Ground-Truth repair was applied at Human review (§4) together with an evidence-faithful rewording of the
thread-inheritance sentence in both the Expected Answer and §2. No Physical Artifact byte changed, the Physical Universe
was not expanded, and the rating and taxonomy are unchanged.

This is a **review pass, not a Formal Freeze**: `Canonicalization Profile v1` is unfrozen, no Suite Manifest exists, and
Formal Suite membership is not frozen.
