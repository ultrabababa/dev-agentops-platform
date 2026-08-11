# N22 — bugswarm-pytest-jira-xray-13013454823 — full Human Review record

> **FINAL DISPOSITION: `REJECTED` — `UNDERDETERMINED_GT_AND_LOW_DISCRIMINATIVE_VALUE`.**
> **N22 is NOT a Formal Suite member.** Retained only as a rejection record. **No salvage attempt was made or should be made.**
> **Layer 1 is NOT recorded as a clean `PASS`.** The artifacts are authentic and byte-identical to the exact revision, but the Ground Truth claim is underdetermined by the frozen evidence (§3) — this is a Layer 1 finding, not merely a flag.

**Layer 1 — Scientific Validity:** **`NOT A CLEAN PASS` — Ground Truth underdetermination.** Artifact fidelity and provenance are sound; the Ground Truth direction is not established by the Physical Universe.
**Layer 2 — Runtime Discriminative Value:** **`LOW`**.
**Failure type:** `test_assertion_failure`.
**Fingerprint:** `14fc476bb06fb46ec4775583590e087094a968414a35b0d1fe3eaaded8c6143b` (`provisional-pre-freeze`; supersedes `872e0d45…`).

## Layer 1
Exact revision `019244aa79f9adc182ee138955cc50efe37df9b6` (fundakol/pytest-jira-xray). `raw.log` **verified byte-exact** (35,496 → 35,474 == frozen). All **6 members byte-identical**. Nothing to repair in the artifacts.

## Causal chain
`raw.log:373` — `> assert xray_result['tests'] == expected_tests`. `src/pytest_xray/evidence.py:24` emits `'contentType': content_type`; the fixtures in `tests/test_xray_plugin.py:118,123,129` expect `'ContentType'`. A contract-key casing change left the two out of sync.

## 3. Ground Truth underdetermination — a Layer 1 finding
The Ground Truth asserts *"the expected fixtures on the failing branch still use ContentType"*, i.e. that **the test oracle is stale**.

**The frozen evidence proves only two things:** the implementation emits `contentType`, and the fixtures expect `ContentType`. It does **not** establish which side is stale or regressed — whether the implementation changed the contract key or regressed it is not decidable from the Physical Universe alone, and the failing and passing revisions here are sibling histories.

The Human decision records this as **Ground Truth underdetermination** and directs that **Layer 1 must not be recorded as a clean `PASS`** for N22. This is distinct from every other rejection in the suite: B05, B09, B16, N10, N12 and N13 were all rejected with Layer 1 `PASS`, purely on measurement value. N22 additionally carries a validity finding — its Expected Answer asserts a causal direction its own evidence cannot support.

**No salvage was attempted, per the Human decision.** Establishing the direction would require evidence outside the frozen Physical Universe, and the Case is `LOW` on Layer 2 regardless, so the effort could not produce an admissible Case.

## Shortcut analysis
Both spellings appear in the log — `ContentType` three times and `contentType` once — so the mismatch is **visible in the observation itself**. The repository only confirms which side emits which. The remaining judgement is the direction question in §3, which the artifacts under-determine.

## Layer 2 — `LOW`
14 units (5 log + 9 repo), Required 3 (**21.4 %**), 6 files / 502 repository lines, log 411 lines. The observation discloses the mismatch; the repository confirms it; the one genuinely open question is not answerable from the frozen evidence.

## Final disposition
**`REJECTED` — `UNDERDETERMINED_GT_AND_LOW_DISCRIMINATIVE_VALUE`.** Two independent grounds, either sufficient: the Ground Truth direction is underdetermined by the frozen evidence (§3), and Runtime Discriminative Value is `LOW` because the observation already discloses the mismatch. **Not a Formal Suite member.** Counts as one `test_assertion_failure` replacement.

**Reusable hazard recorded at ledger level:** a Ground Truth may name a *direction* — which side of a mismatch is wrong — that the Physical Universe cannot decide. Two-sided contract mismatches drawn from sibling histories are the characteristic setting. Removal-testing the Required set does not catch this, because every Required unit can be genuinely necessary while the *claim they jointly support* still overreaches.

## Scope boundary
Only this record, the N22 `case.json` curation status and fingerprint, and the N22 ledger material were changed. No Physical Artifact was modified.
