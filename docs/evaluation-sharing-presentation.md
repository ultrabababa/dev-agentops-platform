# DevAgentOps Evaluation Sharing (10–15 min)

## Purpose

Internal Agent Evaluation technical sharing, focusing on evaluation contracts, evidence-related badcases, experiment designs, and engineering decisions. Not a second full Evaluation Explorer.

## Entry

- Local: run npm ci and npm run dev from frontend/, then open http://127.0.0.1:5173/presentation
- After merge and deployment: https://devagentops.onrender.com/presentation
- Direct link to a slide: append ?slide=1 through ?slide=9

The route combines a **clearly labeled constructed teaching example** (expected 5, got 6; correct code would add rather than multiply) with frozen, publicly documented experiment figures. The example is aligned with the documented `constructed-assertion-001` illustration in `docs/evaluation/structured-triage-report-and-per-case-scoring.md` and is **not** claimed to be one of the 20 formal benchmark Cases. The route does not fetch the Showcase API. Original Explorer routes and API behavior remain unchanged.

## Controls

- Right / Down / Space / PageDown: next slide
- Left / Up / PageUp: previous slide
- Home / End: first / last slide
- F: fullscreen
- Footer links: open Explorer, Experiment & Attribution, or Architecture in a new tab

## Suggested 12-minute pacing

| Slide | Topic | Approx. |
| --- | --- | --- |
| 1 | Hook: is getting the right answer enough? | 0:30 |
| 2 | Worked example: 2 + 3 should be 5, code returns 6 | 1:00 |
| 3 | Frozen Case, hidden Ground Truth, repeated Samples | 2:00 |
| 4 | Three questions: category, evidence, report contract | 1:30 |
| 5 | Different ways L1–L4 acquire material | 1:00 |
| 6 | Badcase A: not retrieved; B: found but not cited | 2:00 |
| 7 | Fixed-output canonicalization replay | 2:00 |
| 8 | Single/Sequential vs Batch/Parallel | 1:00 |
| 9 | Evaluation-driven development and transfer | 1:00 |

Leave up to three minutes for questions and optional Case drill-down.

## Public-facing content contract

The /presentation route is the **audience-facing artifact**. It must display
only understandable slide titles, experiment evidence, controlled examples, and
concise professional conclusions. It must not display first-person speech,
read-aloud scripts, rehearsal cues, or private presenter notes. There is no
Notes button and no N-key presenter overlay. Keep any rehearsal script outside
the deployed frontend.

Metric provenance: slides 5 and 7 refer to **different L4 experiment runs**:
the representative condition-comparison Run and a separate historical fixed-output
canonicalization Replay. Their Exact Match percentages should not be compared
as measurements from the same Run.

## Presentation narrative and design

The deck follows a nine-part technical narrative, from CI triage context through
Frozen Case / Ground Truth, scoring, L1–L4 comparison, evidence attribution,
fixed-output Replay, Runtime efficiency, and a transferable evaluation loop.

A single intentionally simplified arithmetic-test failure appears on several
slides: expected 5, got 6, because the implementation multiplies instead of adds.
It is always labeled as a teaching example and is not one of the formal Cases.
The example helps distinguish a correct failure type from missing evidence or a
malformed Evidence ID. The numerical experiment results are real published formal
figures and use their corresponding aggregation and caveats.

Typography and card layouts are defined in `frontend/src/presentation-polish.css`,
loaded after `presentation.css`. Sizes scale with the 16:9 slide's own width
rather than the browser viewport, so changes to window height cannot accidentally
inflate text beyond the slide. All selectors are scoped to the presentation.

## Provenance and caveats

Figures are transcribed from the project README Formal Evaluation and Four Experiments sections, including:

- 20 human-reviewed Cases, three repeats each, 60 samples per Formal Run
- L1–L4 and Oracle representative Exact Match and Evidence Hit rates
- L3 Retrieval Acquisition 76.56%, Utilization 66.18%, final Evidence Hit 50.67%
- Evidence Canonicalization fixed-output Replay: Protocol Validity 81.36% to 96.61%, unknown IDs 12 to 0, Exact Match unchanged at 88.33%
- L4 Tool Policy: Decisions 877 to 571, ToolCalls 809 to 775, Wall Time 978.27s to 806.69s

Do not describe ordinary fresh-generation Run differences as causal. Canonicalization has stronger isolation because model outputs are fixed. Oracle is a diagnostic intervention, not L5 or an upper bound. Trajectory and Trace are observable execution evidence, not inaccessible model chain-of-thought.

## Review and release

1. Run npm ci, npm run build, and npm test in frontend/.
2. Check all nine slides at 1280×720 and 1600×900 (or the projector's actual display mode). Confirm no clipped Chinese headings, overlapping graph labels, or slide content outside its 16:9 frame. Test arrows, N, and F.
3. Test original Explorer links; its API may cold-start while slides must remain usable.
4. Merge after review. Confirm Render static-site deep-link rewrite to index.html for /presentation.
5. Open /presentation?slide=1 before the meeting; optionally save a browser print/PDF backup.
