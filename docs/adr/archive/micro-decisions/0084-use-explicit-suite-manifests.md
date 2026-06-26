# Use Explicit Suite Manifests

V1 evaluation suites will use explicit suite manifests that list case packages, case weights, suite identity, suite version, and suite schema version. Formal evaluation will not discover suite cases by scanning directories, because immutable suite versions require a fixed case set and weights rather than behavior that can drift when draft cases or temporary files appear.
