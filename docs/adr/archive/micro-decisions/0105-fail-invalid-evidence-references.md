# Fail Invalid Evidence References

V1 report validation will require evidence references to point to evidence identifiers available in the run evidence registry. Missing or nonexistent evidence identifiers are invalid citations that should fail evidence-related scoring, affect report completeness when appropriate, and produce a hallucinated-evidence badcase reason rather than being accepted as natural-language support.
