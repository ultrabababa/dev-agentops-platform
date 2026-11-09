# DevAgentOps Evaluation Sharing (10–15 min)

## Purpose

Internal Agent Evaluation technical sharing, focusing on evaluation contracts, evidence-related badcases, experiment designs, and engineering decisions. Not a second full Evaluation Explorer.

## Entry

- Local: run npm ci and npm run dev from frontend/, then open http://127.0.0.1:5173/presentation
- After merge and deployment: https://devagentops.onrender.com/presentation
- Direct link to a slide: append ?slide=1 through ?slide=8

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
| 1 | 项目背景与分享主题 | 0:30 |
| 2 | CI 失败诊断示例 | 1:00 |
| 3 | Frozen Case、Ground Truth 与重复评测 | 2:00 |
| 4 | 分类、证据、协议三个评测维度 | 1:30 |
| 5 | L1–L4 与 Oracle 条件对照 | 1:30 |
| 6 | Evidence Acquisition / Utilization 归因 | 2:30 |
| 7 | Batch + Parallel Tool Policy 对照实验 | 1:30 |
| 8 | Evaluation-driven Development 总结 | 1:00 |

Leave up to three minutes for questions and optional Case drill-down.

## Public-facing content contract

The /presentation route is the **audience-facing artifact**. It must display
only understandable slide titles, experiment evidence, controlled examples, and
concise professional conclusions. It must not display first-person speech,
read-aloud scripts, rehearsal cues, or private presenter notes. There is no
Notes button and no N-key presenter overlay. Keep any rehearsal script outside
the deployed frontend.

Metric provenance: slide 5 compares representative L1–L4 / Oracle formal runs.
Slide 6 describes the L3 evidence-pipeline attribution; slide 7 presents
the L4 Batch + Parallel Tool Policy experiment. These are distinct
experiments, with different causal and statistical limitations.

## Presentation narrative and design

The deck follows an eight-part technical narrative, from CI triage context through
Frozen Case / Ground Truth, scoring, L1–L4 comparison, evidence attribution, Runtime efficiency, and a transferable evaluation loop.

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
- L4 Tool Policy: Decisions 877 to 571, ToolCalls 809 to 775, Wall Time 978.27s to 806.69s

Do not describe ordinary fresh-generation Run differences as causal. Oracle is a diagnostic intervention, not L5 or an upper bound. Trajectory and Trace are observable execution evidence, not inaccessible model chain-of-thought.

## Review and release

1. Run npm ci, npm run build, and npm test in frontend/.
2. Check all eight slides at 1280×720 and 1600×900 (or the projector's actual display mode). Confirm no clipped Chinese headings, overlapping graph labels, or slide content outside its 16:9 frame. Test arrows, N, and F.
3. Test original Explorer links; its API may cold-start while slides must remain usable.
4. Merge after review. Confirm Render static-site deep-link rewrite to index.html for /presentation.
5. Open /presentation?slide=1 before the meeting; optionally save a browser print/PDF backup.
