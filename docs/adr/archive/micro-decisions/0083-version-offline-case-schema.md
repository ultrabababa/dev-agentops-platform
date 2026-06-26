# Version Offline Case Schema

V1 offline case packages will include a case schema version so loaders and evaluation runners know how to parse case manifests, log artifacts, repository evidence references, project knowledge references, expected answers, forbidden actions, and weights. Unknown schema versions should be rejected instead of guessed to avoid silently scoring cases under the wrong interpretation.
