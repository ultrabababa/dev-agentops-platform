# L1 — bugswarm-pygithub-36442425251 — construction and Human Review record

> **Layer 1 `PASS`** · **Layer 2 `ADEQUATE`** · constructed and reviewed in the targeted replacement round, awaiting Human disposition.
> **NOT a Formal Freeze and NOT frozen Formal Suite membership.** `Canonicalization Profile v1` is unfrozen, no Suite Manifest exists, and all coordinates and the fingerprint are `provisional-pre-freeze`.

**Failure type:** `lint_or_type_failure`, `acceptable_failure_types: []`. **Slot:** the single `lint_or_type_failure` replacement.
**Fingerprint:** `99dd4c748661d637153498fa0d754ad986b0863cd8115f75a5f6a4d366cd15ba`.

## 1. Authenticity and provenance
Source `https://www.bugswarm.org/artifact-logs/36442425251/raw/`. GitHub Actions `pull_request` job for PR 3182. The log records its own executed revision — `* [new ref] b8ceb2891371446741daf16ce1f56f7615cdaf79 -> pull/3182/merge` and `HEAD is now at b8ceb28 Merge e2c57cbd… into 67cfdb21…` — and that **merge revision is verified upstream** (committer date `2025-01-30T20:23:59Z`). Provenance category: recovered-and-verified executed merge revision, as for N20.

`raw.log` 52,196 bytes / 673 lines. Sanitization: ANSI/OSC removal and CRLF/CR normalisation only. All **4 members byte-identical** to the exact revision.

## 2. The observation states the violation and nothing else
```
##[error]github/Requester.py:924:13: error: "object" has no attribute "raise_for_status"  [attr-defined]
Found 1 error in 1 file (checked 291 source files)
```
mypy names the file, line, column, attribute and rule. It says nothing about **why** the value is typed `object`, and nothing about why the very next line's `iter_content` call is accepted.

## 3. Independent causal chain
1. `Requester.py:924` — `output.raise_for_status()`.
2. `:923` — the guard is `if isinstance(output, RequestsResponse) or hasattr(output, "iter_content"):`. Only the left branch narrows to `RequestsResponse`; the `hasattr` branch yields a type known solely to have `iter_content`. mypy joins the branches, and the join retains only what both have.
3. `:1057-1068` — `__requestEncode` is annotated `-> Tuple[int, Dict[str, Any], Union[str, object]]`, so `output` starts as bare `object`.
4. `:132-149` — `RequestsResponse` defines **both** `iter_content` and `raise_for_status`. The wrapper is not missing anything.
5. Therefore `output.iter_content(...)` on `:925` type-checks while `:924` does not — exactly one error, as the log reports.

## 4. Required Evidence — 4 units, removal-tested
| Unit | Only it supplies | Removal test |
|---|---|---|
| `log:raw-log:lines-0601-0673` | The observation | Remove: no failure at all |
| `repo:requester-py:lines-0901-1000` | The guard and the two calls | Remove: the narrowing construct is unknown |
| `repo:requester-py:lines-1001-1100` | `__requestEncode`'s `Union[str, object]` return | Remove: the origin of `object` is unavailable |
| `repo:requester-py:lines-0101-0200` | That `RequestsResponse` really defines `raise_for_status` | Remove: "the wrapper lacks the method" survives, **inverting** the fix |

The fourth is a direction-settling unit (N22 countermeasure). Three units Optional: `pyproject.toml` (mypy strictness), `requirements/types.txt` (`mypy >=1.0.0`, the release in which `hasattr` narrowing arrived), and `lint.yml`.

## 5. Shortcut and leakage review
`Union[str, object]`, `hasattr`, `RequestsResponse` and `iter_content` occur **zero times in the log**; `raise_for_status` occurs once, in the error itself. There is no path from the observation to the mechanism by grep. Answer-prose scan clean — the only hits are an unrelated `FIXME` in `lint.yml` about pinning pre-commit and a `should be` in an unrelated docstring.

## 6. Runtime Discriminative Value — `ADEQUATE`
1,307-line file, 25 units total (7 log + 18 repo), Required 4. The analyzer gives a precise location and no mechanism; the explanation requires a type-origin trace 144 lines below the error, a domain fact about how mypy joins `or`-narrowed branches, and an **absence-based observation** — that the adjacent `iter_content` call produces no error — to confirm the reading. Two hypotheses must be refuted: that the wrapper lacks the method, and that the annotation alone is at fault.

## 7. Disposition
**Recommended `HUMAN REVIEW PASS`**, Layer 1 `PASS`, Layer 2 `ADEQUATE`. Not a Formal Freeze.
