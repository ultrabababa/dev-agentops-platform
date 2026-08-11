# B05 — bugswarm-baragon-86922674 — REJECTED case record

**Layer 1 — Scientific Validity:** `PASS` after correcting a Ground Truth inaccuracy (§3).
**Layer 2 — Runtime Discriminative Value:** **`LOW`**.
**Status:** **`REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`.** Not a Formal Suite member; retained as a rejection record. **Layer 1 remains `PASS`** — it was not rejected for any defect.
**Failure type:** `lint_or_type_failure`. **Fingerprint:** `b333462c8c7fb3019b519d990fa79637c04039a951020660b5b2ad24b922ca8d`.

## 1. Layer 1
`bugswarm.org/artifact-logs/86922674/raw/`; exact revision `25f732d6280b3033dc6f5d7fcf70f5de5e7abf64` (HubSpot/Baragon). `raw.log` **verified byte-exact** (475,054 → 474,332 == frozen). All **4 members byte-identical**. No pruning, no transformation beyond ANSI removal.

## 2. Causal chain
`raw.log:~3256` — `[INFO] There is an apparent infinite recursive loop in com.hubspot.baragon.data.BaragonStateDatastore.fetchServiceToUpstreamInfoMap(Collection) … At BaragonStateDatastore.java:[line 238]`, then `[ERROR] Failed to execute goal … findbugs-maven-plugin:3.0.1:check … failed with 1 bugs`. Source: the method is declared at `:207` and line `:238` is `serviceToUpstreamInfo.putAll(fetchServiceToUpstreamInfoMap(modifiedServices));` — an unconditional self-call after the loops, with no terminating condition on that path.

## 3. Ground Truth correction
The draft's `root_cause` read *"The collection **overload** recursively calls itself without reducing to a **different overload** or base case."* **There is no overload.** `fetchServiceToUpstreamInfoMap` is declared exactly once (`:207`); the only other occurrence is a call from a different method at `:194`. The wording implied an overload set that does not exist. Corrected to state a single method with an unconditional self-call and no base case, and `recommended_action` re-worded to match.

## 4. Shortcut analysis
The log names the bug class in plain English (*"apparent infinite recursive loop"*), the fully-qualified method, its parameter type, the file and the exact line. The repository step is to open line 238 and confirm the self-call — one glance, no semantic inference, no competing hypothesis, no judgement about the remedy. No answer-prose in the workspace.

## 5. Layer 2 — `LOW`
52 units (43 log + 9 repo), Required 2 (**3.8 %**), 4 files. The 4,275-line log gives modest localisation work, but `[ERROR] Failed to execute goal … findbugs` and *"infinite recursive loop"* are single distinctive greps, and the source confirms rather than explains. Weaker than B04, whose log names a *rule violation* but leaves the reader to work out **why** the modifier is redundant from the private nested-class context.

## 6. Final disposition

**`REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`.** Layer 1 stays `PASS` after the accepted Ground Truth correction. The rejection is purely about measurement value: FindBugs prints the diagnosis in plain English alongside the method, signature, file and line, so the source only confirms it. `LOW` Cases are not retained to preserve category count.
