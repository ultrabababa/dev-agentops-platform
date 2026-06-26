# Provide Eval Doctor Command

V1 will provide an `eval doctor` command that validates evaluation configuration without executing the agent or calling the model. It should check matrix schema, defaults and extension resolution, component registry entries, component fingerprints, suite and case manifests, case and suite fingerprints, forbidden evaluation artifact leakage, and model configuration completeness so integrity failures are caught before expensive formal evaluation runs.
