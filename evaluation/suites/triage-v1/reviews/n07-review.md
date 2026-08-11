# N07 — bugswarm-mypy-237548392 — Human Review PASS record

**Layer 1 — Scientific Validity:** `PASS`. **Layer 2 — Runtime Discriminative Value:** **`ADEQUATE`**.
**Status:** **`HUMAN REVIEW PASS`** — retained in the Formal Suite candidate set. **Formal Suite membership is not frozen**: `Canonicalization Profile v1` is unfrozen and no Suite Manifest exists, so coordinates and fingerprint stay `provisional-pre-freeze`.
**Failure type:** `lint_or_type_failure`. **Fingerprint:** `a7a723c2509119bfe58197917e201bcd66113191b5b0ac02e06b33c4bf4ceb44`.

## 1. Layer 1
`bugswarm.org/artifact-logs/237548392/raw/`; exact revision `ec1efc4f95a9ee2abca72e9cef4304a19eb5366f` (python/mypy). `raw.log` **verified byte-exact** (247,495 → 245,690 == frozen). All **5 members byte-identical**. Nothing to repair; Ground Truth accurate as written.

## 2. Causal chain
`raw.log:~2807` — and this is the **entire** failure text:

```
mypy/test/testcheck.py:160: error: Cannot infer type argument 1 of "retry_on_error"
```

The log says *nothing* about why. The explanation is split across two files:

- `mypy/test/helpers.py:292` — `def retry_on_error(func: Callable[[], _T], max_wait: float = 1.0) -> _T:`. The helper is generic in `_T` and promises to return whatever the callback returns.
- `mypy/test/testcheck.py:160` — `retry_on_error(lambda: os.remove(path))`. The callback is a side-effect-only lambda; `os.remove` returns `None`, so there is no useful type to bind `_T` to, and inference of type argument 1 fails.

The signature is over-general for its actual use — every call site here is a side effect, not a value producer.

## 3. Required Evidence
Three units: the log, `helpers.py:0201-0300` (the generic declaration) and `testcheck.py:0101-0200` (the call site). All pass removal tests. Drop the log and there is no observation; drop either source unit and the inference argument collapses, because neither the declaration nor the call site alone explains why `_T` cannot be inferred. Optional is deliberately empty — nothing else corroborates without duplicating.

## 4. Shortcut analysis
No answer-prose in the workspace; no comment anywhere flags the signature as over-general. The distinguishing property is that **the log is a bare assertion**: `Cannot infer type argument 1` names the failing function and location but supplies no mechanism at all. Unlike every other lint/type Case reviewed, the source is not confirmatory — it carries the whole explanation, and it carries it across **two files that must be read together**.

## 5. Layer 2 — `ADEQUATE`
44 units (29 log + 15 repo), Required 3 (**6.8 %**), 5 files / 42,608 repository bytes. Genuine cross-file type-inference reasoning, a bare one-line observation, and a remedy question that follows only from the composed picture. The strongest Case in the lint/type group and above B04, whose single required source window supplies its explanation in one place.
