# Validate Fingerprint Chain Before Formal Evaluation

V1 formal evaluation will validate the full fingerprint chain before executing runs, including component fingerprints, case fingerprints, suite fingerprint, and condition fingerprint. Mismatches are evaluation integrity failures and must fail fast rather than produce leaderboard or badcase results; debug workflows may warn or explicitly bypass validation, but formal evaluation cannot.
