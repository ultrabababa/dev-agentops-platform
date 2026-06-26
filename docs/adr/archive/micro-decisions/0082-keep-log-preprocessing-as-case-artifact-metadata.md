# Keep Log Preprocessing as Case Artifact Metadata

V1 will record log preprocessing version and chunk fingerprints in case artifacts rather than the component registry. Formal evaluation consumes frozen log chunks from offline case packages, so preprocessing is provenance for suite data generation, not a runtime component, until DevAgentOps explicitly evaluates preprocessing strategies as a separate condition dimension.
