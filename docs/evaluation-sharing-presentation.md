# DevAgentOps Evaluation Sharing (10–15 min)

## Purpose

Internal Agent Evaluation technical sharing, focusing on evaluation contracts, evidence-related badcases, experiment designs, and engineering decisions. Not a second full Evaluation Explorer.

## Entry

- Local: run npm ci and npm run dev from frontend/, then open http://127.0.0.1:5173/presentation
- After merge and deployment: https://devagentops.onrender.com/presentation
- Direct link to a slide: append ?slide=1 through ?slide=9

The route uses frozen, publicly documented figures and does not fetch the Showcase API. Original Explorer routes and API behavior remain unchanged.

## Controls

- Right / Down / Space / PageDown: next slide
- Left / Up / PageUp: previous slide
- Home / End: first / last slide
- N or Notes: toggle speaker notes
- F: fullscreen
- Footer links: open Explorer, Experiment & Attribution, or Architecture in a new tab

## Suggested 12-minute pacing

| Slide | Topic | Approx. |
| --- | --- | --- |
| 1 | Intro and problem | 0:30 |
| 2 | System and triage scenario | 1:00 |
| 3 | Frozen Cases, Ground Truth, Scorer | 2:00 |
| 4 | Exact Match, Evidence Hit, Protocol Validity | 1:30 |
| 5 | L1–L4 comparison and Oracle boundary | 1:00 |
| 6 | L3 evidence acquisition/utilization attribution | 2:00 |
| 7 | Fixed-output canonicalization replay | 2:00 |
| 8 | Batch vs Parallel Tool Policy experiment | 1:00 |
| 9 | Evaluation-driven development and transfer | 1:00 |

Leave up to three minutes for questions and optional Case drill-down.

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
2. Check all nine slides on a projector-resolution browser window; test arrows, N, and F.
3. Test original Explorer links; its API may cold-start while slides must remain usable.
4. Merge after review. Confirm Render static-site deep-link rewrite to index.html for /presentation.
5. Open /presentation?slide=1 before the meeting; optionally save a browser print/PDF backup.
