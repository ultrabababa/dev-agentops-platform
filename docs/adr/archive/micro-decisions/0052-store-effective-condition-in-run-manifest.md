# Store Effective Condition in Run Manifest

Run manifests will store the complete effective evaluation condition used for the run, not only a condition identifier or unresolved matrix extension. Matrix `extends` is a configuration convenience, while run manifests are reproducibility evidence; preserving the fully resolved runtime, model, component versions, budgets, and repeat settings keeps historical runs understandable even if matrix files are later reorganized.
