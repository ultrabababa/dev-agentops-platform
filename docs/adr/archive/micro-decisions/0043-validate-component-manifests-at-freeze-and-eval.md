# Validate Component Manifests at Freeze and Evaluation

V1 will validate component manifests when freezing a component and again when starting a formal evaluation run. Freeze-time validation prevents malformed components from entering the registry, while formal-evaluation validation rereads manifests, recomputes fingerprints, and compares them with registry records so hand edits, stale schemas, or component version pollution cannot silently affect leaderboard results.
