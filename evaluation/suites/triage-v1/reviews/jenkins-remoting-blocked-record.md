# Jenkins `remoting` — SUPERSEDED blocked record

> **This record is withdrawn. The conclusion it reached was wrong.**
> The Case was constructed successfully; see `f6-remoting-review.md` (`odrepair-remoting-abf0455a`).

An earlier pass declared `jenkinsci/remoting` `ClassFilterTest.userRequest` **blocked at Layer 1**, on the ground that no
authentic, retrievable, fix-free artifact recorded the victim–polluter pairing.

**The error:** that search covered IDoFT (`pr-data.csv`, `odr-tests.csv`, `gr-data.csv`, `py-data.csv`), the deleted
`flaky-test-dataset` issue, `UT-SE-Research/iDFlakies`, and the `jenkinsci/remoting` issue tracker — but **not
`UT-SE-Research/ODRepair`**, the repository holding the detector's raw per-victim output. `odr-tests.csv` is ODRepair's
*summary* export; `experiments/jsonFiles_0/<victim>/flaky-lists.json` is the underlying record, and it states the
intended and revealed orders with their outcomes directly. Absence from the summary export does not imply absence from
the artifact.

**The lesson worth keeping:** when a benchmark publishes both a summary CSV and per-subject raw output, search the raw
output before concluding a pairing is unsourceable. The reasoning about *what would have been unacceptable* stands — the
fix PR, column excision, and an authored detector record were all correctly refused — but the premise that no acceptable
source existed was false.
