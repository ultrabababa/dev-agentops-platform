# N12 — bugswarm-django-coupons-89457805 — full Human Review record

> **FINAL DISPOSITION: `REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`.**
> **N12 is NOT a Formal Suite member.** Retained only as a rejection record.
> **Layer 1 remains `PASS`** — `raw.log` is verified byte-exact and all 7 members are byte-identical to the exact revision. It was not rejected for any defect.

**Layer 1 — Scientific Validity:** `PASS`.
**Layer 2 — Runtime Discriminative Value:** **`LOW`** — the observation withholds nothing.
**Failure type:** `test_assertion_failure`.
**Fingerprint:** `d3532f68605edde516ad7c5e54a2628d83d1e5dfe98a1401a38d299a5fa2e8af` (`provisional-pre-freeze`; supersedes `047ce6cb…`).

## Layer 1
Exact revision `4776a4e472e3a14cf475e95f0e146fc3f79b50eb` (byteweaver/django-coupons). `raw.log` **verified byte-exact** (18,154 → 17,295 == frozen). All **7 members byte-identical**. Nothing to repair.

## Causal chain
`raw.log:~383` prints the comparison in full:

```
AssertionError: "{'code': [ValidationError([u'This code is not valid…'])]}"
             != "{'code': [ValidationError(['This code is not valid…'])]}"
```

The only difference is the Python 2 `u` prefix. The test stringifies the form-error payload and compares text, so it is coupled to representation rather than to the semantic `form.errors` mapping. `:390` shows the environment as `.tox/py27-1.7.X`, so the interpreter version is visible in the log too.

## Shortcut analysis
The log shows **both sides of the comparison in full**, and the difference is a single visible character. The interpreter version is in the log path. The repository confirms that the test compares stringified output, but adds no fact the observation withholds. No answer-prose; nothing hidden.

## Layer 2 — `LOW`
13 units (5 log + 8 repo), Required 2 (**15.4 %**), 7 files / 391 repository lines, log 418 lines — the smallest observation in the group. Once the diff is read the diagnosis follows immediately, and the remedy — compare the mapping rather than its repr — needs no further evidence.

## Final disposition
**`REJECTED` — `REPLACE_FOR_LOW_DISCRIMINATIVE_VALUE`.** **Layer 1 remains `PASS`** — the package is authentic, byte-identical to its exact revision and correctly diagnosed; no repair would change the outcome. The rejection is purely measurement value: the log prints both sides of the comparison in full, the difference is one visible character, and the repository withholds nothing.

Per the recorded portfolio policy, `LOW` Cases are not retained to preserve category count. **Not a Formal Suite member.** Counts as one `test_assertion_failure` replacement.

## Scope boundary
Only this record, the N12 `case.json` curation status and fingerprint, and the N12 ledger material were changed. No Physical Artifact was modified.
