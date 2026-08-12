# B01 — bugswarm-traccar-170287308 — full Human Review record

> **FINAL DISPOSITION: `HUMAN REVIEW PASS`.** Layer 1 `PASS`, Layer 2 **`BORDERLINE-ADEQUATE`**.
> **This is NOT a Formal Freeze.** `Canonicalization Profile v1` is not frozen, no Suite Manifest exists, Formal Suite membership is not frozen, and all coordinates and the fingerprint remain `provisional-pre-freeze`.
> The `BORDERLINE-ADEQUATE` rating stands as recorded and must not be rewritten upward.

**Layer 1 — Scientific Validity:** `PASS`.
**Layer 2 — Runtime Discriminative Value:** **`BORDERLINE-ADEQUATE`**.
**Failure type:** `test_assertion_failure`.
**Fingerprint:** `1e84833842aaa8cb33fce73aa717d0d472bbb9d59b9118c1d9eed9455d5d5fed` (`provisional-pre-freeze`; supersedes `0ba2e634…`).

## Layer 1
Exact revision `4216e038468184a58e9fa10cb9eaff28450de743` (traccar/traccar). `raw.log` **verified byte-exact** (269,002 → 268,293 == frozen). All **6 members byte-identical**. Nothing to repair.

## Causal chain
`raw.log:2375-2383` — `testDecode(UproProtocolDecoderTest) <<< FAILURE!` with `at ProtocolTest.verifyNothing(ProtocolTest.java:87)` and `at UproProtocolDecoderTest.testDecode(UproProtocolDecoderTest.java:13)`; `:2606` — `expected null, but was:<org.traccar.model.Position@285fb753>`. The sample matches the supported Upro packet pattern and follows the normal `Position` construction path (`UproProtocolDecoder` returns `null` only on unsupported patterns or unknown device sessions), while the test still calls `verifyNothing`. The oracle is stale for a valid decoded sample.

## Shortcut analysis
The log names the test, the helper and the line, and shows the mismatch — but the "actual" side is `Position@285fb753`, an **opaque object identity**. Nothing in the observation says whether producing a `Position` here is correct. Deciding **which side is wrong** — a decoder that should have returned `null`, or a stale `verifyNothing` oracle — requires reading the decoder's supported-pattern path and its two `return null` guards. That is the genuine oracle-versus-product discrimination this failure class exists to measure. No answer-prose in the workspace.

## Layer 2 — `BORDERLINE-ADEQUATE`
37 units (27 log + 10 repo), Required 3 (**8.1 %**), 6 files / 631 repository lines. The 2,632-line log carries many passing protocol tests as distractors. Below B02 because the log does disclose the comparison and names the helper directly; above N12 and N22 because the opaque actual value forces a real source judgement.

## Final disposition
**`HUMAN REVIEW PASS`** — admitted as a `test_assertion_failure` Formal candidate, pre-freeze. Layer 1 `PASS`; Layer 2 **`BORDERLINE-ADEQUATE`**, which must not be rewritten upward.

It is admitted for one specific property: the actual value is an opaque object identity, so the Agent cannot decide from the observation whether the product or the oracle is wrong. That oracle-versus-product judgement is the discrimination this failure class exists to measure.

This is a **review pass, not a Formal Freeze**: `Canonicalization Profile v1` is unfrozen, calibration has not started, no Suite Manifest exists, and Formal Suite membership is not frozen.

## Scope boundary
Only this record, the B01 `case.json` curation status and fingerprint, and the B01 ledger material were changed. No Physical Artifact was modified.
